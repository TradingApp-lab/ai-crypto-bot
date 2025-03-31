import time
import subprocess
import datetime
import os
from telegram_api import send_message, send_photo

UPDATE_INTERVAL_SECONDS = 60 * 60  # 1 година
VENV_PYTHON = os.path.join("venv", "Scripts", "python.exe")  # або 'bin' для Linux/Mac

LOG_FILE = "logs/app.log"
GRAPH_FILE = "ohlcv_preview.png"


def main():
    print("⏳ Scheduled updater started...")
    while True:
        now = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        print(f"\n🔄 Updating data at {now}")

        try:
            # Запуск fetch_data.py для оновлення даних
            subprocess.run([VENV_PYTHON, "fetch_data.py"], check=True)
            print("✅ Data update completed.")

            # Надсилання повідомлення в Telegram
            send_message(config.ALLOWED_USERS[0], f"✅ OHLCV data updated successfully at {now}")

            # Надсилання графіку, якщо існує
            if os.path.exists(GRAPH_FILE):
                send_photo(config.ALLOWED_USERS[0], GRAPH_FILE, caption="📊 OHLCV Chart Preview")
            else:
                print("⚠️ Graph file not found")

            # Надсилання лог-файлу, якщо існує
            if os.path.exists(LOG_FILE):
                send_photo(config.ALLOWED_USERS[0], LOG_FILE, caption="📄 Log File")
            else:
                print("⚠️ Log file not found")

        except subprocess.CalledProcessError as e:
            print(f"❌ Error during data update: {e}")
            send_message(config.ALLOWED_USERS[0], f"❌ Error during data update at {now}: {e}")

        print(f"🕒 Sleeping for {UPDATE_INTERVAL_SECONDS // 60} minutes...\n")
        time.sleep(UPDATE_INTERVAL_SECONDS)


if __name__ == "__main__":
    import config  # Імпортуємо тут, щоб не ламати зовнішні залежності
    main()