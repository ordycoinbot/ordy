# main.py — ORDY Telegram Bot (RAILWAY POLLING VERSION)

import telebot
from telebot import types
from config import TOKEN, JOIN_REWARD, REF_REWARD, TWITTER_HANDLE
from db import get_conn

# ========== BOT ==========
bot = telebot.TeleBot(TOKEN)

# ========== CONFIG ==========
TG_GROUP_INVITE_URL = "https://t.me/OrdinaryGetORDY"
X_FOLLOW_URL = f"https://x.com/{TWITTER_HANDLE}"
DAO_URL = "https://getordinary.website/dao.html"
FOUNDING_MEMBER_LIMIT = 5000

# ========== DB HELPERS ==========
def get_user(telegram_id):
    conn = get_conn()
    with conn.cursor() as cur:
        cur.execute("SELECT * FROM users WHERE telegram_id=%s", (telegram_id,))
        row = cur.fetchone()
    conn.close()
    return row

def create_user_if_not_exists(telegram_id, username, referred_by=None):
    conn = get_conn()
    with conn.cursor() as cur:
        cur.execute(
            """
            INSERT IGNORE INTO users (telegram_id, username, referred_by)
            VALUES (%s,%s,%s)
            """,
            (telegram_id, username, referred_by)
        )
    conn.close()

def set_wallet(telegram_id, wallet):
    conn = get_conn()
    with conn.cursor() as cur:
        cur.execute(
            """
            UPDATE users
            SET wallet=%s, wallet_verified=1
            WHERE telegram_id=%s
            """,
            (wallet, telegram_id)
        )
    conn.close()

def is_wallet_used(wallet):
    conn = get_conn()
    with conn.cursor() as cur:
        cur.execute(
            "SELECT telegram_id FROM users WHERE wallet=%s",
            (wallet,)
        )
        row = cur.fetchone()
    conn.close()
    return row is not None

# ========== UI ==========
def main_keyboard():
    kb = types.InlineKeyboardMarkup(row_width=2)

    kb.add(types.InlineKeyboardButton("💼 Connect Wallet", callback_data="connect_wallet"))
    kb.add(
        types.InlineKeyboardButton("📢 Join Telegram Group", url=TG_GROUP_INVITE_URL),
        types.InlineKeyboardButton("🐦 Follow on X", url=X_FOLLOW_URL),
    )
    kb.add(
        types.InlineKeyboardButton("🎯 Check Progress", callback_data="check_status"),
        types.InlineKeyboardButton("📊 Dashboard", callback_data="dashboard"),
    )
    kb.add(
        types.InlineKeyboardButton("🎁 Claim ORDY", callback_data="claim"),
        types.InlineKeyboardButton("🏛️ ORDY DAO", url=DAO_URL),
    )
    return kb

# ========== COMMANDS ==========
@bot.message_handler(commands=["start"])
def start_cmd(message):
    user_id = message.from_user.id
    username = message.from_user.username or ""

    create_user_if_not_exists(user_id, username)

    bot.send_message(
        message.chat.id,
        "🚀 *Welcome to the ORDY Airdrop!*\n\nConnect your wallet to get started.",
        parse_mode="Markdown",
        reply_markup=main_keyboard()
    )

# ========== CALLBACKS ==========
@bot.callback_query_handler(func=lambda c: True)
def callbacks(call):
    user_id = call.from_user.id
    username = call.from_user.username or ""

    create_user_if_not_exists(user_id, username)
    bot.answer_callback_query(call.id)

    if call.data == "connect_wallet":
        msg = bot.send_message(call.message.chat.id, "Send your TON wallet:")
        bot.register_next_step_handler(msg, save_wallet)

    elif call.data == "dashboard":
        bot.send_message(call.message.chat.id, "📊 Dashboard loading...")

    elif call.data == "check_status":
        bot.send_message(call.message.chat.id, "🎯 Progress OK")

    elif call.data == "claim":
        bot.send_message(call.message.chat.id, "🎁 Claim coming soon")

# ========== WALLET ==========
def save_wallet(message):
    addr = message.text.strip()

    if not addr.startswith(("EQ", "UQ")):
        bot.send_message(message.chat.id, "❌ Invalid wallet")
        return

    if is_wallet_used(addr):
        bot.send_message(message.chat.id, "🚫 Wallet already used")
        return

    set_wallet(message.from_user.id, addr)
    bot.send_message(message.chat.id, "✅ Wallet connected")

# ========== START ==========
if __name__ == "__main__":
    print("🚀 ORDY Bot starting (Railway / Polling mode)")
    bot.delete_webhook(drop_pending_updates=True)
    bot.infinity_polling(timeout=60, long_polling_timeout=60)


