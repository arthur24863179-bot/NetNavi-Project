import sqlite3

DB_NAME = 'nba_gm.db'

def create_stats_tables():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    # 1. 賽程表 (Game_Schedule)
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS Game_Schedule (
        GameID INTEGER PRIMARY KEY AUTOINCREMENT,
        HomeTeamID INTEGER,
        AwayTeamID INTEGER,
        GameDate TEXT,
        HomeScore INTEGER DEFAULT 0,
        AwayScore INTEGER DEFAULT 0,
        IsPlayed BOOLEAN DEFAULT 0
    );
    """)

    # 2. 隊伍統計表 (Team_Stats)
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS Team_Stats (
        TeamID INTEGER PRIMARY KEY,
        Wins INTEGER DEFAULT 0,
        Losses INTEGER DEFAULT 0,
        PointsScored INTEGER DEFAULT 0,
        PointsAllowed INTEGER DEFAULT 0
    );
    """)

    # 3. 球員個人賽季統計表 (Player_Stats)
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS Player_Stats (
        PlayerID INTEGER PRIMARY KEY,
        GP INTEGER DEFAULT 0,               -- 出賽場數
        MPG REAL DEFAULT 0.0,               -- 平均上場時間
        PPG REAL DEFAULT 0.0,               -- 平均得分
        Fatigue REAL DEFAULT 0.0,           -- 賽季累積疲勞 (0-100)
        InjuryStatus TEXT DEFAULT 'Healthy' -- 傷病狀態 (Healthy, Injured, Out)
    );
    """)
    
    # 初始化所有球隊和球員的統計數據
    cursor.execute("INSERT OR IGNORE INTO Team_Stats (TeamID) SELECT TeamID FROM Teams")
    cursor.execute("INSERT OR IGNORE INTO Player_Stats (PlayerID) SELECT PlayerID FROM Players")


    conn.commit()
    conn.close()
    print(f"✅ 成功在 {DB_NAME} 中創建並初始化賽程與統計表格。")

if __name__ == '__main__':
    create_stats_tables()