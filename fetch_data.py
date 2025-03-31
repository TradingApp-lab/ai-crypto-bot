import requests
import sqlite3
import time
import pandas as pd
import os
from datetime import datetime
import config
from log_utils import info, warn, error

DB_PATH = config.DB_PATH
TABLE_NAME = "ohlcv"
SYMBOL = config.SYMBOL
INTERVAL = config.INTERVAL  # у секундах, 60 = 1m
LIMIT = config.LIMIT

def fetch_ohlcv_data(start_ts=None):
    url = config.BYBIT_OHLCV_ENDPOINT
    params = {
        "category": "linear",
        "symbol": SYMBOL,
        "interval": str(INTERVAL),
        "limit": LIMIT,
    }
    if start_ts:
        params["start"] = int(start_ts)

    response = requests.get(url, params=params)
    data = response.json()

    if data.get("retCode") != 0:
        warn(f"⚠️ API returned error: {data}")
        return []

    return data["result"].get("list", [])

def init_db():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute(f'''
        CREATE TABLE IF NOT EXISTS {TABLE_NAME} (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            symbol TEXT,
            timestamp INTEGER,
            open REAL,
            high REAL,
            low REAL,
            close REAL,
            volume REAL
        )
    ''')
    conn.commit()
    return conn

def get_latest_timestamp(conn):
    cursor = conn.cursor()
    cursor.execute(f"SELECT MAX(timestamp) FROM {TABLE_NAME}")
    result = cursor.fetchone()
    return int(result[0]) if result[0] else None

def main():
    info("📥 Fetching OHLCV data from Bybit PROD API...")
    conn = init_db()
    inserted_total = 0
    prev_latest_ts = get_latest_timestamp(conn)

    while True:
        start_ts = prev_latest_ts + 60_000 if prev_latest_ts else None
        ohlcv = fetch_ohlcv_data(start_ts)

        if not ohlcv:
            info("⛔ No more new data available. Exiting.")
            break

        rows = []
        for item in ohlcv:
            # ❌ Skip invalid or unrealistic values
            try:
                close_price = float(item[4])
                if close_price > 100_000:
                    continue

                rows.append((
                    SYMBOL,
                    int(item[0]),
                    float(item[1]),
                    float(item[2]),
                    float(item[3]),
                    close_price,
                    float(item[5])
                ))
            except (ValueError, IndexError) as e:
                warn(f"⚠️ Skipped invalid row: {item} | Error: {e}")

        df = pd.DataFrame(rows, columns=[
            "symbol", "timestamp", "open", "high", "low", "close", "volume"
        ])
        df.drop_duplicates(subset=["timestamp"], inplace=True)

        if df.empty or df["timestamp"].max() == prev_latest_ts:
            info("✅ All data is up to date.")
            break

        df.to_sql(TABLE_NAME, conn, if_exists="append", index=False)
        inserted_total += len(df)
        prev_latest_ts = df["timestamp"].max()
        last_ts = datetime.fromtimestamp(prev_latest_ts / 1000).strftime("%Y-%m-%d %H:%M:%S")
        info(f"📥 Fetched {len(df)} rows. Total: {inserted_total} | Last timestamp: {last_ts}")
        time.sleep(0.5)

    conn.close()
    info("💾 Saved to ohlcv_data.db ✅")

if __name__ == "__main__":
    main()