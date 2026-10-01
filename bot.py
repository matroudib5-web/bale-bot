import os
import re
import threading
from http.server import HTTPServer, BaseHTTPRequestHandler

import requests
from telegram import Update
from telegram.ext import Application, MessageHandler, ContextTypes, filters

TOKEN = "1614589734:BTCrjcrl0i2Mr9z47KUs6HXDzsy1tUx9fiw"


class Handler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b"Search Bot is running!")
    def log_message(self, format, *args):
        pass


def run_server():
    port = int(os.environ.get("PORT", 10000))
    HTTPServer(("0.0.0.0", port), Handler).serve_forever()


def search_web(query):
    # تلاش ۱: DuckDuckGo HTML
    try:
        url = "https://html.duckduckgo.com/html/"
        r = requests.post(
            url,
            data={"q": query},
            timeout=10,
            headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}
        )
        if r.status_code == 200:
            snippets = re.findall(r'result__snippet[^>]*>(.*?)</a>', r.text, re.DOTALL)
            if snippets:
                answer = ""
                for s in snippets[:3]:
                    clean = re.sub(r'<[^>]+>', '', s).strip()
                    if clean:
                        answer += f"• {clean}\n\n"
                if answer:
                    return answer.strip()
    except Exception as e:
        print("DDG error:", e)

    # تلاش ۲: Wikipedia فارسی
    try:
        url = "https://fa.wikipedia.org/api/rest_v1/page/summary/" + query.replace(" ", "_")
        r = requests.get(url, timeout=10)
        if r.status_code == 200:
            data = r.json()
            if "extract" in data and data["extract"]:
                return f"📖 {data['extract']}"
    except Exception as e:
        print("Wiki error:", e)

    return "چیزی پیدا نکردم."


async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message or not update.message.text:
        return
    text = update.message.text.strip()
    if text.startswith("/"):
        return
    response = search_web(text)
    await update.message.reply_text(response)


def main():
    threading.Thread(target=run_server, daemon=True).start()
    app = Application.builder().token(TOKEN).base_url("https://tapi.bale.ai/bot").build()
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    print("Search Bot started...")
    app.run_polling()


if __name__ == "__main__":
    main()
