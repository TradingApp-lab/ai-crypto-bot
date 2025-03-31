import os
import json
import config
from log_utils import info, warn

# === Шлях до JSON-файлу ===
RISK_FILE = config.RISK_STATE_FILE

# === Ініціалізація ризикового стану, якщо файл не існує ===
def init_risk_state():
    if not os.path.exists(RISK_FILE):
        state = {"peak_equity": 0.0}
        save_risk_state(state)
        info("📁 Created new risk state file")

# === Завантаження стану ===
def load_risk_state():
    try:
        with open(RISK_FILE, 'r') as f:
            return json.load(f)
    except Exception as e:
        warn(f"⚠️ Could not load risk state: {e}")
        return {"peak_equity": 0.0}

# === Збереження стану ===
def save_risk_state(state):
    with open(RISK_FILE, 'w') as f:
        json.dump(state, f, indent=2)

# === Перевірка просадки та оновлення ===
def check_drawdown(current_equity):
    init_risk_state()
    state = load_risk_state()
    peak = state.get("peak_equity", 0.0)

    if current_equity > peak:
        state["peak_equity"] = current_equity
        save_risk_state(state)
        info(f"📈 New peak equity recorded: {current_equity}")
        return True, None

    drawdown = 100 * (1 - current_equity / peak) if peak > 0 else 0
    if drawdown >= config.MAX_DRAWDOWN_PERCENT:
        warn(f"🚨 Max drawdown exceeded: {drawdown:.2f}%")
        return False, drawdown

    return True, drawdown
