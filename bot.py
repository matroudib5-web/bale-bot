# -*- coding: utf-8 -*-

"""
Bale Digital Twin
یادگیری همیشه فعال است.
فقط پاسخ‌گویی خودکار قابل خاموش و روشن کردن است.
"""

import os
import re
import time
import sqlite3
import logging
import requests

from difflib import SequenceMatcher
from threading import Lock
from datetime import datetime, timezone


# =========================================================
# تنظیمات اصلی
# =========================================================

# توکن ربات را اینجا قرار بده.
# اگر مخزن GitHub عمومی است، توکن واقعی را داخل آن منتشر نکن.
BOT_TOKEN = "توکن_ربات_بله_را_اینجا_قرار_بده"

ADMIN_IDS = {
    1618371215,
    1937011765,
}

GROUP_LINK = "https://ble.ir/join/3bTuk3VWRB"

# برای Render بهتر است مسیر یک دیسک پایدار را تعیین کنی.
DB_PATH = os.getenv("DB_PATH", "digital_twin.db")

BALE_API = f"https://tapi.bale.ai/bot{BOT_TOKEN}"

REQUEST_TIMEOUT = 45
POLL_TIMEOUT = 30

# حداقل شباهت برای پیدا کردن پاسخ قبلی
MIN_SIMILARITY = 0.82

# پاسخ خودکار با علامت مشخص می‌شود.
REPLY_PREFIX = "🤖 "

# حداکثر تعداد پیام‌های والد برای بررسی زنجیره
MAX_REPLY_DEPTH = 30

# فاصله کوتاه برای جلوگیری از فشار بیش از حد به API
ERROR_SLEEP = 3


# =========================================================
# گزارش خطاها
# =========================================================

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s",
)

logger = logging.getLogger("bale_digital_twin")


# =========================================================
# اتصال به دیتابیس
# =========================================================

db_lock = Lock()


def db_connect():
    connection = sqlite3.connect(
        DB_PATH,
        timeout=30,
        check_same_thread=False,
    )

    connection.row_factory = sqlite3.Row

    connection.execute("PRAGMA journal_mode=WAL")
    connection.execute("PRAGMA foreign_keys=ON")

    return connection


def init_database():
    with db_lock:
        conn = db_connect()

        try:
            conn.executescript(
                """
                CREATE TABLE IF NOT EXISTS settings (
                    key TEXT PRIMARY KEY,
                    value TEXT NOT NULL
                );

                CREATE TABLE IF NOT EXISTS messages (
                    chat_id TEXT NOT NULL,
                    message_id INTEGER NOT NULL,
                    user_id TEXT,
                    user_name TEXT,
                    text TEXT,
                    date TEXT,
                    parent_message_id INTEGER,
                    parent_user_id TEXT,
                    parent_text TEXT,

                    PRIMARY KEY (chat_id, message_id)
                );

                CREATE TABLE IF NOT EXISTS examples (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,

                    chat_id TEXT NOT NULL,

                    source_message_id INTEGER,
                    source_user_id TEXT,
                    source_user_name TEXT,
                    source_text TEXT,

                    source_parent_id INTEGER,
                    source_parent_user_id TEXT,
                    source_parent_text TEXT,

                    response_message_id INTEGER UNIQUE,
                    response_user_id TEXT,
                    response_text TEXT,

                    created_at TEXT
                );

                CREATE INDEX IF NOT EXISTS idx_examples_chat
                ON examples(chat_id);

                CREATE INDEX IF NOT EXISTS idx_messages_chat
                ON messages(chat_id);

                CREATE TABLE IF NOT EXISTS processed (
                    update_id INTEGER PRIMARY KEY,
                    processed_at TEXT
                );
                """
            )

            # یادگیری همیشه روشن است.
            set_setting_db(conn, "learning_enabled", "1", commit=False)

            # پاسخ‌گویی در شروع خاموش است.
            if get_setting_db(conn, "bot_enabled") is None:
                set_setting_db(
                    conn,
                    "bot_enabled",
                    "0",
                    commit=False,
                )

            if get_setting_db(conn, "target_group") is None:
                set_setting_db(
                    conn,
                    "target_group",
                    "",
                    commit=False,
                )

            if get_setting_db(conn, "update_offset") is None:
                set_setting_db(
                    conn,
                    "update_offset",
                    "0",
                    commit=False,
                )

            conn.commit()

        finally:
            conn.close()


def get_setting_db(conn, key):
    row = conn.execute(
        "SELECT value FROM settings WHERE key = ?",
        (key,),
    ).fetchone()

    return row["value"] if row else None


def set_setting_db(conn, key, value, commit=True):
    conn.execute(
        """
        INSERT INTO settings (key, value)
        VALUES (?, ?)
        ON CONFLICT(key)
        DO UPDATE SET value = excluded.value
        """,
        (key, str(value)),
    )

    if commit:
        conn.commit()


def get_setting(key, default=""):
    with db_lock:
        conn = db_connect()

        try:
            value = get_setting_db(conn, key)
            return value if value is not None else default

        finally:
            conn.close()


def set_setting(key, value):
    with db_lock:
        conn = db_connect()

        try:
            set_setting_db(conn, key, value)

        finally:
            conn.close()


# =========================================================
# ارتباط با API بله
# =========================================================

def api_call(method, params=None, post=False):
    url = f"{BALE_API}/{method}"

    try:
        if post:
            response = requests.post(
                url,
                json=params or {},
                timeout=REQUEST_TIMEOUT,
            )
        else:
            response = requests.get(
                url,
                params=params or {},
                timeout=REQUEST_TIMEOUT,
            )

        response.raise_for_status()

        data = response.json()

        if not data.get("ok", False):
            logger.warning(
                "API returned an unsuccessful result for %s",
                method,
            )

        return data

    except requests.RequestException as exc:
        logger.error("API request failed for %s: %s", method, exc)

    except ValueError:
        logger.error("Invalid JSON received from API: %s", method)

    return None


def send_message(
    chat_id,
    text,
    reply_to_message_id=None,
):
    if not text:
        return None

    params = {
        "chat_id": chat_id,
        "text": str(text)[:4000],
    }

    if reply_to_message_id is not None:
        params["reply_to_message_id"] = reply_to_message_id

    result = api_call(
        "sendMessage",
        params=params,
        post=True,
    )

    if result and result.get("ok"):
        return result.get("result")

    return None


# =========================================================
# ابزارهای پیام
# =========================================================

def get_message_text(message):
    if not isinstance(message, dict):
        return ""

    text = message.get("text")

    if text is None:
        text = message.get("caption", "")

    return str(text).strip() if text else ""


def get_sender_id(message):
    user = message.get("from") or {}

    if user.get("id") is None:
        return None

    return str(user["id"])


def get_sender_name(message):
    user = message.get("from") or {}

    first = user.get("first_name", "")
    last = user.get("last_name", "")
    username = user.get("username", "")

    full_name = f"{first} {last}".strip()

    if full_name:
        return full_name

    if username:
        return f"@{username}"

    return "نامشخص"


def is_admin(user_id):
    if user_id is None:
        return False

    try:
        return int(user_id) in ADMIN_IDS

    except (ValueError, TypeError):
        return False


def normalize_text(text):
    text = str(text or "").strip().lower()

    text = text.replace("ي", "ی")
    text = text.replace("ك", "ک")
    text = text.replace("ۀ", "ه")
    text = text.replace("ة", "ه")

    text = re.sub(r"\s+", " ", text)

    return text


def similarity(text1, text2):
    a = normalize_text(text1)
    b = normalize_text(text2)

    if not a or not b:
        return 0.0

    if a == b:
        return 1.0

    return SequenceMatcher(None, a, b).ratio()


def current_time():
    return datetime.now(timezone.utc).isoformat()


# =========================================================
# ذخیره پیام‌ها و زنجیره ریپلای
# =========================================================

def save_message(chat_id, message, depth=0, visited=None):
    """
    پیام‌های مرتبط با ریپلای را ذخیره می‌کند.

    اگر پیام ریپلای نباشد و از طریق یک زنجیره هم
    به آن نرسیده باشیم، به‌تنهایی ذخیره نمی‌شود.

    از پیمایش بی‌نهایت زنجیره جلوگیری می‌شود.
    """

    if not isinstance(message, dict):
        return

    if depth > MAX_REPLY_DEPTH:
        return

    if visited is None:
        visited = set()

    message_id = message.get("message_id")

    if message_id is None:
        return

    if message_id in visited:
        return

    visited.add(message_id)

    text = get_message_text(message)

    # پیام‌های بدون متن برای آموزش پاسخ استفاده نمی‌شوند.
    if not text:
        return

    user_id = get_sender_id(message)
    user_name = get_sender_name(message)

    parent = message.get("reply_to_message")

    parent_id = None
    parent_user_id = None
    parent_text = None

    if isinstance(parent, dict):
        parent_id = parent.get("message_id")
        parent_user_id = get_sender_id(parent)
        parent_text = get_message_text(parent)

    # پیام فقط وقتی ذخیره می‌شود که خودش ریپلای باشد.
    # پیام والد نیز در همین ارتباط ذخیره می‌شود.
    if parent_id is None:
        return

    with db_lock:
        conn = db_connect()

        try:
            conn.execute(
                """
                INSERT INTO messages (
                    chat_id,
                    message_id,
                    user_id,
                    user_name,
                    text,
                    date,
                    parent_message_id,
                    parent_user_id,
                    parent_text
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)

                ON CONFLICT(chat_id, message_id)
                DO UPDATE SET
                    user_id = excluded.user_id,
                    user_name = excluded.user_name,
                    text = excluded.text,
                    parent_message_id = excluded.parent_message_id,
                    parent_user_id = excluded.parent_user_id,
                    parent_text = excluded.parent_text
                """,
                (
                    str(chat_id),
                    int(message_id),
                    user_id,
                    user_name,
                    text,
                    str(message.get("date", "")),
                    parent_id,
                    parent_user_id,
                    parent_text,
                ),
            )

            conn.commit()

        finally:
            conn.close()

    # اگر والد خودش ریپلای داشته باشد، آن را هم بررسی می‌کنیم.
    # بعضی پاسخ‌های API زنجیره کامل را برنمی‌گردانند.
    if isinstance(parent, dict):
        save_message(
            chat_id,
            parent,
            depth=depth + 1,
            visited=visited,
        )


# =========================================================
# آموزش از پاسخ‌های خود کاربر
# =========================================================

def save_training_example(chat_id, message):
    """
    فقط پاسخ‌های ریپلای‌شده‌ای که یکی از حساب‌های
    صاحب ربات نوشته باشد، نمونه آموزشی می‌شوند.

    وضعیت بات روشن یا خاموش هیچ تأثیری روی یادگیری ندارد.
    """

    author_id = get_sender_id(message)

    if not is_admin(author_id):
        return False

    response_text = get_message_text(message)

    if not response_text:
        return False

    source = message.get("reply_to_message")

    # اگر پاسخ ریپلای نباشد، نمونه آموزشی نمی‌سازیم.
    if not isinstance(source, dict):
        return False

    source_text = get_message_text(source)

    if not source_text:
        return False

    response_message_id = message.get("message_id")

    if response_message_id is None:
        return False

    source_user_id = get_sender_id(source)
    source_user_name = get_sender_name(source)

    source_parent = source.get("reply_to_message")

    source_parent_id = None
    source_parent_user_id = None
    source_parent_text = None

    if isinstance(source_parent, dict):
        source_parent_id = source_parent.get("message_id")
        source_parent_user_id = get_sender_id(source_parent)
        source_parent_text = get_message_text(source_parent)

    with db_lock:
        conn = db_connect()

        try:
            conn.execute(
                """
                INSERT OR IGNORE INTO examples (
                    chat_id,

                    source_message_id,
                    source_user_id,
                    source_user_name,
                    source_text,

                    source_parent_id,
                    source_parent_user_id,
                    source_parent_text,

                    response_message_id,
                    response_user_id,
                    response_text,

                    created_at
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    str(chat_id),

                    source.get("message_id"),
                    source_user_id,
                    source_user_name,
                    source_text,

                    source_parent_id,
                    source_parent_user_id,
                    source_parent_text,

                    int(response_message_id),
                    author_id,
                    response_text,

                    current_time(),
                ),
            )

            conn.commit()

            return True

        finally:
            conn.close()


# =========================================================
# پیدا کردن پاسخ مناسب از حافظه
# =========================================================

def find_best_answer(chat_id, incoming_message):
    """
    پاسخ مناسب را از نمونه‌های قبلی پیدا می‌کند.

    به متن پیام و اطلاعات ریپلای توجه می‌کند.
    اگر پاسخ مناسبی پیدا نشود، None برمی‌گرداند.
    """

    incoming_text = get_message_text(incoming_message)

    if not incoming_text:
        return None

    incoming_parent = incoming_message.get("reply_to_message")

    incoming_parent_text = get_message_text(incoming_parent)
    incoming_parent_user_id = get_sender_id(incoming_parent) if isinstance(
        incoming_parent, dict
    ) else None

    incoming_user_id = get_sender_id(incoming_message)

    with db_lock:
        conn = db_connect()

        try:
            rows = conn.execute(
                """
                SELECT *
                FROM examples
                WHERE chat_id = ?
                ORDER BY id DESC
                LIMIT 3000
                """,
                (str(chat_id),),
            ).fetchall()

        finally:
            conn.close()

    best_answer = None
    best_score = 0.0

    incoming_norm = normalize_text(incoming_text)

    for row in rows:
        source_text = row["source_text"] or ""
        response_text = row["response_text"] or ""

        if not source_text or not response_text:
            continue

        score = similarity(incoming_text, source_text)

        # اگر متن پیام تقریباً یکسان باشد، امتیاز بالاست.
        if incoming_norm == normalize_text(source_text):
            score = 1.0

        # اگر شخصی در نمونه قبلی به کاربر پاسخ داده بود،
        # تطابق فرستنده می‌تواند به انتخاب کمک کند.
        if (
            incoming_user_id
            and row["source_user_id"]
            and incoming_user_id == row["source_user_id"]
        ):
            score = min(1.0, score + 0.04)

        # اطلاعات ریپلای را هم بررسی می‌کنیم.
        if incoming_parent_text and row["source_parent_text"]:
            parent_score = similarity(
                incoming_parent_text,
                row["source_parent_text"],
            )

            score = (score * 0.75) + (parent_score * 0.25)

        # وقتی فرستنده پیام والد با نمونه قبلی یکسان باشد،
        # کمی اطمینان بیشتری داریم.
        if (
            incoming_parent_user_id
            and row["source_parent_user_id"]
            and incoming_parent_user_id == row["source_parent_user_id"]
        ):
            score = min(1.0, score + 0.03)

        # برای جلوگیری از پاسخ‌های شخصی اشتباه:
        # اگر متن مشابه است ولی فرستنده متفاوت است،
        # از امتیاز کم نمی‌کنیم؛ بااین‌حال تطابق متنی
        # به‌تنهایی تضمین نمی‌کند پاسخ در همه موقعیت‌ها مناسب باشد.

        if score > best_score:
            best_score = score
            best_answer = response_text

    if best_score >= MIN_SIMILARITY:
        return best_answer

    return None


# =========================================================
# دستورات مدیریتی
# =========================================================

def handle_command(chat_id, message):
    text = get_message_text(message).strip()
    user_id = get_sender_id(message)

    if not is_admin(user_id):
        return False

    command = normalize_text(text)

    # تنظیم گروه هدف
    if command in ("/setgroup", "تنظیم گروه", "ثبت گروه"):
        set_setting("target_group", str(chat_id))

        send_message(
            chat_id,
            "✅ این گروه به‌عنوان گروه هدف ثبت شد.\n"
            "🧠 یادگیری همیشه فعاله.\n"
            "🤖 برای فعال‌کردن پاسخ‌گویی بنویس: بات روشن",
        )

        return True

    # روشن کردن پاسخ‌گویی خودکار
    if command in ("/bot_on", "بات روشن"):
        set_setting("bot_enabled", "1")

        send_message(
            chat_id,
            "🤖 پاسخ‌گویی خودکار روشن شد.\n"
            "🧠 یادگیری همچنان فعاله.",
        )

        return True

    # خاموش کردن پاسخ‌گویی خودکار
    if command in ("/bot_off", "بات خاموش"):
        set_setting("bot_enabled", "0")

        send_message(
            chat_id,
            "🔕 پاسخ‌گویی خودکار خاموش شد.\n"
            "🧠 یادگیری ادامه داره و اطلاعات جدید ذخیره می‌شن.",
        )

        return True

    # وضعیت سیستم
    if command in ("/status", "بات وضعیت", "وضعیت بات"):
        bot_enabled = get_setting("bot_enabled", "0") == "1"
        target_group = get_setting("target_group", "")

        send_message(
            chat_id,
            "📊 وضعیت ربات\n\n"
            "🧠 یادگیری: همیشه روشن ✅\n"
            f"🤖 پاسخ‌گویی: {'روشن ✅' if bot_enabled else 'خاموش 🔕'}\n"
            f"👥 گروه هدف: {target_group or 'هنوز ثبت نشده'}",
        )

        return True

    # آمار حافظه
    if command in ("/stats", "آمار", "آمار بات"):
        with db_lock:
            conn = db_connect()

            try:
                message_count = conn.execute(
                    "SELECT COUNT(*) AS n FROM messages"
                ).fetchone()["n"]

                example_count = conn.execute(
                    "SELECT COUNT(*) AS n FROM examples"
                ).fetchone()["n"]

            finally:
                conn.close()

        send_message(
            chat_id,
            "📚 آمار حافظه ربات\n\n"
            f"💬 پیام‌های مرتبط ذخیره‌شده: {message_count}\n"
            f"🧠 نمونه‌های آموزشی: {example_count}\n"
            "🔒 وضعیت یادگیری: همیشه روشن",
        )

        return True

    # راهنما
    if command in ("/help", "راهنما", "کمک بات"):
        send_message(
            chat_id,
            "📖 راهنمای ربات\n\n"
            "بات روشن — فعال‌کردن جواب‌دهی\n"
            "بات خاموش — توقف جواب‌دهی\n"
            "بات وضعیت — دیدن وضعیت سیستم\n"
            "آمار — نمایش اطلاعات حافظه\n"
            "تنظیم گروه — ثبت گروه هدف\n\n"
            "🧠 یادگیری همیشه فعاله؛ "
            "بات خاموش فقط جواب‌دادن رو متوقف می‌کنه.",
        )

        return True

    return False


# =========================================================
# مدیریت پیام‌های ورودی
# =========================================================

def process_message(message):
    if not isinstance(message, dict):
        return

    chat = message.get("chat") or {}
    chat_id = chat.get("id")

    if chat_id is None:
        return

    text = get_message_text(message)

    if not text:
        return

    user_id = get_sender_id(message)

    # دستورهای مدیریتی فقط برای مدیران هستند.
    if is_admin(user_id):
        if handle_command(chat_id, message):
            return

    target_group = get_setting("target_group", "")

    # اگر گروه هدف هنوز ثبت نشده باشد، پیام‌های عادی پردازش نمی‌شوند.
    if not target_group:
        return

    if str(chat_id) != str(target_group):
        return

    # از پاسخ‌دادن به پیام‌های خود ربات جلوگیری می‌کنیم.
    if message.get("from", {}).get("is_bot"):
        return

    # =====================================================
    # یادگیری مستقل از وضعیت پاسخ‌گویی
    # =====================================================

    if message.get("reply_to_message"):
        save_message(chat_id, message)

        # تنها پاسخ‌های ریپلای‌شده مدیران نمونه آموزشی‌اند.
        if is_admin(user_id):
            save_training_example(chat_id, message)

    # پیام‌های معمولی مدیران، بدون ریپلای، آموزش نیستند.
    # بااین‌حال، می‌توانند در صورت روشن‌بودن بات بررسی شوند،
    # ولی ربات به پیام‌های خودش پاسخ نمی‌دهد.

    # =====================================================
    # پاسخ‌گویی خودکار
    # =====================================================

    if get_setting("bot_enabled", "0") != "1":
        return

    # به پیام‌های دو حساب مدیر پاسخ نده.
    if is_admin(user_id):
        return

    # پاسخ به پیام‌های مناسب حتی اگر پیام جدید ریپلای نباشد،
    # بر اساس نمونه‌های ذخیره‌شده انجام می‌شود.
    answer = find_best_answer(chat_id, message)

    # اگر نمونه مناسبی وجود نداشته باشد، سکوت می‌کند.
    if not answer:
        return

    reply_to_id = message.get("message_id")

    send_message(
        chat_id,
        REPLY_PREFIX + answer,
        reply_to_message_id=reply_to_id,
    )


# =========================================================
# جلوگیری از پردازش دوباره Updateها
# =========================================================

def was_processed(update_id):
    with db_lock:
        conn = db_connect()

        try:
            row = conn.execute(
                "SELECT update_id FROM processed WHERE update_id = ?",
                (int(update_id),),
            ).fetchone()

            return row is not None

        finally:
            conn.close()


def mark_processed(update_id):
    with db_lock:
        conn = db_connect()

        try:
            conn.execute(
                """
                INSERT OR IGNORE INTO processed (
                    update_id,
                    processed_at
                )
                VALUES (?, ?)
                """,
                (int(update_id), current_time()),
            )

            conn.commit()

        finally:
            conn.close()


def save_offset(offset):
    set_setting("update_offset", str(int(offset)))


def get_offset():
    try:
        return int(get_setting("update_offset", "0"))

    except (ValueError, TypeError):
        return 0


# =========================================================
# اجرای اصلی
# =========================================================

def main():
    if not BOT_TOKEN or "اینجا_قرار_بده" in BOT_TOKEN:
        raise RuntimeError(
            "ابتدا توکن ربات بله را در ابتدای bot.py قرار بده."
        )

    init_database()

    # در صورت وجود keep_alive.py، آن را اجرا می‌کنیم.
    try:
        from keep_alive import keep_alive
        keep_alive()

    except ImportError:
        logger.info("keep_alive.py پیدا نشد؛ اجرای ربات ادامه دارد.")

    # بررسی اتصال ربات
    me = api_call("getMe")

    if not me or not me.get("ok"):
        raise RuntimeError(
            "اتصال به API بله برقرار نشد. توکن و اتصال اینترنت را بررسی کن."
        )

    bot_info = me.get("result", {})

    logger.info(
        "Bot started: %s",
        bot_info.get("username") or bot_info.get("id"),
    )

    offset = get_offset()

    logger.info("Learning is always enabled.")
    logger.info(
        "Auto-reply is %s.",
        "enabled" if get_setting("bot_enabled", "0") == "1"
        else "disabled",
    )

    while True:
        result = api_call(
            "getUpdates",
            params={
                "offset": offset,
                "timeout": POLL_TIMEOUT,
            },
        )

        if not result or not result.get("ok"):
            time.sleep(ERROR_SLEEP)
            continue

        updates = result.get("result", [])

        for update in updates:
            update_id = update.get("update_id")

            if update_id is None:
                continue

            offset = max(offset, int(update_id) + 1)

            try:
                # پیام معمولی
                message = update.get("message")

                # پیام ویرایش‌شده را هم می‌پذیریم.
                if message is None:
                    message = update.get("edited_message")

                if message:
                    process_message(message)

                mark_processed(update_id)

            except Exception:
                logger.exception(
                    "Error processing update %s",
                    update_id,
                )

            finally:
                save_offset(offset)


if __name__ == "__main__":
    main()
