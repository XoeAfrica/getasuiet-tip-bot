import os
import time
import sqlite3
import re
import tweepy
from pysui import SuiConfig, SyncClient, handle_result
from pysui.sui.sui_txn import SyncTransaction

print("🚀 Starting GetASUiet Tip Bot - Full Version with 3% Fee... 💙☔️")

# === CONFIG ===
X_CONSUMER_KEY = os.getenv("X_CONSUMER_KEY")
X_CONSUMER_SECRET = os.getenv("X_CONSUMER_SECRET")
X_ACCESS_TOKEN = os.getenv("X_ACCESS_TOKEN")
X_ACCESS_TOKEN_SECRET = os.getenv("X_ACCESS_TOKEN_SECRET")
SUI_PRV_KEY = os.getenv("SUI_PRV_KEY")

RPC_URL = os.getenv("RPC_URL", "https://sui-testnet-rpc.publicnode.com")

# Tweepy client (OAuth 1.0a User Context)
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
    print(f"❌ X Auth failed: {e}")
    BOT_USER_ID = None
    exit(1)

# Sui setup
cfg = SuiConfig.user_config(rpc_url=RPC_URL, prv_keys=[SUI_PRV_KEY])
sui_client = SyncClient(cfg)
BOT_SUI_ADDRESS = str(cfg.active_address)
print(f"🚀 Bot Sui address: {BOT_SUI_ADDRESS} (Testnet)")

print("🤖 GetASUiet Tip Bot FULL VERSION is running! 💙☔️🪙🍭")

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
        return False  # already registered

def get_user_address(x_handle):
    c.execute("SELECT sui_address FROM users WHERE x_handle=?", (x_handle.lower(),))
    row = c.fetchone()
    return row[0] if row else None

# === SUI TIP FUNCTION (3% fee) ===
def send_sui_tip(recipient_address: str, amount_sui: float) -> tuple[bool, str]:
    """Returns (success: bool, message_or_explorer_link: str)"""
    try:
        amount_mist = int(amount_sui * 1_000_000_000)
        fee_mist = int(amount_mist * 0.03)
        net_mist = amount_mist - fee_mist

        if net_mist < 1_000_000:  # ~0.001 SUI minimum
            return False, "Amount too small after 3% fee"

        # Build transaction
        tx = SyncTransaction(client=sui_client)
        split_coin = tx.split_coin(coin=tx.gas, amounts=[net_mist])
        tx.transfer_objects(transfers=[split_coin], recipient=recipient_address)

        # Execute
        tx_result = tx.execute(gas_budget="5000000")

        if tx_result.is_ok():
            digest = tx_result.result_data.digest if hasattr(tx_result.result_data, "digest") else str(tx_result)
            explorer = f"https://suiscan.xyz/testnet/tx/{digest}"
            return True, f"✅ Sent {amount_sui} SUI (3% fee kept by bot) • {explorer}"
        else:
            return False, f"❌ Transaction failed: {tx_result.result_string}"
    except Exception as e:
        return False, f"❌ TX error: {str(e)[:120]}"

last_id = get_last_id()

while True:
    try:
        print("🔄 Checking mentions...")
        if not BOT_USER_ID:
            time.sleep(45)
            continue

        response = client.get_users_mentions(
            id=BOT_USER_ID,
            max_results=10,
            tweet_fields=["author_id"],      # ← CRITICAL FIX
            user_auth=True
        )

        if response and hasattr(response, 'data') and response.data:
            for tweet in reversed(response.data):  # oldest first
                tid = tweet.id
                if tid <= last_id:
                    continue

                text = tweet.text.lower()
                author_id = tweet.author_id

                # Get tipper username
                try:
                    user_resp = client.get_user(id=author_id, user_auth=True)
                    tipper_handle = user_resp.data.username
                except Exception as user_err:
                    print(f"⚠️ Could not get user info for {author_id}: {user_err}")
                    tipper_handle = "unknown"

                print(f"📨 Processing mention from @{tipper_handle} (ID: {tid})")

                # === TIP LOGIC ===
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
                            reply = f"@{recipient_handle} needs to register first! Reply with: register 0x..."
                        else:
                            success, tx_msg = send_sui_tip(recipient_sui, amount)
                            if success:
                                reply = f"🎁🎉 @{recipient_handle} +{amount} SUI #GetASuiet 🍭 {tx_msg}"
                            else:
                                reply = f"❌ @{recipient_handle} Tip failed: {tx_msg}"

                        # Post reply
                        try:
                            client.create_tweet(
                                text=reply,
                                in_reply_to_tweet_id=tid,
                                user_auth=True
                            )
                            print(f"✅ Replied & processed tip to @{recipient_handle}")
                        except Exception as reply_err:
                            print(f"❌ Reply failed: {reply_err}")

                # === REGISTER LOGIC ===
                if "register 0x" in text:
                    addr_match = re.search(r"0x[a-f0-9]{64}", text)
                    if addr_match:
                        addr_str = addr_match.group(0)
                        success = register_user(tipper_handle, addr_str)
                        msg = "✅ Registered successfully! 💙☔️ You can now receive tips 🍭 #GetASuiet" if success else "✅ Already registered 💙 #GetASuiet"
                        try:
                            client.create_tweet(
                                text=msg,
                                in_reply_to_tweet_id=tid,
                                user_auth=True
                            )
                        except:
                            pass

                # Update last processed
                last_id = tid
                save_last_id(tid)

        time.sleep(45)

    except Exception as e:
        print(f"Main loop error: {e}")
        time.sleep(45)