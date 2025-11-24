#!/usr/bin/env python3
import requests
from bs4 import BeautifulSoup
import re
import json
import os

# Configuration
USERNAME = "ts.bs.phamduy"
BOT_TOKEN = os.environ.get("BOT_TOKEN")
GF_CHAT_ID = int(os.environ.get("GF_CHAT_ID"))

THRESHOLDS = [5000, 10000, 15000, 20000, 25000]

def get_margin_for_threshold(threshold):
    """
    Get notification margin based on threshold.
    - For thresholds <= 10K: Use 5 (can read exact counts like 9999)
    - For thresholds > 10K: Use 100 (TikTok shows 14.9K, can't read exact)
    """
    if threshold <= 10000:
        return 5
    else:
        return 100

# Load last follower count
last_count = 0
try:
    with open('last_count.json', 'r') as f:
        data = json.load(f)
        last_count = data.get('count', 0)
        print(f"Last count: {last_count}")
except FileNotFoundError:
    print("No previous count found, starting fresh")
except Exception as e:
    print(f"Error loading last count: {e}")

def send_telegram(message):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    payload = {"chat_id": GF_CHAT_ID, "text": message}
    try:
        response = requests.get(url, params=payload, timeout=10)
        print(f"Telegram message sent. Status: {response.status_code}, Response: {response.text}")
    except Exception as e:
        print(f"Telegram error: {e}")

url = f"https://www.tiktok.com/@{USERNAME}"
headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
    'Accept-Language': 'en-US,en;q=0.9',
}

follower_count = None
try:
    response = requests.get(url, headers=headers, timeout=10)
    if response.status_code == 200:
        html = response.text

        # Method 1: JSON data
        match = re.search(r'<script id="__UNIVERSAL_DATA_FOR_REHYDRATION__" type="application/json">(.*?)</script>', html, re.DOTALL)
        if match:
            try:
                data = json.loads(match.group(1))
                follower_count = data['__DEFAULT_SCOPE__']['webapp.user-detail']['userInfo']['stats']['followerCount']
            except:
                pass

        # Method 2: HTML parsing
        if not follower_count:
            soup = BeautifulSoup(html, 'html.parser')
            element = soup.find('strong', {'data-e2e': 'followers-count'})
            if element:
                follower_count = int(element.text.replace(',', ''))

        # Method 3: Regex fallback
        if not follower_count:
            match = re.search(r'"followerCount":(\d+)', html)
            if match:
                follower_count = int(match.group(1))

        # Output JSON
        if follower_count:
            print(json.dumps({"status": "success", "value": follower_count}))

            # Only send alert if count increased AND within threshold range
            for threshold in THRESHOLDS:
                margin = get_margin_for_threshold(threshold)
                if threshold - margin <= follower_count < threshold:
                    if follower_count > last_count:
                        send_telegram(f"Em Nghĩa thông báo @{USERNAME} kênh sắp đạt {threshold} followers! Hiện tại đã là: {follower_count} rồi!")
                        print(f"Alert sent for threshold {threshold} with margin {margin}")
                    else:
                        print(f"Follower count {follower_count} unchanged from last check, skipping alert (threshold: {threshold}, margin: {margin})")

            # Save current count
            try:
                with open('last_count.json', 'w') as f:
                    json.dump({'count': follower_count}, f)
                print(f"Saved new count: {follower_count}")
            except Exception as e:
                print(f"Error saving count: {e}")
        else:
            print(json.dumps({"status": "failed", "value": None}))
    else:
        print(json.dumps({"status": "error", "value": None}))
except Exception as e:
    print(json.dumps({"status": "error", "value": None}))
