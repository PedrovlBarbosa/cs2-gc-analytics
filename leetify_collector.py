import os
import sys
import time
import requests
from collections import defaultdict
from typing import Dict, List, Any, Optional
from database import (
    get_connection,
    DB_PATH,
    get_known_match_ids,
    save_matches,
    save_monthly_stats,
    find_matching_gc_match,
    enrich_gc_match_telemetry
)

# Garante suporte a UTF-8 no terminal Windows
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass

SQUAD_PLAYERS = {
    'KrannDy':      {'player_id': 108698,  'steam_id': '76561198063961202'},
    'Aquarista':    {'player_id': 87484,   'steam_id': '76561198189457421'},
    'Art':          {'player_id': 108939,  'steam_id': '76561198063957152'},
    'Cherki':       {'player_id': 540777,  'steam_id': '76561198142174476'},
    'Death':        {'player_id': 318687,  'steam_id': '76561198228725928'},
    'Kinha':        {'player_id': 108940,  'steam_id': '76561198135651044'},
    'mch':          {'player_id': 89302,   'steam_id': '76561198212784573'},
    'The merdas':   {'player_id': 2502581, 'steam_id': '76561199051796322'},
    'Coquinha':     {'player_id': 2492447, 'steam_id': '76561199516992485'},
    'Allan Daniel': {'player_id': 2650509, 'steam_id': '76561199238615143'},
    'Daniel':       {'player_id': 2734005, 'steam_id': '76561198993159598'}
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
    """Busca as partidas do jogador no Leetify (Matchmaking, Premier e Gamers Club)."""
    url = f"https://api-public.cs-prod.leetify.com/v3/profile/matches?steam64_id={steam_id}"
    headers = get_leetify_headers()
    
    for attempt in range(3):
        try:
            resp = requests.get(url, headers=headers, timeout=25)
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

def parse_leetify_player_stat(player_stat: Dict[str, Any]) -> Dict[str, Any]:
    """Extrai todas as métricas avançadas de telemetria da Leetify em unidades amigáveis."""
    kills = player_stat.get('total_kills', 0)
    deaths = player_stat.get('total_deaths', 0)
    adr = round(player_stat.get('dpr', 0.0), 1)
    
    # HS% Real: (total_hs_kills / total_kills) * 100
    total_hs = player_stat.get('total_hs_kills')
    if total_hs is not None and kills > 0:
        hs_pct = round((total_hs / kills) * 100, 1)
    else:
        raw_head_acc = player_stat.get('accuracy_head', 0.0)
        hs_pct = round(raw_head_acc * 100, 1) if raw_head_acc > 0 else 0.0

    # Tempo de reação em ms (Leetify retorna em segundos ex: 0.4219 -> 422 ms)
    raw_rt = player_stat.get('reaction_time')
    reaction_time = round(raw_rt * 1000, 0) if raw_rt is not None else 0.0

    # Ângulo de erro na abertura de pixel (em graus, menor é melhor)
    raw_preaim = player_stat.get('preaim')
    preaim = round(raw_preaim, 1) if raw_preaim is not None else 0.0

    # Precisão de rajada/spray (0 a 100%)
    raw_spray = player_stat.get('spray_accuracy')
    spray_accuracy = round(raw_spray * 100, 1) if raw_spray is not None else 0.0

    # Eficiência de Counter-Strafe (% tiros dados 100% parado)
    raw_cs = player_stat.get('counter_strafing_shots_good_ratio')
    counter_strafe_pct = round(raw_cs * 100, 1) if raw_cs is not None else 0.0

    # Sucesso em vingar a morte de parceiro (Trade Kills %)
    raw_trade_k = player_stat.get('trade_kills_success_percentage')
    trade_kill_pct = round(raw_trade_k * 100, 1) if raw_trade_k is not None else 0.0

    # Sucesso do time em vingar a sua morte (Traded Deaths %)
    raw_trade_d = player_stat.get('traded_deaths_success_percentage')
    traded_death_pct = round(raw_trade_d * 100, 1) if raw_trade_d is not None else 0.0

    # Duração média de cegueira causada no inimigo (em segundos)
    raw_flash = player_stat.get('flashbang_hit_foe_avg_duration')
    flash_duration_avg = round(raw_flash, 2) if raw_flash is not None else 0.0

    # Dano médio causado por granada HE
    raw_he = player_stat.get('he_foes_damage_avg')
    he_damage_avg = round(raw_he, 1) if raw_he is not None else 0.0

    # Desperdício de utilitários na morte (valor médio em $)
    raw_util = player_stat.get('utility_on_death_avg')
    utility_on_death_avg = round(raw_util, 1) if raw_util is not None else 0.0

    # Leetify ratings (+/- %)
    raw_lr = player_stat.get('leetify_rating')
    leetify_rating = round(raw_lr * 100, 2) if raw_lr is not None else 0.0

    raw_ct_lr = player_stat.get('ct_leetify_rating')
    ct_leetify_rating = round(raw_ct_lr * 100, 2) if raw_ct_lr is not None else 0.0

    raw_t_lr = player_stat.get('t_leetify_rating')
    t_leetify_rating = round(raw_t_lr * 100, 2) if raw_t_lr is not None else 0.0

    return {
        "kills": kills,
        "deaths": deaths,
        "adr": adr,
        "hs_percent": hs_pct,
        "reaction_time": reaction_time,
        "preaim": preaim,
        "spray_accuracy": spray_accuracy,
        "counter_strafe_pct": counter_strafe_pct,
        "trade_kill_pct": trade_kill_pct,
        "traded_death_pct": traded_death_pct,
        "flash_duration_avg": flash_duration_avg,
        "he_damage_avg": he_damage_avg,
        "utility_on_death_avg": utility_on_death_avg,
        "leetify_rating": leetify_rating,
        "ct_leetify_rating": ct_leetify_rating,
        "t_leetify_rating": t_leetify_rating
    }

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
            AVG(hs_percent) as hs_percent,
            AVG(NULLIF(leetify_rating, 0.0)) as leetify_rating,
            AVG(NULLIF(reaction_time, 0.0)) as reaction_time,
            AVG(NULLIF(preaim, 0.0)) as preaim,
            AVG(NULLIF(spray_accuracy, 0.0)) as spray_accuracy,
            AVG(NULLIF(counter_strafe_pct, 0.0)) as counter_strafe_pct,
            AVG(NULLIF(trade_kill_pct, 0.0)) as trade_kill_pct,
            AVG(NULLIF(flash_duration_avg, 0.0)) as flash_duration_avg,
            AVG(NULLIF(utility_on_death_avg, 0.0)) as utility_on_death_avg
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

        save_monthly_stats({
            "player_id": player_id,
            "month": month,
            "platform": "STEAM",
            "matches": matches_cnt,
            "wins": wins,
            "loss": loss,
            "win_rate": wr,
            "kills": kills,
            "deaths": deaths,
            "kdr": kdr,
            "adr": adr,
            "hs_percent": hs_pct,
            "leetify_rating": round(row[6] or 0.0, 2),
            "reaction_time": round(row[7] or 0.0, 0),
            "preaim": round(row[8] or 0.0, 1),
            "spray_accuracy": round(row[9] or 0.0, 1),
            "counter_strafe_pct": round(row[10] or 0.0, 1),
            "trade_kill_pct": round(row[11] or 0.0, 1),
            "flash_duration_avg": round(row[12] or 0.0, 2),
            "utility_on_death_avg": round(row[13] or 0.0, 0)
        }, db_path)

def sync_steam_matches(db_path: str = DB_PATH, enrich_gc: bool = True, force_all: bool = False) -> int:
    """
    Sincroniza partidas via Leetify com telemetria avançada completa.
    - Sincroniza partidas Steam (Premier, MM, Wingman).
    - Se enrich_gc=True, enriquece partidas da Gamers Club existentes com os dados telemétricos da demo!
    """
    mode_text = "Completa (Backfill & Enriquecimento)" if force_all else "Incremental Rápida"
    print(f"🎯 Sincronizando dados via Leetify ({mode_text})...")
    total_saved = 0
    total_enriched_gc = 0

    for nick, info in SQUAD_PLAYERS.items():
        pid = info['player_id']
        sid = info['steam_id']

        known_ids = get_known_match_ids(pid, db_path=db_path) if not force_all else set()
        matches = fetch_player_steam_matches(sid)

        if not matches:
            print(f"  [-] {nick:10s} -> nenhuma partida encontrada no Leetify.")
            time.sleep(0.2)
            continue

        matches_to_save = []
        player_enriched = 0

        for raw_m in matches:
            if not isinstance(raw_m, dict):
                continue

            ds = raw_m.get('data_source')
            month = raw_m.get('finished_at', '')[:7]
            if not month:
                continue

            stats_list = raw_m.get('stats', [])
            player_stat = next((s for s in stats_list if s.get('steam64_id') == sid), stats_list[0] if stats_list else {})
            parsed_telemetry = parse_leetify_player_stat(player_stat)

            rounds_won = player_stat.get('rounds_won', 0)
            rounds_lost = player_stat.get('rounds_lost', 0)
            win = 1 if rounds_won > rounds_lost else 0
            map_name = raw_m.get('map_name', '')

            # 1. Tratamento para partidas da Gamers Club presentes no Leetify
            if ds == 'gamers_club':
                if enrich_gc:
                    # Encontra o ID da partida já salva da GC e enriquece APENAS os dados telemétricos
                    matched_id = find_matching_gc_match(pid, month, map_name, rounds_won, rounds_lost, db_path=db_path)
                    if matched_id:
                        enrich_gc_match_telemetry(matched_id, pid, parsed_telemetry, db_path=db_path)
                        player_enriched += 1
                continue

            # 2. Tratamento para partidas Steam (Matchmaking / Premier / Wingman)
            if ds in ('matchmaking', 'matchmaking_competitive', 'matchmaking_wingman'):
                m_id = f"steam_{raw_m.get('id')}"

                if not force_all and (m_id in known_ids or str(m_id) in known_ids):
                    # Se não é force_all, para no primeiro jogo Steam já salvo
                    break

                if ds == 'matchmaking':
                    match_type = 'premier'
                elif ds == 'matchmaking_wingman':
                    match_type = 'wingman'
                else:
                    match_type = 'competitive'

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
                    "map": map_name,
                    "match_type": match_type,
                    "platform": "STEAM",
                    **parsed_telemetry
                }
                matches_to_save.append(parsed_m)

        if matches_to_save:
            save_matches(matches_to_save, db_path)
            affected_months = {m["month"] for m in matches_to_save if m.get("platform") == "STEAM"}
            for m_str in affected_months:
                recalculate_steam_monthly_stats(pid, m_str, db_path)

            steam_saved = len([m for m in matches_to_save if m.get("platform") == "STEAM"])
            total_saved += steam_saved
            total_enriched_gc += player_enriched
            print(f"  [+] {nick:10s} -> {steam_saved} partida(s) Steam + {player_enriched} GC enriquecida(s) com telemetria!")
        else:
            print(f"  [-] {nick:10s} -> em dia (0 novas partidas).")

        time.sleep(0.2)

    print(f"\n🎉 Concluído! {total_saved} partidas Steam processadas e {total_enriched_gc} partidas GC enriquecidas com telemetria Leetify!")
    return total_saved + total_enriched_gc

if __name__ == "__main__":
    force = "--all" in sys.argv or "-a" in sys.argv
    sync_steam_matches(enrich_gc=True, force_all=force)
