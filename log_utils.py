import logging
import os
import sys

LOG_DIR = "logs"
LOG_FILE = os.path.join(LOG_DIR, "app.log")
os.makedirs(LOG_DIR, exist_ok=True)

# 🛠️ Виправлення Windows-терміналу, щоб підтримував emoji / юнікод
console_handler = logging.StreamHandler(sys.stdout)
console_handler.setLevel(logging.INFO)
console_handler.setFormatter(logging.Formatter('%(asctime)s [%(levelname)s] %(message)s'))

file_handler = logging.FileHandler(LOG_FILE, encoding="utf-8")
file_handler.setLevel(logging.INFO)
file_handler.setFormatter(logging.Formatter('%(asctime)s [%(levelname)s] %(message)s'))

logging.basicConfig(level=logging.INFO, handlers=[console_handler, file_handler])

# === Шорткати ===
def info(msg):
    logging.info(f"ℹ️ {msg}")

def success(msg):
    logging.info(f"✅ {msg}")

def warn(msg):
    logging.warning(f"⚠️ {msg}")

def error(msg):
    logging.error(f"❌ {msg}")
