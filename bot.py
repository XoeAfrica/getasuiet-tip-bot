import os
import time
import sqlite3
import re
import tweepy
from pysui import SuiConfig, SyncClient
from pysui.sui.sui_txn import SuiTransaction

print("Starting GetASUiet Tip Bot - Improved Testnet with Real 3% Fee... 💙☔️")

# === CONFIG FROM RAILWAY ===
X_CONSUMER_KEY = os.getenv("X_CONSUMER_KEY")
X_CONSUMER_SECRET = os.getenv("X_CONSUMER_SECRET")
X_ACCESS_TOKEN = os.getenv("X_ACCESS_TOKEN")
X_ACCESS_TOKEN_SECRET = os.getenv("X_ACCESS_TOKEN_SECRET")
SUI_PRV_KEY = os.getenv("SUI_PRV_KEY")

# Testnet RPC (reliable public endpoint)
RPC_URL = os.getenv("RPC_URL", "https://sui-testnet-rpc.publicnode.com")

# Your 3% fee wallet
FEE_WALLET = "0xde50c83d6106453585b114bc7854cdfda46661a85b31ad875233938fa8c5f5d1"

# Connect to X (Twitter)
client = tweepy.Client(
    consumer_key=X_CONSUMER_KEY,
    consumer_secret=X_CONSUMER_SECRET,
    access_token=X_ACCESS_TOKEN,
    access_token_secret=X_ACCESS_TOKEN_SECRET
)

# Auth test + test tweet
try:
    me = client.get_me()
    print(f"✅ Authenticated as @{me.data.username} (ID: {me.data.id})")
    BOT_USER_ID = me.data.id

    test_tweet = client.create_tweet(text="🤖 GetASUiet Tip Bot IMPROVED - Real 3% fee transfers on TESTNET! 💙☔️🍭 #GetASuiet")
    tweet_id = getattr(getattr(test_tweet, 'data', None), 'id', 'unknown')
    print(f"✅ Test tweet posted! ID: {tweet_id}")
except Exception as e:
    print(f"❌ Auth/test tweet failed: {e}")
    BOT_USER_ID = None

# Connect to Sui
cfg = SuiConfig.user_config(rpc_url=RPC_URL, prv_keys=[SUI_PRV_KEY])
sui_client = SyncClient(cfg)
BOT_SUI_ADDRESS = str(cfg.active_address)
print(f"🚀 Bot Sui address: {BOT_SUI_ADDRESS} (Testnet)")

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
    except sqlite3.IntegrityError:
        return False  # Already registered
    except Exception as e:
        print(f"Register error: {e}")
        return False

def get_user_address(x_handle):
    c.execute("SELECT sui_address FROM users WHERE x_handle=?", (x_handle.lower(),))
    row = c.fetchone()
    return row[0] if row else None

# Main loop
last_id = get_last_id()

while True:
    try:
        print("🔄 Checking mentions...")
        if BOT_USER_ID:
            response = client.get_users_mentions(id=BOT_USER_ID, max_results=10)

        if response and response.data:
            for tweet in reversed(response.data):
                tid = tweet.id
                if tid <= last_id:
                    continue

                text = tweet.text.lower()

                try:
                    user_resp = client.get_user(tweet.author_id)
                    tipper_handle = user_resp.data.username
                except:
                    tipper_handle = "unknown"

                # === REAL TIP LOGIC WITH 3% FEE ===
                match = re.search(r'@(\w+)\s*\+?(\d+\.?\d*)\s*sui?', text)
                if match:
                    recipient_handle = match.group(1)
                    try:
                        amount = float(match.group(2))
                    except ValueError:
                        amount = 0

                    if amount > 0:
                        fee = amount * 0.03
                        to_send = amount - fee

                        tipper_addr = get_user_address(tipper_handle)
                        recipient_addr = get_user_address(recipient_handle)

                        success = False
                        error_msg = ""

                        if not tipper_addr:
                            error_msg = "Tipper not registered. Use 'register 0x...' first."
                        elif not recipient_addr:
                            error_msg = f"@{recipient_handle} not registered. They must register first."
                        else:
                            try:
                                # Build transaction
                                txer = SuiTransaction(sui_client)

                                # Convert to MIST (1 SUI = 1_000_000_000 MIST)
                                amount_mist = int(amount * 1_000_000_000)
                                fee_mist = int(fee * 1_000_000_000)
                                to_send_mist = amount_mist - fee_mist

                                # Split gas coin into two parts (97% + 3%)
                                split_coins = txer.split_coin(
                                    coin=txer.gas,
                                    amounts=[to_send_mist, fee_mist]
                                )

                                # Transfer 97% to recipient
                                txer.transfer_objects(
                                    transfers=[split_coins[0]],
                                    recipient=recipient_addr
                                )

                                # Transfer 3% fee to your wallet
                                txer.transfer_objects(
                                    transfers=[split_coins[1]],
                                    recipient=FEE_WALLET
                                )

                                # Execute with explicit gas budget for stability
                                result = txer.execute(gas_budget="5000000")  # ~0.005 SUI gas budget

                                if result.is_ok():
                                    success = True
                                    print(f"✅ SUCCESS: {to_send:.4f} SUI to @{recipient_handle} | {fee:.4f} SUI fee to your wallet | Tx: {result.result_data}")
                                else:
                                    error_msg = result.result_string or "Transaction failed"
                                    print(f"❌ Tx failed: {error_msg}")
                            except Exception as tx_err:
                                error_msg = str(tx_err)[:150]
                                print(f"❌ Transaction exception: {error_msg}")

                        # Always post reply
                        fee_note = " (3% maintenance fee applied)"
                        if error_msg:
                            fee_note += f" [Note: {error_msg}]"

                        reply = f"🎁🎉{amount}SUI tipped to @{recipient_handle}{fee_note} #GetASuiet🍭. Thank you for tipping."

                        try:
                            client.create_tweet(text=reply, in_reply_to_tweet_id=tid)
                            print(f"✅ Reply posted for {amount} SUI tip")
                        except Exception as reply_err:
                            print(f"Could not post reply: {reply_err}")

                # Register logic
                if "register 0x" in text:
                    addr_match = re.search(r"0x[a-f0-9]{64}", text)  # More precise
                    if addr_match:
                        addr_str = addr_match.group(0)
                        if register_user(tipper_handle, addr_str):
                            reply = "✅ Registered successfully! 💙☔️ You can now receive tips. 🍭 #GetASuiet"
                        else:
                            reply = "✅ Already registered 💙 #GetASuiet"
                        try:
                            client.create_tweet(text=reply, in_reply_to_tweet_id=tid)
                        except:
                            pass

                # Balance command (shows registered address)
                if "balance" in text:
                    addr = get_user_address(tipper_handle)
                    reply = f"💙 Registered address: {addr if addr else 'Not registered yet'} ☔️🍭 #GetASuiet"
                    try:
                        client.create_tweet(text=reply, in_reply_to_tweet_id=tid)
                    except:
                        pass

                last_id = tid
                save_last_id(tid)

        time.sleep(15)
    except Exception as e:
        print(f"Main loop error: {e}")
        time.sleep(15)
