import os
import json
import time
import numpy as np
import pandas as pd
from datetime import datetime

from stable_baselines3 import PPO
from stable_baselines3.common.vec_env import DummyVecEnv, VecNormalize
from crypto_trading_env import CryptoTradingEnv
from telegram_api import send_message
from log_utils import info, warn, error
import fetch_data  # <=== імпорт fetch_data
import config

STATE_FILE = "paper_trading_state.json"

# === Load environment and model ===
def load_environment():
    info("🔁 Updating OHLCV data before starting paper trading...")
    fetch_data.main()  # <=== оновлення даних

    info("📊 LOADING historical data from DB...")
    vec_env = DummyVecEnv([lambda: CryptoTradingEnv()])
    vec_env = VecNormalize.load(config.MODEL_PATH.replace(".zip", ".pkl"), vec_env)
    vec_env.training = False
    vec_env.norm_reward = False
    return vec_env


def load_model(vec_env):
    info("📦 Loading PPO model...")
    return PPO.load(config.MODEL_PATH, env=vec_env)


def load_state():
    default_state = {
        "balance": 100.0,
        "holding": False,
        "entry_price": 0.0,
        "crypto_amount": 0.0
    }
    if os.path.exists(STATE_FILE):
        try:
            with open(STATE_FILE, "r") as f:
                state = json.load(f)
                for key in default_state:
                    if key not in state:
                        state[key] = default_state[key]
                return state
        except (json.JSONDecodeError, IOError) as e:
            warn(f"⚠️ Failed to read state file: {e}. Reinitializing.")
    return default_state


def save_state(state):
    with open(STATE_FILE, "w") as f:
        json.dump(state, f, indent=2)


def run():
    info("📈 Starting paper trading...")
    send_message(config.CONTACT_ID, "📈 Starting paper trading on real historical data...")

    vec_env = load_environment()
    model = load_model(vec_env)
    state = load_state()

    obs = vec_env.reset()
    step = 0
    done = False

    price_series = vec_env.get_attr("df")[0]['close'].tolist()

    while not done:
        action, _ = model.predict(obs)
        obs, reward, done, step_info = vec_env.step(action)

        price = price_series[step]

        if action == 1 and not state["holding"]:
            state["entry_price"] = price
            state["crypto_amount"] = state["balance"] / price
            state["balance"] = 0
            state["holding"] = True
            msg = (
                f"🟢 Paper BUY executed\n"
                f"💰 Entry Price: {price:.2f}\n"
                f"📊 Amount: {state['crypto_amount']:.6f} BTC"
            )
            send_message(config.CONTACT_ID, msg)

        elif action == 2 and state["holding"]:
            state["balance"] = state["crypto_amount"] * price
            profit = state["balance"] - state["entry_price"] * state["crypto_amount"]
            state["crypto_amount"] = 0
            state["holding"] = False
            msg = (
                f"🔴 Paper SELL executed\n"
                f"💰 Exit Price: {price:.2f}\n"
                f"📈 Profit: {profit:.2f} USDT\n"
                f"💼 New Balance: {state['balance']:.2f} USDT"
            )
            send_message(config.CONTACT_ID, msg)

        elif state["holding"] and step % 50 == 0:
            unrealized = price * state["crypto_amount"] - state["entry_price"] * state["crypto_amount"]
            send_message(config.CONTACT_ID, f"📍 Holding... Price: {price:.2f}, Unrealized PnL: {unrealized:.2f} USDT")

        save_state(state)
        step += 1

    send_message(config.CONTACT_ID, "✅ Paper trading finished.")


if __name__ == "__main__":
    run()