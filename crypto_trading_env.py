import gymnasium as gym
import numpy as np
import pandas as pd
import sqlite3
import os
from gymnasium import spaces
from dotenv import load_dotenv
import config
from log_utils import info, error

# Load environment variables
load_dotenv()

class CryptoTradingEnv(gym.Env):
    def __init__(self):
        super().__init__()

        db_path = os.getenv("DB_PATH", "ohlcv_data.db")
        self.conn = sqlite3.connect(db_path)
        self.df = pd.read_sql("SELECT * FROM ohlcv ORDER BY timestamp", self.conn)
        info(f"📊 LOADED {len(self.df)} rows from {db_path}")

        if self.df.empty:
            error("❌ OHLCV data is empty. Please fetch data first.")
            raise ValueError("❌ OHLCV data is empty. Please fetch data first.")

        self.current_step = 0
        self.balance = 1000.0
        self.crypto_held = 0.0

        self.action_space = spaces.Discrete(3)
        self.observation_space = spaces.Box(low=0, high=np.inf, shape=(6,), dtype=np.float32)

    def _get_observation(self):
        row = self.df.iloc[self.current_step]
        obs = np.array([
            row['open'], row['high'], row['low'],
            row['close'], row['volume'], self.balance
        ], dtype=np.float32)
        return obs

    def reset(self, *, seed=None, options=None):
        super().reset(seed=seed)
        self.current_step = 0
        self.balance = 1000.0
        self.crypto_held = 0.0
        info("🔄 Environment reset")
        return self._get_observation(), {}

    def step(self, action):
        row = self.df.iloc[self.current_step]
        price = row['close']

        if action == 1 and self.balance > 0:
            fee = self.balance * config.TRADING_FEE_PERCENT / 100
            amount_to_use = self.balance - fee
            self.crypto_held = amount_to_use / price
            self.balance = 0
            info(f"🟢 BUY at {price:.2f}, used {amount_to_use:.2f} after fee {fee:.4f}")
        elif action == 2 and self.crypto_held > 0:
            gross = self.crypto_held * price
            fee = gross * config.TRADING_FEE_PERCENT / 100
            self.balance = gross - fee
            info(f"🔴 SELL at {price:.2f}, received {gross:.2f}, fee {fee:.4f}, net {self.balance:.2f}")
            self.crypto_held = 0

        self.current_step += 1
        terminated = self.current_step >= len(self.df) - 1
        truncated = False
        reward = self.balance + self.crypto_held * price

        return self._get_observation(), reward, terminated, truncated, {}

    def render(self):
        info(f"📺 Step: {self.current_step}, Balance: {self.balance:.2f}, Crypto Held: {self.crypto_held:.4f}")