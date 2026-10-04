#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
🎖️ ربات بازی جنگ جهانی دوم — نسخه نهایی (Reply Keyboard — بدون NPC)
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
#  🌍 کشورها (۱۲ کشور)
# ═══════════════════════════════════════════════════════════════
COUNTRIES = {
    "germany": {"flag": "🇩🇪", "name": "آلمان", "capital": "برلین",
        "money": 384, "food": 200, "steel": 23, "oil": 1, "coal": 24, "manpower": 80,
        "neighbors": ["france", "poland", "italy", "ussr"]},
    "uk": {"flag": "🇬🇧", "name": "انگلیس", "capital": "لندن",
        "money": 287, "food": 180, "steel": 13, "oil": 1, "coal": 14, "manpower": 50,
        "neighbors": []},
    "usa": {"flag": "🇺🇸", "name": "آمریکا", "capital": "واشینگتن",
        "money": 869, "food": 450, "steel": 51, "oil": 20, "coal": 21, "manpower": 130,
        "neighbors": []},
    "ussr": {"flag": "🇷🇺", "name": "شوروی", "capital": "مسکو",
        "money": 366, "food": 300, "steel": 19, "oil": 3, "coal": 6, "manpower": 170,
        "neighbors": ["germany", "poland", "china", "japan"]},
    "france": {"flag": "🇫🇷", "name": "فرانسه", "capital": "پاریس",
        "money": 199, "food": 150, "steel": 6, "oil": 0, "coal": 5, "manpower": 45,
        "neighbors": ["germany", "italy"]},
    "japan": {"flag": "🇯🇵", "name": "ژاپن", "capital": "توکیو",
        "money": 184, "food": 120, "steel": 6, "oil": 0, "coal": 2, "manpower": 70,
        "neighbors": ["china", "ussr"]},
    "italy": {"flag": "🇮🇹", "name": "ایتالیا", "capital": "رم",
        "money": 151, "food": 110, "steel": 2, "oil": 0, "coal": 0, "manpower": 40,
        "neighbors": ["germany", "france"]},
    "china": {"flag": "🇨🇳", "name": "چین", "capital": "چونگ‌کینگ",
        "money": 120, "food": 250, "steel": 1, "oil": 0, "coal": 3, "manpower": 200,
        "neighbors": ["ussr", "japan"]},
    "poland": {"flag": "🇵🇱", "name": "لهستان", "capital": "ورشو",
        "money": 80, "food": 100, "steel": 2, "oil": 0, "coal": 4, "manpower": 35,
        "neighbors": ["germany", "ussr"]},
    "canada": {"flag": "🇨🇦", "name": "کانادا", "capital": "اتاوا",
        "money": 110, "food": 180, "steel": 5, "oil": 2, "coal": 6, "manpower": 25,
        "neighbors": []},
    "australia": {"flag": "🇦🇺", "name": "استرالیا", "capital": "کانبرا",
        "money": 95, "food": 160, "steel": 3, "oil": 0, "coal": 4, "manpower": 20,
        "neighbors": []},
    "brazil": {"flag": "🇧🇷", "name": "برزیل", "capital": "ریو",
        "money": 75, "food": 200, "steel": 2, "oil": 0, "coal": 1, "manpower": 60,
        "neighbors": []},
}


# ═══════════════════════════════════════════════════════════════
#  🔬 درخت تحقیقات
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
    "1939-09-01": "🇩🇪 آلمان به لهستان حمله کرد",
    "1939-09-03": "🇬🇧🇫🇷 انگلیس و فرانسه اعلام جنگ کردن",
    "1939-11-30": "🇷🇺 شوروی به فنلاند حمله کرد",
    "1940-04-09": "🇩🇪 آلمان به دانمارک و نروژ حمله کرد",
    "1940-05-10": "🇩🇪 آلمان به فرانسه حمله کرد",
    "1940-06-22": "🇫🇷 فرانسه تسلیم شد",
    "1940-07-10": "✈️ نبرد بریتانیا شروع شد",
    "1941-06-22": "🇩🇪 عملیات بارباروسا",
    "1941-12-07": "🇯🇵 حمله به پرل هاربر",
    "1941-12-11": "🇺🇸 آمریکا وارد جنگ شد",
    "1942-06-04": "🌊 نبرد میدوی",
    "1942-08-23": "🔥 نبرد استالینگراد",
    "1943-02-02": "🏆 پیروزی شوروی در استالینگراد",
    "1944-06-06": "🚢 عملیات اورلرد — D-Day",
    "1945-02-04": "🤝 کنفرانس یالتا",
    "1945-04-30": "💀 خودکشی هیتلر",
    "1945-05-08": "🏁 تسلیم آلمان",
    "1945-08-06": "☢️ بمباران اتمی هیروشیما",
    "1945-08-09": "☢️ بمباران اتمی ناکازاکی",
    "1945-09-02": "🏁 تسلیم ژاپن",
}


# ═══════════════════════════════════════════════════════════════
#  🚚 تدارکات
# ═══════════════════════════════════════════════════════════════
SUPPLY = {
    "soldier": {"money": 1, "food": 2, "oil": 0},
    "tank":    {"money": 5, "food": 10, "oil": 5},
    "plane":   {"money": 3, "food": 5, "oil": 10},
    "ship":    {"money": 10, "food": 30, "oil": 20},
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
    c.execute("INSERT OR IGNORE INTO settings (key, value) VALUES ('atomic_used', 'false')")
    conn.commit()
    conn.close()


def db():
    conn = sqlite3.connect(DB_FILE)
    conn.row_factory = sqlite3.Row
    return conn


def get_setting(key, default="false"):
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


def find_player_by_country(country_key):
    """فقط بازیکن‌های واقعی (user_id > 0)"""
    conn = db()
    row = conn.execute(
        "SELECT user_id FROM games WHERE country=? AND user_id > 0",
        (country_key,)
    ).fetchone()
    conn.close()
    return row["user_id"] if row else None


def get_active_players(exclude_uid=None):
    """فقط بازیکن‌های واقعی"""
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


def get_taken_countries():
    """کشورهایی که بازیکن واقعی دارن"""
    conn = db()
    rows = conn.execute("SELECT country FROM games WHERE user_id > 0").fetchall()
    conn.close()
    return {r["country"] for r in rows}


# ═══════════════════════════════════════════════════════════════
#  📅 تاریخ
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
#  🗺️ همسایگی
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
#  ⚔️ نظامی
# ═══════════════════════════════════════════════════════════════
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
            result.append({"name": name, "money": money, "steel": steel, "oil": oil, "attack": power, "unlocked": True})
        else:
            result.append({"name": name, "money": cost, "unlocked": False})
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
#  🕹️ شروع بازی
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

    war_mult = 1.0 if not g["war_active"] else 0.8
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
#  🎨 کیبوردهای Reply (زیر چت)
# ═══════════════════════════════════════════════════════════════
def main_menu_reply():
    return ReplyKeyboardMarkup([
        [KeyboardButton("💰 اقتصاد"), KeyboardButton("⚔️ ارتش")],
        [KeyboardButton("🔬 تحقیقات"), KeyboardButton("🏗️ پروژه‌ها")],
        [KeyboardButton("🤝 دیپلماسی"), KeyboardButton("📦 تجارت")],
        [KeyboardButton("🎯 حمله"), KeyboardButton("🕵️ جاسوسی")],
        [KeyboardButton("💵 مالیات"), KeyboardButton("🏛️ امور کشور")],
        [KeyboardButton("📊 آمار کامل")],
    ], resize_keyboard=True)


def country_reply():
    """کیبورد انتخاب کشور — فقط کشورهای بدون بازیکن"""
    taken = get_taken_countries()
    rows = []
    row = []
    for key, c in COUNTRIES.items():
        if key in taken:
            continue
        row.append(KeyboardButton(f"{c['flag']} {c['name']}"))
        if len(row) == 2:
            rows.append(row)
            row = []
    if row:
        rows.append(row)
    return ReplyKeyboardMarkup(rows, resize_keyboard=True, one_time_keyboard=True)


def back_menu_reply():
    return ReplyKeyboardMarkup([
        [KeyboardButton("🔙 منو")]
    ], resize_keyboard=True)


def eco_reply():
    return ReplyKeyboardMarkup([
        [KeyboardButton("💵 تغییر مالیات")],
        [KeyboardButton("🏗️ ساخت پروژه")],
        [KeyboardButton("🔙 منو")],
    ], resize_keyboard=True)


def army_reply():
    return ReplyKeyboardMarkup([
        [KeyboardButton("🪖 خرید سرباز"), KeyboardButton("🛡️ خرید تانک")],
        [KeyboardButton("✈️ خرید هواپیما"), KeyboardButton("🚢 خرید کشتی")],
        [KeyboardButton("🔙 منو")],
    ], resize_keyboard=True)


def research_reply(g):
    rows = []
    tree = RESEARCH.get(g["country"], [])
    row = []
    for name, cost, days, power in tree:
        row.append(KeyboardButton(name))
        if len(row) == 2:
            rows.append(row)
            row = []
    if row:
        rows.append(row)
    rows.append([KeyboardButton("🔙 منو")])
    return ReplyKeyboardMarkup(rows, resize_keyboard=True)


def projects_reply(g):
    completed = json.loads(g["completed_projects"] or "[]")
    building = json.loads(g["projects"] or "[]")
    rows = []
    row = []
    for key, p in PROJECTS.items():
        if key in completed:
            continue
        b = any(x.split(":")[0] == key for x in building)
        if b:
            continue
        row.append(KeyboardButton(p["name"]))
        if len(row) == 2:
            rows.append(row)
            row = []
    if row:
        rows.append(row)
    rows.append([KeyboardButton("🔙 منو")])
    return ReplyKeyboardMarkup(rows, resize_keyboard=True)


def buy_tank_reply(g):
    units = get_available_units(g, "tank")
    rows = []
    row = []
    for u in units:
        if u["unlocked"]:
            row.append(KeyboardButton(u["name"]))
            if len(row) == 2:
                rows.append(row)
                row = []
    if row:
        rows.append(row)
    rows.append([KeyboardButton("🔙 منو")])
    return ReplyKeyboardMarkup(rows, resize_keyboard=True)


def buy_plane_reply(g):
    units = get_available_units(g, "plane")
    rows = []
    row = []
    for u in units:
        if u["unlocked"]:
            row.append(KeyboardButton(u["name"]))
            if len(row) == 2:
                rows.append(row)
                row = []
    if row:
        rows.append(row)
    rows.append([KeyboardButton("🔙 منو")])
    return ReplyKeyboardMarkup(rows, resize_keyboard=True)


def buy_ship_reply(g):
    units = get_available_units(g, "ship")
    rows = []
    row = []
    for u in units:
        if u["unlocked"]:
            row.append(KeyboardButton(u["name"]))
            if len(row) == 2:
                rows.append(row)
                row = []
    if row:
        rows.append(row)
    rows.append([KeyboardButton("🔙 منو")])
    return ReplyKeyboardMarkup(rows, resize_keyboard=True)


def internal_reply():
    return ReplyKeyboardMarkup([
        [KeyboardButton("📢 سخنرانی")],
        [KeyboardButton("🚔 سرکوب")],
        [KeyboardButton("🔙 منو")],
    ], resize_keyboard=True)


def dip_reply():
    return ReplyKeyboardMarkup([
        [KeyboardButton("🤝 پیشنهاد اتحاد")],
        [KeyboardButton("☮️ پیشنهاد صلح")],
        [KeyboardButton("⚔️ اعلام جنگ")],
        [KeyboardButton("💬 مذاکره خصوصی")],
        [KeyboardButton("🔙 منو")],
    ], resize_keyboard=True)


def trade_reply():
    return ReplyKeyboardMarkup([
        [KeyboardButton("💰 پول"), KeyboardButton("🍞 غذا")],
        [KeyboardButton("⚙️ فولاد"), KeyboardButton("🛢️ نفت")],
        [KeyboardButton("🪨 زغال"), KeyboardButton("👥 نیرو")],
        [KeyboardButton("🔙 منو")],
    ], resize_keyboard=True)


def attack_target_reply(exclude_uid=None):
    """فقط بازیکن‌های واقعی (به جز خودم)"""
    players = get_active_players(exclude_uid=exclude_uid)
    rows = []
    row = []
    for p in players:
        c = COUNTRIES[p["country"]]
        row.append(KeyboardButton(f"{c['flag']} {c['name']}"))
        if len(row) == 2:
            rows.append(row)
            row = []
    if row:
        rows.append(row)
    rows.append([KeyboardButton("🔙 منو")])
    return ReplyKeyboardMarkup(rows, resize_keyboard=True)


# ═══════════════════════════════════════════════════════════════
#  📊 داشبورد و آمار کامل
# ═══════════════════════════════════════════════════════════════
def render_dashboard(g):
    c = COUNTRIES[g["country"]]
    dt = parse_game_date(g["game_date"])
    date_str = format_game_date(dt)

    text = (
        f"{c['flag']} *{c['name']}* — {date_str} (نوبت {g['turn']})\n"
        f"━━━━━━━━━━━━━━━━━━━━━━\n"
    )

    events = get_events_between(g["game_date"], g["game_date"])
    if events:
        text += f"📰 {events[0]}\n\n"

    text += (
        f"💰 پول: {fmt(g['money'])}   😊 رضایت: {g['happiness']}%\n"
        f"🪖 سرباز: {fmt(g['soldiers'])}   💵 مالیات: {g['tax_rate']}%\n\n"
        f"از دکمه‌های پایین انتخاب کن 👇"
    )
    return text


def render_stats(g):
    c = COUNTRIES[g["country"]]
    dt = parse_game_date(g["game_date"])
    date_str = format_game_date(dt)

    unit_tanks = json.loads(g.get("unit_tanks") or "{}")
    unit_planes = json.loads(g.get("unit_planes") or "{}")
    unit_ships = json.loads(g.get("unit_ships") or "{}")
    building = json.loads(g["projects"] or "[]")
    wars = json.loads(g["wars"] or "[]")
    allies = json.loads(g["allies"] or "[]")
    colonies = json.loads(g["colonies"] or "[]")

    lines = [
        f"{c['flag']} *{c['name']}* — {date_str}",
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
    for name, cnt in unit_tanks.items():
        lines.append(f"🛡️ {name}: {fmt(cnt)}")
    for name, cnt in unit_planes.items():
        lines.append(f"✈️ {name}: {fmt(cnt)}")
    for name, cnt in unit_ships.items():
        lines.append(f"🚢 {name}: {fmt(cnt)}")

    lines.append(f"━━━━━━━━━━━━━━━━━━━━━━")
    lines.append(f"😊 رضایت: {g['happiness']}%  |  💵 مالیات: {g['tax_rate']}%")

    if building:
        b_names = []
        for p in building:
            if ":" in p:
                key, days = p.split(":")
                pinfo = PROJECTS.get(key)
                if pinfo:
                    b_names.append(f"{pinfo['name']} ({days} نوبت)")
        if b_names:
            lines.append(f"🔨 در حال ساخت: {', '.join(b_names)}")

    if g["war_active"]:
        lines.append("⚔️ *در حال جنگ*")

    if wars:
        wars_names = ", ".join(COUNTRIES[a]["name"] for a in wars if a in COUNTRIES)
        lines.append(f"⚔️ در جنگ با: {wars_names}")

    if allies:
        allies_names = ", ".join(COUNTRIES[a]["name"] for a in allies if a in COUNTRIES)
        lines.append(f"🤝 متحدین: {allies_names}")

    if colonies:
        col_names = ", ".join(COUNTRIES[a]["name"] for a in colonies if a in COUNTRIES)
        lines.append(f"🏝️ مستعمرات: {col_names}")

    return "\n".join(lines)


# ═══════════════════════════════════════════════════════════════
#  📝 هندلرهای start/menu/join
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
            reply_markup=main_menu_reply()
        )
        return

    await update.message.reply_text(
        "🎖️ به بازی *جنگ جهانی دوم* خوش آمدی!\n\n"
        "یکی از کشورها رو انتخاب کن و از ۱ سپتامبر ۱۹۳۹ شروع کن.\n\n"
        "📅 هر ۱ ساعت = ۱ نوبت خودکار\n"
        "📅 هر نوبت = ۳ روز بازی جلو میره\n"
        "🏁 کل بازی = ۳۰ روز واقعی\n\n"
        "از دکمه‌های پایین انتخاب کن 👇",
        reply_markup=ReplyKeyboardMarkup([
            [KeyboardButton("🎮 بازی جدید")],
            [KeyboardButton("📖 راهنما")],
        ], resize_keyboard=True, one_time_keyboard=True),
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
        reply_markup=main_menu_reply(),
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
        reply_markup=main_menu_reply()
    )
    uid = update.effective_user.id
    g = get_game(uid)
    if g:
        await update.message.reply_text(render_dashboard(g), reply_markup=main_menu_reply(), parse_mode="Markdown")
    else:
        await update.message.reply_text(
            "برای شروع، یکی رو انتخاب کن:",
            reply_markup=ReplyKeyboardMarkup([
                [KeyboardButton("🎮 بازی جدید")],
                [KeyboardButton("📖 راهنما")],
            ], resize_keyboard=True)
        )
        # ═══════════════════════════════════════════════════════════════
#  🎮 هندلر: بازی جدید
# ═══════════════════════════════════════════════════════════════
async def on_newgame(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    not_joined = await check_all_memberships(update, ctx)
    if not_joined:
        await send_join_message(update, ctx)
        return
    taken = get_taken_countries()
    if len(taken) >= len(COUNTRIES):
        await update.message.reply_text("❌ همه کشورها انتخاب شدن.")
        return
    await update.message.reply_text(
        "🌍 *کشورت رو انتخاب کن:*\n\nاز دکمه‌های پایین انتخاب کن 👇",
        reply_markup=country_reply(),
        parse_mode="Markdown"
    )


COUNTRY_MAP = {
    "🇩🇪 آلمان": "germany",
    "🇬🇧 انگلیس": "uk",
    "🇺🇸 آمریکا": "usa",
    "🇷🇺 شوروی": "ussr",
    "🇫🇷 فرانسه": "france",
    "🇯🇵 ژاپن": "japan",
    "🇮🇹 ایتالیا": "italy",
    "🇨🇳 چین": "china",
    "🇵🇱 لهستان": "poland",
    "🇨🇦 کانادا": "canada",
    "🇦🇺 استرالیا": "australia",
    "🇧🇷 برزیل": "brazil",
}


async def on_country_pick(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.strip()
    if text not in COUNTRY_MAP:
        return
    uid = update.effective_user.id
    key = COUNTRY_MAP[text]
    c = COUNTRIES[key]

    existing = find_player_by_country(key)
    if existing and existing != uid:
        await update.message.reply_text(
            f"❌ {c['name']} قبلاً انتخاب شده!",
            reply_markup=country_reply()
        )
        return

    start_new_game(uid, key)
    g = get_game(uid)

    await update.message.reply_text(
        f"✅ کشور انتخاب شد: {c['flag']} *{c['name']}*\n\n"
        f"{render_dashboard(g)}",
        reply_markup=main_menu_reply(),
        parse_mode="Markdown"
    )


# ═══════════════════════════════════════════════════════════════
#  📊 هندلر: آمار کامل
# ═══════════════════════════════════════════════════════════════
async def on_stats(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    g = get_game(uid)
    if not g:
        await update.message.reply_text("اول بازی جدید بساز: /start")
        return
    check_and_run_turn(uid)
    g = get_game(uid)
    await update.message.reply_text(
        render_stats(g),
        reply_markup=back_menu_reply(),
        parse_mode="Markdown"
    )


# ═══════════════════════════════════════════════════════════════
#  📖 هندلر: راهنما
# ═══════════════════════════════════════════════════════════════
async def on_help(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
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
        "از دکمه‌های پایین انتخاب کن 👇",
        reply_markup=ReplyKeyboardMarkup([
            [KeyboardButton("🎮 بازی جدید")],
            [KeyboardButton("🔙 منو")],
        ], resize_keyboard=True),
        parse_mode="Markdown"
    )


# ═══════════════════════════════════════════════════════════════
#  💰 اقتصاد
# ═══════════════════════════════════════════════════════════════
async def on_eco(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    g = get_game(uid)
    if not g:
        return
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
        f"💵 مالیات: {g['tax_rate']}%  |  😊 رضایت: {g['happiness']}%\n\n"
        f"از دکمه‌های پایین انتخاب کن 👇"
    )
    await update.message.reply_text(text, reply_markup=eco_reply(), parse_mode="Markdown")


# ═══════════════════════════════════════════════════════════════
#  💵 مالیات
# ═══════════════════════════════════════════════════════════════
async def on_tax(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    g = get_game(uid)
    if not g:
        return
    ctx.user_data["waiting_tax"] = True
    await update.message.reply_text(
        f"💵 *مالیات*\n"
        f"━━━━━━━━━━━━━━━━━━━━━━\n"
        f"الان: {g['tax_rate']}%\n"
        f"رضایت: {g['happiness']}%\n\n"
        f"عددی بین ۰ تا ۵۰ تایپ کن و بفرست.",
        reply_markup=back_menu_reply(),
        parse_mode="Markdown"
    )


async def on_tax_input(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    if not ctx.user_data.get("waiting_tax"):
        return False
    text = update.message.text.strip()
    try:
        rate = int(text)
        if not (0 <= rate <= 50):
            raise ValueError
    except:
        return False

    uid = update.effective_user.id
    g = get_game(uid)
    if not g:
        return False
    save_game(uid, tax_rate=rate)
    ctx.user_data["waiting_tax"] = False
    g = get_game(uid)
    await update.message.reply_text(
        f"✅ مالیات شد {rate}%\n\n{render_dashboard(g)}",
        reply_markup=main_menu_reply(),
        parse_mode="Markdown"
    )
    return True


# ═══════════════════════════════════════════════════════════════
#  🏛️ امور کشور
# ═══════════════════════════════════════════════════════════════
async def on_internal(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    g = get_game(uid)
    if not g:
        return
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

    text += "\n\nاز دکمه‌های پایین انتخاب کن 👇"
    await update.message.reply_text(text, reply_markup=internal_reply(), parse_mode="Markdown")


async def on_speech(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    g = get_game(uid)
    if not g:
        return
    if (g.get("speech_turns_left") or 0) > 0:
        await update.message.reply_text("❌ یه سخنرانی فعال داری.")
        return
    if g["money"] < 100:
        await update.message.reply_text("❌ ۱۰۰ پول لازمه.")
        return
    save_game(uid, money=g["money"] - 100, speech_turns_left=5)
    await update.message.reply_text(
        "📢 سخنرانی رهبر شروع شد!\nاثرش در ۵ نوبت آینده ظاهر میشه (+۲ رضایت هر نوبت).",
        reply_markup=main_menu_reply(),
        parse_mode="Markdown"
    )


async def on_suppress(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    g = get_game(uid)
    if not g:
        return
    if (g.get("suppress_cooldown") or 0) > 0:
        await update.message.reply_text("❌ سرکوب قبلی هنوز اثر داره.")
        return
    if g["money"] < 50:
        await update.message.reply_text("❌ ۵۰ پول لازمه.")
        return
    save_game(uid,
        money=g["money"] - 50,
        happiness=min(100, g["happiness"] + 10),
        suppress_cooldown=3,
        suppress_count=(g.get("suppress_count") or 0) + 1)
    await update.message.reply_text(
        "🚔 سرکوب شد!\n+۱۰ رضایت فوری (ولی بعد ۳ نوبت -۵ رضایت پایه)",
        reply_markup=main_menu_reply(),
        parse_mode="Markdown"
    )


# ═══════════════════════════════════════════════════════════════
#  ⚔️ ارتش
# ═══════════════════════════════════════════════════════════════
async def on_army(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    g = get_game(uid)
    if not g:
        return
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
    lines.append("\nاز دکمه‌های پایین انتخاب کن 👇")

    await update.message.reply_text("\n".join(lines), reply_markup=army_reply(), parse_mode="Markdown")


# ═══════════════════════════════════════════════════════════════
#  🪖 خرید سرباز
# ═══════════════════════════════════════════════════════════════
async def on_buy_soldier(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    ctx.user_data["waiting_soldier"] = True
    await update.message.reply_text(
        "🪖 *خرید سرباز*\n"
        "━━━━━━━━━━━━━━━━━━━━━━\n"
        "قیمت هر سرباز: ۱۰💰 + ۱👥\n\n"
        "عدد رو تایپ کن و بفرست:",
        reply_markup=back_menu_reply(),
        parse_mode="Markdown"
    )


async def on_soldier_input(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    if not ctx.user_data.get("waiting_soldier"):
        return False
    try:
        qty = int(update.message.text.strip())
        if qty <= 0:
            raise ValueError
    except:
        return False
    uid = update.effective_user.id
    g = get_game(uid)
    need_money = 10 * qty
    need_man = 1 * qty
    if g["money"] < need_money or g["manpower"] < need_man:
        await update.message.reply_text(f"❌ منابع کافی نداری! نیاز: {need_money}💰 + {need_man}👥")
        ctx.user_data["waiting_soldier"] = False
        return True
    save_game(uid, money=g["money"]-need_money, manpower=g["manpower"]-need_man, soldiers=g["soldiers"]+qty)
    ctx.user_data["waiting_soldier"] = False
    await update.message.reply_text(
        f"✅ *{qty} سرباز* ساخته شد!",
        reply_markup=main_menu_reply(),
        parse_mode="Markdown"
    )
    return True


# ═══════════════════════════════════════════════════════════════
#  🛡️ خرید تانک
# ═══════════════════════════════════════════════════════════════
async def on_buy_tank(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    g = get_game(uid)
    units = get_available_units(g, "tank")
    lines = [f"🛡️ *خرید تانک — {COUNTRIES[g['country']]['name']}*", "━━━━━━━━━━━━━━━━━━━━━━"]
    for u in units:
        if u["unlocked"]:
            lines.append(f"✅ {u['name']} — {u['money']}💰 (قدرت {u['attack']})")
        else:
            lines.append(f"🔒 {u['name']} (تحقیق کن)")
    lines.append("\nاز دکمه‌های پایین انتخاب کن 👇")
    await update.message.reply_text("\n".join(lines), reply_markup=buy_tank_reply(g), parse_mode="Markdown")


async def on_tank_pick(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.strip()
    uid = update.effective_user.id
    g = get_game(uid)
    if not g:
        return
    unlocked = json.loads(g["research"] or "[]")
    if text not in unlocked:
        return
    ctx.user_data["buy_tank_name"] = text
    ctx.user_data["waiting_tank_qty"] = True
    tree = {n: (c, d, p) for n, c, d, p in RESEARCH.get(g["country"], [])}
    power = tree.get(text, (0, 0, 10))[2]
    money = int(power * 2 + 5)
    steel = max(1, power // 5)
    oil = max(0, power // 8)
    await update.message.reply_text(
        f"🛡️ *خرید {text}*\n"
        f"قیمت: {money}💰 + {steel}⚙️ + {oil}🛢️\n\nعدد رو تایپ کن:",
        reply_markup=back_menu_reply(),
        parse_mode="Markdown"
    )


async def on_tank_qty_input(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    if not ctx.user_data.get("waiting_tank_qty"):
        return False
    try:
        qty = int(update.message.text.strip())
        if qty <= 0:
            raise ValueError
    except:
        return False
    uid = update.effective_user.id
    g = get_game(uid)
    name = ctx.user_data.get("buy_tank_name")
    if not name:
        return False
    tree = {n: (c, d, p) for n, c, d, p in RESEARCH.get(g["country"], [])}
    power = tree.get(name, (0, 0, 10))[2]
    money = int(power * 2 + 5) * qty
    steel = max(1, power // 5) * qty
    oil = max(0, power // 8) * qty
    if g["money"] < money or g["steel"] < steel or g["oil"] < oil:
        await update.message.reply_text(f"❌ منابع کافی نداری! نیاز: {money}💰 + {steel}⚙️ + {oil}🛢️")
        ctx.user_data["waiting_tank_qty"] = False
        return True
    unit_tanks = json.loads(g.get("unit_tanks") or "{}")
    unit_tanks[name] = unit_tanks.get(name, 0) + qty
    save_game(uid, money=g["money"]-money, steel=g["steel"]-steel, oil=g["oil"]-oil, unit_tanks=json.dumps(unit_tanks))
    ctx.user_data["waiting_tank_qty"] = False
    await update.message.reply_text(f"✅ *{qty} {name}* ساخته شد!", reply_markup=main_menu_reply(), parse_mode="Markdown")
    return True


# ═══════════════════════════════════════════════════════════════
#  ✈️ خرید هواپیما
# ═══════════════════════════════════════════════════════════════
async def on_buy_plane(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    g = get_game(uid)
    units = get_available_units(g, "plane")
    lines = [f"✈️ *خرید هواپیما — {COUNTRIES[g['country']]['name']}*", "━━━━━━━━━━━━━━━━━━━━━━"]
    for u in units:
        if u["unlocked"]:
            lines.append(f"✅ {u['name']} — {u['money']}💰 (قدرت {u['attack']})")
        else:
            lines.append(f"🔒 {u['name']} (تحقیق کن)")
    lines.append("\nاز دکمه‌های پایین انتخاب کن 👇")
    await update.message.reply_text("\n".join(lines), reply_markup=buy_plane_reply(g), parse_mode="Markdown")


async def on_plane_pick(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.strip()
    uid = update.effective_user.id
    g = get_game(uid)
    if not g:
        return
    unlocked = json.loads(g["research"] or "[]")
    if text not in unlocked:
        return
    ctx.user_data["buy_plane_name"] = text
    ctx.user_data["waiting_plane_qty"] = True
    tree = {n: (c, d, p) for n, c, d, p in RESEARCH.get(g["country"], [])}
    power = tree.get(text, (0, 0, 10))[2]
    money = int(power * 2 + 5)
    steel = max(1, power // 6)
    oil = max(1, power // 4)
    await update.message.reply_text(
        f"✈️ *خرید {text}*\nقیمت: {money}💰 + {steel}⚙️ + {oil}🛢️\n\nعدد رو تایپ کن:",
        reply_markup=back_menu_reply(),
        parse_mode="Markdown"
    )


async def on_plane_qty_input(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    if not ctx.user_data.get("waiting_plane_qty"):
        return False
    try:
        qty = int(update.message.text.strip())
        if qty <= 0:
            raise ValueError
    except:
        return False
    uid = update.effective_user.id
    g = get_game(uid)
    name = ctx.user_data.get("buy_plane_name")
    if not name:
        return False
    tree = {n: (c, d, p) for n, c, d, p in RESEARCH.get(g["country"], [])}
    power = tree.get(name, (0, 0, 10))[2]
    money = int(power * 2 + 5) * qty
    steel = max(1, power // 6) * qty
    oil = max(1, power // 4) * qty
    if g["money"] < money or g["steel"] < steel or g["oil"] < oil:
        await update.message.reply_text(f"❌ منابع کافی نداری!")
        ctx.user_data["waiting_plane_qty"] = False
        return True
    unit_planes = json.loads(g.get("unit_planes") or "{}")
    unit_planes[name] = unit_planes.get(name, 0) + qty
    save_game(uid, money=g["money"]-money, steel=g["steel"]-steel, oil=g["oil"]-oil, unit_planes=json.dumps(unit_planes))
    ctx.user_data["waiting_plane_qty"] = False
    await update.message.reply_text(f"✅ *{qty} {name}* ساخته شد!", reply_markup=main_menu_reply(), parse_mode="Markdown")
    return True


# ═══════════════════════════════════════════════════════════════
#  🚢 خرید کشتی
# ═══════════════════════════════════════════════════════════════
async def on_buy_ship(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    g = get_game(uid)
    units = get_available_units(g, "ship")
    lines = [f"🚢 *خرید کشتی — {COUNTRIES[g['country']]['name']}*", "━━━━━━━━━━━━━━━━━━━━━━"]
    for u in units:
        if u["unlocked"]:
            lines.append(f"✅ {u['name']} — {u['money']}💰 (قدرت {u['attack']})")
        else:
            lines.append(f"🔒 {u['name']} (تحقیق کن)")
    lines.append("\nاز دکمه‌های پایین انتخاب کن 👇")
    await update.message.reply_text("\n".join(lines), reply_markup=buy_ship_reply(g), parse_mode="Markdown")


async def on_ship_pick(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.strip()
    uid = update.effective_user.id
    g = get_game(uid)
    if not g:
        return
    unlocked = json.loads(g["research"] or "[]")
    if text not in unlocked:
        return
    ctx.user_data["buy_ship_name"] = text
    ctx.user_data["waiting_ship_qty"] = True
    tree = {n: (c, d, p) for n, c, d, p in RESEARCH.get(g["country"], [])}
    power = tree.get(text, (0, 0, 15))[2]
    money = int(power * 3 + 20)
    steel = max(2, power // 3)
    oil = max(1, power // 5)
    await update.message.reply_text(
        f"🚢 *خرید {text}*\nقیمت: {money}💰 + {steel}⚙️ + {oil}🛢️\n\nعدد رو تایپ کن:",
        reply_markup=back_menu_reply(),
        parse_mode="Markdown"
    )


async def on_ship_qty_input(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    if not ctx.user_data.get("waiting_ship_qty"):
        return False
    try:
        qty = int(update.message.text.strip())
        if qty <= 0:
            raise ValueError
    except:
        return False
    uid = update.effective_user.id
    g = get_game(uid)
    name = ctx.user_data.get("buy_ship_name")
    if not name:
        return False
    tree = {n: (c, d, p) for n, c, d, p in RESEARCH.get(g["country"], [])}
    power = tree.get(name, (0, 0, 15))[2]
    money = int(power * 3 + 20) * qty
    steel = max(2, power // 3) * qty
    oil = max(1, power // 5) * qty
    if g["money"] < money or g["steel"] < steel or g["oil"] < oil:
        await update.message.reply_text(f"❌ منابع کافی نداری!")
        ctx.user_data["waiting_ship_qty"] = False
        return True
    unit_ships = json.loads(g.get("unit_ships") or "{}")
    unit_ships[name] = unit_ships.get(name, 0) + qty
    save_game(uid, money=g["money"]-money, steel=g["steel"]-steel, oil=g["oil"]-oil, unit_ships=json.dumps(unit_ships))
    ctx.user_data["waiting_ship_qty"] = False
    await update.message.reply_text(f"✅ *{qty} {name}* ساخته شد!", reply_markup=main_menu_reply(), parse_mode="Markdown")
    return True


# ═══════════════════════════════════════════════════════════════
#  🔬 تحقیقات
# ═══════════════════════════════════════════════════════════════
async def on_research(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    g = get_game(uid)
    if not g:
        return
    tree = RESEARCH.get(g["country"], [])
    unlocked = json.loads(g["research"] or "[]")
    lines = [f"🔬 *درخت تحقیقات — {COUNTRIES[g['country']]['name']}*", "━━━━━━━━━━━━━━━━━━━━━━"]
    for name, cost, days, power in tree:
        if name in unlocked:
            lines.append(f"✅ {name} (قدرت {power})")
        else:
            lines.append(f"🔒 {name} — {cost}💰")
    lines.append("\nاز دکمه‌های پایین انتخاب کن 👇")
    await update.message.reply_text("\n".join(lines), reply_markup=research_reply(g), parse_mode="Markdown")


async def on_research_pick(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    name = update.message.text.strip()
    uid = update.effective_user.id
    g = get_game(uid)
    if not g:
        return
    tree = RESEARCH.get(g["country"], [])
    for n, cost, days, power in tree:
        if n == name:
            if g["money"] < cost:
                await update.message.reply_text(f"❌ پول کافی نداری. نیاز: {cost}💰")
                return
            unlocked = json.loads(g["research"] or "[]")
            if name in unlocked:
                await update.message.reply_text("قبلاً تحقیق شده.")
                return
            unlocked.append(name)
            save_game(uid, money=g["money"] - cost, research=json.dumps(unlocked))
            g = get_game(uid)
            await update.message.reply_text(
                f"✅ {name} تحقیق شد!\n\n{render_dashboard(g)}",
                reply_markup=main_menu_reply(),
                parse_mode="Markdown"
            )
            return


# ═══════════════════════════════════════════════════════════════
#  🏗️ پروژه‌ها
# ═══════════════════════════════════════════════════════════════
async def on_projects(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    g = get_game(uid)
    if not g:
        return
    completed = json.loads(g["completed_projects"] or "[]")
    building = json.loads(g["projects"] or "[]")
    lines = ["🏗️ *پروژه‌های ملی*", "━━━━━━━━━━━━━━━━━━━━━━"]
    for key, p in PROJECTS.items():
        if key in completed:
            lines.append(f"✅ {p['name']} (تکمیل)")
        else:
            b = any(x.split(":")[0] == key for x in building)
            if b:
                days_left = 0
                for x in building:
                    if x.startswith(key + ":"):
                        days_left = int(x.split(":")[1])
                lines.append(f"🔨 {p['name']} (در حال ساخت - {days_left} نوبت)")
            else:
                lines.append(f"🆕 {p['name']} — {p['money']}💰 + {p['steel']}⚙️")
    lines.append("\nاز دکمه‌های پایین انتخاب کن 👇")
    await update.message.reply_text("\n".join(lines), reply_markup=projects_reply(g), parse_mode="Markdown")


async def on_project_pick(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    name = update.message.text.strip()
    uid = update.effective_user.id
    g = get_game(uid)
    if not g:
        return
    for key, p in PROJECTS.items():
        if p["name"] == name:
            if g["money"] < p["money"] or g["steel"] < p["steel"]:
                await update.message.reply_text(f"❌ نیاز: {p['money']}💰 + {p['steel']}⚙️")
                return
            projects = json.loads(g["projects"] or "[]")
            if any(x.split(":")[0] == key for x in projects):
                await update.message.reply_text("در حال ساخت است.")
                return
            projects.append(f"{key}:{p['days']}")
            save_game(uid, money=g["money"]-p["money"], steel=g["steel"]-p["steel"], projects=json.dumps(projects))
            g = get_game(uid)
            await update.message.reply_text(
                f"✅ {p['name']} شروع شد ({p['days']} نوبت)\n\n{render_dashboard(g)}",
                reply_markup=main_menu_reply(),
                parse_mode="Markdown"
            )
            return
            # ═══════════════════════════════════════════════════════════════
#  🎯 حمله
# ═══════════════════════════════════════════════════════════════
async def on_attack(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    g = get_game(uid)
    if not g:
        return
    players = get_active_players(exclude_uid=uid)
    if not players:
        await update.message.reply_text("⚔️ هنوز بازیکن دیگه‌ای نیست.", reply_markup=back_menu_reply())
        return
    ctx.user_data["attack_force"] = {"soldiers": 0, "tanks": 0, "planes": 0, "ships": 0}
    ctx.user_data["attack_target"] = None
    lines = ["🎯 *حمله — هدف رو انتخاب کن:*", "━━━━━━━━━━━━━━━━━━━━━━"]
    for p in players:
        c = COUNTRIES[p["country"]]
        can, way = can_attack(g["country"], p["country"])
        marker = "✅" if can else "🔒"
        lines.append(f"{marker} {c['flag']} {c['name']}")
    lines.append("\nاز دکمه‌های پایین انتخاب کن 👇")
    await update.message.reply_text("\n".join(lines), reply_markup=attack_target_reply(exclude_uid=uid), parse_mode="Markdown")


async def on_attack_target(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.strip()
    if text not in COUNTRY_MAP:
        return
    target_key = COUNTRY_MAP[text]
    uid = update.effective_user.id
    g = get_game(uid)
    if not g:
        return
    can, way = can_attack(g["country"], target_key)
    if not can:
        await update.message.reply_text(f"❌ {way}")
        return
    ctx.user_data["attack_target"] = target_key
    ctx.user_data["attack_force"] = {"soldiers": 0, "tanks": 0, "planes": 0, "ships": 0}
    c = COUNTRIES[target_key]
    kb = ReplyKeyboardMarkup([
        [KeyboardButton("🪖 سرباز"), KeyboardButton("🛡️ تانک")],
        [KeyboardButton("✈️ هواپیما"), KeyboardButton("🚢 کشتی")],
        [KeyboardButton("🚀 شروع حمله")],
        [KeyboardButton("🔙 منو")],
    ], resize_keyboard=True)
    await update.message.reply_text(
        f"🎯 هدف: {c['flag']} *{c['name']}*\nراه: {way}\n\n"
        f"نیروهات رو انتخاب کن:\n"
        f"🪖 سرباز: 0  |  🛡️ تانک: 0\n✈️ هواپیما: 0  |  🚢 کشتی: 0",
        reply_markup=kb,
        parse_mode="Markdown"
    )


async def on_attack_force(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.strip()
    if not ctx.user_data.get("attack_target"):
        return
    field_map = {
        "🪖 سرباز": ("soldiers", "🪖"),
        "🛡️ تانک": ("tanks", "🛡️"),
        "✈️ هواپیما": ("planes", "✈️"),
        "🚢 کشتی": ("ships", "🚢"),
    }
    if text not in field_map:
        return
    field, emoji = field_map[text]
    uid = update.effective_user.id
    g = get_game(uid)
    total = compute_total_units(g)
    have = total.get(field, 0)
    ctx.user_data["picking_field"] = field
    ctx.user_data["waiting_attack_qty"] = True
    await update.message.reply_text(
        f"{emoji} چند تا {field} بفرستی؟\n\nتو {have} تا داری.\n\nعدد رو تایپ کن:"
    )


async def on_attack_qty_input(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    if not ctx.user_data.get("waiting_attack_qty"):
        return False
    try:
        qty = int(update.message.text.strip())
        if qty < 0:
            raise ValueError
    except:
        return False
    uid = update.effective_user.id
    g = get_game(uid)
    field = ctx.user_data.get("picking_field")
    total = compute_total_units(g)
    have = total.get(field, 0)
    if qty > have:
        await update.message.reply_text(f"❌ نداری! تو {have} تا داری.")
        ctx.user_data["waiting_attack_qty"] = False
        return True
    ctx.user_data["attack_force"][field] = qty
    ctx.user_data["waiting_attack_qty"] = False
    target_key = ctx.user_data["attack_target"]
    c = COUNTRIES[target_key]
    force = ctx.user_data["attack_force"]
    kb = ReplyKeyboardMarkup([
        [KeyboardButton("🪖 سرباز"), KeyboardButton("🛡️ تانک")],
        [KeyboardButton("✈️ هواپیما"), KeyboardButton("🚢 کشتی")],
        [KeyboardButton("🚀 شروع حمله")],
        [KeyboardButton("🔙 منو")],
    ], resize_keyboard=True)
    await update.message.reply_text(
        f"🎯 هدف: {c['flag']} *{c['name']}*\n\n"
        f"نیروها:\n🪖 {force['soldiers']}  |  🛡️ {force['tanks']}\n"
        f"✈️ {force['planes']}  |  🚢 {force['ships']}",
        reply_markup=kb,
        parse_mode="Markdown"
    )
    return True


async def on_attack_go(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    g = get_game(uid)
    force = ctx.user_data.get("attack_force", {})
    target = ctx.user_data.get("attack_target")
    if not target or sum(force.values()) == 0:
        await update.message.reply_text("❌ نیرو انتخاب نکردی.")
        return

    can, way = can_attack(g["country"], target)
    if way == "دریایی":
        total_transport = force["soldiers"] + force["tanks"]
        ship_capacity = force["ships"] * SHIP_CAPACITY
        if total_transport > ship_capacity:
            await update.message.reply_text(f"❌ کشتی کافی نداری!")
            return

    distance = get_distance(g["country"], target)
    multiplier = get_distance_multiplier(distance)
    base_money = 100
    unit_money = (force["soldiers"]*10 + force["tanks"]*20 + force["planes"]*25 + force["ships"]*50)
    unit_oil = (force["tanks"]*3 + force["planes"]*5 + force["ships"]*10)
    unit_food = force["soldiers"]*1
    cost_money = int((base_money + unit_money) * multiplier)
    cost_oil = int(unit_oil * multiplier)
    cost_food = int(unit_food * multiplier)

    if g["money"] < cost_money or g["oil"] < cost_oil or g["food"] < cost_food:
        await update.message.reply_text(f"❌ منابع کافی نداری! نیاز: {cost_money}💰 + {cost_oil}🛢️ + {cost_food}🍞")
        return

    save_game(uid, money=g["money"]-cost_money, oil=g["oil"]-cost_oil, food=g["food"]-cost_food, war_active=1)

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
    if target_uid:
        tg = get_game(target_uid)
        enemy_def = compute_army_power(tg, "defense") if tg else 100
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
            if to_remove_tank <= 0: break
            remove = min(new_unit_tanks[name], to_remove_tank)
            new_unit_tanks[name] -= remove
            to_remove_tank -= remove
            if new_unit_tanks[name] <= 0: del new_unit_tanks[name]
        to_remove_plane = losses.get("planes", 0)
        for name in list(new_unit_planes.keys()):
            if to_remove_plane <= 0: break
            remove = min(new_unit_planes[name], to_remove_plane)
            new_unit_planes[name] -= remove
            to_remove_plane -= remove
            if new_unit_planes[name] <= 0: del new_unit_planes[name]
        to_remove_ship = losses.get("ships", 0)
        for name in list(new_unit_ships.keys()):
            if to_remove_ship <= 0: break
            remove = min(new_unit_ships[name], to_remove_ship)
            new_unit_ships[name] -= remove
            to_remove_ship -= remove
            if new_unit_ships[name] <= 0: del new_unit_ships[name]
        save_game(uid, soldiers=max(0, new_soldiers), unit_tanks=json.dumps(new_unit_tanks), unit_planes=json.dumps(new_unit_planes), unit_ships=json.dumps(new_unit_ships))
        result = (
            f"🏆 *پیروزی!*\n\nهدف: {c['flag']} {c['name']}\n"
            f"قدرت حمله: {fmt(my_atk)}\nدفاع دشمن: {fmt(enemy_def)}\n"
            f"تلفات:\n🪖 {losses.get('soldiers',0)}  🛡️ {losses.get('tanks',0)}  ✈️ {losses.get('planes',0)}  🚢 {losses.get('ships',0)}\n\n"
            f"📊 اشغال {c['name']}: {new_pct}%"
        )
    else:
        losses = {f: int(force.get(f, 0) * random.uniform(0.3, 0.6)) for f in force}
        new_soldiers = g["soldiers"] - losses.get("soldiers", 0)
        new_unit_tanks = json.loads(g.get("unit_tanks") or "{}")
        new_unit_planes = json.loads(g.get("unit_planes") or "{}")
        new_unit_ships = json.loads(g.get("unit_ships") or "{}")
        for name in list(new_unit_tanks.keys()):
            new_unit_tanks[name] = max(0, new_unit_tanks[name] - losses.get("tanks", 0))
            if new_unit_tanks[name] <= 0: del new_unit_tanks[name]
        for name in list(new_unit_planes.keys()):
            new_unit_planes[name] = max(0, new_unit_planes[name] - losses.get("planes", 0))
            if new_unit_planes[name] <= 0: del new_unit_planes[name]
        for name in list(new_unit_ships.keys()):
            new_unit_ships[name] = max(0, new_unit_ships[name] - losses.get("ships", 0))
            if new_unit_ships[name] <= 0: del new_unit_ships[name]
        save_game(uid, soldiers=max(0, new_soldiers), unit_tanks=json.dumps(new_unit_tanks), unit_planes=json.dumps(new_unit_planes), unit_ships=json.dumps(new_unit_ships))
        result = (
            f"💀 *شکست!*\n\nهدف: {c['flag']} {c['name']}\n"
            f"قدرت حمله: {fmt(my_atk)}\nدفاع دشمن: {fmt(enemy_def)}\n\n"
            f"تلفات:\n🪖 {losses.get('soldiers',0)}  🛡️ {losses.get('tanks',0)}  ✈️ {losses.get('planes',0)}  🚢 {losses.get('ships',0)}"
        )
    ctx.user_data["attack_target"] = None
    ctx.user_data["attack_force"] = None
    await update.message.reply_text(result, reply_markup=main_menu_reply(), parse_mode="Markdown")


# ═══════════════════════════════════════════════════════════════
#  🕵️ جاسوسی
# ═══════════════════════════════════════════════════════════════
async def on_spy(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    players = get_active_players(exclude_uid=uid)
    if not players:
        await update.message.reply_text("🕵️ هنوز بازیکن دیگه‌ای نیست.", reply_markup=back_menu_reply())
        return
    lines = ["🕵️ *جاسوسی*", "هزینه: ۵۰💰", "شانس لو رفتن: ۴۰٪", "", "هدف رو انتخاب کن 👇"]
    await update.message.reply_text("\n".join(lines), reply_markup=attack_target_reply(exclude_uid=uid), parse_mode="Markdown")
    ctx.user_data["waiting_spy"] = True


async def on_spy_target(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    if not ctx.user_data.get("waiting_spy"):
        return
    text = update.message.text.strip()
    if text not in COUNTRY_MAP:
        return
    target_key = COUNTRY_MAP[text]
    uid = update.effective_user.id
    g = get_game(uid)
    if g["money"] < 50:
        await update.message.reply_text("❌ ۵۰ پول لازمه.")
        ctx.user_data["waiting_spy"] = False
        return
    save_game(uid, money=g["money"] - 50)
    ctx.user_data["waiting_spy"] = False
    caught = random.random() < 0.40
    if caught:
        result = f"🚨 *لو رفتی!*\n\nجاسوست گیر افتاد و {COUNTRIES[target_key]['name']} فهمید."
    else:
        target_uid = find_player_by_country(target_key)
        tg = get_game(target_uid) if target_uid else None
        if tg:
            result = (
                f"✅ *موفق!*\nاطلاعات {COUNTRIES[target_key]['flag']} {COUNTRIES[target_key]['name']}:\n"
                f"💰 پول: {fmt(tg['money'])}\n⚙️ فولاد: {fmt(tg['steel'])}\n"
                f"🛢️ نفت: {fmt(tg['oil'])}\n🪖 سرباز: {fmt(tg['soldiers'])}"
            )
        else:
            result = f"✅ اطلاعات {COUNTRIES[target_key]['name']} به دست اومد."
    await update.message.reply_text(result, reply_markup=main_menu_reply(), parse_mode="Markdown")


# ═══════════════════════════════════════════════════════════════
#  🤝 دیپلماسی
# ═══════════════════════════════════════════════════════════════
async def on_dip(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    g = get_game(uid)
    allies = json.loads(g["allies"] or "[]")
    wars = json.loads(g["wars"] or "[]")
    allies_names = ", ".join(COUNTRIES[a]["name"] for a in allies if a in COUNTRIES) or "هیچ"
    wars_names = ", ".join(COUNTRIES[a]["name"] for a in wars if a in COUNTRIES) or "هیچ"
    text = (
        f"🤝 *دیپلماسی*\n━━━━━━━━━━━━━━━━━━━━━━\n"
        f"متحدین: {allies_names}\nدر جنگ با: {wars_names}\n\n"
        f"از دکمه‌های پایین انتخاب کن 👇"
    )
    await update.message.reply_text(text, reply_markup=dip_reply(), parse_mode="Markdown")


async def on_dip_action(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.strip()
    kind_map = {
        "🤝 پیشنهاد اتحاد": "ally",
        "☮️ پیشنهاد صلح": "peace",
        "⚔️ اعلام جنگ": "war",
        "💬 مذاکره خصوصی": "talk",
    }
    if text not in kind_map:
        return
    kind = kind_map[text]
    uid = update.effective_user.id
    players = get_active_players(exclude_uid=uid)
    if not players:
        await update.message.reply_text("🤝 هنوز بازیکن دیگه‌ای نیست.")
        return
    ctx.user_data["dip_kind"] = kind
    ctx.user_data["waiting_dip_target"] = True
    await update.message.reply_text(
        f"🎯 کشور هدف رو انتخاب کن 👇",
        reply_markup=attack_target_reply(exclude_uid=uid)
    )


async def on_dip_target(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    if not ctx.user_data.get("waiting_dip_target"):
        return
    text = update.message.text.strip()
    if text not in COUNTRY_MAP:
        return
    target_key = COUNTRY_MAP[text]
    kind = ctx.user_data.get("dip_kind")
    uid = update.effective_user.id
    g = get_game(uid)
    target_uid = find_player_by_country(target_key)
    if not target_uid:
        await update.message.reply_text("❌ بازیکن نداره.")
        ctx.user_data["waiting_dip_target"] = False
        return
    c = COUNTRIES[target_key]
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
        try:
            await ctx.bot.send_message(target_uid, f"⚔️ {COUNTRIES[g['country']]['name']} به تو اعلام جنگ کرد!", parse_mode="Markdown")
        except: pass
        await update.message.reply_text(f"⚔️ جنگ با {c['name']} اعلام شد.", reply_markup=main_menu_reply())
    elif kind == "talk":
        ctx.user_data["talk_target"] = target_uid
        ctx.user_data["waiting_talk_msg"] = True
        await update.message.reply_text(f"💬 پیامت رو برای {c['name']} بنویس:", reply_markup=back_menu_reply())
    else:
        try:
            await ctx.bot.send_message(target_uid,
                f"📩 درخواست دیپلماتیک از {COUNTRIES[g['country']]['name']}\nنوع: {kind}\n\nقبول می‌کنی؟",
                parse_mode="Markdown")
        except: pass
        await update.message.reply_text(f"📤 درخواست به {c['name']} فرستاده شد.", reply_markup=main_menu_reply())
    ctx.user_data["waiting_dip_target"] = False


async def on_talk_msg_input(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    if not ctx.user_data.get("waiting_talk_msg"):
        return False
    target_uid = ctx.user_data.get("talk_target")
    uid = update.effective_user.id
    g = get_game(uid)
    msg = update.message.text
    try:
        await ctx.bot.send_message(target_uid,
            f"💬 پیام مذاکره از {COUNTRIES[g['country']]['name']}:\n{msg}", parse_mode="Markdown")
    except: pass
    await update.message.reply_text("✅ پیام فرستاده شد.", reply_markup=main_menu_reply())
    ctx.user_data["waiting_talk_msg"] = False
    return True


# ═══════════════════════════════════════════════════════════════
#  📦 تجارت
# ═══════════════════════════════════════════════════════════════
async def on_trade(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    g = get_game(uid)
    text = (
        f"📦 *تجارت*\n━━━━━━━━━━━━━━━━━━━━━━\n"
        f"💰 {fmt(g['money'])}  🍞 {fmt(g['food'])}  ⚙️ {fmt(g['steel'])}\n"
        f"🛢️ {fmt(g['oil'])}  🪨 {fmt(g['coal'])}  👥 {fmt(g['manpower'])}\n\n"
        f"می‌خوای چی صادر کنی؟\nاز دکمه‌های پایین انتخاب کن 👇"
    )
    await update.message.reply_text(text, reply_markup=trade_reply(), parse_mode="Markdown")


async def on_trade_res(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.strip()
    res_map = {
        "💰 پول": "money", "🍞 غذا": "food", "⚙️ فولاد": "steel",
        "🛢️ نفت": "oil", "🪨 زغال": "coal", "👥 نیرو": "manpower",
    }
    if text not in res_map:
        return
    res = res_map[text]
    ctx.user_data["trade_res"] = res
    ctx.user_data["waiting_trade_amount"] = True
    uid = update.effective_user.id
    g = get_game(uid)
    await update.message.reply_text(
        f"🔢 چند تا *{text}* بدی؟\n\nتو {fmt(g[res])} تا داری.\n\nعدد رو تایپ کن:",
        reply_markup=back_menu_reply(),
        parse_mode="Markdown"
    )


async def on_trade_amount_input(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    if not ctx.user_data.get("waiting_trade_amount"):
        return False
    try:
        amount = int(update.message.text.strip())
        if amount <= 0:
            raise ValueError
    except:
        return False
    uid = update.effective_user.id
    g = get_game(uid)
    res = ctx.user_data["trade_res"]
    if g[res] < amount:
        await update.message.reply_text(f"❌ نداری! تو {g[res]} تا داری.")
        ctx.user_data["waiting_trade_amount"] = False
        return True
    ctx.user_data["trade_amount"] = amount
    ctx.user_data["waiting_trade_amount"] = False
    ctx.user_data["waiting_trade_want"] = True
    await update.message.reply_text(
        f"✅ {amount} انتخاب شد.\n\nدر ازای چی می‌خوای؟",
        reply_markup=trade_reply()
    )
    return True


async def on_trade_want(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    if not ctx.user_data.get("waiting_trade_want"):
        return
    text = update.message.text.strip()
    res_map = {
        "💰 پول": "money", "🍞 غذا": "food", "⚙️ فولاد": "steel",
        "🛢️ نفت": "oil", "🪨 زغال": "coal", "👥 نیرو": "manpower",
    }
    if text not in res_map:
        return
    want = res_map[text]
    ctx.user_data["trade_want"] = want
    ctx.user_data["waiting_trade_want"] = False
    uid = update.effective_user.id
    players = get_active_players(exclude_uid=uid)
    if not players:
        await update.message.reply_text("هنوز بازیکن دیگه‌ای نیست.")
        return
    ctx.user_data["waiting_trade_target"] = True
    await update.message.reply_text("🎯 طرف مقابل رو انتخاب کن 👇", reply_markup=attack_target_reply(exclude_uid=uid))


async def on_trade_target(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    if not ctx.user_data.get("waiting_trade_target"):
        return
    text = update.message.text.strip()
    if text not in COUNTRY_MAP:
        return
    target_key = COUNTRY_MAP[text]
    uid = update.effective_user.id
    g = get_game(uid)
    res = ctx.user_data["trade_res"]
    amount = ctx.user_data["trade_amount"]
    want = ctx.user_data["trade_want"]
    target_uid = find_player_by_country(target_key)
    if not target_uid:
        await update.message.reply_text("❌ بازیکن نداره.")
        ctx.user_data["waiting_trade_target"] = False
        return
    try:
        await ctx.bot.send_message(target_uid,
            f"📦 پیشنهاد تجاری از {COUNTRIES[g['country']]['name']}\n"
            f"می‌ده: {amount} {res}\nمی‌خواد: {amount} {want}",
            parse_mode="Markdown")
    except: pass
    await update.message.reply_text(f"📤 پیشنهاد به {COUNTRIES[target_key]['name']} فرستاده شد.", reply_markup=main_menu_reply())
    ctx.user_data["waiting_trade_target"] = False


# ═══════════════════════════════════════════════════════════════
#  🔙 منو
# ═══════════════════════════════════════════════════════════════
async def on_menu_btn(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    g = get_game(uid)
    if not g:
        await update.message.reply_text("اول بازی جدید بساز: /start")
        return
    check_and_run_turn(uid)
    g = get_game(uid)
    await update.message.reply_text(render_dashboard(g), reply_markup=main_menu_reply(), parse_mode="Markdown")


# ═══════════════════════════════════════════════════════════════
#  🎯 Router اصلی متنی
# ═══════════════════════════════════════════════════════════════
async def on_text_router(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    if not update.message or not update.message.text:
        return
    text = update.message.text.strip()

    # Waiting inputs
    if await on_tax_input(update, ctx): return
    if await on_soldier_input(update, ctx): return
    if await on_tank_qty_input(update, ctx): return
    if await on_plane_qty_input(update, ctx): return
    if await on_ship_qty_input(update, ctx): return
    if await on_attack_qty_input(update, ctx): return
    if await on_talk_msg_input(update, ctx): return
    if await on_trade_amount_input(update, ctx): return

    # Country pick — contexts
    if text in COUNTRY_MAP:
        if ctx.user_data.get("waiting_spy"):
            await on_spy_target(update, ctx); return
        if ctx.user_data.get("waiting_dip_target"):
            await on_dip_target(update, ctx); return
        if ctx.user_data.get("waiting_trade_target"):
            await on_trade_target(update, ctx); return
        if ctx.user_data.get("attack_target"):
            await on_attack_target(update, ctx); return
        if not get_game(update.effective_user.id):
            await on_country_pick(update, ctx); return

    # منو اصلی
    if text == "🎮 بازی جدید": await on_newgame(update, ctx); return
    if text == "📖 راهنما": await on_help(update, ctx); return
    if text == "💰 اقتصاد": await on_eco(update, ctx); return
    if text == "⚔️ ارتش": await on_army(update, ctx); return
    if text == "🔬 تحقیقات": await on_research(update, ctx); return
    if text == "🏗️ پروژه‌ها": await on_projects(update, ctx); return
    if text == "🤝 دیپلماسی": await on_dip(update, ctx); return
    if text == "📦 تجارت": await on_trade(update, ctx); return
    if text == "🎯 حمله": await on_attack(update, ctx); return
    if text == "🕵️ جاسوسی": await on_spy(update, ctx); return
    if text == "💵 مالیات": await on_tax(update, ctx); return
    if text == "🏛️ امور کشور": await on_internal(update, ctx); return
    if text == "📊 آمار کامل": await on_stats(update, ctx); return
    if text == "🔙 منو": await on_menu_btn(update, ctx); return

    # اقتصاد
    if text == "💵 تغییر مالیات": await on_tax(update, ctx); return
    if text == "🏗️ ساخت پروژه": await on_projects(update, ctx); return

    # امور
    if text == "📢 سخنرانی": await on_speech(update, ctx); return
    if text == "🚔 سرکوب": await on_suppress(update, ctx); return

    # ارتش
    if text == "🪖 خرید سرباز": await on_buy_soldier(update, ctx); return
    if text == "🛡️ خرید تانک": await on_buy_tank(update, ctx); return
    if text == "✈️ خرید هواپیما": await on_buy_plane(update, ctx); return
    if text == "🚢 خرید کشتی": await on_buy_ship(update, ctx); return

    # دیپلماسی
    if text in ("🤝 پیشنهاد اتحاد", "☮️ پیشنهاد صلح", "⚔️ اعلام جنگ", "💬 مذاکره خصوصی"):
        await on_dip_action(update, ctx); return

    # تجارت
    if text in ("💰 پول", "🍞 غذا", "⚙️ فولاد", "🛢️ نفت", "🪨 زغال", "👥 نیرو"):
        if ctx.user_data.get("waiting_trade_want"):
            await on_trade_want(update, ctx); return
        await on_trade_res(update, ctx); return

    # حمله
    if text == "🚀 شروع حمله": await on_attack_go(update, ctx); return
    if text in ("🪖 سرباز", "🛡️ تانک", "✈️ هواپیما", "🚢 کشتی"):
        if ctx.user_data.get("attack_target"):
            await on_attack_force(update, ctx); return

    # لیست‌ها
    uid = update.effective_user.id
    g = get_game(uid)
    if g:
        tree = RESEARCH.get(g["country"], [])
        for n, c, d, p in tree:
            if text == n:
                await on_research_pick(update, ctx); return
        for key, p in PROJECTS.items():
            if text == p["name"]:
                await on_project_pick(update, ctx); return
        unlocked = json.loads(g["research"] or "[]")
        if text in unlocked:
            for u in get_available_units(g, "tank"):
                if u["unlocked"] and u["name"] == text:
                    await on_tank_pick(update, ctx); return
            for u in get_available_units(g, "plane"):
                if u["unlocked"] and u["name"] == text:
                    await on_plane_pick(update, ctx); return
            for u in get_available_units(g, "ship"):
                if u["unlocked"] and u["name"] == text:
                    await on_ship_pick(update, ctx); return
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
    if not tg:
        await update.message.reply_text("خطا.")
        return

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
#  🕐 نوبت خودکار
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
        try:
            await context.bot.send_message(
                p["user_id"],
                text,
                parse_mode="Markdown",
                reply_markup=main_menu_reply()
            )
        except Exception as e:
            log.warning(f"خطا در ارسال به {p['user_id']}: {e}")


# ═══════════════════════════════════════════════════════════════
#  🚀 main
# ═══════════════════════════════════════════════════════════════
def main():
    init_db()

    if "توکن" in BOT_TOKEN or not BOT_TOKEN:
        print("❌ توکن ربات تنظیم نشده!")
        return

    keep_alive()

    app = Application.builder().token(BOT_TOKEN).base_url(BALE_API).build()

    # Commands
    app.add_handler(CommandHandler("start", cmd_start))
    app.add_handler(CommandHandler("menu", cmd_menu))
    app.add_handler(CommandHandler("next_turn", cmd_next_turn))
    app.add_handler(CommandHandler("admin", cmd_admin))
    app.add_handler(CommandHandler("give", cmd_give))
    app.add_handler(CommandHandler("players", cmd_players))

    # عضویت
    app.add_handler(MessageHandler(filters.TEXT & filters.Regex("^عضو شدم ✅$"), on_joined_check))

    # اطلاعات [کشور] برای ادمین
    app.add_handler(MessageHandler(filters.TEXT & filters.Regex("^اطلاعات "), cmd_country_info))

    # Router اصلی
    app.add_handler(MessageHandler(
        filters.TEXT & ~filters.COMMAND,
        on_text_router
    ))

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
