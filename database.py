import sqlite3
import pandas as pd
from typing import List, Dict, Any, Optional

DB_PATH = "gc_stats.db"

CORE_PLAYERS = [
    'KrannDy', 'Aquarista', 'Art', 'Cherki', 'Death', 'Kinha', 'mch',
    'The merdas', 'Coquinha', 'Allan Daniel', 'Daniel'
]

def get_connection(db_path: str = DB_PATH) -> sqlite3.Connection:
    conn = sqlite3.connect(db_path, timeout=30.0, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    try:
        conn.execute("PRAGMA journal_mode=WAL;")
        conn.execute("PRAGMA synchronous=NORMAL;")
        conn.execute("PRAGMA cache_size=-64000;")
    except Exception:
        pass
    return conn

def init_db(db_path: str = DB_PATH):
    conn = get_connection(db_path)
    cursor = conn.cursor()

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS players (
        player_id INTEGER PRIMARY KEY,
        nick TEXT NOT NULL,
        level INTEGER,
        is_main_user BOOLEAN DEFAULT 0,
        avatar_url TEXT,
        steam_id TEXT,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS monthly_stats (
        player_id INTEGER,
        month TEXT,
        platform TEXT DEFAULT 'GC',
        matches INTEGER DEFAULT 0,
        wins INTEGER DEFAULT 0,
        loss INTEGER DEFAULT 0,
        win_rate REAL DEFAULT 0,
        kdr REAL DEFAULT 0,
        adr REAL DEFAULT 0,
        kills INTEGER DEFAULT 0,
        deaths INTEGER DEFAULT 0,
        kast_percent REAL DEFAULT 0,
        multi_kills INTEGER DEFAULT 0,
        first_kills INTEGER DEFAULT 0,
        hs_percent REAL DEFAULT 0,
        bomb_plants INTEGER DEFAULT 0,
        bomb_defuses INTEGER DEFAULT 0,
        hitbox_head INTEGER DEFAULT 0,
        hitbox_chest INTEGER DEFAULT 0,
        hitbox_stomach INTEGER DEFAULT 0,
        hitbox_arms INTEGER DEFAULT 0,
        hitbox_legs INTEGER DEFAULT 0,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        PRIMARY KEY (player_id, month, platform),
        FOREIGN KEY (player_id) REFERENCES players (player_id)
    )
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS matches (
        match_id TEXT,
        player_id INTEGER,
        month TEXT,
        team_name_a TEXT,
        score_a INTEGER,
        team_name_b TEXT,
        score_b INTEGER,
        win INTEGER,
        rating_player INTEGER,
        rating_diff INTEGER,
        map TEXT,
        match_type TEXT,
        platform TEXT DEFAULT 'GC',
        kills INTEGER DEFAULT 0,
        deaths INTEGER DEFAULT 0,
        adr REAL DEFAULT 0.0,
        hs_percent REAL DEFAULT 0.0,
        leetify_rating REAL DEFAULT 0.0,
        ct_leetify_rating REAL DEFAULT 0.0,
        t_leetify_rating REAL DEFAULT 0.0,
        reaction_time REAL DEFAULT 0.0,
        preaim REAL DEFAULT 0.0,
        spray_accuracy REAL DEFAULT 0.0,
        counter_strafe_pct REAL DEFAULT 0.0,
        trade_kill_pct REAL DEFAULT 0.0,
        traded_death_pct REAL DEFAULT 0.0,
        flash_duration_avg REAL DEFAULT 0.0,
        he_damage_avg REAL DEFAULT 0.0,
        utility_on_death_avg REAL DEFAULT 0.0,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        PRIMARY KEY (match_id, player_id),
        FOREIGN KEY (player_id) REFERENCES players (player_id)
    )
    """)

    # Migrações automáticas para bancos existentes
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS gc_match_scoreboard (
        match_id TEXT,
        player_id INTEGER,
        nick TEXT,
        level INTEGER,
        avatar_url TEXT,
        team TEXT,
        team_name TEXT,
        is_core_squad INTEGER DEFAULT 0,
        gc_rating REAL DEFAULT 0.0,
        round_swing REAL DEFAULT 0.0,
        kills INTEGER DEFAULT 0,
        assists INTEGER DEFAULT 0,
        deaths INTEGER DEFAULT 0,
        adr REAL DEFAULT 0.0,
        kdr REAL DEFAULT 0.0,
        kast REAL DEFAULT 0.0,
        entry_duels INTEGER DEFAULT 0,
        entry_won INTEGER DEFAULT 0,
        entry_lost INTEGER DEFAULT 0,
        entry_success_rate REAL DEFAULT 0.0,
        entry_per_round REAL DEFAULT 0.0,
        trades_made INTEGER DEFAULT 0,
        traded_deaths INTEGER DEFAULT 0,
        trade_rate REAL DEFAULT 0.0,
        trade_avg_time REAL DEFAULT 0.0,
        clutch_situations INTEGER DEFAULT 0,
        clutch_won INTEGER DEFAULT 0,
        clutch_rate REAL DEFAULT 0.0,
        clutch_1v1_won INTEGER DEFAULT 0,
        clutch_1v1_total INTEGER DEFAULT 0,
        clutch_1vn_won INTEGER DEFAULT 0,
        clutch_1vn_total INTEGER DEFAULT 0,
        clutch_biggest TEXT DEFAULT '-',
        utility_damage INTEGER DEFAULT 0,
        flash_assists INTEGER DEFAULT 0,
        enemies_flashed INTEGER DEFAULT 0,
        grenades_thrown INTEGER DEFAULT 0,
        damage_per_grenade REAL DEFAULT 0.0,
        aim_accuracy REAL DEFAULT 0.0,
        aim_hs_rate REAL DEFAULT 0.0,
        aim_head_acc REAL DEFAULT 0.0,
        aim_kpr REAL DEFAULT 0.0,
        main_weapon TEXT DEFAULT '',
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        PRIMARY KEY (match_id, player_id)
    )
    """)

    cursor.execute("PRAGMA table_info(matches)")
    existing_match_cols = {row[1] for row in cursor.fetchall()}
    match_migrations = {
        "leetify_rating": "REAL DEFAULT 0.0",
        "ct_leetify_rating": "REAL DEFAULT 0.0",
        "t_leetify_rating": "REAL DEFAULT 0.0",
        "reaction_time": "REAL DEFAULT 0.0",
        "preaim": "REAL DEFAULT 0.0",
        "spray_accuracy": "REAL DEFAULT 0.0",
        "counter_strafe_pct": "REAL DEFAULT 0.0",
        "trade_kill_pct": "REAL DEFAULT 0.0",
        "traded_death_pct": "REAL DEFAULT 0.0",
        "flash_duration_avg": "REAL DEFAULT 0.0",
        "he_damage_avg": "REAL DEFAULT 0.0",
        "utility_on_death_avg": "REAL DEFAULT 0.0",
        # Novas estatísticas nativas da Gamers Club
        "entry_duels": "INTEGER DEFAULT 0",
        "entry_won": "INTEGER DEFAULT 0",
        "entry_lost": "INTEGER DEFAULT 0",
        "entry_success_rate": "REAL DEFAULT 0.0",
        "entry_per_round": "REAL DEFAULT 0.0",
        "trades_made": "INTEGER DEFAULT 0",
        "traded_deaths": "INTEGER DEFAULT 0",
        "trade_rate": "REAL DEFAULT 0.0",
        "trade_avg_time": "REAL DEFAULT 0.0",
        "clutch_situations": "INTEGER DEFAULT 0",
        "clutch_won": "INTEGER DEFAULT 0",
        "clutch_rate": "REAL DEFAULT 0.0",
        "clutch_1v1_won": "INTEGER DEFAULT 0",
        "clutch_1v1_total": "INTEGER DEFAULT 0",
        "clutch_1vn_won": "INTEGER DEFAULT 0",
        "clutch_1vn_total": "INTEGER DEFAULT 0",
        "clutch_biggest": "TEXT DEFAULT '-'",
        "utility_damage": "INTEGER DEFAULT 0",
        "flash_assists": "INTEGER DEFAULT 0",
        "enemies_flashed": "INTEGER DEFAULT 0",
        "grenades_thrown": "INTEGER DEFAULT 0",
        "damage_per_grenade": "REAL DEFAULT 0.0",
        "aim_accuracy": "REAL DEFAULT 0.0",
        "aim_hs_rate": "REAL DEFAULT 0.0",
        "aim_head_acc": "REAL DEFAULT 0.0",
        "aim_kpr": "REAL DEFAULT 0.0",
        "main_weapon": "TEXT DEFAULT ''",
        "gc_rating": "REAL DEFAULT 0.0",
        "round_swing": "REAL DEFAULT 0.0"
    }
    for col, c_type in match_migrations.items():
        if col not in existing_match_cols:
            cursor.execute(f"ALTER TABLE matches ADD COLUMN {col} {c_type}")

    cursor.execute("PRAGMA table_info(monthly_stats)")
    existing_m_cols = {row[1] for row in cursor.fetchall()}
    monthly_migrations = {
        "leetify_rating": "REAL DEFAULT 0.0",
        "reaction_time": "REAL DEFAULT 0.0",
        "preaim": "REAL DEFAULT 0.0",
        "spray_accuracy": "REAL DEFAULT 0.0",
        "counter_strafe_pct": "REAL DEFAULT 0.0",
        "trade_kill_pct": "REAL DEFAULT 0.0",
        "flash_duration_avg": "REAL DEFAULT 0.0",
        "utility_on_death_avg": "REAL DEFAULT 0.0"
    }
    for col, c_type in monthly_migrations.items():
        if col not in existing_m_cols:
            cursor.execute(f"ALTER TABLE monthly_stats ADD COLUMN {col} {c_type}")

    # Índices para acelerar drasticamente consultas e filtros
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_matches_player_month_plat ON matches(player_id, month, platform);")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_matches_match_id ON matches(match_id);")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_matches_platform ON matches(platform);")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_monthly_stats_plat_month ON monthly_stats(platform, month);")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_gc_scoreboard_mid ON gc_match_scoreboard(match_id);")

    conn.commit()
    conn.close()

def get_known_match_ids(player_id: int, month = None, db_path: str = DB_PATH) -> set:
    """Retorna o conjunto de IDs de partidas já salvas no banco para o jogador."""
    conn = get_connection(db_path)
    cursor = conn.cursor()
    if month:
        cursor.execute("SELECT match_id FROM matches WHERE player_id = ? AND month = ?", (player_id, month))
    else:
        cursor.execute("SELECT match_id FROM matches WHERE player_id = ?", (player_id,))
    rows = cursor.fetchall()
    conn.close()
    result = set()
    for row in rows:
        val = row[0]
        result.add(val)
        result.add(str(val))
        try:
            result.add(int(val))
        except (ValueError, TypeError):
            pass
    return result

def save_player(player: Dict[str, Any], db_path: str = DB_PATH):
    conn = get_connection(db_path)
    cursor = conn.cursor()
    cursor.execute("""
    INSERT INTO players (player_id, nick, level, is_main_user, avatar_url, steam_id, updated_at)
    VALUES (?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
    ON CONFLICT(player_id) DO UPDATE SET
        nick = excluded.nick,
        level = COALESCE(excluded.level, players.level),
        is_main_user = excluded.is_main_user,
        avatar_url = excluded.avatar_url,
        steam_id = COALESCE(excluded.steam_id, players.steam_id),
        updated_at = CURRENT_TIMESTAMP
    """, (
        player["player_id"],
        player["nick"],
        player.get("level"),
        player.get("is_main_user", 0),
        player.get("avatar_url", ""),
        player.get("steam_id")
    ))
    conn.commit()
    conn.close()

def save_monthly_stats(stats: Dict[str, Any], db_path: str = DB_PATH):
    conn = get_connection(db_path)
    cursor = conn.cursor()
    cursor.execute("""
    INSERT INTO monthly_stats (
        player_id, month, platform, matches, wins, loss, win_rate, kdr, adr,
        kills, deaths, kast_percent, multi_kills, first_kills, hs_percent,
        bomb_plants, bomb_defuses, hitbox_head, hitbox_chest, hitbox_stomach,
        hitbox_arms, hitbox_legs, updated_at
    )
    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
    ON CONFLICT(player_id, month, platform) DO UPDATE SET
        matches = excluded.matches,
        wins = excluded.wins,
        loss = excluded.loss,
        win_rate = excluded.win_rate,
        kdr = excluded.kdr,
        adr = excluded.adr,
        kills = excluded.kills,
        deaths = excluded.deaths,
        kast_percent = excluded.kast_percent,
        multi_kills = excluded.multi_kills,
        first_kills = excluded.first_kills,
        hs_percent = excluded.hs_percent,
        bomb_plants = excluded.bomb_plants,
        bomb_defuses = excluded.bomb_defuses,
        hitbox_head = excluded.hitbox_head,
        hitbox_chest = excluded.hitbox_chest,
        hitbox_stomach = excluded.hitbox_stomach,
        hitbox_arms = excluded.hitbox_arms,
        hitbox_legs = excluded.hitbox_legs,
        updated_at = CURRENT_TIMESTAMP
    """, (
        stats["player_id"],
        stats["month"],
        stats.get("platform", "GC"),
        stats.get("matches", 0),
        stats.get("wins", 0),
        stats.get("loss", 0),
        stats.get("win_rate", 0.0),
        stats.get("kdr", 0.0),
        stats.get("adr", 0.0),
        stats.get("kills", 0),
        stats.get("deaths", 0),
        stats.get("kast_percent", 0.0),
        stats.get("multi_kills", 0),
        stats.get("first_kills", 0),
        stats.get("hs_percent", 0.0),
        stats.get("bomb_plants", 0),
        stats.get("bomb_defuses", 0),
        stats.get("hitbox_head", 0),
        stats.get("hitbox_chest", 0),
        stats.get("hitbox_stomach", 0),
        stats.get("hitbox_arms", 0),
        stats.get("hitbox_legs", 0)
    ))
    conn.commit()
    conn.close()

def save_matches(matches_list: List[Dict[str, Any]], db_path: str = DB_PATH):
    if not matches_list:
        return
    conn = get_connection(db_path)
    cursor = conn.cursor()
    for m in matches_list:
        cursor.execute("""
        INSERT INTO matches (
            match_id, player_id, month, team_name_a, score_a,
            team_name_b, score_b, win, rating_player, rating_diff,
            map, match_type, platform, kills, deaths, adr, hs_percent,
            leetify_rating, ct_leetify_rating, t_leetify_rating,
            reaction_time, preaim, spray_accuracy, counter_strafe_pct,
            trade_kill_pct, traded_death_pct, flash_duration_avg,
            he_damage_avg, utility_on_death_avg, updated_at
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
        ON CONFLICT(match_id, player_id) DO UPDATE SET
            month = excluded.month,
            team_name_a = excluded.team_name_a,
            score_a = excluded.score_a,
            team_name_b = excluded.team_name_b,
            score_b = excluded.score_b,
            win = excluded.win,
            rating_player = excluded.rating_player,
            rating_diff = excluded.rating_diff,
            map = excluded.map,
            match_type = excluded.match_type,
            platform = excluded.platform,
            kills = CASE WHEN excluded.kills > 0 THEN excluded.kills ELSE matches.kills END,
            deaths = CASE WHEN excluded.deaths > 0 THEN excluded.deaths ELSE matches.deaths END,
            adr = CASE WHEN excluded.adr > 0.0 THEN excluded.adr ELSE matches.adr END,
            hs_percent = CASE WHEN excluded.hs_percent > 0.0 THEN excluded.hs_percent ELSE matches.hs_percent END,
            leetify_rating = CASE WHEN excluded.leetify_rating != 0.0 THEN excluded.leetify_rating ELSE matches.leetify_rating END,
            ct_leetify_rating = CASE WHEN excluded.ct_leetify_rating != 0.0 THEN excluded.ct_leetify_rating ELSE matches.ct_leetify_rating END,
            t_leetify_rating = CASE WHEN excluded.t_leetify_rating != 0.0 THEN excluded.t_leetify_rating ELSE matches.t_leetify_rating END,
            reaction_time = CASE WHEN excluded.reaction_time > 0.0 THEN excluded.reaction_time ELSE matches.reaction_time END,
            preaim = CASE WHEN excluded.preaim > 0.0 THEN excluded.preaim ELSE matches.preaim END,
            spray_accuracy = CASE WHEN excluded.spray_accuracy > 0.0 THEN excluded.spray_accuracy ELSE matches.spray_accuracy END,
            counter_strafe_pct = CASE WHEN excluded.counter_strafe_pct > 0.0 THEN excluded.counter_strafe_pct ELSE matches.counter_strafe_pct END,
            trade_kill_pct = CASE WHEN excluded.trade_kill_pct > 0.0 THEN excluded.trade_kill_pct ELSE matches.trade_kill_pct END,
            traded_death_pct = CASE WHEN excluded.traded_death_pct > 0.0 THEN excluded.traded_death_pct ELSE matches.traded_death_pct END,
            flash_duration_avg = CASE WHEN excluded.flash_duration_avg > 0.0 THEN excluded.flash_duration_avg ELSE matches.flash_duration_avg END,
            he_damage_avg = CASE WHEN excluded.he_damage_avg > 0.0 THEN excluded.he_damage_avg ELSE matches.he_damage_avg END,
            utility_on_death_avg = CASE WHEN excluded.utility_on_death_avg > 0.0 THEN excluded.utility_on_death_avg ELSE matches.utility_on_death_avg END,
            updated_at = CURRENT_TIMESTAMP
        """, (
            str(m["match_id"]),
            m["player_id"],
            m["month"],
            m.get("team_name_a", ""),
            m.get("score_a", 0),
            m.get("team_name_b", ""),
            m.get("score_b", 0),
            m.get("win", 0),
            m.get("rating_player", 0),
            m.get("rating_diff", 0),
            m.get("map", ""),
            m.get("match_type", "lobby"),
            m.get("platform", "GC"),
            m.get("kills", 0),
            m.get("deaths", 0),
            m.get("adr", 0.0),
            m.get("hs_percent", 0.0),
            m.get("leetify_rating", 0.0),
            m.get("ct_leetify_rating", 0.0),
            m.get("t_leetify_rating", 0.0),
            m.get("reaction_time", 0.0),
            m.get("preaim", 0.0),
            m.get("spray_accuracy", 0.0),
            m.get("counter_strafe_pct", 0.0),
            m.get("trade_kill_pct", 0.0),
            m.get("traded_death_pct", 0.0),
            m.get("flash_duration_avg", 0.0),
            m.get("he_damage_avg", 0.0),
            m.get("utility_on_death_avg", 0.0)
        ))
    conn.commit()
    conn.close()

def enrich_gc_match_telemetry(match_id: str, player_id: int, telemetry: Dict[str, Any], db_path: str = DB_PATH):
    """
    Enriquece com segurança uma partida da Gamers Club apenas com as métricas telemétricas da Leetify,
    sem alterar em hipótese alguma o placar original (score_a/score_b), vitória/derrota (win) ou ratings da GC.
    """
    conn = get_connection(db_path)
    cursor = conn.cursor()
    cursor.execute("""
    UPDATE matches SET
        kills = CASE WHEN ? > 0 THEN ? ELSE kills END,
        deaths = CASE WHEN ? > 0 THEN ? ELSE deaths END,
        adr = CASE WHEN ? > 0.0 THEN ? ELSE adr END,
        hs_percent = CASE WHEN ? > 0.0 THEN ? ELSE hs_percent END,
        leetify_rating = CASE WHEN ? != 0.0 THEN ? ELSE leetify_rating END,
        ct_leetify_rating = CASE WHEN ? != 0.0 THEN ? ELSE ct_leetify_rating END,
        t_leetify_rating = CASE WHEN ? != 0.0 THEN ? ELSE t_leetify_rating END,
        reaction_time = CASE WHEN ? > 0.0 THEN ? ELSE reaction_time END,
        preaim = CASE WHEN ? > 0.0 THEN ? ELSE preaim END,
        spray_accuracy = CASE WHEN ? > 0.0 THEN ? ELSE spray_accuracy END,
        counter_strafe_pct = CASE WHEN ? > 0.0 THEN ? ELSE counter_strafe_pct END,
        trade_kill_pct = CASE WHEN ? > 0.0 THEN ? ELSE trade_kill_pct END,
        traded_death_pct = CASE WHEN ? > 0.0 THEN ? ELSE traded_death_pct END,
        flash_duration_avg = CASE WHEN ? > 0.0 THEN ? ELSE flash_duration_avg END,
        he_damage_avg = CASE WHEN ? > 0.0 THEN ? ELSE he_damage_avg END,
        utility_on_death_avg = CASE WHEN ? > 0.0 THEN ? ELSE utility_on_death_avg END,
        updated_at = CURRENT_TIMESTAMP
    WHERE match_id = ? AND player_id = ?
    """, (
        telemetry.get("kills", 0), telemetry.get("kills", 0),
        telemetry.get("deaths", 0), telemetry.get("deaths", 0),
        telemetry.get("adr", 0.0), telemetry.get("adr", 0.0),
        telemetry.get("hs_percent", 0.0), telemetry.get("hs_percent", 0.0),
        telemetry.get("leetify_rating", 0.0), telemetry.get("leetify_rating", 0.0),
        telemetry.get("ct_leetify_rating", 0.0), telemetry.get("ct_leetify_rating", 0.0),
        telemetry.get("t_leetify_rating", 0.0), telemetry.get("t_leetify_rating", 0.0),
        telemetry.get("reaction_time", 0.0), telemetry.get("reaction_time", 0.0),
        telemetry.get("preaim", 0.0), telemetry.get("preaim", 0.0),
        telemetry.get("spray_accuracy", 0.0), telemetry.get("spray_accuracy", 0.0),
        telemetry.get("counter_strafe_pct", 0.0), telemetry.get("counter_strafe_pct", 0.0),
        telemetry.get("trade_kill_pct", 0.0), telemetry.get("trade_kill_pct", 0.0),
        telemetry.get("traded_death_pct", 0.0), telemetry.get("traded_death_pct", 0.0),
        telemetry.get("flash_duration_avg", 0.0), telemetry.get("flash_duration_avg", 0.0),
        telemetry.get("he_damage_avg", 0.0), telemetry.get("he_damage_avg", 0.0),
        telemetry.get("utility_on_death_avg", 0.0), telemetry.get("utility_on_death_avg", 0.0),
        str(match_id), player_id
    ))
    conn.commit()
    conn.close()

def get_all_players(db_path: str = DB_PATH) -> pd.DataFrame:
    conn = get_connection(db_path)
    df = pd.read_sql_query("SELECT * FROM players ORDER BY is_main_user DESC, nick ASC", conn)
    conn.close()
    return df

def get_all_months(*args, **kwargs) -> List[str]:
    """Retorna lista de meses distintos. Suporta db_path e platform em qualquer ordem."""
    platform = kwargs.get("platform", "TODOS")
    db_path = kwargs.get("db_path", DB_PATH)
    if args:
        if isinstance(args[0], str) and (args[0].endswith(".db") or "/" in args[0] or "\\" in args[0]):
            db_path = args[0]
            if len(args) > 1:
                platform = args[1]
        else:
            platform = args[0]
            if len(args) > 1:
                db_path = args[1]
                
    conn = get_connection(db_path)
    cursor = conn.cursor()
    if platform and platform.upper() != "TODOS":
        cursor.execute("SELECT DISTINCT month FROM monthly_stats WHERE platform = ? ORDER BY month DESC", (platform.upper(),))
    else:
        cursor.execute("SELECT DISTINCT month FROM monthly_stats ORDER BY month DESC")
    rows = cursor.fetchall()
    conn.close()
    return [r[0] for r in rows]

def get_core_players_stats(month: Optional[str] = None, platform: str = "TODOS", db_path: str = DB_PATH, **kwargs) -> pd.DataFrame:
    """
    Retorna as estatísticas consolidadas dos 7 jogadores principais.
    Suporta filtro por mês e por plataforma ('TODOS', 'GC', 'STEAM').
    """
    conn = get_connection(db_path)
    placeholders = ",".join(["?" for _ in CORE_PLAYERS])
    
    conditions = [f"p.nick IN ({placeholders})", "s.matches > 0"]
    params = list(CORE_PLAYERS)
    
    if month and month != "Todos":
        conditions.append("s.month = ?")
        params.append(month)
        
    if platform and platform.upper() != "TODOS":
        conditions.append("s.platform = ?")
        params.append(platform.upper())
        
    where_clause = " AND ".join(conditions)
    
    query = f"""
    SELECT 
        p.nick,
        p.player_id,
        p.level,
        p.is_main_user,
        p.steam_id,
        SUM(s.matches) as matches,
        SUM(s.wins) as wins,
        SUM(s.loss) as loss,
        ROUND(CAST(SUM(s.wins) AS FLOAT) / NULLIF(SUM(s.matches), 0) * 100, 1) as win_rate,
        SUM(s.kills) as kills,
        SUM(s.deaths) as deaths,
        ROUND(CAST(SUM(s.kills) AS FLOAT) / NULLIF(SUM(s.deaths), 0), 2) as kdr,
        ROUND(SUM(s.adr * s.matches) / NULLIF(SUM(s.matches), 0), 1) as adr,
        ROUND(SUM(s.kast_percent * s.matches) / NULLIF(SUM(s.matches), 0), 1) as kast_percent,
        ROUND(SUM(s.hs_percent * s.matches) / NULLIF(SUM(s.matches), 0), 1) as hs_percent,
        SUM(s.first_kills) as first_kills,
        SUM(s.multi_kills) as multi_kills,
        SUM(s.bomb_plants) as bomb_plants,
        SUM(s.bomb_defuses) as bomb_defuses,
        SUM(s.hitbox_head) as hitbox_head,
        SUM(s.hitbox_chest) as hitbox_chest,
        SUM(s.hitbox_stomach) as hitbox_stomach,
        SUM(s.hitbox_arms) as hitbox_arms,
        SUM(s.hitbox_legs) as hitbox_legs
    FROM players p
    JOIN monthly_stats s ON p.player_id = s.player_id
    WHERE {where_clause}
    GROUP BY p.nick, p.player_id, p.level, p.is_main_user
    ORDER BY kdr DESC, adr DESC, matches DESC
    """
    df = pd.read_sql_query(query, conn, params=params)
    conn.close()
    return df

def get_core_squad_totals(month: Optional[str] = None, platform: str = "TODOS", db_path: str = DB_PATH, **kwargs) -> Dict[str, Any]:
    """Calcula os totais e médias somadas do conjunto dos 7 jogadores."""
    default_empty = {
        "players_count": 0,
        "unique_matches": 0,
        "unique_wins": 0,
        "unique_loss": 0,
        "unique_win_rate": 0.0,
        "total_matches": 0,
        "total_wins": 0,
        "total_loss": 0,
        "win_rate": 0.0,
        "total_participations": 0,
        "total_kills": 0,
        "total_deaths": 0,
        "kdr": 0.0,
        "adr": 0.0,
        "first_kills": 0,
        "multi_kills": 0,
        "bomb_plants": 0,
        "bomb_defuses": 0,
        "hitbox_head": 0,
        "hitbox_chest": 0,
        "hitbox_stomach": 0,
        "hitbox_arms": 0,
        "hitbox_legs": 0
    }

    df = get_core_players_stats(month=month, platform=platform, db_path=db_path)
    if df.empty:
        return default_empty

    conn = get_connection(db_path)
    conds = []
    params = []
    if month and month != "Todos":
        conds.append("month = ?")
        params.append(month)
    if platform and platform.upper() != "TODOS":
        conds.append("platform = ?")
        params.append(platform.upper())
    where_c = " WHERE " + " AND ".join(conds) if conds else ""
    q = f"SELECT match_id, MAX(win) as win FROM matches {where_c} GROUP BY match_id"
    u_df = pd.read_sql_query(q, conn, params=params)
    conn.close()

    total_matches_participations = int(df["matches"].sum())
    unique_matches = len(u_df) if not u_df.empty else total_matches_participations
    unique_wins = int(u_df["win"].sum()) if not u_df.empty else int(df["wins"].sum())
    unique_loss = unique_matches - unique_wins
    unique_win_rate = round((unique_wins / unique_matches * 100), 1) if unique_matches > 0 else 0.0

    total_kills = int(df["kills"].sum())
    total_deaths = int(df["deaths"].sum())
    kdr = round(total_kills / total_deaths, 2) if total_deaths > 0 else 0.0

    # ADR ponderado do squad
    adr = round((df["adr"] * df["matches"]).sum() / total_matches_participations, 1) if total_matches_participations > 0 else 0.0

    return {
        "players_count": len(df),
        "unique_matches": unique_matches,
        "unique_wins": unique_wins,
        "unique_loss": unique_loss,
        "unique_win_rate": unique_win_rate,
        "total_matches": unique_matches,
        "total_wins": unique_wins,
        "total_loss": unique_loss,
        "win_rate": unique_win_rate,
        "total_participations": total_matches_participations,
        "total_kills": total_kills,
        "total_deaths": total_deaths,
        "kdr": kdr,
        "adr": adr,
        "first_kills": int(df["first_kills"].sum()),
        "multi_kills": int(df["multi_kills"].sum()),
        "bomb_plants": int(df["bomb_plants"].sum()),
        "bomb_defuses": int(df["bomb_defuses"].sum()),
        "hitbox_head": int(df["hitbox_head"].sum()),
        "hitbox_chest": int(df["hitbox_chest"].sum()),
        "hitbox_stomach": int(df["hitbox_stomach"].sum()),
        "hitbox_arms": int(df["hitbox_arms"].sum()),
        "hitbox_legs": int(df["hitbox_legs"].sum())
    }

def get_player_history(player_id: int, platform: str = "TODOS", db_path: str = DB_PATH, **kwargs) -> pd.DataFrame:
    conn = get_connection(db_path)
    conds = ["player_id = ?", "matches > 0"]
    params = [player_id]
    if platform and platform.upper() != "TODOS":
        conds.append("platform = ?")
        params.append(platform.upper())
    where_c = " AND ".join(conds)
    query = f"""
    SELECT 
        player_id, month,
        SUM(matches) as matches,
        SUM(wins) as wins,
        SUM(loss) as loss,
        ROUND(CAST(SUM(wins) AS FLOAT) / NULLIF(SUM(matches), 0) * 100, 1) as win_rate,
        ROUND(CAST(SUM(kills) AS FLOAT) / NULLIF(SUM(deaths), 0), 2) as kdr,
        ROUND(SUM(adr * matches) / NULLIF(SUM(matches), 0), 1) as adr,
        SUM(kills) as kills,
        SUM(deaths) as deaths,
        ROUND(SUM(kast_percent * matches) / NULLIF(SUM(matches), 0), 1) as kast_percent,
        ROUND(SUM(hs_percent * matches) / NULLIF(SUM(matches), 0), 1) as hs_percent
    FROM monthly_stats
    WHERE {where_c}
    GROUP BY player_id, month
    ORDER BY month ASC
    """
    df = pd.read_sql_query(query, conn, params=params)
    conn.close()
    return df

def get_matches_by_month(month: Optional[str] = None, player_id: Optional[int] = None, platform: str = "TODOS", db_path: str = DB_PATH, **kwargs) -> pd.DataFrame:
    conn = get_connection(db_path)
    conditions = []
    params = []
    if month and month != "Todos":
        conditions.append("m.month = ?")
        params.append(month)
    if player_id:
        conditions.append("m.player_id = ?")
        params.append(player_id)
    if platform and platform.upper() != "TODOS":
        conditions.append("m.platform = ?")
        params.append(platform.upper())
        
    where_clause = " WHERE " + " AND ".join(conditions) if conditions else ""
    query = f"""
    SELECT m.*, p.nick as player_nick 
    FROM matches m 
    LEFT JOIN players p ON m.player_id = p.player_id 
    {where_clause} 
    ORDER BY m.month DESC, m.match_id DESC
    """
    df = pd.read_sql_query(query, conn, params=params)
    conn.close()
    return df


def get_map_stats_by_player(
    month: Optional[str] = None,
    player_id: Optional[int] = None,
    platform: str = "TODOS",
    db_path: str = DB_PATH,
    **kwargs
) -> pd.DataFrame:
    """
    Retorna as estatísticas detalhadas por mapa para um ou todos os jogadores do Core Squad.
    Calcula: partidas, vitórias, derrotas, win_rate, kills, deaths, kdr, adr, kills_per_match e hs_percent.
    """
    conn = get_connection(db_path)
    conditions = ["m.map IS NOT NULL", "m.map != ''"]
    params = []
    
    if player_id:
        conditions.append("m.player_id = ?")
        params.append(player_id)
    else:
        placeholders = ",".join(["?" for _ in CORE_PLAYERS])
        conditions.append(f"p.nick IN ({placeholders})")
        params.extend(list(CORE_PLAYERS))
        
    if month and month != "Todos":
        conditions.append("m.month = ?")
        params.append(month)
        
    if platform and platform.upper() != "TODOS":
        conditions.append("m.platform = ?")
        params.append(platform.upper())
        
    where_c = " AND ".join(conditions)
    
    query = f"""
    SELECT 
        p.nick,
        p.player_id,
        m.map,
        COUNT(m.match_id) as matches,
        SUM(m.win) as wins,
        COUNT(m.match_id) - SUM(m.win) as losses,
        ROUND(CAST(SUM(m.win) AS FLOAT) / COUNT(m.match_id) * 100, 1) as win_rate,
        SUM(m.kills) as kills,
        SUM(m.deaths) as deaths,
        ROUND(CAST(SUM(m.kills) AS FLOAT) / NULLIF(SUM(m.deaths), 0), 2) as kdr,
        ROUND(AVG(NULLIF(m.adr, 0)), 1) as adr,
        ROUND(CAST(SUM(m.kills) AS FLOAT) / NULLIF(COUNT(CASE WHEN m.kills > 0 THEN 1 END), 0), 1) as kills_per_match,
        ROUND(AVG(NULLIF(m.hs_percent, 0)), 1) as hs_percent
    FROM matches m
    JOIN players p ON m.player_id = p.player_id
    WHERE {where_c}
    GROUP BY p.nick, p.player_id, m.map
    ORDER BY matches DESC
    """
    df = pd.read_sql_query(query, conn, params=params)
    conn.close()
    return df


def get_squad_map_stats(
    month: Optional[str] = None,
    platform: str = "TODOS",
    db_path: str = DB_PATH,
    **kwargs
) -> pd.DataFrame:
    """
    Retorna as estatísticas consolidadas e deduplicadas por mapa para o Squad como um todo.
    """
    conn = get_connection(db_path)
    conditions = ["m.map IS NOT NULL", "m.map != ''"]
    params = []
    
    placeholders = ",".join(["?" for _ in CORE_PLAYERS])
    conditions.append(f"p.nick IN ({placeholders})")
    params.extend(list(CORE_PLAYERS))
        
    if month and month != "Todos":
        conditions.append("m.month = ?")
        params.append(month)
        
    if platform and platform.upper() != "TODOS":
        conditions.append("m.platform = ?")
        params.append(platform.upper())
        
    where_c = " AND ".join(conditions)
    
    query = f"""
    WITH unique_matches AS (
        SELECT 
            m.match_id,
            m.map,
            MAX(m.win) as win,
            SUM(m.kills) as team_kills,
            SUM(m.deaths) as team_deaths,
            AVG(NULLIF(m.adr, 0)) as team_adr
        FROM matches m
        JOIN players p ON m.player_id = p.player_id
        WHERE {where_c}
        GROUP BY m.match_id, m.map
    )
    SELECT 
        map,
        COUNT(match_id) as matches,
        SUM(win) as wins,
        COUNT(match_id) - SUM(win) as losses,
        ROUND(CAST(SUM(win) AS FLOAT) / COUNT(match_id) * 100, 1) as win_rate,
        SUM(team_kills) as kills,
        SUM(team_deaths) as deaths,
        ROUND(CAST(SUM(team_kills) AS FLOAT) / NULLIF(SUM(team_deaths), 0), 2) as kdr,
        ROUND(AVG(NULLIF(team_adr, 0)), 1) as adr
    FROM unique_matches
    GROUP BY map
    ORDER BY matches DESC
    """
    df = pd.read_sql_query(query, conn, params=params)
    conn.close()
    return df


def get_telemetry_stats(month: Optional[str] = None, platform: str = "TODOS", db_path: str = DB_PATH, **kwargs) -> pd.DataFrame:
    """
    Retorna estatísticas médias de telemetria avançada (Leetify) para os jogadores do Core Squad.
    Calcula apenas para partidas onde há dados telemétricos (reaction_time > 0 ou leetify_rating != 0).
    """
    conn = get_connection(db_path)
    placeholders = ",".join(["?" for _ in CORE_PLAYERS])
    conditions = [
        f"p.nick IN ({placeholders})",
        "(m.reaction_time > 0 OR m.leetify_rating != 0 OR m.counter_strafe_pct > 0)"
    ]
    params = list(CORE_PLAYERS)
    
    if month and month != "Todos":
        conditions.append("m.month = ?")
        params.append(month)
        
    if platform and platform.upper() != "TODOS":
        conditions.append("m.platform = ?")
        params.append(platform.upper())
        
    where_clause = " WHERE " + " AND ".join(conditions)
    
    query = f"""
    SELECT 
        p.nick,
        p.player_id,
        p.level,
        COUNT(m.match_id) as analyzed_matches,
        ROUND(AVG(NULLIF(m.leetify_rating, 0.0)), 2) as avg_leetify_rating,
        ROUND(AVG(NULLIF(m.ct_leetify_rating, 0.0)), 2) as avg_ct_rating,
        ROUND(AVG(NULLIF(m.t_leetify_rating, 0.0)), 2) as avg_t_rating,
        ROUND(AVG(NULLIF(m.reaction_time, 0.0)), 0) as avg_reaction_time,
        ROUND(AVG(NULLIF(m.preaim, 0.0)), 1) as avg_preaim,
        ROUND(AVG(NULLIF(m.spray_accuracy, 0.0)), 1) as avg_spray_accuracy,
        ROUND(AVG(NULLIF(m.counter_strafe_pct, 0.0)), 1) as avg_counter_strafe,
        ROUND(AVG(NULLIF(m.trade_kill_pct, 0.0)), 1) as avg_trade_kills,
        ROUND(AVG(NULLIF(m.traded_death_pct, 0.0)), 1) as avg_traded_deaths,
        ROUND(AVG(NULLIF(m.flash_duration_avg, 0.0)), 2) as avg_flash_duration,
        ROUND(AVG(NULLIF(m.he_damage_avg, 0.0)), 1) as avg_he_damage,
        ROUND(AVG(NULLIF(m.utility_on_death_avg, 0.0)), 0) as avg_utility_waste,
        ROUND(AVG(NULLIF(m.adr, 0.0)), 1) as avg_adr,
        ROUND(AVG(NULLIF(m.hs_percent, 0.0)), 1) as avg_hs_percent
    FROM players p
    JOIN matches m ON p.player_id = m.player_id
    {where_clause}
    GROUP BY p.nick, p.player_id, p.level
    ORDER BY avg_leetify_rating DESC, analyzed_matches DESC
    """
    df = pd.read_sql_query(query, conn, params=params)
    conn.close()
    return df

def find_matching_gc_match(player_id: int, month: str, map_name: str, score_a: int, score_b: int, db_path: str = DB_PATH) -> Optional[str]:
    """
    Encontra um match_id existente da Gamers Club no banco com base no mapa e placar.
    Como na GC o placar pode estar invertido dependendo de qual time começou,
    verifica ambas as orientações (score_a==sa e score_b==sb OU score_a==sb e score_b==sa).
    """
    conn = get_connection(db_path)
    cursor = conn.cursor()
    cursor.execute("""
        SELECT match_id, score_a, score_b 
        FROM matches 
        WHERE player_id = ? AND month = ? AND map = ? AND platform = 'GC'
    """, (player_id, month, map_name))
    rows = cursor.fetchall()
    conn.close()
    
    for r in rows:
        mid, sa, sb = r[0], r[1], r[2]
        if (sa == score_a and sb == score_b) or (sa == score_b and sb == score_a):
            return str(mid)
    return None


def save_gc_match_details(match_id: str, stats_data: Dict[str, Any], lobby_data: Optional[Dict[str, Any]] = None, db_path: str = DB_PATH):
    """
    Salva e enriquece todos os dados detalhados da Gamers Club (Geral, Entries, Trades, Clutch, Utilitárias, Mira)
    para todos os 10 jogadores na tabela gc_match_scoreboard e atualiza a tabela matches para os jogadores monitorados.
    """
    if not stats_data or not isinstance(stats_data, dict):
        return
        
    conn = get_connection(db_path)
    cursor = conn.cursor()
    
    # Mapeia metadados dos jogadores do lobby se fornecido
    player_meta = {}
    team_a_name = "Time A"
    team_b_name = "Time B"
    if lobby_data and isinstance(lobby_data, dict):
        team_a_name = lobby_data.get("time_a") or "Time A"
        team_b_name = lobby_data.get("time_b") or "Time B"
        jogos_players = lobby_data.get("jogos", {}).get("players", {})
        if isinstance(jogos_players, dict):
            for room, plist in jogos_players.items():
                if isinstance(plist, list):
                    for pl in plist:
                        pid_str = str(pl.get("idplayer"))
                        p_info = pl.get("player", {})
                        avatar_url = ""
                        if pl.get("plAvatar"):
                            avatar_url = f"https://static.gamersclub.com.br/{pl.get('plAvatar')}_medium.jpg"
                        nick = p_info.get("nick") or pl.get("player", {}).get("nick") or f"Player {pid_str}"
                        level = pl.get("level") or p_info.get("level")
                        player_meta[pid_str] = {
                            "nick": nick,
                            "level": int(level) if level else None,
                            "avatar_url": avatar_url,
                            "team": str(pl.get("player_room", room)).upper()
                        }
                        
    players_stats = stats_data.get("players", {})
    scoreboard = stats_data.get("scoreboard", {})
    
    # Também busca nicks conhecidos da tabela players
    cursor.execute("SELECT player_id, nick, level, avatar_url FROM players")
    known_db_players = {str(row[0]): {"nick": row[1], "level": row[2], "avatar_url": row[3]} for row in cursor.fetchall()}
    
    for pid_str, pdata in players_stats.items():
        try:
            pid = int(pid_str)
        except (ValueError, TypeError):
            continue
            
        meta = player_meta.get(pid_str, known_db_players.get(pid_str, {}))
        nick = meta.get("nick") or f"Jogador {pid_str}"
        level = meta.get("level")
        avatar_url = meta.get("avatar_url", "")
        team = pdata.get("team") or meta.get("team", "A")
        team_name = team_a_name if team == "A" else team_b_name
        is_core = 1 if nick in CORE_PLAYERS else 0
        
        row = pdata.get("row", {})
        sb = scoreboard.get(pid_str, {})
        
        gen = row.get("general", {})
        ent = row.get("entries", {})
        trd = row.get("trades", {})
        clt = row.get("clutch", {})
        utl = row.get("utility", {})
        aim = row.get("aim", {})
        
        gc_rating = round(float(gen.get("rating", 0.0) or 0.0), 2)
        round_swing = round(float(gen.get("roundSwing", 0.0) or 0.0), 4)
        
        kills = int(sb.get("kills", 0) or 0)
        assists = int(sb.get("assists", 0) or 0)
        deaths = int(sb.get("deaths", 0) or 0)
        adr = round(float(sb.get("adr", 0.0) or 0.0), 1)
        kdr = round(float(sb.get("kdr", 0.0) or 0.0), 2)
        kast = round(float(sb.get("kast", 0.0) or 0.0), 1)
        
        entry_duels = int(ent.get("duels", 0) or 0)
        entry_won = int(ent.get("won", 0) or 0)
        entry_lost = int(ent.get("lost", 0) or 0)
        entry_succ = round(float(ent.get("successRate", 0.0) or 0.0), 1)
        entry_pr = round(float(ent.get("perRound", 0.0) or 0.0), 2)
        
        tr_made = int(trd.get("made", 0) or 0)
        tr_deaths = int(trd.get("tradedDeaths", 0) or 0)
        tr_rate = round(float(trd.get("tradedRate", 0.0) or 0.0), 1)
        tr_time = round(float(trd.get("avgTime", 0.0) or 0.0), 1)
        
        cl_sit = int(clt.get("situations", 0) or 0)
        cl_won = int(clt.get("won", 0) or 0)
        cl_rate = round(float(clt.get("rate", 0.0) or 0.0), 1)
        cl_1v1_w = int(clt.get("oneVsOneWon", 0) or 0)
        cl_1v1_t = int(clt.get("oneVsOneTotal", 0) or 0)
        cl_1vn_w = int(clt.get("oneVsManyWon", 0) or 0)
        cl_1vn_t = int(clt.get("oneVsManyTotal", 0) or 0)
        cl_biggest_raw = clt.get("biggestComeback")
        cl_biggest = f"1v{cl_biggest_raw}" if cl_biggest_raw else "-"
        
        ut_dmg = int(utl.get("damage", 0) or 0)
        ut_fa = int(utl.get("flashAssists", 0) or 0)
        ut_ef = int(utl.get("enemiesFlashed", 0) or 0)
        ut_gr = int(utl.get("grenades", 0) or 0)
        ut_dpg = round(float(utl.get("damagePerGrenade", 0.0) or 0.0), 1)
        
        aim_acc = round(float(aim.get("accuracy", 0.0) or 0.0), 1)
        aim_hs = round(float(aim.get("headshotRate", 0.0) or 0.0), 1)
        aim_head_acc = round(float(aim.get("headAccuracy", 0.0) or 0.0), 1)
        aim_kpr = round(float(aim.get("killsPerRound", 0.0) or 0.0), 2)
        aim_weapon = str(aim.get("mainWeapon", "") or "")
        
        # Salva na tabela dedicada do scoreboard
        cursor.execute("""
        INSERT INTO gc_match_scoreboard (
            match_id, player_id, nick, level, avatar_url, team, team_name, is_core_squad,
            gc_rating, round_swing, kills, assists, deaths, adr, kdr, kast,
            entry_duels, entry_won, entry_lost, entry_success_rate, entry_per_round,
            trades_made, traded_deaths, trade_rate, trade_avg_time,
            clutch_situations, clutch_won, clutch_rate, clutch_1v1_won, clutch_1v1_total,
            clutch_1vn_won, clutch_1vn_total, clutch_biggest,
            utility_damage, flash_assists, enemies_flashed, grenades_thrown, damage_per_grenade,
            aim_accuracy, aim_hs_rate, aim_head_acc, aim_kpr, main_weapon, updated_at
        ) VALUES (
            ?, ?, ?, ?, ?, ?, ?, ?,
            ?, ?, ?, ?, ?, ?, ?, ?,
            ?, ?, ?, ?, ?,
            ?, ?, ?, ?,
            ?, ?, ?, ?, ?,
            ?, ?, ?,
            ?, ?, ?, ?, ?,
            ?, ?, ?, ?, ?, CURRENT_TIMESTAMP
        )
        ON CONFLICT(match_id, player_id) DO UPDATE SET
            nick = excluded.nick,
            level = COALESCE(excluded.level, gc_match_scoreboard.level),
            avatar_url = COALESCE(excluded.avatar_url, gc_match_scoreboard.avatar_url),
            team = excluded.team,
            team_name = excluded.team_name,
            is_core_squad = excluded.is_core_squad,
            gc_rating = excluded.gc_rating,
            round_swing = excluded.round_swing,
            kills = excluded.kills,
            assists = excluded.assists,
            deaths = excluded.deaths,
            adr = excluded.adr,
            kdr = excluded.kdr,
            kast = excluded.kast,
            entry_duels = excluded.entry_duels,
            entry_won = excluded.entry_won,
            entry_lost = excluded.entry_lost,
            entry_success_rate = excluded.entry_success_rate,
            entry_per_round = excluded.entry_per_round,
            trades_made = excluded.trades_made,
            traded_deaths = excluded.traded_deaths,
            trade_rate = excluded.trade_rate,
            trade_avg_time = excluded.trade_avg_time,
            clutch_situations = excluded.clutch_situations,
            clutch_won = excluded.clutch_won,
            clutch_rate = excluded.clutch_rate,
            clutch_1v1_won = excluded.clutch_1v1_won,
            clutch_1v1_total = excluded.clutch_1v1_total,
            clutch_1vn_won = excluded.clutch_1vn_won,
            clutch_1vn_total = excluded.clutch_1vn_total,
            clutch_biggest = excluded.clutch_biggest,
            utility_damage = excluded.utility_damage,
            flash_assists = excluded.flash_assists,
            enemies_flashed = excluded.enemies_flashed,
            grenades_thrown = excluded.grenades_thrown,
            damage_per_grenade = excluded.damage_per_grenade,
            aim_accuracy = excluded.aim_accuracy,
            aim_hs_rate = excluded.aim_hs_rate,
            aim_head_acc = excluded.aim_head_acc,
            aim_kpr = excluded.aim_kpr,
            main_weapon = excluded.main_weapon,
            updated_at = CURRENT_TIMESTAMP
        """, (
            str(match_id), pid, nick, level, avatar_url, team, team_name, is_core,
            gc_rating, round_swing, kills, assists, deaths, adr, kdr, kast,
            entry_duels, entry_won, entry_lost, entry_succ, entry_pr,
            tr_made, tr_deaths, tr_rate, tr_time,
            cl_sit, cl_won, cl_rate, cl_1v1_w, cl_1v1_t,
            cl_1vn_w, cl_1vn_t, cl_biggest,
            ut_dmg, ut_fa, ut_ef, ut_gr, ut_dpg,
            aim_acc, aim_hs, aim_head_acc, aim_kpr, aim_weapon
        ))
        
        # Atualiza a tabela matches se o jogador já estiver registrado nessa partida
        cursor.execute("""
        UPDATE matches SET
            kills = CASE WHEN ? > 0 THEN ? ELSE kills END,
            deaths = CASE WHEN ? > 0 THEN ? ELSE deaths END,
            adr = CASE WHEN ? > 0.0 THEN ? ELSE adr END,
            hs_percent = CASE WHEN ? > 0.0 THEN ? ELSE hs_percent END,
            gc_rating = ?,
            round_swing = ?,
            entry_duels = ?,
            entry_won = ?,
            entry_lost = ?,
            entry_success_rate = ?,
            entry_per_round = ?,
            trades_made = ?,
            traded_deaths = ?,
            trade_rate = ?,
            trade_avg_time = ?,
            clutch_situations = ?,
            clutch_won = ?,
            clutch_rate = ?,
            clutch_1v1_won = ?,
            clutch_1v1_total = ?,
            clutch_1vn_won = ?,
            clutch_1vn_total = ?,
            clutch_biggest = ?,
            utility_damage = ?,
            flash_assists = ?,
            enemies_flashed = ?,
            grenades_thrown = ?,
            damage_per_grenade = ?,
            aim_accuracy = ?,
            aim_hs_rate = ?,
            aim_head_acc = ?,
            aim_kpr = ?,
            main_weapon = ?
        WHERE match_id = ? AND player_id = ?
        """, (
            kills, kills,
            deaths, deaths,
            adr, adr,
            aim_hs, aim_hs,
            gc_rating, round_swing,
            entry_duels, entry_won, entry_lost, entry_succ, entry_pr,
            tr_made, tr_deaths, tr_rate, tr_time,
            cl_sit, cl_won, cl_rate, cl_1v1_w, cl_1v1_t,
            cl_1vn_w, cl_1vn_t, cl_biggest,
            ut_dmg, ut_fa, ut_ef, ut_gr, ut_dpg,
            aim_acc, aim_hs, aim_head_acc, aim_kpr, aim_weapon,
            str(match_id), pid
        ))
        
    conn.commit()
    conn.close()

def get_gc_match_scoreboard(match_id: str, db_path: str = DB_PATH) -> pd.DataFrame:
    """Retorna o scoreboard completo dos 10 jogadores de uma partida da GC."""
    conn = get_connection(db_path)
    q = """
    SELECT * FROM gc_match_scoreboard
    WHERE match_id = ?
    ORDER BY team ASC, gc_rating DESC, kills DESC
    """
    df = pd.read_sql_query(q, conn, params=[str(match_id)])
    conn.close()
    return df

def get_gc_advanced_squad_stats(month: Optional[str] = None, db_path: str = DB_PATH) -> pd.DataFrame:
    """
    Calcula médias e totais consolidados das novas estatísticas da GC (Entries, Trades, Clutch, Utilitárias e Mira)
    para os 7 jogadores principais a partir das partidas registradas.
    """
    conn = get_connection(db_path)
    placeholders = ",".join(["?" for _ in CORE_PLAYERS])
    conditions = [
        f"p.nick IN ({placeholders})",
        "m.platform = 'GC'",
        "(m.aim_accuracy > 0 OR m.entry_duels > 0 OR m.trades_made > 0 OR m.utility_damage > 0)"
    ]
    params = list(CORE_PLAYERS)
    if month and month != "Todos":
        conditions.append("m.month = ?")
        params.append(month)
    where_c = " AND ".join(conditions)
    
    query = f"""
    SELECT 
        p.nick,
        p.player_id,
        p.level,
        COUNT(m.match_id) as analyzed_matches,
        -- Geral & Impacto
        ROUND(AVG(NULLIF(m.gc_rating, 0.0)), 2) as avg_gc_rating,
        ROUND(AVG(m.round_swing), 4) as avg_round_swing,
        ROUND(SUM(m.round_swing), 3) as total_round_swing,
        -- Entries
        SUM(m.entry_duels) as total_entry_duels,
        SUM(m.entry_won) as total_entry_won,
        SUM(m.entry_lost) as total_entry_lost,
        ROUND(CAST(SUM(m.entry_won) AS FLOAT) / NULLIF(SUM(m.entry_duels), 0) * 100, 1) as entry_success_rate,
        ROUND(AVG(NULLIF(m.entry_per_round, 0.0)), 2) as avg_entry_per_round,
        -- Trades
        SUM(m.trades_made) as total_trades_made,
        ROUND(CAST(SUM(m.trades_made) AS FLOAT) / COUNT(m.match_id), 1) as avg_trades_per_match,
        SUM(m.traded_deaths) as total_traded_deaths,
        ROUND(AVG(NULLIF(m.trade_rate, 0.0)), 1) as avg_trade_rate,
        ROUND(AVG(NULLIF(m.trade_avg_time, 0.0)), 1) as avg_trade_time,
        -- Clutch
        SUM(m.clutch_situations) as total_clutches,
        SUM(m.clutch_won) as total_clutches_won,
        ROUND(CAST(SUM(m.clutch_won) AS FLOAT) / COUNT(m.match_id), 2) as avg_clutches_per_match,
        ROUND(CAST(SUM(m.clutch_won) AS FLOAT) / NULLIF(SUM(m.clutch_situations), 0) * 100, 1) as clutch_win_rate,
        SUM(m.clutch_1v1_won) as total_1v1_won,
        SUM(m.clutch_1v1_total) as total_1v1_played,
        SUM(m.clutch_1vn_won) as total_1vn_won,
        SUM(m.clutch_1vn_total) as total_1vn_played,
        -- Utilitárias
        SUM(m.utility_damage) as total_util_damage,
        ROUND(AVG(NULLIF(m.utility_damage, 0)), 1) as avg_util_damage,
        SUM(m.flash_assists) as total_flash_assists,
        ROUND(CAST(SUM(m.flash_assists) AS FLOAT) / COUNT(m.match_id), 2) as avg_flash_assists_per_match,
        SUM(m.enemies_flashed) as total_enemies_flashed,
        ROUND(CAST(SUM(m.enemies_flashed) AS FLOAT) / COUNT(m.match_id), 1) as avg_enemies_flashed_per_match,
        SUM(m.grenades_thrown) as total_grenades,
        ROUND(CAST(SUM(m.grenades_thrown) AS FLOAT) / COUNT(m.match_id), 1) as avg_grenades_per_match,
        ROUND(AVG(NULLIF(m.damage_per_grenade, 0.0)), 1) as avg_damage_per_grenade,
        -- Mira
        ROUND(AVG(NULLIF(m.aim_accuracy, 0.0)), 1) as avg_accuracy,
        ROUND(AVG(NULLIF(m.aim_hs_rate, 0.0)), 1) as avg_hs_rate,
        ROUND(AVG(NULLIF(m.aim_head_acc, 0.0)), 1) as avg_head_acc,
        ROUND(AVG(NULLIF(m.aim_kpr, 0.0)), 2) as avg_kpr
    FROM players p
    JOIN matches m ON p.player_id = m.player_id
    WHERE {where_c}
    GROUP BY p.nick, p.player_id, p.level
    ORDER BY avg_gc_rating DESC, analyzed_matches DESC
    """
    df = pd.read_sql_query(query, conn, params=params)
    conn.close()
    return df
