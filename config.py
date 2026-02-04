# config.py — ORDY (Railway safe)

import os

# ========== TELEGRAM ==========
TOKEN = os.getenv("BOT_TOKEN")

JOIN_REWARD = int(os.getenv("JOIN_REWARD", 1000))
REF_REWARD = int(os.getenv("REF_REWARD", 500))

GROUP_CHAT_ID = int(os.getenv("GROUP_CHAT_ID", "-1001234567890"))
TWITTER_HANDLE = os.getenv("TWITTER_HANDLE", "OrdinaryGetORDY")

# ========== DATABASE ==========
DB_CONFIG = {
    "host": os.getenv("DB_HOST"),
    "user": os.getenv("DB_USER"),
    "password": os.getenv("DB_PASS"),
    "database": os.getenv("DB_NAME"),
    "charset": "utf8mb4"
}
