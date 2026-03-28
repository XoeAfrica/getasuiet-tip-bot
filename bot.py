import os
import time
import sqlite3
import re
import tweepy
from pysui import SuiConfig, SyncClient

print("Starting GetASUiet Tip Bot - Minimal Stable (Mentions Disabled)... 💙☔️")

# CONFIG
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

try:
    me = client.get_me()
    print(f"✅ Authenticated as @{me.data.username} (ID: {me.data.id})")
    BOT_USER_ID = me.data.id
except Exception as e:
    print(f"❌ Auth failed: {e}")
    BOT_USER_ID = None

cfg = SuiConfig.user_config(rpc_url=RPC_URL, prv_keys=[SUI_PRV_KEY])
sui_client = SyncClient(cfg)
BOT_SUI_ADDRESS = str(cfg.active_address)
print(f"🚀 Bot Sui address: {BOT_SUI_ADDRESS} (Testnet)")

print("🤖 GetASUiet Tip Bot is running MINIMAL STABLE (mentions disabled until credits added)... 💙☔️🪙🍭")

# Database (kept for future)
conn = sqlite3.connect('bot.db', check_same_thread=False)
c = conn.cursor()
c.execute('''CREATE TABLE IF NOT EXISTS users (x_handle TEXT PRIMARY KEY, sui_address TEXT UNIQUE)''')
c.execute('''CREATE TABLE IF NOT EXISTS last_tweet (id INTEGER)''')
conn.commit()

def save_last_id(tid):
    c.execute("DELETE FROM last_tweet")
    c.execute("INSERT INTO last_tweet (id) VALUES (?)", (tid,))
    conn.commit()

print("✅ Bot is stable and waiting for credits. No mentions checking for now.")

# Keep the process alive
while True:
    try:
        print("🤖 Bot is alive (mentions disabled). Top up credits to enable tipping.")
        time.sleep(120)  # Sleep 2 minutes
    except Exception as e:
        print(f"Loop error: {e}")
        time.sleep(120)
