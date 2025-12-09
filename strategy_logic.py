# strategy_logic.py
"""
NBA GM 模擬器：戰略層邏輯定義 (白皮書 V5.0 第 3 & 4 節)
定義了八大進攻風格、七大防守策略和十大戰術角色。
"""

# --- 1. 八大進攻風格定義 (Offensive Styles) ---
# 數據來源：白皮書 V5.0 4.1 節 [cite: 57]
OFFENSIVE_STYLES = {
    # 風格: {節奏(Pace), 助攻率(AstRate), 克制(Counter), 懼怕(Fear)}
    "PACE": {
        "pace_mult": 1.30, 
        "assist_rate": 0.60, 
        "counter": "GRIND", 
        "fear": "MOTION",
        "desc": "極速攻防，擅長轉換快攻。"
    },
    "GRIND": {
        "pace_mult": 0.85, 
        "assist_rate": 0.50, 
        "counter": "MOTION", 
        "fear": "PACE",
        "desc": "陣地肉搏戰，注重低位與護框。"
    },
    "MOTION": {
        "pace_mult": 1.00, 
        "assist_rate": 0.75, 
        "counter": "PACE", 
        "fear": "GRIND",
        "desc": "極致傳導球，偏好組織前鋒。"
    },
    "ISO": {
        "pace_mult": 0.95, 
        "assist_rate": 0.40, 
        "counter": "BALANCED", 
        "fear": "ZONE",
        "desc": "球星單打決勝，低助攻率。"
    },
    "PnR": {
        "pace_mult": 1.05, 
        "assist_rate": 0.65, 
        "counter": "MAN_TO_MAN", 
        "fear": "SWITCH",
        "desc": "擋拆二人轉為核心。"
    },
    "TRIANGLE": {
        "pace_mult": 0.90, 
        "assist_rate": 0.55, 
        "counter": "SWITCH", 
        "fear": "ZONE",
        "desc": "低位策應，三角戰術體系。"
    },
    "5-OUT": {
        "pace_mult": 1.15, 
        "assist_rate": 0.50, 
        "counter": "DROP", 
        "fear": "SWITCH",
        "desc": "五外拉開空間，全隊三分威脅。"
    },
    "BALANCED": {
        "pace_mult": 1.00, 
        "assist_rate": 0.55, 
        "counter": None, 
        "fear": None,
        "desc": "適應性強，均衡發揮。"
    },
}

# --- 2. 七大防守策略定義 (Defensive Schemes) ---
# 數據來源：白皮書 V5.0 4.2 節 [cite: 59-65]
DEFENSIVE_SCHEMES = [
    "MAN_TO_MAN",       # 標準人盯人 [cite: 59]
    "SWITCH_ALL",       # 無限換防 (剋擋拆/五外，怕錯位單打) [cite: 60]
    "DROP_COVERAGE",    # 沉退護框 (怕中距離/持球投射) [cite: 61]
    "ZONE_2-3",         # 2-3 聯防 (剋內線，怕射手隊) [cite: 62]
    "ZONE_3-2",         # 3-2 聯防 (壓迫外線，漏籃板) [cite: 63]
    "FULL_COURT_PRESS", # 全場緊逼 (製造失誤，體力消耗大) [cite: 64]
    "BOX_AND_1",        # 一盯四聯 (鎖死單核，怕多核隊) [cite: 65]
]

# --- 3. 十大戰術角色定義 (Tactical Archetypes) ---
# 數據來源：白皮書 V5.0 3.2 節 [cite: 50-54]
TACTICAL_ARCHETYPES = [
    # 持球類 [cite: 50]
    "HANDLER",      # 持球大核
    "POINT_FWD",    # 組織前鋒
    # 得分類 [cite: 51]
    "SCORER",       # 萬花筒
    "SLASHER",      # 撕裂者
    "POST_UP",      # 低位殺器
    # 輔助類 [cite: 52]
    "SPACER",       # 空間射手
    "ROLL_MAN",     # 擋拆吃餅
    # 防守類 [cite: 53]
    "LOCKDOWN",     # 領防大鎖
    "ANCHOR",       # 護框門神
    "HUSTLE",       # 拼命三郎
    # 策應類 [cite: 54]
    "LINK",         # 戰術策應
]

# --- 測試函數 (可選，用於確認數據結構) ---
def print_strategic_data():
    """輸出戰略數據結構以供驗證。"""
    print("--- 🏀 戰略層數據結構初始化 ---")
    print(f"1. 進攻風格總數: {len(OFFENSIVE_STYLES)}")
    print(f"   -> 跑轟節奏乘數: {OFFENSIVE_STYLES['PACE']['pace_mult']}")
    print(f"2. 防守策略總數: {len(DEFENSIVE_SCHEMES)}")
    print(f"   -> 第 3 個策略: {DEFENSIVE_SCHEMES[2]} (沉退)")
    print(f"3. 戰術角色總數: {len(TACTICAL_ARCHETYPES)}")
    print(f"   -> 持球大核: {TACTICAL_ARCHETYPES[0]}")
    
# if __name__ == '__main__':
#     print_strategic_data()