# config.py
import sqlite3

# --- 核心數據庫設定 ---
DB_NAME = 'nba_gm_game.db'
NUM_TEAMS = 30           
SEASON_GAMES = 82        
GM_CONTROLLED_TEAM_ID = 1 

# --- 白皮書 V5.0 規格與常數 ---
MAX_ROSTER = 15     # 名單上限
MIN_ROSTER = 13     # 名單下限
ACTIVE_LIST_SIZE = 13 # 每場可登入人數

# 疲勞懲罰常數 (【致命 Bug 修正】：確保疲勞值不會溢出)
FATIGUE_DECAY_RATE = 0.85   # 每次模擬後疲勞衰減率 (強衰減)
REST_BONUS = 15.0           # 未上場球員額外恢復值
FATIGUE_OVR_THRESHOLD = 80  # 疲勞懲罰觸發值 (Fatigue > 80 全屬性 -20%)
FATIGUE_PUNISH_PCT = 0.80   # 懲罰倍率 (1.0 - 0.20)

# 完整球員屬性 (沿用您 V5.0 的 15 項屬性)
FULL_ATTRIBUTES = [
    'Height', 'Strength', 'Speed', 'Jump', 'Explosiveness', 'Stamina', 'Durability',
    'Shooting', 'Finishing', 'Handle', 'Passing', 'DefenseSkill',
    'Tactics', 'Judgment', 'Mentality'
]

# 模擬中追蹤的賽季數據 (基於您的 Player_Stats 表格欄位)
STATS_COLUMNS = [
    'GamesPlayed', 'MinutesPlayed', 'Points', 'Rebounds', 'Assists', 'Steals', 
    'Blocks', 'Turnovers', 'FG_Attempt', 'FG_Made', 'ThreeP_Attempt', 
    'ThreeP_Made', 'FT_Attempt', 'FT_Made'
]

def get_db_connection():
    """獲取數據庫連線"""
    return sqlite3.connect(DB_NAME)