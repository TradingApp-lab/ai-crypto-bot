import random
from bybit_client import get_usdt_balance, get_market_price, get_position_info, set_leverage, place_order, set_tp_sl
from log_utils import info, success, warn, error
from risk_utils import check_drawdown
import config

SYMBOL = config.SYMBOL
CATEGORY = "linear"
ACCOUNT_TYPE = "UNIFIED"
MARGIN_MODE = "REGULAR"

def get_current_position():
    info("🔎 Fetching current position info...")
    position_info = get_position_info(SYMBOL)
    size = float(position_info.get("size", 0))
    side = position_info.get("side", "")
    return size, side, position_info

def calculate_tp_sl(entry_price, direction):
    if direction == "Buy":
        stop_loss_price = entry_price * (1 - config.STOP_LOSS_PERCENT / 100)
        take_profit_price = entry_price * (1 + config.TAKE_PROFIT_PERCENT / 100)
    else:
        stop_loss_price = entry_price * (1 + config.STOP_LOSS_PERCENT / 100)
        take_profit_price = entry_price * (1 - config.TAKE_PROFIT_PERCENT / 100)
    return round(take_profit_price, 2), round(stop_loss_price, 2)

def open_long_position(usdt_amount):
    return open_position("Buy", usdt_amount)

def open_short_position(usdt_amount):
    return open_position("Sell", usdt_amount)

def open_position(direction, usdt_amount):
    try:
        current_balance = get_usdt_balance()
        ok, drawdown = check_drawdown(current_balance)
        if not ok:
            return False, f"🚫 Trading halted due to drawdown: {drawdown:.2f}%"

        size, _, _ = get_current_position()
        if size > 0:
            warn("❗ Attempt to open a position while one is already open")
            return False, "⚠️ Position already open!"

        leverage = random.randint(1, 10)
        info(f"🎚️ Setting leverage: {leverage}x")
        leverage_set, leverage_msg = set_leverage(SYMBOL, leverage)
        if not leverage_set:
            error(f"❌ Leverage setting failed: {leverage_msg}")
            return False, f"⚠️ Leverage setting failed: {leverage_msg}"

        price = get_market_price(SYMBOL)
        if not price:
            error("❌ Failed to fetch market price")
            return False, "⚠️ Market price fetch error!"

        fee_cost = (usdt_amount * config.TRADING_FEE_PERCENT / 100)
        usdt_amount_after_fee = usdt_amount - fee_cost
        qty = round((usdt_amount_after_fee * leverage) / price, 3)

        info(f"💸 Fee deducted: {fee_cost:.4f} USDT | Final amount: {usdt_amount_after_fee:.4f}")
        info(f"📦 Calculated qty: {qty} for direction {direction}")
        if qty <= 0:
            warn("❗ Calculated qty is zero or negative")
            return False, "⚠️ Calculated qty is zero!"

        order_data = {
            "category": CATEGORY,
            "symbol": SYMBOL,
            "side": direction,
            "orderType": "Market",
            "qty": str(qty),
            "timeInForce": "GoodTillCancel",
            "accountType": ACCOUNT_TYPE,
            "marginMode": MARGIN_MODE,
            "reduceOnly": False
        }

        info(f"📤 Placing {'LONG' if direction == 'Buy' else 'SHORT'} order...")
        placed, order_response = place_order(order_data)
        if placed:
            success("✅ Order placed successfully")
            position = get_position_info(SYMBOL)
            entry_price = float(position.get('avgPrice', price))
            liq_price = position.get('liqPrice', 'N/A')
            leverage_used = position.get('leverage', leverage)

            tp, sl = calculate_tp_sl(entry_price, direction)
            set_tp_sl(direction, tp, sl)

            msg = (
                f"{'🟢 LONG' if direction == 'Buy' else '🔴 SHORT'} position opened\n"
                f"💰 Qty: {qty}\n"
                f"🎯 Entry price: {entry_price}\n"
                f"🚨 Liq price: {liq_price}\n"
                f"📈 Leverage: {leverage_used}x\n"
                f"🎯 TP: {tp}\n"
                f"🛑 SL: {sl}"
            )
            msg += f"\n💸 Fee (entry): {fee_cost:.4f} USDT"
            return True, msg
        else:
            error(f"❌ Order placement failed: {order_response}")
            return False, f"⚠️ Order placement failed: {order_response}"

    except Exception as e:
        error(f"❌ Exception while opening position: {e}")
        return False, f"⚠️ Exception: {str(e)}"

def close_position():
    size, side, position_info = get_current_position()
    if size == 0 or side == "":
        warn("❗ Attempt to close when no position is open")
        return False, "⚠️ No open position to close!"

    opposite_side = "Sell" if side == "Buy" else "Buy"

    order_data = {
        "category": CATEGORY,
        "symbol": SYMBOL,
        "side": opposite_side,
        "orderType": "Market",
        "qty": str(size),
        "timeInForce": "GoodTillCancel",
        "accountType": ACCOUNT_TYPE,
        "marginMode": MARGIN_MODE,
        "reduceOnly": True
    }

    info(f"🔒 Closing position ({side} → {opposite_side}), Qty: {size}")
    closed, order_response = place_order(order_data)

    if closed:
        success("✅ Position closed successfully")
        entry_price = float(position_info.get('avgPrice', 0))
        close_price = get_market_price(SYMBOL)
        pnl_percentage = round(((close_price - entry_price) / entry_price) * 100 * (1 if side == 'Buy' else -1), 2)
        amount_received = round(size * close_price, 2)

        fee_exit = amount_received * config.TRADING_FEE_PERCENT / 100
        amount_after_fee = round(amount_received - fee_exit, 2)

        msg = (
            f"🔒 Position closed\n"
            f"💰 Qty: {size}\n"
            f"🎯 Entry price: {entry_price}\n"
            f"🏁 Close price: {close_price}\n"
            f"📊 PNL: {pnl_percentage}% {'📈' if pnl_percentage > 0 else '📉'}\n"
            f"💵 Gross received: {amount_received} USDT\n"
            f"💸 Fee (exit): {fee_exit:.2f} USDT\n"
            f"💰 Net received: {amount_after_fee} USDT"
        )
        return True, msg
    else:
        error(f"❌ Failed to close position: {order_response}")
        return False, f"⚠️ Failed to close position: {order_response}"