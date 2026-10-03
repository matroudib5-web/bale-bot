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
# ═══════════════════════════════════════════════════════════════
#  📅 توابع تاریخ
# ═══════════════════════════════════════════════════════════════
def parse_game_date(date_str):
    try:
        return datetime.strptime(date_str, "%Y-%m-%d")
    except:
        return datetime(1939, 9, 1)


def format_game_date(dt):
    months_fa = ["ژانویه", "فوریه", "مارس", "آپریل", "مه", "ژوئن",
                 "ژوئیه", "اوت", "سپتامبر", "اکتبر", "نوامبر", "دسامبر"]
    return f"{dt.day} {months_fa[dt.month-1]} {dt.year}"


def advance_game_date(game_date, days=GAME_DAYS_PER_TURN):
    dt = parse_game_date(game_date)
    return (dt + timedelta(days=days)).strftime("%Y-%m-%d")


def get_events_between(date_from, date_to):
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


def turn_to_atomic_date():
    start = datetime(1939, 9, 1)
    atomic = datetime(1942, 8, 13)
    days = (atomic - start).days
    return days // GAME_DAYS_PER_TURN


# ═══════════════════════════════════════════════════════════════
#  🗺️ توابع همسایگی و مسیر
# ═══════════════════════════════════════════════════════════════
def get_owned_territories(owner_key):
    conn = db()
    rows = conn.execute(
        "SELECT country_key, percentage FROM territories WHERE owner=?",
        (owner_key,)
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def get_neighbors_dynamic(country_key):
    base = list(COUNTRIES.get(country_key, {}).get("neighbors", []))
    owned = get_owned_territories(country_key)
    for t in owned:
        if t["percentage"] >= 100:
            base.extend(COUNTRIES.get(t["country_key"], {}).get("neighbors", []))
    return list(set(base))


def can_attack(from_key, to_key):
    if from_key == to_key:
        return False, "نمی‌تونی به خودت حمله کنی"
    neighbors = get_neighbors_dynamic(from_key)
    if to_key in neighbors:
        return True, "زمینی"
    conn = db()
    row = conn.execute("SELECT has_naval_base FROM games WHERE country=?", (from_key,)).fetchone()
    conn.close()
    if row and row["has_naval_base"]:
        return True, "دریایی"
    return False, "راهی برای حمله نداری"


def get_distance(from_key, to_key):
    if to_key in COUNTRIES.get(from_key, {}).get("neighbors", []):
        return 1
    if to_key in get_neighbors_dynamic(from_key):
        return 2
    return 3


def get_distance_multiplier(distance):
    return {1: 1.0, 2: 1.5, 3: 2.5}.get(distance, 2.5)


def get_territory_owner(country_key):
    conn = db()
    row = conn.execute(
        "SELECT owner, percentage FROM territories WHERE country_key=?",
        (country_key,)
    ).fetchone()
    conn.close()
    if row:
        return dict(row)
    return None


def set_territory_owner(country_key, owner, percentage=0):
    conn = db()
    conn.execute("""
        INSERT OR REPLACE INTO territories (country_key, owner, percentage, occupied)
        VALUES (?, ?, ?, ?)
    """, (country_key, owner, percentage, 1 if percentage >= 100 else 0))
    conn.commit()
    conn.close()


# ═══════════════════════════════════════════════════════════════
#  ⚔️ توابع نظامی
# ═══════════════════════════════════════════════════════════════
def get_last_researched(country_key, category):
    conn = db()
    row = conn.execute("SELECT research FROM games WHERE country=?", (country_key,)).fetchone()
    conn.close()
    if not row:
        return None
    unlocked = json.loads(row["research"] or "[]")
    tree = RESEARCH.get(country_key, [])
    last = None
    for name, cost, days, power in tree:
        if name in unlocked:
            name_lower = name.lower()
            if category == "tank" and any(x in name_lower for x in ["panzer", "tiger", "panther", "t-", "m4", "m3", "m26", "churchill", "matilda", "cromwell", "char", "r-35", "type", "7tp", "ram", "sentinel", "m13", "p26"]):
                last = name
            elif category == "plane" and any(x in name_lower for x in ["bf", "fw", "me ", "spitfire", "hurricane", "typhoon", "lancaster", "p-", "b-", "yak", "la-", "mig", "il-", "a6m", "ki-", "kikka", "mc.", "d.520", "hawk", "pzl", "boomerang"]):
                last = name
            elif category == "ship" and any(x in name_lower for x in ["u-boat", "bismarck", "tirpitz", "scharnhorst", "king george", "nelson", "essex", "iowa", "kirov", "richelieu", "yamato", "littorio", "ning hai", "grom", "tribal", "perth", "bahia"]):
                last = name
    return last


def get_available_units(g, category):
    unlocked = json.loads(g["research"] or "[]")
    tree = RESEARCH.get(g["country"], [])
    result = []
    for name, cost, days, power in tree:
        name_lower = name.lower()
        is_tank = any(x in name_lower for x in ["panzer", "tiger", "panther", "t-", "m4", "m3", "m26", "churchill", "matilda", "cromwell", "char", "r-35", "7tp", "ram", "sentinel", "m13", "p26"])
        is_plane = any(x in name_lower for x in ["bf", "fw", "me ", "spitfire", "hurricane", "typhoon", "lancaster", "p-", "b-", "yak", "la-", "mig", "il-", "a6m", "ki-", "kikka", "mc.", "d.520", "hawk", "pzl", "boomerang"])
        is_ship = any(x in name_lower for x in ["u-boat", "bismarck", "tirpitz", "scharnhorst", "king george", "nelson", "essex", "iowa", "kirov", "richelieu", "yamato", "littorio", "ning hai", "grom", "tribal", "perth", "bahia"])

        if category == "tank" and not is_tank:
            continue
        if category == "plane" and not is_plane:
            continue
        if category == "ship" and not is_ship:
            continue

        if name in unlocked:
            money = int(power * 2 + 5)
            steel = max(1, power // 5)
            oil = max(0, power // 8)
            result.append({
                "name": name,
                "money": money,
                "steel": steel,
                "oil": oil,
                "attack": power,
                "unlocked": True
            })
        else:
            result.append({
                "name": name,
                "money": cost,
                "unlocked": False
            })
    return result


def compute_army_power(g, mode="attack"):
    unit_tanks = json.loads(g.get("unit_tanks") or "{}")
    unit_planes = json.loads(g.get("unit_planes") or "{}")
    unit_ships = json.loads(g.get("unit_ships") or "{}")

    tree = {name: (cost, days, power) for name, cost, days, power in RESEARCH.get(g["country"], [])}

    atk = 0
    dfn = 0
    atk += g["soldiers"] * 6
    dfn += g["soldiers"] * 8

    for name, count in unit_tanks.items():
        if name in tree:
            atk += count * tree[name][2]
            dfn += count * int(tree[name][2] * 0.7)

    for name, count in unit_planes.items():
        if name in tree:
            atk += count * tree[name][2]
            dfn += count * int(tree[name][2] * 0.5)

    for name, count in unit_ships.items():
        if name in tree:
            atk += count * tree[name][2]
            dfn += count * int(tree[name][2] * 0.9)

    completed = json.loads(g["completed_projects"] or "[]")
    for p_key in completed:
        p = PROJECTS.get(p_key)
        if not p:
            continue
        if p["effect"] == "attack_bonus":
            atk = int(atk * (1 + p["value"] / 100))
        elif p["effect"] == "defense_bonus":
            dfn = int(dfn * (1 + p["value"] / 100))

    if g["oil"] <= 0:
        atk = int(atk * 0.5)
        dfn = int(dfn * 0.5)

    if mode == "attack":
        return atk
    return dfn


def compute_total_units(g):
    unit_tanks = json.loads(g.get("unit_tanks") or "{}")
    unit_planes = json.loads(g.get("unit_planes") or "{}")
    unit_ships = json.loads(g.get("unit_ships") or "{}")
    return {
        "soldiers": g["soldiers"],
        "tanks": sum(unit_tanks.values()),
        "planes": sum(unit_planes.values()),
        "ships": sum(unit_ships.values())
    }


def fmt(n):
    return f"{n:,}"


# ═══════════════════════════════════════════════════════════════
#  🤖 NPCها
# ═══════════════════════════════════════════════════════════════
NPC_ID_START = -1000000


def ensure_npcs_exist():
    conn = db()
    existing = conn.execute("SELECT country FROM games WHERE user_id > 0").fetchall()
    taken = {r["country"] for r in existing}
    conn.close()

    for c_key in COUNTRIES:
        if c_key in taken:
            continue
        conn = db()
        row = conn.execute(
            "SELECT user_id FROM games WHERE country=? AND user_id < 0",
            (c_key,)
        ).fetchone()
        conn.close()
        if row:
            continue
        npc_id = NPC_ID_START - abs(hash(c_key)) % 100000
        c = COUNTRIES[c_key]
        conn = db()
        conn.execute("""
            INSERT OR IGNORE INTO games (user_id, country, turn, game_date,
                money, food, steel, oil, coal, manpower,
                last_turn, created_at)
            VALUES (?, ?, 1, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (npc_id, c_key, START_DATE,
              c["money"], c["food"], c["steel"], c["oil"], c["coal"], c["manpower"],
              datetime.utcnow().isoformat(), datetime.utcnow().isoformat()))
        conn.commit()
        conn.close()


def is_npc(user_id):
    return user_id < 0


# ═══════════════════════════════════════════════════════════════
#  🕹️ شروع بازی جدید
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
    """, (user_id, country_key, START_DATE,
          c["money"], c["food"], c["steel"], c["oil"], c["coal"], c["manpower"],
          datetime.utcnow().isoformat(), datetime.utcnow().isoformat()))
    conn.commit()
    conn.close()


# ═══════════════════════════════════════════════════════════════
#  🔄 پردازش نوبت
# ═══════════════════════════════════════════════════════════════
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

    war_mult = 1.0
    if g["war_active"]:
        war_mult = 0.8

    tax_mult = g["tax_rate"] / 20.0

    new_money    = g["money"]    + int(country["money"] * tax_mult * war_mult)
    new_food     = g["food"]     + int(country["food"] * war_mult)
    new_steel    = g["steel"]    + int(country["steel"]    * bonus["steel"] * war_mult)
    new_oil      = g["oil"]      + int(country["oil"]      * bonus["oil"] * war_mult)
    new_coal     = g["coal"]     + int(country["coal"]     * bonus["coal"] * war_mult)
    new_manpower = g["manpower"] + int(country["manpower"] * bonus["manpower"] * war_mult)

    total_units = compute_total_units(g)
    supply_money = 0
    supply_food = 0
    supply_oil = 0
    for unit_type, count in total_units.items():
        if unit_type == "soldiers":
            s = SUPPLY["soldier"]
        elif unit_type == "tanks":
            s = SUPPLY["tank"]
        elif unit_type == "planes":
            s = SUPPLY["plane"]
        elif unit_type == "ships":
            s = SUPPLY["ship"]
        else:
            continue
        mult = 1.0 if g["war_active"] else 0.5
        supply_money += int(s["money"] * count * mult)
        supply_food  += int(s["food"]  * count * mult)
        supply_oil   += int(s["oil"]   * count * mult)

    new_money = max(0, new_money - supply_money)
    new_food  = max(0, new_food  - supply_food)
    new_oil   = max(0, new_oil   - supply_oil)

    new_happiness = g["happiness"]
    if g["tax_rate"] > 25:
        new_happiness -= 2
    elif g["tax_rate"] < 15:
        new_happiness += 2
    if g["war_active"]:
        new_happiness -= 1
    else:
        new_happiness += 1
    if new_food < 100:
        new_happiness -= 3
    elif new_food > 500:
        new_happiness += 1
    if new_money <= 0:
        new_happiness -= 2

    speech_turns = g.get("speech_turns_left") or 0
    if speech_turns > 0:
        new_happiness += 2
        speech_turns -= 1

    suppress_cd = g.get("suppress_cooldown") or 0
    if suppress_cd > 0:
        suppress_cd -= 1
        if suppress_cd == 0:
            new_happiness -= 5

    new_happiness = max(0, min(100, new_happiness))
    new_unrest = 100 - new_happiness

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

    extra_updates = {}
    for p_key in newly_done:
        if p_key == "supply_rail":
            extra_updates["has_supply_rail"] = 1
        elif p_key == "naval_base":
            extra_updates["has_naval_base"] = 1

    old_date = g["game_date"]
    new_date = advance_game_date(old_date, GAME_DAYS_PER_TURN)
    events = get_events_between(old_date, new_date)

    save_game(user_id,
        turn=g["turn"] + 1,
        game_date=new_date,
        money=new_money, food=new_food, steel=new_steel,
        oil=new_oil, coal=new_coal, manpower=new_manpower,
        happiness=new_happiness, unrest=new_unrest,
        projects=json.dumps(still_building),
        completed_projects=json.dumps(completed),
        speech_turns_left=speech_turns,
        suppress_cooldown=suppress_cd,
        last_turn=datetime.utcnow().isoformat(),
        **extra_updates)

    return {
        "newly_done": newly_done,
        "date": new_date,
        "date_pretty": format_game_date(parse_game_date(new_date)),
        "events": events,
    }


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


# ═══════════════════════════════════════════════════════════════
#  🔒 عضویت اجباری
# ═══════════════════════════════════════════════════════════════
async def is_user_member(update, ctx, username):
    try:
        member = await ctx.bot.get_chat_member(
            chat_id=username,
            user_id=update.effective_user.id
        )
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
        resize_keyboard=True,
        one_time_keyboard=False
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
def menu_btn():
    return InlineKeyboardButton("🔙 منو", callback_data="menu")


def back_kb():
    return InlineKeyboardMarkup([[menu_btn()]])


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
    unit_tanks = json.loads(g.get("unit_tanks") or "{}")
    unit_planes = json.loads(g.get("unit_planes") or "{}")
    unit_ships = json.loads(g.get("unit_ships") or "{}")

    lines = [
        f"{c['flag']} *{c['name']}* — {date_str} (نوبت {g['turn']})",
        f"━━━━━━━━━━━━━━━━━━━━━━",
        f"💰 پول: {fmt(g['money'])}",
        f"🍞 غذا: {fmt(g['food'])}",
        f"⚙️ فولاد: {fmt(g['steel'])}",
        f"🛢️ نفت: {fmt(g['oil'])}",
        f"🪨 زغال: {fmt(g['coal'])}",
        f"👥 نیرو: {fmt(g['manpower'])}",
        f"━━━━━━━━━━━━━━━━━━━━━━",
        f"🪖 سرباز: {fmt(g['soldiers'])}",
    ]

    for name, count in unit_tanks.items():
        lines.append(f"🛡️ {name}: {fmt(count)}")
    for name, count in unit_planes.items():
        lines.append(f"✈️ {name}: {fmt(count)}")
    for name, count in unit_ships.items():
        lines.append(f"🚢 {name}: {fmt(count)}")

    lines.append(f"━━━━━━━━━━━━━━━━━━━━━━")
    lines.append(f"😊 رضایت: {g['happiness']}%  |  💵 مالیات: {g['tax_rate']}%")
    if g["war_active"]:
        lines.append("⚔️ *در حال جنگ*")
    return "\n".join(lines)


# ═══════════════════════════════════════════════════════════════
#  📝 هندلرهای اصلی
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
        "یکی از ۱۲ کشور رو انتخاب کن و از ۱ سپتامبر ۱۹۳۹ شروع کن.\n\n"
        "📅 هر ۱ ساعت = ۱ نوبت خودکار\n"
        "📅 هر نوبت = ۳ روز بازی جلو میره\n"
        "🏁 کل بازی = ۳۰ روز واقعی\n\n"
        "⚠️ این یه بازی استراتژیک تاریخیه. هدفش یادگیری تاریخه.\n"
        "*مرگ بر فاشیسم*",
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
    check_and_run_turn(uid)
    g = get_game(uid)
    await update.message.reply_text(
        render_dashboard(g),
        reply_markup=main_menu_kb(),
        parse_mode="Markdown"
    )


async def on_joined_check(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
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
        await update.message.reply_text(
            render_dashboard(g),
            reply_markup=main_menu_kb(),
            parse_mode="Markdown"
        )
    else:
        await update.message.reply_text(
            "🎖️ برای شروع:",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("🎮 بازی جدید", callback_data="newgame")],
                [InlineKeyboardButton("📖 راهنما", callback_data="help")],
            ])
        )


# ═══════════════════════════════════════════════════════════════
#  📋 کال‌بک‌های منو
# ═══════════════════════════════════════════════════════════════
async def cb_newgame(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()
    await q.edit_message_text(
        "🌍 *کشورت رو انتخاب کن:*\n\n🟢 آسان  |  🟡 متوسط  |  🔴 سخت",
        reply_markup=countries_kb(),
        parse_mode="Markdown"
    )


async def cb_pick_country(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()
    uid = q.from_user.id
    key = q.data.replace("pick_", "")
    c = COUNTRIES[key]

    existing = find_player_by_country(key)
    if existing and existing != uid:
        await q.answer(f"❌ {c['name']} قبلاً انتخاب شده!", show_alert=True)
        return

    start_new_game(uid, key)
    g = get_game(uid)

    await q.message.reply_text(
        f"✅ کشور انتخاب شد: {c['flag']} *{c['name']}*\n\n"
        f"{render_dashboard(g)}\n\n"
        f"از اینجا بازی شروع میشه!",
        reply_markup=main_menu_kb(),
        parse_mode="Markdown"
    )
    await q.edit_message_text(
        f"🎖️ *بازی شروع شد!*\n"
        f"کشورت: {c['flag']} {c['name']}",
        parse_mode="Markdown"
    )


async def cb_menu(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()
    g = get_game(q.from_user.id)
    if not g:
        await q.edit_message_text("بازی پیدا نشد. /start رو بزن.")
        return
    await q.edit_message_text(
        render_dashboard(g),
        reply_markup=main_menu_kb(),
        parse_mode="Markdown"
    )


async def cb_stats(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()
    g = get_game(q.from_user.id)
    await q.edit_message_text(
        render_dashboard(g),
        reply_markup=back_kb(),
        parse_mode="Markdown"
    )


async def cb_help(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()
    await q.edit_message_text(
        "📖 *راهنما*\n"
        "━━━━━━━━━━━━━━━━━━━━━━\n"
        "1️⃣ کشور انتخاب کن\n"
        "2️⃣ منابع تولید می‌شه\n"
        "3️⃣ ارتش بساز، تحقیق کن\n"
        "4️⃣ مالیات تنظیم کن\n"
        "5️⃣ حمله و جاسوسی\n"
        "6️⃣ هدف: پیروزی!\n\n"
        "📅 هر ۱ ساعت یه نوبت خودکار میاد.\n"
        "⚔️ هر نوبت = ۳ روز بازی\n\n"
        "⚠️ این یه بازی تاریخیه. *مرگ بر فاشیسم*",
        reply_markup=back_kb(),
        parse_mode="Markdown"
    )
    # ═══════════════════════════════════════════════════════════════
#  💰 اقتصاد
# ═══════════════════════════════════════════════════════════════
async def cb_eco(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()
    g = get_game(q.from_user.id)
    c = COUNTRIES[g["country"]]
    tax_mult = g["tax_rate"] / 20.0
    war_mult = 0.8 if g["war_active"] else 1.0

    total = compute_total_units(g)
    sup_money = 0
    sup_food = 0
    sup_oil = 0
    for ut, count in total.items():
        if ut == "soldiers":
            s = SUPPLY["soldier"]
        elif ut == "tanks":
            s = SUPPLY["tank"]
        elif ut == "planes":
            s = SUPPLY["plane"]
        elif ut == "ships":
            s = SUPPLY["ship"]
        else:
            continue
        mult = 1.0 if g["war_active"] else 0.5
        sup_money += int(s["money"] * count * mult)
        sup_food  += int(s["food"]  * count * mult)
        sup_oil   += int(s["oil"]   * count * mult)

    text = (
        f"💰 *اقتصاد {c['name']}*\n"
        f"━━━━━━━━━━━━━━━━━━━━━━\n"
        f"💰 پول: {fmt(g['money'])}\n"
        f"   📈 تولید: +{int(c['money']*tax_mult*war_mult)}  |  📉 تدارکات: -{sup_money}\n"
        f"🍞 غذا: {fmt(g['food'])}\n"
        f"   📈 تولید: +{int(c['food']*war_mult)}  |  📉 تدارکات: -{sup_food}\n"
        f"⚙️ فولاد: {fmt(g['steel'])}  (+{c['steel']}/نوبت)\n"
        f"🛢️ نفت: {fmt(g['oil'])}\n"
        f"   📈 تولید: +{c['oil']}  |  📉 تدارکات: -{sup_oil}\n"
        f"🪨 زغال: {fmt(g['coal'])}  (+{c['coal']}/نوبت)\n"
        f"👥 نیرو: {fmt(g['manpower'])}  (+{c['manpower']}/نوبت)\n"
        f"━━━━━━━━━━━━━━━━━━━━━━\n"
        f"💵 مالیات: {g['tax_rate']}%  |  😊 رضایت: {g['happiness']}%"
    )

    kb = InlineKeyboardMarkup([
        [InlineKeyboardButton("💵 تغییر مالیات", callback_data="tax")],
        [InlineKeyboardButton("🏗️ ساخت پروژه", callback_data="proj")],
        [menu_btn()],
    ])
    await q.edit_message_text(text, reply_markup=kb, parse_mode="Markdown")


# ═══════════════════════════════════════════════════════════════
#  💵 مالیات
# ═══════════════════════════════════════════════════════════════
TAX_INPUT = 10


async def cb_tax(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()
    g = get_game(q.from_user.id)
    await q.edit_message_text(
        f"💵 *مالیات*\n"
        f"━━━━━━━━━━━━━━━━━━━━━━\n"
        f"الان: {g['tax_rate']}%\n"
        f"رضایت: {g['happiness']}%\n\n"
        f"عددی بین ۰ تا ۵۰ بفرست.\n"
        f"• بالای ۲۵٪ = نارضایتی هر نوبت\n"
        f"• زیر ۱۵٪ = رضایت بیشتر\n"
        f"• ۲۰٪ = تعادل",
        parse_mode="Markdown",
        reply_markup=InlineKeyboardMarkup([[menu_btn()]])
    )
    return TAX_INPUT


async def tax_set(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
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

    await update.message.reply_text(
        f"✅ مالیات شد {rate}%\n\n"
        f"{render_dashboard(g)}",
        reply_markup=main_menu_kb(),
        parse_mode="Markdown"
    )
    return ConversationHandler.END


# ═══════════════════════════════════════════════════════════════
#  🏛️ امور کشور
# ═══════════════════════════════════════════════════════════════
async def cb_internal(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()
    g = get_game(q.from_user.id)

    speech_left = g.get("speech_turns_left") or 0
    suppress_cd = g.get("suppress_cooldown") or 0

    text = (
        f"🏛️ *امور کشور*\n"
        f"━━━━━━━━━━━━━━━━━━━━━━\n"
        f"😊 رضایت مردم: {g['happiness']}%\n"
        f"🔥 نارضایتی: {g['unrest']}%\n"
    )
    if speech_left > 0:
        text += f"\n📢 سخنرانی فعال ({speech_left} نوبت مونده)\n"
    if suppress_cd > 0:
        text += f"\n⚠️ عوارض سرکوب در {suppress_cd} نوبت\n"

    if g["happiness"] < 30:
        text += "\n🔥 *مردم در حال اعتراضن!*"
    elif g["happiness"] < 50:
        text += "\n⚠️ نارضایتی در حال رشد."
    else:
        text += "\n✅ وضعیت آرامه."

    kb = InlineKeyboardMarkup([
        [InlineKeyboardButton("📢 سخنرانی (۱۰۰💰)", callback_data="speech")],
        [InlineKeyboardButton("🚔 سرکوب (۵۰💰)", callback_data="suppress")],
        [menu_btn()],
    ])
    await q.edit_message_text(text, reply_markup=kb, parse_mode="Markdown")


async def cb_speech(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()
    uid = q.from_user.id
    g = get_game(uid)

    if (g.get("speech_turns_left") or 0) > 0:
        await q.answer("❌ یه سخنرانی فعال داری. صبر کن تموم بشه.", show_alert=True)
        return
    if g["money"] < 100:
        await q.answer("❌ ۱۰۰ پول لازمه.", show_alert=True)
        return

    save_game(uid, money=g["money"] - 100, speech_turns_left=5)

    await q.message.reply_text(
        "📢 سخنرانی رهبر شروع شد!\n"
        "اثرش در ۵ نوبت آینده ظاهر میشه (+۲ رضایت هر نوبت).",
        reply_markup=main_menu_kb(),
        parse_mode="Markdown"
    )
    await q.edit_message_text(
        "📢 سخنرانی شروع شد — بالا ببین ⬆️",
        reply_markup=back_kb()
    )


async def cb_suppress(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()
    uid = q.from_user.id
    g = get_game(uid)

    if (g.get("suppress_cooldown") or 0) > 0:
        await q.answer("❌ سرکوب قبلی هنوز اثر داره. صبر کن.", show_alert=True)
        return
    if g["money"] < 50:
        await q.answer("❌ ۵۰ پول لازمه.", show_alert=True)
        return

    save_game(uid,
        money=g["money"] - 50,
        happiness=min(100, g["happiness"] + 10),
        suppress_cooldown=3,
        suppress_count=(g.get("suppress_count") or 0) + 1)

    await q.message.reply_text(
        "🚔 سرکوب شد!\n"
        "+۱۰ رضایت فوری (ولی بعد ۳ نوبت -۵ رضایت پایه)",
        reply_markup=main_menu_kb(),
        parse_mode="Markdown"
    )
    await q.edit_message_text(
        "🚔 سرکوب شد — بالا ببین ⬆️",
        reply_markup=back_kb()
    )


# ═══════════════════════════════════════════════════════════════
#  ⚔️ ارتش
# ═══════════════════════════════════════════════════════════════
async def cb_army(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()
    g = get_game(q.from_user.id)
    atk = compute_army_power(g, "attack")
    dfn = compute_army_power(g, "defense")

    unit_tanks = json.loads(g.get("unit_tanks") or "{}")
    unit_planes = json.loads(g.get("unit_planes") or "{}")
    unit_ships = json.loads(g.get("unit_ships") or "{}")

    lines = [
        f"⚔️ *ارتش {COUNTRIES[g['country']]['name']}*",
        f"━━━━━━━━━━━━━━━━━━━━━━",
        f"🪖 سرباز: {fmt(g['soldiers'])}",
    ]
    for name, count in unit_tanks.items():
        lines.append(f"🛡️ {name}: {fmt(count)}")
    for name, count in unit_planes.items():
        lines.append(f"✈️ {name}: {fmt(count)}")
    for name, count in unit_ships.items():
        lines.append(f"🚢 {name}: {fmt(count)}")

    lines.append(f"━━━━━━━━━━━━━━━━━━━━━━")
    lines.append(f"⚔️ حمله کل: {fmt(atk)}")
    lines.append(f"🛡️ دفاع کل: {fmt(dfn)}")

    if g["oil"] <= 0:
        lines.append("\n⚠️ *نفتت تمومه! ارتشت ۵۰٪ ضعیف شده.*")

    kb = InlineKeyboardMarkup([
        [InlineKeyboardButton("🪖 خرید سرباز", callback_data="buy_soldier"),
         InlineKeyboardButton("🛡️ خرید تانک", callback_data="buy_tank")],
        [InlineKeyboardButton("✈️ خرید هواپیما", callback_data="buy_plane"),
         InlineKeyboardButton("🚢 خرید کشتی", callback_data="buy_ship")],
        [menu_btn()],
    ])
    await q.edit_message_text("\n".join(lines), reply_markup=kb, parse_mode="Markdown")


# ═══════════════════════════════════════════════════════════════
#  🪖 خرید سرباز
# ═══════════════════════════════════════════════════════════════
BUY_SOLDIER_QTY = 20


async def buy_soldier_start(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()
    await q.edit_message_text(
        "🪖 *خرید سرباز*\n"
        "━━━━━━━━━━━━━━━━━━━━━━\n"
        "قیمت هر سرباز: ۱۰💰 + ۱👥\n\n"
        "چند تا سرباز می‌خوای؟\n"
        "عدد بفرست:",
        parse_mode="Markdown",
        reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("❌ انصراف", callback_data="army")]])
    )
    return BUY_SOLDIER_QTY


async def buy_soldier_qty(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    try:
        qty = int(update.message.text.strip())
        if qty <= 0:
            raise ValueError
    except:
        await update.message.reply_text("❌ فقط یه عدد مثبت بفرست.")
        return BUY_SOLDIER_QTY

    g = get_game(uid)
    need_money = 10 * qty
    need_man = 1 * qty

    if g["money"] < need_money or g["manpower"] < need_man:
        await update.message.reply_text(
            f"❌ منابع کافی نداری!\n\n"
            f"نیاز: {need_money}💰 + {need_man}👥\n"
            f"داری: {g['money']}💰 + {g['manpower']}👥"
        )
        return ConversationHandler.END

    save_game(uid,
        money=g["money"] - need_money,
        manpower=g["manpower"] - need_man,
        soldiers=g["soldiers"] + qty)

    await update.message.reply_text(
        f"✅ *{qty} سرباز* ساخته شد!\n"
        f"هزینه: {need_money}💰 + {need_man}👥",
        parse_mode="Markdown",
        reply_markup=main_menu_kb()
    )
    return ConversationHandler.END


# ═══════════════════════════════════════════════════════════════
#  🛡️ خرید تانک
# ═══════════════════════════════════════════════════════════════
BUY_TANK_QTY = 21


async def buy_tank_start(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()
    g = get_game(q.from_user.id)
    units = get_available_units(g, "tank")

    lines = [f"🛡️ *خرید تانک — {COUNTRIES[g['country']]['name']}*", "━━━━━━━━━━━━━━━━━━━━━━"]
    rows = []
    for u in units:
        if u["unlocked"]:
            lines.append(f"✅ {u['name']} — {u['money']}💰 + {u['steel']}⚙️ + {u['oil']}🛢️ (قدرت {u['attack']})")
            rows.append([InlineKeyboardButton(
                f"🛡️ {u['name']} ({u['money']}💰)",
                callback_data=f"buytank_{u['name'].replace(' ', '_')}"
            )])
        else:
            lines.append(f"🔒 {u['name']} — {u['money']}💰 (تحقیق کن)")
    rows.append([InlineKeyboardButton("❌ انصراف", callback_data="army")])

    await q.edit_message_text(
                text += "\n✅ *پروژه‌های تکمیل‌شده:*\n"
            for k in result["newly_done"]:
                p_info = PROJECTS.get(k)
                if p_info:
                    text += f"• {p_info['name']}\n"
                elif k == "atomic_bomb":
                    text += "• ☢️ *بمب اتم آماده شد!*\n"

        try:
            await context.bot.send_message(
                p["user_id"],
                text,
                parse_mode="Markdown",
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("📊 آمار", callback_data="stats")],
                    [InlineKeyboardButton("🎮 منو", callback_data="menu")],
                ])
            )
        except Exception as e:
            log.warning(f"خطا در ارسال به {p['user_id']}: {e}")


# ═══════════════════════════════════════════════════════════════
#  🚀 main
# ═══════════════════════════════════════════════════════════════
def main():
    init_db()
    ensure_npcs_exist()

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

    # ─── دستور «اطلاعات [کشور]» برای ادمین ────────
    app.add_handler(MessageHandler(
        filters.TEXT & filters.Regex("^اطلاعات "),
        cmd_country_info
    ))

    # ─── ConversationHandler: خرید سرباز ──────────
    buy_soldier_conv = ConversationHandler(
        entry_points=[CallbackQueryHandler(buy_soldier_start, pattern="^buy_soldier$")],
        states={BUY_SOLDIER_QTY: [MessageHandler(filters.TEXT & ~filters.COMMAND, buy_soldier_qty)]},
        fallbacks=[CallbackQueryHandler(cb_army, pattern="^army$")],
        per_user=True,
    )
    app.add_handler(buy_soldier_conv)

    # ─── ConversationHandler: خرید تانک ───────────
    buy_tank_conv = ConversationHandler(
        entry_points=[
            CallbackQueryHandler(buy_tank_start, pattern="^buy_tank$"),
            CallbackQueryHandler(buytank_pick, pattern="^buytank_"),
        ],
        states={
            BUY_TANK_QTY: [MessageHandler(filters.TEXT & ~filters.COMMAND, buytank_qty)],
        },
        fallbacks=[CallbackQueryHandler(cb_army, pattern="^army$")],
        per_user=True,
        allow_reentry=True,
    )
    app.add_handler(buy_tank_conv)

    # ─── ConversationHandler: خرید هواپیما ────────
    buy_plane_conv = ConversationHandler(
        entry_points=[
            CallbackQueryHandler(buy_plane_start, pattern="^buy_plane$"),
            CallbackQueryHandler(buyplane_pick, pattern="^buyplane_"),
        ],
        states={
            BUY_PLANE_QTY: [MessageHandler(filters.TEXT & ~filters.COMMAND, buyplane_qty)],
        },
        fallbacks=[CallbackQueryHandler(cb_army, pattern="^army$")],
        per_user=True,
        allow_reentry=True,
    )
    app.add_handler(buy_plane_conv)

    # ─── ConversationHandler: خرید کشتی ───────────
    buy_ship_conv = ConversationHandler(
        entry_points=[
            CallbackQueryHandler(buy_ship_start, pattern="^buy_ship$"),
            CallbackQueryHandler(buyship_pick, pattern="^buyship_"),
        ],
        states={
            BUY_SHIP_QTY: [MessageHandler(filters.TEXT & ~filters.COMMAND, buyship_qty)],
        },
        fallbacks=[CallbackQueryHandler(cb_army, pattern="^army$")],
        per_user=True,
        allow_reentry=True,
    )
    app.add_handler(buy_ship_conv)

    # ─── ConversationHandler: مالیات ──────────────
    tax_conv = ConversationHandler(
        entry_points=[CallbackQueryHandler(cb_tax, pattern="^tax$")],
        states={TAX_INPUT: [MessageHandler(filters.TEXT & ~filters.COMMAND, tax_set)]},
        fallbacks=[CallbackQueryHandler(cb_menu, pattern="^menu$")],
        per_user=True,
    )
    app.add_handler(tax_conv)

    # ─── ConversationHandler: حمله ────────────────
    attack_conv = ConversationHandler(
        entry_points=[CallbackQueryHandler(cb_attack, pattern="^attack$")],
        states={
            ATTACK_TARGET: [
                CallbackQueryHandler(attack_target, pattern="^atk_"),
            ],
            ATTACK_FORCE: [
                CallbackQueryHandler(attack_pick_unit, pattern="^af_(soldiers|tanks|planes|ships)$"),
                CallbackQueryHandler(af_back, pattern="^af_back$"),
                CallbackQueryHandler(attack_go, pattern="^af_go$"),
            ],
            ATTACK_QTY: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, attack_qty),
                CallbackQueryHandler(af_back, pattern="^af_back$"),
            ],
        },
        fallbacks=[CallbackQueryHandler(cb_menu, pattern="^menu$")],
        per_user=True,
        allow_reentry=True,
    )
    app.add_handler(attack_conv)

    # ─── ConversationHandler: مذاکره ──────────────
    talk_conv = ConversationHandler(
        entry_points=[
            CallbackQueryHandler(cb_dip_confirm, pattern="^dipt_talk_"),
            CallbackQueryHandler(cb_talk_reply, pattern="^talkreply_"),
        ],
        states={DIP_TALK_MSG: [MessageHandler(filters.TEXT & ~filters.COMMAND, dip_talk_send)]},
        fallbacks=[CallbackQueryHandler(cb_menu, pattern="^menu$")],
        per_user=True,
        allow_reentry=True,
    )
    app.add_handler(talk_conv)

    # ─── ConversationHandler: تجارت ───────────────
    trade_conv = ConversationHandler(
        entry_points=[CallbackQueryHandler(cb_trade, pattern="^trade$")],
        states={
            TRADE_PICK_TYPE: [CallbackQueryHandler(trade_pick_type, pattern="^tp_")],
            TRADE_PICK_AMOUNT: [MessageHandler(filters.TEXT & ~filters.COMMAND, trade_pick_amount)],
            TRADE_PICK_WANT: [CallbackQueryHandler(trade_pick_want, pattern="^tw_")],
        },
        fallbacks=[CallbackQueryHandler(cb_menu, pattern="^menu$")],
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
    app.add_handler(CallbackQueryHandler(cb_colony, pattern="^colony_"))

    # ─── دیپلماسی ─────────────────────────────────
    app.add_handler(CallbackQueryHandler(cb_dip, pattern="^dip$"))
    app.add_handler(CallbackQueryHandler(cb_dip_ally, pattern="^dip_ally$"))
    app.add_handler(CallbackQueryHandler(cb_dip_peace, pattern="^dip_peace$"))
    app.add_handler(CallbackQueryHandler(cb_dip_war, pattern="^dip_war$"))
    app.add_handler(CallbackQueryHandler(cb_dip_nap, pattern="^dip_nap$"))
    app.add_handler(CallbackQueryHandler(cb_dip_tech, pattern="^dip_tech$"))
    app.add_handler(CallbackQueryHandler(cb_dip_trade, pattern="^dip_trade$"))
    app.add_handler(CallbackQueryHandler(cb_dip_talk, pattern="^dip_talk$"))
    app.add_handler(CallbackQueryHandler(cb_dip_accept, pattern="^dipacc_"))
    app.add_handler(CallbackQueryHandler(cb_dip_reject, pattern="^diprej_"))
    app.add_handler(CallbackQueryHandler(cb_dip_confirm, pattern="^dipt_(?!talk_)"))

    # ─── تجارت ────────────────────────────────────
    app.add_handler(CallbackQueryHandler(cb_trade_send, pattern="^tt_"))
    app.add_handler(CallbackQueryHandler(cb_trade_accept, pattern="^tradeacc_"))
    app.add_handler(CallbackQueryHandler(cb_trade_reject, pattern="^traderej_"))

    # ─── بمب اتم ──────────────────────────────────
    app.add_handler(CallbackQueryHandler(cb_atom_use, pattern="^atom_use$"))
    app.add_handler(CallbackQueryHandler(cb_atom_target, pattern="^atom_"))

    # ─── JobQueue: نوبت خودکار هر ۱ ساعت ──────────
    if app.job_queue:
        app.job_queue.run_repeating(auto_turn_job, interval=3600, first=120)
        print("⏰ نوبت خودکار فعال شد (هر ۱ ساعت)")

    print("🎖️ ربات جنگ جهانی دوم در حال اجراست...")
    print(f"📅 شروع: ۱ سپتامبر ۱۹۳۹")
    print(f"🏁 پایان: ۲ سپتامبر ۱۹۴۵")
    print(f"⏰ هر نوبت: ۳ روز بازی | هر ۱ ساعت واقعی")
    app.run_polling()


if __name__ == "__main__":
    main()
