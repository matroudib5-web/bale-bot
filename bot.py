import random
import time
import os
import threading
from http.server import HTTPServer, BaseHTTPRequestHandler

import psycopg2
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

DATABASE_URL = os.environ.get("DATABASE_URL")


# =========================
# وب‌سرور کوچیک برای Render
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
    server = HTTPServer(("0.0.0.0", port), Handler)
    server.serve_forever()


# =========================
# دیتابیس
# =========================

conn = psycopg2.connect(DATABASE_URL, sslmode="require")
cursor = conn.cursor()

cursor.execute("""
CREATE TABLE IF NOT EXISTS users (
    user_id BIGINT PRIMARY KEY,
    points INTEGER DEFAULT 0,
    last_nazi DOUBLE PRECISION DEFAULT 0
)
""")

conn.commit()


def get_user(user_id):
    cursor.execute(
        "SELECT points, last_nazi FROM users WHERE user_id = %s",
        (user_id,)
    )
    user = cursor.fetchone()

    if user is None:
        cursor.execute(
            "INSERT INTO users (user_id, points, last_nazi) VALUES (%s, %s, %s)",
            (user_id, 0, 0)
        )
        conn.commit()
        return 0, 0

    return user


def update_points(user_id, points):
    cursor.execute(
        "UPDATE users SET points = %s WHERE user_id = %s",
        (points, user_id)
    )
    conn.commit()


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

    if text == "پوینت":
        await update.message.reply_text(
            f"🥳 نازی پوینت‌هات: {points} (پولداریا 😂)"
        )
        return

    if text.startswith("قمار"):
        parts = text.split()

        if len(parts) != 2:
            await update.message.reply_text("❌ فرمت درست: قمار 100")
            return

        try:
            amount = int(parts[1])
        except:
            await update.message.reply_text("❌ مقدار باید عدد باشه!")
            return

        if amount <= 0:
            await update.message.reply_text("❌ مقدار باید بیشتر از ۰ باشه!")
            return

        if amount > points:
            await update.message.reply_text(
                f"❌ پوینت کافی نداری!\n"
                f"🥳 نازی پوینت‌هات: {points}"
            )
            return

        win = random.choice([True, False])

        if win:
            new_points = points + amount
            update_points(user_id, new_points)
            await update.message.reply_text(
                f"🎉 بردی!\n"
                f"🪙 +{amount} نازی پوینت\n"
                f"🥳 نازی پوینت‌هات: {new_points} (پولداریا 😂)"
            )
        else:
            new_points = points - amount
            update_points(user_id, new_points)
            await update.message.reply_text(
                f"💔 باختی!\n"
                f"🪙 -{amount} نازی پوینت\n"
                f"🥳 نازی پوینت‌هات: {new_points} (پولداریا 😂)"
            )
        return

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

        earned = random.randint(MIN_POINTS, MAX_POINTS)
        new_points = points + earned

        cursor.execute(
            "UPDATE users SET points = %s, last_nazi = %s WHERE user_id = %s",
            (new_points, now, user_id)
        )
        conn.commit()

        await update.message.reply_text(
            f"زنده باد هیتلر🙋🫡" 
            f"🎉 {earned} نازی پوینت گرفتی!\n"
            f"🥳 نازی پوینت‌هات: {new_points} (پولداریا 😂)"
        )
        return


# =========================
# اجرای بات
# =========================

def main():
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
