import sqlite3
import sys

DB_NAME = 'nba_gm.db'

def query_player_stats():
    """使用 Python 內建模組查詢並輸出 Player_Stats 數據。"""
    conn = None
    try:
        conn = sqlite3.connect(DB_NAME)
        cursor = conn.cursor()
        
        query = "SELECT PlayerID, GP, PPG, Fatigue, InjuryStatus FROM Player_Stats WHERE PlayerID BETWEEN 1 AND 5"
        cursor.execute(query)
        results = cursor.fetchall()

        if not results:
            print("🚫 數據庫查詢結果為空。請確認您已運行 game_simulation.py 並成功保存數據。")
            return

        print("\n--------------------------------------------------")
        print("✅ 最終數據庫統計驗證結果 (Player_Stats)")
        print("--------------------------------------------------")
        print("PlayerID | GP | PPG | Fatigue | InjuryStatus")
        print("--------------------------------------------------")
        
        # 輸出結果並格式化
        for row in results:
            player_id, gp, ppg, fatigue, injury_status = row
            ppg = round(ppg, 1)
            fatigue = round(fatigue, 1)
            print(f"{player_id:<8} | {gp:<2} | {ppg:<3} | {fatigue:<7} | {injury_status}")

    except sqlite3.Error as e:
        print(f"🚫 數據庫錯誤: {e}", file=sys.stderr)
    except Exception as e:
        print(f"🚫 發生錯誤: {e}", file=sys.stderr)
    finally:
        if conn:
            conn.close()

if __name__ == '__main__':
    query_player_stats()