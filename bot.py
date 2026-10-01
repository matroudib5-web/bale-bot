import os
import threading
from http.server import HTTPServer, BaseHTTPRequestHandler

from telegram import Update
from telegram.ext import Application, MessageHandler, ContextTypes, filters
from duckduckgo_search import DDGS

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
    try:
        results = DDGS().text(query, max_results=3)
        if not results:
            return "چیزی پیدا نکردم."
        answer = ""
        for r in results:
            answer += f"📌 {r.get('title', '')}\n{r.get('body', '')}\n\n"
        return answer.strip()
    except Exception as e:
        return f"خطا در سرچ: {e}"


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
