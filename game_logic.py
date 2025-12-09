# game_logic.py (核心模擬邏輯)
import config
import db_interface as db
import random
import math

# --- 核心邏輯修正 1：疲勞與 OVR 懲罰修正 ---

def normalize_and_decay_fatigue(player_id, minutes_played):
    """【致命 Bug 修正】規範疲勞數值並進行衰減。"""
    player_data = db.get_player_full_data(player_id)
    if not player_data: return

    current_fatigue = player_data.get('Fatigue', 0)
    stamina = player_data.get('Stamina', 50) 

    # 1. 疲勞累積 (V5.0 公式: Fatigue += Mins * (2.0 - Sta/200))
    fatigue_increase = minutes_played * (2.0 - stamina / 200.0)
    new_fatigue = current_fatigue + fatigue_increase

    # 2. 衰減與恢復
    if minutes_played == 0:
        decayed_fatigue = max(0, new_fatigue * config.FATIGUE_DECAY_RATE - config.REST_BONUS)
    else:
        decayed_fatigue = max(0, new_fatigue * config.FATIGUE_DECAY_RATE)

    # 3. 最終規範：將疲勞值硬性限制在 0-100 之間 (【解決溢出】)
    final_fatigue = min(100.0, max(0.0, decayed_fatigue)) 
    
    db.update_player_state(player_id, 'Fatigue', final_fatigue)


def calculate_modified_ovr(player_data):
    """計算懲罰後的 OVR，用於決定輪替和表現。"""
    original_ovr = player_data.get('OriginalOVR', 50)
    current_fatigue = player_data.get('Fatigue', 0)
    
    fatigue_for_check = min(100, current_fatigue) 
    modified_ovr = original_ovr
    
    if player_data.get('InjuryRemainingGames', 0) > 0:
        modified_ovr = original_ovr * config.FATIGUE_PUNISH_PCT
    elif fatigue_for_check > config.FATIGUE_OVR_THRESHOLD:
        # 疲勞懲罰 (> 80 全屬性 -20%)
        modified_ovr = original_ovr * config.FATIGUE_PUNISH_PCT
        
    db.update_player_state(player_data['PlayerID'], 'OVR', round(modified_ovr))
    
    return round(modified_ovr)

# --- 核心邏輯修正 2：單場數據累積 ---

def simulate_game_action(player_id, team_efficiency, rotation_mins):
    """模擬單一球員在比賽中的行為並產生統計數據。"""
    if rotation_mins <= 0:
        return dict.fromkeys(config.STATS_COLUMNS, 0)

    player_data = db.get_player_full_data(player_id)
    if not player_data or player_data.get('InjuryRemainingGames', 0) > 0:
        return dict.fromkeys(config.STATS_COLUMNS, 0)

    modified_ovr = calculate_modified_ovr(player_data) 
    
    base_factor = modified_ovr / 100.0 * team_efficiency * (rotation_mins / 82) 
    
    fga = random.randint(int(base_factor * 8), int(base_factor * 18))
    tpa = random.randint(0, fga // 2)
    fta = random.randint(int(base_factor * 2), int(base_factor * 6))
    
    shooting_skill = player_data.get('Shooting', 50)
    fg_pct = (shooting_skill / 100.0) * 0.3 + 0.35 
    
    fgm = round(fga * fg_pct)
    tpm = round(tpa * fg_pct * 1.1) if tpa > 0 else 0
    ftm = round(fta * (player_data.get('Judgment', 70) / 100.0))

    points = fgm * 2 + tpm + ftm

    stats = {
        'GamesPlayed': 1,
        'MinutesPlayed': rotation_mins,
        'Points': points,
        'Rebounds': random.randint(int(base_factor * 3), int(base_factor * 12)),
        'Assists': random.randint(int(base_factor * 1), int(base_factor * 8)),
        'Steals': random.randint(0, 3),
        'Blocks': random.randint(0, 3),
        'Turnovers': random.randint(0, 5),
        'FG_Attempt': fga,
        'FG_Made': fgm,
        'ThreeP_Attempt': tpa,
        'ThreeP_Made': tpm,
        'FT_Attempt': fta,
        'FT_Made': ftm
    }
    
    return stats


def determine_rotation(team_id):
    """確保輪替是基於當前 OVR (已修正疲勞懲罰)。"""
    player_ids = db.get_players_on_roster(team_id)
    roster_data = []
    
    for pid in player_ids:
        p_data = db.get_player_full_data(pid)
        if p_data and p_data.get('InjuryRemainingGames', 0) == 0:
            current_ovr = calculate_modified_ovr(p_data) 
            roster_data.append({'PlayerID': pid, 'OVR': current_ovr})
            
    roster_data.sort(key=lambda x: x['OVR'], reverse=True)
    
    rotations = {}
    
    if len(roster_data) >= config.ACTIVE_LIST_SIZE:
        # 核心輪替 (前 13 名球員)
        rotations[roster_data[0]['PlayerID']] = random.randint(34, 38) 
        rotations[roster_data[1]['PlayerID']] = random.randint(30, 35)
        rotations[roster_data[2]['PlayerID']] = random.randint(28, 33)
        rotations[roster_data[3]['PlayerID']] = random.randint(25, 30)
        for i in range(4, 8):
             rotations[roster_data[i]['PlayerID']] = random.randint(18, 28)
        for i in range(8, config.ACTIVE_LIST_SIZE):
             rotations[roster_data[i]['PlayerID']] = random.randint(5, 15)

    return rotations

def simulate_single_game(team_id_1, team_id_2):
    """模擬單場比賽並正確寫入數據。"""
    rot_1 = determine_rotation(team_id_1)
    rot_2 = determine_rotation(team_id_2)

    team_eff_1, team_eff_2 = 1.0, 1.0 
    team1_total_score = 0
    team2_total_score = 0

    # 1. 模擬 Team 1 
    for player_id, minutes in rot_1.items():
        stats = simulate_game_action(player_id, team_eff_1, minutes)
        if stats['GamesPlayed'] > 0:
            db.update_player_game_stats(player_id, stats)
            team1_total_score += stats['Points']
        normalize_and_decay_fatigue(player_id, minutes) 
        
    # 2. 模擬 Team 2 
    for player_id, minutes in rot_2.items():
        stats = simulate_game_action(player_id, team_eff_2, minutes)
        if stats['GamesPlayed'] > 0:
            db.update_player_game_stats(player_id, stats)
            team2_total_score += stats['Points']
        normalize_and_decay_fatigue(player_id, minutes) 
        
    # 3. 處理未上場球員的疲勞恢復
    all_players_t1 = db.get_players_on_roster(team_id_1)
    all_players_t2 = db.get_players_on_roster(team_id_2)
    
    for pid in all_players_t1:
        if pid not in rot_1:
            normalize_and_decay_fatigue(pid, 0)
    for pid in all_players_t2:
        if pid not in rot_2:
            normalize_and_decay_fatigue(pid, 0)

    # 4. 更新戰績
    if team1_total_score > team2_total_score:
        db.update_team_standing(team_id_1, win=True)
        db.update_team_standing(team_id_2, win=False)
        winner = team_id_1
    else:
        db.update_team_standing(team_id_1, win=False)
        db.update_team_standing(team_id_2, win=True)
        winner = team_id_2

    return f"比賽結束: Team {team_id_1} ({team1_total_score:.0f}) vs Team {team_id_2} ({team2_total_score:.0f}). Winner: Team {winner}"


def simulate_season():
    """模擬整個賽季"""
    teams = list(range(1, config.NUM_TEAMS + 1))
    
    for i in range(config.SEASON_GAMES):
        t1 = random.choice(teams)
        t2 = random.choice(teams)
        while t1 == t2:
            t2 = random.choice(teams)

        simulate_single_game(t1, t2)
        
        if (i+1) % 410 == 0: 
             print(f"... 模擬賽季中：已完成約 {i+1} 場比賽 ...")
    
    print(f"✅ 賽季模擬完成！")
    return "賽季模擬結束"