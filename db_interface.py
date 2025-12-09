# db_interface.py
import config
import sqlite3

def get_player_full_data(player_id):
    """獲取球員在 Players 和 Player_Attributes 表中的所有數據"""
    conn = config.get_db_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM Players WHERE PlayerID=?", (player_id,))
    player_data = cursor.fetchone()
    if not player_data:
        conn.close()
        return None
    
    player_cols = [desc[0] for desc in cursor.description]
    data = dict(zip(player_cols, player_data))
    
    # 查詢 Attributes (例如 Stamina, Shooting 屬性)
    cursor.execute("SELECT * FROM Player_Attributes WHERE PlayerID=?", (player_id,))
    attrs_data = cursor.fetchone()
    if attrs_data:
        attrs_cols = [desc[0] for desc in cursor.description]
        data.update(dict(zip(attrs_cols, attrs_data)))

    conn.close()
    return data

def update_player_state(player_id, column, value):
    """更新 Players 表中的狀態欄位 (例如 OVR, Fatigue)"""
    conn = config.get_db_connection()
    cursor = conn.cursor()
    cursor.execute(f"UPDATE Players SET {column}=? WHERE PlayerID=?", (value, player_id))
    conn.commit()
    conn.close()

def update_team_standing(team_id, win=False):
    """更新隊伍戰績"""
    conn = config.get_db_connection()
    cursor = conn.cursor()
    if win:
        cursor.execute("UPDATE Team_Standings SET Wins = Wins + 1 WHERE TeamID=?", (team_id,))
    else:
        cursor.execute("UPDATE Team_Standings SET Losses = Losses + 1 WHERE TeamID=?", (team_id,))
    conn.commit()
    conn.close()

def get_players_on_roster(team_id):
    """獲取特定隊伍所有球員 ID"""
    conn = config.get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT PlayerID FROM Players WHERE TeamID=?", (team_id,))
    players = [row[0] for row in cursor.fetchall()]
    conn.close()
    return players

def update_player_game_stats(player_id, stats_dict):
    """【致命 Bug 修正】：累積單場比賽數據到 Player_Stats 表中"""
    conn = config.get_db_connection()
    cursor = conn.cursor()
    
    # 創建 SQL SET 語句：累積數據
    set_clauses = [f"{col} = {col} + ?" for col in config.STATS_COLUMNS]
    values = [stats_dict.get(col, 0) for col in config.STATS_COLUMNS]
    values.append(player_id)

    # 執行累積更新
    cursor.execute(f"UPDATE Player_Stats SET {', '.join(set_clauses)} WHERE PlayerID=?", tuple(values))

    conn.commit()
    conn.close()