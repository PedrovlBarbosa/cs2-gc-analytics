import os
import sys
import time
import subprocess
from datetime import datetime

# Garante suporte a UTF-8 no terminal Windows
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass
from collector import load_config, GamersClubCollector
from database import (
    save_monthly_stats,
    save_matches,
    get_known_match_ids,
    get_all_months,
    CORE_PLAYERS
)

TARGET_PLAYERS = {
    'KrannDy': 108698,
    'Aquarista': 87484,
    'Art': 108939,
    'Cherki': 540777,
    'Death': 318687,
    'Kinha': 108940,
    'mch': 89302
}

def push_to_github() -> bool:
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

def get_target_months() -> list:
    """Determina quais meses verificar. Por padrão o mês atual, e se início do mês, inclui o anterior."""
    now = datetime.now()
    cur_m = now.strftime("%Y-%m")
    target = [cur_m]
    
    # Se estiver nos primeiros 3 dias do mês, também verifica o mês anterior por precaução
    if now.day <= 3:
        # Calcula mês anterior
        prev_year = now.year if now.month > 1 else now.year - 1
        prev_month = now.month - 1 if now.month > 1 else 12
        prev_m = f"{prev_year:04d}-{prev_month:02d}"
        target.append(prev_m)
        
    return target

def sync_recent(months_count=None, auto_push=True):
    """
    Sincronização INTELIGENTE e ULTRA-RÁPIDA:
    Busca apenas os jogos novos que ainda não estão no banco de dados.
    Para imediatamente assim que encontra a primeira partida já conhecida.
    """
    start_time = time.time()
    cfg = load_config()
    collector = GamersClubCollector(cfg)

    target_months = get_target_months()
    print(f"⚡ Verificando jogos novos para os 7 jogadores ({', '.join(target_months)})...")

    total_new_matches = 0
    updated_players = set()

    for m in target_months:
        for nick, pid in TARGET_PLAYERS.items():
            known_ids = get_known_match_ids(pid, m)
            new_matches = collector.fetch_new_matches(pid, m, known_ids)

            if new_matches:
                save_matches(new_matches)
                total_new_matches += len(new_matches)
                updated_players.add((nick, pid, m))
                print(f"  [+] {nick:10s} -> {len(new_matches)} nova(s) partida(s) adicionada(s)!")
            else:
                print(f"  [-] {nick:10s} -> em dia (0 novas partidas).")
            
            time.sleep(0.02)

    # Se encontramos partidas novas, atualizamos o resumo consolidado do mês correspondente
    if updated_players:
        print(f"\n📊 Atualizando estatísticas acumuladas do mês...")
        for nick, pid, m in updated_players:
            stats = collector.fetch_player_month_stats(pid, m)
            if stats:
                save_monthly_stats(stats)
            time.sleep(0.02)

    elapsed = round(time.time() - start_time, 1)

    pushed = False
    if total_new_matches > 0:
        if auto_push and not os.environ.get("GITHUB_ACTIONS"):
            print("🚀 Enviando atualizações para o GitHub...")
            pushed = push_to_github()
        status_pub = "e enviado para o GitHub!" if pushed else ""
        print(f"\n✨ Finalizado em {elapsed}s! Total de {total_new_matches} partida(s) nova(s) sincronizada(s) {status_pub}")
    else:
        print(f"\n✨ Tudo 100% atualizado em {elapsed}s! Nenhuma partida nova pendente.")

    return len(target_months), total_new_matches, pushed

if __name__ == "__main__":
    sync_recent(auto_push=True)
