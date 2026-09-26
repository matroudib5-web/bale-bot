import sqlite3
import random
import time
import os
import threading
from http.server import HTTPServer, BaseHTTPRequestHandler

from telegram import Update
from telegram.ext import (
    Application,
    MessageHandler,
    ContextTypes,
    filters
)

# =========================
# تنظیمات
# =========================

TOKEN = "152004939:gjvarQqggvlUKNXdDBoJPx-mTNcNGPBu0k8"

COOLDOWN_SECONDS = 10
MIN_POINTS = 10
MAX_POINTS = 30

DB_NAME = "nazi_bot.db"


# =========================
# وب‌سرور کوچیک برای Render
# =========================

class Handler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b"Bot is running!")

    def log_message(self, format, *args):
        pass  # لاگ‌های اضافی رو نشون نده


def run_server():
    port = int(os.environ.get("PORT", 10000))
    server = HTTPServer(("0.0.0.0", port), Handler)
    server.serve_forever()


# =========================
# دیتابیس
# =========================

conn = sqlite3.connect(DB_NAME, check_same_thread=False)
cursor = conn.cursor()

cursor.execute("""
CREATE TABLE IF NOT EXISTS users (
    user_id INTEGER PRIMARY KEY,
    points INTEGER DEFAULT 0,
    last_nazi REAL DEFAULT 0
)
""")

conn.commit()


# =========================
# گرفتن / ساخت کاربر
# =========================

def get_user(user_id):
    cursor.execute(
        "SELECT points, last_nazi FROM users WHERE user_id = ?",
        (user_id,)
    )

    user = cursor.fetchone()

    if user is None:
        cursor.execute(
            "INSERT INTO users (user_id, points, last_nazi) VALUES (?, ?, ?)",
            (user_id, 0, 0)
        )
        conn.commit()

        return 0, 0

    return user


# =========================
# پیام‌ها
# =========================

async def handle_message(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    if not update.message or not update.message.text:
        return

    text = update.message.text.strip()
    user_id = update.message.from_user.id

    points, last_nazi = get_user(user_id)

    # -------------------------
    # دیدن پوینت
    # -------------------------

    if text == "پوینت":
        await update.message.reply_text(
            f"🪙 پوینت شما: {points}"
        )
        return

    # -------------------------
    # سیستم نازی
    # -------------------------

    if "نازی" in text:

        now = time.time()
        elapsed = now - last_nazi

        if elapsed < COOLDOWN_SECONDS:

            remaining = int(COOLDOWN_SECONDS - elapsed) + 1

            await update.message.reply_text(
                f"⏱️ هنوز زوده!\n"
                f"{remaining} ثانیه دیگه دوباره امتحان کن."
            )

            return

        earned = random.randint(
            MIN_POINTS,
            MAX_POINTS
        )

        new_points = points + earned

        cursor.execute(
            """
            UPDATE users
            SET points = ?, last_nazi = ?
            WHERE user_id = ?
            """,
            (
                new_points,
                now,
                user_id
            )
        )

        conn.commit()

        await update.message.reply_text(
            f"🪙 +{earned} پوینت!\n"
            f"💰 موجودی: {new_points}"
        )

        return


# =========================
# اجرای بات
# =========================

def main():

    # وب‌سرور رو توی یه ترد جدا اجرا کن
    threading.Thread(target=run_server, daemon=True).start()

    app = (
        Application.builder()
        .token(TOKEN)
        .base_url("https://tapi.bale.ai/bot")
        .build()
    )

    app.add_handler(
        MessageHandler(
            filters.TEXT & ~filters.COMMAND,
            handle_message
        )
    )

    print("Bot started...")

    app.run_polling()


if __name__ == "__main__":
    main()
