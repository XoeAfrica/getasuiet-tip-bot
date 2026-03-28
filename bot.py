import os
import time
import sqlite3
import re
import tweepy
from pysui import SuiConfig, SyncClient

print("Starting GetASUiet Tip Bot... 💙☔️")

# === CONFIG FROM RAILWAY ===
X_CONSUMER_KEY = os.getenv("X_CONSUMER_KEY")
X_CONSUMER_SECRET = os.getenv("X_CONSUMER_SECRET")
X_ACCESS_TOKEN = os.getenv("X_ACCESS_TOKEN")
X_ACCESS_TOKEN_SECRET = os.getenv("X_ACCESS_TOKEN_SECRET")
SUI_PRV_KEY = os.getenv("SUI_PRV_KEY")
RPC_URL = os.getenv("RPC_URL", "https://sui-testnet-rpc.publicnode.com")

# Connect to X
client = tweepy.Client(
    consumer_key=X_CONSUMER_KEY,
    consumer_secret=X_CONSUMER_SECRET,
    access_token=X_ACCESS_TOKEN,
    access_token_secret=X_ACCESS_TOKEN_SECRET
)

# === AUTH TEST + TEST TWEET (activates the token) ===
try:
    me = client.get_me()
    print(f"✅ Authenticated as @{me.data.username} (ID: {me.data.id})")
    BOT_USER_ID = me.data.id

    # One-time test tweet
    test_tweet = client.create_tweet(text="🤖 GetASUiet Tip Bot is now LIVE on mainnet! 💙☔️🍭 #GetASuiet")
    # Safe ID access (works for both dict and Response object)
    tweet_id = test_tweet.data.id if hasattr(test_tweet, 'data') and hasattr(test_tweet.data, 'id') else test_tweet.get('id', 'unknown')
    print(f"✅ Test tweet posted! ID: {tweet_id}")
except Exception as e:
    print(f"❌ Auth/test tweet failed: {e}")
    BOT_USER_ID = None

# Connect to Sui
cfg = SuiConfig.user_config(rpc_url=RPC_URL, prv_keys=[SUI_PRV_KEY])
sui_client = SyncClient(cfg)
BOT_SUI_ADDRESS = str(cfg.active_address)
print(f"🚀 Bot Sui address: {BOT_SUI_ADDRESS}")

print("🤖 GetASUiet Tip Bot is running! 💙☔️🪙💚🍭")

# Database
conn = sqlite3.connect('bot.db', check_same_thread=False)
c = conn.cursor()
c.execute('''CREATE TABLE IF NOT EXISTS users (x_handle TEXT PRIMARY KEY, sui_address TEXT UNIQUE, balance INTEGER DEFAULT 0)''')
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

def get_user(x_handle):
    c.execute("SELECT sui_address, balance FROM users WHERE x_handle=?", (x_handle.lower(),))
    return c.fetchone()

def update_balance(x_handle, new_balance):
    c.execute("UPDATE users SET balance=? WHERE x_handle=?", (new_balance, x_handle.lower()))
    conn.commit()

# Main loop
last_id = get_last_id()

while True:
    try:
        print("🔄 Checking mentions...")
        if BOT_USER_ID:
            # Extra retries + logging to keep the bot alive
            for attempt in range(5):
                try:
                    response = client.get_users_mentions(
                        id=BOT_USER_ID,
                        max_results=10
                    )
                    print(f"✅ Got {len(response.data) if response and response.data else 0} mentions")
                    break
                except Exception as inner_e:
                    print(f"❌ Mentions attempt {attempt+1}/5 failed: {inner_e}")
                    if attempt == 4:
                        raise
                    time.sleep(8)
        else:
            response = None

        if response and response.data:
            for tweet in reversed(response.data):
                tid = tweet.id
                if tid <= last_id: continue
                text = tweet.text.lower()

                try:
                    user_resp = client.get_user(tweet.author_id)
                    tipper_handle = user_resp.data.username
                except:
                    tipper_handle = "user"

                # Tip logic
                match = re.search(r'@(\w+)\s*\+?(\d+\.?\d*)\s*sui?', text)
                if match:
                    recipient = match.group(1)
                    amount = float(match.group(2))
                    if 0 < amount <= 50:
                        reply = f"💙☔️🪙 {amount} $SUI tipped to @{recipient}! Thank you for tipping 🍭 #GetASuiet"
                        try:
                            client.create_tweet(text=reply, in_reply_to_tweet_id=tid)
                        except:
                            print("Could not post reply")

                # Register logic
                if "register 0x" in text:
                    addr = re.search(r"0x[a-f0-9]+", text)
                    if addr:
                        addr = addr.group(0)
                        if register_user(tipper_handle, addr):
                            reply = "✅ Registered! 💙☔️ Send test SUI to the bot to start tipping 🍭 #GetASuiet"
                            try:
                                client.create_tweet(text=reply, in_reply_to_tweet_id=tid)
                            except:
                                print("Could not post reply")
                        else:
                            reply = "Already registered 💙 #GetASuiet"
                            try:
                                client.create_tweet(text=reply, in_reply_to_tweet_id=tid)
                            except:
                                pass

                # Balance logic
                if "balance" in text:
                    data = get_user(tipper_handle)
                    bal = data[1] / 1_000_000_000 if data else 0
                    reply = f"💙 Your balance: {bal:.2f} $SUI ☔️🍭 #GetASuiet"
                    try:
                        client.create_tweet(text=reply, in_reply_to_tweet_id=tid)
                    except:
                        print("Could not post reply")

                last_id = tid
                save_last_id(tid)

        time.sleep(15)
    except Exception as e:
        print(f"Error: {e}")
        time.sleep(15)
