import os
import time
import sqlite3
import re
import tweepy
from pysui import SuiConfig, SyncClient

# === CONFIG FROM RAILWAY ===
X_CONSUMER_KEY = os.getenv("X_CONSUMER_KEY")
X_CONSUMER_SECRET = os.getenv("X_CONSUMER_SECRET")
X_ACCESS_TOKEN = os.getenv("X_ACCESS_TOKEN")
X_ACCESS_TOKEN_SECRET = os.getenv("X_ACCESS_TOKEN_SECRET")
SUI_PRV_KEY = os.getenv("SUI_PRV_KEY")
RPC_URL = os.getenv("RPC_URL", "https://fullnode.mainnet.sui.io:443")

# Connect to X
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

print(f"🚀 Bot Sui address: {BOT_SUI_ADDRESS} (tell people to send SUI here!)")

# Database
conn = sqlite3.connect('bot.db', check_same_thread=False)
c = conn.cursor()
c.execute('''CREATE TABLE IF NOT EXISTS users 
             (x_handle TEXT PRIMARY KEY, sui_address TEXT UNIQUE, balance INTEGER DEFAULT 0)''')
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

def process_tip(tweet, tipper_handle, recipient_handle, amount):
    tipper_data = get_user(tipper_handle)
    if not tipper_data:
        client.create_tweet(text=f"@{tipper_handle} Please register first! Reply: @GetASUiet register 0xYOURADDRESS 💙☔️ #GetASuiet", in_reply_to_tweet_id=tweet.id)
        return
    balance = tipper_data[1]
    if balance < amount * 1_000_000_000:
        client.create_tweet(text=f"@{tipper_handle} Not enough balance! 💙 Check with @GetASUiet balance", in_reply_to_tweet_id=tweet.id)
        return
    fee = int(amount * 0.03 * 1_000_000_000)
    tip_mist = int(amount * 1_000_000_000)
    new_tipper = balance - tip_mist
    recipient_data = get_user(recipient_handle)
    if recipient_data:
        new_recip = recipient_data[1] + (tip_mist - fee)
        update_balance(recipient_handle, new_recip)
    else:
        c.execute("INSERT OR IGNORE INTO users (x_handle, sui_address, balance) VALUES (?, ?, ?)", (recipient_handle.lower(), "pending", tip_mist - fee))
        conn.commit()
    update_balance(tipper_handle, new_tipper)
    reply = f"💙☔️🪙💚🍭 Tip processed! {amount} $SUI from @{tipper_handle} → @{recipient_handle} (3% fee kept for bot). #GetASuiet"
    client.create_tweet(text=reply, in_reply_to_tweet_id=tweet.id)

# Main loop
print("🤖 GetASUiet Tip Bot is running! 💙☔️🪙💚🍭")
last_id = get_last_id()

while True:
    try:
        response = client.search_recent_tweets(
            query="#GetASuiet @GetASUiet",
            since_id=last_id,
            max_results=10,
            tweet_fields=["author_id"]
        )
        if response.data:
            for tweet in reversed(response.data):
                tid = tweet.id
                if tid <= last_id: continue
                text = tweet.text.lower()
                author_id = tweet.author_id
                try:
                    user_resp = client.get_user(author_id)
                    tipper_handle = user_resp.data.username
                except:
                    tipper_handle = "user"

                # Register command
                if "register 0x" in text:
                    addr = re.search(r"0x[a-f0-9]+", text).group(0)
                    if register_user(tipper_handle, addr):
                        client.create_tweet(text=f"✅ @{tipper_handle} Registered! 💙☔️ Send SUI to {BOT_SUI_ADDRESS} to deposit. #GetASuiet", in_reply_to_tweet_id=tid)
                    else:
                        client.create_tweet(text=f"@{tipper_handle} Already registered or error 💙", in_reply_to_tweet_id=tid)

                # Balance command
                elif "balance" in text:
                    data = get_user(tipper_handle)
                    bal = data[1] / 1_000_000_000 if data else 0
                    client.create_tweet(text=f"@{tipper_handle} Your balance: {bal} $SUI 💙☔️ #GetASuiet", in_reply_to_tweet_id=tid)

                # Tip command
                else:
                    match = re.search(r'@(\w+)\s*(\d+\.?\d*)\s*sui?', text)
                    if match:
                        recipient = match.group(1)
                        amount = float(match.group(2))
                        if amount > 50 or amount <= 0: continue
                        process_tip(tweet, tipper_handle, recipient, amount)
                        last_id = tid
                        save_last_id(tid)

        time.sleep(30)
    except Exception as e:
        print("Error:", e)
        time.sleep(30)
