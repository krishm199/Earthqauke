import requests
import time
import os

# CONFIGURATION
TELEGRAM_TOKEN = "8865445174:AAEf_5LAUpnMllqQFjF3UI0q3CKw1oiO5zg"
CHAT_ID = "-1003810343797"

# USGS API URL for Magnitude 4.5+ past day
USGS_URL = "https://earthquake.usgs.gov/earthquakes/feed/v1.0/summary/4.5_day.geojson"

# Railway persistent volume directory setup
STORAGE_DIR = "/app/data"
if not os.path.exists(STORAGE_DIR):
    os.makedirs(STORAGE_DIR)
    
SEEN_FILE = os.path.join(STORAGE_DIR, "seen_earthquakes.txt")

def load_seen_quakes():
    """Loads previously notified earthquake IDs so you don't get spam."""
    if os.path.exists(SEEN_FILE):
        with open(SEEN_FILE, 'r') as f:
            return set(f.read().splitlines())
    return set()

def save_seen_quake(quake_id):
    """Saves a new earthquake ID to the file."""
    with open(SEEN_FILE, 'a') as f:
        f.write(f"{quake_id}\n")

def send_telegram_message(text):
    """Sends the notification to your Telegram channel/chat."""
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    payload = {
        "chat_id": CHAT_ID, 
        "text": text, 
        "parse_mode": "Markdown",
        "disable_web_page_preview": False
    }
    try:
        response = requests.post(url, json=payload)
        if response.status_code != 200:
            print(f"Telegram API Error: {response.text}")
    except Exception as e:
        print(f"Error connecting to Telegram: {e}")

def check_earthquakes():
    print("Checking USGS for new M5.5+ earthquakes...")
    seen_quakes = load_seen_quakes()
    
    try:
        response = requests.get(USGS_URL, timeout=5).json()
        features = response.get('features', [])
        
        for feature in reversed(features):
            properties = feature['properties']
            quake_id = feature['id']
            magnitude = properties['mag']
            place = properties['place']
            url = properties['url']
            
            if magnitude is not None and magnitude >= 5.5:
                if quake_id not in seen_quakes:
                    message = (
                        f"🚨 *New Major Earthquake Alert!* 🚨\n\n"
                        f"• *Magnitude:* {magnitude}\n"
                        f"• *Location:* {place}\n"
                        f"• [View on USGS Map]({url})"
                    )
                    send_telegram_message(message)
                    save_seen_quake(quake_id)
                    seen_quakes.add(quake_id)
                    print(f"Notification sent for quake: {quake_id} ({place})")
                
    except Exception as e:
        print(f"Error fetching data from USGS: {e}")

if __name__ == "__main__":
    print("Earthquake monitor started. Checking every 10 seconds...")
    
    # Initialize baseline data on fresh setup if file doesn't exist
    if not os.path.exists(SEEN_FILE):
        try:
            initial_response = requests.get(USGS_URL, timeout=5).json()
            with open(SEEN_FILE, 'w') as f:
                for feature in initial_response.get('features', []):
                    f.write(f"{feature['id']}\n")
            print("Initialized baseline data. Monitoring for FUTURE events now.")
        except Exception:
            print("Could not initialize baseline file. Starting fresh.")

    while True:
        check_earthquakes()
        time.sleep(10)  # Check interval set to 10 seconds
