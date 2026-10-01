import os
import threading
from http.server import HTTPServer, BaseHTTPRequestHandler

import requests
from telegram import Update
from telegram.ext import Application, MessageHandler, ContextTypes, filters

# =========================
# تنظیمات
# =========================

BALE_TOKEN = "1614589734:BTCrjcrl0i2Mr9z47KUs6HXDzsy1tUx9fiw"
GROQ_API_KEY = os.environ.get("GROQ_API_KEY")

GROQ_URL = "https://api.groq.com/openai/v1/chat/completions"
GROQ_MODEL = "llama-3.3-70b-versatile"


# =========================
# وب‌سرور برای Render
# =========================

class Handler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b"AI Bot is running!")
    def log_message(self, format, *args):
        pass


def run_server():
    port = int(os.environ.get("PORT", 10000))
    HTTPServer(("0.0.0.0", port), Handler).serve_forever()


# =========================
# هوش مصنوعی Groq
# =========================

def ask_ai(user_message):
    try:
        headers = {
            "Authorization": f"Bearer {GROQ_API_KEY}",
            "Content-Type": "application/json"
        }
        data = {
            "model": GROQ_MODEL,
            "messages": [
                {
                    "role": "system",
                    "content": "تو یه دستیار فارسی‌زبان هستی. کوتاه، مفید و دقیق جواب بده."
                },
                {
                    "role": "user",
                    "content": user_message
                }
            ],
            "temperature": 0.7,
            "max_tokens": 500
        }
        r = requests.post(GROQ_URL, headers=headers, json=data, timeout=30)
        if r.status_code == 200:
            result = r.json()
            return result["choices"][0]["message"]["content"].strip()
        else:
            print("Groq error:", r.status_code, r.text)
            return f"خطا در هوش مصنوعی: {r.status_code}"
    except Exception as e:
        print("Ask AI error:", e)
        return f"خطا: {e}"


# =========================
# هندلر پیام‌ها
# =========================

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message or not update.message.text:
        return

    text = update.message.text.strip()

    if text.startswith("/"):
        return

    await update.message.chat.send_action("typing")

    response = ask_ai(text)
    await update.message.reply_text(response)


# =========================
# اجرا
# =========================

def main():
    threading.Thread(target=run_server, daemon=True).start()

    app = Application.builder().token(BALE_TOKEN).base_url("https://tapi.bale.ai/bot").build()
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    print("AI Bot started...")
    app.run_polling()


if __name__ == "__main__":
    main()
