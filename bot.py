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
conn.autocommit = True
cursor = conn.cursor()

cursor.execute("""
CREATE TABLE IF NOT EXISTS users (
    user_id BIGINT PRIMARY KEY,
    points INTEGER DEFAULT 0,
    last_nazi DOUBLE PRECISION DEFAULT 0,
    last_gamble DOUBLE PRECISION DEFAULT 0,
    username TEXT DEFAULT ''
)
""")

try:
    cursor.execute(
        "ALTER TABLE users ADD COLUMN IF NOT EXISTS last_gamble DOUBLE PRECISION DEFAULT 0"
    )
    cursor.execute(
        "ALTER TABLE users ADD COLUMN IF NOT EXISTS username TEXT DEFAULT ''"
    )
except Exception as e:
    print("Alter table error:", e)


def get_user(user_id):
    try:
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
            return 0, 0, 0

        return user

    except Exception as e:
        print("get_user error:", e)
        return 0, 0, 0


def update_points(user_id, points):
    try:
        cursor.execute(
            "UPDATE users SET points = %s WHERE user_id = %s",
            (points, user_id)
        )
    except Exception as e:
        print("update_points error:", e)


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

    # ذخیره‌ی یوزرنیم
    try:
        uname = update.message.from_user.username or update.message.from_user.first_name or ""
        cursor.execute(
            "UPDATE users SET username = %s WHERE user_id = %s",
            (uname, user_id)
        )
    except Exception as e:
        print("username error:", e)

    points, last_nazi, last_gamble = get_user(user_id)

    # -------------------------
    # راهنما
    # -------------------------
    if text == "راهنما":
        await update.message.reply_text(
            "📖 راهنمای ربات:\n\n"
            "🔹 نازی → دریافت پوینت (هر ۲ دقیقه)\n"
            "🔹 پوینت → مشاهده موجودی\n"
            "🔹 قمار [مقدار] → شرط‌بندی (هر ۱ دقیقه)\n"
            "🔹 رنکینگ → برترین‌های حزب\n"
            "🔹 انتقال [مقدار] → با ریپلای، پوینت به کاربر بفرست\n"
            "🔹 راهنما → همین پیام\n\n"
            "🛠 پشتیبانی: @KM12502\n\n"
            "زنده باد پیشوای بزرگ هیتلر🙋🫡"
        )
        return

    # -------------------------
    # رنکینگ
    # -------------------------
    if text == "رنکینگ":
        try:
            cursor.execute(
                "SELECT username, points FROM users ORDER BY points DESC LIMIT 10"
            )
            top_users = cursor.fetchall()

            if not top_users:
                await update.message.reply_text("هنوز هیچ کاربری پوینت نداره!")
                return

            result = "🏆 برترین‌های حزب:\n\n"
            for i, (uname, pts) in enumerate(top_users, 1):
                name = uname if uname else "بی‌نام"
                result += f"{i}. {name} — {pts} نازی پوینت\n"

            await update.message.reply_text(result)
        except Exception as e:
            print("ranking error:", e)
        return

    # -------------------------
    # مشاهده پوینت
    # -------------------------
    if text == "پوینت":
        await update.message.reply_text(
            f"زنده باد پیشوای بزرگ هیتلر🙋🫡\n"
            f"نازی پوینت هات: {points}"
        )
        return

    # -------------------------
    # انتقال پوینت
    # -------------------------
    if text.startswith("انتقال"):
        if not update.message.reply_to_message:
            await update.message.reply_text(
                "❌ برای انتقال، روی پیام کاربر ریپلای کن و بنویس:\n"
                "انتقال 100"
            )
            return

        target_user = update.message.reply_to_message.from_user
        target_id = target_user.id

        if target_id == user_id:
            await update.message.reply_text("❌ نمی‌تونی به خودت پوینت بدی!")
            return

        parts = text.split()
        if len(parts) != 2:
            await update.message.reply_text("❌ فرمت درست: انتقال 100")
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

        target_points, _, _ = get_user(target_id)

        update_points(user_id, points - amount)
        update_points(target_id, target_points + amount)

        await update.message.reply_text(
            f"✅ {amount} نازی پوینت به {target_user.first_name} انتقال یافت.\n"
            f"نازی پوینت هات: {points - amount}"
        )
        return

    # -------------------------
    # قمار
    # -------------------------
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
            try:
                cursor.execute(
                    "UPDATE users SET last_gamble = %s WHERE user_id = %s",
                    (now, user_id)
                )
            except Exception as e:
                print("gamble time error:", e)
            await update.message.reply_text(
                f"زنده باد پیشوای بزرگ هیتلر🙋🫡\n"
                f"پیشوا مقداری پول به تو بخشید.\n"
                f"{reward} تا دریافت کردی.\n"
                f"نازی پوینت هات: {new_points}"
            )
        else:
            new_points = points - amount
            update_points(user_id, new_points)
            try:
                cursor.execute(
                    "UPDATE users SET last_gamble = %s WHERE user_id = %s",
                    (now, user_id)
                )
            except Exception as e:
                print("gamble time error:", e)
            await update.message.reply_text(
                f"زنده باد پیشوای بزرگ هیتلر🙋🫡\n"
                f"پولت خرج امور حزب و پیشوا شد.\n"
                f"نازی پوینت هات: {new_points}"
            )
        return

    # -------------------------
    # نازی
    # -------------------------
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

        try:
            cursor.execute(
                "UPDATE users SET points = %s, last_nazi = %s WHERE user_id = %s",
                (new_points, now, user_id)
            )
        except Exception as e:
            print("nazi update error:", e)

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
