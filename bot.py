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
