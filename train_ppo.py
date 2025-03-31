import os
import datetime
import numpy as np
import pandas as pd
from dotenv import load_dotenv
from sb3_contrib import RecurrentPPO
from stable_baselines3.common.vec_env import DummyVecEnv, VecNormalize
from crypto_trading_env import CryptoTradingEnv
import config
from telegram_api import send_message
from log_utils import info, success
import sqlite3

# === LOAD .env ===
load_dotenv()

# === AUTO-HYPERPARAMETER SELECTION ===
def auto_select_hyperparams():
    info("🔍 Auto-selecting PPO and risk parameters...")

    # Load OHLCV data
    df = pd.read_sql("SELECT * FROM ohlcv ORDER BY timestamp", sqlite3.connect(config.DB_PATH))
    row_count = len(df)
    returns = df['close'].pct_change().dropna()
    volatility = returns.std()

    TRAIN_TIMESTEPS = 100_000 if row_count > 100 else 50_000
    LEARNING_RATE = 3e-4
    GAMMA = 0.99
    GAE_LAMBDA = 0.95
    BATCH_SIZE = 64
    N_STEPS = 256

    # Risk management
    STOP_LOSS_PERCENT = 2.0
    TAKE_PROFIT_PERCENT = 4.0
    RISK_PERCENT = 2.0

    if volatility > 0.05:
        STOP_LOSS_PERCENT = 4.0
        TAKE_PROFIT_PERCENT = 8.0
    
    # Log
    ts = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    msg = (
        f"🧠 *Auto-Selected PPO Parameters* ({ts})\n"
        f"==============================\n"
        f"🕒 Timesteps: `{TRAIN_TIMESTEPS}`\n"
        f"📉 SL / TP: `{STOP_LOSS_PERCENT}%` / `{TAKE_PROFIT_PERCENT}%`\n"
        f"💥 Risk %: `{RISK_PERCENT}%`\n"
        f"📊 Volatility: `{volatility:.4f}`\n"
        f"📉 Rows in DB: `{row_count}`"
    )
    send_message(config.CONTACT_ID, msg)

    return TRAIN_TIMESTEPS, LEARNING_RATE, GAMMA, GAE_LAMBDA, BATCH_SIZE, N_STEPS, STOP_LOSS_PERCENT, TAKE_PROFIT_PERCENT, RISK_PERCENT


# === MAIN ===
def main():
    (TRAIN_TIMESTEPS, LEARNING_RATE, GAMMA, GAE_LAMBDA, BATCH_SIZE, 
     N_STEPS, STOP_LOSS_PERCENT, TAKE_PROFIT_PERCENT, RISK_PERCENT) = auto_select_hyperparams()

    info("🧠 Starting Recurrent PPO (LSTM) training with auto-selected hyperparameters...")

    env = DummyVecEnv([lambda: CryptoTradingEnv()])
    env = VecNormalize(env, norm_obs=True, norm_reward=True, clip_obs=10.)

    model = RecurrentPPO(
        "MlpLstmPolicy",
        env,
        verbose=1,
        learning_rate=LEARNING_RATE,
        gamma=GAMMA,
        gae_lambda=GAE_LAMBDA,
        batch_size=BATCH_SIZE,
        n_steps=N_STEPS,
        tensorboard_log=os.getenv("TENSORBOARD_LOG", "./tensorboard_logs/")
    )

    model.learn(total_timesteps=TRAIN_TIMESTEPS)

    # Save with timestamp
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    model_name = f"ppo_model_{timestamp}"
    vecnorm_name = f"vecnormalize_{timestamp}.pkl"
    model_path = os.path.join("models", model_name)
    vecnorm_path = os.path.join("models", vecnorm_name)
    model.save(model_path)
    env.save(vecnorm_path)

    # === Save default version for paper trading ===
    model.save("ppo_crypto_trader.zip")
    env.save("ppo_crypto_trader.pkl")

    msg = (
        f"✅ Model training complete ({timestamp})\n"
        f"🧠 Saved model: `{model_name}.zip`\n"
        f"📁 VecNormalize: `{vecnorm_name}`\n"
        f"🛠️ Params: LR={LEARNING_RATE}, Gamma={GAMMA}, GAE={GAE_LAMBDA}, Batch={BATCH_SIZE}, Steps={N_STEPS}"
    )
    success(msg)
    send_message(config.CONTACT_ID, msg)


if __name__ == "__main__":
    main()