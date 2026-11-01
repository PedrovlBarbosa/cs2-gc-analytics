import time
import requests
from collector import load_config, GamersClubCollector
from database import init_db, save_monthly_stats, save_matches, save_player

TARGET_PLAYERS = {
    'KrannDy': 108698,
    'Aquarista': 87484,
    'Art': 108939,
    'Cherki': 540777,
    'Death': 318687,
    'Kinha': 108940,
    'mch': 89302
}

def collect_core_squad(max_months=30):
    init_db()
    cfg = load_config()
    collector = GamersClubCollector(cfg)

    print(f"Coletando histórico completo para os 7 jogadores principais ({max_months} meses)...")

    # Garante que os 7 estão salvos na tabela players
    for nick, pid in TARGET_PLAYERS.items():
        save_player({
            "player_id": pid,
            "nick": nick,
            "level": None,
            "is_main_user": 1 if pid == int(collector.player_id) else 0,
            "avatar_url": ""
        })

    all_months = collector.fetch_available_months()
    target_months = all_months[:max_months] if max_months else all_months

    for idx, month in enumerate(target_months, 1):
        print(f"[{idx}/{len(target_months)}] Coletando mês {month}...")
        for nick, pid in TARGET_PLAYERS.items():
            stats = collector.fetch_player_month_stats(pid, month)
            if stats and stats.get("matches", 0) > 0:
                save_monthly_stats(stats)
            time.sleep(0.04)

        # Partidas para o usuário principal
        matches = collector.fetch_matches_for_month(int(collector.player_id), month)
        if matches:
            save_matches(matches)

    print("Coleta dos 7 jogadores concluída com sucesso!")

if __name__ == "__main__":
    collect_core_squad(30)
