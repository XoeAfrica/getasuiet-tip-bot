import os
import time
import sqlite3
import re
import tweepy
from pysui import SuiConfig, SyncClient
from pysui.sui.sui_txn import SyncTransaction

print("🚀 GetASUiet Tip Bot - SUPER LIGHT VERSION (credit-friendly + X-compliant) 💙☔️")

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
    print(f"✅ Authenticated as @{me.data.username}")
    BOT_USER_ID = me.data.id
except Exception as e:
    print(f"❌ X Auth failed: {e}")
    exit(1)

# Sui setup
cfg = SuiConfig.user_config(rpc_url=RPC_URL, prv_keys=[SUI_PRV_KEY])
sui_client = SyncClient(cfg)
BOT_SUI_ADDRESS = str(cfg.active_address)
print(f"🚀 Bot Sui address: {BOT_SUI_ADDRESS} (Testnet)")

# === DATABASE ===
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
    except sqlite3.IntegrityError:
        return False

def get_user_address(x_handle):
    c.execute("SELECT sui_address FROM users WHERE x_handle=?", (x_handle.lower(),))
    row = c.fetchone()
    return row[0] if row else None

# === SUI TIP (3% fee) ===
def send_sui_tip(recipient_address: str, amount_sui: float) -> tuple[bool, str]:
    try:
        amount_mist = int(amount_sui * 1_000_000_000)
        fee_mist = int(amount_mist * 0.03)
        net_mist = amount_mist - fee_mist

        if net_mist < 1_000_000:
            return False, "Amount too small after fee"

        tx = SyncTransaction(client=sui_client)
        split_coin = tx.split_coin(coin=tx.gas, amounts=[net_mist])
        tx.transfer_objects(transfers=[split_coin], recipient=recipient_address)

        tx_result = tx.execute(gas_budget="5000000")

        if tx_result.is_ok():
            digest = getattr(tx_result.result_data, "digest", str(tx_result))
            explorer = f"https://suiscan.xyz/testnet/tx/{digest}"
            return True, f"✅ {amount_sui} SUI sent • {explorer}"
        else:
            return False, f"❌ TX failed: {tx_result.result_string}"
    except Exception as e:
        return False, f"❌ TX error: {str(e)[:100]}"

last_id = get_last_id()

print("🤖 SUPER LIGHT Bot running... (checks every 3 min)")

while True:
    try:
        if not BOT_USER_ID:
            time.sleep(180)
            continue

        response = client.get_users_mentions(
            id=BOT_USER_ID,
            max_results=5,
            tweet_fields=["author_id"],
            expansions=["author_id"],
            user_fields=["username"],
            user_auth=True
        )

        if response and response.data:
            # Safe username lookup
            user_dict = {}
            if hasattr(response, 'includes') and response.includes is not None:
                includes = response.includes
                if isinstance(includes, dict):
                    users = includes.get('users', [])
                else:
                    users = getattr(includes, 'users', [])
                for user in users:
                    if isinstance(user, dict):
                        uid = user.get('id')
                        uname = user.get('username')
                    else:
                        uid = getattr(user, 'id', None)
                        uname = getattr(user, 'username', None)
                    if uid and uname:
                        user_dict[uid] = uname

            for tweet in reversed(response.data):
                tid = tweet.id
                if tid <= last_id:
                    continue

                text = tweet.text.lower()
                author_id = tweet.author_id
                tipper_handle = user_dict.get(author_id, "unknown")

                # === TIP LOGIC (X-COMPLIANT - NO @recipient in reply) ===
                match = re.search(r'@(\w+)\s*\+?(\d+\.?\d*)\s*sui?', text)
                if match:
                    recipient_handle = match.group(1)
                    try:
                        amount = float(match.group(2))
                    except:
                        amount = 0

                    if amount > 0:
                        recipient_sui = get_user_address(recipient_handle)
                        if not recipient_sui:
                            reply = f"@{recipient_handle} needs to register first! Reply: register 0x..."
                        else:
                            success, tx_msg = send_sui_tip(recipient_sui, amount)
                            # FIXED: No @mention in reply → this is what X Staff wants
                            reply = f"🎁🎉 {amount} SUI tipped successfully! #GetASuiet 🍭 {tx_msg}" if success else f"❌ Tip failed: {tx_msg}"

                        try:
                            client.create_tweet(text=reply, in_reply_to_tweet_id=tid, user_auth=True)
                        except Exception as reply_err:
                            print(f"Reply failed: {reply_err}")

                # === REGISTER LOGIC ===
                if "register 0x" in text:
                    addr_match = re.search(r"0x[a-f0-9]{64}", text)
                    if addr_match:
                        addr_str = addr_match.group(0)
                        msg = "✅ Registered! 💙☔️ You can now receive tips 🍭 #GetASuiet" if register_user(tipper_handle, addr_str) else "✅ Already registered 💙 #GetASuiet"
                        try:
                            client.create_tweet(text=msg, in_reply_to_tweet_id=tid, user_auth=True)
                        except:
                            pass

                last_id = tid
                save_last_id(tid)

        time.sleep(180)

    except Exception as e:
        print(f"Loop error: {e}")
        time.sleep(180)