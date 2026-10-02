#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
🎖️ ربات بازی جنگ جهانی دوم
برای پیام‌رسان بله (Bale)
با سیستم عضویت اجباری
"""

import os
import sqlite3
import random
import logging
import json
from datetime import datetime, timedelta

from telegram import (
    Update, InlineKeyboardButton, InlineKeyboardMarkup,
    ReplyKeyboardMarkup, KeyboardButton
)
from telegram.ext import (
    Application, CommandHandler, CallbackQueryHandler,
    MessageHandler, filters, ContextTypes
)
from telegram.constants import ChatMemberStatus

from keep_alive import keep_alive

# ═══════════════════════════════════════════════════════════════
#  ⚙️ تنظیمات
# ═══════════════════════════════════════════════════════════════
# 🔑 توکن ربات بله رو اینجا بذار 👇
BOT_TOKEN = "152004939:gjvarQqggvlUKNXdDBoJPx-mTNcNGPBu0k8"

DB_FILE = "ww2_game.db"
TURN_HOURS = 24

# 🔒 کانال‌های اجباری
REQUIRED_CHANNELS = [
    {"username": "@Hitlerss1",     "label": "عضویت در کانال اول"},
    {"username": "@WORLDWAR21250", "label": "عضویت در کانال دوم"},
]

logging.basicConfig(
    format='%(asctime)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
log = logging.getLogger(__name__)


# ═══════════════════════════════════════════════════════════════
#  🌍 کشورها (آمار واقعی ۱۹۳۹)
# ═══════════════════════════════════════════════════════════════
COUNTRIES = {
    "germany": {"flag": "🇩🇪", "name": "آلمان", "capital": "برلین", "difficulty": "🟡 متوسط",
        "money": 384, "food": 200, "steel": 23, "oil": 1, "coal": 24, "manpower": 80},
    "uk": {"flag": "🇬🇧", "name": "انگلیس", "capital": "لندن", "difficulty": "🟡 متوسط",
        "money": 287, "food": 180, "steel": 13, "oil": 1, "coal": 14, "manpower": 50},
    "usa": {"flag": "🇺🇸", "name": "آمریکا", "capital": "واشینگتن", "difficulty": "🟢 آسان",
        "money": 869, "food": 450, "steel": 51, "oil": 20, "coal": 21, "manpower": 130},
    "ussr": {"flag": "🇷🇺", "name": "شوروی", "capital": "مسکو", "difficulty": "🟢 آسان",
        "money": 366, "food": 300, "steel": 19, "oil": 3, "coal": 6, "manpower": 170},
    "france": {"flag": "🇫🇷", "name": "فرانسه", "capital": "پاریس", "difficulty": "🔴 سخت",
        "money": 199, "food": 150, "steel": 6, "oil": 0, "coal": 5, "manpower": 45},
    "japan": {"flag": "🇯🇵", "name": "ژاپن", "capital": "توکیو", "difficulty": "🔴 سخت",
        "money": 184, "food": 120, "steel": 6, "oil": 0, "coal": 2, "manpower": 70},
    "italy": {"flag": "🇮🇹", "name": "ایتالیا", "capital": "رم", "difficulty": "🔴 سخت",
        "money": 151, "food": 110, "steel": 2, "oil": 0, "coal": 0, "manpower": 40},
}


# ═══════════════════════════════════════════════════════════════
#  🔬 درخت تحقیقات
# ═══════════════════════════════════════════════════════════════
RESEARCH = {
    "germany": [
        ("Panzer I", 20, 2, 8), ("Panzer II", 30, 3, 10), ("Panzer III", 40, 4, 12),
        ("Panzer IV", 60, 5, 15), ("Panther", 80, 6, 18), ("Tiger I", 100, 8, 22),
        ("Bf 109", 30, 3, 10), ("Fw 190", 70, 5, 16), ("Me 262", 120, 8, 25),
        ("U-Boat VII", 60, 5, 15),
    ],
    "uk": [
        ("Matilda II", 50, 4, 12), ("Churchill", 80, 6, 18),
        ("Spitfire", 40, 3, 12), ("Hurricane", 35, 3, 10),
        ("Lancaster", 80, 6, 20), ("Gloster Meteor", 120, 8, 25),
        ("HMS King George V", 100, 7, 22),
    ],
    "usa": [
        ("M3 Stuart", 40, 4, 10), ("M4 Sherman", 70, 5, 16),
        ("P-40", 35, 3, 10), ("P-51 Mustang", 80, 5, 18),
        ("B-17", 90, 6, 20), ("B-29", 130, 8, 26),
        ("Essex Carrier", 120, 8, 24),
    ],
    "ussr": [
        ("T-26", 30, 3, 9), ("T-34", 70, 5, 17),
        ("KV-1", 80, 6, 19), ("IS-2", 100, 7, 22),
        ("Yak-1", 35, 3, 11), ("La-5", 65, 5, 15), ("MiG-9", 120, 8, 24),
    ],
    "france": [
        ("R-35", 25, 2, 8), ("Char B1", 60, 5, 15),
        ("D.520", 45, 4, 13), ("Richelieu", 100, 7, 22),
    ],
    "japan": [
        ("Type 97", 40, 4, 11), ("Type 1 Chi-He", 60, 5, 14),
        ("A6M Zero", 50, 4, 15), ("Ki-84", 75, 6, 18),
        ("Kikka", 120, 8, 24), ("Yamato", 130, 8, 26),
    ],
    "italy": [
        ("M13/40", 35, 3, 9), ("P26/40", 55, 4, 13),
        ("MC.200", 35, 3, 10), ("MC.202", 60, 5, 14),
    ],
}


# ═══════════════════════════════════════════════════════════════
#  🏗️ پروژه‌های ملی
# ═══════════════════════════════════════════════════════════════
PROJECTS = {
    "autobahn":     {"name": "🛣️ اتوبان رایش",       "money": 50, "steel": 10, "days": 3, "effect": "steel_bonus",    "value": 15},
    "steel_mill":   {"name": "🏭 کارخانه فولاد",      "money": 40, "steel": 15, "days": 4, "effect": "steel_bonus",    "value": 20},
    "refinery":     {"name": "🛢️ پالایشگاه نفت",      "money": 60, "steel": 20, "days": 5, "effect": "oil_bonus",      "value": 30},
    "coal_mine":    {"name": "⛏️ معدن زغال‌سنگ",      "money": 30, "steel": 5,  "days": 3, "effect": "coal_bonus",     "value": 20},
    "railway":      {"name": "🚂 راه‌آهن",             "money": 35, "steel": 8,  "days": 3, "effect": "speed_bonus",    "value": 10},
    "conscription": {"name": "📋 خدمت اجباری",        "money": 40, "steel": 0,  "days": 2, "effect": "manpower_bonus", "value": 50},
    "weapon_lab":   {"name": "🔬 آزمایشگاه تسلیحات",  "money": 50, "steel": 10, "days": 4, "effect": "attack_bonus",   "value": 10},
    "propaganda":   {"name": "📻 تبلیغات",             "money": 30, "steel": 0,  "days": 1, "effect": "morale_bonus",   "value": 10},
    "fortress":     {"name": "🏗️ استحکامات",          "money": 25, "steel": 10, "days": 3, "effect": "defense_bonus",  "value": 30},
    "shipyard":     {"name": "🚢 کشتی‌سازی",           "money": 80, "steel": 25, "days": 6, "effect": "ship_bonus",     "value": 50},
}


# ═══════════════════════════════════════════════════════════════
#  🔒 بررسی عضویت اجباری
# ═══════════════════════════════════════════════════════════════
async def is_user_member(update: Update, ctx: ContextTypes.DEFAULT_TYPE, username: str) -> bool:
    try:
        member = await ctx.bot.get_chat_member(chat_id=username, user_id=update.effective_user.id)
        if member.status in (ChatMemberStatus.MEMBER, ChatMemberStatus.ADMINISTRATOR, ChatMemberStatus.OWNER):
            return True
        return False
    except Exception as e:
        log.warning(f"خطا در چک عضویت {username}: {e}")
        return False


async def check_all_memberships(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    not_joined = []
    for ch in REQUIRED_CHANNELS:
        ok = await is_user_member(update, ctx, ch["username"])
        if not ok:
            not_joined.append(ch)
    return not_joined


def join_message_kb():
    rows = []
    for ch in REQUIRED_CHANNELS:
        username = ch["username"].lstrip("@")
        rows.append([InlineKeyboardButton(
            ch["label"],
            url=f"https://ble.ir/{username}"
        )])
    return InlineKeyboardMarkup(rows)


def join_reply_kb():
    return ReplyKeyboardMarkup(
        [[KeyboardButton("عضو شدم ✅")]],
        resize_keyboard=True,
        one_time_keyboard=False
    )


async def send_join_message(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    text = (
        "🔒 *برای استفاده از بات، در کانال اسپانسر و کانال خودمان عضو شوید.*\n\n"
        f"📢 کانال اول: {REQUIRED_CHANNELS[0]['username']}\n"
        f"📢 کانال دوم: {REQUIRED_CHANNELS[1]['username']}\n\n"
        "پس از عضویت، دکمه *«عضو شدم ✅»* رو بزن."
    )
    await update.message.reply_text(
        text,
        reply_markup=join_message_kb(),
        parse_mode="Markdown"
    )
    await update.message.reply_text(
        "👇 وقتی عضو شدی این دکمه رو بزن:",
        reply_markup=join_reply_kb()
    )


# ═══════════════════════════════════════════════════════════════
#  💾 دیتابیس
# ═══════════════════════════════════════════════════════════════
def init_db():
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("""
        CREATE TABLE IF NOT EXISTS games (
            user_id     INTEGER PRIMARY KEY,
            country     TEXT,
            turn        INTEGER DEFAULT 1,
            game_date   TEXT,
            money       INTEGER, food INTEGER, steel INTEGER,
            oil         INTEGER, coal INTEGER, manpower INTEGER,
            soldiers    INTEGER DEFAULT 0,
            tanks       INTEGER DEFAULT 0,
            planes      INTEGER DEFAULT 0,
            ships       INTEGER DEFAULT 0,
            projects    TEXT DEFAULT '[]',
            completed_projects TEXT DEFAULT '[]',
            research    TEXT DEFAULT '[]',
            allies      TEXT DEFAULT '[]',
            wars        TEXT DEFAULT '[]',
            sanctions   TEXT DEFAULT '[]',
            last_turn   TEXT,
            created_at  TEXT
        )
    """)
    conn.commit()
    conn.close()


def db():
    conn = sqlite3.connect(DB_FILE)
    conn.row_factory = sqlite3.Row
    return conn


def get_game(user_id):
    conn = db()
    row = conn.execute("SELECT * FROM games WHERE user_id=?", (user_id,)).fetchone()
    conn.close()
    return dict(row) if row else None


def save_game(user_id, **fields):
    if not fields:
        return
    cols = ", ".join(f"{k}=?" for k in fields)
    vals = list(fields.values()) + [user_id]
    conn = db()
    conn.execute(f"UPDATE games SET {cols} WHERE user_id=?", vals)
    conn.commit()
    conn.close()


# ═══════════════════════════════════════════════════════════════
#  🕹️ منطق بازی
# ═══════════════════════════════════════════════════════════════
def start_new_game(user_id, country_key):
    c = COUNTRIES[country_key]
    conn = db()
    conn.execute("DELETE FROM games WHERE user_id=?", (user_id,))
    conn.execute("""
        INSERT INTO games (user_id, country, turn, game_date,
            money, food, steel, oil, coal, manpower,
            last_turn, created_at)
        VALUES (?, ?, 1, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (user_id, country_key, "1939-09-01",
          c["money"], c["food"], c["steel"], c["oil"], c["coal"], c["manpower"],
          datetime.utcnow().isoformat(), datetime.utcnow().isoformat()))
    conn.commit()
    conn.close()


def process_turn(user_id):
    g = get_game(user_id)
    if not g:
        return None
    country = COUNTRIES[g["country"]]
    completed = json.loads(g["completed_projects"] or "[]")
    projects = json.loads(g["projects"] or "[]")
    bonus = {"steel": 1.0, "oil": 1.0, "coal": 1.0, "manpower": 1.0}
    for p_key in completed:
        p = PROJECTS.get(p_key)
        if not p:
            continue
        eff, val = p["effect"], p["value"] / 100.0
        if eff == "steel_bonus":       bonus["steel"]    += val
        elif eff == "oil_bonus":       bonus["oil"]      += val
        elif eff == "coal_bonus":      bonus["coal"]     += val
        elif eff == "manpower_bonus":  bonus["manpower"] += val

    new_money    = g["money"]    + country["money"]
    new_food     = g["food"]     + country["food"]
    new_steel    = g["steel"]    + int(country["steel"]    * bonus["steel"])
    new_oil      = g["oil"]      + int(country["oil"]      * bonus["oil"])
    new_coal     = g["coal"]     + int(country["coal"]     * bonus["coal"])
    new_manpower = g["manpower"] + int(country["manpower"] * bonus["manpower"])

    still_building = []
    newly_done = []
    for p_key in projects:
        if ":" in p_key:
            key, days = p_key.split(":")
            days = int(days) - 1
            if days <= 0:
                newly_done.append(key)
            else:
                still_building.append(f"{key}:{days}")
        else:
            still_building.append(p_key)
    completed.extend(newly_done)

    old_date = datetime.strptime(g["game_date"], "%Y-%m-%d")
    new_date = old_date + timedelta(days=1)

    save_game(user_id,
        turn=g["turn"] + 1,
        game_date=new_date.strftime("%Y-%m-%d"),
        money=new_money, food=new_food, steel=new_steel,
        oil=new_oil, coal=new_coal, manpower=new_manpower,
        projects=json.dumps(still_building),
        completed_projects=json.dumps(completed),
        last_turn=datetime.utcnow().isoformat())
    return {"newly_done": newly_done, "date": new_date.strftime("%Y-%m-%d")}


def check_and_run_turn(user_id):
    g = get_game(user_id)
    if not g:
        return None
    try:
        last = datetime.fromisoformat(g["last_turn"])
    except Exception:
        return None
    if datetime.utcnow() - last >= timedelta(hours=TURN_HOURS):
        return process_turn(user_id)
    return None


def compute_army_power(g, mode="attack"):
    completed = json.loads(g["completed_projects"] or "[]")
    attack_bonus = 1.0
    defense_bonus = 1.0
    for p_key in completed:
        p = PROJECTS.get(p_key)
        if not p:
            continue
        if p["effect"] == "attack_bonus":
            attack_bonus += p["value"] / 100
        elif p["effect"] == "defense_bonus":
            defense_bonus += p["value"] / 100
    atk = g["soldiers"]*5 + g["tanks"]*15 + g["planes"]*12 + g["ships"]*20
    dfn = g["soldiers"]*8 + g["tanks"]*10 + g["planes"]*6  + g["ships"]*18
    if mode == "attack":
        return int(atk * attack_bonus)
    return int(dfn * defense_bonus)


def fmt(n):
    return f"{n:,}"


# ═══════════════════════════════════════════════════════════════
#  🎨 کیبوردها
# ═══════════════════════════════════════════════════════════════
def main_menu_kb():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("💰 اقتصاد", callback_data="eco"),
         InlineKeyboardButton("⚔️ ارتش", callback_data="army")],
        [InlineKeyboardButton("🔬 تحقیقات", callback_data="res"),
         InlineKeyboardButton("🏗️ پروژه‌ها", callback_data="proj")],
        [InlineKeyboardButton("🤝 دیپلماسی", callback_data="dip"),
         InlineKeyboardButton("📦 تجارت", callback_data="trade")],
        [InlineKeyboardButton("🎯 حمله", callback_data="attack"),
         InlineKeyboardButton("📊 آمار کامل", callback_data="stats")],
        [InlineKeyboardButton("🔄 نوبت بعدی", callback_data="next_turn")],
    ])


def back_kb():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("🔙 بازگشت به منو", callback_data="menu")]
    ])


def countries_kb():
    rows = []
    for key, c in COUNTRIES.items():
        rows.append([InlineKeyboardButton(
            f"{c['flag']} {c['name']} — {c['difficulty']}",
            callback_data=f"pick_{key}"
        )])
    return InlineKeyboardMarkup(rows)


def render_dashboard(g):
    c = COUNTRIES[g["country"]]
    return (
        f"{c['flag']} *{c['name']}* — {g['game_date']} (نوبت {g['turn']})\n"
        f"━━━━━━━━━━━━━━━━━━━━━━\n"
        f"💰 پول: {fmt(g['money'])}\n"
        f"🍞 غذا: {fmt(g['food'])}\n"
        f"⚙️ فولاد: {fmt(g['steel'])}\n"
        f"🛢️ نفت: {fmt(g['oil'])}\n"
        f"🪨 زغال: {fmt(g['coal'])}\n"
        f"👥 نیرو: {fmt(g['manpower'])}\n"
        f"━━━━━━━━━━━━━━━━━━━━━━\n"
        f"🪖 سرباز: {fmt(g['soldiers'])}\n"
        f"🛡️ تانک: {fmt(g['tanks'])}\n"
        f"✈️ هواپیما: {fmt(g['planes'])}\n"
        f"🚢 کشتی: {fmt(g['ships'])}\n"
    )


# ═══════════════════════════════════════════════════════════════
#  📝 هندلرها
# ═══════════════════════════════════════════════════════════════
async def cmd_start(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    not_joined = await check_all_memberships(update, ctx)
    if not_joined:
        await send_join_message(update, ctx)
        return
    uid = update.effective_user.id
    g = get_game(uid)
    if g:
        await update.message.reply_text(
            f"👋 دوباره خوش اومدی!\n"
            f"کشورت: {COUNTRIES[g['country']]['flag']} {COUNTRIES[g['country']]['name']}",
            reply_markup=main_menu_kb()
        )
        return
    await update.message.reply_text(
        "🎖️ به بازی *جنگ جهانی دوم* خوش آمدی!\n\n"
        "یکی از ۷ کشور اصلی رو انتخاب کن و از سال ۱۹۳۹ شروع کن.\n"
        "هدف: پیروزی در جنگ!",
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("🎮 بازی جدید", callback_data="newgame")],
            [InlineKeyboardButton("📖 راهنما", callback_data="help")],
        ]),
        parse_mode="Markdown"
    )


async def cmd_menu(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    not_joined = await check_all_memberships(update, ctx)
    if not_joined:
        await send_join_message(update, ctx)
        return
    uid = update.effective_user.id
    g = get_game(uid)
    if not g:
        await update.message.reply_text("اول بازی جدید بساز: /start")
        return
    result = check_and_run_turn(uid)
    g = get_game(uid)
    text = render_dashboard(g)
    if result and result["newly_done"]:
        done_names = [PROJECTS[k]["name"] for k in result["newly_done"]]
        text = "✅ پروژه‌ها تکمیل شد: " + ", ".join(done_names) + "\n\n" + text
    await update.message.reply_text(text, reply_markup=main_menu_kb(), parse_mode="Markdown")


async def on_joined_check(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    not_joined = await check_all_memberships(update, ctx)
    if not_joined:
        names = ", ".join(ch["username"] for ch in not_joined)
        await update.message.reply_text(
            f"❌ هنوز در این کانال‌ها عضو نشدی:\n{names}\n\n"
            "لطفاً اول عضو شو، بعد دکمه رو بزن.",
            reply_markup=join_reply_kb()
        )
        return
    await update.message.reply_text(
        "✅ عضویتت تأیید شد!\n\nحالا می‌تونی بازی رو شروع کنی 👇",
        reply_markup=ReplyKeyboardMarkup(
            [[KeyboardButton("🎮 منو")]],
            resize_keyboard=True
        )
    )
    uid = update.effective_user.id
    g = get_game(uid)
    if g:
        await update.message.reply_text(render_dashboard(g), reply_markup=main_menu_kb(), parse_mode="Markdown")
    else:
        await update.message.reply_text(
            "🎖️ برای شروع:",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("🎮 بازی جدید", callback_data="newgame")],
                [InlineKeyboardButton("📖 راهنما", callback_data="help")],
            ])
        )


# ─── Callback Handlers ──────────────────────────────────────
async def cb_newgame(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()
    await q.edit_message_text(
        "🌍 *کشورت رو انتخاب کن:*\n\n"
        "🟢 آسان: منابع زیاد، امن\n"
        "🟡 متوسط: متعادل\n"
        "🔴 سخت: منابع کم، تهدید فوری",
        reply_markup=countries_kb(),
        parse_mode="Markdown"
    )


async def cb_pick_country(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()
    uid = q.from_user.id
    key = q.data.replace("pick_", "")
    c = COUNTRIES[key]
    start_new_game(uid, key)
    g = get_game(uid)
    await q.edit_message_text(
        f"✅ کشور انتخاب شد: {c['flag']} *{c['name']}*\n\n"
        f"{render_dashboard(g)}\n\n"
        f"از اینجا بازی شروع می‌شه!",
        reply_markup=main_menu_kb(),
        parse_mode="Markdown"
    )


async def cb_menu(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()
    g = get_game(q.from_user.id)
    if not g:
        await q.edit_message_text("بازی پیدا نشد. /start رو بزن.")
        return
    await q.edit_message_text(render_dashboard(g), reply_markup=main_menu_kb(), parse_mode="Markdown")


async def cb_eco(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()
    g = get_game(q.from_user.id)
    c = COUNTRIES[g["country"]]
    text = (
        f"💰 *اقتصاد {c['name']}*\n"
        f"━━━━━━━━━━━━━━━━━━━━━━\n"
        f"💰 پول: {fmt(g['money'])}  (+{fmt(c['money'])}/نوبت)\n"
        f"🍞 غذا: {fmt(g['food'])}  (+{fmt(c['food'])}/نوبت)\n"
        f"⚙️ فولاد: {fmt(g['steel'])}  (+{fmt(c['steel'])}/نوبت)\n"
        f"🛢️ نفت: {fmt(g['oil'])}  (+{fmt(c['oil'])}/نوبت)\n"
        f"🪨 زغال: {fmt(g['coal'])}  (+{fmt(c['coal'])}/نوبت)\n"
        f"👥 نیرو: {fmt(g['manpower'])}  (+{fmt(c['manpower'])}/نوبت)\n"
    )
    kb = InlineKeyboardMarkup([
        [InlineKeyboardButton("🏗️ ساخت پروژه", callback_data="proj")],
        [InlineKeyboardButton("🔙 بازگشت", callback_data="menu")],
    ])
    await q.edit_message_text(text, reply_markup=kb, parse_mode="Markdown")


async def cb_army(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()
    g = get_game(q.from_user.id)
    atk = compute_army_power(g, "attack")
    dfn = compute_army_power(g, "defense")
    text = (
        f"⚔️ *ارتش*\n"
        f"━━━━━━━━━━━━━━━━━━━━━━\n"
        f"🪖 سرباز: {fmt(g['soldiers'])}\n"
        f"🛡️ تانک: {fmt(g['tanks'])}\n"
        f"✈️ هواپیما: {fmt(g['planes'])}\n"
        f"🚢 کشتی: {fmt(g['ships'])}\n"
        f"━━━━━━━━━━━━━━━━━━━━━━\n"
        f"⚔️ قدرت حمله: {fmt(atk)}\n"
        f"🛡️ قدرت دفاع: {fmt(dfn)}\n\n"
        f"*سربازگیری:*\n"
        f"• ۱ سرباز = ۱۰ پول\n"
        f"• ۱ تانک = ۳۰ پول + ۵ فولاد + ۲ نفت\n"
        f"• ۱ هواپیما = ۲۵ پول + ۳ فولاد + ۳ نفت\n"
        f"• ۱ کشتی = ۸۰ پول + ۱۰ فولاد + ۵ نفت"
    )
    kb = InlineKeyboardMarkup([
        [InlineKeyboardButton("🪖 ۱ سرباز", callback_data="buy_soldier"),
         InlineKeyboardButton("🛡️ ۱ تانک", callback_data="buy_tank")],
        [InlineKeyboardButton("✈️ ۱ هواپیما", callback_data="buy_plane"),
         InlineKeyboardButton("🚢 ۱ کشتی", callback_data="buy_ship")],
        [InlineKeyboardButton("🔙 بازگشت", callback_data="menu")],
    ])
    await q.edit_message_text(text, reply_markup=kb, parse_mode="Markdown")


async def cb_buy(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()
    uid = q.from_user.id
    g = get_game(uid)
    action = q.data
    msg = ""
    if action == "buy_soldier":
        if g["money"] >= 10 and g["manpower"] >= 1:
            save_game(uid, money=g["money"]-10, manpower=g["manpower"]-1, soldiers=g["soldiers"]+1)
            msg = "✅ ۱ سرباز اضافه شد."
        else:
            msg = "❌ منابع کافی نداری."
    elif action == "buy_tank":
        if g["money"] >= 30 and g["steel"] >= 5 and g["oil"] >= 2:
            save_game(uid, money=g["money"]-30, steel=g["steel"]-5, oil=g["oil"]-2, tanks=g["tanks"]+1)
            msg = "✅ ۱ تانک ساخته شد."
        else:
            msg = "❌ منابع کافی نداری."
    elif action == "buy_plane":
        if g["money"] >= 25 and g["steel"] >= 3 and g["oil"] >= 3:
            save_game(uid, money=g["money"]-25, steel=g["steel"]-3, oil=g["oil"]-3, planes=g["planes"]+1)
            msg = "✅ ۱ هواپیما ساخته شد."
        else:
            msg = "❌ منابع کافی نداری."
    elif action == "buy_ship":
        if g["money"] >= 80 and g["steel"] >= 10 and g["oil"] >= 5:
            save_game(uid, money=g["money"]-80, steel=g["steel"]-10, oil=g["oil"]-5, ships=g["ships"]+1)
            msg = "✅ ۱ کشتی ساخته شد."
        else:
            msg = "❌ منابع کافی نداری."
    await q.answer(msg, show_alert=True)
    await cb_army(update, ctx)


async def cb_res(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()
    g = get_game(q.from_user.id)
    tree = RESEARCH.get(g["country"], [])
    unlocked = json.loads(g["research"] or "[]")
    lines = [f"🔬 *درخت تحقیقات — {COUNTRIES[g['country']]['name']}*\n"]
    rows = []
    for name, cost, days, power in tree:
        if name in unlocked:
            lines.append(f"✅ {name} (قدرت {power})")
        else:
            lines.append(f"🔒 {name} — {cost} پول (قدرت {power})")
            rows.append([InlineKeyboardButton(f"🔬 {name} ({cost}💰)", callback_data=f"res_{name}")])
    rows.append([InlineKeyboardButton("🔙 بازگشت", callback_data="menu")])
    await q.edit_message_text("\n".join(lines), reply_markup=InlineKeyboardMarkup(rows), parse_mode="Markdown")


async def cb_research(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()
    uid = q.from_user.id
    name = q.data.replace("res_", "")
    g = get_game(uid)
    tree = RESEARCH.get(g["country"], [])
    for n, cost, days, power in tree:
        if n == name:
            if g["money"] < cost:
                await q.answer("❌ پول کافی نداری.", show_alert=True)
                return
            unlocked = json.loads(g["research"] or "[]")
            if name in unlocked:
                await q.answer("قبلاً تحقیق شده.", show_alert=True)
                return
            unlocked.append(name)
            save_game(uid, money=g["money"]-cost, research=json.dumps(unlocked))
            await q.answer(f"✅ {name} تحقیق شد!", show_alert=True)
            await cb_res(update, ctx)
            return


async def cb_proj(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()
    g = get_game(q.from_user.id)
    completed = json.loads(g["completed_projects"] or "[]")
    building = json.loads(g["projects"] or "[]")
    lines = ["🏗️ *پروژه‌های ملی*\n"]
    rows = []
    for key, p in PROJECTS.items():
        if key in completed:
            lines.append(f"✅ {p['name']} (تکمیل)")
        else:
            building_now = any(b.split(":")[0] == key for b in building)
            if building_now:
                lines.append(f"🔨 {p['name']} (در حال ساخت)")
            else:
                lines.append(f"🆕 {p['name']} — {p['money']}💰 + {p['steel']}⚙️ ({p['days']} روز)")
                rows.append([InlineKeyboardButton(f"🏗️ {p['name']}", callback_data=f"build_{key}")])
    rows.append([InlineKeyboardButton("🔙 بازگشت", callback_data="menu")])
    await q.edit_message_text("\n".join(lines), reply_markup=InlineKeyboardMarkup(rows), parse_mode="Markdown")


async def cb_build(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()
    uid = q.from_user.id
    key = q.data.replace("build_", "")
    g = get_game(uid)
    p = PROJECTS[key]
    if g["money"] < p["money"] or g["steel"] < p["steel"]:
        await q.answer(f"❌ نیاز: {p['money']} پول + {p['steel']} فولاد", show_alert=True)
        return
    projects = json.loads(g["projects"] or "[]")
    if any(x.split(":")[0] == key for x in projects):
        await q.answer("در حال ساخت است.", show_alert=True)
        return
    projects.append(f"{key}:{p['days']}")
    save_game(uid, money=g["money"]-p["money"], steel=g["steel"]-p["steel"], projects=json.dumps(projects))
    await q.answer(f"✅ شروع ساخت {p['name']}", show_alert=True)
    await cb_proj(update, ctx)


async def cb_dip(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()
    g = get_game(q.from_user.id)
    text = (
        f"🤝 *دیپلماسی*\n"
        f"━━━━━━━━━━━━━━━━━━━━━━\n"
        f"متحدین: {', '.join(json.loads(g['allies'] or '[]')) or 'هیچ'}\n"
        f"در جنگ با: {', '.join(json.loads(g['wars'] or '[]')) or 'هیچ'}\n"
        f"تحریم‌شده: {', '.join(json.loads(g['sanctions'] or '[]')) or 'هیچ'}\n\n"
        f"⚠️ دیپلماسی پیشرفته در نسخه بعدی."
    )
    await q.edit_message_text(text, reply_markup=back_kb(), parse_mode="Markdown")


async def cb_trade(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()
    await q.edit_message_text(
        "📦 *تجارت*\n\n"
        "🇸🇪 سوئد: آهن\n"
        "🇷🇴 رومانی: نفت\n"
        "🇪🇸 اسپانیا: تنگستن\n"
        "🇹🇷 ترکیه: کروم\n\n"
        "⚠️ سیستم تجارت کامل در نسخه بعدی.",
        reply_markup=back_kb(), parse_mode="Markdown"
    )


async def cb_attack(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()
    g = get_game(q.from_user.id)
    enemies = [k for k in COUNTRIES if k != g["country"]]
    rows = []
    for e in enemies[:5]:
        c = COUNTRIES[e]
        rows.append([InlineKeyboardButton(f"⚔️ {c['flag']} {c['name']}", callback_data=f"atk_{e}")])
    rows.append([InlineKeyboardButton("🔙 بازگشت", callback_data="menu")])
    await q.edit_message_text(
        f"🎯 *هدف حمله:*\n\n⚔️ قدرت حمله تو: {fmt(compute_army_power(g, 'attack'))}",
        reply_markup=InlineKeyboardMarkup(rows), parse_mode="Markdown"
    )


async def cb_do_attack(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()
    uid = q.from_user.id
    g = get_game(uid)
    my_atk = compute_army_power(g, "attack")
    enemy_def = random.randint(50, 200)
    if my_atk > enemy_def:
        loss = random.randint(0, max(1, g["soldiers"] // 5))
        save_game(uid, soldiers=max(0, g["soldiers"] - loss))
        result = f"🏆 *پیروزی!*\n\nحمله: {fmt(my_atk)}\nدفاع: {fmt(enemy_def)}\nتلفات: {loss}"
    else:
        loss = random.randint(1, max(2, g["soldiers"] // 3))
        save_game(uid, soldiers=max(0, g["soldiers"] - loss))
        result = f"💀 *شکست!*\n\nحمله: {fmt(my_atk)}\nدفاع: {fmt(enemy_def)}\nتلفات: {loss}"
    await q.edit_message_text(result, reply_markup=back_kb(), parse_mode="Markdown")


async def cb_stats(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()
    g = get_game(q.from_user.id)
    await q.edit_message_text(render_dashboard(g), reply_markup=back_kb(), parse_mode="Markdown")


async def cb_next_turn(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()
    uid = q.from_user.id
    result = process_turn(uid)
    g = get_game(uid)
    msg = "⏭️ نوبت جدید!\n\n" + render_dashboard(g)
    if result and result["newly_done"]:
        names = [PROJECTS[k]["name"] for k in result["newly_done"]]
        msg = "✅ تکمیل: " + ", ".join(names) + "\n\n" + msg
    await q.edit_message_text(msg, reply_markup=main_menu_kb(), parse_mode="Markdown")


async def cb_help(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()
    await q.edit_message_text(
        "📖 *راهنما*\n"
        "━━━━━━━━━━━━━━━━━━━━━━\n"
        "1️⃣ کشور انتخاب کن\n"
        "2️⃣ منابع تولید می‌شه\n"
        "3️⃣ ارتش بساز، تحقیق کن\n"
        "4️⃣ حمله کن\n"
        "5️⃣ هدف: پیروزی!\n\n"
        "🔄 «نوبت بعدی» = روز بعد",
        reply_markup=back_kb(), parse_mode="Markdown"
    )


# ═══════════════════════════════════════════════════════════════
#  🚀 main
# ═══════════════════════════════════════════════════════════════
def main():
    init_db()
    if "توکن" in BOT_TOKEN or not BOT_TOKEN:
        print("❌ توکن ربات تنظیم نشده!")
        return
    keep_alive()
    app = Application.builder().token(BOT_TOKEN).base_url("https://tapi.bale.ai/bot").build()

    app.add_handler(CommandHandler("start", cmd_start))
    app.add_handler(CommandHandler("menu", cmd_menu))

    # 🔒 هندلر دکمه «عضو شدم»
    app.add_handler(MessageHandler(
        filters.TEXT & filters.Regex("^عضو شدم ✅$"),
        on_joined_check
    ))
    # هندلر دکمه «منو»
    app.add_handler(MessageHandler(
        filters.TEXT & filters.Regex("^🎮 منو$"),
        cmd_menu
    ))

    app.add_handler(CallbackQueryHandler(cb_newgame, pattern="^newgame$"))
    app.add_handler(CallbackQueryHandler(cb_pick_country, pattern="^pick_"))
    app.add_handler(CallbackQueryHandler(cb_menu, pattern="^menu$"))
    app.add_handler(CallbackQueryHandler(cb_eco, pattern="^eco$"))
    app.add_handler(CallbackQueryHandler(cb_army, pattern="^army$"))
    app.add_handler(CallbackQueryHandler(cb_buy, pattern="^buy_"))
    app.add_handler(CallbackQueryHandler(cb_res, pattern="^res$"))
    app.add_handler(CallbackQueryHandler(cb_research, pattern="^res_"))
    app.add_handler(CallbackQueryHandler(cb_proj, pattern="^proj$"))
    app.add_handler(CallbackQueryHandler(cb_build, pattern="^build_"))
    app.add_handler(CallbackQueryHandler(cb_dip, pattern="^dip$"))
    app.add_handler(CallbackQueryHandler(cb_trade, pattern="^trade$"))
    app.add_handler(CallbackQueryHandler(cb_attack, pattern="^attack$"))
    app.add_handler(CallbackQueryHandler(cb_do_attack, pattern="^atk_"))
    app.add_handler(CallbackQueryHandler(cb_stats, pattern="^stats$"))
    app.add_handler(CallbackQueryHandler(cb_next_turn, pattern="^next_turn$"))
    app.add_handler(CallbackQueryHandler(cb_help, pattern="^help$"))

    print("🎖️ ربات در حال اجراست...")
    app.run_polling()


if __name__ == "__main__":
    main()
