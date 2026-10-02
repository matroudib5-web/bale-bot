import os
import sqlite3
import threading
from http.server import HTTPServer, BaseHTTPRequestHandler
from datetime import datetime

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup, KeyboardButton
from telegram.ext import Application, CommandHandler, MessageHandler, ContextTypes, filters

# =========================
# تنظیمات
# =========================

BALE_TOKEN = "152004939:gjvarQqggvlUKNXdDBoJPx-mTNcNGPBu0k8"

CHANNELS = [
    "@ghghgdrh",
    "@Hitlerss1"
]

CHANNEL_NAMES = [
    "عضویت در کانال اول",
    "عضویت در کانال دوم"
]

REQUIRED_SUBS = 10
SUPPORT_ID = "@KSBR8371250"

DB_NAME = "bot.db"


# =========================
# وب‌سرور Render
# =========================

class Handler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b"Bot is running!")
    def log_message(self, format, *args):
        pass


def run_server():
    port = int(os.environ.get("PORT", 10000))
    HTTPServer(("0.0.0.0", port), Handler).serve_forever()


# =========================
# دیتابیس
# =========================

conn = sqlite3.connect(DB_NAME, check_same_thread=False)
cursor = conn.cursor()

cursor.execute("""
CREATE TABLE IF NOT EXISTS users (
    user_id INTEGER PRIMARY KEY,
    username TEXT,
    first_name TEXT,
    invited_by INTEGER DEFAULT NULL,
    joined_at TEXT
)
""")
conn.commit()


def create_user(user_id, username, first_name, invited_by=None):
    cursor.execute(
        "INSERT OR IGNORE INTO users (user_id, username, first_name, invited_by, joined_at) VALUES (?, ?, ?, ?, ?)",
        (user_id, username, first_name, invited_by, datetime.now().isoformat())
    )
    conn.commit()


def count_invites(user_id):
    cursor.execute("SELECT COUNT(*) FROM users WHERE invited_by = ?", (user_id,))
    return cursor.fetchone()[0]


# =========================
# چک عضویت
# =========================

async def check_membership(context, user_id):
    for channel in CHANNELS:
        try:
            member = await context.bot.get_chat_member(chat_id=channel, user_id=user_id)
            if member.status in ["left", "kicked"]:
                return False
        except Exception as e:
            print(f"Error checking {channel}: {e}")
            return False
    return True


# =========================
# کیبوردها
# =========================

def get_join_keyboard():
    keyboard = []
    for i, ch in enumerate(CHANNELS):
        keyboard.append([InlineKeyboardButton(CHANNEL_NAMES[i], url=f"https://ble.ir/{ch.replace('@','')}")])
    return InlineKeyboardMarkup(keyboard)


def get_main_keyboard():
    keyboard = [
        [KeyboardButton("زیرمجموعه هام👨‍👩‍👧‍👦")],
        [KeyboardButton("دریافت جایزه💳💸💰💵")]
    ]
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True)


def get_start_keyboard():
    keyboard = [
        [KeyboardButton("عضو شدم✅")]
    ]
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True)


# =========================
# /start
# =========================

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.message.from_user
    user_id = user.id
    username = user.username or ""
    first_name = user.first_name or ""

    invited_by = None
    if context.args and len(context.args) > 0:
        try:
            invited_by = int(context.args[0])
        except:
            pass

    create_user(user_id, username, first_name, invited_by)

    is_member = await check_membership(context, user_id)

    if not is_member:
        await update.message.reply_text(
            "سلام! 👋\n\n"
            "برای استفاده از ربات، ابتدا در کانال‌های زیر عضو شوید:\n\n"
            "👇 روی دکمه‌های زیر بزنید و عضو شوید.\n\n"
            "بعد از عضویت، دکمه‌ی «عضو شدم✅» رو بزنید.",
            reply_markup=get_join_keyboard()
        )
        await update.message.reply_text(
            "👇",
            reply_markup=get_start_keyboard()
        )
        return

    bot_username = (await context.bot.get_me()).username
    invite_link = f"https://ble.ir/{bot_username}?start={user_id}"

    await update.message.reply_text(
        f"✅ عضویت شما تایید شد!\n\n"
        f"🔗 لینک زیرمجموعه‌گیری شما:\n{invite_link}\n\n"
        f"📌 هرکس با لینک شما وارد ربات شود و عضو کانال‌ها شود، به عنوان زیرمجموعه ثبت می‌شود.\n\n"
        f"🎁 با ۱۰ زیرمجموعه، ۳۰ هزار تومان برنده شوید!",
        reply_markup=get_main_keyboard()
    )


# =========================
# هندلر پیام‌ها
# =========================

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message or not update.message.text:
        return

    text = update.message.text.strip()
    user = update.message.from_user
    user_id = user.id

    # عضو شدم
    if text == "عضو شدم✅":
        is_member = await check_membership(context, user_id)
        if is_member:
            bot_username = (await context.bot.get_me()).username
            invite_link = f"https://ble.ir/{bot_username}?start={user_id}"
            await update.message.reply_text(
                f"✅ عضویت شما تایید شد!\n\n"
                f"🔗 لینک زیرمجموعه‌گیری شما:\n{invite_link}\n\n"
                f"📌 هرکس با لینک شما وارد ربات شود و عضو کانال‌ها شود، به عنوان زیرمجموعه ثبت می‌شود.\n\n"
                f"🎁 با ۱۰ زیرمجموعه، ۳۰ هزار تومان برنده شوید!",
                reply_markup=get_main_keyboard()
            )
        else:
            await update.message.reply_text(
                "❌ شما هنوز عضو نشده‌اید.\n\n"
                "لطفاً ابتدا در کانال‌ها عضو شوید و بعد دکمه‌ی «عضو شدم✅» رو بزنید.",
                reply_markup=get_join_keyboard()
            )
            await update.message.reply_text(
                "👇",
                reply_markup=get_start_keyboard()
            )
        return

    # زیرمجموعه هام
    if text == "زیرمجموعه هام👨‍👩‍👧‍👦":
        count = count_invites(user_id)
        bot_username = (await context.bot.get_me()).username
        invite_link = f"https://ble.ir/{bot_username}?start={user_id}"

        await update.message.reply_text(
            f"👥 زیرمجموعه‌های شما:\n\n"
            f"{count}/{REQUIRED_SUBS}\n\n"
            f"🔗 لینک زیرمجموعه‌گیری شما:\n{invite_link}",
            reply_markup=get_main_keyboard()
        )
        return

    # دریافت جایزه
    if text == "دریافت جایزه💳💸💰💵":
        count = count_invites(user_id)
        if count >= REQUIRED_SUBS:
            await update.message.reply_text(
                f"🎉 تبریک! شما به {REQUIRED_SUBS} زیرمجموعه رسیدید!\n\n"
                f"برای دریافت جایزه، به {SUPPORT_ID} پیام دهید.",
                reply_markup=get_main_keyboard()
            )
        else:
            bot_username = (await context.bot.get_me()).username
            invite_link = f"https://ble.ir/{bot_username}?start={user_id}"
            await update.message.reply_text(
                f"❌ هنوز زیرمجموعه‌های شما کامل نشده.\n\n"
                f"تعداد فعلی: {count}/{REQUIRED_SUBS}\n\n"
                f"🔗 لینک زیرمجموعه‌گیری شما:\n{invite_link}",
                reply_markup=get_main_keyboard()
            )
        return


# =========================
# اجرا
# =========================

def main():
    threading.Thread(target=run_server, daemon=True).start()

    app = Application.builder().token(BALE_TOKEN).base_url("https://tapi.bale.ai/bot").build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    print("Referral Bot started...")
    app.run_polling()


if __name__ == "__main__":
    main()
