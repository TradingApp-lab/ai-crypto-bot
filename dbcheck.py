import sqlite3
import pandas as pd

conn = sqlite3.connect("ohlcv_data.db")
df = pd.read_sql("SELECT * FROM ohlcv ORDER BY timestamp ASC LIMIT 10", conn)
print(df)
conn.close()
