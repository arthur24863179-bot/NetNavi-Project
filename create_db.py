# create_db.py (【已修正】的數據庫創建與初始化文件)
import sqlite3
import random
import os
import config # 導入新的配置檔

# DB_NAME, FULL_ATTRIBUTES 等已移至 config.py，這裡直接使用 config.***

OFFENSIVE_SYSTEMS = ['PACE', 'GRIND', 'MOTION', 'ISO', 'PnR', 'TRIANGLE', '5-OUT', 'BALANCED']
DEFENSIVE_SYSTEMS = ['Man-to-Man', 'Switch All', 'Drop Coverage', 'Zone 2-3', 'Zone 3-2', 'Full Court Press', 'Box-and-1']
PLAYER_ARCHETYPES = ['HANDLER', 'POINT_FWD', 'SCORER', 'SLASHER', 'POST_UP', 'SPACER', 'ROLL_MAN', 'LOCKDOWN', 'ANCHOR', 'HUSTLE', 'LINK']

def calculate_initial_ovr(attrs):
    """簡化 OVR 計算，確保 OVR 數值存在"""
    # 假設 OVR 是所有屬性的平均 (或更複雜的加權平均)
    avg = sum(attrs.values()) / len(attrs)
    return round(avg)

def generate_random_attributes():
    """生成 V5.0 要求的 15 項深度屬性 (50-99)。"""
    attrs = {}
    for attr in config.FULL_ATTRIBUTES:
        if attr == 'Height': 
            attrs[attr] = random.randint(185, 215)
        else:
            attrs[attr] = random.randint(50, 99)
    return attrs

def generate_random_badges():
    """隨機生成徽章 (T1/T2/T3) - 簡化為數量。"""
    return {
        'Org_T1': random.randint(0, 3), 'Org_T3': 1 if random.random() < 0.1 else 0, 
        'Shot_T1': random.randint(0, 5), 'Shot_T3': 1 if random.random() < 0.15 else 0,
        'Fin_T1': random.randint(0, 4), 'Fin_T3': 1 if random.random() < 0.05 else 0,
        'Def_T1': random.randint(0, 5), 'Def_T3': 1 if random.random() < 0.1 else 0,
    }

def generate_random_personalities():
    """生成 V5.0 個性矩陣數值 (0-100)"""
    personalities = [
        'TeamFirst', 'AlphaDog', 'MoneyMotivated', 'WinningDriven', 
        'BallHog', 'Shrink', 'Mentor', 'Cancer'
    ]
    return {p: random.randint(0, 100) for p in personalities}


def create_tables(conn):
    """創建遊戲所需的所有數據庫表格，包含 V5.0 擴展。"""
    cursor = conn.cursor()
    
    # 1. Teams (隊伍)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS Teams (
            TeamID INTEGER PRIMARY KEY,
            Name TEXT NOT NULL,
            CoachID INTEGER,
            IsGMControlled INTEGER DEFAULT 0,
            SalaryCap REAL DEFAULT 140.0,
            LuxuryTax REAL DEFAULT 0.0
        )
    """)

    # 2. Coaches (教練)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS Coaches (
            CoachID INTEGER PRIMARY KEY, Name TEXT NOT NULL, Offense INTEGER NOT NULL, Defense INTEGER NOT NULL,
            Chemistry INTEGER NOT NULL, IGA INTEGER NOT NULL, OffensiveSystem TEXT NOT NULL, DefensiveSystem TEXT NOT NULL
        )
    """)

    # 3. Players (球員) - 【關鍵修正點】：新增 OVR, OriginalOVR, Fatigue, Injury 欄位
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS Players (
            PlayerID INTEGER PRIMARY KEY, Name TEXT NOT NULL, TeamID INTEGER, Age INTEGER NOT NULL,
            Potential INTEGER NOT NULL,
            OVR REAL DEFAULT 50.0,            
            OriginalOVR REAL DEFAULT 50.0,    
            Fatigue REAL DEFAULT 0.0,         
            InjuryRemainingGames INTEGER DEFAULT 0, 
            Contract REAL NOT NULL, ContractYears INTEGER DEFAULT 1, IsRookiePool INTEGER DEFAULT 0, 
            Archetype TEXT NOT NULL 
        )
    """)

    # 4. Player_Attributes (球員屬性)
    attrs_columns = ", ".join([f"{attr} INTEGER NOT NULL" for attr in config.FULL_ATTRIBUTES])
    cursor.execute(f"""
        CREATE TABLE IF NOT EXISTS Player_Attributes (
            PlayerID INTEGER PRIMARY KEY, 
            {attrs_columns}
        )
    """)

    # 5. Player_Personalities (球員個性)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS Player_Personalities (
            PlayerID INTEGER PRIMARY KEY, TeamFirst INTEGER NOT NULL, AlphaDog INTEGER NOT NULL, 
            MoneyMotivated INTEGER NOT NULL, WinningDriven INTEGER NOT NULL, BallHog INTEGER NOT NULL,
            Shrink INTEGER NOT NULL, Mentor INTEGER NOT NULL, Cancer INTEGER NOT NULL 
        )
    """)
    
    # 6. Player_Badges (球員徽章)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS Player_Badges (
            PlayerID INTEGER PRIMARY KEY, Org_T1 INTEGER DEFAULT 0, Org_T3 INTEGER DEFAULT 0,
            Shot_T1 INTEGER DEFAULT 0, Shot_T3 INTEGER DEFAULT 0, Fin_T1 INTEGER DEFAULT 0, Fin_T3 INTEGER DEFAULT 0,
            Def_T1 INTEGER DEFAULT 0, Def_T3 INTEGER DEFAULT 0
        )
    """)

    # 7. Player_Stats (球員賽季數據)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS Player_Stats (
            PlayerID INTEGER PRIMARY KEY, GamesPlayed INTEGER DEFAULT 0, MinutesPlayed REAL DEFAULT 0.0,
            Points REAL DEFAULT 0.0, Rebounds REAL DEFAULT 0.0, Assists REAL DEFAULT 0.0, Steals REAL DEFAULT 0.0, 
            Blocks REAL DEFAULT 0.0, Turnovers REAL DEFAULT 0.0, FG_Attempt INTEGER DEFAULT 0, FG_Made INTEGER DEFAULT 0,
            ThreeP_Attempt INTEGER DEFAULT 0, ThreeP_Made INTEGER DEFAULT 0, FT_Attempt INTEGER DEFAULT 0, 
            FT_Made INTEGER DEFAULT 0, PER REAL DEFAULT 0.0
        )
    """)
    
    # 8. Team_Standings (隊伍戰績)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS Team_Standings (
            TeamID INTEGER PRIMARY KEY, Wins INTEGER DEFAULT 0, Losses INTEGER DEFAULT 0
        )
    """)
    
    # 9. DraftPicks (選秀權)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS DraftPicks (
            DraftPickID INTEGER PRIMARY KEY, Year INTEGER NOT NULL, PickNumber INTEGER NOT NULL,
            OriginalTeamID INTEGER NOT NULL, CurrentTeamID INTEGER NOT NULL
        )
    """)
    
    # 10. Finances (財務)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS Finances (
            TeamID INTEGER PRIMARY KEY, Year INTEGER NOT NULL, Revenue REAL DEFAULT 0.0,
            Expenses REAL DEFAULT 0.0, Profit REAL DEFAULT 0.0, ConsecutiveLossYears INTEGER DEFAULT 0
        )
    """)
    
    conn.commit()

def populate_initial_data(conn):
    """填入初始隊伍、教練和球員數據。"""
    cursor = conn.cursor()
    
    teams = [f"Team {i}" for i in range(1, config.NUM_TEAMS + 1)] 
    
    for i, name in enumerate(teams):
        team_id = i + 1
        
        # 1. 創建教練、隊伍和財務
        coach_id = team_id
        cursor.execute("""
            INSERT INTO Coaches (CoachID, Name, Offense, Defense, Chemistry, IGA, OffensiveSystem, DefensiveSystem) 
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (coach_id, f"Coach {team_id} ({name})", random.randint(70, 95), random.randint(70, 95), 
              random.randint(70, 95), random.randint(70, 95),
              random.choice(OFFENSIVE_SYSTEMS), random.choice(DEFENSIVE_SYSTEMS)))
        
        is_gm_controlled = 1 if team_id == config.GM_CONTROLLED_TEAM_ID else 0 
        cursor.execute("""
            INSERT INTO Teams (TeamID, Name, CoachID, IsGMControlled) 
            VALUES (?, ?, ?, ?)
        """, (team_id, name, coach_id, is_gm_controlled))
        
        cursor.execute("""
            INSERT INTO Finances (TeamID, Year) VALUES (?, 2025)
        """, (team_id,))
        
        # 【修正點】：初始化 Team_Standings
        cursor.execute("""
            INSERT INTO Team_Standings (TeamID, Wins, Losses) VALUES (?, 0, 0)
        """, (team_id,))
        
        # 2. 為每隊創建 15 名球員
        total_salary = 0
        for j in range(1, config.MAX_ROSTER + 1):
            player_id = (team_id - 1) * config.MAX_ROSTER + j
            
            age = random.randint(19, 35)
            potential = random.randint(60, 99)
            contract_value = round(random.uniform(1.0, 35.0), 1)
            contract_years = random.randint(1, 4)
            
            attrs = generate_random_attributes()
            badges = generate_random_badges()
            personalities = generate_random_personalities()
            initial_ovr = calculate_initial_ovr(attrs) # 計算 OVR
            archetype = random.choice(PLAYER_ARCHETYPES) 
            total_salary += contract_value

            # 插入 Players - 【關鍵修正點】：插入 OVR, OriginalOVR, Fatigue
            cursor.execute("""
                INSERT INTO Players (PlayerID, Name, TeamID, Age, Potential, Contract, ContractYears, Archetype, OVR, OriginalOVR, Fatigue, InjuryRemainingGames) 
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (player_id, f"Player {j} ({name})", team_id, age, potential, contract_value, contract_years, archetype, 
                  initial_ovr, initial_ovr, 0.0, 0))
            
            # 插入 Attributes
            attrs_values = tuple(attrs[attr] for attr in config.FULL_ATTRIBUTES)
            attrs_placeholders = ', '.join(['?' for _ in config.FULL_ATTRIBUTES])
            cursor.execute(f"""
                INSERT INTO Player_Attributes (PlayerID, {', '.join(config.FULL_ATTRIBUTES)})
                VALUES (?, {attrs_placeholders})
            """, (player_id,) + attrs_values)
            
            # 插入 Personalities
            pers_values = tuple(personalities[p] for p in personalities.keys()) # 使用 keys 來匹配順序
            pers_placeholders = ', '.join(['?' for _ in personalities.keys()])
            cursor.execute(f"""
                INSERT INTO Player_Personalities (PlayerID, {', '.join(personalities.keys())})
                VALUES (?, {pers_placeholders})
            """, (player_id,) + pers_values)
            
            # 插入 Badges
            cursor.execute("""
                INSERT INTO Player_Badges (PlayerID, Org_T1, Org_T3, Shot_T1, Shot_T3, Fin_T1, Fin_T3, Def_T1, Def_T3)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (player_id, badges['Org_T1'], badges['Org_T3'], badges['Shot_T1'], badges['Shot_T3'], 
                  badges['Fin_T1'], badges['Fin_T3'], badges['Def_T1'], badges['Def_T3']))

            # 插入 Stats
            cursor.execute("""
                INSERT INTO Player_Stats (PlayerID) VALUES (?)
            """, (player_id,))
            
        cursor.execute("UPDATE Teams SET SalaryCap = ? WHERE TeamID = ?", (total_salary, team_id))

    # 3. 初始化選秀權
    picks = list(range(1, config.NUM_TEAMS + 1))
    random.shuffle(picks)
    for i, pick_num in enumerate(picks):
        team_id = i + 1 
        cursor.execute("""
            INSERT INTO DraftPicks (Year, PickNumber, OriginalTeamID, CurrentTeamID)
            VALUES (?, ?, ?, ?)
        """, (2026, pick_num, team_id, team_id))
        
    conn.commit()


def create_and_populate_db():
    """主函數：檢查並創建/填充數據庫。"""
    if os.path.exists(config.DB_NAME):
        print(f"警告：正在刪除舊的數據庫文件 {config.DB_NAME}...")
        os.remove(config.DB_NAME)

    conn = config.get_db_connection()
    create_tables(conn)
    populate_initial_data(conn)
    conn.close()

if __name__ == '__main__':
    create_and_populate_db()
    print(f"數據庫 {config.DB_NAME} 已創建和填充，包含 V5.0 擴展結構。")