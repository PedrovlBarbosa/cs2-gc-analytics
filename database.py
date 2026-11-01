import sqlite3
import pandas as pd
from typing import List, Dict, Any, Optional

DB_PATH = "gc_stats.db"

def get_connection(db_path: str = DB_PATH) -> sqlite3.Connection:
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    return conn

def init_db(db_path: str = DB_PATH):
    conn = get_connection(db_path)
    cursor = conn.cursor()

    # Tabela de jogadores (usuário principal e companheiros de equipe)
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS players (
        player_id INTEGER PRIMARY KEY,
        nick TEXT NOT NULL,
        level INTEGER,
        is_main_user BOOLEAN DEFAULT 0,
        avatar_url TEXT,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    """)

    # Tabela de estatísticas consolidadas mensais
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS monthly_stats (
        player_id INTEGER,
        month TEXT,
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
        PRIMARY KEY (player_id, month),
        FOREIGN KEY (player_id) REFERENCES players (player_id)
    )
    """)

    # Tabela de partidas individuais
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS matches (
        match_id INTEGER PRIMARY KEY,
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
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (player_id) REFERENCES players (player_id)
    )
    """)

    conn.commit()
    conn.close()

def save_player(player: Dict[str, Any], db_path: str = DB_PATH):
    conn = get_connection(db_path)
    cursor = conn.cursor()
    cursor.execute("""
    INSERT INTO players (player_id, nick, level, is_main_user, avatar_url, updated_at)
    VALUES (?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
    ON CONFLICT(player_id) DO UPDATE SET
        nick = excluded.nick,
        level = excluded.level,
        is_main_user = excluded.is_main_user,
        avatar_url = excluded.avatar_url,
        updated_at = CURRENT_TIMESTAMP
    """, (
        player["player_id"],
        player["nick"],
        player.get("level"),
        player.get("is_main_user", 0),
        player.get("avatar_url", "")
    ))
    conn.commit()
    conn.close()

def save_monthly_stats(stats: Dict[str, Any], db_path: str = DB_PATH):
    conn = get_connection(db_path)
    cursor = conn.cursor()
    cursor.execute("""
    INSERT INTO monthly_stats (
        player_id, month, matches, wins, loss, win_rate, kdr, adr,
        kills, deaths, kast_percent, multi_kills, first_kills, hs_percent,
        bomb_plants, bomb_defuses, hitbox_head, hitbox_chest, hitbox_stomach,
        hitbox_arms, hitbox_legs, updated_at
    )
    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
    ON CONFLICT(player_id, month) DO UPDATE SET
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
            team_name_b, score_b, win, rating_player, rating_diff, map, match_type, updated_at
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
        ON CONFLICT(match_id) DO UPDATE SET
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
            updated_at = CURRENT_TIMESTAMP
        """, (
            m["match_id"],
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
            m.get("match_type", "lobby")
        ))
    conn.commit()
    conn.close()

def get_all_players(db_path: str = DB_PATH) -> pd.DataFrame:
    conn = get_connection(db_path)
    df = pd.read_sql_query("SELECT * FROM players ORDER BY is_main_user DESC, nick ASC", conn)
    conn.close()
    return df

def get_all_months(db_path: str = DB_PATH) -> List[str]:
    conn = get_connection(db_path)
    cursor = conn.cursor()
    cursor.execute("SELECT DISTINCT month FROM monthly_stats WHERE matches > 0 ORDER BY month DESC")
    rows = cursor.fetchall()
    conn.close()
    return [r[0] for r in rows]

def get_monthly_summary(month: Optional[str] = None, db_path: str = DB_PATH) -> pd.DataFrame:
    conn = get_connection(db_path)
    if month:
        query = """
        SELECT p.nick, p.level, p.is_main_user, s.*
        FROM monthly_stats s
        JOIN players p ON s.player_id = p.player_id
        WHERE s.month = ?
        ORDER BY s.matches DESC, s.kdr DESC
        """
        df = pd.read_sql_query(query, conn, params=(month,))
    else:
        query = """
        SELECT p.nick, p.level, p.is_main_user, s.*
        FROM monthly_stats s
        JOIN players p ON s.player_id = p.player_id
        ORDER BY s.month DESC, s.matches DESC
        """
        df = pd.read_sql_query(query, conn)
    conn.close()
    return df

def get_player_history(player_id: int, db_path: str = DB_PATH) -> pd.DataFrame:
    conn = get_connection(db_path)
    query = """
    SELECT * FROM monthly_stats
    WHERE player_id = ? AND matches > 0
    ORDER BY month ASC
    """
    df = pd.read_sql_query(query, conn, params=(player_id,))
    conn.close()
    return df

def get_matches_by_month(month: Optional[str] = None, player_id: Optional[int] = None, db_path: str = DB_PATH) -> pd.DataFrame:
    conn = get_connection(db_path)
    conditions = []
    params = []
    if month:
        conditions.append("month = ?")
        params.append(month)
    if player_id:
        conditions.append("player_id = ?")
        params.append(player_id)
    where_clause = " WHERE " + " AND ".join(conditions) if conditions else ""
    query = f"SELECT * FROM matches {where_clause} ORDER BY match_id DESC"
    df = pd.read_sql_query(query, conn, params=params)
    conn.close()
    return df
