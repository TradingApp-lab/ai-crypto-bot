import os 
from dotenv import load_dotenv

# === Load .env ===
load_dotenv()

# === Telegram Bot ===
BOT_TOKEN = os.getenv("BOT_TOKEN")
CONTACT_ID = os.getenv("CONTACT_ID")

# 🔐 Allowed users (Telegram IDs)
ALLOWED_USERS = list(map(int, [x.strip() for x in os.getenv("ALLOWED_USERS", "").split(",")]))

# === OHLCV DB ===
DB_PATH = os.getenv("DB_PATH", "ohlcv_data.db")

# === Trading config ===
SYMBOL = os.getenv("SYMBOL", "BTCUSDT")
INTERVAL = int(os.getenv("INTERVAL", "60"))  # in seconds
LIMIT = int(os.getenv("LIMIT", "200"))

# === Model config ===
MODEL_PATH = os.getenv("MODEL_PATH", "ppo_crypto_trader.zip")

# === Bybit Endpoint ===
BYBIT_OHLCV_ENDPOINT = os.getenv("BYBIT_OHLCV_ENDPOINT", "https://api.bybit.com/v5/market/kline")

# === Bybit API Keys ===
BYBIT_API_KEY = os.getenv("BYBIT_API_KEY")
BYBIT_API_SECRET = os.getenv("BYBIT_API_SECRET")

# === Risk Management ===
STOP_LOSS_PERCENT = float(os.getenv("STOP_LOSS_PERCENT", 2))
TAKE_PROFIT_PERCENT = float(os.getenv("TAKE_PROFIT_PERCENT", 4))
RISK_PERCENT = float(os.getenv("RISK_PERCENT", 2))
MAX_DRAWDOWN_PERCENT = float(os.getenv("MAX_DRAWDOWN_PERCENT", 10))
RISK_STATE_FILE = os.getenv("RISK_STATE_FILE", "risk_state.json")

# === Fees ===
TRADING_FEE_PERCENT = float(os.getenv("TRADING_FEE_PERCENT", 0.04))  # default: 0.04%
