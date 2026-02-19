import os
import json
from flask import jsonify
from groq import Groq
from datetime import datetime
from dotenv import load_dotenv  # support .env

# Load variables from .env
load_dotenv()

# Get API key from .env
groq_api_key = os.getenv("GROQ_API_KEY")
if not groq_api_key:
    raise ValueError("⚠️ GROQ_API_KEY not found in .env file")

client = Groq(api_key=groq_api_key)

# Fallback model list
MODEL_LIST = [
    "llama-3.3-70b-versatile",
    "llama-3.1-70b-versatile",
    "llama3-70b-8192",
    "llama3-8b-8192",
    "gemma2-9b-it"
]

# Bot status per sender
bot_status = {}

# --- Chat History Support ---
HISTORY_FILE = "chat_history.json"

def load_chat_history():
    """Load chat history from JSON file."""
    if os.path.exists(HISTORY_FILE):
        try:
            with open(HISTORY_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except json.JSONDecodeError:
            return []
    return []

def handle_status(data):
    sender = data.get("sender")
    action = data.get("action")

    if sender not in bot_status:
        bot_status[sender] = True

    if action == "toggle":
        bot_status[sender] = not bot_status[sender]

    # Include chat history snippet in status
    history = load_chat_history()
    sender_history = [h for h in history if h.get("sender") == sender]

    return jsonify({
        "active": bot_status[sender],
        "history_count": len(sender_history),
        "recent_history": sender_history[-10:]  # last 10 messages
    })

def handle_chat(data):
    sender = data.get("sender")
    msg = data.get("msg")

    if not bot_status.get(sender, True):
        return "⚠️ Belinda AI is currently OFF."

    now = datetime.now()
    waktu_sekarang = now.strftime("%A, %d %B %Y | %H:%M:%S")
    milidetik = now.strftime("%f")[:3]

    # Load chat history for context
    history = load_chat_history()
    sender_history = [h for h in history if h.get("sender") == sender]
    recent_context = "\n".join(
        [f"{h['participant']}: {h['text']}" for h in sender_history[-5:]]
    )

    def get_ai_response(message, model_index=0):
        if model_index >= len(MODEL_LIST):
            return "⚠️ All free models are busy. Please try again later."

        current_model = MODEL_LIST[model_index]
        try:
            completion = client.chat.completions.create(
                model=current_model,
                messages=[
                    {
                        "role": "system",
                        "content": (
                            f"You are Belinda AI, an intelligent assistant created by Studio 234 (Danta).\n"
                            f"Real-time: {waktu_sekarang}.{milidetik}\n"
                            f"Recent chat context:\n{recent_context}"
                        )
                    },
                    {"role": "user", "content": message}
                ],
                temperature=0.7,
                max_tokens=1024,
            )
            return completion.choices[0].message.content
        except Exception as e:
            error_str = str(e).lower()
            if "rate_limit" in error_str or "429" in error_str:
                return get_ai_response(message, model_index + 1)
            return f"⚠️ Technical issue with Belinda AI server: {str(e)}"
    return get_ai_response(msg)