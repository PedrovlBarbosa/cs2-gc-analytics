import sqlite3
import pandas as pd
from typing import List, Dict, Any, Optional

DB_PATH = "gc_stats.db"

CORE_PLAYERS = ['KrannDy', 'Aquarista', 'Art', 'Cherki', 'Death', 'Kinha', 'mch']

def get_connection(db_path: str = DB_PATH) -> sqlite3.Connection:
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
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
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        PRIMARY KEY (match_id, player_id),
        FOREIGN KEY (player_id) REFERENCES players (player_id)
    )
    """)

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
    return {row[0] for row in rows}

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
            map, match_type, platform, kills, deaths, adr, hs_percent, updated_at
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
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
            kills = excluded.kills,
            deaths = excluded.deaths,
            adr = excluded.adr,
            hs_percent = excluded.hs_percent,
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
            m.get("hs_percent", 0.0)
        ))
    conn.commit()
    conn.close()

def get_all_players(db_path: str = DB_PATH) -> pd.DataFrame:
    conn = get_connection(db_path)
    df = pd.read_sql_query("SELECT * FROM players ORDER BY is_main_user DESC, nick ASC", conn)
    conn.close()
    return df

def get_all_months(platform: str = "TODOS", db_path: str = DB_PATH) -> List[str]:
    conn = get_connection(db_path)
    cursor = conn.cursor()
    if platform and platform.upper() != "TODOS":
        cursor.execute("SELECT DISTINCT month FROM monthly_stats WHERE platform = ? ORDER BY month DESC", (platform.upper(),))
    else:
        cursor.execute("SELECT DISTINCT month FROM monthly_stats ORDER BY month DESC")
    rows = cursor.fetchall()
    conn.close()
    return [r[0] for r in rows]

def get_core_players_stats(month: Optional[str] = None, platform: str = "TODOS", db_path: str = DB_PATH) -> pd.DataFrame:
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
    ORDER BY matches DESC, kdr DESC
    """
    df = pd.read_sql_query(query, conn, params=params)
    conn.close()
    return df

def get_core_squad_totals(month: Optional[str] = None, platform: str = "TODOS", db_path: str = DB_PATH) -> Dict[str, Any]:
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

def get_player_history(player_id: int, platform: str = "TODOS", db_path: str = DB_PATH) -> pd.DataFrame:
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

def get_matches_by_month(month: Optional[str] = None, player_id: Optional[int] = None, platform: str = "TODOS", db_path: str = DB_PATH) -> pd.DataFrame:
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
