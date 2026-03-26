import os
import time
from pysui import SuiConfig, SyncClient

print("Starting GetASUiet Tip Bot (minimal mode)... 💙☔️")

SUI_PRV_KEY = os.getenv("SUI_PRV_KEY")
RPC_URL = os.getenv("RPC_URL", "https://sui-testnet-rpc.publicnode.com")

# Connect to Sui
cfg = SuiConfig.user_config(rpc_url=RPC_URL, prv_keys=[SUI_PRV_KEY])
BOT_SUI_ADDRESS = str(cfg.active_address)
print(f"🚀 Bot Sui address: {BOT_SUI_ADDRESS}")

print("🤖 GetASUiet Tip Bot is running in minimal mode! 💙☔️🪙💚🍭")
print("X replies are disabled until permissions are fixed.")

# Keep the container alive
while True:
    print("Bot is alive and waiting... 💙")
    time.sleep(60)
