print("🔧 ORDY bot is starting...")

import telebot
from telebot import types
from db import get_conn
from config import TOKEN, JOIN_REWARD, REF_REWARD, TWITTER_HANDLE

# ===== BOT INIT =====
bot = telebot.TeleBot(TOKEN)
bot.delete_webhook()

TG_GROUP_INVITE_URL = "https://t.me/OrdinaryGetORDY"
X_FOLLOW_URL = f"https://x.com/{TWITTER_HANDLE}"
DAO_URL = "https://getordinary.website/dao.html"

# ===== INIT DATABASE =====
def init_db():
    conn = get_conn()
    with conn.cursor() as cur:
        cur.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id INT AUTO_INCREMENT PRIMARY KEY,
                user_id BIGINT NOT NULL UNIQUE,
                username VARCHAR(255),
                ref_id BIGINT NULL,
                wallet VARCHAR(255) NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
    conn.close()

# ===== DB HELPERS =====
def create_user_if_not_exists(user_id, username, ref_id=None):
    conn = get_conn()
    with conn.cursor() as cur:
        cur.execute(
            """
            INSERT IGNORE INTO users (user_id, username, ref_id)
            VALUES (%s,%s,%s)
            """,
            (user_id, username, ref_id)
        )
    conn.close()

def get_ref_count(user_id):
    conn = get_conn()
    with conn.cursor() as cur:
        cur.execute("SELECT COUNT(*) FROM users WHERE ref_id=%s", (user_id,))
        count = cur.fetchone()[0]
    conn.close()
    return count

def set_wallet(user_id, wallet):
    conn = get_conn()
    with conn.cursor() as cur:
        cur.execute(
            "UPDATE users SET wallet=%s WHERE user_id=%s",
            (wallet, user_id)
        )
    conn.close()

def is_wallet_used(wallet):
    conn = get_conn()
    with conn.cursor() as cur:
        cur.execute("SELECT user_id FROM users WHERE wallet=%s", (wallet,))
        row = cur.fetchone()
    conn.close()
    return row is not None

# ===== KEYBOARD =====
def main_keyboard():
    kb = types.InlineKeyboardMarkup(row_width=2)

    kb.add(types.InlineKeyboardButton("💼 Connect Wallet", callback_data="connect_wallet"))

    kb.add(
        types.InlineKeyboardButton("📢 Join Telegram Group", url=TG_GROUP_INVITE_URL),
        types.InlineKeyboardButton("🐦 Follow on X", url=X_FOLLOW_URL)
    )

    kb.add(
        types.InlineKeyboardButton("🎯 Check Progress", callback_data="check_status"),
        types.InlineKeyboardButton("📊 Dashboard", callback_data="dashboard")
    )

    kb.add(
        types.InlineKeyboardButton("🎁 Claim ORDY", callback_data="claim"),
        types.InlineKeyboardButton("🏛️ ORDY DAO", url=DAO_URL)
    )

    return kb

# ===== START COMMAND =====
@bot.message_handler(commands=["start"])
def start_cmd(message):

    user_id = message.from_user.id
    username = message.from_user.username or ""

    args = message.text.split()
    ref_id = None

    if len(args) > 1 and args[1].isdigit():
        if int(args[1]) != user_id:
            ref_id = int(args[1])

    create_user_if_not_exists(user_id, username, ref_id)

    bot.send_message(
        message.chat.id,
        "🚀 *Welcome to the ORDY Airdrop!*\n\nConnect your wallet to continue.",
        parse_mode="Markdown",
        reply_markup=main_keyboard()
    )

# ===== CALLBACK HANDLER =====
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
        refs = get_ref_count(user_id)
        total = JOIN_REWARD + refs * REF_REWARD

        bot.send_message(
            call.message.chat.id,
            f"📊 Dashboard\n\n👥 Referrals: {refs}\n💰 Earned: {total} ORDY"
        )

    elif call.data == "check_status":
        bot.send_message(call.message.chat.id, "🎯 Tasks completed ✔")

    elif call.data

RaJa (OldSeed Hunters), [5. 2. 2026. 13:08]
== "claim":
        refs = get_ref_count(user_id)

        if refs < 50:
            bot.send_message(
                call.message.chat.id,
                "❌ You need at least 50 referrals to claim."
            )
        else:
            bot.send_message(
                call.message.chat.id,
                "🎉 Claim feature coming soon!"
            )

# ===== SAVE WALLET =====
def save_wallet(message):

    wallet = message.text.strip()

    if not wallet.startswith(("EQ", "UQ")):
        bot.send_message(message.chat.id, "❌ Invalid wallet format.")
        return

    if is_wallet_used(wallet):
        bot.send_message(message.chat.id, "🚫 Wallet already used.")
        return

    set_wallet(message.from_user.id, wallet)

    bot.send_message(message.chat.id, "✅ Wallet connected!")

# ===== BOT START =====
if __name__ == "__main__":

    print("🚀 ORDY Bot running (Railway polling)")

    init_db()

    bot.infinity_polling(timeout=60, long_polling_timeout=60)
