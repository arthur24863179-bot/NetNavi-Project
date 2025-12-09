# main.py (主程式)
import config
import create_db as db_creator # 引用修正後的 create_db
import db_interface as db
import game_logic as gl_logic
import sqlite3

def handle_main_menu():
    print("歡迎回到 NBA GM 模擬器 (王朝深耕 V5.6.2 - 核心數據修正版)！")
    
    while True:
        print("\n=============== NBA GM 遊戲菜單 V5.6.2 (修正版) ===============")
        print("1. 🛠️ 初始化/重新開始遊戲 (V5.6.2 結構)")
        print("2. 📅 模擬一個賽季 (82 場，核心數據修正)")
        print("3. 🏆 查看當前戰績與數據排行榜 ⭐ 數據已修正!")
        print("4. ⛹️ 進入隊伍管理 (V5.6 交易/深度報告)")
        print("0. 🚪 退出遊戲")
        print("==================================================")
        
        choice = input("請輸入選項數字 (0-4): ")
        
        if choice == '1':
            db_creator.create_and_populate_db() # 執行修正後的初始化
            print(f"✅ 遊戲 V5.6.2 結構初始化完成！(30 隊數據已填充)")
        elif choice == '2':
            print("... 賽季模擬開始 (數據累積與疲勞已修正) ...")
            gl_logic.simulate_season()
        elif choice == '3':
            view_standings_and_stats()
        elif choice == '4':
            print("隊伍管理介面開發中...")
        elif choice == '0':
            print("🚪 感謝遊玩，下次見！")
            break
        else:
             print("無效選項，請重新輸入。")

def view_standings_and_stats():
    conn = config.get_db_connection()
    cursor = conn.cursor()

    print("\n=============== 賽季數據排行榜 (場均) ===============\n")
    
    try:
        # 【致命 Bug 修正】：確保只計算 GamesPlayed > 0 的數據
        cursor.execute("""
            SELECT 
                ps.Points, 
                ps.GamesPlayed, 
                p.Name
            FROM Player_Stats ps
            JOIN Players p ON ps.PlayerID = p.PlayerID
            WHERE ps.GamesPlayed > 0
            ORDER BY ps.Points DESC
        """)
        top_scorers = cursor.fetchall()
        
        print("--- 得分王 (Points) ---")
        if not top_scorers:
            print("無有效賽季數據。請先模擬賽季 (選項 2)。")
        else:
            leaders = []
            for pts, gp, name in top_scorers:
                if gp > 0:
                    avg_pts = round(pts / gp, 1)
                    leaders.append((avg_pts, name, gp))

            # 重新排序確保場均最高
            leaders.sort(key=lambda x: x[0], reverse=True)
            
            for i, (avg_pts, name, gp) in enumerate(leaders[:5], 1):
                print(f"#{i}: {name.ljust(30)} | 場均得分: {avg_pts} (總場次: {gp})")

    except sqlite3.OperationalError as e:
        print(f"數據庫錯誤: {e}。請確保已執行初始化 (選項 1)。")
    finally:
        conn.close()

if __name__ == '__main__':
    handle_main_menu()