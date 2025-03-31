from flask import Flask, request
from telegram_api import send_message, send_photo
from bybit_client import get_usdt_balance
from futures_trader import close_position
from ai_utils import run_script_async, get_status
import config
import datetime
from log_utils import info, success, warn, error

app = Flask(__name__)

# Temporary storage for user amounts
trade_amounts = {}
pending_amount_input = set()

@app.route('/', methods=['POST'])
def webhook():
    payload = request.get_json()
    info(f"📬 Raw payload: {payload}")

    # ✅ Fix: unwrap if payload is a list (SendPulse-style fallback)
    if isinstance(payload, list):
        payload = payload[0]

    user_id = None
    text = None

    # Handle standard message
    if 'message' in payload:
        msg = payload['message']
        user_id = msg['from']['id']
        text = msg.get('text', '').strip()

    # Handle button callback
    elif 'callback_query' in payload:
        callback = payload['callback_query']
        user_id = callback['from']['id']
        text = callback['data']

    if not user_id or not text:
        warn("Missing user_id or text")
        return '', 200

    if int(user_id) not in config.ALLOWED_USERS:
        warn(f"Access denied for user: {user_id}")
        send_message(user_id, f"⛔️ Access denied. Your ID is: {user_id}")
        return '', 200

    success(f"✅ Command: {text} from {user_id}")

    # Handle amount input
    if user_id in pending_amount_input:
        try:
            amount = float(text)
            trade_amounts[user_id] = amount
            pending_amount_input.remove(user_id)
            send_message(user_id, f"✅ Amount set to: {amount} USDT")
        except ValueError:
            send_message(user_id, "❌ Invalid input. Please enter a numeric amount.")
        return '', 200

    if text == '/start':
        welcome = (
            "👋 Hi! I'm your crypto trading bot 🤖\n\n"
            "Use the buttons below or type a command."
        )
        keyboard = {
            "inline_keyboard": [
                [
                    {"text": "💰 Balance", "callback_data": "/balance"},
                    {"text": "📈 Status", "callback_data": "/status"}
                ],
                [
                    {"text": "📉 Simulate", "callback_data": "/simulate"},
                    {"text": "🔄 Update Data", "callback_data": "/updatedata"}
                ],
                [
                    {"text": "🧠 Train Model", "callback_data": "/trainmodel"},
                    {"text": "💵 Set Amount", "callback_data": "/setamount"}
                ],
                [
                    {"text": "🤖 Paper Trade", "callback_data": "/papertrade"},
                    {"text": "❌ Stop & Close", "callback_data": "/closeposition"}
                ],
                [
                    {"text": "ℹ️ Help", "callback_data": "/help"}
                ]
            ]
        }
        send_message(user_id, welcome, reply_markup=keyboard)

    elif text == '/balance':
        balance = get_usdt_balance()
        send_message(user_id, f"💰 Your current USDT balance: {balance}")

    elif text == '/status':
        status_msg = get_status()
        send_message(user_id, status_msg)

    elif text == '/simulate':
        def on_start():
            send_message(user_id, "📉 Starting simulation...")
        def on_finish():
            caption = (
                f"📉 Simulation completed ✅\n"
                f"🕒 Time: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
                f"📄 Logs saved to 'simulation_log.csv'\n"
                f"📈 Equity chart:"
            )
            send_photo(user_id, 'equity_curve.png', caption=caption)
        run_script_async('run_simulation.py', on_start=on_start, on_finish=on_finish)

    elif text == '/updatedata':
        def on_start():
            send_message(user_id, "🔄 Fetching fresh OHLCV data...")
        def on_finish():
            send_message(user_id, f"✅ Data updated\n🕒 {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        run_script_async('fetch_data.py', on_start=on_start, on_finish=on_finish)

    elif text == '/trainmodel':
        def on_start():
            send_message(user_id, "🧠 Starting model training...")
        def on_finish():
            send_message(user_id, f"✅ Model trained\n🕒 {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        run_script_async('train_ppo.py', on_start=on_start, on_finish=on_finish)

    elif text == '/papertrade':
        def on_start():
            send_message(user_id, "📈 Starting paper trading...")
        run_script_async('paper_trader.py', on_start=on_start)

    elif text == '/setamount':
        send_message(user_id, "💵 Please enter the amount in USDT:")
        pending_amount_input.add(user_id)

    elif text == '/closeposition':
        send_message(user_id, "🛘 Stopping bot and closing position...")
        success_flag, msg = close_position()
        send_message(user_id, msg if success_flag else f"❌ Failed to close position: {msg}")

    elif text == '/help':
        help_text = (
            "📖 *Available Commands*\n\n"
            "/start - Show menu\n"
            "/balance - Show USDT balance\n"
            "/setamount - Set trading amount\n"
            "/simulate - Run backtest\n"
            "/updatedata - Refresh OHLCV\n"
            "/trainmodel - Train model\n"
            "/status - DB/model info\n"
            "/papertrade - Run paper trading\n"
            "/closeposition - Stop bot"
        )
        send_message(user_id, help_text)

    return '', 200

if __name__ == '__main__':
    import os
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=True)
