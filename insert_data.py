import sqlite3
import random
import os

DB_NAME = 'nba_gm.db'

# --- 1. 定義系統配置數據 (來自白皮書 4.1 & 4.2) ---
OFFENSE_STYLES = [
    ("PACE", "OffenseStyle", 1.30, 60, "剋 GRIND / 怕 MOTION"),
    ("GRIND", "OffenseStyle", 0.85, 50, "剋 MOTION / 怕 PACE"),
    ("MOTION", "OffenseStyle", 1.00, 75, "剋 PACE / 怕 GRIND"),
    ("ISO", "OffenseStyle", 0.95, 40, "剋 BALANCED / 怕 ZONE"),
    ("PnR", "OffenseStyle", 1.05, 65, "剋 MAN_TO_MAN / 怕 SWITCH"),
    ("TRIANGLE", "OffenseStyle", 0.90, 55, "剋 SWITCH / 怕 ZONE"),
    ("5-OUT", "OffenseStyle", 1.15, 50, "剋 DROP / 怕 SWITCH"),
    ("BALANCED", "OffenseStyle", 1.00, 55, "適應性強"),
]

DEFENSE_SCHEMES = [
    ("Man-to-Man", "DefenseScheme", None, None, None),
    ("Switch All", "DefenseScheme", None, None, None),
    ("Drop Coverage", "DefenseScheme", None, None, None),
    ("Zone 2-3", "DefenseScheme", None, None, None),
    ("Zone 3-2", "DefenseScheme", None, None, None),
    ("Full Court Press", "DefenseScheme", None, None, None),
    ("Box-and-1", "DefenseScheme", None, None, None),
]

AI_LOGIC_TYPES = ["Contender", "Rebuilder", "Buyer", "Seller"] # 來自白皮書 6.5 [cite: 110-113]
POSITIONS = ["PG", "SG", "SF", "PF", "C"]
ROTATION_ROLES = ["STAR", "STARTER", "SIXTH", "ROTATION", "BENCH", "GARBAGE"]
TACTICAL_ARCHETYPES = ["HANDLER", "SCORER", "SPACER", "LOCKDOWN", "ANCHOR"] # 簡化選取
BASE_TEAM_NAMES = [f"Team {i+1}" for i in range(30)]


def get_random_rating():
    """生成 60-95 之間的隨機數值 (模擬能力分佈)"""
    return random.randint(60, 95)

def get_random_personality():
    """生成 0-100 之間的隨機個性數值"""
    return random.randint(0, 100)


def insert_initial_data():
    """將所有配置、球隊、教練和球員數據插入數據庫"""
    if not os.path.exists(DB_NAME):
        print(f"🚫 數據庫文件 {DB_NAME} 不存在，請先運行 create_db.py")
        return

    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    
    try:
        # --- 2. 插入系統配置 (System_Config) ---
        print("-> 插入 System_Config...")
        config_data = OFFENSE_STYLES + DEFENSE_SCHEMES
        cursor.executemany("""
            INSERT INTO System_Config (Name, Category, Parameter1, Parameter2, CounterType)
            VALUES (?, ?, ?, ?, ?)
        """, config_data)
        
        
        # --- 3. 插入教練與球隊數據 (Coaches & Teams) ---
        print("-> 插入 Coaches & Teams (共 30 隊)...")
        coach_id_counter = 1
        team_id_counter = 1
        
        for name in BASE_TEAM_NAMES:
            # 創建教練
            coach_name = f"Coach {name}"
            off_style = random.choice(OFFENSE_STYLES)[0]
            def_scheme = random.choice(DEFENSE_SCHEMES)[0]
            iga = random.randint(70, 95) # IGA (臨場應變評級) [cite: 67]
            ai_logic = random.choice(AI_LOGIC_TYPES) # AI 行為模式 [cite: 110-113]
            
            cursor.execute("""
                INSERT INTO Coaches (CoachID, Name, OffenseStyle, DefenseScheme, IGA_Rating, AILogic)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (coach_id_counter, coach_name, off_style, def_scheme, iga, ai_logic))

            # 創建球隊
            # 初始財務數據 (薪資帽 $140M, 豪華稅 $165M [cite: 97, 98])
            initial_salary = random.uniform(130, 170) * 1_000_000
            initial_cash = random.uniform(50, 150) * 1_000_000
            
            cursor.execute("""
                INSERT INTO Teams (TeamID, TeamName, CoachID, CashBalance, CurrentTotalSalary, RosterCount)
                VALUES (?, ?, ?, ?, ?, 0)
            """, (team_id_counter, name, coach_id_counter, initial_cash, initial_salary))
            
            coach_id_counter += 1
            team_id_counter += 1


        # --- 4. 插入球員數據 (Players, Attributes, Personalities, Contracts) ---
        print("-> 插入 450 名球員數據 (含屬性、個性、合約)...")
        player_id_counter = 1
        for team_id in range(1, 31):
            team_name = BASE_TEAM_NAMES[team_id - 1]
            roster_size = 15 # 確保名單上限 15 人 

            for i in range(roster_size):
                # PlayerID 必須唯一
                
                # a. 插入 Players 主表
                player_name = f"Player {player_id_counter} ({team_name})"
                pos = random.choice(POSITIONS)
                height = round(random.uniform(6.0, 7.3), 1) # 身高臂展 
                age = random.randint(19, 39)
                mentality = get_random_rating() # Mentality 來自 IQ 心智類 
                role = random.choice(ROTATION_ROLES)
                archetype = random.choice(TACTICAL_ARCHETYPES)
                
                cursor.execute("""
                    INSERT INTO Players (PlayerID, Name, Position, Height, Age, TeamID, Mentality, TacticalArchetype, RoleInRotation)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (player_id_counter, player_name, pos, height, age, team_id, mentality, archetype, role))
                
                # b. 插入 Player_Attributes 素質表 (14個欄位)
                # 確保覆蓋白皮書所有 11 個素質 
                attributes = {
                    'Strength': get_random_rating(), 'Speed': get_random_rating(),
                    'Jump': get_random_rating(), 'Explosiveness': get_random_rating(),
                    'Stamina': get_random_rating(), 'Durability': get_random_rating(),
                    'Shooting': get_random_rating(), 'Finishing': get_random_rating(),
                    'Handle': get_random_rating(), 'Passing': get_random_rating(),
                    'DefenseSkill': get_random_rating(), 'Tactics': get_random_rating(), 
                    'Judgment': get_random_rating(),
                }
                
                cursor.execute(f"""
                    INSERT INTO Player_Attributes (
                        PlayerID, {', '.join(attributes.keys())}
                    ) VALUES (?, {', '.join(['?'] * len(attributes))})
                """, (player_id_counter, *attributes.values()))
                
                # c. 插入 Player_Personalities 個性表 (8個欄位)
                # 確保覆蓋白皮書所有 8 種個性 
                personalities = {
                    'TeamFirst': get_random_personality(), 'AlphaDog': get_random_personality(),
                    'MoneyMotivated': get_random_personality(), 'WinningDriven': get_random_personality(),
                    'BallHog': get_random_personality(), 'Shrink': get_random_personality(),
                    'Mentor': get_random_personality(), 'Cancer': get_random_personality(),
                }
                
                cursor.execute(f"""
                    INSERT INTO Player_Personalities (
                        PlayerID, {', '.join(personalities.keys())}
                    ) VALUES (?, {', '.join(['?'] * len(personalities))})
                """, (player_id_counter, *personalities.values()))
                
                # d. 插入 Contracts 合約表 (簡化為 1-4 年合約)
                contract_years = random.randint(1, 4)
                salary = random.uniform(1_000_000, 45_000_000)
                
                cursor.execute("""
                    INSERT INTO Contracts (PlayerID, TeamID, CurrentYear, SalaryThisYear, YearsRemaining)
                    VALUES (?, ?, ?, ?, ?)
                """, (player_id_counter, team_id, 1, salary, contract_years))
                
                # e. 更新 Teams 表 RosterCount
                cursor.execute("UPDATE Teams SET RosterCount = RosterCount + 1 WHERE TeamID = ?", (team_id,))
                
                player_id_counter += 1
                
        # --- 5. 插入徽章 (Badges) 與選秀權 (DraftPicks) ---
        print("-> 插入 Badges (隨機) 與 DraftPicks (模擬)...")
        BADGE_TYPES = ["組織類", "投射類", "終結類", "防守類", "護框類", "內線類"]
        TIERS = ["T1", "T2", "T3"]
        
        for p_id in range(1, player_id_counter):
            # 每個球員隨機獲得 1-4 個徽章
            for _ in range(random.randint(1, 4)):
                badge_cat = random.choice(BADGE_TYPES)
                badge_tier = random.choice(TIERS)
                badge_name = f"{badge_cat}-{badge_tier}-{random.randint(1, 99)}" # 簡化徽章名稱
                
                try:
                    cursor.execute("""
                        INSERT INTO Badges (PlayerID, BadgeCategory, BadgeName, Tier)
                        VALUES (?, ?, ?, ?)
                    """, (p_id, badge_cat, badge_name, badge_tier))
                except sqlite3.IntegrityError:
                    # 避免 UNIQUE(PlayerID, BadgeName) 限制導致的錯誤
                    pass

        # 模擬 30 支球隊未來 3 年的選秀權
        for team_id in range(1, 31):
            for year in [2026, 2027, 2028]:
                # 模擬第一輪選秀權
                cursor.execute("""
                    INSERT INTO DraftPicks (TeamID, OriginalTeamID, DraftYear, Round, Protection)
                    VALUES (?, ?, ?, ?, ?)
                """, (team_id, team_id, year, 1, "Unprotected"))
                # 模擬第二輪選秀權
                cursor.execute("""
                    INSERT INTO DraftPicks (TeamID, OriginalTeamID, DraftYear, Round, Protection)
                    VALUES (?, ?, ?, ?, ?)
                """, (team_id, team_id, year, 2, None))
                
        
        conn.commit()
        print("\n🎉 數據庫初始化完成！")
        print("已插入 30 支球隊, 450 名球員, 教練, 合約, 徽章與選秀權數據。")
        print("現在您可以開始撰寫模擬運算引擎的程式碼了。")

    except sqlite3.Error as e:
        print(f"🚫 數據插入失敗：{e}")
    finally:
        if conn:
            conn.close()

# 執行函數
insert_initial_data()