# test_request.py
import requests

def test_bybit_api():
    url = "https://api.bybit.com/v5/market/time"
    try:
        print("📡 Sending request to Bybit...")
        response = requests.get(url)
        print("✅ Status code:", response.status_code)
        print("📄 Response body:", response.text)
    except Exception as e:
        print("❌ Exception occurred:", str(e))

if __name__ == "__main__":
    test_bybit_api()
