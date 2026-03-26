import os
import time
from pysui import SuiConfig, SyncClient

print("Starting GetASUiet Tip Bot (stable minimal mode)... 💙☔️")

SUI_PRV_KEY = os.getenv("SUI_PRV_KEY")
RPC_URL = os.getenv("RPC_URL", "https://sui-testnet-rpc.publicnode.com")

# Sui connection
cfg = SuiConfig.user_config(rpc_url=RPC_URL, prv_keys=[SUI_PRV_KEY])
BOT_SUI_ADDRESS = str(cfg.active_address)
print(f"🚀 Bot Sui address: {BOT_SUI_ADDRESS}")

print("🤖 GetASUiet Tip Bot is running in stable minimal mode! 💙☔️🪙💚🍭")
print("X replies are paused until permissions fully activate on X side.")

# Keep alive without X calls to avoid 401
while True:
    print("Bot is alive and waiting... 💙 (checking every 60s)")
    time.sleep(60)
