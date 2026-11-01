import os
import sys
import time
import requests
from collections import defaultdict
from typing import Dict, List, Any
from database import get_connection, DB_PATH, get_known_match_ids, save_matches

# Garante suporte a UTF-8 no terminal Windows
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass

SQUAD_PLAYERS = {
    'KrannDy':   {'player_id': 108698, 'steam_id': '76561198063961202'},
    'Aquarista': {'player_id': 87484,  'steam_id': '76561198189457421'},
    'Art':       {'player_id': 108939, 'steam_id': '76561198063957152'},
    'Cherki':    {'player_id': 540777, 'steam_id': '76561198142174476'},
    'Death':     {'player_id': 318687, 'steam_id': '76561198228725928'},
    'Kinha':     {'player_id': 108940, 'steam_id': '76561198135651044'},
    'mch':       {'player_id': 89302,  'steam_id': '76561198212784573'}
}

def get_leetify_headers() -> Dict[str, str]:
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
    }
    try:
        from collector import load_config
        cfg = load_config()
        if "leetify_api_key" in cfg:
            headers['Authorization'] = f"Bearer {cfg['leetify_api_key']}"
    except Exception:
        pass
    return headers

def fetch_player_steam_matches(steam_id: str) -> List[Dict[str, Any]]:
    """Busca as partidas do jogador no Leetify e filtra as partidas da Steam (Matchmaking/Premier)."""
    url = f"https://api-public.cs-prod.leetify.com/v3/profile/matches?steam64_id={steam_id}"
    headers = get_leetify_headers()
    
    for attempt in range(3):
        try:
            resp = requests.get(url, headers=headers, timeout=20)
            if resp.status_code == 200:
                data = resp.json()
                if isinstance(data, list):
                    return data
            elif resp.status_code == 429:
                time.sleep(5 * (attempt + 1))
            else:
                break
        except Exception:
            time.sleep(1)
    return []

def save_steam_monthly_stats(stats: Dict[str, Any], db_path: str = DB_PATH):
    conn = get_connection(db_path)
    cursor = conn.cursor()
    cursor.execute("""
    INSERT INTO monthly_stats (
        player_id, month, platform, matches, wins, loss, win_rate, kdr, adr,
        kills, deaths, multi_kills, hs_percent, updated_at
    )
    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
    ON CONFLICT(player_id, month, platform) DO UPDATE SET
        matches = excluded.matches,
        wins = excluded.wins,
        loss = excluded.loss,
        win_rate = excluded.win_rate,
        kdr = excluded.kdr,
        adr = excluded.adr,
        kills = excluded.kills,
        deaths = excluded.deaths,
        multi_kills = excluded.multi_kills,
        hs_percent = excluded.hs_percent,
        updated_at = CURRENT_TIMESTAMP
    """, (
        stats["player_id"],
        stats["month"],
        "STEAM",
        stats.get("matches", 0),
        stats.get("wins", 0),
        stats.get("loss", 0),
        stats.get("win_rate", 0.0),
        stats.get("kdr", 0.0),
        stats.get("adr", 0.0),
        stats.get("kills", 0),
        stats.get("deaths", 0),
        stats.get("multi_kills", 0),
        stats.get("hs_percent", 0.0)
    ))
    conn.commit()
    conn.close()

def recalculate_steam_monthly_stats(player_id: int, month: str, db_path: str = DB_PATH):
    """Recalcula os dados agregados mensais para o jogador a partir das partidas no banco."""
    conn = get_connection(db_path)
    cursor = conn.cursor()
    cursor.execute("""
        SELECT 
            COUNT(match_id) as matches,
            SUM(win) as wins,
            SUM(kills) as kills,
            SUM(deaths) as deaths,
            AVG(adr) as adr,
            AVG(hs_percent) as hs_percent
        FROM matches
        WHERE player_id = ? AND month = ? AND platform = 'STEAM'
    """, (player_id, month))
    row = cursor.fetchone()
    conn.close()

    if row and row[0] and row[0] > 0:
        matches_cnt = row[0]
        wins = row[1] or 0
        loss = matches_cnt - wins
        wr = round((wins / matches_cnt) * 100, 1)
        kills = row[2] or 0
        deaths = row[3] or 0
        kdr = round(kills / deaths, 2) if deaths > 0 else 0.0
        adr = round(row[4] or 0.0, 1)
        hs_pct = round(row[5] or 0.0, 1)

        save_steam_monthly_stats({
            "player_id": player_id,
            "month": month,
            "matches": matches_cnt,
            "wins": wins,
            "loss": loss,
            "win_rate": wr,
            "kills": kills,
            "deaths": deaths,
            "kdr": kdr,
            "adr": adr,
            "hs_percent": hs_pct
        }, db_path)

def sync_steam_matches(db_path: str = DB_PATH) -> int:
    """
    Sincroniza apenas partidas novas da Steam via Leetify.
    Para imediatamente assim que encontrar a primeira partida já conhecida no banco.
    """
    print("🎯 Sincronizando partidas novas da STEAM (Premier & MM) via Leetify...")
    total_saved = 0

    for nick, info in SQUAD_PLAYERS.items():
        pid = info['player_id']
        sid = info['steam_id']

        # Carrega partidas já conhecidas deste jogador
        known_ids = get_known_match_ids(pid, db_path=db_path)

        matches = fetch_player_steam_matches(sid)
        steam_matches = [
            m for m in matches 
            if isinstance(m, dict) and m.get('data_source') in ('matchmaking', 'matchmaking_competitive', 'matchmaking_wingman')
        ]

        if not steam_matches:
            print(f"  [-] {nick:10s} -> nenhuma partida encontrada.")
            time.sleep(0.2)
            continue

        new_matches_to_save = []
        for raw_m in steam_matches:
            m_id = f"steam_{raw_m.get('id')}"

            # Early exit: como Leetify lista em ordem cronológica decrescente (mais recente primeiro),
            # assim que encontrar uma partida que já temos, todas as seguintes também já foram salvas.
            if m_id in known_ids or str(m_id) in known_ids:
                break

            month = raw_m.get('finished_at', '')[:7]
            if not month:
                continue

            # Mapeia tipo
            ds = raw_m.get('data_source')
            if ds == 'matchmaking':
                match_type = 'premier'
            elif ds == 'matchmaking_wingman':
                match_type = 'wingman'
            else:
                match_type = 'competitive'

            # Extrai stats do jogador
            stats_list = raw_m.get('stats', [])
            player_stat = next((s for s in stats_list if s.get('steam64_id') == sid), stats_list[0] if stats_list else {})

            kills = player_stat.get('total_kills', 0)
            deaths = player_stat.get('total_deaths', 0)
            adr = round(player_stat.get('dpr', 0.0), 1)
            hs_pct = round(player_stat.get('accuracy_head', 0.0) * 100, 1)
            rounds_won = player_stat.get('rounds_won', 0)
            rounds_lost = player_stat.get('rounds_lost', 0)
            win = 1 if rounds_won > rounds_lost else 0

            parsed_m = {
                "match_id": m_id,
                "player_id": pid,
                "month": month,
                "team_name_a": "Seu Time",
                "score_a": rounds_won,
                "team_name_b": "Adversário",
                "score_b": rounds_lost,
                "win": win,
                "rating_player": 0,
                "rating_diff": 0,
                "map": raw_m.get('map_name', ''),
                "match_type": match_type,
                "platform": "STEAM",
                "kills": kills,
                "deaths": deaths,
                "adr": adr,
                "hs_percent": hs_pct
            }
            new_matches_to_save.append(parsed_m)

        if new_matches_to_save:
            save_matches(new_matches_to_save, db_path)
            affected_months = {m["month"] for m in new_matches_to_save}
            for m_str in affected_months:
                recalculate_steam_monthly_stats(pid, m_str, db_path)

            total_saved += len(new_matches_to_save)
            print(f"  [+] {nick:10s} -> {len(new_matches_to_save)} nova(s) partida(s) adicionada(s)!")
        else:
            print(f"  [-] {nick:10s} -> em dia (0 novas partidas).")

        time.sleep(0.2)

    if total_saved > 0:
        print(f"\n🎉 Sucesso! {total_saved} nova(s) partida(s) da Steam sincronizada(s)!")
    else:
        print(f"\n✨ Steam 100% atualizada! Nenhuma partida nova pendente.")

    return total_saved

if __name__ == "__main__":
    sync_steam_matches()
