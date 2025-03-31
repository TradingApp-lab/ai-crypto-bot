import os
import gymnasium as gym
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib
from datetime import datetime

from stable_baselines3 import PPO
from stable_baselines3.common.vec_env import DummyVecEnv, VecNormalize
from crypto_trading_env import CryptoTradingEnv
import config
from telegram_api import send_message, send_photo
from log_utils import info, success

matplotlib.use('Agg')  # Use headless backend

# === Select latest available model ===
def get_latest_model_path():
    model_dir = "models"
    files = [f for f in os.listdir(model_dir) if f.startswith("ppo_model_") and f.endswith(".zip")]
    if not files:
        raise FileNotFoundError("❌ No model found in /models")
    files.sort(reverse=True)
    return os.path.join(model_dir, files[0])

# === Select latest available vecnormalize ===
def get_latest_vecnormalize_path():
    model_dir = "models"
    files = [f for f in os.listdir(model_dir) if f.startswith("vecnormalize_") and f.endswith(".pkl")]
    if not files:
        raise FileNotFoundError("❌ No vecnormalize file found in /models")
    files.sort(reverse=True)
    return os.path.join(model_dir, files[0])

# === Load environment and model ===
info("🧠 Loading environment with VecNormalize...")
vec_env = DummyVecEnv([lambda: CryptoTradingEnv()])
vec_env = VecNormalize.load(get_latest_vecnormalize_path(), vec_env)
vec_env.training = False
vec_env.norm_reward = False

info("📦 Loading model...")
model = PPO.load(get_latest_model_path(), env=vec_env)

# === Simulation ===
info("🚀 Starting simulation...")
obs = vec_env.reset()
done = False
reward_sum = 0
step = 0
log_data = []
entry_points = []
exit_points = []
price_series = vec_env.get_attr("df")[0]['close'].tolist()

holding = False

while not done:
    action, _ = model.predict(obs)
    obs, reward, done, step_info = vec_env.step(action)


    if isinstance(reward, np.ndarray):
        reward_val = reward[0]
    else:
        reward_val = reward

    reward_sum += reward_val

    current_price = price_series[step]
    if action == 1 and not holding:
        entry_points.append((step, current_price))
        holding = True
    elif action == 2 and holding:
        exit_points.append((step, current_price))
        holding = False

    log_data.append({
        "step": step,
        "reward": reward_val,
        "total_reward": reward_sum,
        "price": current_price
    })
    step += 1

# === Save logs ===
log_df = pd.DataFrame(log_data)
log_df.to_csv("simulation_log.csv", index=False)
info("Logs saved to simulation_log.csv ✅")

# === Price chart with trade points ===
plt.figure(figsize=(12, 6))
plt.plot(log_df["step"], log_df["price"], label="BTC Price", color="blue")
if entry_points:
    ep_x, ep_y = zip(*entry_points)
    plt.scatter(ep_x, ep_y, marker='^', color='green', label='Buy', s=60)
if exit_points:
    xp_x, xp_y = zip(*exit_points)
    plt.scatter(xp_x, xp_y, marker='v', color='red', label='Sell', s=60)
plt.title("BTC Price + Trade Points")
plt.xlabel("Step")
plt.ylabel("Price")
plt.legend()
plt.grid(True)
plt.tight_layout()
price_chart_path = "price_with_trades.png"
plt.savefig(price_chart_path)
info(f"📈 Price chart saved to {price_chart_path}")

# === Equity curve ===
plt.figure(figsize=(10, 4))
plt.plot(log_df["step"], log_df["total_reward"])
plt.title("Equity Curve (Total Reward Over Time)")
plt.xlabel("Step")
plt.ylabel("Total Reward")
plt.grid(True)
plt.tight_layout()
equity_chart_path = "equity_curve.png"
plt.savefig(equity_chart_path)
info(f"📉 Equity curve chart saved to {equity_chart_path}")

# === Performance Metrics ===
returns = log_df["reward"]
total_return = log_df["total_reward"].iloc[-1]
positive_trades = (returns > 0).sum()
total_trades = len(returns)
win_rate = positive_trades / total_trades * 100 if total_trades > 0 else 0
drawdown = (log_df["total_reward"].cummax() - log_df["total_reward"]).max()
volatility = returns.std()
sharpe_ratio = (returns.mean() / (returns.std() + 1e-9)) * np.sqrt(252)

report = (
    f"📊 *Simulation Performance Metrics:*\n"
    f"-----------------------------\n"
    f"📈 Total Return: `{total_return:.2f}`\n"
    f"✅ Win Rate: `{win_rate:.2f}%`\n"
    f"📉 Max Drawdown: `{drawdown:.2f}`\n"
    f"📊 Volatility: `{volatility:.4f}`\n"
    f"📐 Sharpe Ratio: `{sharpe_ratio:.2f}`"
)

# === Send charts to Telegram ===
send_photo(config.CONTACT_ID, equity_chart_path, caption="📈 Equity Curve")
send_photo(config.CONTACT_ID, price_chart_path, caption=report)

# === Final ===
success("✅ Simulation completed")
info(f"📈 Total steps: {step}")
info(f"💰 Total reward: {reward_sum}")