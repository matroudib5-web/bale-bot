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

COOLDOWN_SECONDS = 120
GAMBLE_COOLDOWN_SECONDS = 60
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
    last_nazi DOUBLE PRECISION DEFAULT 0,
    last_gamble DOUBLE PRECISION DEFAULT 0
)
""")

conn.commit()


def get_user(user_id):
    cursor.execute(
        "SELECT points, last_nazi, last_gamble FROM users WHERE user_id = %s",
        (user_id,)
    )
    user = cursor.fetchone()

    if user is None:
        cursor.execute(
            "INSERT INTO users (user_id, points, last_nazi, last_gamble) VALUES (%s, %s, %s, %s)",
            (user_id, 0, 0, 0)
        )
        conn.commit()
        return 0, 0, 0

    return user


def update_points(user_id, points):
    cursor.execute(
        "UPDATE users SET points = %s WHERE user_id = %s",
        (points, user_id)
    )
    conn.commit()


def format_time(seconds):
    m = seconds // 60
    s = seconds % 60
    return f"{m}:{s:02d}"


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

    points, last_nazi, last_gamble = get_user(user_id)

    if text == "پوینت":
        await update.message.reply_text(
            f"زنده باد پیشوای بزرگ هیتلر🙋🫡\n"
            f"نازی پوینت هات: {points}"
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
                f"نازی پوینت هات: {points}"
            )
            return

        now = time.time()
        elapsed = now - last_gamble

        if elapsed < GAMBLE_COOLDOWN_SECONDS:
            remaining = int(GAMBLE_COOLDOWN_SECONDS - elapsed) + 1
            await update.message.reply_text(
                f"⏱️ {format_time(remaining)} دیگه می‌تونی قمار کنی."
            )
            return

        win = random.choice([True, False])

        if win:
            reward = amount * 2
            new_points = points + amount
            update_points(user_id, new_points)
            cursor.execute(
                "UPDATE users SET last_gamble = %s WHERE user_id = %s",
                (now, user_id)
            )
            conn.commit()
            await update.message.reply_text(
                f"زنده باد پیشوای بزرگ هیتلر🙋🫡\n"
                f"پیشوا مقداری پول به تو بخشید.\n"
                f"{reward} تا دریافت کردی.\n"
                f"نازی پوینت هات: {new_points}"
            )
        else:
            new_points = points - amount
            update_points(user_id, new_points)
            cursor.execute(
                "UPDATE users SET last_gamble = %s WHERE user_id = %s",
                (now, user_id)
            )
            conn.commit()
            await update.message.reply_text(
                f"زنده باد پیشوای بزرگ هیتلر🙋🫡\n"
                f"پولت خرج امور حزب و پیشوا شد.\n"
                f"نازی پوینت هات: {new_points}"
            )
        return

    if "نازی" in text:
        now = time.time()
        elapsed = now - last_nazi

        if elapsed < COOLDOWN_SECONDS:
            remaining = int(COOLDOWN_SECONDS - elapsed) + 1
            await update.message.reply_text(
                f"پیشوا مشغول امور کشور، مردم، جنگ، حزب و... است.\n"
                f"⏱️ {format_time(remaining)} دیگر کارش تمام می‌شود و آنگاه درخواستت را به او بگو."
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
            f"به دلیل کار برای حزب در شاخه‌ی خودت، {earned} نازی پوینت دریافت کردی.\n"
            f"نازی پوینت هات: {new_points}"
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
