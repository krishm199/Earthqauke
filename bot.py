import requests
import time
import os
import json

BOT_TOKEN = os.getenv("BOT_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")

USGS_URL = "https://earthquake.usgs.gov/earthquakes/feed/v1.0/summary/5.5_week.geojson"

SEEN_FILE = "seen.json"

# Load seen earthquake IDs
if os.path.exists(SEEN_FILE):
    with open(SEEN_FILE, "r") as f:
        seen_ids = set(json.load(f))
else:
    seen_ids = set()


def save_seen():
    with open(SEEN_FILE, "w") as f:
        json.dump(list(seen_ids), f)


def send_telegram(message):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"

    data = {
        "chat_id": CHAT_ID,
        "text": message,
        "parse_mode": "HTML",
        "disable_web_page_preview": False
    }

    response = requests.post(url, data=data)

    if response.status_code == 200:
        print("Telegram alert sent")
    else:
        print("Telegram error:", response.text)


# Prevent spam on first startup
first_run = True


def check_earthquakes():
    global first_run

    response = requests.get(USGS_URL, timeout=20)
    data = response.json()

    earthquakes = data["features"]

    earthquakes.reverse()

    for quake in earthquakes:
        quake_id = quake["id"]

        # First run: only save IDs, do not send alerts
        if first_run:
            seen_ids.add(quake_id)
            continue

        if quake_id not in seen_ids:
            seen_ids.add(quake_id)

            props = quake["properties"]

            magnitude = props.get("mag")
            place = props.get("place")
            quake_url = props.get("url")
            tsunami = props.get("tsunami")

            tsunami_text = "⚠️ Tsunami Warning Possible\n" if tsunami == 1 else ""

            message = (
                f"🌍 <b>New Earthquake Alert</b>\n\n"
                f"📈 Magnitude: <b>{magnitude}</b>\n"
                f"📍 Location: {place}\n"
                f"{tsunami_text}\n"
                f"🔗 {quake_url}"
            )

            send_telegram(message)
            save_seen()

    first_run = False


while True:
    try:
        print("Checking earthquakes...")
        check_earthquakes()

    except Exception as e:
        print("Error:", e)

    time.sleep(10)
