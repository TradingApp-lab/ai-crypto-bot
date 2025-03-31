import requests
import config
import os
from log_utils import success, error

def send_message(chat_id, text, parse_mode=None, reply_markup=None):
    url = f"https://api.telegram.org/bot{config.BOT_TOKEN}/sendMessage"

    payload = {
        "chat_id": chat_id,
        "text": text
    }

    if parse_mode:
        payload["parse_mode"] = parse_mode

    if reply_markup:
        payload["reply_markup"] = reply_markup

    print(f"\n📤 send_message() called → chat_id: {chat_id}")
    print(f"🔗 URL: {url}")
    print(f"📦 Payload: {payload}")

    try:
        response = requests.post(url, json=payload)
        print(f"📨 Response status: {response.status_code}")
        print(f"📨 Response body: {response.text}")
        response.raise_for_status()
        success("✅ Message sent successfully")
    except requests.exceptions.RequestException as e:
        error(f"❌ Error sending message: {e}")
        print(f"📨 Response: {response.text}")

def send_photo(chat_id, image_path, caption=None):
    url = f"https://api.telegram.org/bot{config.BOT_TOKEN}/sendPhoto"

    if not os.path.exists(image_path):
        error(f"❌ File not found: {image_path}")
        return

    try:
        with open(image_path, 'rb') as photo:
            files = {"photo": photo}
            data = {"chat_id": chat_id}
            if caption:
                data["caption"] = caption
            response = requests.post(url, data=data, files=files)
            response.raise_for_status()
            success("✅ Photo sent successfully")
    except requests.exceptions.RequestException as e:
        error(f"⚠️ Error sending photo: {e}")
