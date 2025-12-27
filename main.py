print("🔧 ORDY bot is starting...")

import telebot
from telebot import types
import pymysql
from config import TOKEN, db_config

# Inicijalizacija bota i onemogućavanje webhook-a
bot = telebot.TeleBot(TOKEN)
bot.delete_webhook()

GROUP_CHAT_ID   = -1
TWITTER_HANDLE  = ""
AIRDROP_TOTAL   = 250_000_000  # Ukupno tokena za airdrop

def connect_db():
    try:
        db = pymysql.connect(
            host=db_config['host'],
            user=db_config['user'],
            password=db_config['password'],
            database=db_config['database']
        )
        print("✅ Connected to database")
        return db
    except Exception as e:
        print("❌ Database connection failed:", e)
        raise

def send_main_menu(chat_id):
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add("💼 Submit Wallet", "📊 Status")
    markup.add("🎁 Claim", "👥 My Referral Link")
    markup.add("📉 Airdrop Status", "📋 Leaderboard")
    menu_text = (
        "👇 Choose an option:\n\n"
        "🔔 Sponzor: XYZ Finance – 10% popusta uz kod *ORDYXYZ*\n"
        "https://xyz-finance.link"
    )
    bot.send_message(chat_id, menu_text, parse_mode="Markdown", reply_markup=markup)

########################################
#               /start
########################################
@bot.message_handler(commands=['start'])
def start_handler(message):
    user_id = message.from_user.id
    args    = message.text.split()
    ref_id  = int(args[1]) if len(args) > 1 and args[1].isdigit() and int(args[1]) != user_id else None

    # 1) Prikaz reklame/sponzorskog oglasa
    sponsor_name = "XYZ Finance"
    sponsor_url  = "https://xyz-finance.link"
    promo_text = (
        f"🔔 Sponzor: *{sponsor_name}*\n"
        f"Dobij 10% popusta uz kod *ORDYXYZ*:\n"
        f"{sponsor_url}\n\n"
        "Klikni „Nastavi” da bi ti prikazali dalje zadatke."
    )
    promo_markup = types.InlineKeyboardMarkup()
    promo_markup.add(
        types.InlineKeyboardButton("✅ Nastavi", callback_data=f"show_join:{ref_id or 0}")
    )

    bot.send_message(
        user_id,
        promo_text,
        parse_mode="Markdown",
        reply_markup=promo_markup
    )

########################################
#    Callback nakon reklame (show_join)
########################################
@bot.callback_query_handler(func=lambda call: call.data.startswith("show_join"))
def show_join(call):
    user_id, ref = call.from_user.id, call.data.split(":")[1]
    ref_id = int(ref) if ref.isdigit() and int(ref) != user_id else None

    # 2) Inline tastatura za X, Join Group i I’ve Done It
    markup = types.InlineKeyboardMarkup()
    markup.add(
        types.InlineKeyboardButton("🐦 Follow on X", url=f"https://x.com/{TWITTER_HANDLE}"),
        types.InlineKeyboardButton("👥 Join Telegram Group", url="https://t.me/+NlYlKcwMZHo0OWFk")
    )
    markup.add(types.InlineKeyboardButton("✅ I’ve Done It", callback_data=f"check_tasks:{ref_id or 0}"))

    bot.edit_message_text(
        chat_id=user_id,
        message_id=call.message.message_id,
        text=(
            "👋 Hvala što ste pogledali našu ponudu!\n\n"
            "Sada, molimo vas da uradite sledeće zadatke:"
        ),
        reply_markup=markup
    )

########################################
#      Callback: verify Telegram grupa
########################################
@bot.callback_query_handler(func=lambda call: call.data.startswith("check_tasks"))
def check_tasks(call):
    user_id, ref = call.from_user.id, call.data.split(":")[1]
    ref_id = int(ref) if ref.isdigit() and int(ref) != user_id else None
    try:
        status = bot.get_chat_member(GROUP_CHAT_ID, user_id).status
        if status in ("member", "administrator", "creator"):
            register_user(user_id, call.from_user.username, ref_id)
            send_main_menu(user_id)
            bot.answer_callback_query(call.id, "✅ Tasks verified! You're in.")
        else:
            bot.answer_callback_query(call.id, "❌ Please join the Telegram group first.", show_alert=True)
    except Exception:
        bot.answer_callback_query(call.id, "❌ Couldn't verify membership. Try again.", show_alert=True)

def register_user(user_id, username, ref_id):
    db     = connect_db()
    cursor = db.cursor()
    cursor.execute("SELECT 1 FROM ordy_users WHERE user_id = %s", (user_id,))
    if not cursor.fetchone():
        cursor.execute(
            "INSERT INTO ordy_users (user_id, username, ref_id) VALUES (%s, %s, %s)",
            (user_id, username or "", ref_id)
        )
        db.commit()
    cursor.close()
    db.close()

########################################
#       Buton: My Referral Link
########################################
@bot.message_handler(func=lambda m: m.text == "👥 My Referral Link")
def ref_link(m):
    link = f"https://t.me/ORDYCoinBot?start={m.from_user.id}"
    bot.send_message(m.chat.id, f"👥 Your referral link:\n{link}\n\n🔁 Earn 500 $ORDY per invite")

########################################
#       Buton: Submit Wallet
########################################
@bot.message_handler(func=lambda m: m.text == "💼 Submit Wallet")
def ask_wallet(m):
    msg = bot.send_message(m.chat.id, "Please enter your TON wallet address:")
    bot.register_next_step_handler(msg, save_wallet)

def save_wallet(m):
    addr = m.text.strip()
    if not (addr.startswith(("EQ", "UQ")) and len(addr) == 48):
        bot.send_message(m.chat.id, "❌ Invalid TON address. Try again.")
        return
    db = connect_db()
    c  = db.cursor()
    c.execute("UPDATE ordy_users SET wallet = %s WHERE user_id = %s", (addr, m.from_user.id))
    db.commit()
    c.close()
    db.close()
    bot.send_message(m.chat.id, "✅ Wallet saved successfully!")

########################################
#       Buton: Status
########################################
@bot.message_handler(func=lambda m: m.text == "📊 Status")
def status(m):
    db = connect_db()
    c  = db.cursor()
    c.execute("SELECT COUNT(*) FROM ordy_users WHERE ref_id = %s", (m.from_user.id,))
    refs  = c.fetchone()[0]
    total = 1000 + refs * 500
    c.execute("SELECT wallet FROM ordy_users WHERE user_id = %s", (m.from_user.id,))
    wallet_data = c.fetchone()
    wallet = wallet_data[0] if wallet_data else "Not set"
    c.close()
    db.close()
    bot.send_message(
        m.chat.id,
        f"📈 You have {refs} referrals.\n"
        f"💰 Total earned: {total} $ORDY\n"
        f"🔐 Wallet: {wallet}"
    )

########################################
#       Buton: Claim
########################################
@bot.message_handler(func=lambda m: m.text == "🎁 Claim")
def claim(m):
    db = connect_db()
    c  = db.cursor()
    c.execute("SELECT COUNT(*) FROM ordy_users WHERE ref_id = %s", (m.from_user.id,))
    refs = c.fetchone()[0]
    if refs < 50:
        bot.send_message(m.chat.id, "❌ You need at least 50 referrals to claim your ORDY tokens.")
    else:
        bot.send_message(
            m.chat.id,
            "🎉 You’re eligible to claim your ORDY tokens!\n\n"
            "💰 To receive them, send *0.05 TON* to:\n"
            "`UQDiwl-14JKkqY59Y6Wge1R3fE8TQhRGed1Pt-3blg-ZZpFs`\n"
            "⚙️ Claiming will be automatic soon via smart contract.",
            parse_mode="Markdown"
        )
    c.close()
    db.close()

########################################
#   Buton: Airdrop Status
########################################
@bot.message_handler(commands=['airdrop'])
@bot.message_handler(func=lambda m: m.text == "📉 Airdrop Status")
def airdrop(m):
    db = connect_db()
    c  = db.cursor()
    c.execute("SELECT COUNT(*) FROM ordy_users")
    users = c.fetchone()[0]
    c.execute("SELECT COUNT(*) FROM ordy_users WHERE ref_id IS NOT NULL")
    refs  = c.fetchone()[0]
    dist  = users * 1000 + refs * 500
    remaining = AIRDROP_TOTAL - dist
    c.close()
    db.close()
    bot.send_message(
        m.chat.id,
        f"📉 ORDY Airdrop Status\n\n"
        f"👥 Users joined: {users}\n"
        f"💸 Distributed: {dist:,} $ORDY\n"
        f"⏳ Remaining: {remaining:,} $ORDY"
    )

########################################
#       Komanda: /users
########################################
@bot.message_handler(commands=['users'])
def users_count(message):
    db = connect_db()
    cursor = db.cursor()
    cursor.execute("SELECT COUNT(*) FROM ordy_users")
    total_users = cursor.fetchone()[0]
    cursor.close()
    db.close()
    bot.send_message(message.chat.id, f"👥 Total registered users: {total_users}")

########################################
#       Komanda: /stats (admin)
########################################
@bot.message_handler(commands=['stats'])
def stats_handler(message):
    admin_id = 123456789  # Zamenite sa stvarnim Telegram ID-jem
    if message.from_user.id != admin_id:
        bot.send_message(message.chat.id, "❌ Unauthorized.")
        return

    db = connect_db()
    cursor = db.cursor()
    cursor.execute("SELECT COUNT(*) FROM ordy_users")
    total_users = cursor.fetchone()[0]
    cursor.execute("SELECT COUNT(*) FROM ordy_users WHERE ref_id IS NOT NULL")
    total_refs = cursor.fetchone()[0]
    cursor.close()
    db.close()

    bot.send_message(
        message.chat.id,
        f"📊 Admin Stats:\n\n"
        f"👥 Total users: {total_users}\n"
        f"🔗 Total referrals: {total_refs}"
    )

########################################
#       Komanda: /leaderboard  i dugme
########################################
@bot.message_handler(commands=['leaderboard'])
@bot.message_handler(func=lambda m: m.text == "📋 Leaderboard")
def leaderboard_handler(message):
    db = connect_db()
    cursor = db.cursor()

    cursor.execute("""
        SELECT ref_id, COUNT(*) AS cnt 
        FROM ordy_users 
        WHERE ref_id IS NOT NULL 
        GROUP BY ref_id 
        ORDER BY cnt DESC 
        LIMIT 5
    """)
    top_refs = cursor.fetchall()

    if not top_refs:
        bot.send_message(message.chat.id, "📋 Leaderboard is empty. No referrals yet.")
        cursor.close()
        db.close()
        return

    msg = "🏆 ORDY Airdrop Leaderboard 🏆\n\n"
    rank = 1
    for (user_id, cnt) in top_refs:
        total_earned = 1000 + cnt * 500
        cursor.execute("SELECT username FROM ordy_users WHERE user_id = %s", (user_id,))
        row = cursor.fetchone()
        username = row[0] if row and row[0] else f"user_{user_id}"
        msg += f"{rank}. {username} — {cnt} referrals — {total_earned} $ORDY\n"
        rank += 1

    cursor.close()
    db.close()
    bot.send_message(message.chat.id, msg)

########################################
#         Komanda: /help
########################################
@bot.message_handler(commands=['help'])
def help_handler(message):
    text = (
        "ℹ ORDY Bot Commands:\n\n"
        "1. /start – pokreće registraciju i prikazuje zadatke (X + Telegram grupa), uz kratku reklamu.\n"
        "2. 📊 Status – prikazuje koliko imate referala i total earned ORDY + vaša wallet adresa.\n"
        "3. 💼 Submit Wallet – unesite vašu TON adresu (EQ*/UQ*).\n"
        "4. 🎁 Claim – zatražite ORDY kada imate ≥50 referala; dobićete instrukcije.\n"
        "5. 👥 My Referral Link – dobijaš link za deljenje i 500 $ORDY po referral-u.\n"
        "6. 📉 Airdrop Status ili /airdrop – prikazuje ukupan broj korisnika, podeljeno ORDY i preostalo.\n"
        "7. /users – prikazuje ukupan broj registrovanih korisnika.\n"
        "8. /stats – (samo za admin) prikazuje total users i total referrals.\n"
        "9. 📋 Leaderboard ili /leaderboard – top 5 po broju referala i ORDY zarađenih.\n\n"
        "🔗 Get started: pošaljite /start i pratite uputstva!"
    )
    bot.send_message(message.chat.id, text)

print("🚀 Bot polling started")
try:
    bot.infinity_polling(timeout=60, long_polling_timeout=20)
except Exception as e:
    print("❌ Polling failed:", e)

