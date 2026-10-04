#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
🎖️ ربات بازی جنگ جهانی دوم — نسخه نهایی
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
BOT_TOKEN = "152004939:-yVJrAHZWHVeopSTZUUltAAIkdjE3f7qNm8"
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


async def new_msg(q, ctx, text, kb=None):
    """ارسال پیام جدید (بدون ویرایش)"""
    try:
        await ctx.bot.send_message(
            chat_id=q.from_user.id,
            text=text,
            reply_markup=kb,
            parse_mode="Markdown"
        )
    except Exception as e:
        log.warning(f"send failed: {e}")


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
    try:
        await q.answer()
    except:
        pass
    await new_msg(q, ctx, "🌍 *کشورت رو انتخاب کن:*\n\n🟢 آسان  |  🟡 متوسط  |  🔴 سخت", countries_kb())


async def cb_pick_country(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    try:
        await q.answer()
    except:
        pass
    uid = q.from_user.id
    key = q.data.replace("pick_", "")
    c = COUNTRIES[key]

    existing = find_player_by_country(key)
    if existing and existing != uid:
        try:
            await q.answer(f"❌ {c['name']} قبلاً انتخاب شده!", show_alert=True)
        except:
            pass
        return

    start_new_game(uid, key)
    g = get_game(uid)

    await new_msg(q, ctx,
        f"✅ کشور انتخاب شد: {c['flag']} *{c['name']}*\n\n"
        f"{render_dashboard(g)}\n\n"
        f"از اینجا بازی شروع میشه!",
        main_menu_kb()
    )


async def cb_menu(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    try:
        await q.answer()
    except:
        pass
    g = get_game(q.from_user.id)
    if not g:
        await new_msg(q, ctx, "بازی پیدا نشد. /start رو بزن.")
        return
    await new_msg(q, ctx, render_dashboard(g), main_menu_kb())


async def cb_stats(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    try:
        await q.answer()
    except:
        pass
    g = get_game(q.from_user.id)
    await new_msg(q, ctx, render_dashboard(g), back_kb())


async def cb_help(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    try:
        await q.answer()
    except:
        pass
    text = (
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
        "卐زنده باد فاشیسم و نازیسم卐"
    )
    await new_msg(q, ctx, text, back_kb())
    # ═══════════════════════════════════════════════════════════════
#  💰 اقتصاد
# ═══════════════════════════════════════════════════════════════
async def cb_eco(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    try:
        await q.answer()
    except:
        pass
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
    await new_msg(q, ctx, text, kb)


# ═══════════════════════════════════════════════════════════════
#  💵 مالیات
# ═══════════════════════════════════════════════════════════════
TAX_INPUT = 10


async def cb_tax(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    try:
        await q.answer()
    except:
        pass
    g = get_game(q.from_user.id)
    text = (
        f"💵 *مالیات*\n"
        f"━━━━━━━━━━━━━━━━━━━━━━\n"
        f"الان: {g['tax_rate']}%\n"
        f"رضایت: {g['happiness']}%\n\n"
        f"عددی بین ۰ تا ۵۰ بفرست.\n"
        f"• بالای ۲۵٪ = نارضایتی هر نوبت\n"
        f"• زیر ۱۵٪ = رضایت بیشتر\n"
        f"• ۲۰٪ = تعادل"
    )
    await new_msg(q, ctx, text, InlineKeyboardMarkup([[menu_btn()]]))
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
    try:
        await q.answer()
    except:
        pass
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
    await new_msg(q, ctx, text, kb)


async def cb_speech(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    try:
        await q.answer()
    except:
        pass
    uid = q.from_user.id
    g = get_game(uid)

    if (g.get("speech_turns_left") or 0) > 0:
        try:
            await q.answer("❌ یه سخنرانی فعال داری. صبر کن تموم بشه.", show_alert=True)
        except:
            pass
        return
    if g["money"] < 100:
        try:
            await q.answer("❌ ۱۰۰ پول لازمه.", show_alert=True)
        except:
            pass
        return

    save_game(uid, money=g["money"] - 100, speech_turns_left=5)

    await new_msg(q, ctx,
        "📢 سخنرانی رهبر شروع شد!\n"
        "اثرش در ۵ نوبت آینده ظاهر میشه (+۲ رضایت هر نوبت).",
        main_menu_kb()
    )


async def cb_suppress(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    try:
        await q.answer()
    except:
        pass
    uid = q.from_user.id
    g = get_game(uid)

    if (g.get("suppress_cooldown") or 0) > 0:
        try:
            await q.answer("❌ سرکوب قبلی هنوز اثر داره. صبر کن.", show_alert=True)
        except:
            pass
        return
    if g["money"] < 50:
        try:
            await q.answer("❌ ۵۰ پول لازمه.", show_alert=True)
        except:
            pass
        return

    save_game(uid,
        money=g["money"] - 50,
        happiness=min(100, g["happiness"] + 10),
        suppress_cooldown=3,
        suppress_count=(g.get("suppress_count") or 0) + 1)

    await new_msg(q, ctx,
        "🚔 سرکوب شد!\n"
        "+۱۰ رضایت فوری (ولی بعد ۳ نوبت -۵ رضایت پایه)",
        main_menu_kb()
    )


# ═══════════════════════════════════════════════════════════════
#  ⚔️ ارتش
# ═══════════════════════════════════════════════════════════════
async def cb_army(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    try:
        await q.answer()
    except:
        pass
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
    await new_msg(q, ctx, "\n".join(lines), kb)


# ═══════════════════════════════════════════════════════════════
#  🪖 خرید سرباز
# ═══════════════════════════════════════════════════════════════
BUY_SOLDIER_QTY = 20


async def buy_soldier_start(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    try:
        await q.answer()
    except:
        pass
    text = (
        "🪖 *خرید سرباز*\n"
        "━━━━━━━━━━━━━━━━━━━━━━\n"
        "قیمت هر سرباز: ۱۰💰 + ۱👥\n\n"
        "چند تا سرباز می‌خوای؟\n"
        "عدد بفرست:"
    )
    await new_msg(q, ctx, text, InlineKeyboardMarkup([[InlineKeyboardButton("❌ انصراف", callback_data="army")]]))
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
    try:
        await q.answer()
    except:
        pass
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

    await new_msg(q, ctx, "\n".join(lines), InlineKeyboardMarkup(rows))


async def buytank_pick(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    try:
        await q.answer()
    except:
        pass
    name = q.data.replace("buytank_", "").replace("_", " ")
    g = get_game(q.from_user.id)

    unlocked = json.loads(g["research"] or "[]")
    if name not in unlocked:
        try:
            await q.answer("❌ اول این تانک رو تحقیق کن!", show_alert=True)
        except:
            pass
        return

    ctx.user_data["buy_tank_name"] = name

    tree = {n: (c, d, p) for n, c, d, p in RESEARCH.get(g["country"], [])}
    power = tree.get(name, (0, 0, 10))[2]
    money = int(power * 2 + 5)
    steel = max(1, power // 5)
    oil = max(0, power // 8)

    text = (
        f"🛡️ *خرید {name}*\n"
        f"━━━━━━━━━━━━━━━━━━━━━━\n"
        f"قیمت هر واحد: {money}💰 + {steel}⚙️ + {oil}🛢️\n"
        f"قدرت: {power} حمله\n\n"
        f"چند تا می‌خوای؟\nعدد بفرست:"
    )
    await new_msg(q, ctx, text, InlineKeyboardMarkup([[InlineKeyboardButton("❌ انصراف", callback_data="army")]]))
    return BUY_TANK_QTY


async def buytank_qty(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    try:
        qty = int(update.message.text.strip())
        if qty <= 0:
            raise ValueError
    except:
        await update.message.reply_text("❌ فقط یه عدد مثبت بفرست.")
        return BUY_TANK_QTY

    g = get_game(uid)
    name = ctx.user_data.get("buy_tank_name")
    if not name:
        await update.message.reply_text("❌ خطا. دوباره امتحان کن.")
        return ConversationHandler.END

    tree = {n: (c, d, p) for n, c, d, p in RESEARCH.get(g["country"], [])}
    power = tree.get(name, (0, 0, 10))[2]
    money = int(power * 2 + 5) * qty
    steel = max(1, power // 5) * qty
    oil = max(0, power // 8) * qty

    if g["money"] < money or g["steel"] < steel or g["oil"] < oil:
        await update.message.reply_text(
            f"❌ منابع کافی نداری!\n\n"
            f"نیاز: {money}💰 + {steel}⚙️ + {oil}🛢️\n"
            f"داری: {g['money']}💰 + {g['steel']}⚙️ + {g['oil']}🛢️"
        )
        return ConversationHandler.END

    unit_tanks = json.loads(g.get("unit_tanks") or "{}")
    unit_tanks[name] = unit_tanks.get(name, 0) + qty

    save_game(uid,
        money=g["money"] - money,
        steel=g["steel"] - steel,
        oil=g["oil"] - oil,
        unit_tanks=json.dumps(unit_tanks))

    await update.message.reply_text(
        f"✅ *{qty} {name}* ساخته شد!\n"
        f"هزینه: {money}💰 + {steel}⚙️ + {oil}🛢️",
        parse_mode="Markdown",
        reply_markup=main_menu_kb()
    )
    return ConversationHandler.END


# ═══════════════════════════════════════════════════════════════
#  ✈️ خرید هواپیما
# ═══════════════════════════════════════════════════════════════
BUY_PLANE_QTY = 22


async def buy_plane_start(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    try:
        await q.answer()
    except:
        pass
    g = get_game(q.from_user.id)
    units = get_available_units(g, "plane")

    lines = [f"✈️ *خرید هواپیما — {COUNTRIES[g['country']]['name']}*", "━━━━━━━━━━━━━━━━━━━━━━"]
    rows = []
    for u in units:
        if u["unlocked"]:
            lines.append(f"✅ {u['name']} — {u['money']}💰 + {u['steel']}⚙️ + {u['oil']}🛢️ (قدرت {u['attack']})")
            rows.append([InlineKeyboardButton(
                f"✈️ {u['name']} ({u['money']}💰)",
                callback_data=f"buyplane_{u['name'].replace(' ', '_')}"
            )])
        else:
            lines.append(f"🔒 {u['name']} — {u['money']}💰 (تحقیق کن)")
    rows.append([InlineKeyboardButton("❌ انصراف", callback_data="army")])

    await new_msg(q, ctx, "\n".join(lines), InlineKeyboardMarkup(rows))


async def buyplane_pick(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    try:
        await q.answer()
    except:
        pass
    name = q.data.replace("buyplane_", "").replace("_", " ")
    g = get_game(q.from_user.id)
    unlocked = json.loads(g["research"] or "[]")
    if name not in unlocked:
        try:
            await q.answer("❌ اول این هواپیما رو تحقیق کن!", show_alert=True)
        except:
            pass
        return

    ctx.user_data["buy_plane_name"] = name
    tree = {n: (c, d, p) for n, c, d, p in RESEARCH.get(g["country"], [])}
    power = tree.get(name, (0, 0, 10))[2]
    money = int(power * 2 + 5)
    steel = max(1, power // 6)
    oil = max(1, power // 4)

    text = (
        f"✈️ *خرید {name}*\n"
        f"━━━━━━━━━━━━━━━━━━━━━━\n"
        f"قیمت هر واحد: {money}💰 + {steel}⚙️ + {oil}🛢️\n"
        f"قدرت: {power} حمله\n\n"
        f"چند تا می‌خوای؟"
    )
    await new_msg(q, ctx, text, InlineKeyboardMarkup([[InlineKeyboardButton("❌ انصراف", callback_data="army")]]))
    return BUY_PLANE_QTY


async def buyplane_qty(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    try:
        qty = int(update.message.text.strip())
        if qty <= 0:
            raise ValueError
    except:
        await update.message.reply_text("❌ فقط یه عدد مثبت بفرست.")
        return BUY_PLANE_QTY

    g = get_game(uid)
    name = ctx.user_data.get("buy_plane_name")
    if not name:
        await update.message.reply_text("❌ خطا.")
        return ConversationHandler.END

    tree = {n: (c, d, p) for n, c, d, p in RESEARCH.get(g["country"], [])}
    power = tree.get(name, (0, 0, 10))[2]
    money = int(power * 2 + 5) * qty
    steel = max(1, power // 6) * qty
    oil = max(1, power // 4) * qty

    if g["money"] < money or g["steel"] < steel or g["oil"] < oil:
        await update.message.reply_text(
            f"❌ منابع کافی نداری!\nنیاز: {money}💰 + {steel}⚙️ + {oil}🛢️"
        )
        return ConversationHandler.END

    unit_planes = json.loads(g.get("unit_planes") or "{}")
    unit_planes[name] = unit_planes.get(name, 0) + qty

    save_game(uid,
        money=g["money"] - money,
        steel=g["steel"] - steel,
        oil=g["oil"] - oil,
        unit_planes=json.dumps(unit_planes))

    await update.message.reply_text(
        f"✅ *{qty} {name}* ساخته شد!\nهزینه: {money}💰 + {steel}⚙️ + {oil}🛢️",
        parse_mode="Markdown",
        reply_markup=main_menu_kb()
    )
    return ConversationHandler.END


# ═══════════════════════════════════════════════════════════════
#  🚢 خرید کشتی
# ═══════════════════════════════════════════════════════════════
BUY_SHIP_QTY = 23


async def buy_ship_start(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    try:
        await q.answer()
    except:
        pass
    g = get_game(q.from_user.id)
    units = get_available_units(g, "ship")

    lines = [f"🚢 *خرید کشتی — {COUNTRIES[g['country']]['name']}*", "━━━━━━━━━━━━━━━━━━━━━━"]
    rows = []
    for u in units:
        if u["unlocked"]:
            lines.append(f"✅ {u['name']} — {u['money']}💰 + {u['steel']}⚙️ + {u['oil']}🛢️ (قدرت {u['attack']})")
            rows.append([InlineKeyboardButton(
                f"🚢 {u['name']} ({u['money']}💰)",
                callback_data=f"buyship_{u['name'].replace(' ', '_')}"
            )])
        else:
            lines.append(f"🔒 {u['name']} — {u['money']}💰 (تحقیق کن)")
    rows.append([InlineKeyboardButton("❌ انصراف", callback_data="army")])

    await new_msg(q, ctx, "\n".join(lines), InlineKeyboardMarkup(rows))


async def buyship_pick(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    try:
        await q.answer()
    except:
        pass
    name = q.data.replace("buyship_", "").replace("_", " ")
    g = get_game(q.from_user.id)
    unlocked = json.loads(g["research"] or "[]")
    if name not in unlocked:
        try:
            await q.answer("❌ اول این کشتی رو تحقیق کن!", show_alert=True)
        except:
            pass
        return

    ctx.user_data["buy_ship_name"] = name
    tree = {n: (c, d, p) for n, c, d, p in RESEARCH.get(g["country"], [])}
    power = tree.get(name, (0, 0, 15))[2]
    money = int(power * 3 + 20)
    steel = max(2, power // 3)
    oil = max(1, power // 5)

    text = (
        f"🚢 *خرید {name}*\n"
        f"━━━━━━━━━━━━━━━━━━━━━━\n"
        f"قیمت هر واحد: {money}💰 + {steel}⚙️ + {oil}🛢️\n"
        f"قدرت: {power} حمله\n\n"
        f"چند تا می‌خوای؟"
    )
    await new_msg(q, ctx, text, InlineKeyboardMarkup([[InlineKeyboardButton("❌ انصراف", callback_data="army")]]))
    return BUY_SHIP_QTY


async def buyship_qty(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    try:
        qty = int(update.message.text.strip())
        if qty <= 0:
            raise ValueError
    except:
        await update.message.reply_text("❌ فقط یه عدد مثبت بفرست.")
        return BUY_SHIP_QTY

    g = get_game(uid)
    name = ctx.user_data.get("buy_ship_name")
    if not name:
        await update.message.reply_text("❌ خطا.")
        return ConversationHandler.END

    tree = {n: (c, d, p) for n, c, d, p in RESEARCH.get(g["country"], [])}
    power = tree.get(name, (0, 0, 15))[2]
    money = int(power * 3 + 20) * qty
    steel = max(2, power // 3) * qty
    oil = max(1, power // 5) * qty

    if g["money"] < money or g["steel"] < steel or g["oil"] < oil:
        await update.message.reply_text(
            f"❌ منابع کافی نداری!\nنیاز: {money}💰 + {steel}⚙️ + {oil}🛢️"
        )
        return ConversationHandler.END

    unit_ships = json.loads(g.get("unit_ships") or "{}")
    unit_ships[name] = unit_ships.get(name, 0) + qty

    save_game(uid,
        money=g["money"] - money,
        steel=g["steel"] - steel,
        oil=g["oil"] - oil,
        unit_ships=json.dumps(unit_ships))

    await update.message.reply_text(
        f"✅ *{qty} {name}* ساخته شد!\nهزینه: {money}💰 + {steel}⚙️ + {oil}🛢️",
        parse_mode="Markdown",
        reply_markup=main_menu_kb()
    )
    return ConversationHandler.END
    # ═══════════════════════════════════════════════════════════════
#  🔬 تحقیقات
# ═══════════════════════════════════════════════════════════════
async def cb_res(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    try:
        await q.answer()
    except:
        pass
    g = get_game(q.from_user.id)
    tree = RESEARCH.get(g["country"], [])
    unlocked = json.loads(g["research"] or "[]")

    lines = [f"🔬 *درخت تحقیقات — {COUNTRIES[g['country']]['name']}*\n"]
    rows = []
    for name, cost, days, power in tree:
        if name in unlocked:
            lines.append(f"✅ {name} (قدرت {power})")
        else:
            lines.append(f"🔒 {name} — {cost}💰 ({days} نوبت)")
            rows.append([InlineKeyboardButton(
                f"🔬 {name} ({cost}💰)",
                callback_data=f"res_{name.replace(' ', '_')}"
            )])
    rows.append([menu_btn()])

    await new_msg(q, ctx, "\n".join(lines), InlineKeyboardMarkup(rows))


async def cb_research(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    try:
        await q.answer()
    except:
        pass
    uid = q.from_user.id
    name = q.data.replace("res_", "").replace("_", " ")
    g = get_game(uid)
    tree = RESEARCH.get(g["country"], [])

    for n, cost, days, power in tree:
        if n == name:
            if g["money"] < cost:
                try:
                    await q.answer("❌ پول کافی نداری.", show_alert=True)
                except:
                    pass
                return
            unlocked = json.loads(g["research"] or "[]")
            if name in unlocked:
                try:
                    await q.answer("قبلاً تحقیق شده.", show_alert=True)
                except:
                    pass
                return
            unlocked.append(name)
            save_game(uid, money=g["money"] - cost, research=json.dumps(unlocked))
            try:
                await q.answer(f"✅ {name} تحقیق شد!", show_alert=True)
            except:
                pass
            await cb_res(update, ctx)
            return


# ═══════════════════════════════════════════════════════════════
#  🏗️ پروژه‌ها
# ═══════════════════════════════════════════════════════════════
async def cb_proj(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    try:
        await q.answer()
    except:
        pass
    g = get_game(q.from_user.id)
    completed = json.loads(g["completed_projects"] or "[]")
    building = json.loads(g["projects"] or "[]")

    lines = ["🏗️ *پروژه‌های ملی*\n"]
    rows = []

    atomic_turn = turn_to_atomic_date()
    atomic_used = get_setting("atomic_used", "false") == "true"
    can_build_atom = False
    if g["country"] in ("usa", "germany") and g["turn"] >= atomic_turn:
        can_build_atom = True
    elif atomic_used and g["turn"] >= atomic_turn:
        can_build_atom = True

    if can_build_atom:
        if "atomic_bomb" not in completed:
            building_now = any(x.split(":")[0] == "atomic_bomb" for x in building)
            if building_now:
                lines.append("🔨 ☢️ پروژه بمب اتم (در حال ساخت)")
            else:
                lines.append(f"☢️ *پروژه بمب اتم* — ۵۰۰۰💰 + ۵۰۰⚙️ + ۲۰۰🛢️ (۳۰ نوبت)")
                rows.append([InlineKeyboardButton("☢️ پروژه بمب اتم", callback_data="build_atomic")])

    for key, p in PROJECTS.items():
        if key in completed:
            lines.append(f"✅ {p['name']} (تکمیل)")
        else:
            b = any(x.split(":")[0] == key for x in building)
            if b:
                lines.append(f"🔨 {p['name']} (در حال ساخت)")
            else:
                lines.append(f"🆕 {p['name']} — {p['money']}💰 + {p['steel']}⚙️ ({p['days']} نوبت)")
                rows.append([InlineKeyboardButton(
                    f"🏗️ {p['name']}",
                    callback_data=f"build_{key}"
                )])
    rows.append([menu_btn()])

    await new_msg(q, ctx, "\n".join(lines), InlineKeyboardMarkup(rows))


async def cb_build(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    try:
        await q.answer()
    except:
        pass
    uid = q.from_user.id
    key = q.data.replace("build_", "")

    if key == "atomic":
        g = get_game(uid)
        completed = json.loads(g["completed_projects"] or "[]")
        if "atomic_bomb" in completed:
            try:
                await q.answer("قبلاً ساخته شده.", show_alert=True)
            except:
                pass
            return
        if g["money"] < 5000 or g["steel"] < 500 or g["oil"] < 200:
            try:
                await q.answer("❌ نیاز: ۵۰۰۰💰 + ۵۰۰⚙️ + ۲۰۰🛢️", show_alert=True)
            except:
                pass
            return
        projects = json.loads(g["projects"] or "[]")
        projects.append("atomic_bomb:30")
        save_game(uid,
            money=g["money"] - 5000,
            steel=g["steel"] - 500,
            oil=g["oil"] - 200,
            projects=json.dumps(projects))
        try:
            await q.answer("☢️ پروژه بمب اتم شروع شد! (۳۰ نوبت)", show_alert=True)
        except:
            pass
        await cb_proj(update, ctx)
        return

    p = PROJECTS.get(key)
    if not p:
        try:
            await q.answer("❌ پروژه پیدا نشد.", show_alert=True)
        except:
            pass
        return

    g = get_game(uid)
    if g["money"] < p["money"] or g["steel"] < p["steel"]:
        try:
            await q.answer(f"❌ نیاز: {p['money']}💰 + {p['steel']}⚙️", show_alert=True)
        except:
            pass
        return

    projects = json.loads(g["projects"] or "[]")
    if any(x.split(":")[0] == key for x in projects):
        try:
            await q.answer("در حال ساخت است.", show_alert=True)
        except:
            pass
        return

    projects.append(f"{key}:{p['days']}")
    save_game(uid,
        money=g["money"] - p["money"],
        steel=g["steel"] - p["steel"],
        projects=json.dumps(projects))
    try:
        await q.answer(f"✅ {p['name']} شروع شد ({p['days']} نوبت)", show_alert=True)
    except:
        pass
    await cb_proj(update, ctx)


# ═══════════════════════════════════════════════════════════════
#  🎯 حمله
# ═══════════════════════════════════════════════════════════════
ATTACK_TARGET, ATTACK_FORCE, ATTACK_QTY = range(30, 33)


async def cb_attack(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    try:
        await q.answer()
    except:
        pass
    uid = q.from_user.id
    g = get_game(uid)
    players = get_active_players(exclude_uid=uid)

    if not players:
        await new_msg(q, ctx,
            "⚔️ *هنوز کسی تو بازی نیست که بهش حمله کنی.*\n\n"
            "صبر کن بازیکن‌های دیگه بیان.",
            back_kb()
        )
        return ConversationHandler.END

    rows = []
    for p in players:
        c = COUNTRIES[p["country"]]
        can, way = can_attack(g["country"], p["country"])
        marker = "✅" if can else "🔒"
        rows.append([InlineKeyboardButton(
            f"{marker} {c['flag']} {c['name']}",
            callback_data=f"atk_{p['country']}"
        )])
    rows.append([InlineKeyboardButton("❌ انصراف", callback_data="menu")])

    text = (
        f"🎯 *حمله — هدف رو انتخاب کن:*\n\n"
        f"⚔️ قدرت حمله تو: {fmt(compute_army_power(g, 'attack'))}\n"
        f"🗺️ ✅ = راه داری | 🔒 = راه نداری"
    )
    await new_msg(q, ctx, text, InlineKeyboardMarkup(rows))
    return ATTACK_TARGET


async def attack_target(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    try:
        await q.answer()
    except:
        pass
    uid = q.from_user.id
    target = q.data.replace("atk_", "")
    g = get_game(uid)

    can, way = can_attack(g["country"], target)
    if not can:
        try:
            await q.answer(f"❌ {way}", show_alert=True)
        except:
            pass
        return ATTACK_TARGET

    ctx.user_data["target"] = target
    ctx.user_data["force"] = {"soldiers": 0, "tanks": 0, "planes": 0, "ships": 0}
    c = COUNTRIES[target]

    text = (
        f"🎯 هدف: {c['flag']} *{c['name']}*\n"
        f"راه: {way}\n\n"
        f"نیروهات رو مشخص کن. روی هر واحد بزن تا تعداد بپرسه:"
    )
    await new_msg(q, ctx, text, attack_force_kb(ctx.user_data["force"]))
    return ATTACK_FORCE


def attack_force_kb(force):
    return InlineKeyboardMarkup([
        [InlineKeyboardButton(f"🪖 سرباز: {force['soldiers']}", callback_data="af_soldiers"),
         InlineKeyboardButton(f"🛡️ تانک: {force['tanks']}", callback_data="af_tanks")],
        [InlineKeyboardButton(f"✈️ هواپیما: {force['planes']}", callback_data="af_planes"),
         InlineKeyboardButton(f"🚢 کشتی: {force['ships']}", callback_data="af_ships")],
        [InlineKeyboardButton("🚀 شروع حمله", callback_data="af_go")],
        [InlineKeyboardButton("❌ انصراف", callback_data="menu")],
    ])


async def attack_pick_unit(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    try:
        await q.answer()
    except:
        pass
    field = q.data.replace("af_", "")
    ctx.user_data["picking_field"] = field

    uid = q.from_user.id
    g = get_game(uid)
    total = compute_total_units(g)
    have = total.get(field, 0)

    text = (
        f"🔢 چند تا *{field}* رو بفرستی؟\n\n"
        f"تو {have} تا داری.\n"
        f"عدد بفرست:"
    )
    await new_msg(q, ctx, text, InlineKeyboardMarkup([[InlineKeyboardButton("🔙 برگشت", callback_data="af_back")]]))
    return ATTACK_QTY


async def attack_qty(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    try:
        qty = int(update.message.text.strip())
        if qty < 0:
            raise ValueError
    except:
        await update.message.reply_text("❌ عدد مثبت بفرست.")
        return ATTACK_QTY

    uid = update.effective_user.id
    g = get_game(uid)
    field = ctx.user_data.get("picking_field")
    total = compute_total_units(g)
    have = total.get(field, 0)

    if qty > have:
        await update.message.reply_text(f"❌ نداری! تو {have} تا داری.")
        return ATTACK_QTY

    ctx.user_data["force"][field] = qty
    c = COUNTRIES[ctx.user_data["target"]]
    force = ctx.user_data["force"]

    cost_info = compute_attack_cost(g, ctx.user_data["target"], force)

    await update.message.reply_text(
        f"🎯 هدف: {c['flag']} *{c['name']}*\n\n"
        f"نیروها:\n"
        f"🪖 {force['soldiers']}  |  🛡️ {force['tanks']}\n"
        f"✈️ {force['planes']}  |  🚢 {force['ships']}\n\n"
        f"💰 هزینه تخمینی: {fmt(cost_info['money'])}💰 + {fmt(cost_info['oil'])}🛢️ + {fmt(cost_info['food'])}🍞",
        parse_mode="Markdown",
        reply_markup=attack_force_kb(force)
    )
    return ATTACK_FORCE


async def af_back(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    try:
        await q.answer()
    except:
        pass
    c = COUNTRIES[ctx.user_data["target"]]
    text = f"🎯 هدف: {c['flag']} *{c['name']}*\n\nنیروهات رو تنظیم کن:"
    await new_msg(q, ctx, text, attack_force_kb(ctx.user_data["force"]))
    return ATTACK_FORCE


def compute_attack_cost(g, target_key, force):
    distance = get_distance(g["country"], target_key)
    multiplier = get_distance_multiplier(distance)

    base_money = 100
    unit_money = (force["soldiers"] * 10 + force["tanks"] * 20 +
                  force["planes"] * 25 + force["ships"] * 50)
    unit_oil = (force["tanks"] * 3 + force["planes"] * 5 + force["ships"] * 10)
    unit_food = force["soldiers"] * 1

    return {
        "money": int((base_money + unit_money) * multiplier),
        "oil": int(unit_oil * multiplier),
        "food": int(unit_food * multiplier),
        "distance": distance,
        "multiplier": multiplier
    }


# ═══════════════════════════════════════════════════════════════
#  🚀 اجرای حمله
# ═══════════════════════════════════════════════════════════════
async def attack_go(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    try:
        await q.answer()
    except:
        pass
    uid = q.from_user.id
    g = get_game(uid)
    force = ctx.user_data.get("force", {})
    target = ctx.user_data.get("target")

    if sum(force.values()) == 0:
        try:
            await q.answer("❌ حداقل یه واحد انتخاب کن.", show_alert=True)
        except:
            pass
        return ATTACK_FORCE

    can, way = can_attack(g["country"], target)
    if way == "دریایی":
        total_transport = force["soldiers"] + force["tanks"]
        ship_capacity = force["ships"] * SHIP_CAPACITY
        if total_transport > ship_capacity:
            try:
                await q.answer(
                    f"❌ کشتی کافی نداری!\nنیاز: {(total_transport + SHIP_CAPACITY - 1) // SHIP_CAPACITY} کشتی\n"
                    f"داری: {force['ships']}",
                    show_alert=True
                )
            except:
                pass
            return ATTACK_FORCE

    cost = compute_attack_cost(g, target, force)

    if g["money"] < cost["money"]:
        try:
            await q.answer(f"❌ پول کافی نداری! نیاز: {fmt(cost['money'])}", show_alert=True)
        except:
            pass
        return ATTACK_FORCE
    if g["oil"] < cost["oil"]:
        try:
            await q.answer(f"❌ نفت کافی نداری! نیاز: {fmt(cost['oil'])}", show_alert=True)
        except:
            pass
        return ATTACK_FORCE
    if g["food"] < cost["food"]:
        try:
            await q.answer(f"❌ غذا کافی نداری! نیاز: {fmt(cost['food'])}", show_alert=True)
        except:
            pass
        return ATTACK_FORCE

    save_game(uid,
        money=g["money"] - cost["money"],
        oil=g["oil"] - cost["oil"],
        food=g["food"] - cost["food"],
        war_active=1)

    unit_tanks = json.loads(g.get("unit_tanks") or "{}")
    unit_planes = json.loads(g.get("unit_planes") or "{}")
    unit_ships = json.loads(g.get("unit_ships") or "{}")
    tree = {n: (c, d, p) for n, c, d, p in RESEARCH.get(g["country"], [])}

    my_atk = force["soldiers"] * 6
    for name, cnt in unit_tanks.items():
        if cnt > 0 and name in tree:
            used = min(cnt, force["tanks"])
            my_atk += used * tree[name][2]
            force["tanks"] -= used
    for name, cnt in unit_planes.items():
        if cnt > 0 and name in tree:
            used = min(cnt, force["planes"])
            my_atk += used * tree[name][2]
            force["planes"] -= used
    for name, cnt in unit_ships.items():
        if cnt > 0 and name in tree:
            used = min(cnt, force["ships"])
            my_atk += used * tree[name][2]
            force["ships"] -= used

    target_uid = find_player_by_country(target)
    if target_uid and not is_npc(target_uid):
        tg = get_game(target_uid)
        enemy_def = compute_army_power(tg, "defense")
    else:
        enemy_def = random.randint(100, 300)

    c = COUNTRIES[target]

    if my_atk > enemy_def:
        pct_gain = min(100, max(20, int(my_atk / enemy_def * 30)))
        existing = get_territory_owner(target)
        old_pct = existing["percentage"] if existing else 0
        new_pct = min(100, old_pct + pct_gain)
        set_territory_owner(target, g["country"], new_pct)

        losses = {f: int(force.get(f, 0) * random.uniform(0.05, 0.2)) for f in force}
        new_soldiers = g["soldiers"] - losses.get("soldiers", 0)
        new_unit_tanks = json.loads(g.get("unit_tanks") or "{}")
        new_unit_planes = json.loads(g.get("unit_planes") or "{}")
        new_unit_ships = json.loads(g.get("unit_ships") or "{}")

        to_remove_tank = losses.get("tanks", 0)
        for name in list(new_unit_tanks.keys()):
            if to_remove_tank <= 0:
                break
            remove = min(new_unit_tanks[name], to_remove_tank)
            new_unit_tanks[name] -= remove
            to_remove_tank -= remove
            if new_unit_tanks[name] <= 0:
                del new_unit_tanks[name]

        to_remove_plane = losses.get("planes", 0)
        for name in list(new_unit_planes.keys()):
            if to_remove_plane <= 0:
                break
            remove = min(new_unit_planes[name], to_remove_plane)
            new_unit_planes[name] -= remove
            to_remove_plane -= remove
            if new_unit_planes[name] <= 0:
                del new_unit_planes[name]

        to_remove_ship = losses.get("ships", 0)
        for name in list(new_unit_ships.keys()):
            if to_remove_ship <= 0:
                break
            remove = min(new_unit_ships[name], to_remove_ship)
            new_unit_ships[name] -= remove
            to_remove_ship -= remove
            if new_unit_ships[name] <= 0:
                del new_unit_ships[name]

        save_game(uid,
            soldiers=max(0, new_soldiers),
            unit_tanks=json.dumps(new_unit_tanks),
            unit_planes=json.dumps(new_unit_planes),
            unit_ships=json.dumps(new_unit_ships))

        result = (
            f"🏆 *پیروزی!*\n\n"
            f"هدف: {c['flag']} {c['name']}\n"
            f"قدرت حمله تو: {fmt(my_atk)}\n"
            f"دفاع دشمن: {fmt(enemy_def)}\n"
            f"مسافت: ×{cost['multiplier']}\n\n"
            f"تلفات:\n🪖 {losses.get('soldiers',0)}  🛡️ {losses.get('tanks',0)}  ✈️ {losses.get('planes',0)}  🚢 {losses.get('ships',0)}\n\n"
            f"📊 اشغال {c['name']}: {new_pct}%"
        )

        if new_pct >= 100:
            result += f"\n\n🏴 {c['name']} کاملاً فتح شد!"
            kb = back_kb()
        else:
            kb = InlineKeyboardMarkup([
                [InlineKeyboardButton("🏝️ مستعمره کن", callback_data=f"colony_{target}")],
                [InlineKeyboardButton("🎯 ادامه حمله", callback_data=f"atk_{target}")],
                [menu_btn()],
            ])

        await new_msg(q, ctx, result, kb)

    else:
        losses = {f: int(force.get(f, 0) * random.uniform(0.3, 0.6)) for f in force}
        new_soldiers = g["soldiers"] - losses.get("soldiers", 0)
        new_unit_tanks = json.loads(g.get("unit_tanks") or "{}")
        new_unit_planes = json.loads(g.get("unit_planes") or "{}")
        new_unit_ships = json.loads(g.get("unit_ships") or "{}")

        for name in list(new_unit_tanks.keys()):
            new_unit_tanks[name] = max(0, new_unit_tanks[name] - losses.get("tanks", 0))
            if new_unit_tanks[name] <= 0:
                del new_unit_tanks[name]
        for name in list(new_unit_planes.keys()):
            new_unit_planes[name] = max(0, new_unit_planes[name] - losses.get("planes", 0))
            if new_unit_planes[name] <= 0:
                del new_unit_planes[name]
        for name in list(new_unit_ships.keys()):
            new_unit_ships[name] = max(0, new_unit_ships[name] - losses.get("ships", 0))
            if new_unit_ships[name] <= 0:
                del new_unit_ships[name]

        save_game(uid,
            soldiers=max(0, new_soldiers),
            unit_tanks=json.dumps(new_unit_tanks),
            unit_planes=json.dumps(new_unit_planes),
            unit_ships=json.dumps(new_unit_ships))

        result = (
            f"💀 *شکست!*\n\n"
            f"هدف: {c['flag']} {c['name']}\n"
            f"قدرت حمله تو: {fmt(my_atk)}\n"
            f"دفاع دشمن: {fmt(enemy_def)}\n\n"
            f"تلفات سنگین:\n🪖 {losses.get('soldiers',0)}  🛡️ {losses.get('tanks',0)}  ✈️ {losses.get('planes',0)}  🚢 {losses.get('ships',0)}"
        )
        await new_msg(q, ctx, result, back_kb())

    return ConversationHandler.END


async def cb_colony(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    try:
        await q.answer()
    except:
        pass
    uid = q.from_user.id
    target = q.data.replace("colony_", "")
    g = get_game(uid)
    colonies = json.loads(g["colonies"] or "[]")
    if target not in colonies:
        colonies.append(target)
    save_game(uid, colonies=json.dumps(colonies))
    c = COUNTRIES[target]

    await new_msg(q, ctx,
        f"🏝️ {c['flag']} {c['name']} مستعمره شد!\n\n+۵۰٪ تولیدش به تو می‌رسه.",
        main_menu_kb()
    )


# ═══════════════════════════════════════════════════════════════
#  🕵️ جاسوسی
# ═══════════════════════════════════════════════════════════════
async def cb_spy(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    try:
        await q.answer()
    except:
        pass
    uid = q.from_user.id
    g = get_game(uid)
    players = get_active_players(exclude_uid=uid)

    if not players:
        await new_msg(q, ctx, "🕵️ *هنوز بازیکن دیگه‌ای نیست.*", back_kb())
        return

    rows = []
    for p in players:
        c = COUNTRIES[p["country"]]
        rows.append([InlineKeyboardButton(
            f"🕵️ {c['flag']} {c['name']}",
            callback_data=f"spy_{p['country']}"
        )])
    rows.append([menu_btn()])

    text = (
        f"🕵️ *جاسوسی*\n\n"
        f"هزینه: ۵۰💰\n"
        f"شانس لو رفتن: ۴۰٪\n\n"
        f"هدف رو انتخاب کن:"
    )
    await new_msg(q, ctx, text, InlineKeyboardMarkup(rows))


async def cb_spy_do(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    try:
        await q.answer()
    except:
        pass
    uid = q.from_user.id
    target = q.data.replace("spy_", "")
    g = get_game(uid)

    if g["money"] < 50:
        try:
            await q.answer("❌ ۵۰ پول لازمه.", show_alert=True)
        except:
            pass
        return

    save_game(uid, money=g["money"] - 50)
    caught = random.random() < 0.40

    if caught:
        result = f"🚨 *لو رفتی!*\n\nجاسوست گیر افتاد و {COUNTRIES[target]['name']} فهمید."
    else:
        target_uid = find_player_by_country(target)
        tg = get_game(target_uid) if target_uid else None
        if tg:
            unit_tanks = json.loads(tg.get("unit_tanks") or "{}")
            unit_planes = json.loads(tg.get("unit_planes") or "{}")
            unit_ships = json.loads(tg.get("unit_ships") or "{}")

            lines = [
                f"✅ *موفق!*",
                f"━━━━━━━━━━━━━━━━━━━━━━",
                f"اطلاعات {COUNTRIES[target]['flag']} {COUNTRIES[target]['name']}:",
                f"💰 پول: {fmt(tg['money'])}",
                f"⚙️ فولاد: {fmt(tg['steel'])}",
                f"🛢️ نفت: {fmt(tg['oil'])}",
                f"🪖 سرباز: {fmt(tg['soldiers'])}",
            ]
            for name, cnt in unit_tanks.items():
                lines.append(f"🛡️ {name}: {fmt(cnt)}")
            for name, cnt in unit_planes.items():
                lines.append(f"✈️ {name}: {fmt(cnt)}")
            for name, cnt in unit_ships.items():
                lines.append(f"🚢 {name}: {fmt(cnt)}")
            result = "\n".join(lines)
        else:
            result = f"✅ *موفق!*\n\nاطلاعات {COUNTRIES[target]['name']} به دست اومد."

    await new_msg(q, ctx, result, back_kb())
    # ═══════════════════════════════════════════════════════════════
#  🤝 دیپلماسی
# ═══════════════════════════════════════════════════════════════
DIP_TYPES = {
    "ally":   "🤝 اتحاد",
    "peace":  "☮️ صلح",
    "war":    "⚔️ اعلام جنگ",
    "nap":    "🤐 عدم تخاصم",
    "tech":   "🔄 تبادل فناوری",
    "trade":  "📦 قرارداد تجاری",
    "talk":   "💬 مذاکره",
}

DIP_TALK_MSG = 40


async def cb_dip(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    try:
        await q.answer()
    except:
        pass
    g = get_game(q.from_user.id)

    allies = json.loads(g["allies"] or "[]")
    wars = json.loads(g["wars"] or "[]")
    allies_names = ", ".join(COUNTRIES[a]["name"] for a in allies if a in COUNTRIES) or "هیچ"
    wars_names = ", ".join(COUNTRIES[a]["name"] for a in wars if a in COUNTRIES) or "هیچ"

    text = (
        f"🤝 *دیپلماسی*\n"
        f"━━━━━━━━━━━━━━━━━━━━━━\n"
        f"متحدین: {allies_names}\n"
        f"در جنگ با: {wars_names}"
    )
    kb = InlineKeyboardMarkup([
        [InlineKeyboardButton("🤝 پیشنهاد اتحاد", callback_data="dip_ally")],
        [InlineKeyboardButton("☮️ پیشنهاد صلح", callback_data="dip_peace")],
        [InlineKeyboardButton("⚔️ اعلام جنگ", callback_data="dip_war")],
        [InlineKeyboardButton("🤐 پیمان عدم تخاصم", callback_data="dip_nap")],
        [InlineKeyboardButton("🔄 تبادل فناوری", callback_data="dip_tech")],
        [InlineKeyboardButton("📦 قرارداد تجاری", callback_data="dip_trade")],
        [InlineKeyboardButton("💬 مذاکره خصوصی", callback_data="dip_talk")],
        [menu_btn()],
    ])
    await new_msg(q, ctx, text, kb)


async def _dip_pick_target(update, ctx, kind):
    q = update.callback_query
    uid = q.from_user.id
    players = get_active_players(exclude_uid=uid)

    if not players:
        await new_msg(q, ctx, "🤝 *هنوز بازیکن دیگه‌ای نیست.*", back_kb())
        return

    rows = []
    for p in players:
        c = COUNTRIES[p["country"]]
        rows.append([InlineKeyboardButton(
            f"{c['flag']} {c['name']}",
            callback_data=f"dipt_{kind}_{p['country']}"
        )])
    rows.append([InlineKeyboardButton("🔙 بازگشت", callback_data="dip")])

    text = f"🎯 *{DIP_TYPES.get(kind, kind)}* — کشور هدف:"
    await new_msg(q, ctx, text, InlineKeyboardMarkup(rows))


async def cb_dip_ally(update, ctx):
    q = update.callback_query
    try:
        await q.answer()
    except:
        pass
    await _dip_pick_target(update, ctx, "ally")


async def cb_dip_peace(update, ctx):
    q = update.callback_query
    try:
        await q.answer()
    except:
        pass
    await _dip_pick_target(update, ctx, "peace")


async def cb_dip_war(update, ctx):
    q = update.callback_query
    try:
        await q.answer()
    except:
        pass
    await _dip_pick_target(update, ctx, "war")


async def cb_dip_nap(update, ctx):
    q = update.callback_query
    try:
        await q.answer()
    except:
        pass
    await _dip_pick_target(update, ctx, "nap")


async def cb_dip_tech(update, ctx):
    q = update.callback_query
    try:
        await q.answer()
    except:
        pass
    await _dip_pick_target(update, ctx, "tech")


async def cb_dip_trade(update, ctx):
    q = update.callback_query
    try:
        await q.answer()
    except:
        pass
    await _dip_pick_target(update, ctx, "trade")


async def cb_dip_talk(update, ctx):
    q = update.callback_query
    try:
        await q.answer()
    except:
        pass
    await _dip_pick_target(update, ctx, "talk")


async def cb_dip_confirm(update, ctx):
    q = update.callback_query
    try:
        await q.answer()
    except:
        pass
    uid = q.from_user.id
    parts = q.data.split("_", 2)
    kind = parts[1]
    target_key = parts[2]
    g = get_game(uid)
    c = COUNTRIES[target_key]

    target_uid = find_player_by_country(target_key)
    if not target_uid or is_npc(target_uid):
        await new_msg(q, ctx, f"🤖 {c['name']} بازیکن نداره.", back_kb())
        return

    if kind == "war":
        wars = json.loads(g["wars"] or "[]")
        if target_key not in wars:
            wars.append(target_key)
            save_game(uid, wars=json.dumps(wars))
        tg = get_game(target_uid)
        t_wars = json.loads(tg["wars"] or "[]")
        if g["country"] not in t_wars:
            t_wars.append(g["country"])
            save_game(target_uid, wars=json.dumps(t_wars))

        await new_msg(q, ctx,
            f"⚔️ *جنگ اعلام شد!*\n\n"
            f"{COUNTRIES[g['country']]['flag']} {COUNTRIES[g['country']]['name']} "
            f"به {c['flag']} {c['name']} اعلام جنگ کرد.",
            back_kb()
        )
        try:
            await ctx.bot.send_message(
                target_uid,
                f"⚔️ *جنگ!*\n\n{COUNTRIES[g['country']]['flag']} {COUNTRIES[g['country']]['name']} "
                f"به تو اعلام جنگ کرد!",
                parse_mode="Markdown"
            )
        except:
            pass
        return

    if kind == "talk":
        ctx.user_data["talk_target"] = target_uid
        ctx.user_data["talk_country"] = target_key
        await new_msg(q, ctx,
            f"💬 *مذاکره با {c['flag']} {c['name']}*\n\nپیامت رو بنویس:",
            InlineKeyboardMarkup([[InlineKeyboardButton("❌ انصراف", callback_data="dip")]])
        )
        return DIP_TALK_MSG

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
        await new_msg(q, ctx,
            f"📤 درخواست *{DIP_TYPES[kind]}* به {c['flag']} {c['name']} فرستاده شد.",
            back_kb()
        )
    except Exception as e:
        log.warning(f"خطا: {e}")
        await new_msg(q, ctx, "❌ خطا در ارسال.", back_kb())


async def cb_dip_accept(update, ctx):
    q = update.callback_query
    try:
        await q.answer()
    except:
        pass
    uid = q.from_user.id
    parts = q.data.split("_", 2)
    kind = parts[1]
    from_uid = int(parts[2])
    g_from = get_game(from_uid)
    g_me = get_game(uid)
    if not g_from or not g_me:
        await new_msg(q, ctx, "خطا.", back_kb())
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

    await new_msg(q, ctx, f"✅ درخواست *{DIP_TYPES[kind]}* رو قبول کردی.", back_kb())
    try:
        await ctx.bot.send_message(
            from_uid,
            f"✅ {COUNTRIES[my_country]['flag']} {COUNTRIES[my_country]['name']} "
            f"درخواست *{DIP_TYPES[kind]}* رو قبول کرد.",
            parse_mode="Markdown"
        )
    except:
        pass


async def cb_dip_reject(update, ctx):
    q = update.callback_query
    try:
        await q.answer()
    except:
        pass
    uid = q.from_user.id
    parts = q.data.split("_", 2)
    kind = parts[1]
    from_uid = int(parts[2])
    g_me = get_game(uid)
    await new_msg(q, ctx, f"❌ درخواست *{DIP_TYPES[kind]}* رو رد کردی.", back_kb())
    try:
        await ctx.bot.send_message(
            from_uid,
            f"❌ {COUNTRIES[g_me['country']]['flag']} {COUNTRIES[g_me['country']]['name']} "
            f"درخواست *{DIP_TYPES[kind]}* رو رد کرد.",
            parse_mode="Markdown"
        )
    except:
        pass


# ═══════════════════════════════════════════════════════════════
#  💬 مذاکره خصوصی
# ═══════════════════════════════════════════════════════════════
async def dip_talk_send(update, ctx):
    uid = update.effective_user.id
    target_uid = ctx.user_data.get("talk_target")
    target_country = ctx.user_data.get("talk_country")
    if not target_uid:
        await update.message.reply_text("انصراف.", reply_markup=main_menu_kb())
        return ConversationHandler.END

    g = get_game(uid)
    my_country = COUNTRIES[g["country"]]
    msg = update.message.text

    try:
        await ctx.bot.send_message(
            target_uid,
            f"💬 *پیام مذاکره*\n"
            f"از: {my_country['flag']} {my_country['name']}\n"
            f"━━━━━━━━━━━━━━━━━━━━━━\n{msg}",
            parse_mode="Markdown",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("↩️ پاسخ", callback_data=f"talkreply_{uid}")]
            ])
        )
    except:
        pass

    await update.message.reply_text("✅ پیام فرستاده شد.", reply_markup=main_menu_kb())
    return ConversationHandler.END


async def cb_talk_reply(update, ctx):
    q = update.callback_query
    try:
        await q.answer()
    except:
        pass
    target_uid = int(q.data.replace("talkreply_", ""))
    g_target = get_game(target_uid)
    if not g_target:
        await new_msg(q, ctx, "کاربر پیدا نشد.", back_kb())
        return
    ctx.user_data["talk_target"] = target_uid
    ctx.user_data["talk_country"] = g_target["country"]
    await new_msg(q, ctx,
        "↩️ پیامت رو بنویس:",
        InlineKeyboardMarkup([[InlineKeyboardButton("❌ انصراف", callback_data="menu")]])
    )
    return DIP_TALK_MSG


# ═══════════════════════════════════════════════════════════════
#  📦 تجارت
# ═══════════════════════════════════════════════════════════════
TRADE_PICK_TYPE, TRADE_PICK_AMOUNT, TRADE_PICK_WANT = range(50, 53)

RESOURCES = {
    "money":    "💰 پول",
    "food":     "🍞 غذا",
    "steel":    "⚙️ فولاد",
    "oil":      "🛢️ نفت",
    "coal":     "🪨 زغال",
    "manpower": "👥 نیرو",
}


async def cb_trade(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    try:
        await q.answer()
    except:
        pass
    g = get_game(q.from_user.id)
    text = (
        f"📦 *تجارت*\n"
        f"━━━━━━━━━━━━━━━━━━━━━━\n"
        f"💰 {fmt(g['money'])}  🍞 {fmt(g['food'])}  ⚙️ {fmt(g['steel'])}\n"
        f"🛢️ {fmt(g['oil'])}  🪨 {fmt(g['coal'])}  👥 {fmt(g['manpower'])}\n\n"
        f"می‌خوای چی صادر کنی؟"
    )
    rows = [[InlineKeyboardButton(label, callback_data=f"tp_{key}")]
            for key, label in RESOURCES.items()]
    rows.append([menu_btn()])
    await new_msg(q, ctx, text, InlineKeyboardMarkup(rows))
    return TRADE_PICK_TYPE


async def trade_pick_type(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    try:
        await q.answer()
    except:
        pass
    res = q.data.replace("tp_", "")
    ctx.user_data["trade_res"] = res
    g = get_game(q.from_user.id)
    text = (
        f"🔢 چند تا *{RESOURCES[res]}* بدی؟\n\n"
        f"تو {fmt(g[res])} تا داری.\nعدد بفرست:"
    )
    await new_msg(q, ctx, text, InlineKeyboardMarkup([[InlineKeyboardButton("❌ انصراف", callback_data="trade")]]))
    return TRADE_PICK_AMOUNT


async def trade_pick_amount(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
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
    kb = InlineKeyboardMarkup([
        [InlineKeyboardButton(label, callback_data=f"tw_{key}")]
        for key, label in RESOURCES.items()
    ] + [[InlineKeyboardButton("❌ انصراف", callback_data="trade")]])
    await update.message.reply_text(
        f"✅ {amount} {RESOURCES[res]} انتخاب شد.\n\nدر ازای چی می‌خوای؟",
        reply_markup=kb
    )
    return TRADE_PICK_WANT


async def trade_pick_want(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    try:
        await q.answer()
    except:
        pass
    want = q.data.replace("tw_", "")
    ctx.user_data["trade_want"] = want
    uid = q.from_user.id

    players = get_active_players(exclude_uid=uid)
    if not players:
        await new_msg(q, ctx, "📦 *هنوز بازیکن دیگه‌ای نیست.*", back_kb())
        return ConversationHandler.END

    rows = []
    for p in players:
        c = COUNTRIES[p["country"]]
        rows.append([InlineKeyboardButton(
            f"{c['flag']} {c['name']}",
            callback_data=f"tt_{p['country']}"
        )])
    rows.append([menu_btn()])

    await new_msg(q, ctx, "🎯 طرف مقابل رو انتخاب کن:", InlineKeyboardMarkup(rows))
    return ConversationHandler.END


async def cb_trade_send(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    try:
        await q.answer()
    except:
        pass
    target_key = q.data.replace("tt_", "")
    uid = q.from_user.id
    g = get_game(uid)
    res = ctx.user_data.get("trade_res")
    amount = ctx.user_data.get("trade_amount")
    want = ctx.user_data.get("trade_want")
    target_uid = find_player_by_country(target_key)

    if not target_uid or is_npc(target_uid):
        await new_msg(q, ctx, "❌ بازیکن پیدا نشد.", back_kb())
        return

    c = COUNTRIES[target_key]
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
        await new_msg(q, ctx,
            f"📤 پیشنهاد تجاری به {c['flag']} {c['name']} فرستاده شد.\n"
            f"منتظر پاسخ باش.",
            back_kb()
        )
    except Exception as e:
        log.warning(f"خطا: {e}")
        await new_msg(q, ctx, "❌ خطا.", back_kb())


async def cb_trade_accept(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    try:
        await q.answer()
    except:
        pass
    uid = q.from_user.id
    parts = q.data.split("_")
    from_uid = int(parts[1])
    res = parts[2]
    want = parts[3]
    amount = int(parts[4])

    g_from = get_game(from_uid)
    g_me = get_game(uid)
    if not g_from or not g_me:
        await new_msg(q, ctx, "خطا.", back_kb())
        return

    if g_from[res] < amount or g_me[want] < amount:
        await new_msg(q, ctx, "❌ یکی از طرفین منابع کافی نداره.", back_kb())
        return

    save_game(from_uid, **{res: g_from[res] - amount, want: g_from[want] + amount})
    save_game(uid, **{res: g_me[res] + amount, want: g_me[want] - amount})

    await new_msg(q, ctx, "✅ معامله انجام شد!", back_kb())
    try:
        await ctx.bot.send_message(from_uid, f"✅ معامله با {COUNTRIES[g_me['country']]['name']} انجام شد.")
    except:
        pass


async def cb_trade_reject(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    try:
        await q.answer()
    except:
        pass
    from_uid = int(q.data.replace("traderej_", ""))
    g_me = get_game(q.from_user.id)
    await new_msg(q, ctx, "❌ رد کردی.", back_kb())
    try:
        await ctx.bot.send_message(from_uid, f"❌ {COUNTRIES[g_me['country']]['name']} معامله رو رد کرد.")
    except:
        pass


# ═══════════════════════════════════════════════════════════════
#  ☢️ بمب اتم
# ═══════════════════════════════════════════════════════════════
async def cb_atom_use(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    try:
        await q.answer()
    except:
        pass
    uid = q.from_user.id
    g = get_game(uid)
    completed = json.loads(g["completed_projects"] or "[]")

    if "atomic_bomb" not in completed:
        try:
            await q.answer("❌ هنوز بمب اتم نساختی!", show_alert=True)
        except:
            pass
        return
    if g.get("atomic_ready") and g["atomic_ready"] >= 1:
        try:
            await q.answer("❌ بمب اتم قبلاً استفاده شده!", show_alert=True)
        except:
            pass
        return

    players = get_active_players(exclude_uid=uid)
    rows = []
    for p in players:
        c = COUNTRIES[p["country"]]
        rows.append([InlineKeyboardButton(
            f"☢️ {c['flag']} {c['name']}",
            callback_data=f"atom_{p['country']}"
        )])
    rows.append([menu_btn()])

    text = (
        "☢️ *استفاده از بمب اتم*\n\n"
        "⚠️ فقط یه بار! ۵۰٪ به هدف آسیب می‌زنه.\n"
        "⚠️ عوارض: ۳۰٪ رضایت کم، رقابت اتمی شروع میشه.\n\n"
        "کشور هدف رو انتخاب کن:"
    )
    await new_msg(q, ctx, text, InlineKeyboardMarkup(rows))


async def cb_atom_target(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    try:
        await q.answer()
    except:
        pass
    uid = q.from_user.id
    target = q.data.replace("atom_", "")
    g = get_game(uid)
    target_uid = find_player_by_country(target)

    if not target_uid:
        await new_msg(q, ctx, "❌ بازیکن پیدا نشد.", back_kb())
        return

    c = COUNTRIES[target]
    tg = get_game(target_uid)

    save_game(target_uid,
        money=int(tg["money"] * 0.5),
        food=int(tg["food"] * 0.5),
        steel=int(tg["steel"] * 0.5),
        oil=int(tg["oil"] * 0.5),
        coal=int(tg["coal"] * 0.5),
        manpower=int(tg["manpower"] * 0.5),
        soldiers=int(tg["soldiers"] * 0.5),
        happiness=max(0, tg["happiness"] - 30))

    save_game(uid,
        atomic_ready=1,
        happiness=max(0, g["happiness"] - 30))

    set_setting("atomic_used", "true")

    result = (
        f"☢️ *بمب اتم پرتاب شد!*\n\n"
        f"هدف: {c['flag']} {c['name']}\n"
        f"━━━━━━━━━━━━━━━━━━━━━━\n"
        f"📉 *آسیب به هدف:*\n"
        f"• ۵۰٪ پول و منابع\n"
        f"• ۵۰٪ ارتش\n"
        f"• ۳۰٪ رضایت\n\n"
        f"⚠️ *عوارض برای تو:*\n"
        f"• ۳۰٪ رضایت مردم کم شد\n"
        f"🌍 رقابت اتمی شروع شد — بقیه کشورها حالا می‌تونن بمب اتم بسازن."
    )

    await new_msg(q, ctx, result, back_kb())

    try:
        await ctx.bot.send_message(
            target_uid,
            f"☢️ *فاجعه!*\n\n"
            f"بمب اتم روی کشورت پرتاب شد!\n"
            f"۵۰٪ منابع و ارتشت از بین رفت.",
            parse_mode="Markdown"
        )
    except:
        pass
        # ═══════════════════════════════════════════════════════════════
#  👑 ادمین
# ═══════════════════════════════════════════════════════════════
async def cmd_admin(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    if uid not in ADMIN_IDS:
        await update.message.reply_text("🚫 دسترسی نداری.")
        return
    players = get_active_players()
    text = f"👑 *پنل ادمین*\n━━━━━━━━━━━━━━━━━━━━━━\n👥 بازیکنان: {len(players)}\n\n"
    for p in players[:20]:
        c = COUNTRIES.get(p["country"], {})
        text += f"{c.get('flag','❓')} [{p['user_id']}] {c.get('name','?')}\n"
    await update.message.reply_text(text, parse_mode="Markdown")


async def cmd_give(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
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


async def cmd_players(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    players = get_active_players()
    if not players:
        await update.message.reply_text("هنوز کسی بازی نکرده.")
        return
    text = "🌍 *بازیکنان فعال:*\n━━━━━━━━━━━━━━━━━━━━━━\n"
    for p in players:
        c = COUNTRIES.get(p["country"], {})
        text += f"{c.get('flag','❓')} {c.get('name','?')} — [{p['user_id']}]\n"
    await update.message.reply_text(text, parse_mode="Markdown")


async def cmd_country_info(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    if uid not in ADMIN_IDS:
        return

    text_in = update.message.text.strip()
    if not text_in.startswith("اطلاعات "):
        return

    country_name = text_in.replace("اطلاعات ", "").strip()
    target_key = None
    for k, v in COUNTRIES.items():
        if v["name"] == country_name:
            target_key = k
            break

    if not target_key:
        await update.message.reply_text("❌ کشور پیدا نشد.")
        return

    target_uid = find_player_by_country(target_key)
    if not target_uid:
        await update.message.reply_text(f"❌ کسی {country_name} رو نگرفته.")
        return

    tg = get_game(target_uid)
    c = COUNTRIES[target_key]
    unit_tanks = json.loads(tg.get("unit_tanks") or "{}")
    unit_planes = json.loads(tg.get("unit_planes") or "{}")
    unit_ships = json.loads(tg.get("unit_ships") or "{}")

    lines = [
        f"🔍 *اطلاعات {c['flag']} {c['name']}*",
        f"━━━━━━━━━━━━━━━━━━━━━━",
        f"👤 بازیکن: `{target_uid}`",
        f"📅 نوبت: {tg['turn']} | تاریخ: {format_game_date(parse_game_date(tg['game_date']))}",
        f"━━━━━━━━━━━━━━━━━━━━━━",
        f"💰 پول: {fmt(tg['money'])}",
        f"🍞 غذا: {fmt(tg['food'])}",
        f"⚙️ فولاد: {fmt(tg['steel'])}",
        f"🛢️ نفت: {fmt(tg['oil'])}",
        f"🪨 زغال: {fmt(tg['coal'])}",
        f"👥 نیرو: {fmt(tg['manpower'])}",
        f"━━━━━━━━━━━━━━━━━━━━━━",
        f"🪖 سرباز: {fmt(tg['soldiers'])}",
    ]
    for name, cnt in unit_tanks.items():
        lines.append(f"🛡️ {name}: {fmt(cnt)}")
    for name, cnt in unit_planes.items():
        lines.append(f"✈️ {name}: {fmt(cnt)}")
    for name, cnt in unit_ships.items():
        lines.append(f"🚢 {name}: {fmt(cnt)}")

    lines.append(f"━━━━━━━━━━━━━━━━━━━━━━")
    lines.append(f"😊 رضایت: {tg['happiness']}%  |  💵 مالیات: {tg['tax_rate']}%")

    allies = json.loads(tg["allies"] or "[]")
    wars = json.loads(tg["wars"] or "[]")
    allies_names = ", ".join(COUNTRIES[a]["name"] for a in allies if a in COUNTRIES) or "هیچ"
    wars_names = ", ".join(COUNTRIES[a]["name"] for a in wars if a in COUNTRIES) or "هیچ"
    lines.append(f"🤝 متحدین: {allies_names}")
    lines.append(f"⚔️ در جنگ با: {wars_names}")

    await update.message.reply_text("\n".join(lines), parse_mode="Markdown")


async def cmd_next_turn(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    if uid not in ADMIN_IDS:
        await update.message.reply_text("🚫 فقط ادمین‌ها.")
        return
    players = get_active_players()
    count = 0
    for p in players:
        process_turn(p["user_id"])
        count += 1
    await update.message.reply_text(f"⏭️ نوبت جدید برای {count} بازیکن اجرا شد.")


# ═══════════════════════════════════════════════════════════════
#  🕐 نوبت خودکار (هر ۱ ساعت)
# ═══════════════════════════════════════════════════════════════
async def auto_turn_job(context: ContextTypes.DEFAULT_TYPE):
    players = get_active_players()

    for p in players:
        result = process_turn(p["user_id"])
        if not result:
            continue

        text = (
            f"📅 *نوبت جدید!*\n"
            f"━━━━━━━━━━━━━━━━━━━━━━\n"
            f"🗓️ تاریخ: *{result['date_pretty']}*\n"
            f"🔢 نوبت: {p['turn'] + 1}\n"
        )

        if result["events"]:
            text += "\n📰 *رویدادهای تاریخی:*\n"
            for ev in result["events"]:
                text += f"• {ev}\n"

        if result["newly_done"]:
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

    # ─── اطلاعات [کشور] برای ادمین ────────────────
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
    print("📅 شروع: ۱ سپتامبر ۱۹۳۹")
    print("🏁 پایان: ۲ سپتامبر ۱۹۴۵")
    print("⏰ هر نوبت: ۳ روز بازی | هر ۱ ساعت واقعی")
    app.run_polling()


if __name__ == "__main__":
    main()
