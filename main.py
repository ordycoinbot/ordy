# main.py — ORDY Telegram Bot (Railway / Polling)

import telebot
from telebot import types
from config import TOKEN, JOIN_REWARD, REF_REWARD, TWITTER_HANDLE
from db import get_conn

print("🔧 ORDY bot is starting...")

# ========== BOT ==========
bot = telebot.TeleBot(TOKEN)

TG_GROUP_INVITE_URL = "https://t.me/OrdinaryGetORDY"
X_FOLLOW_URL = f"https://x.com/{TWITTER_HANDLE}"

# ========== DB HELPERS ==========
def create_user_if_not_exists(user_id, username, ref_id=None):
    conn = get_conn()
    with conn.cursor() as cur:
        cur.execute(
            """
            INSERT IGNORE INTO ordy_users (user_id, username, ref_id)
            VALUES (%s, %s, %s)
            """,
            (user_id, username or "", ref_id)
        )
    conn.close()

def set_wallet(user_id, wallet):
    conn = get_conn()
    with conn.cursor() as cur:
        cur.execute(
            "UPDATE ordy_users SET wallet=%s WHERE user_id=%s",
            (wallet, user_id)
        )
    conn.close()

def is_wallet_used(wallet):
    conn = get_conn()
    with conn.cursor() as cur:
        cur.execute(
            "SELECT user_id FROM ordy_users WHERE wallet=%s",
            (wallet,)
        )
        row = cur.fetchone()
    conn.close()
    return row is not None

def count_referrals(user_id):
    conn = get_conn()
    with conn.cursor() as cur:
        cur.execute(
            "SELECT COUNT(*) FROM ordy_users WHERE ref_id=%s",
            (user_id,)
        )
        count = cur.fetchone()[0]
    conn.close()
    return count

# ========== UI ==========
def main_keyboard():
    kb = types.InlineKeyboardMarkup(row_width=2)
    kb.add(types.InlineKeyboardButton("💼 Connect Wallet", callback_data="connect_wallet"))
    kb.add(
        types.InlineKeyboardButton("📢 Join Telegram Group", url=TG_GROUP_INVITE_URL),
        types.InlineKeyboardButton("🐦 Follow on X", url=X_FOLLOW_URL),
    )
    kb.add(types.InlineKeyboardButton("📊 My Status", callback_data="status"))
    return kb

# ========== COMMANDS ==========
@bot.message_handler(commands=["start"])
def start_cmd(message):
    user_id = message.from_user.id
    username = message.from_user.username or ""

    args = message.text.split()
    ref_id = None
    if len(args) > 1 and args[1].isdigit():
        rid = int(args[1])
        if rid != user_id:
            ref_id = rid

    create_user_if_not_exists(user_id, username, ref_id)

    bot.send_message(
        message.chat.id,
        "🚀 *Welcome to the ORDY Airdrop!*\n\n"
        "Complete the tasks and connect your wallet.",
        parse_mode="Markdown",
        reply_markup=main_keyboard()
    )

# ========== CALLBACKS ==========
@bot.callback_query_handler(func=lambda c: True)
def callbacks(call):
    user_id = call.from_user.id
    bot.answer_callback_query(call.id)

    if call.data == "connect_wallet":
        msg = bot.send_message(call.message.chat.id, "Send your TON wallet address:")
        bot.register_next_step_handler(msg, save_wallet)

    elif call.data == "status":
        refs = count_referrals(user_id)
        total = JOIN_REWARD + refs * REF_REWARD
        bot.send_message(
            call.message.chat.id,
            f"📊 *Your Status*\n\n"
            f"👥 Referrals: {refs}\n"
            f"💰 Earned: {total} $ORDY",
            parse_mode="Markdown"
        )

# ========== WALLET ==========
def save_wallet(message):
    addr = message.text.strip()

    if not addr.startswith(("EQ", "UQ")):
        bot.send_message(message.chat.id, "❌ Invalid TON wallet address.")
        return

    if is_wallet_used(addr):
        bot.send_message(message.chat.id, "🚫 This wallet is already used.")
        return

    set_wallet(message.from_user.id, addr)
    bot.send_message(message.chat.id, "✅ Wallet connected successfully!")

# ========== START ==========
if __name__ == "__main__":
    print("🚀 ORDY Bot running (Railway polling)")
    bot.delete_webhook(drop_pending_updates=True)
    bot.infinity_polling(timeout=60, long_polling_timeout=60)




