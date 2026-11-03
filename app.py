from flask import Flask, request, jsonify
from flask_cors import CORS

app = Flask(__name__)
# Allow requests from your WordPress store URL
CORS(app, resources={r"/api/*": {"origins": "*"}})

@app.route("/api/chat", methods=["POST"])
def chat():
    data = request.get_json() or {}
    
    session_id = data.get("session_id")
    user_message = data.get("message", "").strip()
    current_page = data.get("page_url", "")
    
    if not user_message:
        return jsonify({"error": "Empty message"}), 400

    # ----------------------------------------------------
    # Process the message here:
    # 1. Custom logic / FAQ lookup
    # 2. Forward to LLM (OpenAI, Claude, etc.)
    # 3. Or forward to Telegram/Discord for a human agent
    # ----------------------------------------------------
    bot_reply = f"Thank you for your message! You asked: '{user_message}'. We are checking availability."

    return jsonify({
        "reply": bot_reply,
        "session_id": session_id
    })

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)


