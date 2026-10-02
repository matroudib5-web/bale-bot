# keep_alive.py
from flask import Flask
from threading import Thread
import os

app = Flask(__name__)


@app.route('/')
def home():
    return "🎖️ WW2 Bot is alive!", 200


@app.route('/health')
def health():
    return "OK", 200


def run():
    port = int(os.environ.get("PORT", 8080))
    app.run(host="0.0.0.0", port=port)


def keep_alive():
    t = Thread(target=run)
    t.daemon = True
    t.start()
