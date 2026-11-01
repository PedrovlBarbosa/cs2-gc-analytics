import os
import sys
import json
import time
import re
import requests
from typing import Dict, List, Any, Optional
from database import init_db, save_player, save_monthly_stats, save_matches

CONFIG_FILE = "config.json"

def load_config(config_path: str = CONFIG_FILE) -> Dict[str, Any]:
    # 1. Tenta carregar do arquivo local config.json
    if os.path.exists(config_path):
        with open(config_path, "r", encoding="utf-8") as f:
            return json.load(f)
            
    # 2. Se estiver rodando no Streamlit Cloud, tenta carregar de st.secrets
    try:
        import streamlit as st
        if hasattr(st, "secrets"):
            if "GC_CONFIG" in st.secrets:
                raw = st.secrets["GC_CONFIG"]
                return json.loads(raw) if isinstance(raw, str) else dict(raw)
            if "cookies" in st.secrets:
                return {
                    "player_id": st.secrets.get("player_id", "108698"),
                    "player_nick": st.secrets.get("player_nick", "KrannDy"),
                    "cookies": dict(st.secrets.get("cookies", {})),
                    "headers": dict(st.secrets.get("headers", {}))
                }
    except Exception:
        pass

    raise FileNotFoundError(
        "Arquivo de configuração 'config.json' não encontrado. "
        "No computador local, certifique-se de que o 'config.json' está na pasta. "
        "No Streamlit Cloud, configure seus cookies em 'Settings -> Secrets'."
    )

class GamersClubCollector:
    def __init__(self, config: Dict[str, Any]):
        self.player_id = str(config.get("player_id", "108698"))
        self.player_nick = config.get("player_nick", "KrannDy")
        self.cookies = config.get("cookies", {})
        self.headers = config.get("headers", {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Referer": f"https://gamersclub.com.br/player/{self.player_id}",
            "Accept": "application/json, text/plain, */*"
        })
        self.session = requests.Session()
        self.session.cookies.update(self.cookies)
        self.session.headers.update(self.headers)

    def fetch_profile_and_teammates(self) -> List[Dict[str, Any]]:
        """Busca o perfil do jogador e extrai dados do usuário e lista de companheiros/amigos."""
        print(f"\n[1/3] Acessando perfil do jogador {self.player_id} ({self.player_nick})...")
        url = f"https://gamersclub.com.br/player/{self.player_id}"
        resp = self.session.get(url, timeout=15)
        if resp.status_code != 200:
            print(f"Erro ao acessar perfil: status {resp.status_code}")
            return []

        html = resp.text
        
        # Salva o usuário principal
        save_player({
            "player_id": int(self.player_id),
            "nick": self.player_nick,
            "level": 15,
            "is_main_user": 1,
            "avatar_url": ""
        })

        # Extrai lista de amigos/companheiros
        teammates = []
        idx = html.find("friendsList:")
        if idx != -1:
            sub = html[idx + len("friendsList:"):].strip()
            bracket_count = 0
            end_idx = 0
            for i, ch in enumerate(sub):
                if ch == '[':
                    bracket_count += 1
                elif ch == ']':
                    bracket_count -= 1
                    if bracket_count == 0:
                        end_idx = i + 1
                        break
            try:
                raw_friends = json.loads(sub[:end_idx])
                for f in raw_friends:
                    pid = int(f.get("PID"))
                    nick = f.get("PNick", "Desconhecido")
                    level = int(f.get("level", 0)) if f.get("level") else None
                    avatar = f"https://steamcdn-a.akamaihd.net/steamcommunity/public/images/avatars/{f.get('PAvatar', '')}"
                    teammates.append({
                        "player_id": pid,
                        "nick": nick,
                        "level": level,
                        "is_main_user": 0,
                        "avatar_url": avatar
                    })
                    save_player(teammates[-1])
                print(f" -> Encontrados {len(teammates)} companheiros de equipe na Gamers Club!")
            except Exception as e:
                print(f"Aviso ao analisar lista de amigos: {e}")

        return teammates

    def fetch_available_months(self) -> List[str]:
        """Obtém a lista de todos os meses disponíveis no histórico."""
        url = f"https://gamersclub.com.br/api/box/history/{self.player_id}"
        resp = self.session.get(url, timeout=15)
        if resp.status_code == 200:
            try:
                data = resp.json()
                months = data.get("months", [])
                print(f" -> {len(months)} meses encontrados no histórico da GC.")
                return months
            except Exception as e:
                print(f"Erro ao analisar meses: {e}")
                return []
        print(f"Aviso ao buscar meses GC: HTTP {resp.status_code} - {resp.text[:200]}")
        return []

    def parse_stat_dict(self, stat_list: List[Dict[str, str]]) -> Dict[str, Any]:
        """Converte a lista de stat da GC em um dicionário limpo."""
        mapping = {}
        for item in stat_list:
            stat_name = item.get("stat")
            val = str(item.get("value", "")).strip().replace("%", "")
            mapping[stat_name] = val

        def to_float(k, default=0.0):
            try:
                return float(mapping.get(k, default))
            except (ValueError, TypeError):
                return default

        def to_int(k, default=0):
            try:
                return int(float(mapping.get(k, default)))
            except (ValueError, TypeError):
                return default

        return {
            "kdr": to_float("KDR"),
            "adr": to_float("ADR"),
            "kills": to_int("Matou"),
            "deaths": to_int("Morreu"),
            "kast_percent": to_float("KAST%"),
            "multi_kills": to_int("Multi Kills"),
            "first_kills": to_int("First kills"),
            "hs_percent": to_float("HS%"),
            "bomb_plants": to_int("Bombas pla."),
            "bomb_defuses": to_int("Bombas def.")
        }

    def fetch_player_month_stats(self, pid: int, month: str) -> Optional[Dict[str, Any]]:
        """Busca as estatísticas de um jogador para um mês específico."""
        url = f"https://gamersclub.com.br/api/box/historyFilterDate/{pid}/{month}"
        try:
            resp = self.session.get(url, timeout=15)
            if resp.status_code == 200:
                data = resp.json()
                stat_clean = self.parse_stat_dict(data.get("stat", []))
                matches_info = data.get("matches", {})
                
                wins = int(matches_info.get("wins", 0))
                loss = int(matches_info.get("loss", 0))
                total_matches = int(matches_info.get("matches", 0))
                win_rate = round((wins / total_matches * 100), 1) if total_matches > 0 else 0.0

                character = data.get("character", {}).get("hitbox", {})

                return {
                    "player_id": pid,
                    "month": month,
                    "matches": total_matches,
                    "wins": wins,
                    "loss": loss,
                    "win_rate": win_rate,
                    **stat_clean,
                    "hitbox_head": character.get("head", 0),
                    "hitbox_chest": character.get("chest", 0),
                    "hitbox_stomach": character.get("stomach", 0),
                    "hitbox_arms": character.get("leftArm", 0) + character.get("rightArm", 0),
                    "hitbox_legs": character.get("leftLeg", 0) + character.get("rightLeg", 0)
                }
        except Exception as e:
            print(f"Erro ao buscar stats do jogador {pid} para {month}: {e}")
        return None

    def fetch_new_matches(self, pid: int, month: str, known_ids: set) -> List[Dict[str, Any]]:
        """Busca apenas as partidas novas que ainda não estão salvas no banco (para na primeira partida já conhecida)."""
        new_matches = []
        page = 0
        hit_known = False
        while not hit_known:
            url = f"https://gamersclub.com.br/api/box/historyMatchesPage/{pid}/{month}/{page}"
            try:
                resp = self.session.get(url, timeout=15)
                if resp.status_code != 200:
                    break
                data = resp.json()
                page_matches = data.get("monthMatches", [])
                if not page_matches:
                    break
                for m in page_matches:
                    m_id = m.get("id")
                    if m_id in known_ids or str(m_id) in known_ids:
                        hit_known = True
                        break
                    new_matches.append({
                        "match_id": m_id,
                        "player_id": pid,
                        "month": month,
                        "team_name_a": m.get("teamNameA", ""),
                        "score_a": m.get("scoreA", 0),
                        "team_name_b": m.get("teamNameB", ""),
                        "score_b": m.get("scoreB", 0),
                        "win": m.get("win", 0),
                        "rating_player": m.get("ratingPlayer", 0),
                        "rating_diff": m.get("ratingDiff", 0),
                        "map": m.get("map", ""),
                        "match_type": m.get("type", "lobby")
                    })
                page += 1
            except Exception:
                break
        return new_matches

    def fetch_matches_for_month(self, pid: int, month: str) -> List[Dict[str, Any]]:
        """Busca todas as partidas de um mês paginadas."""
        matches_result = []
        page = 0
        while True:
            url = f"https://gamersclub.com.br/api/box/historyMatchesPage/{pid}/{month}/{page}"
            try:
                resp = self.session.get(url, timeout=15)
                if resp.status_code != 200:
                    break
                data = resp.json()
                page_matches = data.get("monthMatches", [])
                if not page_matches:
                    break
                for m in page_matches:
                    matches_result.append({
                        "match_id": m.get("id"),
                        "player_id": pid,
                        "month": month,
                        "team_name_a": m.get("teamNameA", ""),
                        "score_a": m.get("scoreA", 0),
                        "team_name_b": m.get("teamNameB", ""),
                        "score_b": m.get("scoreB", 0),
                        "win": m.get("win", 0),
                        "rating_player": m.get("ratingPlayer", 0),
                        "rating_diff": m.get("ratingDiff", 0),
                        "map": m.get("map", ""),
                        "match_type": m.get("type", "lobby")
                    })
                page += 1
            except Exception:
                break
        return matches_result

    def run(self, max_months: Optional[int] = None):
        """Executa a coleta completa de dados."""
        init_db()
        teammates = self.fetch_profile_and_teammates()
        all_months = self.fetch_available_months()

        if max_months:
            target_months = all_months[:max_months]
        else:
            target_months = all_months

        print(f"\n[2/3] Coletando estatísticas mensais e partidas para {len(target_months)} meses...")

        main_pid = int(self.player_id)
        
        # Jogadores a monitorar: Usuário principal + todos os companheiros
        all_monitored_pids = [main_pid] + [t["player_id"] for t in teammates]

        for i, m in enumerate(target_months, 1):
            print(f"[{i}/{len(target_months)}] Processando mês {m}...")

            # 1. Estatísticas do usuário principal
            user_stats = self.fetch_player_month_stats(main_pid, m)
            if user_stats:
                save_monthly_stats(user_stats)

            # 2. Partidas do usuário principal
            matches = self.fetch_matches_for_month(main_pid, m)
            if matches:
                save_matches(matches)

            # 3. Estatísticas dos companheiros de equipe para este mês
            for tm in teammates:
                t_pid = tm["player_id"]
                t_stats = self.fetch_player_month_stats(t_pid, m)
                if t_stats and t_stats.get("matches", 0) > 0:
                    save_monthly_stats(t_stats)
                # Pequena pausa para respeitar o rate-limit da GC
                time.sleep(0.05)

        print("\n[3/3] Coleta concluída com sucesso! Banco 'gc_stats.db' atualizado.")

if __name__ == "__main__":
    cfg = load_config()
    collector = GamersClubCollector(cfg)
    
    # Por padrão, se passado um argumento, limita o número de meses recentes (ex: python collector.py 12)
    max_m = int(sys.argv[1]) if len(sys.argv) > 1 else 12
    print(f"Iniciando coleta para os últimos {max_m} meses...")
    collector.run(max_months=max_m)
