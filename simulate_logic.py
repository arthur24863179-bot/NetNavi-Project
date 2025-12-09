import sqlite3
import random

DB_NAME = 'nba_gm.db'

# --- 核心數據讀取函數 ---

def fetch_team_roster_personalities(team_id):
    """從數據庫讀取指定球隊所有球員的 PlayerID 和個性矩陣數據。"""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    query = """
    SELECT T1.PlayerID, T2.TeamFirst, T2.AlphaDog, T2.MoneyMotivated, T2.WinningDriven, 
        T2.BallHog, T2.Shrink, T2.Mentor, T2.Cancer
    FROM Players T1 JOIN Player_Personalities T2 ON T1.PlayerID = T2.PlayerID
    WHERE T1.TeamID = ?
    """
    cursor.execute(query, (team_id,))
    columns = [desc[0] for desc in cursor.description]
    roster_data = [dict(zip(columns, row)) for row in cursor.fetchall()]
    conn.close()
    return roster_data

def fetch_player_attributes(player_id):
    """從數據庫讀取指定球員的單個屬性數據。"""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    query = """
    SELECT T1.Shooting, T1.Judgment, T1.Jump, T1.Strength, T1.Stamina, T1.Durability, 
           T1.DefenseSkill, T2.Height
    FROM Player_Attributes T1 JOIN Players T2 ON T1.PlayerID = T2.PlayerID
    WHERE T1.PlayerID = ?
    """
    cursor.execute(query, (player_id,))
    columns = [desc[0] for desc in cursor.description]
    result = cursor.fetchone()
    conn.close()
    if result:
        return dict(zip(columns, result))
    return None

# --- 1. 化學反應：性格契合計算 ---

def calculate_personality_fit(team_id):
    """實作性格契合度 (0-100) 計算。"""
    roster = fetch_team_roster_personalities(team_id)
    if not roster: return 50
    total_positive_fit = sum(p['TeamFirst'] for p in roster)
    
    alpha_dogs = [p for p in roster if p['AlphaDog'] > 70]
    num_alpha_conflicts = len(alpha_dogs) * (len(alpha_dogs) - 1) / 2
    
    total_negative_conflict = num_alpha_conflicts * 5.0 + \
                              sum(p['Cancer'] * 0.2 + p['BallHog'] * 0.1 for p in roster)

    average_team_first = total_positive_fit / len(roster)
    raw_fit = average_team_first - total_negative_conflict 
    
    return max(40, min(100, round(raw_fit, 1))) 


# --- 2. 智商籃板 (IQ Rebound) 計算 ---

def calculate_iq_rebound(player_id):
    data = fetch_player_attributes(player_id)
    if not data: return 0
    judgment, jump, strength = data['Judgment'], data['Jump'], data['Strength']
    
    W_JUD = 0.2 
    if judgment > 90: W_JUD = 0.5 
    W_BODY = 1.0 - W_JUD 
    
    body_attribute = (jump + strength) / 2
    rebound_rating = (body_attribute * W_BODY) + (judgment * W_JUD)
    return round(rebound_rating, 1)

# --- 3. 球權衝突懲罰 (Ball Hog Penalty) 計算 ---

def calculate_usage_demand(player_data):
    W_ALPHA = 0.2
    W_BHOG = 0.8
    BASE_DEMAND = 10 
    demand_score = (player_data['AlphaDog'] * W_ALPHA) + (player_data['BallHog'] * W_BHOG)
    usage_demand = BASE_DEMAND + (demand_score / 100) * 20
    return round(usage_demand, 1)

def calculate_ball_hog_penalty(team_id):
    roster_personalities = fetch_team_roster_personalities(team_id)
    on_court_roster = roster_personalities[:5] 
    if len(on_court_roster) < 5: return 0, 0, "隊伍人數不足 5 人，無法計算衝突。"
    total_usage_demand = sum(calculate_usage_demand(p) for p in on_court_roster)

    THRESHOLD = 130 
    penalty_percent = 0
    if total_usage_demand > THRESHOLD:
        overage = total_usage_demand - THRESHOLD
        penalty_percent = min(20, 10 + (overage // 10))
        
    return round(total_usage_demand, 1), penalty_percent, f"總球權需求超過 {THRESHOLD} 觸發懲罰。" if penalty_percent > 0 else "總球權需求在安全範圍內。"


# --- 4. 技術壓制 (Skill Override) 判斷 ---

def check_skill_override(player_id):
    data = fetch_player_attributes(player_id)
    if not data: return 0, "球員不存在"
    shooting, judgment = data['Shooting'], data['Judgment']
    
    if shooting > 90 and judgment > 90:
        return 0.40, f"✅ 觸發技術壓制！Shooting({shooting}) > 90 且 Judgment({judgment}) > 90。"
    else:
        return 0, f"🚫 未觸發技術壓制。Shooting({shooting}) 或 Judgment({judgment}) 不足。"


# --- 5. 疲勞與傷病 (Fatigue & Injury) 機制 ---

def calculate_fatigue_and_injury(player_id, minutes_played, current_fatigue=0):
    data = fetch_player_attributes(player_id)
    if not data: return 0, 0, "球員不存在"
    stamina, durability = data['Stamina'], data['Durability']
    
    fatigue_increase = minutes_played * (2.0 - stamina / 200.0)
    new_fatigue = current_fatigue + fatigue_increase
    new_fatigue = min(100, round(new_fatigue, 1))

    base_risk = 100.0 / durability
    injury_probability = base_risk * (new_fatigue / 100.0)
    injury_probability = round(injury_probability, 2) 
    
    return new_fatigue, injury_probability, "計算成功", stamina, durability


# --- 6. 對位剝削 (Matchup Exploit) 機制 ---

def check_matchup_exploit(offensive_player_id):
    """實作白皮書 5.2 對位剝削 (Matchup Exploit) 機制。"""
    offense_data = fetch_player_attributes(offensive_player_id)
    if not offense_data: 
        return 0, "進攻球員不存在。", 0, 0

    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    # 這裡我們隨機選一個非進攻球員作為對位防守者
    cursor.execute("""
        SELECT T1.DefenseSkill, T2.Height 
        FROM Player_Attributes T1 JOIN Players T2 ON T1.PlayerID = T2.PlayerID
        WHERE T1.PlayerID != ? ORDER BY RANDOM() LIMIT 1
    """, (offensive_player_id,))
    defender_data = cursor.fetchone()
    conn.close()

    if not defender_data:
        return 0, "無法模擬對位防守者。", 0, 0
    
    defender_dfs, defender_height = defender_data

    # 1. 身體錯位：進攻方比防守方高 0.5 米
    height_mismatch = offense_data['Height'] - defender_height
    is_mismatch = height_mismatch >= 0.5 

    # 2. 防守弱點：對位防守者的 DefenseSkill < 70
    is_defensive_weakness = defender_dfs < 70
    
    bonus = 0.0
    reason = "🚫 未觸發對位剝削。"
    
    if is_mismatch and is_defensive_weakness:
        bonus = 0.20 
        reason = f"✅ 雙重觸發！身高錯位({round(height_mismatch, 2)}m) 且 防守弱點(Dfs={defender_dfs})。"
    elif is_mismatch:
        bonus = 0.15 
        reason = f"✅ 觸發錯位！身高差距 {round(height_mismatch, 2)}m >= 0.5m。"
    elif is_defensive_weakness:
        bonus = 0.15
        reason = f"✅ 觸發防守弱點！對位Dfs={defender_dfs} < 70。"

    return bonus, reason, defender_dfs, defender_height


# --- 測試腳本：同時運行所有機制 ---

def run_test():
    """執行測試：化學反應、智商籃板、球權衝突、技術壓制、疲勞傷病與對位剝削"""
    team_id_to_test = 1
    
    # --- 測試 1: 化學反應 ---
    print("--------------------------------------------------")
    print("🔥 測試 1：化學反應 - 性格契合度 (TeamID=1)")
    print("--------------------------------------------------")
    try:
        personality_fit_score = calculate_personality_fit(team_id_to_test)
        print(f"✅ 成功讀取 TeamID={team_id_to_test} 的 15 名球員數據。")
        print(f"💡 性格契合度 (0-100) 調整後結果為: {personality_fit_score}")
        print(f"💡 性格契合對總化學反應的貢獻: {round(personality_fit_score * 0.4, 1)}")
    except Exception as e:
        print(f"🚫 化學反應測試失敗：{e}")


    # --- 測試 2: 智商籃板 ---
    print("\n--------------------------------------------------")
    print("🧠 測試 2：智商籃板 (IQ Rebound) 機制")
    print("--------------------------------------------------")
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("""
        SELECT T1.PlayerID, T2.Name, T1.Judgment, T1.Jump, T1.Strength 
        FROM Player_Attributes T1 JOIN Players T2 ON T1.PlayerID = T2.PlayerID
        WHERE T1.Judgment > 90 LIMIT 1
    """)
    player_data = cursor.fetchone()
    conn.close()
    
    if player_data:
        p_id, name, judgment, jump, strength = player_data
        rebound_score = calculate_iq_rebound(p_id)
        print(f"✅ 找到高 IQ 球員: {name} (ID: {p_id})")
        print(f"   -> 最終籃板能力評級: {rebound_score}")
        if judgment > 90:
            print("   -> 觸發 IQ Override: 預判權重已提升至 50%！")
    else:
        print("🚫 未找到 Judgment > 90 的模擬球員。")

    
    # --- 測試 3: 球權衝突懲罰 ---
    print("\n--------------------------------------------------")
    print("🏀 測試 3：球權衝突懲罰 (Ball Hog Penalty)")
    print("--------------------------------------------------")
    total_demand, penalty, message = calculate_ball_hog_penalty(team_id_to_test)
    print(f"✅ 成功計算 TeamID={team_id_to_test} 場上五人的總球權需求。")
    print(f"💡 場上五人總球權需求: {total_demand} (閾值: 130)")
    print(f"   -> 結果訊息: {message}")
    print(f"   -> 進攻效率下降懲罰: {penalty}%")


    # --- 測試 4: 技術壓制 ---
    print("\n--------------------------------------------------")
    print("🎯 測試 4：技術壓制 (Skill Override) 機制")
    print("--------------------------------------------------")
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("""
        SELECT T1.PlayerID, T2.Name, T1.Shooting, T1.Judgment
        FROM Player_Attributes T1 JOIN Players T2 ON T1.PlayerID = T2.PlayerID
        WHERE T1.Shooting > 90 AND T1.Judgment > 90 LIMIT 1
    """)
    player_data_skill = cursor.fetchone()
    conn.close()

    if player_data_skill:
        p_id, name, shooting, judgment = player_data_skill
        reduction, message = check_skill_override(p_id)
        
        print(f"✅ 找到超級射手: {name} (ID: {p_id})")
        print(f"   -> 數值: 投射(Sht): {shooting}, 判斷(Jud): {judgment}")
        print(f"   -> 減免程度: {int(reduction*100)}% (防守干擾權重)")
        print(f"   -> 結果訊息: {message}")
    else:
        print("🚫 數據庫中未找到同時滿足 Shooting > 90 且 Judgment > 90 的模擬球員。")


    # --- 測試 5: 疲勞與傷病 ---
    print("\n--------------------------------------------------")
    print("🤕 測試 5：疲勞與傷病 (Fatigue & Injury) 機制")
    print("--------------------------------------------------")
    
    test_player_id = 1
    test_minutes = 35
    initial_fatigue = 50 
    
    new_fatigue, injury_prob, message, stamina, durability = calculate_fatigue_and_injury(
        test_player_id, test_minutes, initial_fatigue
    )
    
    print(f"✅ 測試球員 ID: {test_player_id} (Player 1)")
    print(f"   -> 上場時間: {test_minutes} 分鐘")
    print(f"   -> 初始疲勞: {initial_fatigue}")
    print(f"   -> 體能(Sta): {stamina}")
    print(f"   -> 耐戰(Dur): {durability}")
    print("--- 結果 ---")
    print(f"💡 新疲勞值 (New Fatigue): {new_fatigue} (滿 100)")
    
    prob_in_ten_thousand = int(injury_prob * 10000) 
    print(f"💡 本場受傷檢定機率: {prob_in_ten_thousand} / 10000 (或 {injury_prob}%)")


    # --- 測試 6: 對位剝削 (Matchup Exploit) ---
    print("\n--------------------------------------------------")
    print("⚔️ 測試 6：對位剝削 (Matchup Exploit) 機制")
    print("--------------------------------------------------")
    
    offensive_player_id = 1
    bonus, reason, defender_dfs, defender_height = check_matchup_exploit(offensive_player_id)
    off_data = fetch_player_attributes(offensive_player_id)
    
    print(f"✅ 測試進攻球員 ID: {offensive_player_id} (Player 1) (身高: {off_data['Height']}m)")
    
    if defender_dfs != 0:
        print(f"   -> 模擬對位防守者 (身高: {defender_height}m, Dfs: {defender_dfs})")
    
    print(f"   -> 結果訊息: {reason}")
    print(f"   -> 進攻效率加成: {int(bonus*100)}%")


# 執行所有測試
if __name__ == '__main__':
    run_test()