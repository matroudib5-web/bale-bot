import random
import time
import os
import threading
from http.server import HTTPServer, BaseHTTPRequestHandler
from datetime import datetime, timedelta

import psycopg2
from telegram import Update
from telegram.ext import Application, MessageHandler, ContextTypes, filters

# =========================
# تنظیمات
# =========================

TOKEN = "152004939:gjvarQqggvlUKNXdDBoJPx-mTNcNGPBu0k8"
FÜHRER_ID = 1618371215
DATABASE_URL = os.environ.get("DATABASE_URL")

# کول‌داون‌ها
WORK_COOLDOWN = 300  # هر ۵ دقیقه کار
BATTLE_COOLDOWN = 600  # هر ۱۰ دقیقه حمله


# =========================
# وب‌سرور برای Render
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
# اتصال دیتابیس
# =========================

conn = psycopg2.connect(DATABASE_URL, sslmode="require")
conn.autocommit = True
cursor = conn.cursor()

cursor.execute("""
CREATE TABLE IF NOT EXISTS users (
    user_id BIGINT PRIMARY KEY,
    username TEXT DEFAULT '',
    first_name TEXT DEFAULT '',
    rank INTEGER DEFAULT 1,
    branch TEXT DEFAULT '',
    experience INTEGER DEFAULT 0,
    rm INTEGER DEFAULT 0,
    manpower INTEGER DEFAULT 0,
    steel INTEGER DEFAULT 0,
    oil INTEGER DEFAULT 0,
    food INTEGER DEFAULT 0,
    approval INTEGER DEFAULT 100,
    soldiers INTEGER DEFAULT 0,
    tanks INTEGER DEFAULT 0,
    planes INTEGER DEFAULT 0,
    submarines INTEGER DEFAULT 0,
    last_work DOUBLE PRECISION DEFAULT 0,
    last_battle DOUBLE PRECISION DEFAULT 0
)
""")

cursor.execute("""
CREATE TABLE IF NOT EXISTS treasury (
    id INTEGER PRIMARY KEY,
    rm BIGINT DEFAULT 0,
    manpower BIGINT DEFAULT 0,
    steel BIGINT DEFAULT 0,
    oil BIGINT DEFAULT 0,
    food BIGINT DEFAULT 0
)
""")

# مقدار اولیه خزانه
cursor.execute("SELECT COUNT(*) FROM treasury")
if cursor.fetchone()[0] == 0:
    cursor.execute(
        "INSERT INTO treasury (id, rm, manpower, steel, oil, food) VALUES (1, 0, 0, 0, 0, 0)"
    )


# =========================
# رتبه‌ها و شاخه‌ها
# =========================

RANKS = {
    1: "Schütze",
    2: "Obergefreiter",
    3: "Gefreiter",
    4: "Stabsgefreiter",
    5: "Unteroffizier",
    6: "Feldwebel",
    7: "Leutnant",
    8: "Oberleutnant",
    9: "Hauptmann",
    10: "Major",
    11: "Oberstleutnant",
    12: "Oberst",
    13: "Generalmajor",
    14: "Generalleutnant",
    15: "General",
    16: "Generaloberst",
    17: "Feldmarschall",
    18: "Reichsführer"
}

RANK_XP = {
    1: 0, 2: 100, 3: 300, 4: 600, 5: 1000,
    6: 2000, 7: 4000, 8: 8000, 9: 16000,
    10: 32000, 11: 64000, 12: 128000,
    13: 256000, 14: 512000, 15: 1024000,
    16: 2048000, 17: 4096000, 18: 8192000
}

BRANCHES = {
    "Wehrmacht": {"name": "وافن‌ماخت", "bonus": "قدرت نظامی +۵۰٪"},
    "Gestapo": {"name": "گشتاپو", "bonus": "قدرت سیاسی +۵۰٪"},
    "Propaganda": {"name": "پروپاگاندا", "bonus": "رضایت +۵٪ در روز"},
    "Wirtschaft": {"name": "اقتصاد", "bonus": "Reichsmark +۲۵٪"},
    "Landwirtschaft": {"name": "کشاورزی", "bonus": "غذا +۲۵٪"},
    "Rüstungsindustrie": {"name": "صنعت", "bonus": "فولاد +۲۵٪"}
}


# =========================
# توابع کمکی
# =========================

def calculate_rank(xp):
    rank = 1
    for r, threshold in RANK_XP.items():
        if xp >= threshold:
            rank = r
    return rank


def get_user(user_id):
    cursor.execute("SELECT * FROM users WHERE user_id = %s", (user_id,))
    cols = [desc[0] for desc in cursor.description]
    row = cursor.fetchone()
    if row:
        return dict(zip(cols, row))
    return None


def create_user(user_id, username, first_name):
    cursor.execute(
        """INSERT INTO users (user_id, username, first_name)
           VALUES (%s, %s, %s)
           ON CONFLICT (user_id) DO NOTHING""",
        (user_id, username, first_name)
    )
    return get_user(user_id)


def update_user(user_id, **kwargs):
    for field, value in kwargs.items():
        cursor.execute(
            f"UPDATE users SET {field} = %s WHERE user_id = %s",
            (value, user_id)
        )


def get_treasury():
    cursor.execute("SELECT rm, manpower, steel, oil, food FROM treasury WHERE id = 1")
    return cursor.fetchone()


def update_treasury(**kwargs):
    for field, value in kwargs.items():
        cursor.execute(
            f"UPDATE treasury SET {field} = %s WHERE id = 1",
            (value,)
        )


def format_time(seconds):
    m = seconds // 60
    s = seconds % 60
    return f"{m}:{s:02d}"


def display_name(user):
    if user.get("username"):
        return f"@{user['username']}"
    elif user.get("first_name"):
        return user["first_name"]
    return str(user["user_id"])


# =========================
# دستورات
# =========================

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message or not update.message.text:
        return

    text = update.message.text.strip()
    user_id = update.message.from_user.id
    username = update.message.from_user.username or ""
    first_name = update.message.from_user.first_name or ""

    user = get_user(user_id)
    if not user:
        user = create_user(user_id, username, first_name)
    else:
        # آپدیت یوزرنیم و اسم
        update_user(user_id, username=username, first_name=first_name)
        user["username"] = username
        user["first_name"] = first_name

    # آپدیت خودکار رتبه
    new_rank = calculate_rank(user["experience"])
    if new_rank != user["rank"]:
        update_user(user_id, rank=new_rank)
        user["rank"] = new_rank
        if new_rank > 1:
            await update.message.reply_text(
                f"🎖️ ترفیع گرفتی!\n"
                f"رتبه‌ی جدید: {RANKS[new_rank]}"
            )

    # ==================== راهنما ====================
    if text == "راهنما":
        await update.message.reply_text(
            "🏛️ **راهنمای Greater Reich**\n\n"
            "👤 **اطلاعات:**\n"
            "وضعیت | رتبه | شاخه‌ها | شورا\n\n"
            "💼 **کار و اقتصاد:**\n"
            "کار | خزانه | کمک [منبع] [مقدار] | درخواست [منبع]\n\n"
            "⚔️ **جنگ:**\n"
            "ارتش | حمله به [کشور] | دفاع\n\n"
            "🏆 **رتبه‌بندی:**\n"
            "رنک | رنک جهانی | برترین‌ها\n\n"
            "🏛️ **پیشوا (فقط رهبر):**\n"
            "انتصاب [@کاربر] [رتبه] | حکم [متن] | پروژه [نام]\n\n"
            "🛠 پشتیبانی: @KM12502"
        )
        return

    # ==================== شاخه‌ها ====================
    if text == "شاخه‌ها":
        msg = "🧩 **شاخه‌های رایش:**\n\n"
        for key, val in BRANCHES.items():
            msg += f"🔹 `{key}` — {val['name']}\n"
            msg += f"   مزیت: {val['bonus']}\n\n"
        msg += "برای انتخاب: `شاخه [نام انگلیسی]`"
        await update.message.reply_text(msg, parse_mode="Markdown")
        return

    if text.startswith("شاخه "):
        parts = text.split(maxsplit=1)
        if len(parts) != 2:
            await update.message.reply_text("❌ فرمت: شاخه Wehrmacht")
            return
        branch = parts[1]
        if branch not in BRANCHES:
            await update.message.reply_text("❌ شاخه نامعتبر!")
            return
        if user["branch"]:
            await update.message.reply_text(f"❌ تو قبلاً در شاخه {BRANCHES[user['branch']]['name']} هستی!")
            return
        update_user(user_id, branch=branch)
        await update.message.reply_text(
            f"✅ به شاخه‌ی {BRANCHES[branch]['name']} پیوستی!\n"
            f"مزیت: {BRANCHES[branch]['bonus']}\n\n"
            f"زنده باد پیشوا🙋🫡"
        )
        return

    # ==================== وضعیت ====================
    if text == "وضعیت":
        branch_name = BRANCHES.get(user["branch"], {}).get("name", "انتخاب نشده")
        rank_name = RANKS.get(user["rank"], "Schütze")
        await update.message.reply_text(
            f"📊 **وضعیت {display_name(user)}**\n\n"
            f"🎖️ رتبه: {rank_name} (سطح {user['rank']})\n"
            f"🧩 شاخه: {branch_name}\n"
            f"⭐ تجربه: {user['experience']}\n\n"
            f"💰 Reichsmark: {user['rm']}\n"
            f"🧑 نیروی انسانی: {user['manpower']}\n"
            f"⚙️ فولاد: {user['steel']}\n"
            f"⛽ نفت: {user['oil']}\n"
            f"🍞 غذا: {user['food']}\n"
            f"👥 رضایت: {user['approval']}%\n\n"
            f"🪖 سرباز: {user['soldiers']}\n"
            f"🛡️ تانک: {user['tanks']}\n"
            f"✈️ هواپیما: {user['planes']}\n"
            f"🚢 زیردریایی: {user['submarines']}",
            parse_mode="Markdown"
        )
        return

    # ==================== رتبه ====================
    if text == "رتبه":
        rank_name = RANKS.get(user["rank"], "Schütze")
        next_rank = user["rank"] + 1
        if next_rank in RANK_XP:
            needed = RANK_XP[next_rank] - user["experience"]
            next_name = RANKS[next_rank]
        else:
            needed = 0
            next_name = "بالاترین رتبه"
        await update.message.reply_text(
            f"🎖️ رتبه‌ی تو: **{rank_name}**\n"
            f"⭐ تجربه: {user['experience']}\n"
            f"📈 تا رتبه‌ی بعدی ({next_name}): {needed} XP",
            parse_mode="Markdown"
        )
        return

    # ==================== کار ====================
    if text == "کار":
        now = time.time()
        elapsed = now - user["last_work"]
        if elapsed < WORK_COOLDOWN:
            remaining = int(WORK_COOLDOWN - elapsed) + 1
            await update.message.reply_text(
                f"⏱️ برای کار بعدی {format_time(remaining)} صبر کن."
            )
            return

        # درآمد بر اساس شاخه
        rm_gain = random.randint(30, 80)
        xp_gain = random.randint(5, 15)

        if user["branch"] == "Wirtschaft":
            rm_gain = int(rm_gain * 1.25)
        elif user["branch"] == "Landwirtschaft":
            pass
        elif user["branch"] == "Rüstungsindustrie":
            steel_gain = random.randint(5, 15)
            update_user(user_id, steel=user["steel"] + steel_gain)

        new_rm = user["rm"] + rm_gain
        new_xp = user["experience"] + xp_gain

        update_user(
            user_id,
            rm=new_rm,
            experience=new_xp,
            last_work=now
        )

        await update.message.reply_text(
            f"💼 کار در {BRANCHES.get(user['branch'], {}).get('name', 'رایش')}:\n\n"
            f"💰 +{rm_gain} Reichsmark\n"
            f"⭐ +{xp_gain} تجربه\n"
            f"💰 موجودی: {new_rm}"
        )
        return

    # ==================== خزانه ====================
    if text == "خزانه":
        t = get_treasury()
        await update.message.reply_text(
            f"🏛️ **خزانه‌ی رایش:**\n\n"
            f"💰 Reichsmark: {t[0]}\n"
            f"🧑 نیروی انسانی: {t[1]}\n"
            f"⚙️ فولاد: {t[2]}\n"
            f"⛽ نفت: {t[3]}\n"
            f"🍞 غذا: {t[4]}",
            parse_mode="Markdown"
        )
        return

    # ==================== کمک به خزانه ====================
    if text.startswith("کمک "):
        parts = text.split()
        if len(parts) != 3:
            await update.message.reply_text("❌ فرمت: کمک rm 100")
            return
        resource, amount_str = parts[1], parts[2]
        try:
            amount = int(amount_str)
        except:
            await update.message.reply_text("❌ مقدار باید عدد باشه!")
            return
        if amount <= 0:
            await update.message.reply_text("❌ مقدار باید مثبت باشه!")
            return

        valid_resources = ["rm", "manpower", "steel", "oil", "food"]
        if resource not in valid_resources:
            await update.message.reply_text(f"❌ منابع معتبر: {', '.join(valid_resources)}")
            return

        if user[resource] < amount:
            await update.message.reply_text(f"❌ {resource} کافی نداری!")
            return

        update_user(user_id, **{resource: user[resource] - amount})
        t = get_treasury()
        t_idx = {"rm": 0, "manpower": 1, "steel": 2, "oil": 3, "food": 4}
        new_val = t[t_idx[resource]] + amount
        update_treasury(**{resource: new_val})

        await update.message.reply_text(
            f"✅ {amount} {resource} به خزانه اهدا شد.\n"
            f"زنده باد پیشوا🙋🫡"
        )
        return

    # ==================== درخواست از خزانه ====================
    if text.startswith("درخواست "):
        parts = text.split()
        if len(parts) != 3:
            await update.message.reply_text("❌ فرمت: درخواست rm 100")
            return
        resource, amount_str = parts[1], parts[2]
        try:
            amount = int(amount_str)
        except:
            await update.message.reply_text("❌ مقدار باید عدد باشه!")
            return
        if amount <= 0:
            await update.message.reply_text("❌ مقدار باید مثبت باشه!")
            return

        t = get_treasury()
        t_idx = {"rm": 0, "manpower": 1, "steel": 2, "oil": 3, "food": 4}
        if resource not in t_idx:
            await update.message.reply_text("❌ منبع نامعتبر!")
            return

        if t[t_idx[resource]] < amount:
            await update.message.reply_text("❌ خزانه موجودی کافی نداره!")
            return

        update_treasury(**{resource: t[t_idx[resource]] - amount})
        update_user(user_id, **{resource: user[resource] + amount})

        await update.message.reply_text(
            f"✅ {amount} {resource} از خزانه دریافت کردی."
        )
        return

    # ==================== خرید تجهیزات ====================
    if text.startswith("خرید "):
        parts = text.split()
        if len(parts) != 3:
            await update.message.reply_text("❌ فرمت: خرید سرباز 5")
            return
        item, qty_str = parts[1], parts[2]
        try:
            qty = int(qty_str)
        except:
            await update.message.reply_text("❌ تعداد باید عدد باشه!")
            return
        if qty <= 0:
            await update.message.reply_text("❌ تعداد باید مثبت باشه!")
            return

        costs = {
            "سرباز": (10, "manpower"),
            "تانک": (50, "steel"),
            "هواپیما": (100, "oil"),
            "زیردریایی": (150, "steel")
        }

        if item not in costs:
            await update.message.reply_text(
                "❌ آیتم‌ها: سرباز، تانک، هواپیما، زیردریایی"
            )
            return

        unit_cost, resource = costs[item]
        total = unit_cost * qty

        if user[resource] < total:
            await update.message.reply_text(
                f"❌ {resource} کافی نداری! نیاز: {total}"
            )
            return

        field_map = {
            "سرباز": "soldiers",
            "تانک": "tanks",
            "هواپیما": "planes",
            "زیردریایی": "submarines"
        }
        field = field_map[item]

        update_user(user_id, **{
            resource: user[resource] - total,
            field: user[field] + qty
        })

        await update.message.reply_text(
            f"✅ {qty} {item} خریدی!\n"
            f"💰 هزینه: {total} {resource}\n"
            f"📦 موجودی جدید: {user[field] + qty}"
        )
        return

    # ==================== ارتش ====================
    if text == "ارتش":
        power = user["soldiers"] * 1 + user["tanks"] * 5 + user["planes"] * 10 + user["submarines"] * 15
        if user["branch"] == "Wehrmacht":
            power = int(power * 1.5)

        await update.message.reply_text(
            f"⚔️ **ارتش تو:**\n\n"
            f"🪖 سرباز: {user['soldiers']}\n"
            f"🛡️ تانک: {user['tanks']}\n"
            f"✈️ هواپیما: {user['planes']}\n"
            f"🚢 زیردریایی: {user['submarines']}\n\n"
            f"💪 قدرت کل: {power}",
            parse_mode="Markdown"
        )
        return

    # ==================== حمله ====================
    if text.startswith("حمله به "):
        target = text.replace("حمله به ", "").strip()
        now = time.time()
        elapsed = now - user["last_battle"]
        if elapsed < BATTLE_COOLDOWN:
            remaining = int(BATTLE_COOLDOWN - elapsed) + 1
            await update.message.reply_text(
                f"⏱️ برای حمله بعدی {format_time(remaining)} صبر کن."
            )
            return

        my_power = user["soldiers"] * 1 + user["tanks"] * 5 + user["planes"] * 10
        if user["branch"] == "Wehrmacht":
            my_power = int(my_power * 1.5)

        if my_power < 10:
            await update.message.reply_text("❌ قدرت نظامی کافی نداری!")
            return

        # NPC
        npcs = {
            "اتریش": 50,
            "چکسلواکی": 100,
            "لهستان": 200,
            "فرانسه": 500,
            "انگلستان": 1000,
            "شوروی": 2000,
            "آمریکا": 3000
        }

        if target not in npcs:
            await update.message.reply_text(f"❌ دشمن نامعتبر!\nدشمنان: {', '.join(npcs.keys())}")
            return

        enemy_power = npcs[target]
        my_roll = my_power * random.uniform(0.7, 1.3)
        enemy_roll = enemy_power * random.uniform(0.7, 1.3)

        if my_roll > enemy_roll:
            # برد
            xp_gain = enemy_power // 10
            rm_gain = enemy_power * 2
            casualties = max(1, user["soldiers"] // 10)

            update_user(
                user_id,
                experience=user["experience"] + xp_gain,
                rm=user["rm"] + rm_gain,
                soldiers=max(0, user["soldiers"] - casualties),
                last_battle=now
            )

            await update.message.reply_text(
                f"🎉 **پیروزی در {target}!**\n\n"
                f"💰 +{rm_gain} RM\n"
                f"⭐ +{xp_gain} XP\n"
                f"🪖 تلفات: {casualties} سرباز\n\n"
                f"زنده باد پیشوا🙋🫡"
            )
        else:
            # باخت
            casualties = max(1, user["soldiers"] // 3)
            rm_loss = min(user["rm"], enemy_power)

            update_user(
                user_id,
                soldiers=max(0, user["soldiers"] - casualties),
                rm=user["rm"] - rm_loss,
                last_battle=now
            )

            await update.message.reply_text(
                f"💔 **شکست در {target}**\n\n"
                f"🪖 تلفات: {casualties} سرباز\n"
                f"💰 از دست رفته: {rm_loss} RM"
            )
        return

    # ==================== رنک ====================
    if text in ["رنک", "رنکم"]:
        cursor.execute("SELECT COUNT(*) FROM users WHERE experience > %s", (user["experience"],))
        rank_pos = cursor.fetchone()[0] + 1
        await update.message.reply_text(
            f"📊 رتبه‌ی تو در رایش:\n"
            f"🏅 مقام: {rank_pos}\n"
            f"⭐ تجربه: {user['experience']}"
        )
        return

    if text in ["رنک جهانی", "برترین‌ها"]:
        cursor.execute(
            "SELECT username, first_name, user_id, experience, rank FROM users ORDER BY experience DESC LIMIT 10"
        )
        top = cursor.fetchall()
        msg = "🏆 **برترین‌های رایش:**\n\n"
        for i, (uname, fname, uid, xp, rk) in enumerate(top, 1):
            name = f"@{uname}" if uname else (fname if fname else str(uid))
            rank_name = RANKS.get(rk, "Schütze")
            msg += f"{i}. {name} — {rank_name} ({xp} XP)\n"
        await update.message.reply_text(msg, parse_mode="Markdown")
        return

    # ==================== دستورات پیشوا ====================
    if user_id == FÜHRER_ID:

        if text.startswith("انتصاب "):
            parts = text.split()
            if len(parts) != 3:
                await update.message.reply_text("❌ فرمت: انتصاب @user 15")
                return
            target_username = parts[1].replace("@", "")
            try:
                new_rank = int(parts[2])
            except:
                await update.message.reply_text("❌ رتبه باید عدد باشه (۱ تا ۱۸)!")
                return
            if new_rank < 1 or new_rank > 18:
                await update.message.reply_text("❌ رتبه باید بین ۱ تا ۱۸ باشه!")
                return

            cursor.execute(
                "SELECT user_id FROM users WHERE username = %s",
                (target_username,)
            )
            result = cursor.fetchone()
            if not result:
                await update.message.reply_text("❌ کاربر پیدا نشد!")
                return

            target_id = result[0]
            update_user(target_id, rank=new_rank)
            await update.message.reply_text(
                f"✅ @{target_username} به رتبه‌ی {RANKS[new_rank]} منصوب شد.\n"
                f"فرمان پیشوا🙋🫡"
            )
            return

        if text.startswith("حکم "):
            command = text.replace("حکم ", "")
            cursor.execute("SELECT user_id FROM users")
            users = cursor.fetchall()
            for u in users:
                try:
                    await context.bot.send_message(
                        chat_id=u[0],
                        text=f"📜 **فرمان پیشوا:**\n\n{command}\n\nزنده باد پیشوا🙋🫡",
                        parse_mode="Markdown"
                    )
                except:
                    pass
            await update.message.reply_text(f"✅ فرمان به همه ارسال شد.")
            return

        if text == "شورا":
            cursor.execute(
                "SELECT username, first_name, user_id, experience, rank, branch FROM users ORDER BY experience DESC LIMIT 5"
            )
            top = cursor.fetchall()
            msg = "🏛️ **شورای رایش:**\n\n"
            for i, (uname, fname, uid, xp, rk, br) in enumerate(top, 1):
                name = f"@{uname}" if uname else (fname if fname else str(uid))
                rank_name = RANKS.get(rk, "Schütze")
                branch_name = BRANCHES.get(br, {}).get("name", "—")
                msg += f"{i}. {name}\n   رتبه: {rank_name}\n   شاخه: {branch_name}\n\n"
            await update.message.reply_text(msg, parse_mode="Markdown")
            return

        if text.startswith("پروژه "):
            project = text.replace("پروژه ", "")
            await update.message.reply_text(
                f"🏗️ پروژه‌ی **{project}** آغاز شد!\n"
                f"همه‌ی پلیرا برای تکمیل آن تلاش کنند.",
                parse_mode="Markdown"
            )
            return

    # ==================== اگر هیچ‌کدام ====================
    # پیام پیش‌فرض فقط در پیوی
    if update.message.chat.type == "private":
        await update.message.reply_text(
            "❓ دستور نامشخص!\n"
            "برای دیدن دستورات بنویس: راهنما"
        )


# =========================
# راه‌اندازی
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
