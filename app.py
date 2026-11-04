import os
import re
import time
import requests
from flask import Flask, request, jsonify
from flask_cors import CORS

app = Flask(__name__)
CORS(app, resources={r"/api/*": {"origins": "*"}})

TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

# Store replies for customer sessions in memory
# Format: { session_id: [ {"id": 1, "text": "...", "timestamp": 123456} ] }
CLIENT_MESSAGES = {}
MESSAGE_COUNTER = 0

def send_telegram_alert(session_id, message, page_url, customer="guest"):
    if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
        print("Telegram credentials missing!")
        return

    text = (
        f"💬 *New Chat Message*\n\n"
        f"*Session:* `{session_id}`\n"
        f"*Customer:* {customer}\n"
        f"*Page:* {page_url}\n"
        f"*Message:* {message}\n\n"
        f"👉 _Reply directly to this message to answer the customer._"
    )
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    try:
        requests.post(
            url,
            json={
                "chat_id": TELEGRAM_CHAT_ID,
                "text": text,
                "parse_mode": "Markdown"
            },
            timeout=5
        )
    except Exception as e:
        print(f"Telegram send error: {e}")

@app.route("/api/chat", methods=["POST"])
def chat():
    data = request.get_json() or {}
    session_id = data.get("session_id", "anonymous")
    user_message = data.get("message", "").strip()
    page_url = data.get("page_url", "unknown")
    customer = data.get("customer", "guest")

    if not user_message:
        return jsonify({"error": "Empty message"}), 400

    send_telegram_alert(session_id, user_message, page_url, customer)

    return jsonify({
        "reply": "Bienvenido a 🌶️ pepitonas.com !",
        "session_id": session_id
    })

@app.route("/api/chat/messages", methods=["GET"])
@app.route("/api/messages", methods=["GET"])
def get_messages():
    session_id = request.args.get("session_id")
    after_id = int(request.args.get("after_id", 0))

    if not session_id or session_id not in CLIENT_MESSAGES:
        return jsonify({"messages": []})

    new_msgs = [m for m in CLIENT_MESSAGES[session_id] if m["id"] > after_id]
    return jsonify({"messages": new_msgs})

@app.route("/api/telegram-webhook", methods=["POST"])
def telegram_webhook():
    global MESSAGE_COUNTER
    update = request.get_json() or {}
    message_obj = update.get("message", {})

    sender_chat_id = str(message_obj.get("chat", {}).get("id", ""))
    # Security: only accept replies from your authorized chat ID
    if TELEGRAM_CHAT_ID and sender_chat_id != str(TELEGRAM_CHAT_ID):
        return jsonify({"ok": True})

    text = message_obj.get("text", "").strip()
    if not text:
        return jsonify({"ok": True})

    target_session_id = None

    # Case 1: You replied directly to a bot alert message in Telegram
    reply_to = message_obj.get("reply_to_message", {})
    if reply_to:
        quoted_text = reply_to.get("text", "")
        match = re.search(r"Session:\*?\s*[`*_]?([a-zA-Z0-9_\-]+)[`*_]?", quoted_text, re.IGNORECASE)
        if match:
            target_session_id = match.group(1)

    # Case 2: You used a command like /reply <session_id> <text> or /r <session_id> <text>
    if not target_session_id:
        cmd_match = re.match(r"^/(?:reply|r)\s+([a-zA-Z0-9_\-]+)\s+(.+)$", text, re.DOTALL)
        if cmd_match:
            target_session_id = cmd_match.group(1)
            text = cmd_match.group(2).strip()

    if target_session_id:
        MESSAGE_COUNTER += 1
        if target_session_id not in CLIENT_MESSAGES:
            CLIENT_MESSAGES[target_session_id] = []

        CLIENT_MESSAGES[target_session_id].append({
            "id": MESSAGE_COUNTER,
            "text": text,
            "timestamp": time.time()
        })

        # Send confirmation checkmark back to Telegram
        if TELEGRAM_BOT_TOKEN:
            confirm_url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
            try:
                requests.post(
                    confirm_url,
                    json={
                        "chat_id": sender_chat_id,
                        "text": f"✅ Sent to customer (`{target_session_id}`)",
                        "parse_mode": "Markdown",
                        "reply_to_message_id": message_obj.get("message_id")
                    },
                    timeout=5
                )
            except Exception as e:
                print(f"Error sending confirmation: {e}")

    return jsonify({"ok": True})

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
