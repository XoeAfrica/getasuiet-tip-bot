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
    x_handle = x_handle.lower().strip().replace(" ", "")
    try:
        c.execute("INSERT INTO users (x_handle, sui_address) VALUES (?, ?)", (x_handle, sui_address))
        conn.commit()
        return True
    except:
        return False

def get_user_address(x_handle):
    x_handle = x_handle.lower().strip().replace(" ", "")
    c.execute("SELECT sui_address FROM users WHERE x_handle=?", (x_handle,))
    row = c.fetchone()
    return row[0] if row else None

last_id = get_last_id()

while True:
    try:
        print("🔄 Checking mentions...")
        response = None
        if BOT_USER_ID:
            try:
                response = client.get_users_mentions(id=BOT_USER_ID, max_results=10, user_auth=True)
            except Exception as e:
                print(f"❌ Mention fetch error: {e}")

        if response and hasattr(response, 'data') and response.data:
            for tweet in reversed(response.data):
                tid = tweet.id
                if tid <= last_id:
                    continue

                text = tweet.text.lower()

                # Get tipper
                try:
                    if hasattr(tweet, 'author_id') and tweet.author_id:
                        user_resp = client.get_user(id=tweet.author_id, user_auth=True)
                        tipper_handle = user_resp.data.username
                    else:
                        tipper_handle = "unknown"
                except:
                    tipper_handle = "unknown"

                # === REGISTER LOGIC ===
                if "register 0x" in text:
                    addr_match = re.search(r"0x[a-f0-9]{64}", text)
                    if addr_match:
                        addr_str = addr_match.group(0)
                        success = register_user(tipper_handle, addr_str)
                        status = "Success" if success else "Already registered"
                        print(f"Registration for @{tipper_handle}: {status}")
                        msg = f"✅ {status}! 💙☔️ You can now receive tips 🍭 #GetASuiet"
                        try:
                            client.create_tweet(text=msg, in_reply_to_tweet_id=tid, user_auth=True)
                            print(f"✅ Registration reply sent")
                        except Exception as e:
                            print(f"❌ Registration reply failed: {e}")
                        last_id = tid
                        save_last_id(tid)
                        continue

                # === TIP LOGIC - Matches your new input format ===
                # Looks for 🎁🎉 @username +amount SUI #GetASuiet
                match = re.search(r'🎁🎉\s*@?([a-zA-Z0-9_]+)\s*\+?(\d+\.?\d*)\s*sui?', text, re.IGNORECASE)
                if match:
                    recipient_handle = match.group(1).strip()

                    try:
                        amount = float(match.group(2))
                    except:
                        amount = 0

                    if amount > 0:
                        fee = round(amount * 0.03, 4)
                        net_amount = round(amount - fee, 4)

                        print(f"💰 Tip detected: {amount} SUI → Net {net_amount} SUI to @{recipient_handle}")

                        recipient_addr = get_user_address(recipient_handle)
                        if recipient_addr:
                            try:
                                txn = SyncTransaction(sui_client)
                                txn.transfer_sui(
                                    recipient=SuiAddress(recipient_addr),
                                    amount=int(net_amount * 1_000_000_000),
                                    sender=BOT_SUI_ADDRESS
                                )
                                txn.execute()
                                print(f"✅ Sent {net_amount} SUI to @{recipient_handle}")
                            except Exception as e:
                                print(f"❌ Sui transfer failed: {e}")
                        else:
                            print(f"⚠️ @{recipient_handle} not registered - no transfer sent")

                        # Your exact requested reply format
                        reply = f"🎁🎉@{recipient_handle} +{net_amount} SUI #GetASuiet 🍭"

                        try:
                            client.create_tweet(text=reply, in_reply_to_tweet_id=tid, user_auth=True)
                            print(f"✅ Reply posted: {reply}")
                        except Exception as e:
                            print(f"❌ Reply failed: {e}")

                last_id = tid
                save_last_id(tid)

        time.sleep(180)

    except Exception as e:
        print(f"Main loop error (continuing): {e}")
        time.sleep(180)