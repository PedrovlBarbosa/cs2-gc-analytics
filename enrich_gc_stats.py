import os
import sys
import time
import sqlite3
from typing import Optional

# Garante UTF-8 no Windows
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass

from collector import load_config, GamersClubCollector
from database import DB_PATH, init_db

def enrich_gc_matches(limit: Optional[int] = None, verbose: bool = True) -> int:
    """
    Busca e enriquece partidas da Gamers Club com as novas estatísticas detalhadas
    (Entries, Trades, Clutch, Utilitárias, Mira e Rating GC).
    Começa pelas partidas mais recentes.
    """
    init_db()
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # Seleciona partidas da GC que ainda não têm dados no scoreboard
    query = """
    SELECT DISTINCT m.match_id, m.month
    FROM matches m
    WHERE m.platform = 'GC'
      AND m.match_id NOT IN (SELECT DISTINCT match_id FROM gc_match_scoreboard)
    ORDER BY m.month DESC, m.match_id DESC
    """
    if limit:
        query += f" LIMIT {limit}"
        
    matches_to_enrich = cursor.execute(query).fetchall()
    conn.close()
    
    if not matches_to_enrich:
        if verbose:
            print("✅ Todas as partidas recentes da Gamers Club já estão com as novas estatísticas em dia!")
        return 0

    if verbose:
        print(f"⚡ Verificando novas estatísticas da GC para {len(matches_to_enrich)} partidas recentes...")

    cfg = load_config()
    collector = GamersClubCollector(cfg)

    enriched_count = 0
    consecutive_unavailable = 0

    for i, (mid, month) in enumerate(matches_to_enrich, 1):
        try:
            ok = collector.fetch_and_save_gc_match_stats(str(mid))
            if ok:
                enriched_count += 1
                consecutive_unavailable = 0
                if verbose:
                    print(f"  [{i}/{len(matches_to_enrich)}] Partida {mid} ({month}) -> 🎯 Enriquecida!")
            else:
                consecutive_unavailable += 1
                if verbose and consecutive_unavailable <= 5:
                    print(f"  [{i}/{len(matches_to_enrich)}] Partida {mid} ({month}) -> Estatísticas indisponíveis na GC")
            
            time.sleep(0.05)
            
            # Se encontrar 10 partidas consecutivas indisponíveis, são partidas anteriores à atualização da GC
            if consecutive_unavailable >= 10:
                if verbose:
                    print("ℹ️ Partidas restantes são anteriores ao lançamento dessa novidade na Gamers Club.")
                break
        except Exception as e:
            if verbose:
                print(f"  Erro na partida {mid}: {e}")

    if verbose:
        print(f"\n🎉 Concluído! {enriched_count} partidas novas enriquecidas com as novas estatísticas da GC.")
    return enriched_count

if __name__ == "__main__":
    lim = int(sys.argv[1]) if len(sys.argv) > 1 else None
    enrich_gc_matches(limit=lim, verbose=True)
