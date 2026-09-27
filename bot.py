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
        self.wfile.write(b"Greater Reich is running!")

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
    username TEXT DEFAULT '',
    first_name TEXT DEFAULT '',
    branch TEXT DEFAULT '',
    rank INTEGER DEFAULT 1,
    soldiers INTEGER DEFAULT 0,
    tanks INTEGER DEFAULT 0,
    planes INTEGER DEFAULT 0,
    approval INTEGER DEFAULT 100
)
""")

try:
    cursor.execute("ALTER TABLE users ADD COLUMN IF NOT EXISTS last_gamble DOUBLE PRECISION DEFAULT 0")
    cursor.execute("ALTER TABLE users ADD COLUMN IF NOT EXISTS username TEXT DEFAULT ''")
    cursor.execute("ALTER TABLE users ADD COLUMN IF NOT EXISTS first_name TEXT DEFAULT ''")
    cursor.execute("ALTER TABLE users ADD COLUMN IF NOT EXISTS branch TEXT DEFAULT ''")
    cursor.execute("ALTER TABLE users ADD COLUMN IF NOT EXISTS rank INTEGER DEFAULT 1")
    cursor.execute("ALTER TABLE users ADD COLUMN IF NOT EXISTS soldiers INTEGER DEFAULT 0")
    cursor.execute("ALTER TABLE users ADD COLUMN IF NOT EXISTS tanks INTEGER DEFAULT 0")
    cursor.execute("ALTER TABLE users ADD COLUMN IF NOT EXISTS planes INTEGER DEFAULT 0")
    cursor.execute("ALTER TABLE users ADD COLUMN IF NOT EXISTS approval INTEGER DEFAULT 100")
except Exception as e:
    print("Alter table error:", e)


RANKS = {
    1: "Soldat",
    2: "Unteroffizier",
    3: "Leutnant",
    4: "Hauptmann",
    5: "Major",
    6: "Oberst",
    7: "General",
    8: "Feldmarschall",
    9: "Reichsführer"
}

RANK_THRESHOLDS = {
    1: 0,
    2: 100,
    3: 300,
    4: 700,
    5: 1500,
    6: 3000,
    7: 6000,
    8: 12000,
    9: 25000
}

BRANCHES = ["Wehrmacht", "Gestapo", "Propaganda", "Wirtschaft"]


def calculate_rank(points):
    rank = 1
    for r, threshold in RANK_THRESHOLDS.items():
        if points >= threshold:
            rank = r
    return rank


def get_user(user_id):
    try:
        cursor.execute(
            """SELECT points, last_nazi, last_gamble, branch, rank,
                      soldiers, tanks, planes, approval
               FROM users WHERE user_id = %s""",
            (user_id,)
        )
        user = cursor.fetchone()

        if user is None:
            cursor.execute(
                "INSERT INTO users (user_id, points, last_nazi, last_gamble) VALUES (%s, %s, %s, %s)",
                (user_id, 0, 0, 0)
            )
            return 0, 0, 0, "", 1, 0, 0, 0, 100

        return user

    except Exception as e:
        print("get_user error:", e)
        return 0, 0, 0, "", 1, 0, 0, 0, 100


def update_field(user_id, field, value):
    try:
        cursor.execute(
            f"UPDATE users SET {field} = %s WHERE user_id = %s",
            (value, user_id)
        )
    except Exception as e:
        print(f"update {field} error:", e)


def format_time(seconds):
    m = seconds // 60
    s = seconds % 60
    return f"{m}:{s:02d}"


def user_display(uname, uid, fname):
    if uname:
        return f"@{uname}"
    elif fname:
        return fname
    else:
        return str(uid)


# =========================
# پیام‌ها
# =========================

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):

    if not update.message or not update.message.text:
        return

    text = update.message.text.strip()
    user_id = update.message.from_user.id
    chat_type = update.message.chat.type

    try:
        uname = update.message.from_user.username or ""
        fname = update.message.from_user.first_name or ""
        cursor.execute(
            "UPDATE users SET username = %s, first_name = %s WHERE user_id = %s",
            (uname, fname, user_id)
        )
    except Exception as e:
        print("username error:", e)

    (points, last_nazi, last_gamble,
     branch, rank, soldiers, tanks, planes, approval) = get_user(user_id)

    # محاسبه‌ی رتبه‌ی خودکار
    new_rank = calculate_rank(points)
    if new_rank != rank:
        update_field(user_id, "rank", new_rank)
        rank = new_rank

    # ================= راهنما =================
    if text == "راهنما":
        await update.message.reply_text(
            "🏛️ راهنمای Greater Reich:\n\n"
            "🔹 نازی → دریافت Reichsmark (هر ۲ دقیقه)\n"
            "🔹 پوینت → مشاهده موجودی\n"
            "🔹 قمار [مقدار] → شرط‌بندی (هر ۱ دقیقه)\n"
            "🔹 انتقال [مقدار] → با ریپلای\n"
            "🔹 شاخه [نام] → Wehrmacht / Gestapo / Propaganda / Wirtschaft\n"
            "🔹 رتبه → مشاهده رتبه و وضعیت\n"
            "🔹 خرید سرباز [تعداد]\n"
            "🔹 خرید تانک [تعداد]\n"
            "🔹 خرید هواپیما [تعداد]\n"
            "🔹 حمله به [کاربر] → با ریپلای\n"
            "🔹 مالیات → دریافت مالیات\n"
            "🔹 تبلیغات → افزایش رضایت مردم\n"
            "🔹 رنکم → رتبه‌ی من\n"
            "🔹 رنک → لیدربرد گروه\n"
            "🔹 رنک جهانی → لیدربرد جهانی\n\n"
            "🛠 پشتیبانی: @KM12502\n\n"
            "زنده باد پیشوای بزرگ هیتلر🙋🫡"
        )
        return

    # ================= پوینت =================
    if text == "پوینت":
        await update.message.reply_text(
            f"زنده باد پیشوای بزرگ هیتلر🙋🫡\n"
            f"Reichsmark: {points}"
        )
        return

    # ================= رتبه =================
    if text == "رتبه":
        rank_name = RANKS.get(rank, "Soldat")
        await update.message.reply_text(
            f"🎖️ وضعیت تو در رایش:\n\n"
            f"🔹 رتبه: {rank_name} (سطح {rank})\n"
            f"🔹 شاخه: {branch if branch else 'انتخاب نشده'}\n"
            f"💰 Reichsmark: {points}\n"
            f"🪖 سرباز: {soldiers}\n"
            f"🛡️ تانک: {tanks}\n"
            f"✈️ هواپیما: {planes}\n"
            f"👥 رضایت مردم: {approval}%"
        )
        return

    # ================= شاخه =================
    if text.startswith("شاخه"):
        parts = text.split()
        if len(parts) != 2:
            await update.message.reply_text(
                "❌ فرمت: شاخه Wehrmacht\n"
                "شاخه‌ها: Wehrmacht / Gestapo / Propaganda / Wirtschaft"
            )
            return

        chosen = parts[1]
        if chosen not in BRANCHES:
            await update.message.reply_text(
                "❌ شاخه نامعتبر!\n"
                "شاخه‌ها: Wehrmacht / Gestapo / Propaganda / Wirtschaft"
            )
            return

        if branch:
            await update.message.reply_text(
                f"❌ تو قبلاً شاخه‌ی {branch} رو انتخاب کردی!"
            )
            return

        update_field(user_id, "branch", chosen)
        await update.message.reply_text(
            f"✅ به شاخه‌ی {chosen} پیوستی!\n"
            f"زنده باد پیشوا🙋🫡"
        )
        return

    # ================= خرید سرباز =================
    if text.startswith("خرید سرباز"):
        parts = text.split()
        if len(parts) != 3:
            await update.message.reply_text("❌ فرمت: خرید سرباز 5")
            return
        try:
            qty = int(parts[2])
        except:
            await update.message.reply_text("❌ تعداد باید عدد باشه!")
            return
        if qty <= 0:
            await update.message.reply_text("❌ تعداد باید بیشتر از ۰ باشه!")
            return
        cost = qty * 10
        if points < cost:
            await update.message.reply_text(f"❌ Reichsmark کافی نداری! نیاز: {cost}")
            return
        update_field(user_id, "points", points - cost)
        update_field(user_id, "soldiers", soldiers + qty)
        await update.message.reply_text(
            f"✅ {qty} سرباز خریدی!\n"
            f"💰 هزینه: {cost}\n"
            f"🪖 سربازان تو: {soldiers + qty}"
        )
        return

    # ================= خرید تانک =================
    if text.startswith("خرید تانک"):
        parts = text.split()
        if len(parts) != 3:
            await update.message.reply_text("❌ فرمت: خرید تانک 2")
            return
        try:
            qty = int(parts[2])
        except:
            await update.message.reply_text("❌ تعداد باید عدد باشه!")
            return
        if qty <= 0:
            await update.message.reply_text("❌ تعداد باید بیشتر از ۰ باشه!")
            return
        cost = qty * 50
        if points < cost:
            await update.message.reply_text(f"❌ Reichsmark کافی نداری! نیاز: {cost}")
            return
        update_field(user_id, "points", points - cost)
        update_field(user_id, "tanks", tanks + qty)
        await update.message.reply_text(
            f"✅ {qty} تانک خریدی!\n"
            f"💰 هزینه: {cost}\n"
            f"🛡️ تانک‌های تو: {tanks + qty}"
        )
        return

    # ================= خرید هواپیما =================
    if text.startswith("خرید هواپیما"):
        parts = text.split()
        if len(parts) != 3:
            await update.message.reply_text("❌ فرمت: خرید هواپیما 1")
            return
        try:
            qty = int(parts[2])
        except:
            await update.message.reply_text("❌ تعداد باید عدد باشه!")
            return
        if qty <= 0:
            await update.message.reply_text("❌ تعداد باید بیشتر از ۰ باشه!")
            return
        cost = qty * 100
        if points < cost:
            await update.message.reply_text(f"❌ Reichsmark کافی نداری! نیاز: {cost}")
            return
        update_field(user_id, "points", points - cost)
        update_field(user_id, "planes", planes + qty)
        await update.message.reply_text(
            f"✅ {qty} هواپیما خریدی!\n"
            f"💰 هزینه: {cost}\n"
            f"✈️ هواپیماهای تو: {planes + qty}"
        )
        return

    # ================= حمله =================
    if text.startswith("حمله به"):
        if not update.message.reply_to_message:
            await update.message.reply_text("❌ روی پیام کاربر ریپلای کن و بنویس: حمله به")
            return

        target = update.message.reply_to_message.from_user
        target_id = target.id

        if target_id == user_id:
            await update.message.reply_text("❌ به خودت حمله نکن!")
            return

        my_power = (soldiers * 1) + (tanks * 5) + (planes * 10)
        if my_power < 10:
            await update.message.reply_text("❌ قدرت نظامی کافی نداری! اول تجهیزات بخر.")
            return

        (t_points, _, _, _, _, t_soldiers, t_tanks, t_planes, _) = get_user(target_id)
        target_power = (t_soldiers * 1) + (t_tanks * 5) + (t_planes * 10)

        my_total = my_power * random.uniform(0.7, 1.3)
        target_total = target_power * random.uniform(0.7, 1.3) + 10

        if my_total > target_total:
            # برد
            gain = random.randint(50, 200)
            new_points = points + gain
            update_field(user_id, "points", new_points)

            # تلفات دشمن
            if t_soldiers > 0:
                update_field(target_id, "soldiers", max(0, t_soldiers - 1))

            await update.message.reply_text(
                f"🎉 حمله موفق بود!\n"
                f"💰 +{gain} Reichsmark\n"
                f"زنده باد پیشوا🙋🫡"
            )
        else:
            # باخت
            loss = random.randint(30, 100)
            new_points = max(0, points - loss)
            update_field(user_id, "points", new_points)

            if soldiers > 0:
                update_field(user_id, "soldiers", soldiers - 1)

            await update.message.reply_text(
                f"💔 حمله شکست خورد!\n"
                f"💰 -{loss} Reichsmark\n"
                f"🪖 یک سرباز از دست دادی."
            )
        return

    # ================= مالیات =================
    if text == "مالیات":
        tax = random.randint(20, 50)
        new_points = points + tax
        update_field(user_id, "points", new_points)
        await update.message.reply_text(
            f"💰 مالیات دریافت شد: +{tax} Reichsmark\n"
            f"موجودی: {new_points}"
        )
        return

    # ================= تبلیغات =================
    if text == "تبلیغات":
        if points < 50:
            await update.message.reply_text("❌ نیاز به ۵۰ Reichsmark داری!")
            return
        update_field(user_id, "points", points - 50)
        new_approval = min(100, approval + 5)
        update_field(user_id, "approval", new_approval)
        await update.message.reply_text(
            f"📢 تبلیغات انجام شد!\n"
            f"👥 رضایت مردم: {new_approval}%"
        )
        return

    # ================= رنکم =================
    if text == "رنکم":
        cursor.execute("SELECT COUNT(*) FROM users WHERE points > %s", (points,))
        global_rank = cursor.fetchone()[0] + 1
        await update.message.reply_text(
            f"📊 رتبه‌ی تو:\n"
            f"🏅 رتبه جهانی: {global_rank}\n"
            f"💰 Reichsmark: {points}"
        )
        return

    # ================= لیدربرد جهانی =================
    if text in ["رنک جهانی", "لیدربرد جهانی"]:
        cursor.execute(
            "SELECT user_id, username, first_name, points FROM users WHERE points > 0 ORDER BY points DESC LIMIT 10"
        )
        top = cursor.fetchall()
        if not top:
            await update.message.reply_text("هنوز هیچ کاربری پوینت نداره!")
            return
        result = "🌍 لیدربرد جهانی:\n\n"
        for i, (uid, uname, fname, pts) in enumerate(top, 1):
            name = user_display(uname, uid, fname)
            result += f"{i}- {name} - نازی پوینت هاش: {pts}\n"
        await update.message.reply_text(result)
        return

    # ================= لیدربرد گروه =================
    if text in ["رنک", "لیدربرد"]:
        cursor.execute(
            "SELECT user_id, username, first_name, points FROM users WHERE points > 0 ORDER BY points DESC LIMIT 10"
        )
        top = cursor.fetchall()
        if not top:
            await update.message.reply_text("هنوز هیچ کاربری پوینت نداره!")
            return
        result = "🏆 لیدربرد گروه:\n\n"
        for i, (uid, uname, fname, pts) in enumerate(top, 1):
            name = user_display(uname, uid, fname)
            result += f"{i}- {name} - نازی پوینت هاش: {pts}\n"
        await update.message.reply_text(result)
        return

    # ================= انتقال =================
    if text.startswith("انتقال"):
        if not update.message.reply_to_message:
            await update.message.reply_text("❌ روی پیام کاربر ریپلای کن و بنویس: انتقال 100")
            return
        target = update.message.reply_to_message.from_user
        target_id = target.id
        if target_id == user_id:
            await update.message.reply_text("❌ نمی‌تونی به خودت پوینت بدی!")
            return
        parts = text.split()
        if len(parts) != 2:
            await update.message.reply_text("❌ فرمت: انتقال 100")
            return
        try:
            amount = int(parts[1])
        except:
            await update.message.reply_text("❌ مقدار باید عدد باشه!")
            return
        if amount <= 0 or amount > points:
            await update.message.reply_text("❌ مقدار نامعتبر!")
            return
        t_points, _, _, _, _, _, _, _, _ = get_user(target_id)
        update_field(user_id, "points", points - amount)
        update_field(target_id, "points", t_points + amount)
        await update.message.reply_text(
            f"✅ {amount} Reichsmark به {target.first_name} انتقال یافت."
        )
        return

    # ================= قمار =================
    if text.startswith("قمار"):
        parts = text.split()
        if len(parts) != 2:
            await update.message.reply_text("❌ فرمت: قمار 100")
            return
        try:
            amount = int(parts[1])
        except:
            await update.message.reply_text("❌ مقدار باید عدد باشه!")
            return
        if amount <= 0 or amount > points:
            await update.message.reply_text("❌ مقدار نامعتبر یا موجودی کافی نیست!")
            return
        now = time.time()
        if now - last_gamble < GAMBLE_COOLDOWN_SECONDS:
            remaining = int(GAMBLE_COOLDOWN_SECONDS - (now - last_gamble)) + 1
            await update.message.reply_text(f"⏱️ {format_time(remaining)} دیگه می‌تونی قمار کنی.")
            return
        win = random.choice([True, False])
        if win:
            new_points = points + amount
            update_field(user_id, "points", new_points)
            update_field(user_id, "last_gamble", now)
            await update.message.reply_text(
                f"زنده باد پیشوای بزرگ هیتلر🙋🫡\n"
                f"پیشوا مقداری پول به تو بخشید.\n"
                f"{amount * 2} تا دریافت کردی.\n"
                f"موجودی: {new_points}"
            )
        else:
            new_points = points - amount
            update_field(user_id, "points", new_points)
            update_field(user_id, "last_gamble", now)
            await update.message.reply_text(
                f"زنده باد پیشوای بزرگ هیتلر🙋🫡\n"
                f"پولت خرج امور حزب و پیشوا شد.\n"
                f"موجودی: {new_points}"
            )
        return

    # ================= نازی =================
    if "نازی" in text:
        now = time.time()
        if now - last_nazi < COOLDOWN_SECONDS:
            remaining = int(COOLDOWN_SECONDS - (now - last_nazi)) + 1
            await update.message.reply_text(
                f"پیشوا مشغول امور کشور، مردم، جنگ، حزب و... است.\n"
                f"⏱️ {format_time(remaining)} دیگر کارش تمام می‌شود."
            )
            return
        earned = random.randint(MIN_POINTS, MAX_POINTS)
        new_points = points + earned
        update_field(user_id, "points", new_points)
        update_field(user_id, "last_nazi", now)
        await update.message.reply_text(
            f"به دلیل کار برای حزب در شاخه‌ی خودت، {earned} Reichsmark دریافت کردی.\n"
            f"موجودی: {new_points}"
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
        MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message)
    )

    print("Greater Reich bot started...")
    app.run_polling()


if __name__ == "__main__":
    main()
