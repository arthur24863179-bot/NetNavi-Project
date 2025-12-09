import sqlite3
import random
from datetime import date 

# --- 導入核心運算引擎 ---
from simulate_logic import (
    calculate_personality_fit, 
    calculate_ball_hog_penalty, 
    check_skill_override,
    check_matchup_exploit,
    calculate_fatigue_and_injury,
    fetch_player_attributes 
)

# --- 導入戰略層數據 (NEW IMPORT) ---
from strategy_logic import OFFENSIVE_STYLES 

DB_NAME = 'nba_gm.db'

# --- 數據持久化函數 (不變) ---

def save_game_stats(team1_id, team2_id, final_score, minutes_played, final_fatigue, injury_checks, game_log):
    """將比賽結果寫入數據庫中的統計表格。"""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    
    # 1. 寫入 Game_Schedule
    cursor.execute("""
    INSERT INTO Game_Schedule (HomeTeamID, AwayTeamID, GameDate, HomeScore, AwayScore, IsPlayed)
    VALUES (?, ?, ?, ?, ?, 1)
    """, (team1_id, team2_id, date.today().isoformat(), final_score[team1_id], final_score[team2_id]))

    # 2. 更新 Team_Stats
    t1_wins_change = 1 if final_score[team1_id] > final_score[team2_id] else 0
    t2_wins_change = 1 - t1_wins_change
    t1_losses_change = 1 - t1_wins_change
    t2_losses_change = 1 - t2_wins_change

    for team_id, wins, losses, pts_scored, pts_allowed in [(team1_id, t1_wins_change, t1_losses_change, final_score[team1_id], final_score[team2_id]), 
                                                            (team2_id, t2_wins_change, t2_losses_change, final_score[team2_id], final_score[team1_id])]:
        cursor.execute("""
        UPDATE Team_Stats 
        SET Wins = Wins + ?, Losses = Losses + ?, PointsScored = PointsScored + ?, PointsAllowed = PointsAllowed + ?
        WHERE TeamID = ?
        """, (wins, losses, pts_scored, pts_allowed, team_id))

    # 3. 更新 Player_Stats
    player_points = {}
    for _, _, p_id, points, _, _ in game_log:
        player_points[p_id] = player_points.get(p_id, 0) + points

    for p_id in minutes_played:
        mins = minutes_played[p_id]
        if mins > 0:
            fatigue = final_fatigue.get(p_id, 0.0)
            injury_data = injury_checks.get(p_id, {})
            points_scored = player_points.get(p_id, 0)
            
            injury_status = 'Healthy'
            if random.random() < injury_data.get('prob', 0):
                injury_status = 'Injured' 

            # 獲取現有數據進行累積計算 (累積 PPG/MPG)
            cursor.execute("SELECT GP, PPG, MPG FROM Player_Stats WHERE PlayerID = ?", (p_id,))
            current_data = cursor.fetchone()
            # 處理第一次插入數據的情況
            current_gp, current_ppg, current_mpg = current_data if current_data else (0, 0.0, 0.0)

            new_gp = current_gp + 1
            new_total_mp = current_mpg * current_gp + mins
            new_total_pts = current_ppg * current_gp + points_scored
            
            new_mpg = round(new_total_mp / new_gp, 1) if new_gp > 0 else 0.0
            new_ppg = round(new_total_pts / new_gp, 1) if new_gp > 0 else 0.0
            
            # 使用 INSERT OR REPLACE 確保數據存在
            cursor.execute("""
            INSERT OR REPLACE INTO Player_Stats (PlayerID, GP, MPG, PPG, Fatigue, InjuryStatus)
            VALUES (?, ?, ?, ?, ?, ?)
            """, (p_id, new_gp, new_mpg, new_ppg, fatigue, injury_status))
    
    conn.commit()
    conn.close()
    print("\n✅ 數據持久化完成：比賽結果與統計數據已成功保存至數據庫。")

# --- A. 模擬單一回合進攻 (UPDATED: 接受戰術風格參數) ---
def simulate_possession(offense_player_id, defense_player_id, team_id, team_chemistry, team_ball_hog_penalty, off_style, def_style):
    """
    模擬單一回合的進攻，整合所有核心機制。
    返回: 得分 (0, 2, 或 3), 備註, 觸發機制列表
    """
    off_data = fetch_player_attributes(offense_player_id)
    if not off_data:
        return 0, "球員數據缺失", []

    base_off_rating = (off_data['Shooting'] + off_data['Judgment']) / 200.0 # 0.0 - 1.0

    modifier = 0.0
    notes = []

    # --- 應用深度機制 ---

    # 2a. 技術壓制
    skill_reduction, skill_note = check_skill_override(offense_player_id)
    if skill_reduction > 0:
        modifier += 0.05
        notes.append(f"[技術壓制]: {skill_note}。+5% 命中率。")
    
    # 2b. 對位剝削
    exploit_bonus, exploit_note, *_ = check_matchup_exploit(offense_player_id) 
    modifier += exploit_bonus 
    if exploit_bonus > 0:
        notes.append(f"[對位剝削]: {exploit_note}。+{int(exploit_bonus*100)}% 效率。")

    # 2c. 化學反應
    if team_chemistry > 80:
        modifier += 0.03
        notes.append(f"[化學反應]: Chem({team_chemistry}) > 80. +3% 團隊效率。")
    elif team_chemistry < 40:
        modifier -= 0.05
        notes.append(f"[化學反應]: Chem({team_chemistry}) < 40. -5% 失誤增加。")

    # 2d. 球權衝突
    modifier -= team_ball_hog_penalty / 100.0
    if team_ball_hog_penalty > 0:
        notes.append(f"[球權衝突]: -{team_ball_hog_penalty}% 效率懲罰。")
        
    # 2e. 戰術風格相剋 (NEW LOGIC)
    strategic_mod = 0.0
    off_style_data = OFFENSIVE_STYLES.get(off_style, OFFENSIVE_STYLES['BALANCED'])
    
    # 檢查是否克制 OR 被懼怕
    if off_style_data.get('counter') and off_style_data['counter'] == def_style:
        strategic_mod += 0.05 # 5% 效率加成
        notes.append(f"[戰術克制]: {off_style} 克制 {def_style}。+5% 團隊效率！")
    elif off_style_data.get('fear') and off_style_data['fear'] == def_style:
        strategic_mod -= 0.05 # 5% 效率懲罰
        notes.append(f"[戰術懼怕]: {off_style} 懼怕 {def_style}。-5% 團隊效率！")
        
    modifier += strategic_mod

    # 3. 最終命中率
    final_prob = max(0.2, min(0.9, base_off_rating + modifier))

    # 4. 判斷得分結果
    if random.random() < final_prob:
        is_three_pointer = random.random() < 0.35 
        points = 3 if is_three_pointer else 2
        outcome = f"命中並得分 {points} 分。(Final Prob: {round(final_prob*100, 1)}%)"
        return points, outcome, notes
    else:
        is_turnover = random.random() < (0.10 - team_chemistry * 0.0005) 
        points = 0
        outcome = "失誤" if is_turnover else "投籃不進/被防守成功"
        return points, outcome, notes


# --- B. 模擬一場完整的比賽 (UPDATED: 讀取戰術風格) ---
def simulate_game(team1_id, team2_id, total_possessions=200):
    """
    模擬一場完整的比賽，並在結束後保存數據。
    """
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    # 1. 賽前準備：讀取名單、初始疲勞、和戰術風格 (NEW)
    roster_query = "SELECT PlayerID FROM Players WHERE TeamID = ? LIMIT 5"
    cursor.execute(roster_query, (team1_id,))
    team1_roster = [row[0] for row in cursor.fetchall()]
    cursor.execute(roster_query, (team2_id,))
    team2_roster = [row[0] for row in cursor.fetchall()]
    
    # NEW: 讀取戰術風格
    cursor.execute("SELECT OffenseStyle, DefenseScheme FROM Teams WHERE TeamID = ?", (team1_id,))
    t1_off_style, t1_def_scheme = cursor.fetchone()
    cursor.execute("SELECT OffenseStyle, DefenseScheme FROM Teams WHERE TeamID = ?", (team2_id,))
    t2_off_style, t2_def_scheme = cursor.fetchone()
    
    # 讀取初始疲勞
    player_fatigue = {}
    for p_id in team1_roster + team2_roster:
        cursor.execute("SELECT Fatigue FROM Player_Stats WHERE PlayerID = ?", (p_id,))
        fatigue_data = cursor.fetchone()
        player_fatigue[p_id] = fatigue_data[0] if fatigue_data and fatigue_data[0] is not None else random.randint(0, 40)
    conn.close()

    if not team1_roster or not team2_roster:
        return "錯誤：隊伍數據不足。", {}, {}, {}, []
    
    score = {team1_id: 0, team2_id: 0}
    minutes_played = {p: 0.0 for p in team1_roster + team2_roster}
    
    # 預先計算團隊永久性修正值
    team1_chem = calculate_personality_fit(team1_id)
    _, team1_hog_penalty, _ = calculate_ball_hog_penalty(team1_id)
    team2_chem = calculate_personality_fit(team2_id)
    _, team2_hog_penalty, _ = calculate_ball_hog_penalty(team2_id)
    
    game_log = []
    
    print(f"--- 📊 模擬比賽開始 (總回合數: {total_possessions}) ---")
    print(f"Team {team1_id} (Off Style: {t1_off_style}) vs. Team {team2_id} (Off Style: {t2_off_style})")
    
    for i in range(1, total_possessions + 1):
        # --- Team 1 進攻 ---
        off_p1 = random.choice(team1_roster)
        def_p2 = random.choice(team2_roster)
        # 傳入戰術風格參數
        points, outcome, notes = simulate_possession(off_p1, def_p2, team1_id, team1_chem, team1_hog_penalty, t1_off_style, t2_def_scheme)
        score[team1_id] += points
        game_log.append((i, team1_id, off_p1, points, outcome, notes))
        minutes_played[off_p1] += 0.5 

        # --- Team 2 進攻 ---
        off_p2 = random.choice(team2_roster)
        def_p1 = random.choice(team1_roster)
        # 傳入戰術風格參數
        points, outcome, notes = simulate_possession(off_p2, def_p1, team2_id, team2_chem, team2_hog_penalty, t2_off_style, t1_def_scheme)
        score[team2_id] += points
        game_log.append((i, team2_id, off_p2, points, outcome, notes))
        minutes_played[off_p2] += 0.5

    # 2. 賽後結算與數據持久化
    final_fatigue = {}
    injury_checks = {}
    
    for player_id in minutes_played:
        if minutes_played[player_id] > 0:
            initial_f = player_fatigue.get(player_id, 0)
            new_f, injury_prob, _, stamina, durability = calculate_fatigue_and_injury(
                player_id, minutes_played[player_id], initial_f
            )
            final_fatigue[player_id] = new_f
            injury_checks[player_id] = {'prob': injury_prob, 'sta': stamina, 'dur': durability}
            
    save_game_stats(team1_id, team2_id, score, minutes_played, final_fatigue, injury_checks, game_log)
    
    return score, minutes_played, final_fatigue, injury_checks, game_log


# --- C. 執行模擬測試 (不變) ---
def run_simulation_test():
    """執行模擬測試並輸出結果"""
    
    TEAM_A_ID = 1
    TEAM_B_ID = 2 
    
    final_score, minutes, final_fatigue, injury_checks, game_log = simulate_game(TEAM_A_ID, TEAM_B_ID)

    # 輸出比賽結果
    print("\n--------------------------------------------------")
    print("🏆 最終比分 (Final Score) 🏆")
    print("--------------------------------------------------")
    print(f"Team {TEAM_A_ID}: {final_score[TEAM_A_ID]} (Off Style: {final_score[TEAM_A_ID] > final_score[TEAM_B_ID] and 'PACE' or 'GRIND'})")
    print(f"Team {TEAM_B_ID}: {final_score[TEAM_B_ID]}")
    
    if final_score[TEAM_A_ID] > final_score[TEAM_B_ID]:
        print(f"🎉 Team {TEAM_A_ID} 獲勝！")
    elif final_score[TEAM_A_ID] < final_score[TEAM_B_ID]:
        print(f"🎉 Team {TEAM_B_ID} 獲勝！")
    else:
        print("🤝 平手！")

    # 輸出賽後結算
    print("\n--------------------------------------------------")
    print("🤕 賽後結算：疲勞與傷病 (Fatigue & Injury)")
    print("--------------------------------------------------")
    
    top_players = sorted(minutes.items(), key=lambda item: item[1], reverse=True)[:5]
    
    for p_id, min_played in top_players:
        if min_played > 0:
            fatigue = final_fatigue.get(p_id, 'N/A')
            injury_data = injury_checks.get(p_id, {})
            prob = injury_data.get('prob', 0) * 100
            sta = injury_data.get('sta', 'N/A')
            dur = injury_data.get('dur', 'N/A')
            
            # 查詢數據庫中的最新狀態 (確認數據已保存)
            conn = sqlite3.connect(DB_NAME)
            cursor = conn.cursor()
            cursor.execute("SELECT GP, PPG, InjuryStatus FROM Player_Stats WHERE PlayerID = ?", (p_id,))
            db_stats = cursor.fetchone()
            conn.close()

            print(f"Player {p_id} (Sta:{sta}/Dur:{dur}):")
            print(f"  -> 上場時間: {round(min_played, 1)} 分鐘 (賽季總GP: {db_stats[0]})")
            print(f"  -> 賽季平均得分(PPG): {db_stats[1]}")
            print(f"  -> 最終疲勞: {fatigue} / 100")
            print(f"  -> 傷病檢定機率: {round(prob, 2)}% (DB 狀態: {db_stats[2]})")

    # 輸出深度機制觸發範例 (確認戰術克制觸發)
    print("\n--------------------------------------------------")
    print("💡 深度機制觸發範例 (Possession Log)")
    print("--------------------------------------------------")
    
    # 尋找一個有觸發機制的 log 
    for i, team_id, player_id, points, outcome, notes in game_log:
        if notes:
            print(f"回合 {i} - Team {team_id} 進攻 (Player {player_id}):")
            print(f"  結果: {outcome}")
            for note in notes:
                print(f"  - {note}")
            break 
    else:
        print("本次模擬中沒有顯著的深度機制觸發。")


if __name__ == '__main__':
    run_simulation_test()