import os
import sqlite3
import threading
from http.server import HTTPServer, BaseHTTPRequestHandler
from datetime import datetime

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, ContextTypes, filters

# =========================
# تنظیمات
# =========================

BALE_TOKEN = "152004939:gjvarQqggvlUKNXdDBoJPx-mTNcNGPBu0k8"

CHANNELS = [
    "@ghghgdrh",
    "@Hitlerss1"
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


def get_user(user_id):
    cursor.execute("SELECT * FROM users WHERE user_id = ?", (user_id,))
    return cursor.fetchone()


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
# چک کردن عضویت
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
# /start
# =========================

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.message.from_user
    user_id = user.id
    username = user.username or ""
    first_name = user.first_name or ""

    # گرفتن زیرمجموعه‌کننده از لینک استارت
    invited_by = None
    if context.args and len(context.args) > 0:
        try:
            invited_by = int(context.args[0])
        except:
            pass

    create_user(user_id, username, first_name, invited_by)

    # چک کردن عضویت
    is_member = await check_membership(context, user_id)

    if not is_member:
        keyboard = []
        for ch in CHANNELS:
            keyboard.append([InlineKeyboardButton(f"عضو شو در {ch}", url=f"https://ble.ir/{ch.replace('@','')}")])
        
        await update.message.reply_text(
            "برای استفاده از ربات، ابتدا در کانال‌های زیر عضو شوید:\n\n"
            "بعد از عضویت، بنویسید: عضو شدم✅",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
        return

    # کاربر عضو هست
    bot_username = (await context.bot.get_me()).username
    invite_link = f"https://ble.ir/{bot_username}?start={user_id}"

    await update.message.reply_text(
        f"✅ خوش آمدید {first_name}!\n\n"
        f"🔗 لینک زیرمجموعه‌گیری شما:\n{invite_link}\n\n"
        f"📌 هرکس که با لینک شما وارد بات شود و عضو کانال‌ها شود، به عنوان زیرمجموعه ثبت می‌شود.\n\n"
        f"🎁 با ۱۰ زیرمجموعه، ۳۰ هزار تومان برنده شوید.\n\n"
        f"دستورات:\n"
        f"• زیرمجموعه هام👨‍👩‍👧‍👦 → مشاهده تعداد\n"
        f"• دریافت جایزه💳💸💰💵 → دریافت جایزه"
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

    # عضویت
    if text == "عضو شدم✅":
        is_member = await check_membership(context, user_id)
        if is_member:
            bot_username = (await context.bot.get_me()).username
            invite_link = f"https://ble.ir/{bot_username}?start={user_id}"
            await update.message.reply_text(
                f"✅ عضویت شما تایید شد!\n\n"
                f"🔗 لینک زیرمجموعه‌گیری شما:\n{invite_link}\n\n"
                f"🎁 با ۱۰ زیرمجموعه، ۳۰ هزار تومان برنده شوید.\n\n"
                f"دستورات:\n"
                f"• زیرمجموعه هام👨‍👩‍👧‍👦\n"
                f"• دریافت جایزه💳💸💰💵"
            )
        else:
            await update.message.reply_text(
                "❌ شما هنوز عضو نشده‌اید.\n"
                "لطفاً ابتدا در کانال‌ها عضو شوید و دوباره بنویسید: عضو شدم✅"
            )
        return

    # نمایش زیرمجموعه‌ها
    if text == "زیرمجموعه هام👨‍👩‍👧‍👦":
        count = count_invites(user_id)
        await update.message.reply_text(
            f"👥 زیرمجموعه‌های شما:\n\n{count}/{REQUIRED_SUBS}"
        )
        return

    # دریافت جایزه
    if text == "دریافت جایزه💳💸💰💵":
        count = count_invites(user_id)
        if count >= REQUIRED_SUBS:
            await update.message.reply_text(
                f"🎉 تبریک! شما به {REQUIRED_SUBS} زیرمجموعه رسیدید.\n\n"
                f"برای دریافت جایزه، به {SUPPORT_ID} پیام دهید."
            )
        else:
            await update.message.reply_text(
                f"❌ هنوز زیرمجموعه‌های شما کامل نشده.\n"
                f"تعداد فعلی: {count}/{REQUIRED_SUBS}"
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
