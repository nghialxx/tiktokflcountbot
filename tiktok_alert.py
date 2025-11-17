#!/usr/bin/env python3
import requests
from bs4 import BeautifulSoup
import re
import json
import time
import random
import os

# Configuration
USERNAME = "ts.bs.phamduy"
BOT_TOKEN = os.environ.get("BOT_TOKEN")
GF_CHAT_ID = int(os.environ.get("GF_CHAT_ID"))

THRESHOLDS = [4742, 5000, 10000, 15000, 20000, 25000]
NEAR_MARGIN = 10

def send_telegram(message):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    payload = {"chat_id": GF_CHAT_ID, "text": message}
    try:
        requests.get(url, params=payload, timeout=10)
    except Exception as e:
        print(f"Telegram error: {e}")

# Random delay ±2 minutes
time.sleep(random.randint(0, 240))

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
            for threshold in THRESHOLDS:
                if threshold - NEAR_MARGIN <= follower_count < threshold:
                    send_telegram(f"Em Nghĩa thông báo @{USERNAME} kênh sắp đạt {threshold} followers! Hiện tại đã là: {follower_count} rồi!")
        else:
            print(json.dumps({"status": "failed", "value": None}))
    else:
        print(json.dumps({"status": "error", "value": None}))
except Exception as e:
    print(json.dumps({"status": "error", "value": None}))
