import os
import re
import sys
import json
import sqlite3
from datetime import datetime
from collections import defaultdict
from typing import Dict, List, Any, Optional
from bs4 import BeautifulSoup

from database import get_connection, save_matches, save_monthly_stats, DB_PATH

# Garante suporte a UTF-8 no terminal Windows
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass

SQUAD_PLAYERS = {
    'KrannDy':      {'player_id': 108698,  'steam_id': '76561198063961202', 'aliases': ['krandy', 'kranndy']},
    'Aquarista':    {'player_id': 87484,   'steam_id': '76561198189457421', 'aliases': ['aquarista', 'jhonfissura', 'jhon', 'jhonkek']},
    'Art':          {'player_id': 108939,  'steam_id': '76561198063957152', 'aliases': ['art', 'artricolor']},
    'Cherki':       {'player_id': 540777,  'steam_id': '76561198142174476', 'aliases': ['cherki', 'fn$', 'fn$ 777']},
    'Death':        {'player_id': 318687,  'steam_id': '76561198228725928', 'aliases': ['death', 'thors']},
    'Kinha':        {'player_id': 108940,  'steam_id': '76561198135651044', 'aliases': ['kinha', 'monster']},
    'mch':          {'player_id': 89302,   'steam_id': '76561198212784573', 'aliases': ['mch', 'tgzinh0', 'tgzin', 'thierryguedes']},
    'The merdas':   {'player_id': 2502581, 'steam_id': '76561199051796322', 'aliases': ['zicoring', 'the merdas', 'merdas']},
    'Coquinha':     {'player_id': 2492447, 'steam_id': '76561199516992485', 'aliases': ['perinao', 'coquinha', 'coca', 'allandaniela']},
    'Allan Daniel': {'player_id': 2650509, 'steam_id': '76561199238615143', 'aliases': ['noobeeskins', 'allan daniel', 'allan']},
    'Daniel':       {'player_id': 2734005, 'steam_id': '76561198993159598', 'aliases': ['john wick', 'daniel']}
}

def identify_squad_player(name: str, steam_id: Optional[str] = None) -> Optional[tuple]:
    """Identifica se o jogador é um dos 7 do Squad pelo SteamID ou Nickname."""
    if steam_id:
        for nick, info in SQUAD_PLAYERS.items():
            if info['steam_id'] == str(steam_id).strip():
                return nick, info['player_id']
                
    name_clean = name.strip().lower()
    for nick, info in SQUAD_PLAYERS.items():
        if nick.lower() in name_clean:
            return nick, info['player_id']
        for alias in info['aliases']:
            if alias.lower() in name_clean:
                return nick, info['player_id']
    return None

def normalize_map_name(text: str) -> str:
    t = text.lower()
    mapping = {
        'mirage': 'de_mirage',
        'inferno': 'de_inferno',
        'dust': 'de_dust2',
        'nuke': 'de_nuke',
        'overpass': 'de_overpass',
        'anubis': 'de_anubis',
        'ancient': 'de_ancient',
        'vertigo': 'de_vertigo',
        'train': 'de_train',
        'office': 'cs_office'
    }
    for k, v in mapping.items():
        if k in t:
            return v
    return "de_unknown"

def parse_steam_gcpd_html(html_content: str) -> List[Dict[str, Any]]:
    """Analisa o código HTML completo da página Steam GCPD (Premier / Competitivo)."""
    soup = BeautifulSoup(html_content, 'html.parser')
    matches = []
    
    # Procura por tabelas genéricas de histórico
    tables = soup.find_all("table", class_="generic_kv_table")
    if not tables:
        # Tenta container principal
        tables = soup.find_all("table")

    match_idx = 0
    for table in tables:
        text = table.get_text()
        # Verifica se é uma tabela de partida (tem data ou mapa)
        date_match = re.search(r'(\d{4}-\d{2}-\d{2})\s+(\d{2}:\d{2}:\d{2})', text)
        if not date_match:
            continue

        match_date = date_match.group(1)
        match_month = match_date[:7]
        map_name = normalize_map_name(text)

        # Procura placar no texto da tabela ou irmãos
        score_match = re.search(r'(\d{1,2})\s*[:xX\-]\s*(\d{1,2})', text)
        score_a = int(score_match.group(1)) if score_match else 0
        score_b = int(score_match.group(2)) if score_match else 0

        # Jogadores presentes na partida
        players_in_match = []
        links = table.find_all("a", href=True)
        for a in links:
            href = a['href']
            p_name = a.get_text().strip()
            sid_match = re.search(r'profiles/(\d+)', href)
            sid = sid_match.group(1) if sid_match else None
            
            squad_info = identify_squad_player(p_name, sid)
            if squad_info:
                # Tenta extrair kills/deaths das células adjacentes (td/tr)
                kills = 0
                deaths = 0
                tr = a.find_parent("tr")
                if tr:
                    tds = [td.get_text().strip() for td in tr.find_all("td")]
                    # Geralmente: [Nome, Ping, Kills, Assists, Deaths, MVPs, Score]
                    nums = [int(re.sub(r'\D', '', x)) for x in tds if re.match(r'^\d+$', x.strip())]
                    if len(nums) >= 3:
                        kills = nums[1] if len(nums) > 1 else 0
                        deaths = nums[3] if len(nums) > 3 else (nums[2] if len(nums) > 2 else 0)

                nick, pid = squad_info
                players_in_match.append({
                    "nick": nick,
                    "player_id": pid,
                    "kills": kills,
                    "deaths": deaths
                })

        # Se nenhum link direto foi achado, tenta varrer o texto procurando nicks do squad
        if not players_in_match:
            for nick, info in SQUAD_PLAYERS.items():
                if nick.lower() in text.lower():
                    players_in_match.append({
                        "nick": nick,
                        "player_id": info['player_id'],
                        "kills": 0,
                        "deaths": 0
                    })

        if players_in_match:
            match_idx += 1
            mid = f"steam_gcpd_{match_date.replace('-', '')}_{match_idx}"
            win = 1 if score_a > score_b else 0
            
            for p in players_in_match:
                matches.append({
                    "match_id": mid,
                    "player_id": p["player_id"],
                    "month": match_month,
                    "team_name_a": "Seu Time",
                    "score_a": score_a,
                    "team_name_b": "Adversário",
                    "score_b": score_b,
                    "win": win,
                    "map": map_name,
                    "match_type": "premier",
                    "platform": "STEAM",
                    "kills": p["kills"],
                    "deaths": p["deaths"],
                    "adr": 0.0,
                    "hs_percent": 0.0
                })

    return matches

def parse_steam_json(json_content: str) -> List[Dict[str, Any]]:
    """Analisa arquivo JSON extraído do console da Steam."""
    data = json.loads(json_content) if isinstance(json_content, str) else json_content
    matches = []
    
    for item in data:
        date_str = item.get("date", "")
        month = item.get("month") or (date_str[:7] if date_str else "2024-01")
        map_name = normalize_map_name(item.get("map", ""))
        score_a = int(item.get("score_a", 0))
        score_b = int(item.get("score_b", 0))
        win = 1 if score_a > score_b else 0
        mid = item.get("id") or f"steam_json_{date_str.replace('-', '')}_{len(matches)}"

        players = item.get("players", [])
        for p in players:
            name = p.get("name", "")
            sid = p.get("steam_id")
            squad_info = identify_squad_player(name, sid)
            if squad_info:
                nick, pid = squad_info
                matches.append({
                    "match_id": mid,
                    "player_id": pid,
                    "month": month,
                    "team_name_a": "Seu Time",
                    "score_a": score_a,
                    "team_name_b": "Adversário",
                    "score_b": score_b,
                    "win": win,
                    "map": map_name,
                    "match_type": "premier",
                    "platform": "STEAM",
                    "kills": int(p.get("kills", 0)),
                    "deaths": int(p.get("deaths", 0)),
                    "adr": float(p.get("adr", 0.0)),
                    "hs_percent": float(p.get("hs_percent", 0.0))
                })

    return matches

def import_matches_into_db(matches_list: List[Dict[str, Any]], db_path: str = DB_PATH) -> int:
    """Insere partidas no SQLite e recalcula estatísticas mensais da Steam."""
    if not matches_list:
        return 0

    for m in matches_list:
        if "match_id" not in m and "id" in m:
            m["match_id"] = m["id"]
        if "player_id" not in m and "players" in m:
            pass

    save_matches(matches_list, db_path=db_path)
    
    # Agrupa por (player_id, month) para calcular os resumos mensais
    grouped = defaultdict(list)
    for m in matches_list:
        grouped[(m["player_id"], m["month"])].append(m)

    for (pid, month), m_list in grouped.items():
        m_cnt = len(m_list)
        wins = sum(x["win"] for x in m_list)
        loss = m_cnt - wins
        wr = round(wins / m_cnt * 100, 1) if m_cnt > 0 else 0.0
        tot_kills = sum(x.get("kills", 0) for x in m_list)
        tot_deaths = sum(x.get("deaths", 0) for x in m_list)
        kdr = round(tot_kills / tot_deaths, 2) if tot_deaths > 0 else 0.0
        avg_adr = round(sum(x.get("adr", 0.0) for x in m_list) / m_cnt, 1) if m_cnt > 0 else 0.0

        save_monthly_stats({
            "player_id": pid,
            "month": month,
            "platform": "STEAM",
            "matches": m_cnt,
            "wins": wins,
            "loss": loss,
            "win_rate": wr,
            "kills": tot_kills,
            "deaths": tot_deaths,
            "kdr": kdr,
            "adr": avg_adr,
            "multi_kills": 0,
            "hs_percent": 0.0
        }, db_path=db_path)

    return len(matches_list)

def import_file(file_path: str, db_path: str = DB_PATH) -> int:
    """Lê um arquivo local (.html ou .json) e importa para o banco."""
    if not os.path.exists(file_path):
        print(f"Arquivo não encontrado: {file_path}")
        return 0

    with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
        content = f.read()

    if file_path.endswith(".json") or content.strip().startswith("[") or content.strip().startswith("{"):
        matches = parse_steam_json(content)
    else:
        matches = parse_steam_gcpd_html(content)

    count = import_matches_into_db(matches, db_path=db_path)
    print(f"✅ Sucesso! {count} partidas importadas de '{file_path}'!")
    return count

if __name__ == "__main__":
    if len(sys.argv) > 1:
        import_file(sys.argv[1])
    else:
        # Procura arquivos padrão na pasta
        found = False
        for fname in ["steam_matches.json", "steam_premier.html", "matchhistorypremier.html"]:
            if os.path.exists(fname):
                import_file(fname)
                found = True
        if not found:
            print("Coloque o arquivo 'steam_matches.json' ou 'steam_premier.html' na pasta e execute novamente:")
            print("  python import_steam_data.py <caminho_do_arquivo>")
