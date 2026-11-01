import time
import subprocess
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

def push_to_github():
    """Envia o banco de dados atualizado para o GitHub para atualizar o link dos amigos."""
    try:
        subprocess.run(["git", "add", "gc_stats.db"], check=True, capture_output=True)
        diff = subprocess.run(["git", "diff", "--cached", "--name-only"], capture_output=True, text=True)
        if "gc_stats.db" in diff.stdout:
            subprocess.run(["git", "commit", "-m", "chore: sync latest GC matches [skip ci]"], check=True, capture_output=True)
            subprocess.run(["git", "push", "origin", "main"], check=True, capture_output=True)
            return True
        return False
    except Exception as e:
        print(f"Aviso ao enviar para o GitHub: {e}")
        return False

def sync_recent(months_count=2, auto_push=True):
    """Atualiza rapidamente apenas o mês atual e o anterior para os 7 jogadores."""
    cfg = load_config()
    collector = GamersClubCollector(cfg)
    
    # Obtém os meses disponíveis mais recentes da GC
    all_months = collector.fetch_available_months()
    recent_months = all_months[:months_count] if all_months else []

    updated_count = 0
    matches_count = 0
    for m in recent_months:
        for nick, pid in TARGET_PLAYERS.items():
            stats = collector.fetch_player_month_stats(pid, m)
            if stats and stats.get("matches", 0) > 0:
                save_monthly_stats(stats)
                updated_count += 1
            
            p_matches = collector.fetch_matches_for_month(pid, m)
            if p_matches:
                save_matches(p_matches)
                matches_count += len(p_matches)
            time.sleep(0.04)

    pushed = False
    if auto_push:
        pushed = push_to_github()

    return len(recent_months), updated_count, pushed

if __name__ == "__main__":
    m_count, up_count, pushed = sync_recent(2, auto_push=True)
    status_cloud = "e publicado no GitHub para seus amigos!" if pushed else "localmente."
    print(f"Sincronização concluída! {m_count} meses verificados, {up_count} registros atualizados {status_cloud}")
