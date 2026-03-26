import os
import time
import sqlite3
import re
import tweepy
from pysui import SuiConfig, SyncClient

print("Starting GetASUiet Tip Bot... 💙☔️")

# Config from Railway
X_CONSUMER_KEY = os.getenv("X_CONSUMER_KEY")
X_CONSUMER_SECRET = os.getenv("X_CONSUMER_SECRET")
X_ACCESS_TOKEN = os.getenv("X_ACCESS_TOKEN")
X_ACCESS_TOKEN_SECRET = os.getenv("X_ACCESS_TOKEN_SECRET")
SUI_PRV_KEY = os.getenv("SUI_PRV_KEY")
RPC_URL = os.getenv("RPC_URL", "https://sui-testnet-rpc.publicnode.com")

# Connect to X (this may still give 401 until permissions fully activate)
client = tweepy.Client(
    consumer_key=X_CONSUMER_KEY,
    consumer_secret=X_CONSUMER_SECRET,
    access_token=X_ACCESS_TOKEN,
    access_token_secret=X_ACCESS_TOKEN_SECRET
)

# Connect to Sui
cfg = SuiConfig.user_config(rpc_url=RPC_URL, prv_keys=[SUI_PRV_KEY])
sui_client = SyncClient(cfg)
BOT_SUI_ADDRESS = str(cfg.active_address)
print(f"🚀 Bot Sui address: {BOT_SUI_ADDRESS}")

print("🤖 GetASUiet Tip Bot is running! 💙☔️🪙💚🍭")

# Simple loop - only logs for now to avoid crash
while True:
    try:
        response = client.search_recent_tweets(
            query="@GetASUiet",
            max_results=5
        )
        if response.data:
            for tweet in response.data:
                print(f"Detected tweet: {tweet.text[:100]}...")
        time.sleep(20)
    except Exception as e:
        print(f"Error: {e}")
        time.sleep(20)
