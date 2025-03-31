import subprocess
import threading
import os
import sys
import sqlite3
from datetime import datetime
import config
from log_utils import info, error
import pandas as pd
import numpy as np

# 🔄 Active tasks (used in /status)
active_tasks = set()

def run_script_async(script_name, on_finish=None, on_start=None, args=None):
    """
    Runs a script asynchronously in a separate thread using the current venv.
    on_start — function called immediately before script starts (e.g. send_message)
    on_finish — function called after script completes
    """
    def run():
        try:
            active_tasks.add(script_name)
            info(f"⚙️ [run_script_async] Starting: {script_name}")

            if on_start:
                info(f"➡️ Calling on_start() for {script_name}")
                on_start()

            venv_python = os.path.join(sys.prefix, 'Scripts', 'python.exe') if os.name == 'nt' else os.path.join(sys.prefix, 'bin', 'python')
            script_path = os.path.abspath(script_name)
            command = [venv_python, script_path]
            if args:
                command += args

            info(f"📿 Command to run: {' '.join(command)}")
            subprocess.run(command, check=True)
            info(f"✅ Script finished: {script_name}")

            if on_finish:
                info(f"➡️ Calling on_finish() for {script_name}")
                on_finish()
        except subprocess.CalledProcessError as e:
            error(f"❌ Script failed: {script_name}\n{e}")
            if on_finish:
                on_finish()
        finally:
            active_tasks.discard(script_name)

    thread = threading.Thread(target=run)
    thread.start()

def get_status():
    try:
        conn = sqlite3.connect(config.DB_PATH)
        cursor = conn.cursor()

        cursor.execute("SELECT COUNT(*) FROM ohlcv")
        row_count = cursor.fetchone()[0]

        cursor.execute("SELECT MAX(timestamp) FROM ohlcv")
        last_ts = cursor.fetchone()[0]
        last_date = datetime.fromtimestamp(last_ts / 1000).strftime("%Y-%m-%d %H:%M:%S")

        conn.close()

        status = (
            f"📊 *Status"
            f"📈 Rows in DB: {row_count}"
            f"🗕️ Last data: {last_date}"
        )

        # === Performance metrics from simulation_log.csv ===
        try:
            df = pd.read_csv("simulation_log.csv")
            if not df.empty:
                total_return = round(df["total_reward"].iloc[-1], 2)
                wins = df[df["reward"] > 0].shape[0]
                win_rate = round(100 * wins / len(df), 2)
                max_drawdown = round((df["total_reward"].cummax() - df["total_reward"]).max(), 2)
                volatility = round(df["reward"].std(), 4)
                sharpe_ratio = round(df["reward"].mean() / (df["reward"].std() + 1e-8), 2)

                status += (
                    f"\n\n📈 *Performance Metrics"
                    f"💰 Total Return: {total_return}"
                    f"✅ Win Rate: {win_rate}%"
                    f"📉 Max Drawdown: {max_drawdown}"
                    f"📈 Volatility: {volatility}"
                    f"🖐 Sharpe Ratio: {sharpe_ratio}"
                )
        except Exception as e:
            status += f"\n⚠️ Could not load performance metrics: {e}"

        if active_tasks:
            status += f"\n🕒 Active tasks: {', '.join(active_tasks)}"

        return status

    except Exception as e:
        return f"❌ Error while fetching status: {str(e)}"
