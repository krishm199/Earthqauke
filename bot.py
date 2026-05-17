import requests
import time
import os
import json

BOT_TOKEN = os.getenv("BOT_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")

USGS_URL = "https://earthquake.usgs.gov/earthquakes/feed/v1.0/summary/5.5_week.geojson"

SEEN_FILE = "seen.json"

# Safe loading of seen IDs
try:
    if os.path.exists(SEEN_FILE):
        with open(SEEN_FILE, "r") as f:
            content = f.read().strip()

            if content:
                seen_ids = set(json.loads(content))
            else:
                seen_ids = set()
    else:
        seen_ids = set()

except Exception as e:
    print("seen.json error:", e)
    seen_ids = set()


def save_seen():
    try:
        with open(SEEN_FILE, "w") as f:
            json.dump(list(seen_ids), f)
    except Exception as e:
        print("Save error:", e)


def send_telegram(message):
    try:
        url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"

        data = {
            "chat_id": CHAT_ID,
            "text": message,
            "parse_mode": "HTML",
            "disable_web_page_preview": False
        }

        response = requests.post(url, data=data, timeout=20)

        print("Telegram response:", response.text)

    except Exception as e:
        print("Telegram error:", e)


first_run = True


def check_earthquakes():
    global first_run

    response = requests.get(USGS_URL, timeout=20)

    data = response.json()

    earthquakes = data.get("features", [])

    earthquakes.reverse()

    for quake in earthquakes:

        quake_id = quake.get("id")

        if not quake_id:
            continue

        # Prevent spam on first startup
        if first_run:
            seen_ids.add(quake_id)
            continue

        if quake_id not in seen_ids:

            seen_ids.add(quake_id)

            props = quake.get("properties", {})

            magnitude = props.get("mag", "Unknown")
            place = props.get("place", "Unknown Location")
            quake_url = props.get("url", "")

            tsunami = props.get("tsunami", 0)

            tsunami_text = ""

            if tsunami == 1:
                tsunami_text = "⚠️ Possible Tsunami Warning\n\n"

            message = (
                f"🌍 <b>New Earthquake Alert</b>\n\n"
                f"📈 Magnitude: <b>{magnitude}</b>\n"
                f"📍 Location: {place}\n\n"
                f"{tsunami_text}"
                f"🔗 {quake_url}"
            )

            send_telegram(message)

            save_seen()

    first_run = False


print("Bot started...")

while True:

    try:
        print("Checking earthquakes...")

        check_earthquakes()

    except Exception as e:
        print("Main loop error:", e)

    time.sleep(10)
