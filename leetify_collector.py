import os
import sys
import time
import requests
from collections import defaultdict
from typing import Dict, List, Any
from database import get_connection, DB_PATH

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
    # Tenta carregar API key se o usuário configurou
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
                time.sleep(10 * (attempt + 1))
            else:
                break
        except Exception as e:
            time.sleep(2)
    return []

def save_steam_match(m: Dict[str, Any], player_id: int, db_path: str = DB_PATH):
    conn = get_connection(db_path)
    cursor = conn.cursor()
    cursor.execute("""
    INSERT INTO matches (
        match_id, player_id, month, team_name_a, score_a,
        team_name_b, score_b, win, rating_player, rating_diff,
        map, match_type, platform, kills, deaths, adr, hs_percent, updated_at
    )
    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
    ON CONFLICT(match_id, player_id) DO UPDATE SET
        month = excluded.month,
        score_a = excluded.score_a,
        score_b = excluded.score_b,
        win = excluded.win,
        map = excluded.map,
        match_type = excluded.match_type,
        platform = excluded.platform,
        kills = excluded.kills,
        deaths = excluded.deaths,
        adr = excluded.adr,
        hs_percent = excluded.hs_percent,
        updated_at = CURRENT_TIMESTAMP
    """, (
        m["match_id"],
        player_id,
        m["month"],
        m.get("team_name_a", "Seu Time"),
        m.get("score_a", 0),
        m.get("team_name_b", "Adversário"),
        m.get("score_b", 0),
        m.get("win", 0),
        m.get("rating_player", 0),
        m.get("rating_diff", 0),
        m.get("map", ""),
        m.get("match_type", "premier"),
        "STEAM",
        m.get("kills", 0),
        m.get("deaths", 0),
        m.get("adr", 0.0),
        m.get("hs_percent", 0.0)
    ))
    conn.commit()
    conn.close()

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

def sync_steam_matches(db_path: str = DB_PATH):
    print("🎯 Iniciando sincronização das partidas da STEAM (Premier & MM) via Leetify...")
    total_saved = 0

    for nick, info in SQUAD_PLAYERS.items():
        pid = info['player_id']
        sid = info['steam_id']
        print(f"\n🔍 Buscando partidas de {nick} (Steam: {sid})...")
        
        matches = fetch_player_steam_matches(sid)
        steam_matches = [m for m in matches if isinstance(m, dict) and m.get('data_source') in ('matchmaking', 'matchmaking_competitive', 'matchmaking_wingman')]
        
        if not steam_matches:
            print(f"  [-] Nenhuma partida da Steam encontrada para {nick}.")
            time.sleep(1.5)
            continue

        player_month_matches = defaultdict(list)
        p_count = 0

        for raw_m in steam_matches:
            m_id = f"steam_{raw_m.get('id')}"
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
            multis = player_stat.get('multi2k', 0) + player_stat.get('multi3k', 0) + player_stat.get('multi4k', 0) + player_stat.get('multi5k', 0)

            parsed_m = {
                "match_id": m_id,
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
                "kills": kills,
                "deaths": deaths,
                "adr": adr,
                "hs_percent": hs_pct,
                "multi_kills": multis
            }

            save_steam_match(parsed_m, pid, db_path)
            player_month_matches[month].append(parsed_m)
            p_count += 1

        # Consolida estatísticas mensais da Steam para o jogador
        for month, m_list in player_month_matches.items():
            m_cnt = len(m_list)
            wins = sum(x['win'] for x in m_list)
            loss = m_cnt - wins
            wr = round(wins / m_cnt * 100, 1) if m_cnt > 0 else 0.0
            tot_kills = sum(x['kills'] for x in m_list)
            tot_deaths = sum(x['deaths'] for x in m_list)
            kdr = round(tot_kills / tot_deaths, 2) if tot_deaths > 0 else 0.0
            avg_adr = round(sum(x['adr'] for x in m_list) / m_cnt, 1) if m_cnt > 0 else 0.0
            tot_multis = sum(x['multi_kills'] for x in m_list)
            avg_hs = round(sum(x['hs_percent'] for x in m_list) / m_cnt, 1) if m_cnt > 0 else 0.0

            save_steam_monthly_stats({
                "player_id": pid,
                "month": month,
                "matches": m_cnt,
                "wins": wins,
                "loss": loss,
                "win_rate": wr,
                "kills": tot_kills,
                "deaths": tot_deaths,
                "kdr": kdr,
                "adr": avg_adr,
                "multi_kills": tot_multis,
                "hs_percent": avg_hs
            }, db_path)

        total_saved += p_count
        print(f"  [+] {nick}: {p_count} partidas da Steam sincronizadas em {len(player_month_matches)} meses!")
        time.sleep(2.0)

    print(f"\n🎉 Sucesso! Total de {total_saved} registros de partidas da Steam sincronizados!")
    return total_saved

if __name__ == "__main__":
    sync_steam_matches()
