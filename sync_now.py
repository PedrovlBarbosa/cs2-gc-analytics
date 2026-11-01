import time
from datetime import datetime
from collector import load_config, GamersClubCollector
from database import save_monthly_stats, save_matches, CORE_PLAYERS

TARGET_PLAYERS = {
    'KrannDy': 108698,
    'Aquarista': 87484,
    'Art': 108939,
    'Cherki': 540777,
    'Death': 318687,
    'Kinha': 108940,
    'mch': 89302
}

def sync_recent(months_count=2):
    """Atualiza rapidamente apenas o mês atual e o anterior para os 7 jogadores."""
    cfg = load_config()
    collector = GamersClubCollector(cfg)
    
    # Obtém os meses disponíveis mais recentes da GC
    all_months = collector.fetch_available_months()
    recent_months = all_months[:months_count] if all_months else []

    updated_count = 0
    for m in recent_months:
        for nick, pid in TARGET_PLAYERS.items():
            stats = collector.fetch_player_month_stats(pid, m)
            if stats and stats.get("matches", 0) > 0:
                save_monthly_stats(stats)
                updated_count += 1
            time.sleep(0.04)

        matches = collector.fetch_matches_for_month(int(collector.player_id), m)
        if matches:
            save_matches(matches)

    return len(recent_months), updated_count

if __name__ == "__main__":
    m_count, up_count = sync_recent(2)
    print(f"Sincronização concluída! {m_count} meses recentes verificados, {up_count} registros de jogadores atualizados.")
