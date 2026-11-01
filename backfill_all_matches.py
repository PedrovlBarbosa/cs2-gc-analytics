import time
from collector import load_config, GamersClubCollector
from database import save_matches, get_all_months

TARGET_PLAYERS = {
    'KrannDy': 108698,
    'Aquarista': 87484,
    'Art': 108939,
    'Cherki': 540777,
    'Death': 318687,
    'Kinha': 108940,
    'mch': 89302
}

def backfill():
    cfg = load_config()
    collector = GamersClubCollector(cfg)
    months = get_all_months()

    print(f"Iniciando coleta de TODAS as partidas dos 7 jogadores para {len(months)} meses...")

    total_matches_saved = 0
    for i, m in enumerate(months, 1):
        month_matches = []
        for nick, pid in TARGET_PLAYERS.items():
            matches = collector.fetch_matches_for_month(pid, m)
            if matches:
                month_matches.extend(matches)
            time.sleep(0.03)

        if month_matches:
            save_matches(month_matches)
            total_matches_saved += len(month_matches)
            print(f"[{i}/{len(months)}] Mês {m}: +{len(month_matches)} partidas coletadas (Total: {total_matches_saved})")
        else:
            print(f"[{i}/{len(months)}] Mês {m}: 0 partidas")

    print(f"\nFinalizado! Total de {total_matches_saved} partidas salvas no banco de dados!")

if __name__ == "__main__":
    backfill()
