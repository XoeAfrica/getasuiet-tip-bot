import os
import time
import sqlite3
import re
import tweepy
from pysui import SuiConfig, SyncClient

print("Starting GetASUiet Tip Bot... 💙☔️")

# Config
X_CONSUMER_KEY = os.getenv("X_CONSUMER_KEY")
X_CONSUMER_SECRET = os.getenv("X_CONSUMER_SECRET")
X_ACCESS_TOKEN = os.getenv("X_ACCESS_TOKEN")
X_ACCESS_TOKEN_SECRET = os.getenv("X_ACCESS_TOKEN_SECRET")
SUI_PRV_KEY = os.getenv("SUI_PRV_KEY")
RPC_URL = os.getenv("RPC_URL", "https://sui-testnet-rpc.publicnode.com")

client = tweepy.Client(
    consumer_key=X_CONSUMER_KEY,
    consumer_secret=X_CONSUMER_SECRET,
    access_token=X_ACCESS_TOKEN,
    access_token_secret=X_ACCESS_TOKEN_SECRET
)

cfg = SuiConfig.user_config(rpc_url=RPC_URL, prv_keys=[SUI_PRV_KEY])
sui_client = SyncClient(cfg)
BOT_SUI_ADDRESS = str(cfg.active_address)
print(f"🚀 Bot Sui address: {BOT_SUI_ADDRESS}")

print("🤖 GetASUiet Tip Bot is running! 💙☔️🪙💚🍭")

# Main loop with your requested changes
last_id = 0

while True:
    try:
        response = client.search_recent_tweets(
            query="@GetASUiet",
            max_results=10
        )
        if response.data:
            for tweet in reversed(response.data):
                text = tweet.text.lower()
                try:
                    user_resp = client.get_user(tweet.author_id)
                    tipper_handle = user_resp.data.username
                except:
                    tipper_handle = "user"

                # Support both "5SUI" and "+5SUI"
                match = re.search(r'@(\w+)\s*\+?(\d+\.?\d*)\s*sui?', text)
                if match:
                    recipient = match.group(1)
                    amount = float(match.group(2))
                    if 0 < amount <= 50:
                        print(f"Processing tip: {amount} SUI from {tipper_handle} to {recipient}")
                        # For now we log only (replies disabled to avoid 401)
                        print(f"💙☔️🪙 {amount} $SUI tipped to @{recipient}! Thank you for tipping 🍭 #GetASuiet")

                # Register
                if "register 0x" in text:
                    addr = re.search(r"0x[a-f0-9]+", text)
                    if addr:
                        print(f"Register request from {tipper_handle}")
                        print("✅ Registered! 💙☔️ Send test SUI to the bot to start tipping 🍭 #GetASuiet")

                # Balance
                if "balance" in text:
                    print(f"Balance request from {tipper_handle}")
                    print("💙 Your balance: 0.00 $SUI ☔️🍭 #GetASuiet")  # placeholder for now

        time.sleep(15)
    except Exception as e:
        print(f"Error: {e}")
        time.sleep(15)
