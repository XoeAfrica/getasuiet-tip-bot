import os
import time
import sqlite3
import re
import tweepy
import random
from pysui import SuiConfig, SyncClient
from pysui.sui.sui_types import SuiAddress
from pysui.sui.sui_txn import SyncTransaction

print("Starting GetASUiet Tip Bot - Full Version with 3% Fee... 💙☔️")

# === CONFIG ===
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
    me = client.get_me(user_auth=True)
    print(f"✅ Authenticated as @{me.data.username} (ID: {me.data.id})")
    BOT_USER_ID = me.data.id
except Exception as e:
    print(f"❌ Auth failed: {e}")
    BOT_USER_ID = None

cfg = SuiConfig.user_config(rpc_url=RPC_URL, prv_keys=[SUI_PRV_KEY])
sui_client = SyncClient(cfg)
BOT_SUI_ADDRESS = str(cfg.active_address)
print(f"🚀 Bot Sui address: {BOT_SUI_ADDRESS} (Testnet)")

print("🤖 GetASUiet Tip Bot FULL VERSION is running! 💙☔️🪙🍭")

# Database
conn = sqlite3.connect('bot.db', check_same_thread=False)
c = conn.cursor()
c.execute('''CREATE TABLE IF NOT EXISTS users (x_handle TEXT PRIMARY KEY, sui_address TEXT UNIQUE)''')
c.execute('''CREATE TABLE IF NOT EXISTS last_tweet (id INTEGER)''')
conn.commit()

def get_last_id():
    c.execute("SELECT id FROM last_tweet")
    row = c.fetchone()
    return row[0] if row else 0

def save_last_id(tid):
    c.execute("DELETE FROM last_tweet")
    c.execute("INSERT INTO last_tweet (id) VALUES (?)", (tid,))
    conn.commit()

def register_user(x_handle, sui_address):
    try:
        c.execute("INSERT INTO users (x_handle, sui_address) VALUES (?, ?)", (x_handle.lower(), sui_address))
        conn.commit()
        return True
    except:
        return False

def get_user_address(x_handle):
    c.execute("SELECT sui_address FROM users WHERE x_handle=?", (x_handle.lower(),))
    row = c.fetchone()
    return row[0] if row else None

last_id = get_last_id()

# Strong variations to avoid 403
thank_you_phrases = [
    "Thanks for the tip! 💙",
    "Appreciate your support ☔️",
    "Much love for this tip 🍭",
    "Awesome tip, thank you! 🪙",
    "Grateful for your generosity ✨",
    "Thanks a lot! Keep tipping 🚀"
]

while True:
    try:
        print("🔄 Checking mentions...")
        response = None
        
        if BOT_USER_ID:
            try:
                response = client.get_users_mentions(id=BOT_USER_ID, max_results=10, user_auth=True)
            except Exception as api_err:
                print(f"❌ X API Error: {str(api_err)[:150]}")

        if response and hasattr(response, 'data') and response.data:
            for tweet in reversed(response.data):
                tid = tweet.id
                if tid <= last_id:
                    continue

                text = tweet.text.lower()

                # Get tipper username safely
                try:
                    if hasattr(tweet, 'author_id') and tweet.author_id:
                        user_resp = client.get_user(id=tweet.author_id, user_auth=True)
                        tipper_handle = user_resp.data.username
                    else:
                        tipper_handle = "unknown"
                except Exception as user_err:
                    print(f"⚠️ Could not get user info for tweet {tid}: {user_err}")
                    tipper_handle = "unknown"

                # === REGISTER LOGIC (independent + better logging) ===
                if "register 0x" in text:
                    addr_match = re.search(r"0x[a-f0-9]{64}", text)
                    if addr_match:
                        addr_str = addr_match.group(0)
                        success = register_user(tipper_handle, addr_str)
                        if success:
                            msg = "✅ Registered successfully! 💙☔️ You can now receive tips 🍭 #GetASuiet"
                            print(f"✅ Registration successful for @{tipper_handle}")
                        else:
                            msg = "✅ Already registered 💙 #GetASuiet"
                            print(f"ℹ️ @{tipper_handle} was already registered")
                        
                        try:
                            client.create_tweet(text=msg, in_reply_to_tweet_id=tid, user_auth=True)
                            print(f"✅ Registration​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​