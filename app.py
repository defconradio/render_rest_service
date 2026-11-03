import os
import requests
from flask import Flask, request, jsonify
from flask_cors import CORS

app = Flask(__name__)
CORS(app, resources={r"/api/*": {"origins": "*"}})

TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

def send_telegram_alert(session_id, message, page_url):
    if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
        print("Telegram credentials missing!")
        return

    text = (
        f"💬 *New Chat Message*\n"
        f"*Session:* `{session_id}`\n"
        f"*Page:* {page_url}\n"
        f"*Message:* {message}"
    )
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    try:
        requests.post(url, json={"chat_id": TELEGRAM_CHAT_ID, "text": text, "parse_mode": "Markdown"}, timeout=5)
    except Exception as e:
        print(f"Telegram error: {e}")

@app.route("/api/chat", methods=["POST"])
def chat():
    data = request.get_json() or {}
    session_id = data.get("session_id", "anonymous")
    user_message = data.get("message", "").strip()
    page_url = data.get("page_url", "unknown")

    if not user_message:
        return jsonify({"error": "Empty message"}), 400

    send_telegram_alert(session_id, user_message, page_url)

    return jsonify({
        "reply": "Thank you! Our support team has received your message.",
        "session_id": session_id
    })

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
