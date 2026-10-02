#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
🎖️ ربات بازی جنگ جهانی دوم — نسخه کامل
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
    MessageHandler, filters, ContextTypes, ConversationHandler
)
from telegram.constants import ChatMemberStatus

from keep_alive import keep_alive

# ═══════════════════════════════════════════════════════════════
#  ⚙️ تنظیمات
# ═══════════════════════════════════════════════════════════════
# 🔑 توکن ربات بله رو اینجا بذار 👇
BOT_TOKEN = "152004939:gjvarQqggvlUKNXdDBoJPx-mTNcNGPBu0k8"
BALE_API = "https://tapi.bale.ai/bot"

DB_FILE = "ww2_game.db"
TURN_HOURS = 1  # هر ۱ ساعت یه نوبت

REQUIRED_CHANNELS = [
    {"username": "@Hitlerss1",     "label": "عضویت در کانال اول"},
    {"username": "@WORLDWAR21250", "label": "عضویت در کانال دوم"},
]

ADMIN_IDS = [1429506412, 1618371215]

logging.basicConfig(format='%(asctime)s - %(levelname)s - %(message)s', level=logging.INFO)
log = logging.getLogger(__name__)


# ═══════════════════════════════════════════════════════════════
#  🌍 کشورها (۱۲ کشور — آمار ۱۹۳۹)
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
    "china": {"flag": "🇨🇳", "name": "چین", "capital": "چونگ‌کینگ", "difficulty": "🔴 سخت",
        "money": 120, "food": 250, "steel": 1, "oil": 0, "coal": 3, "manpower": 200},
    "poland": {"flag": "🇵🇱", "name": "لهستان", "capital": "ورشو", "difficulty": "🔴 سخت",
        "money": 80, "food": 100, "steel": 2, "oil": 0, "coal": 4, "manpower": 35},
    "canada": {"flag": "🇨🇦", "name": "کانادا", "capital": "اتاوا", "difficulty": "🟢 آسان",
        "money": 110, "food": 180, "steel": 5, "oil": 2, "coal": 6, "manpower": 25},
    "australia": {"flag": "🇦🇺", "name": "استرالیا", "capital": "کانبرا", "difficulty": "🟢 آسان",
        "money": 95, "food": 160, "steel": 3, "oil": 0, "coal": 4, "manpower": 20},
    "brazil": {"flag": "🇧🇷", "name": "برزیل", "capital": "ریو", "difficulty": "🟢 آسان",
        "money": 75, "food": 200, "steel": 2, "oil": 0, "coal": 1, "manpower": 60},
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
    "china": [("Type 88", 25, 2, 8), ("Type 24", 40, 4, 11)],
    "poland": [("7TP", 30, 3, 9), ("PZL.37", 35, 3, 10)],
    "canada": [("Ram", 45, 4, 12)],
    "australia": [("Sentinel", 40, 4, 11)],
    "brazil": [("M3 Stuart", 40, 4, 10)],
}


# ═══════════════════════════════════════════════════════════════
#  🏗️ پروژه‌های ملی
# ═══════════════════════════════════════════════════════════════
PROJECTS = {
    "autobahn":     {"name": "🛣️ اتوبان",             "money": 50, "steel": 10, "days": 3, "effect": "steel_bonus",    "value": 15},
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
#  📊 آمار واقعی نظامی هر کشور
# ═══════════════════════════════════════════════════════════════
COUNTRY_UNITS = {
    "germany": {
        "soldier": {"name": "Wehrmacht",  "attack": 6,  "defense": 8,  "cost": {"money": 10, "manpower": 1}},
        "tank":    {"name": "Panzer IV",  "attack": 15, "defense": 10, "cost": {"money": 30, "steel": 5, "oil": 2}},
        "plane":   {"name": "Bf 109",     "attack": 12, "defense": 6,  "cost": {"money": 25, "steel": 3, "oil": 3}},
        "ship":    {"name": "Bismarck",   "attack": 22, "defense": 20, "cost": {"money": 90, "steel": 12, "oil": 5}},
    },
    "uk": {
        "soldier": {"name": "Tommy",      "attack": 5,  "defense": 9,  "cost": {"money": 10, "manpower": 1}},
        "tank":    {"name": "Churchill",  "attack": 14, "defense": 12, "cost": {"money": 32, "steel": 5, "oil": 2}},
        "plane":   {"name": "Spitfire",   "attack": 13, "defense": 7,  "cost": {"money": 26, "steel": 3, "oil": 3}},
        "ship":    {"name": "King George","attack": 21, "defense": 22, "cost": {"money": 95, "steel": 13, "oil": 5}},
    },
    "usa": {
        "soldier": {"name": "G.I.",       "attack": 6,  "defense": 8,  "cost": {"money": 10, "manpower": 1}},
        "tank":    {"name": "M4 Sherman", "attack": 13, "defense": 11, "cost": {"money": 28, "steel": 5, "oil": 2}},
        "plane":   {"name": "P-51",       "attack": 14, "defense": 7,  "cost": {"money": 28, "steel": 3, "oil": 3}},
        "ship":    {"name": "Essex",      "attack": 24, "defense": 20, "cost": {"money": 100, "steel": 14, "oil": 6}},
    },
    "ussr": {
        "soldier": {"name": "Red Army",   "attack": 7,  "defense": 7,  "cost": {"money": 8, "manpower": 1}},
        "tank":    {"name": "T-34",       "attack": 16, "defense": 12, "cost": {"money": 26, "steel": 5, "oil": 2}},
        "plane":   {"name": "Yak-9",      "attack": 12, "defense": 7,  "cost": {"money": 24, "steel": 3, "oil": 3}},
        "ship":    {"name": "Kirov",      "attack": 18, "defense": 16, "cost": {"money": 80, "steel": 11, "oil": 5}},
    },
    "japan": {
        "soldier": {"name": "IJA",        "attack": 8,  "defense": 6,  "cost": {"money": 9, "manpower": 1}},
        "tank":    {"name": "Type 97",    "attack": 11, "defense": 9,  "cost": {"money": 26, "steel": 4, "oil": 2}},
        "plane":   {"name": "A6M Zero",   "attack": 15, "defense": 5,  "cost": {"money": 28, "steel": 3, "oil": 4}},
        "ship":    {"name": "Yamato",     "attack": 26, "defense": 24, "cost": {"money": 110, "steel": 15, "oil": 7}},
    },
    "italy": {
        "soldier": {"name": "Bersaglieri","attack": 5,  "defense": 7,  "cost": {"money": 9, "manpower": 1}},
        "tank":    {"name": "M13/40",     "attack": 10, "defense": 8,  "cost": {"money": 24, "steel": 4, "oil": 2}},
        "plane":   {"name": "MC.202",     "attack": 11, "defense": 6,  "cost": {"money": 24, "steel": 3, "oil": 3}},
        "ship":    {"name": "Littorio",   "attack": 19, "defense": 17, "cost": {"money": 85, "steel": 12, "oil": 5}},
    },
    "france": {
        "soldier": {"name": "Poilu",      "attack": 5,  "defense": 9,  "cost": {"money": 10, "manpower": 1}},
        "tank":    {"name": "Char B1",    "attack": 14, "defense": 14, "cost": {"money": 32, "steel": 6, "oil": 2}},
        "plane":   {"name": "D.520",      "attack": 12, "defense": 7,  "cost": {"money": 26, "steel": 3, "oil": 3}},
        "ship":    {"name": "Richelieu",  "attack": 20, "defense": 21, "cost": {"money": 90, "steel": 13, "oil": 5}},
    },
    "china": {
        "soldier": {"name": "NRA",        "attack": 4,  "defense": 7,  "cost": {"money": 6, "manpower": 1}},
        "tank":    {"name": "Type 88",    "attack": 8,  "defense": 7,  "cost": {"money": 22, "steel": 4, "oil": 2}},
        "plane":   {"name": "Hawk III",   "attack": 9,  "defense": 5,  "cost": {"money": 22, "steel": 3, "oil": 3}},
        "ship":    {"name": "Ning Hai",   "attack": 12, "defense": 10, "cost": {"money": 60, "steel": 8, "oil": 4}},
    },
    "poland": {
        "soldier": {"name": "WP",         "attack": 5,  "defense": 8,  "cost": {"money": 8, "manpower": 1}},
        "tank":    {"name": "7TP",        "attack": 9,  "defense": 8,  "cost": {"money": 22, "steel": 4, "oil": 2}},
        "plane":   {"name": "PZL.37",     "attack": 10, "defense": 5,  "cost": {"money": 22, "steel": 3, "oil": 3}},
        "ship":    {"name": "Grom",       "attack": 12, "defense": 10, "cost": {"money": 60, "steel": 8, "oil": 4}},
    },
    "canada": {
        "soldier": {"name": "Canadian",   "attack": 6,  "defense": 8,  "cost": {"money": 10, "manpower": 1}},
        "tank":    {"name": "Ram",        "attack": 13, "defense": 11, "cost": {"money": 28, "steel": 5, "oil": 2}},
        "plane":   {"name": "Hurricane",  "attack": 11, "defense": 6,  "cost": {"money": 24, "steel": 3, "oil": 3}},
        "ship":    {"name": "Tribal",     "attack": 15, "defense": 14, "cost": {"money": 70, "steel": 9, "oil": 4}},
    },
    "australia": {
        "soldier": {"name": "AIF",        "attack": 6,  "defense": 7,  "cost": {"money": 10, "manpower": 1}},
        "tank":    {"name": "Sentinel",   "attack": 11, "defense": 10, "cost": {"money": 26, "steel": 5, "oil": 2}},
        "plane":   {"name": "Boomerang",  "attack": 10, "defense": 6,  "cost": {"money": 24, "steel": 3, "oil": 3}},
        "ship":    {"name": "Perth",      "attack": 14, "defense": 13, "cost": {"money": 68, "steel": 9, "oil": 4}},
    },
    "brazil": {
        "soldier": {"name": "FEB",        "attack": 5,  "defense": 7,  "cost": {"money": 8, "manpower": 1}},
        "tank":    {"name": "M3 Stuart",  "attack": 10, "defense": 8,  "cost": {"money": 24, "steel": 4, "oil": 2}},
        "plane":   {"name": "P-40",       "attack": 10, "defense": 5,  "cost": {"money": 22, "steel": 3, "oil": 3}},
        "ship":    {"name": "Bahia",      "attack": 11, "defense": 10, "cost": {"money": 60, "steel": 8, "oil": 4}},
    },
}


# ═══════════════════════════════════════════════════════════════
#  📅 رویدادهای تاریخی (تاریخ دقیق)
# ═══════════════════════════════════════════════════════════════
HISTORIC_EVENTS = {
    "1939-09-01": "🇩🇪 آلمان به لهستان حمله کرد — شروع جنگ جهانی دوم",
    "1939-09-03": "🇬🇧🇫🇷 انگلیس و فرانسه به آلمان اعلام جنگ کردن",
    "1939-11-30": "🇷🇺 شوروی به فنلاند حمله کرد — جنگ زمستانی",
    "1940-04-09": "🇩🇪 آلمان به دانمارک و نروژ حمله کرد",
    "1940-05-10": "🇩🇪 آلمان به فرانسه و کشورهای کم‌ارتفاع حمله کرد",
    "1940-06-22": "🇫🇷 فرانسه تسلیم شد",
    "1940-07-10": "✈️ نبرد بریتانیا شروع شد",
    "1941-06-22": "🇩🇪 عملیات بارباروسا — حمله به شوروی",
    "1941-12-07": "🇯🇵 حمله به پرل هاربر",
    "1941-12-11": "🇺🇸 آمریکا وارد جنگ شد",
    "1942-06-04": "🌊 نبرد میدوی — شکست ژاپن",
    "1942-08-23": "🔥 نبرد استالینگراد شروع شد",
    "1943-02-02": "🏆 پیروزی شوروی در استالینگراد",
    "1944-06-06": "🚢 عملیات اورلرد — D-Day",
    "1945-02-04": "🤝 کنفرانس یالتا",
    "1945-04-30": "💀 خودکشی هیتلر",
    "1945-05-08": "🏁 تسلیم آلمان — پایان جنگ در اروپا",
    "1945-08-06": "☢️ بمباران اتمی هیروشیما",
    "1945-08-09": "☢️ بمباران اتمی ناکازاکی",
    "1945-09-02": "🏁 تسلیم ژاپن — پایان جنگ جهانی دوم",
}

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
            game_date   TEXT DEFAULT '1939-09-01',
            money       INTEGER, food INTEGER, steel INTEGER,
            oil         INTEGER, coal INTEGER, manpower INTEGER,
            soldiers    INTEGER DEFAULT 0,
            tanks       INTEGER DEFAULT 0,
            planes      INTEGER DEFAULT 0,
            ships       INTEGER DEFAULT 0,
            tax_rate    INTEGER DEFAULT 20,
            happiness   INTEGER DEFAULT 70,
            unrest      INTEGER DEFAULT 0,
            projects    TEXT DEFAULT '[]',
            completed_projects TEXT DEFAULT '[]',
            research    TEXT DEFAULT '[]',
            allies      TEXT DEFAULT '[]',
            wars        TEXT DEFAULT '[]',
            sanctions   TEXT DEFAULT '[]',
            colonies    TEXT DEFAULT '[]',
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


def find_player_by_country(country_key):
    conn = db()
    row = conn.execute("SELECT user_id FROM games WHERE country=?", (country_key,)).fetchone()
    conn.close()
    return row["user_id"] if row else None


def get_all_players():
    conn = db()
    rows = conn.execute("SELECT * FROM games").fetchall()
    conn.close()
    return [dict(r) for r in rows]


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


def parse_game_date(date_str):
    """تبدیل تاریخ بازی به datetime"""
    try:
        return datetime.strptime(date_str, "%Y-%m-%d")
    except:
        return datetime(1939, 9, 1)


def format_game_date(dt):
    """نمایش قشنگ تاریخ"""
    months_fa = ["فروردین", "اردیبهشت", "خرداد", "تیر", "مرداد", "شهریور",
                 "مهر", "آبان", "آذر", "دی", "بهمن", "اسفند"]
    # از میلادی استفاده می‌کنیم با ماه انگلیسی
    months_en = ["ژانویه", "فوریه", "مارس", "آپریل", "مه", "ژوئن",
                 "ژوئیه", "اوت", "سپتامبر", "اکتبر", "نوامبر", "دسامبر"]
    return f"{dt.day} {months_en[dt.month-1]} {dt.year}"


def advance_game_date(game_date, days=3):
    """تاریخ بازی رو N روز جلو ببر"""
    dt = parse_game_date(game_date)
    return (dt + timedelta(days=days)).strftime("%Y-%m-%d")


def get_events_between(date_from, date_to):
    """رویدادهای تاریخی بین دو تاریخ"""
    events = []
    dt_from = parse_game_date(date_from)
    dt_to = parse_game_date(date_to)
    current = dt_from
    while current <= dt_to:
        key = current.strftime("%Y-%m-%d")
        if key in HISTORIC_EVENTS:
            events.append(HISTORIC_EVENTS[key])
        current += timedelta(days=1)
    return events


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
        if eff == "steel_bonus":
            bonus["steel"] += val
        elif eff == "oil_bonus":
            bonus["oil"] += val
        elif eff == "coal_bonus":
            bonus["coal"] += val
        elif eff == "manpower_bonus":
            bonus["manpower"] += val

    tax_mult = g["tax_rate"] / 20.0
    new_money    = g["money"]    + int(country["money"] * tax_mult)
    new_food     = g["food"]     + country["food"]
    new_steel    = g["steel"]    + int(country["steel"]    * bonus["steel"])
    new_oil      = g["oil"]      + int(country["oil"]      * bonus["oil"])
    new_coal     = g["coal"]     + int(country["coal"]     * bonus["coal"])
    new_manpower = g["manpower"] + int(country["manpower"] * bonus["manpower"])

    # رضایت
    new_happiness = g["happiness"]
    if g["tax_rate"] > 25:
        new_happiness -= (g["tax_rate"] - 25) // 2
    elif g["tax_rate"] < 15:
        new_happiness += 2
    new_happiness = max(0, min(100, new_happiness))
    new_unrest = 100 - new_happiness

    # پروژه‌ها
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

    # تاریخ
    old_date = g["game_date"]
    new_date = advance_game_date(old_date, 3)
    events = get_events_between(old_date, new_date)

    save_game(user_id,
        turn=g["turn"] + 1,
        game_date=new_date,
        money=new_money, food=new_food, steel=new_steel,
        oil=new_oil, coal=new_coal, manpower=new_manpower,
        happiness=new_happiness, unrest=new_unrest,
        projects=json.dumps(still_building),
        completed_projects=json.dumps(completed),
        last_turn=datetime.utcnow().isoformat())

    return {
        "newly_done": newly_done,
        "date": new_date,
        "date_pretty": format_game_date(parse_game_date(new_date)),
        "events": events,
    }


def compute_army_power(g, mode="attack"):
    units = COUNTRY_UNITS.get(g["country"], COUNTRY_UNITS["germany"])
    atk = 0
    dfn = 0
    for unit, field in [("soldier", "soldiers"), ("tank", "tanks"),
                         ("plane", "planes"), ("ship", "ships")]:
        u = units.get(unit, {})
        count = g.get(field, 0)
        atk += count * u.get("attack", 5)
        dfn += count * u.get("defense", 5)

    completed = json.loads(g["completed_projects"] or "[]")
    atk_bonus = 1.0
    def_bonus = 1.0
    for p_key in completed:
        p = PROJECTS.get(p_key)
        if not p:
            continue
        if p["effect"] == "attack_bonus":
            atk_bonus += p["value"] / 100
        elif p["effect"] == "defense_bonus":
            def_bonus += p["value"] / 100

    if mode == "attack":
        return int(atk * atk_bonus)
    return int(dfn * def_bonus)


def fmt(n):
    return f"{n:,}"


async def notify_admins(ctx, text):
    for aid in ADMIN_IDS:
        try:
            await ctx.bot.send_message(aid, text, parse_mode="Markdown")
        except Exception as e:
            log.warning(f"خطا در ارسال به ادمین {aid}: {e}")


# ═══════════════════════════════════════════════════════════════
#  🔒 عضویت اجباری
# ═══════════════════════════════════════════════════════════════
async def is_user_member(update, ctx, username):
    try:
        member = await ctx.bot.get_chat_member(chat_id=username, user_id=update.effective_user.id)
        if member.status in (ChatMemberStatus.MEMBER, ChatMemberStatus.ADMINISTRATOR, ChatMemberStatus.OWNER):
            return True
        return False
    except Exception as e:
        log.warning(f"خطا در چک عضویت {username}: {e}")
        return False


async def check_all_memberships(update, ctx):
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
        rows.append([InlineKeyboardButton(ch["label"], url=f"https://ble.ir/{username}")])
    return InlineKeyboardMarkup(rows)


def join_reply_kb():
    return ReplyKeyboardMarkup(
        [[KeyboardButton("عضو شدم ✅")]],
        resize_keyboard=True, one_time_keyboard=False
    )


async def send_join_message(update, ctx):
    text = (
        "🔒 *برای استفاده از بات، در کانال اسپانسر و کانال خودمان عضو شوید.*\n\n"
        f"📢 کانال اول: {REQUIRED_CHANNELS[0]['username']}\n"
        f"📢 کانال دوم: {REQUIRED_CHANNELS[1]['username']}\n\n"
        "پس از عضویت، دکمه *«عضو شدم ✅»* رو بزن."
    )
    await update.message.reply_text(text, reply_markup=join_message_kb(), parse_mode="Markdown")
    await update.message.reply_text("👇 وقتی عضو شدی این دکمه رو بزن:", reply_markup=join_reply_kb())


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
         InlineKeyboardButton("🕵️ جاسوسی", callback_data="spy")],
        [InlineKeyboardButton("💵 مالیات", callback_data="tax"),
         InlineKeyboardButton("🏛️ امور کشور", callback_data="internal")],
        [InlineKeyboardButton("📊 آمار کامل", callback_data="stats")],
    ])


def back_kb():
    return InlineKeyboardMarkup([[InlineKeyboardButton("🔙 بازگشت به منو", callback_data="menu")]])


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
    dt = parse_game_date(g["game_date"])
    date_str = format_game_date(dt)
    return (
        f"{c['flag']} *{c['name']}* — {date_str} (نوبت {g['turn']})\n"
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
        f"━━━━━━━━━━━━━━━━━━━━━━\n"
        f"😊 رضایت: {g['happiness']}%  |  💵 مالیات: {g['tax_rate']}%"
    )


# ═══════════════════════════════════════════════════════════════
#  📝 هندلرهای اصلی
# ═══════════════════════════════════════════════════════════════
async def cmd_start(update, ctx):
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
        "یکی از ۱۲ کشور رو انتخاب کن و از ۱ سپتامبر ۱۹۳۹ شروع کن.\n\n"
        "📅 هر ۱ ساعت = ۱ نوبت خودکار\n"
        "📅 هر نوبت = ۳ روز بازی جلو میره\n"
        "🏁 کل بازی = ۳۰ روز واقعی",
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("🎮 بازی جدید", callback_data="newgame")],
            [InlineKeyboardButton("📖 راهنما", callback_data="help")],
        ]),
        parse_mode="Markdown"
    )


async def cmd_menu(update, ctx):
    not_joined = await check_all_memberships(update, ctx)
    if not_joined:
        await send_join_message(update, ctx)
        return
    uid = update.effective_user.id
    g = get_game(uid)
    if not g:
        await update.message.reply_text("اول بازی جدید بساز: /start")
        return
    await update.message.reply_text(render_dashboard(g), reply_markup=main_menu_kb(), parse_mode="Markdown")


async def on_joined_check(update, ctx):
    not_joined = await check_all_memberships(update, ctx)
    if not_joined:
        names = ", ".join(ch["username"] for ch in not_joined)
        await update.message.reply_text(
            f"❌ هنوز عضو نشدی:\n{names}\n\nلطفاً اول عضو شو.",
            reply_markup=join_reply_kb()
        )
        return
    await update.message.reply_text(
        "✅ عضویت تأیید شد!\n\nحالا بازی رو شروع کن 👇",
        reply_markup=ReplyKeyboardMarkup([[KeyboardButton("🎮 منو")]], resize_keyboard=True)
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


# ═══════════════════════════════════════════════════════════════
#  📋 کال‌بک‌های عمومی
# ═══════════════════════════════════════════════════════════════
async def cb_newgame(update, ctx):
    q = update.callback_query
    await q.answer()
    await q.edit_message_text(
        "🌍 *کشورت رو انتخاب کن:*\n\n🟢 آسان  |  🟡 متوسط  |  🔴 سخت",
        reply_markup=countries_kb(), parse_mode="Markdown"
    )


async def cb_pick_country(update, ctx):
    q = update.callback_query
    await q.answer()
    uid = q.from_user.id
    key = q.data.replace("pick_", "")
    c = COUNTRIES[key]
    start_new_game(uid, key)
    g = get_game(uid)
    await q.edit_message_text(
        f"✅ کشور انتخاب شد: {c['flag']} *{c['name']}*\n\n{render_dashboard(g)}",
        reply_markup=main_menu_kb(), parse_mode="Markdown"
    )
    await notify_admins(ctx, f"🎮 کاربر [{uid}] کشور *{c['name']}* رو انتخاب کرد.")


async def cb_menu(update, ctx):
    q = update.callback_query
    await q.answer()
    g = get_game(q.from_user.id)
    if not g:
        await q.edit_message_text("بازی پیدا نشد. /start رو بزن.")
        return
    await q.edit_message_text(render_dashboard(g), reply_markup=main_menu_kb(), parse_mode="Markdown")


async def cb_stats(update, ctx):
    q = update.callback_query
    await q.answer()
    g = get_game(q.from_user.id)
    await q.edit_message_text(render_dashboard(g), reply_markup=back_kb(), parse_mode="Markdown")


async def cb_help(update, ctx):
    q = update.callback_query
    await q.answer()
    await q.edit_message_text(
        "📖 *راهنما*\n━━━━━━━━━━━━━━━━━━━━━━\n"
        "1️⃣ کشور انتخاب کن\n"
        "2️⃣ منابع تولید می‌شه\n"
        "3️⃣ ارتش بساز، تحقیق کن\n"
        "4️⃣ مالیات تنظیم کن\n"
        "5️⃣ حمله و جاسوسی\n"
        "6️⃣ هدف: پیروزی!\n\n"
        "📅 هر ۱ ساعت یه نوبت خودکار میاد.",
        reply_markup=back_kb(), parse_mode="Markdown"
    )

# ═══════════════════════════════════════════════════════════════
#  💰 اقتصاد
# ═══════════════════════════════════════════════════════════════
async def cb_eco(update, ctx):
    q = update.callback_query
    await q.answer()
    g = get_game(q.from_user.id)
    c = COUNTRIES[g["country"]]
    tax_mult = g["tax_rate"] / 20.0
    text = (
        f"💰 *اقتصاد {c['name']}*\n━━━━━━━━━━━━━━━━━━━━━━\n"
        f"💰 پول: {fmt(g['money'])} (+{int(c['money']*tax_mult)}/نوبت)\n"
        f"🍞 غذا: {fmt(g['food'])} (+{c['food']}/نوبت)\n"
        f"⚙️ فولاد: {fmt(g['steel'])} (+{c['steel']}/نوبت)\n"
        f"🛢️ نفت: {fmt(g['oil'])} (+{c['oil']}/نوبت)\n"
        f"🪨 زغال: {fmt(g['coal'])} (+{c['coal']}/نوبت)\n"
        f"👥 نیرو: {fmt(g['manpower'])} (+{c['manpower']}/نوبت)\n"
        f"━━━━━━━━━━━━━━━━━━━━━━\n"
        f"💵 مالیات: {g['tax_rate']}%  |  😊 رضایت: {g['happiness']}%"
    )
    kb = InlineKeyboardMarkup([
        [InlineKeyboardButton("💵 تغییر مالیات", callback_data="tax")],
        [InlineKeyboardButton("🏗️ ساخت پروژه", callback_data="proj")],
        [InlineKeyboardButton("🔙 بازگشت", callback_data="menu")],
    ])
    await q.edit_message_text(text, reply_markup=kb, parse_mode="Markdown")


# ═══════════════════════════════════════════════════════════════
#  💵 مالیات
# ═══════════════════════════════════════════════════════════════
TAX_INPUT = 10


async def cb_tax(update, ctx):
    q = update.callback_query
    await q.answer()
    g = get_game(q.from_user.id)
    await q.edit_message_text(
        f"💵 *مالیات*\n━━━━━━━━━━━━━━━━━━━━━━\n"
        f"الان: {g['tax_rate']}%\n"
        f"رضایت: {g['happiness']}%\n\n"
        f"عددی بین ۰ تا ۵۰ بفرست.\n"
        f"بالای ۲۵٪ = نارضایتی\n"
        f"زیر ۱۵٪ = رضایت بیشتر",
        parse_mode="Markdown",
        reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("❌ انصراف", callback_data="menu")]])
    )
    return TAX_INPUT


async def tax_set(update, ctx):
    try:
        rate = int(update.message.text.strip())
        if not (0 <= rate <= 50):
            raise ValueError
    except:
        await update.message.reply_text("❌ عدد بین ۰ تا ۵۰ بفرست.")
        return TAX_INPUT
    uid = update.effective_user.id
    g = get_game(uid)
    save_game(uid, tax_rate=rate)
    await update.message.reply_text(f"✅ مالیات شد {rate}%", reply_markup=main_menu_kb())
    await notify_admins(ctx, f"💵 کاربر [{uid}] مالیات رو {rate}% کرد.")
    return ConversationHandler.END


# ═══════════════════════════════════════════════════════════════
#  ⚔️ ارتش — خرید گروهی
# ═══════════════════════════════════════════════════════════════
BUY_QTY = 20


async def cb_army(update, ctx):
    q = update.callback_query
    await q.answer()
    uid = q.from_user.id
    g = get_game(uid)
    units = COUNTRY_UNITS.get(g["country"], COUNTRY_UNITS["germany"])
    atk = compute_army_power(g, "attack")
    dfn = compute_army_power(g, "defense")
    text = (
        f"⚔️ *ارتش {COUNTRIES[g['country']]['name']}*\n"
        f"━━━━━━━━━━━━━━━━━━━━━━\n"
        f"🪖 {units['soldier']['name']}: {fmt(g['soldiers'])}\n"
        f"🛡️ {units['tank']['name']}: {fmt(g['tanks'])}\n"
        f"✈️ {units['plane']['name']}: {fmt(g['planes'])}\n"
        f"🚢 {units['ship']['name']}: {fmt(g['ships'])}\n"
        f"━━━━━━━━━━━━━━━━━━━━━━\n"
        f"⚔️ حمله: {fmt(atk)}  |  🛡️ دفاع: {fmt(dfn)}\n\n"
        f"*قیمت‌ها:*"
    )
    kb = InlineKeyboardMarkup([
        [InlineKeyboardButton("🪖 خرید سرباز", callback_data="buy_soldier"),
         InlineKeyboardButton("🛡️ خرید تانک", callback_data="buy_tank")],
        [InlineKeyboardButton("✈️ خرید هواپیما", callback_data="buy_plane"),
         InlineKeyboardButton("🚢 خرید کشتی", callback_data="buy_ship")],
        [InlineKeyboardButton("🔙 بازگشت", callback_data="menu")],
    ])
    await q.edit_message_text(text, reply_markup=kb, parse_mode="Markdown")


async def buy_start(update, ctx):
    q = update.callback_query
    await q.answer()
    kind = q.data.replace("buy_", "")
    ctx.user_data["buy_kind"] = kind
    uid = q.from_user.id
    g = get_game(uid)
    units = COUNTRY_UNITS.get(g["country"], {})
    unit_info = units.get(kind, {})
    name = unit_info.get("name", kind)
    cost = unit_info.get("cost", {})
    cost_str = " + ".join(f"{v}{'💰' if k=='money' else '⚙️' if k=='steel' else '🛢️' if k=='oil' else '👥'}" for k, v in cost.items())
    await q.edit_message_text(
        f"🔢 چندتا *{name}* می‌خوای بخری؟\n\n"
        f"قیمت هر واحد: {cost_str}\n\n"
        f"عدد رو بفرست:",
        parse_mode="Markdown",
        reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("❌ انصراف", callback_data="army")]])
    )
    return BUY_QTY


async def buy_qty(update, ctx):
    uid = update.effective_user.id
    try:
        qty = int(update.message.text.strip())
        if qty <= 0:
            raise ValueError
    except:
        await update.message.reply_text("❌ فقط یه عدد مثبت بفرست.")
        return BUY_QTY

    g = get_game(uid)
    kind = ctx.user_data.get("buy_kind")
    units = COUNTRY_UNITS.get(g["country"], {})
    m = units.get(kind, {})
    cost = m.get("cost", {})

    need_money = cost.get("money", 0) * qty
    need_steel = cost.get("steel", 0) * qty
    need_oil   = cost.get("oil", 0) * qty
    need_man   = cost.get("manpower", 0) * qty

    if (g["money"] < need_money or g["steel"] < need_steel
        or g["oil"] < need_oil or g["manpower"] < need_man):
        await update.message.reply_text(
            f"❌ منابع کافی نداری!\n\n"
            f"نیاز: {need_money}💰 + {need_steel}⚙️ + {need_oil}🛢️ + {need_man}👥\n"
            f"داری: {g['money']}💰 + {g['steel']}⚙️ + {g['oil']}🛢️ + {g['manpower']}👥"
        )
        return ConversationHandler.END

    field_map = {"soldier": "soldiers", "tank": "tanks", "plane": "planes", "ship": "ships"}
    new_val = g[field_map[kind]] + qty

    save_game(uid,
        money=g["money"] - need_money,
        steel=g["steel"] - need_steel,
        oil=g["oil"] - need_oil,
        manpower=g["manpower"] - need_man,
        **{field_map[kind]: new_val})

    await update.message.reply_text(
        f"✅ *{qty} {m['name']}* ساخته شد!\n\n"
        f"هزینه: {need_money}💰 + {need_steel}⚙️ + {need_oil}🛢️ + {need_man}👥",
        parse_mode="Markdown",
        reply_markup=main_menu_kb()
    )
    await notify_admins(ctx, f"⚔️ [{uid}] {qty} {m['name']} خرید.")
    return ConversationHandler.END


# ═══════════════════════════════════════════════════════════════
#  🔬 تحقیقات
# ═══════════════════════════════════════════════════════════════
async def cb_res(update, ctx):
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
            lines.append(f"🔒 {name} — {cost}💰 (قدرت {power})")
            rows.append([InlineKeyboardButton(f"🔬 {name} ({cost}💰)", callback_data=f"res_{name}")])
    rows.append([InlineKeyboardButton("🔙 بازگشت", callback_data="menu")])
    await q.edit_message_text("\n".join(lines), reply_markup=InlineKeyboardMarkup(rows), parse_mode="Markdown")


async def cb_research(update, ctx):
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
            await notify_admins(ctx, f"🔬 [{uid}] {name} رو تحقیق کرد.")
            await cb_res(update, ctx)
            return


# ═══════════════════════════════════════════════════════════════
#  🏗️ پروژه‌ها
# ═══════════════════════════════════════════════════════════════
async def cb_proj(update, ctx):
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
            b = any(x.split(":")[0] == key for x in building)
            if b:
                lines.append(f"🔨 {p['name']} (در حال ساخت)")
            else:
                lines.append(f"🆕 {p['name']} — {p['money']}💰 + {p['steel']}⚙️ ({p['days']} روز)")
                rows.append([InlineKeyboardButton(f"🏗️ {p['name']}", callback_data=f"build_{key}")])
    rows.append([InlineKeyboardButton("🔙 بازگشت", callback_data="menu")])
    await q.edit_message_text("\n".join(lines), reply_markup=InlineKeyboardMarkup(rows), parse_mode="Markdown")


async def cb_build(update, ctx):
    q = update.callback_query
    await q.answer()
    uid = q.from_user.id
    key = q.data.replace("build_", "")
    g = get_game(uid)
    p = PROJECTS[key]
    if g["money"] < p["money"] or g["steel"] < p["steel"]:
        await q.answer(f"❌ نیاز: {p['money']}💰 + {p['steel']}⚙️", show_alert=True)
        return
    projects = json.loads(g["projects"] or "[]")
    if any(x.split(":")[0] == key for x in projects):
        await q.answer("در حال ساخت است.", show_alert=True)
        return
    projects.append(f"{key}:{p['days']}")
    save_game(uid, money=g["money"]-p["money"], steel=g["steel"]-p["steel"], projects=json.dumps(projects))
    await q.answer(f"✅ {p['name']} شروع شد ({p['days']} روز)", show_alert=True)
    await notify_admins(ctx, f"🏗️ [{uid}] پروژه {p['name']} رو شروع کرد.")
    await cb_proj(update, ctx)


# ═══════════════════════════════════════════════════════════════
#  🏛️ امور کشور
# ═══════════════════════════════════════════════════════════════
async def cb_internal(update, ctx):
    q = update.callback_query
    await q.answer()
    g = get_game(q.from_user.id)
    text = (
        f"🏛️ *امور کشور*\n━━━━━━━━━━━━━━━━━━━━━━\n"
        f"😊 رضایت مردم: {g['happiness']}%\n"
        f"🔥 نارضایتی: {g['unrest']}%\n"
    )
    if g["happiness"] < 30:
        text += "\n⚠️ *مردم در حال اعتراضن!*"
    elif g["happiness"] < 50:
        text += "\n⚠️ نارضایتی در حال رشد."
    else:
        text += "\n✅ وضعیت آرامه."
    kb = InlineKeyboardMarkup([
        [InlineKeyboardButton("📢 سخنرانی (۱۰۰💰 → +۱۰ رضایت)", callback_data="speech")],
        [InlineKeyboardButton("🚔 سرکوب (۵۰💰 → -۲۰ نارضایتی)", callback_data="suppress")],
        [InlineKeyboardButton("🔙 بازگشت", callback_data="menu")],
    ])
    await q.edit_message_text(text, reply_markup=kb, parse_mode="Markdown")


async def cb_speech(update, ctx):
    q = update.callback_query
    await q.answer()
    uid = q.from_user.id
    g = get_game(uid)
    if g["money"] < 100:
        await q.answer("❌ ۱۰۰ پول لازمه.", show_alert=True)
        return
    new_hap = min(100, g["happiness"] + 10)
    save_game(uid, money=g["money"]-100, happiness=new_hap, unrest=100-new_hap)
    await q.answer("✅ سخنرانی موفق بود! +۱۰ رضایت", show_alert=True)
    await cb_internal(update, ctx)


async def cb_suppress(update, ctx):
    q = update.callback_query
    await q.answer()
    uid = q.from_user.id
    g = get_game(uid)
    if g["money"] < 50:
        await q.answer("❌ ۵۰ پول لازمه.", show_alert=True)
        return
    new_hap = max(0, g["happiness"] - 20)
    save_game(uid, money=g["money"]-50, happiness=new_hap, unrest=100-new_hap)
    await q.answer("✅ اعتراضات سرکوب شد. -۲۰ رضایت", show_alert=True)
    await notify_admins(ctx, f"🚔 [{uid}] اعتراضات رو سرکوب کرد.")
    await cb_internal(update, ctx)
    

# ═══════════════════════════════════════════════════════════════
#  🎯 حمله — انتخاب دستی تجهیزات
# ═══════════════════════════════════════════════════════════════
ATTACK_TARGET, ATTACK_FORCE, ATTACK_FORCE_QTY = range(50, 53)


async def cb_attack(update, ctx):
    q = update.callback_query
    await q.answer()
    g = get_game(q.from_user.id)
    enemies = [k for k in COUNTRIES if k != g["country"]]
    rows = []
    for e in enemies:
        c = COUNTRIES[e]
        rows.append([InlineKeyboardButton(f"⚔️ {c['flag']} {c['name']}", callback_data=f"atk_{e}")])
    rows.append([InlineKeyboardButton("❌ انصراف", callback_data="menu")])
    await q.edit_message_text(
        f"🎯 *حمله — هدف رو انتخاب کن:*\n\n"
        f"⚔️ قدرت حمله تو: {fmt(compute_army_power(g, 'attack'))}",
        reply_markup=InlineKeyboardMarkup(rows), parse_mode="Markdown"
    )
    return ATTACK_TARGET


async def attack_target(update, ctx):
    q = update.callback_query
    await q.answer()
    target = q.data.replace("atk_", "")
    ctx.user_data["target"] = target
    ctx.user_data["force"] = {"soldiers": 0, "tanks": 0, "planes": 0, "ships": 0}
    c = COUNTRIES[target]
    await q.edit_message_text(
        f"🎯 هدف: {c['flag']} *{c['name']}*\n\n"
        f"نیروهات رو مشخص کن. روی هر واحد بزن تا تعداد بپرسه:",
        reply_markup=attack_force_kb(ctx.user_data["force"]),
        parse_mode="Markdown"
    )
    return ATTACK_FORCE


def attack_force_kb(force):
    return InlineKeyboardMarkup([
        [InlineKeyboardButton(f"🪖 سرباز: {force['soldiers']}", callback_data="af_pick_soldiers"),
         InlineKeyboardButton(f"🛡️ تانک: {force['tanks']}", callback_data="af_pick_tanks")],
        [InlineKeyboardButton(f"✈️ هواپیما: {force['planes']}", callback_data="af_pick_planes"),
         InlineKeyboardButton(f"🚢 کشتی: {force['ships']}", callback_data="af_pick_ships")],
        [InlineKeyboardButton("🚀 شروع حمله", callback_data="af_go")],
        [InlineKeyboardButton("❌ انصراف", callback_data="menu")],
    ])


async def attack_pick_unit(update, ctx):
    q = update.callback_query
    await q.answer()
    field = q.data.replace("af_pick_", "")
    ctx.user_data["picking_field"] = field
    await q.edit_message_text(
        f"🔢 چند تا *{field}* رو بفرستی؟\n\nعدد بفرست (۰ = انصراف):",
        parse_mode="Markdown",
        reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 برگشت", callback_data="af_back")]])
    )
    return ATTACK_FORCE_QTY


async def attack_force_qty(update, ctx):
    try:
        qty = int(update.message.text.strip())
        if qty < 0:
            raise ValueError
    except:
        await update.message.reply_text("❌ عدد مثبت بفرست.")
        return ATTACK_FORCE_QTY
    uid = update.effective_user.id
    g = get_game(uid)
    field = ctx.user_data.get("picking_field")
    if qty > g[field]:
        await update.message.reply_text(f"❌ نداری! تو {g[field]} تا داری.")
        return ATTACK_FORCE_QTY
    ctx.user_data["force"][field] = qty
    c = COUNTRIES[ctx.user_data["target"]]
    force = ctx.user_data["force"]
    await update.message.reply_text(
        f"🎯 هدف: {c['flag']} *{c['name']}*\n\n"
        f"نیروهای انتخاب‌شده:\n"
        f"🪖 {force['soldiers']}  |  🛡️ {force['tanks']}\n"
        f"✈️ {force['planes']}  |  🚢 {force['ships']}\n\n"
        f"برای ادامه، دکمه «شروع حمله» یا دکمه‌ها رو بزن:",
        parse_mode="Markdown",
        reply_markup=attack_force_kb(force)
    )
    return ATTACK_FORCE


async def af_back(update, ctx):
    q = update.callback_query
    await q.answer()
    c = COUNTRIES[ctx.user_data["target"]]
    await q.edit_message_text(
        f"🎯 هدف: {c['flag']} *{c['name']}*\n\nنیروهات رو تنظیم کن:",
        reply_markup=attack_force_kb(ctx.user_data["force"]),
        parse_mode="Markdown"
    )
    return ATTACK_FORCE


async def attack_go(update, ctx):
    q = update.callback_query
    await q.answer()
    uid = q.from_user.id
    g = get_game(uid)
    force = ctx.user_data.get("force", {})
    total_units = sum(force.values())
    if total_units == 0:
        await q.answer("❌ حداقل یه واحد انتخاب کن.", show_alert=True)
        return ATTACK_FORCE

    units = COUNTRY_UNITS.get(g["country"], {})
    my_atk = (force["soldiers"] * units["soldier"]["attack"] +
              force["tanks"]    * units["tank"]["attack"] +
              force["planes"]   * units["plane"]["attack"] +
              force["ships"]    * units["ship"]["attack"])

    target = ctx.user_data["target"]
    enemy_def = random.randint(50, 300)
    c = COUNTRIES[target]

    if my_atk > enemy_def:
        loss = {f: int(force[f] * random.uniform(0.05, 0.20)) for f in force}
        save_game(uid,
            soldiers=g["soldiers"]-loss["soldiers"],
            tanks=g["tanks"]-loss["tanks"],
            planes=g["planes"]-loss["planes"],
            ships=g["ships"]-loss["ships"])
        result = (
            f"🏆 *پیروزی!*\n\n"
            f"هدف: {c['flag']} {c['name']}\n"
            f"قدرت حمله تو: {fmt(my_atk)}\n"
            f"دفاع دشمن: {fmt(enemy_def)}\n\n"
            f"تلفات:\n🪖 {loss['soldiers']}  🛡️ {loss['tanks']}  ✈️ {loss['planes']}  🚢 {loss['ships']}\n\n"
            f"می‌خوای چیکارش کنی؟"
        )
        kb = InlineKeyboardMarkup([
            [InlineKeyboardButton("🏝️ مستعمره (۵۰٪ تولید)", callback_data=f"colony_{target}")],
            [InlineKeyboardButton("🏴 فتح کامل (۱۰۰٪ تولید)", callback_data=f"conquer_{target}")],
        ])
        await q.edit_message_text(result, reply_markup=kb, parse_mode="Markdown")
    else:
        loss = {f: int(force[f] * random.uniform(0.30, 0.60)) for f in force}
        save_game(uid,
            soldiers=g["soldiers"]-loss["soldiers"],
            tanks=g["tanks"]-loss["tanks"],
            planes=g["planes"]-loss["planes"],
            ships=g["ships"]-loss["ships"])
        result = (
            f"💀 *شکست!*\n\n"
            f"هدف: {c['flag']} {c['name']}\n"
            f"قدرت حمله تو: {fmt(my_atk)}\n"
            f"دفاع دشمن: {fmt(enemy_def)}\n\n"
            f"تلفات سنگین:\n🪖 {loss['soldiers']}  🛡️ {loss['tanks']}  ✈️ {loss['planes']}  🚢 {loss['ships']}"
        )
        await q.edit_message_text(result, reply_markup=main_menu_kb(), parse_mode="Markdown")

    await notify_admins(ctx, f"🎯 [{uid}] به {c['name']} حمله کرد.\nنتیجه: {'پیروزی' if my_atk > enemy_def else 'شکست'}")
    return ConversationHandler.END


async def cb_colony(update, ctx):
    q = update.callback_query
    await q.answer()
    uid = q.from_user.id
    target = q.data.replace("colony_", "")
    g = get_game(uid)
    colonies = json.loads(g["colonies"] or "[]")
    if target not in colonies:
        colonies.append(target)
    save_game(uid, colonies=json.dumps(colonies))
    c = COUNTRIES[target]
    await q.edit_message_text(
        f"🏝️ {c['flag']} {c['name']} مستعمره شد!\n\n+۵۰٪ تولیدش به تو می‌رسه.",
        reply_markup=main_menu_kb(), parse_mode="Markdown"
    )
    await notify_admins(ctx, f"🏝️ [{uid}] {c['name']} رو مستعمره کرد.")


async def cb_conquer(update, ctx):
    q = update.callback_query
    await q.answer()
    uid = q.from_user.id
    target = q.data.replace("conquer_", "")
    c = COUNTRIES[target]
    conn = db()
    conn.execute("DELETE FROM games WHERE country=? AND user_id!=?", (target, uid))
    conn.close()
    await q.edit_message_text(
        f"🏴 {c['flag']} {c['name']} کاملاً فتح شد!",
        reply_markup=main_menu_kb(), parse_mode="Markdown"
    )
    await notify_admins(ctx, f"🏴 [{uid}] {c['name']} رو فتح کامل کرد.")


# ═══════════════════════════════════════════════════════════════
#  🕵️ جاسوسی
# ═══════════════════════════════════════════════════════════════
async def cb_spy(update, ctx):
    q = update.callback_query
    await q.answer()
    g = get_game(q.from_user.id)
    enemies = [k for k in COUNTRIES if k != g["country"]]
    rows = [[InlineKeyboardButton(
        f"🕵️ {COUNTRIES[e]['flag']} {COUNTRIES[e]['name']}",
        callback_data=f"spy_{e}"
    )] for e in enemies]
    rows.append([InlineKeyboardButton("🔙 بازگشت", callback_data="menu")])
    await q.edit_message_text(
        f"🕵️ *جاسوسی*\n\nهزینه: ۵۰💰\nشانس لو رفتن: ۴۰٪\n\nهدف رو انتخاب کن:",
        reply_markup=InlineKeyboardMarkup(rows), parse_mode="Markdown"
    )


async def cb_spy_do(update, ctx):
    q = update.callback_query
    await q.answer()
    uid = q.from_user.id
    target = q.data.replace("spy_", "")
    g = get_game(uid)
    if g["money"] < 50:
        await q.answer("❌ ۵۰ پول لازمه.", show_alert=True)
        return
    save_game(uid, money=g["money"]-50)

    caught = random.random() < 0.40
    if caught:
        result = f"🚨 *لو رفتی!*\n\nجاسوست گیر افتاد و {COUNTRIES[target]['name']} فهمید."
    else:
        target_uid = find_player_by_country(target)
        target_g = get_game(target_uid) if target_uid else None
        if target_g:
            units = COUNTRY_UNITS.get(target, {})
            result = (
                f"✅ *موفق!*\n\n"
                f"اطلاعات {COUNTRIES[target]['flag']} {COUNTRIES[target]['name']}:\n"
                f"💰 {fmt(target_g['money'])}  ⚙️ {fmt(target_g['steel'])}\n"
                f"🪖 {fmt(target_g['soldiers'])}  🛡️ {fmt(target_g['tanks'])}\n"
                f"✈️ {fmt(target_g['planes'])}  🚢 {fmt(target_g['ships'])}"
            )
        else:
            result = f"✅ *موفق!*\n\nاطلاعات {COUNTRIES[target]['flag']} {COUNTRIES[target]['name']} به دست اومد (کشور NPC)."
    await q.edit_message_text(result, reply_markup=main_menu_kb(), parse_mode="Markdown")
    await notify_admins(ctx, f"🕵️ [{uid}] به {COUNTRIES[target]['name']} جاسوسی فرستاد. {'لو رفت' if caught else 'موفق'}")


# ═══════════════════════════════════════════════════════════════
#  🤝 دیپلماسی
# ═══════════════════════════════════════════════════════════════
DIP_TYPES = {
    "ally":   "🤝 اتحاد",
    "peace":  "☮️ صلح",
    "war":    "⚔️ اعلام جنگ",
    "nap":    "🤐 عدم تخاصم",
    "tech":   "🔄 تبادل فناوری",
    "colony": "🏝️ مستعمره کردن",
    "talk":   "💬 مذاکره خصوصی",
}


async def cb_dip(update, ctx):
    q = update.callback_query
    await q.answer()
    g = get_game(q.from_user.id)
    allies = json.loads(g["allies"] or "[]")
    wars = json.loads(g["wars"] or "[]")
    allies_names = ", ".join(COUNTRIES[a]["name"] for a in allies if a in COUNTRIES) or "هیچ"
    wars_names = ", ".join(COUNTRIES[a]["name"] for a in wars if a in COUNTRIES) or "هیچ"
    text = (
        f"🤝 *دیپلماسی*\n━━━━━━━━━━━━━━━━━━━━━━\n"
        f"متحدین: {allies_names}\n"
        f"در جنگ با: {wars_names}"
    )
    kb = InlineKeyboardMarkup([
        [InlineKeyboardButton("🤝 پیشنهاد اتحاد", callback_data="dip_ally")],
        [InlineKeyboardButton("☮️ پیشنهاد صلح", callback_data="dip_peace")],
        [InlineKeyboardButton("⚔️ اعلام جنگ", callback_data="dip_war")],
        [InlineKeyboardButton("🤐 پیمان عدم تخاصم", callback_data="dip_nap")],
        [InlineKeyboardButton("🔄 تبادل فناوری", callback_data="dip_tech")],
        [InlineKeyboardButton("🏝️ مستعمره کردن", callback_data="dip_colony")],
        [InlineKeyboardButton("💬 مذاکره خصوصی", callback_data="dip_talk")],
        [InlineKeyboardButton("🔙 بازگشت", callback_data="menu")],
    ])
    await q.edit_message_text(text, reply_markup=kb, parse_mode="Markdown")


async def dip_pick_target(update, ctx, kind):
    q = update.callback_query
    uid = q.from_user.id
    g = get_game(uid)
    countries = [k for k in COUNTRIES if k != g["country"]]
    rows = []
    for c_key in countries:
        c = COUNTRIES[c_key]
        target_uid = find_player_by_country(c_key)
        marker = " 👤" if target_uid else " 🤖"
        rows.append([InlineKeyboardButton(
            f"{c['flag']} {c['name']}{marker}",
            callback_data=f"dipt_{kind}_{c_key}"
        )])
    rows.append([InlineKeyboardButton("🔙 بازگشت", callback_data="dip")])
    await q.edit_message_text(
        f"🎯 *{DIP_TYPES.get(kind, kind)}* — کشور هدف:\n\n"
        f"👤 = بازیکن  |  🤖 = NPC",
        reply_markup=InlineKeyboardMarkup(rows), parse_mode="Markdown"
    )


async def cb_dip_ally(update, ctx):
    q = update.callback_query
    await q.answer()
    await dip_pick_target(update, ctx, "ally")


async def cb_dip_peace(update, ctx):
    q = update.callback_query
    await q.answer()
    await dip_pick_target(update, ctx, "peace")


async def cb_dip_war(update, ctx):
    q = update.callback_query
    await q.answer()
    await dip_pick_target(update, ctx, "war")


async def cb_dip_nap(update, ctx):
    q = update.callback_query
    await q.answer()
    await dip_pick_target(update, ctx, "nap")


async def cb_dip_tech(update, ctx):
    q = update.callback_query
    await q.answer()
    await dip_pick_target(update, ctx, "tech")


async def cb_dip_colony(update, ctx):
    q = update.callback_query
    await q.answer()
    await dip_pick_target(update, ctx, "colony")


async def cb_dip_talk(update, ctx):
    q = update.callback_query
    await q.answer()
    await dip_pick_target(update, ctx, "talk")


async def cb_dip_confirm(update, ctx):
    q = update.callback_query
    await q.answer()
    uid = q.from_user.id
    parts = q.data.split("_", 2)
    kind = parts[1]
    target_key = parts[2]
    g = get_game(uid)
    c = COUNTRIES[target_key]

    if kind == "war":
        wars = json.loads(g["wars"] or "[]")
        if target_key not in wars:
            wars.append(target_key)
            save_game(uid, wars=json.dumps(wars))
        await q.edit_message_text(
            f"⚔️ *جنگ اعلام شد!*\n\n{COUNTRIES[g['country']]['flag']} {COUNTRIES[g['country']]['name']} "
            f"به {c['flag']} {c['name']} اعلام جنگ کرد.",
            reply_markup=back_kb(), parse_mode="Markdown"
        )
        await notify_admins(ctx, f"⚔️ [{uid}] به {c['name']} اعلام جنگ کرد.")
        return

    if kind == "talk":
        target_uid = find_player_by_country(target_key)
        if not target_uid:
            await q.edit_message_text(
                f"🤖 {c['name']} یه NPC هست و مذاکره نمی‌کنه.",
                reply_markup=back_kb(), parse_mode="Markdown"
            )
            return
        ctx.user_data["talk_target"] = target_uid
        ctx.user_data["talk_country"] = target_key
        await q.edit_message_text(
            f"💬 *مذاکره با {c['flag']} {c['name']}*\n\nپیامت رو بنویس:",
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("❌ انصراف", callback_data="dip")]])
        )
        return DIP_TALK_MSG

    target_uid = find_player_by_country(target_key)
    if not target_uid:
        accept = random.random() < 0.5
        if accept:
            if kind == "ally":
                allies = json.loads(g["allies"] or "[]")
                if target_key not in allies:
                    allies.append(target_key)
                save_game(uid, allies=json.dumps(allies))
            await q.edit_message_text(
                f"✅ {c['flag']} {c['name']} پیشنهاد *{DIP_TYPES[kind]}* رو قبول کرد.",
                reply_markup=back_kb(), parse_mode="Markdown"
            )
        else:
            await q.edit_message_text(
                f"❌ {c['flag']} {c['name']} پیشنهاد *{DIP_TYPES[kind]}* رو رد کرد.",
                reply_markup=back_kb(), parse_mode="Markdown"
            )
        return

    try:
        await ctx.bot.send_message(
            target_uid,
            f"📩 *درخواست دیپلماتیک*\n\n"
            f"از: {COUNTRIES[g['country']]['flag']} {COUNTRIES[g['country']]['name']}\n"
            f"نوع: {DIP_TYPES[kind]}\n\nقبول می‌کنی؟",
            parse_mode="Markdown",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("✅ قبول", callback_data=f"dipacc_{kind}_{uid}")],
                [InlineKeyboardButton("❌ رد", callback_data=f"diprej_{kind}_{uid}")],
            ])
        )
    except Exception as e:
        log.warning(f"خطا: {e}")

    await q.edit_message_text(
        f"📤 درخواست *{DIP_TYPES[kind]}* به {c['flag']} {c['name']} فرستاده شد.",
        reply_markup=back_kb(), parse_mode="Markdown"
    )
    await notify_admins(ctx, f"📩 [{uid}] درخواست {DIP_TYPES[kind]} به {c['name']} فرستاد.")


async def cb_dip_accept(update, ctx):
    q = update.callback_query
    await q.answer()
    uid = q.from_user.id
    parts = q.data.split("_", 2)
    kind = parts[1]
    from_uid = int(parts[2])
    g_from = get_game(from_uid)
    g_me = get_game(uid)
    if not g_from or not g_me:
        await q.edit_message_text("خطا.")
        return
    my_country = g_me["country"]
    from_country = g_from["country"]
    if kind == "ally":
        allies_me = json.loads(g_me["allies"] or "[]")
        if from_country not in allies_me:
            allies_me.append(from_country)
            save_game(uid, allies=json.dumps(allies_me))
        allies_from = json.loads(g_from["allies"] or "[]")
        if my_country not in allies_from:
            allies_from.append(my_country)
            save_game(from_uid, allies=json.dumps(allies_from))
    elif kind == "peace":
        wars_me = json.loads(g_me["wars"] or "[]")
        if from_country in wars_me:
            wars_me.remove(from_country)
            save_game(uid, wars=json.dumps(wars_me))
        wars_from = json.loads(g_from["wars"] or "[]")
        if my_country in wars_from:
            wars_from.remove(my_country)
            save_game(from_uid, wars=json.dumps(wars_from))
    await q.edit_message_text(f"✅ درخواست *{DIP_TYPES[kind]}* رو قبول کردی.", parse_mode="Markdown")
    try:
        await ctx.bot.send_message(
            from_uid,
            f"✅ {COUNTRIES[my_country]['flag']} {COUNTRIES[my_country]['name']} درخواست *{DIP_TYPES[kind]}* رو قبول کرد.",
            parse_mode="Markdown"
        )
    except:
        pass
    await notify_admins(ctx, f"✅ [{uid}] درخواست {DIP_TYPES[kind]} از [{from_uid}] رو قبول کرد.")


async def cb_dip_reject(update, ctx):
    q = update.callback_query
    await q.answer()
    uid = q.from_user.id
    parts = q.data.split("_", 2)
    kind = parts[1]
    from_uid = int(parts[2])
    g_me = get_game(uid)
    await q.edit_message_text(f"❌ درخواست *{DIP_TYPES[kind]}* رو رد کردی.", parse_mode="Markdown")
    try:
        await ctx.bot.send_message(
            from_uid,
            f"❌ {COUNTRIES[g_me['country']]['flag']} {COUNTRIES[g_me['country']]['name']} درخواست *{DIP_TYPES[kind]}* رو رد کرد.",
            parse_mode="Markdown"
        )
    except:
        pass


# ─── مذاکره خصوصی ────────────────────────────────────────────
DIP_TALK_MSG = 60


async def dip_talk_send(update, ctx):
    uid = update.effective_user.id
    target_uid = ctx.user_data.get("talk_target")
    target_country = ctx.user_data.get("talk_country")
    if not target_uid:
        await update.message.reply_text("انصراف.")
        return ConversationHandler.END
    g = get_game(uid)
    my_country = COUNTRIES[g["country"]]
    c = COUNTRIES[target_country]
    msg = update.message.text
    try:
        await ctx.bot.send_message(
            target_uid,
            f"💬 *پیام مذاکره*\nاز: {my_country['flag']} {my_country['name']}\n"
            f"━━━━━━━━━━━━━━━━━━━━━━\n{msg}",
            parse_mode="Markdown",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("↩️ پاسخ", callback_data=f"talkreply_{uid}")]
            ])
        )
    except:
        pass
    await update.message.reply_text("✅ پیام فرستاده شد.", reply_markup=main_menu_kb())
    await notify_admins(ctx, f"💬 مذاکره: [{uid}] → [{target_uid}]\n{msg}")
    return ConversationHandler.END


async def cb_talk_reply(update, ctx):
    q = update.callback_query
    await q.answer()
    target_uid = int(q.data.replace("talkreply_", ""))
    g_target = get_game(target_uid)
    if not g_target:
        await q.edit_message_text("کاربر پیدا نشد.")
        return
    ctx.user_data["talk_target"] = target_uid
    ctx.user_data["talk_country"] = g_target["country"]
    await q.edit_message_text(
        "↩️ پیامت رو بنویس:",
        reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("❌ انصراف", callback_data="menu")]])
    )
    return DIP_TALK_MSG
    

# ═══════════════════════════════════════════════════════════════
#  📦 تجارت کامل
# ═══════════════════════════════════════════════════════════════
TRADE_PICK_TYPE, TRADE_PICK_AMOUNT, TRADE_PICK_WANT = range(70, 73)

RESOURCES = {
    "money":    "💰 پول",
    "food":     "🍞 غذا",
    "steel":    "⚙️ فولاد",
    "oil":      "🛢️ نفت",
    "coal":     "🪨 زغال",
    "manpower": "👥 نیرو",
}


async def cb_trade(update, ctx):
    q = update.callback_query
    await q.answer()
    uid = q.from_user.id
    g = get_game(uid)
    text = (
        f"📦 *تجارت*\n━━━━━━━━━━━━━━━━━━━━━━\n"
        f"💰 {fmt(g['money'])}  🍞 {fmt(g['food'])}  ⚙️ {fmt(g['steel'])}\n"
        f"🛢️ {fmt(g['oil'])}  🪨 {fmt(g['coal'])}  👥 {fmt(g['manpower'])}\n\n"
        f"می‌خوای چی صادر کنی؟"
    )
    rows = [[InlineKeyboardButton(label, callback_data=f"tp_{key}")]
            for key, label in RESOURCES.items()]
    rows.append([InlineKeyboardButton("🔙 بازگشت", callback_data="menu")])
    await q.edit_message_text(text, reply_markup=InlineKeyboardMarkup(rows), parse_mode="Markdown")
    return TRADE_PICK_TYPE


async def trade_pick_type(update, ctx):
    q = update.callback_query
    await q.answer()
    res = q.data.replace("tp_", "")
    ctx.user_data["trade_res"] = res
    g = get_game(q.from_user.id)
    await q.edit_message_text(
        f"🔢 چند تا *{RESOURCES[res]}* بدی؟\n\nتو {fmt(g[res])} تا داری.\nعدد بفرست:",
        parse_mode="Markdown",
        reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("❌ انصراف", callback_data="trade")]])
    )
    return TRADE_PICK_AMOUNT


async def trade_pick_amount(update, ctx):
    try:
        amount = int(update.message.text.strip())
        if amount <= 0:
            raise ValueError
    except:
        await update.message.reply_text("❌ عدد مثبت بفرست.")
        return TRADE_PICK_AMOUNT
    uid = update.effective_user.id
    g = get_game(uid)
    res = ctx.user_data["trade_res"]
    if g[res] < amount:
        await update.message.reply_text(f"❌ نداری! تو {g[res]} تا داری.")
        return TRADE_PICK_AMOUNT
    ctx.user_data["trade_amount"] = amount
    await update.message.reply_text(
        f"✅ {amount} {RESOURCES[res]} انتخاب شد.\n\nدر ازای چی می‌خوای؟",
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton(label, callback_data=f"tw_{key}")]
            for key, label in RESOURCES.items()
        ] + [[InlineKeyboardButton("❌ انصراف", callback_data="trade")]])
    )
    return TRADE_PICK_WANT


async def trade_pick_want(update, ctx):
    q = update.callback_query
    await q.answer()
    want = q.data.replace("tw_", "")
    ctx.user_data["trade_want"] = want
    uid = q.from_user.id
    g = get_game(uid)
    countries = [k for k in COUNTRIES if k != g["country"]]
    rows = []
    for c_key in countries:
        c = COUNTRIES[c_key]
        target_uid = find_player_by_country(c_key)
        marker = " 👤" if target_uid else " 🤖"
        rows.append([InlineKeyboardButton(
            f"{c['flag']} {c['name']}{marker}",
            callback_data=f"tt_{c_key}"
        )])
    rows.append([InlineKeyboardButton("🔙 بازگشت", callback_data="menu")])
    await q.edit_message_text("🎯 طرف مقابل رو انتخاب کن:", reply_markup=InlineKeyboardMarkup(rows), parse_mode="Markdown")
    return ConversationHandler.END


async def cb_trade_send(update, ctx):
    q = update.callback_query
    await q.answer()
    target_key = q.data.replace("tt_", "")
    uid = q.from_user.id
    g = get_game(uid)
    res = ctx.user_data.get("trade_res")
    amount = ctx.user_data.get("trade_amount")
    want = ctx.user_data.get("trade_want")
    target_uid = find_player_by_country(target_key)
    c = COUNTRIES[target_key]

    if not target_uid:
        accept = random.random() < 0.6
        if accept:
            new_vals = {res: g[res] - amount, want: g[want] + int(amount * 0.8)}
            save_game(uid, **new_vals)
            await q.edit_message_text(
                f"✅ {c['flag']} {c['name']} معامله رو قبول کرد!\n\n"
                f"{amount} {RESOURCES[res]} دادی، {int(amount*0.8)} {RESOURCES[want]} گرفتی.",
                reply_markup=main_menu_kb(), parse_mode="Markdown"
            )
        else:
            await q.edit_message_text(
                f"❌ {c['flag']} {c['name']} معامله رو رد کرد.",
                reply_markup=back_kb(), parse_mode="Markdown"
            )
        return

    try:
        await ctx.bot.send_message(
            target_uid,
            f"📦 *پیشنهاد تجاری*\n\n"
            f"از: {COUNTRIES[g['country']]['flag']} {COUNTRIES[g['country']]['name']}\n"
            f"می‌ده: {amount} {RESOURCES[res]}\n"
            f"می‌خواد: {amount} {RESOURCES[want]}\n\nقبول می‌کنی؟",
            parse_mode="Markdown",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("✅ قبول", callback_data=f"tradeacc_{uid}_{res}_{want}_{amount}")],
                [InlineKeyboardButton("❌ رد", callback_data=f"traderej_{uid}")],
            ])
        )
    except Exception as e:
        log.warning(f"خطا: {e}")

    await q.edit_message_text(
        f"📤 پیشنهاد به {c['flag']} {c['name']} فرستاده شد.",
        reply_markup=back_kb(), parse_mode="Markdown"
    )


async def cb_trade_accept(update, ctx):
    q = update.callback_query
    await q.answer()
    uid = q.from_user.id
    parts = q.data.split("_")
    from_uid = int(parts[1])
    res = parts[2]
    want = parts[3]
    amount = int(parts[4])
    g_from = get_game(from_uid)
    g_me = get_game(uid)
    if not g_from or not g_me:
        await q.edit_message_text("خطا.")
        return
    if g_from[res] < amount or g_me[want] < amount:
        await q.edit_message_text("❌ یکی از طرفین منابع کافی نداره.")
        return
    save_game(from_uid, **{res: g_from[res] - amount, want: g_from[want] + amount})
    save_game(uid, **{res: g_me[res] + amount, want: g_me[want] - amount})
    await q.edit_message_text("✅ معامله انجام شد!", parse_mode="Markdown")
    try:
        await ctx.bot.send_message(from_uid, f"✅ معامله با {COUNTRIES[g_me['country']]['name']} انجام شد.")
    except:
        pass
    await notify_admins(ctx, f"📦 معامله بین [{uid}] و [{from_uid}]: {amount} {res} → {want}")


async def cb_trade_reject(update, ctx):
    q = update.callback_query
    await q.answer()
    from_uid = int(q.data.replace("traderej_", ""))
    g_me = get_game(q.from_user.id)
    await q.edit_message_text("❌ رد کردی.")
    try:
        await ctx.bot.send_message(from_uid, f"❌ {COUNTRIES[g_me['country']]['name']} معامله رو رد کرد.")
    except:
        pass


# ═══════════════════════════════════════════════════════════════
#  ⏭️ دور بعد فقط برای ادمین
# ═══════════════════════════════════════════════════════════════
async def cmd_next_turn(update, ctx):
    uid = update.effective_user.id
    if uid not in ADMIN_IDS:
        await update.message.reply_text("🚫 فقط ادمین‌ها می‌تونن دور بعد بزنن.")
        return
    players = get_all_players()
    count = 0
    for p in players:
        process_turn(p["user_id"])
        count += 1
    await update.message.reply_text(f"⏭️ نوبت جدید برای {count} بازیکن اجرا شد.")
    await notify_admins(ctx, f"⏭️ ادمین [{uid}] نوبت جدید رو اجرا کرد ({count} بازیکن).")


# ═══════════════════════════════════════════════════════════════
#  👑 پنل ادمین
# ═══════════════════════════════════════════════════════════════
async def cmd_admin(update, ctx):
    uid = update.effective_user.id
    if uid not in ADMIN_IDS:
        await update.message.reply_text("🚫 دسترسی نداری.")
        return
    players = get_all_players()
    text = f"👑 *پنل ادمین*\n━━━━━━━━━━━━━━━━━━━━━━\n👥 بازیکنان: {len(players)}\n\n"
    for p in players[:20]:
        c = COUNTRIES.get(p["country"], {})
        text += f"{c.get('flag','❓')} [{p['user_id']}] — نوبت {p['turn']} — {p['money']}💰\n"
    if len(players) > 20:
        text += f"\n... و {len(players)-20} نفر دیگه"
    await update.message.reply_text(text, parse_mode="Markdown")


async def cmd_give(update, ctx):
    uid = update.effective_user.id
    if uid not in ADMIN_IDS:
        return
    try:
        _, target, field, amount = update.message.text.split()
        target = int(target)
        amount = int(amount)
    except:
        await update.message.reply_text(
            "فرمت: `/give user_id money|steel|oil|coal|food|manpower amount`",
            parse_mode="Markdown"
        )
        return
    g = get_game(target)
    if not g:
        await update.message.reply_text("کاربر پیدا نشد.")
        return
    save_game(target, **{field: g[field] + amount})
    await update.message.reply_text(f"✅ {amount} {field} به [{target}] داده شد.")


async def cmd_players(update, ctx):
    players = get_all_players()
    if not players:
        await update.message.reply_text("هنوز کسی بازی نکرده.")
        return
    text = "🌍 *بازیکنان فعال:*\n━━━━━━━━━━━━━━━━━━━━━━\n"
    for p in players:
        c = COUNTRIES.get(p["country"], {})
        text += f"{c.get('flag','❓')} {c.get('name','?')} — نوبت {p['turn']}\n"
    await update.message.reply_text(text, parse_mode="Markdown")


# ═══════════════════════════════════════════════════════════════
#  🕐 سیستم نوبت خودکار (JobQueue)
# ═══════════════════════════════════════════════════════════════
async def auto_turn_job(context: ContextTypes.DEFAULT_TYPE):
    """هر ۱ ساعت اجرا میشه — نوبت همه بازیکنا رو جلو میبره"""
    players = get_all_players()
    for p in players:
        result = process_turn(p["user_id"])
        if result:
            try:
                # پیام تاریخ جدید + رویدادها
                text = (
                    f"📅 *نوبت جدید!*\n"
                    f"━━━━━━━━━━━━━━━━━━━━━━\n"
                    f"تاریخ: {result['date_pretty']}\n"
                )
                if result["events"]:
                    text += "\n📰 *رویدادهای تاریخی:*\n"
                    for ev in result["events"]:
                        text += f"• {ev}\n"
                if result["newly_done"]:
                    text += "\n✅ *پروژه‌های تکمیل‌شده:*\n"
                    for k in result["newly_done"]:
                        text += f"• {PROJECTS[k]['name']}\n"

                await context.bot.send_message(p["user_id"], text, parse_mode="Markdown")
            except Exception as e:
                log.warning(f"خطا در ارسال پیام نوبت به {p['user_id']}: {e}") 

# ═══════════════════════════════════════════════════════════════
#  🚀 main — راه‌اندازی ربات
# ═══════════════════════════════════════════════════════════════
def main():
    init_db()

    if "توکن" in BOT_TOKEN or not BOT_TOKEN:
        print("❌ توکن ربات تنظیم نشده!")
        return

    keep_alive()

    app = Application.builder().token(BOT_TOKEN).base_url(BALE_API).build()

    # ─── Commands ─────────────────────────────────
    app.add_handler(CommandHandler("start", cmd_start))
    app.add_handler(CommandHandler("menu", cmd_menu))
    app.add_handler(CommandHandler("next_turn", cmd_next_turn))
    app.add_handler(CommandHandler("admin", cmd_admin))
    app.add_handler(CommandHandler("give", cmd_give))
    app.add_handler(CommandHandler("players", cmd_players))

    # ─── عضویت اجباری ─────────────────────────────
    app.add_handler(MessageHandler(
        filters.TEXT & filters.Regex("^عضو شدم ✅$"),
        on_joined_check
    ))
    app.add_handler(MessageHandler(
        filters.TEXT & filters.Regex("^🎮 منو$"),
        cmd_menu
    ))

    # ─── ConversationHandler: خرید ارتش ───────────
    buy_conv = ConversationHandler(
        entry_points=[
            CallbackQueryHandler(buy_start, pattern="^buy_(soldier|tank|plane|ship)$"),
        ],
        states={
            BUY_QTY: [MessageHandler(filters.TEXT & ~filters.COMMAND, buy_qty)],
        },
        fallbacks=[
            CallbackQueryHandler(cb_army, pattern="^army$"),
            CallbackQueryHandler(cb_menu, pattern="^menu$"),
        ],
        per_user=True,
        allow_reentry=True,
    )
    app.add_handler(buy_conv)

    # ─── ConversationHandler: مالیات ──────────────
    tax_conv = ConversationHandler(
        entry_points=[CallbackQueryHandler(cb_tax, pattern="^tax$")],
        states={
            TAX_INPUT: [MessageHandler(filters.TEXT & ~filters.COMMAND, tax_set)],
        },
        fallbacks=[
            CallbackQueryHandler(cb_menu, pattern="^menu$"),
            CallbackQueryHandler(cb_eco, pattern="^eco$"),
        ],
        per_user=True,
        allow_reentry=True,
    )
    app.add_handler(tax_conv)

    # ─── ConversationHandler: حمله ────────────────
    attack_conv = ConversationHandler(
        entry_points=[CallbackQueryHandler(cb_attack, pattern="^attack$")],
        states={
            ATTACK_TARGET: [
                CallbackQueryHandler(attack_target, pattern="^atk_"),
                CallbackQueryHandler(cb_attack, pattern="^attack$"),
                CallbackQueryHandler(cb_menu, pattern="^menu$"),
            ],
            ATTACK_FORCE: [
                CallbackQueryHandler(attack_pick_unit, pattern="^af_pick_"),
                CallbackQueryHandler(af_back, pattern="^af_back$"),
                CallbackQueryHandler(attack_go, pattern="^af_go$"),
                CallbackQueryHandler(cb_menu, pattern="^menu$"),
            ],
            ATTACK_FORCE_QTY: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, attack_force_qty),
                CallbackQueryHandler(af_back, pattern="^af_back$"),
                CallbackQueryHandler(cb_menu, pattern="^menu$"),
            ],
        },
        fallbacks=[
            CallbackQueryHandler(cb_menu, pattern="^menu$"),
            CommandHandler("start", cmd_start),
        ],
        per_user=True,
        allow_reentry=True,
    )
    app.add_handler(attack_conv)

    # ─── ConversationHandler: مذاکره خصوصی ────────
    talk_conv = ConversationHandler(
        entry_points=[
            CallbackQueryHandler(cb_dip_confirm, pattern="^dipt_talk_"),
            CallbackQueryHandler(cb_talk_reply, pattern="^talkreply_"),
        ],
        states={
            DIP_TALK_MSG: [MessageHandler(filters.TEXT & ~filters.COMMAND, dip_talk_send)],
        },
        fallbacks=[
            CallbackQueryHandler(cb_menu, pattern="^menu$"),
            CallbackQueryHandler(cb_dip, pattern="^dip$"),
        ],
        per_user=True,
        allow_reentry=True,
    )
    app.add_handler(talk_conv)

    # ─── ConversationHandler: تجارت ───────────────
    trade_conv = ConversationHandler(
        entry_points=[CallbackQueryHandler(cb_trade, pattern="^trade$")],
        states={
            TRADE_PICK_TYPE: [
                CallbackQueryHandler(trade_pick_type, pattern="^tp_"),
            ],
            TRADE_PICK_AMOUNT: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, trade_pick_amount),
            ],
            TRADE_PICK_WANT: [
                CallbackQueryHandler(trade_pick_want, pattern="^tw_"),
            ],
        },
        fallbacks=[
            CallbackQueryHandler(cb_menu, pattern="^menu$"),
            CallbackQueryHandler(cb_trade, pattern="^trade$"),
        ],
        per_user=True,
        allow_reentry=True,
    )
    app.add_handler(trade_conv)

    # ─── Callbacks عمومی ──────────────────────────
    app.add_handler(CallbackQueryHandler(cb_newgame, pattern="^newgame$"))
    app.add_handler(CallbackQueryHandler(cb_pick_country, pattern="^pick_"))
    app.add_handler(CallbackQueryHandler(cb_menu, pattern="^menu$"))
    app.add_handler(CallbackQueryHandler(cb_eco, pattern="^eco$"))
    app.add_handler(CallbackQueryHandler(cb_army, pattern="^army$"))
    app.add_handler(CallbackQueryHandler(cb_res, pattern="^res$"))
    app.add_handler(CallbackQueryHandler(cb_research, pattern="^res_"))
    app.add_handler(CallbackQueryHandler(cb_proj, pattern="^proj$"))
    app.add_handler(CallbackQueryHandler(cb_build, pattern="^build_"))
    app.add_handler(CallbackQueryHandler(cb_internal, pattern="^internal$"))
    app.add_handler(CallbackQueryHandler(cb_speech, pattern="^speech$"))
    app.add_handler(CallbackQueryHandler(cb_suppress, pattern="^suppress$"))
    app.add_handler(CallbackQueryHandler(cb_spy, pattern="^spy$"))
    app.add_handler(CallbackQueryHandler(cb_spy_do, pattern="^spy_"))
    app.add_handler(CallbackQueryHandler(cb_stats, pattern="^stats$"))
    app.add_handler(CallbackQueryHandler(cb_help, pattern="^help$"))

    # ─── مستعمره/فتح ──────────────────────────────
    app.add_handler(CallbackQueryHandler(cb_colony, pattern="^colony_"))
    app.add_handler(CallbackQueryHandler(cb_conquer, pattern="^conquer_"))

    # ─── دیپلماسی ─────────────────────────────────
    app.add_handler(CallbackQueryHandler(cb_dip, pattern="^dip$"))
    app.add_handler(CallbackQueryHandler(cb_dip_ally, pattern="^dip_ally$"))
    app.add_handler(CallbackQueryHandler(cb_dip_peace, pattern="^dip_peace$"))
    app.add_handler(CallbackQueryHandler(cb_dip_war, pattern="^dip_war$"))
    app.add_handler(CallbackQueryHandler(cb_dip_talk, pattern="^dip_talk$"))
    app.add_handler(CallbackQueryHandler(cb_dip_nap, pattern="^dip_nap$"))
    app.add_handler(CallbackQueryHandler(cb_dip_tech, pattern="^dip_tech$"))
    app.add_handler(CallbackQueryHandler(cb_dip_colony, pattern="^dip_colony$"))
    app.add_handler(CallbackQueryHandler(cb_dip_accept, pattern="^dipacc_"))
    app.add_handler(CallbackQueryHandler(cb_dip_reject, pattern="^diprej_"))
    app.add_handler(CallbackQueryHandler(cb_dip_confirm, pattern="^dipt_(?!talk_)"))

    # ─── تجارت ────────────────────────────────────
    app.add_handler(CallbackQueryHandler(cb_trade_send, pattern="^tt_"))
    app.add_handler(CallbackQueryHandler(cb_trade_accept, pattern="^tradeacc_"))
    app.add_handler(CallbackQueryHandler(cb_trade_reject, pattern="^traderej_"))

    # ─── JobQueue: نوبت خودکار هر ۱ ساعت ──────────
    if app.job_queue:
        app.job_queue.run_repeating(auto_turn_job, interval=3600, first=60)
        print("⏰ نوبت خودکار فعال شد (هر ۱ ساعت)")

    print("🎖️ ربات جنگ جهانی دوم در حال اجراست...")
    print(f"📅 شروع: ۱ سپتامبر ۱۹۳۹")
    print(f"🏁 پایان: ۲ سپتامبر ۱۹۴۵")
    print(f"⏰ هر نوبت: ۳ روز بازی | هر ۱ ساعت واقعی")
    app.run_polling()


if __name__ == "__main__":
    main()
