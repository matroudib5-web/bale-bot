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
#  ⚙️ تنظیمات اصلی
# ═══════════════════════════════════════════════════════════════
BOT_TOKEN = "152004939:gjvarQqggvlUKNXdDBoJPx-mTNcNGPBu0k8"
BALE_API = "https://tapi.bale.ai/bot"

DB_FILE = "ww2_game.db"
TURN_HOURS = 1
GAME_DAYS_PER_TURN = 3
START_DATE = "1939-09-01"

REQUIRED_CHANNELS = [
    {"username": "@Hitlerss1",     "label": "عضویت در کانال اول"},
    {"username": "@WORLDWAR21250", "label": "عضویت در کانال دوم"},
]

ADMIN_IDS = [1429506412, 1618371215]

logging.basicConfig(
    format='%(asctime)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
log = logging.getLogger(__name__)

# ═══════════════════════════════════════════════════════════════
#  🌍 کشورها (۱۲ کشور — آمار ۱۹۳۹)
# ═══════════════════════════════════════════════════════════════
COUNTRIES = {
    "germany": {"flag": "🇩🇪", "name": "آلمان", "capital": "برلین",
        "difficulty": "🟡 متوسط",
        "money": 384, "food": 200, "steel": 23, "oil": 1, "coal": 24, "manpower": 80,
        "neighbors": ["france", "poland", "italy", "ussr"]},
    "uk": {"flag": "🇬🇧", "name": "انگلیس", "capital": "لندن",
        "difficulty": "🟡 متوسط",
        "money": 287, "food": 180, "steel": 13, "oil": 1, "coal": 14, "manpower": 50,
        "neighbors": []},
    "usa": {"flag": "🇺🇸", "name": "آمریکا", "capital": "واشینگتن",
        "difficulty": "🟢 آسان",
        "money": 869, "food": 450, "steel": 51, "oil": 20, "coal": 21, "manpower": 130,
        "neighbors": []},
    "ussr": {"flag": "🇷🇺", "name": "شوروی", "capital": "مسکو",
        "difficulty": "🟢 آسان",
        "money": 366, "food": 300, "steel": 19, "oil": 3, "coal": 6, "manpower": 170,
        "neighbors": ["germany", "poland", "china", "japan"]},
    "france": {"flag": "🇫🇷", "name": "فرانسه", "capital": "پاریس",
        "difficulty": "🔴 سخت",
        "money": 199, "food": 150, "steel": 6, "oil": 0, "coal": 5, "manpower": 45,
        "neighbors": ["germany", "italy"]},
    "japan": {"flag": "🇯🇵", "name": "ژاپن", "capital": "توکیو",
        "difficulty": "🔴 سخت",
        "money": 184, "food": 120, "steel": 6, "oil": 0, "coal": 2, "manpower": 70,
        "neighbors": ["china", "ussr"]},
    "italy": {"flag": "🇮🇹", "name": "ایتالیا", "capital": "رم",
        "difficulty": "🔴 سخت",
        "money": 151, "food": 110, "steel": 2, "oil": 0, "coal": 0, "manpower": 40,
        "neighbors": ["germany", "france"]},
    "china": {"flag": "🇨🇳", "name": "چین", "capital": "چونگ‌کینگ",
        "difficulty": "🔴 سخت",
        "money": 120, "food": 250, "steel": 1, "oil": 0, "coal": 3, "manpower": 200,
        "neighbors": ["ussr", "japan"]},
    "poland": {"flag": "🇵🇱", "name": "لهستان", "capital": "ورشو",
        "difficulty": "🔴 سخت",
        "money": 80, "food": 100, "steel": 2, "oil": 0, "coal": 4, "manpower": 35,
        "neighbors": ["germany", "ussr"]},
    "canada": {"flag": "🇨🇦", "name": "کانادا", "capital": "اتاوا",
        "difficulty": "🟢 آسان",
        "money": 110, "food": 180, "steel": 5, "oil": 2, "coal": 6, "manpower": 25,
        "neighbors": []},
    "australia": {"flag": "🇦🇺", "name": "استرالیا", "capital": "کانبرا",
        "difficulty": "🟢 آسان",
        "money": 95, "food": 160, "steel": 3, "oil": 0, "coal": 4, "manpower": 20,
        "neighbors": []},
    "brazil": {"flag": "🇧🇷", "name": "برزیل", "capital": "ریو",
        "difficulty": "🟢 آسان",
        "money": 75, "food": 200, "steel": 2, "oil": 0, "coal": 1, "manpower": 60,
        "neighbors": []},
}
# ═══════════════════════════════════════════════════════════════
#  🔬 درخت تحقیقات (کامل — Panzer I تا Tiger II)
# ═══════════════════════════════════════════════════════════════
RESEARCH = {
    "germany": [
        ("Panzer I", 20, 2, 5), ("Panzer II", 30, 3, 7),
        ("Panzer III", 40, 4, 10), ("Panzer IV", 60, 5, 14),
        ("Panther", 80, 6, 18), ("Tiger I", 100, 8, 22),
        ("Tiger II", 120, 10, 26),
        ("Bf 109 E", 30, 3, 8), ("Fw 190", 50, 5, 12),
        ("Bf 109 G", 70, 6, 15), ("Me 262", 120, 8, 20),
        ("U-Boat VII", 60, 5, 12), ("Scharnhorst", 90, 7, 18),
        ("Bismarck", 120, 8, 24), ("Tirpitz", 150, 10, 28),
    ],
    "uk": [
        ("Matilda II", 50, 4, 12), ("Churchill", 80, 6, 14),
        ("Cromwell", 100, 7, 18),
        ("Hurricane", 35, 3, 10), ("Spitfire", 40, 3, 13),
        ("Typhoon", 70, 5, 16), ("Gloster Meteor", 120, 8, 20),
        ("Lancaster", 100, 7, 20),
        ("HMS King George V", 120, 8, 21), ("HMS Nelson", 100, 7, 18),
    ],
    "usa": [
        ("M3 Stuart", 40, 4, 10), ("M4 Sherman", 70, 5, 13),
        ("M26 Pershing", 100, 7, 18),
        ("P-40", 35, 3, 10), ("P-51 Mustang", 80, 5, 14),
        ("P-47 Thunderbolt", 100, 6, 16),
        ("B-17", 120, 7, 20), ("B-29", 150, 9, 26),
        ("Essex Carrier", 150, 9, 24), ("Iowa", 130, 8, 22),
    ],
    "ussr": [
        ("T-26", 30, 3, 9), ("T-34", 70, 5, 16),
        ("KV-1", 80, 6, 19), ("IS-2", 100, 7, 22),
        ("Yak-1", 35, 3, 11), ("La-5", 65, 5, 12),
        ("MiG-9", 120, 8, 24), ("IL-2 Sturmovik", 80, 6, 15),
        ("Kirov", 90, 6, 18),
    ],
    "france": [
        ("R-35", 25, 2, 8), ("Char B1", 60, 5, 14),
        ("D.520", 45, 4, 12), ("Richelieu", 100, 7, 20),
    ],
    "japan": [
        ("Type 97", 40, 4, 11), ("Type 1 Chi-He", 60, 5, 14),
        ("A6M Zero", 50, 4, 15), ("Ki-84", 75, 6, 18),
        ("Kikka", 120, 8, 24), ("Yamato", 130, 8, 26),
        ("Type 97 Chi-Ha", 30, 3, 9),
    ],
    "italy": [
        ("M13/40", 35, 3, 10), ("P26/40", 55, 4, 13),
        ("MC.200", 35, 3, 11), ("MC.202", 60, 5, 12),
        ("Littorio", 90, 6, 19),
    ],
    "china": [
        ("Type 88", 25, 2, 8), ("Type 24", 40, 4, 11),
        ("Hawk III", 40, 4, 9), ("Ning Hai", 60, 5, 12),
    ],
    "poland": [
        ("7TP", 30, 3, 9), ("PZL.37", 35, 3, 10),
        ("Grom", 60, 5, 12),
    ],
    "canada": [
        ("Ram", 45, 4, 13), ("Hurricane", 35, 3, 11),
        ("Tribal", 70, 5, 15),
    ],
    "australia": [
        ("Sentinel", 40, 4, 11), ("Boomerang", 45, 4, 10),
        ("Perth", 65, 5, 14),
    ],
    "brazil": [
        ("M3 Stuart", 40, 4, 10), ("P-40", 35, 3, 10),
        ("Bahia", 60, 5, 11),
    ],
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
    "supply_rail":  {"name": "🚂 راه‌آهن تدارکاتی",    "money": 150, "steel": 30, "days": 7, "effect": "supply_range",  "value": 1},
    "naval_base":   {"name": "⚓ پایگاه دریایی",      "money": 200, "steel": 40, "days": 10, "effect": "naval_range",  "value": 1},
}

# ═══════════════════════════════════════════════════════════════
#  🗓️ رویدادهای تاریخی
# ═══════════════════════════════════════════════════════════════
HISTORIC_EVENTS = {
    "1939-09-01": "🇩🇪 آلمان به لهستان حمله کرد — شروع جنگ جهانی دوم",
    "1939-09-03": "🇬🇧🇫🇷 انگلیس و فرانسه به آلمان اعلام جنگ کردن",
    "1939-11-30": "🇷🇺 شوروی به فنلاند حمله کرد — جنگ زمستانی",
    "1940-04-09": "🇩🇪 آلمان به دانمارک و نروژ حمله کرد",
    "1940-05-10": "🇩🇪 آلمان به فرانسه حمله کرد",
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
#  🚚 تدارکات هر واحد (مصرف هر نوبت)
# ═══════════════════════════════════════════════════════════════
SUPPLY = {
    "soldier": {"money": 1, "food": 2, "oil": 0},
    "tank":    {"money": 5, "food": 10, "oil": 5},
    "plane":   {"money": 3, "food": 5, "oil": 10},
    "ship":    {"money": 10, "food": 30, "oil": 20},
}

UNIT_SPEED = {
    "soldier": 1,
    "tank": 2,
    "plane": 3,
    "ship": 1,
}

SHIP_CAPACITY = 20

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
            unit_tanks  TEXT DEFAULT '{}',
            unit_planes TEXT DEFAULT '{}',
            unit_ships  TEXT DEFAULT '{}',
            tax_rate    INTEGER DEFAULT 20,
            happiness   INTEGER DEFAULT 70,
            unrest      INTEGER DEFAULT 0,
            war_active  INTEGER DEFAULT 0,
            has_supply_rail INTEGER DEFAULT 0,
            has_naval_base  INTEGER DEFAULT 0,
            has_atomic      INTEGER DEFAULT 0,
            atomic_ready    INTEGER DEFAULT 0,
            projects    TEXT DEFAULT '[]',
            completed_projects TEXT DEFAULT '[]',
            research    TEXT DEFAULT '[]',
            allies      TEXT DEFAULT '[]',
            wars        TEXT DEFAULT '[]',
            sanctions   TEXT DEFAULT '[]',
            colonies    TEXT DEFAULT '[]',
            speech_turns_left INTEGER DEFAULT 0,
            suppress_count INTEGER DEFAULT 0,
            suppress_cooldown INTEGER DEFAULT 0,
            last_turn   TEXT,
            created_at  TEXT
        )
    """)
    c.execute("""
        CREATE TABLE IF NOT EXISTS settings (
            key TEXT PRIMARY KEY,
            value TEXT
        )
    """)
    c.execute("""
        CREATE TABLE IF NOT EXISTS territories (
            country_key TEXT PRIMARY KEY,
            owner       TEXT,
            occupied    INTEGER DEFAULT 0,
            percentage  INTEGER DEFAULT 0
        )
    """)
    c.execute("INSERT OR IGNORE INTO settings (key, value) VALUES ('war_open', 'true')")
    c.execute("INSERT OR IGNORE INTO settings (key, value) VALUES ('atomic_used', 'false')")
    conn.commit()
    conn.close()


def db():
    conn = sqlite3.connect(DB_FILE)
    conn.row_factory = sqlite3.Row
    return conn


def get_setting(key, default="true"):
    conn = db()
    row = conn.execute("SELECT value FROM settings WHERE key=?", (key,)).fetchone()
    conn.close()
    return row["value"] if row else default


def set_setting(key, value):
    conn = db()
    conn.execute("INSERT OR REPLACE INTO settings (key, value) VALUES (?, ?)", (key, value))
    conn.commit()
    conn.close()


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


def get_all_players():
    conn = db()
    rows = conn.execute("SELECT * FROM games WHERE user_id > 0 ORDER BY user_id").fetchall()
    conn.close()
    return [dict(r) for r in rows]


def find_player_by_country(country_key):
    conn = db()
    row = conn.execute("SELECT user_id FROM games WHERE country=?", (country_key,)).fetchone()
    conn.close()
    return row["user_id"] if row else None


def get_active_players(exclude_uid=None):
    conn = db()
    rows = conn.execute(
        "SELECT user_id, country FROM games WHERE user_id > 0 ORDER BY country"
    ).fetchall()
    conn.close()
    result = []
    for r in rows:
        if exclude_uid and r["user_id"] == exclude_uid:
            continue
        result.append({"user_id": r["user_id"], "country": r["country"]})
    return result
    
