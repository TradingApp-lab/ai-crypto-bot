# === bybit_client.py ===
from pybit.unified_trading import HTTP
import config
import time
import hmac
import hashlib
import requests
import json

from log_utils import info, error, success, warn  # 🔧 Імпорт логування


def get_session():
    return HTTP(
        testnet=True,
        api_key=config.BYBIT_API_KEY,
        api_secret=config.BYBIT_API_SECRET
    )

def get_usdt_balance():
    try:
        server_time_resp = requests.get("https://api.bybit.com/v5/market/time")
        server_timestamp = str(server_time_resp.json()["time"])

        url = "https://api.bybit.com/v5/account/wallet-balance"
        recv_window = "5000"
        params = f"accountType=UNIFIED&coin=USDT"

        to_sign = f"{server_timestamp}{config.BYBIT_API_KEY}{recv_window}{params}"
        sign = hmac.new(
            config.BYBIT_API_SECRET.encode("utf-8"),
            to_sign.encode("utf-8"),
            hashlib.sha256
        ).hexdigest()

        headers = {
            "X-BAPI-API-KEY": config.BYBIT_API_KEY,
            "X-BAPI-SIGN": sign,
            "X-BAPI-TIMESTAMP": server_timestamp,
            "X-BAPI-RECV-WINDOW": recv_window
        }

        response = requests.get(f"{url}?{params}", headers=headers)

        print("📡 Response status:", response.status_code)
        print("📄 Response headers:", response.headers)
        print("📄 Raw response:", response.text)

        try:
            data = response.json()
        except Exception as e:
            error(f"❌ JSON parse error: {e} | Raw: {response.text}")
            return None

        info(f"🔎 FULL BALANCE RESPONSE: {data}")

        if data.get("retCode") != 0:
            error(f"❌ API Error: {data.get('retMsg', 'Unknown error')}")
            return None

        # === Перевірка структури відповіді ===
        try:
            coin_list = data["result"]["list"][0]["coin"]
            for coin_data in coin_list:
                if coin_data["coin"] == "USDT":
                    wallet_balance = float(coin_data["walletBalance"])
                    return wallet_balance
            warn("⚠️ USDT not found in wallet")
            return 0.0
        except (IndexError, KeyError, TypeError) as e:
            error(f"❌ Unexpected response format: {e}")
            return None

    except Exception as e:
        error(f"❌ Raw API balance error: {e}")
        return None


def get_market_price(symbol):
    try:
        url = "https://api.bybit.com/v5/market/tickers"
        params = {"category": "linear", "symbol": symbol}
        response = requests.get(url, params=params)
        data = response.json()
        return float(data['result']['list'][0]['lastPrice'])
    except Exception as e:
        error(f"Market price error: {e}")
        return None

def get_position_info(symbol):
    try:
        server_time_resp = requests.get("https://api.bybit.com/v5/market/time")
        server_timestamp = str(server_time_resp.json()["time"])

        url = "https://api.bybit.com/v5/position/list"
        recv_window = "5000"
        params = f"category=linear&symbol={symbol}"

        to_sign = f"{server_timestamp}{config.BYBIT_API_KEY}{recv_window}{params}"
        sign = hmac.new(
            config.BYBIT_API_SECRET.encode("utf-8"),
            to_sign.encode("utf-8"),
            hashlib.sha256
        ).hexdigest()

        headers = {
            "X-BAPI-API-KEY": config.BYBIT_API_KEY,
            "X-BAPI-SIGN": sign,
            "X-BAPI-TIMESTAMP": server_timestamp,
            "X-BAPI-RECV-WINDOW": recv_window
        }

        response = requests.get(f"{url}?{params}", headers=headers)
        data = response.json()
        info(f"📦 POSITION INFO: {data}")

        return data["result"]["list"][0] if data["result"]["list"] else {}
    except Exception as e:
        error(f"Position info error: {e}")
        return {}

def set_leverage(symbol, leverage):
    try:
        server_time_resp = requests.get("https://api.bybit.com/v5/market/time")
        server_timestamp = str(server_time_resp.json()["time"])

        url = "https://api.bybit.com/v5/position/set-leverage"
        recv_window = "5000"

        body = {
            "category": "linear",
            "symbol": symbol,
            "buyLeverage": str(leverage),
            "sellLeverage": str(leverage)
        }

        body_str = json.dumps(body, separators=(",", ":"))
        to_sign = f"{server_timestamp}{config.BYBIT_API_KEY}{recv_window}{body_str}"

        sign = hmac.new(
            config.BYBIT_API_SECRET.encode("utf-8"),
            to_sign.encode("utf-8"),
            hashlib.sha256
        ).hexdigest()

        headers = {
            "Content-Type": "application/json",
            "X-BAPI-API-KEY": config.BYBIT_API_KEY,
            "X-BAPI-SIGN": sign,
            "X-BAPI-TIMESTAMP": server_timestamp,
            "X-BAPI-RECV-WINDOW": recv_window
        }

        response = requests.post(url, data=body_str, headers=headers)
        data = response.json()
        info(f"📨 LEVERAGE RESPONSE: {data}")

        if data["retCode"] == 0:
            return True, f"Leverage set to {leverage}x"
        else:
            return False, f"Leverage error: {data.get('retMsg')}"
    except Exception as e:
        error(f"Leverage error: {e}")
        return False, "Leverage request failed"

def place_order(order_data):
    try:
        server_time_resp = requests.get("https://api.bybit.com/v5/market/time")
        server_timestamp = str(server_time_resp.json()["time"])

        url = "https://api.bybit.com/v5/order/create"
        recv_window = "5000"

        body_str = json.dumps(order_data, separators=(",", ":"))
        to_sign = f"{server_timestamp}{config.BYBIT_API_KEY}{recv_window}{body_str}"

        sign = hmac.new(
            config.BYBIT_API_SECRET.encode("utf-8"),
            to_sign.encode("utf-8"),
            hashlib.sha256
        ).hexdigest()

        headers = {
            "Content-Type": "application/json",
            "X-BAPI-API-KEY": config.BYBIT_API_KEY,
            "X-BAPI-SIGN": sign,
            "X-BAPI-TIMESTAMP": server_timestamp,
            "X-BAPI-RECV-WINDOW": recv_window
        }

        response = requests.post(url, data=body_str, headers=headers)
        data = response.json()
        info(f"📤 ORDER RESPONSE: {data}")

        if data["retCode"] == 0:
            return True, data
        else:
            return False, f"Order error: {data.get('retMsg')}"
    except Exception as e:
        error(f"Order error: {e}")
        return False, f"Order error: {str(e)}"

def set_tp_sl(side, take_profit, stop_loss):
    try:
        server_time_resp = requests.get("https://api.bybit.com/v5/market/time")
        server_timestamp = str(server_time_resp.json()["time"])

        url = "https://api.bybit.com/v5/position/trading-stop"
        recv_window = "5000"
        body = {
            "category": "linear",
            "symbol": config.SYMBOL,
            "takeProfit": str(round(take_profit, 2)),
            "stopLoss": str(round(stop_loss, 2)),
            "positionIdx": 1 if side == "Buy" else 2
        }

        body_str = json.dumps(body, separators=(",", ":"))
        to_sign = f"{server_timestamp}{config.BYBIT_API_KEY}{recv_window}{body_str}"

        sign = hmac.new(
            config.BYBIT_API_SECRET.encode("utf-8"),
            to_sign.encode("utf-8"),
            hashlib.sha256
        ).hexdigest()

        headers = {
            "Content-Type": "application/json",
            "X-BAPI-API-KEY": config.BYBIT_API_KEY,
            "X-BAPI-SIGN": sign,
            "X-BAPI-TIMESTAMP": server_timestamp,
            "X-BAPI-RECV-WINDOW": recv_window
        }

        response = requests.post(url, data=body_str, headers=headers)
        data = response.json()
        info(f"🎯 TP/SL RESPONSE: {data}")

        if data["retCode"] == 0:
            success("🎯 TP & SL set successfully.")
            return True
        else:
            error(f"❌ Error setting TP/SL: {data.get('retMsg')}")
            return False
    except Exception as e:
        error(f"TP/SL error: {e}")
        return False