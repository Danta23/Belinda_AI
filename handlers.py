import os
from flask import jsonify
from groq import Groq
from datetime import datetime
from dotenv import load_dotenv  # support .env

# Load variabel dari file .env
load_dotenv()

# Ambil API key dari .env
groq_api_key = os.getenv("GROQ_API_KEY")
if not groq_api_key:
    raise ValueError("⚠️ GROQ_API_KEY tidak ditemukan di file .env")

client = Groq(api_key=groq_api_key)

# Daftar model fallback
MODEL_LIST = [
    "llama-3.3-70b-versatile",
    "llama-3.1-70b-versatile",
    "llama3-70b-8192",
    "llama3-8b-8192",
    "gemma2-9b-it"
]

# Status bot per sender
bot_status = {}

def handle_status(data):
    sender = data.get("sender")
    action = data.get("action")

    if sender not in bot_status:
        bot_status[sender] = True

    if action == "toggle":
        bot_status[sender] = not bot_status[sender]

    return jsonify({"active": bot_status[sender]})

def handle_chat(data):
    sender = data.get("sender")
    msg = data.get("msg")

    if not bot_status.get(sender, True):
        return "⚠️ AI Belinda sedang OFF."

    now = datetime.now()
    waktu_sekarang = now.strftime("%A, %d %B %Y | %H:%M:%S")
    milidetik = now.strftime("%f")[:3]

    def get_ai_response(message, model_index=0):
        if model_index >= len(MODEL_LIST):
            return "⚠️ Semua model free sedang sibuk. Coba lagi nanti."

        current_model = MODEL_LIST[model_index]
        try:
            completion = client.chat.completions.create(
                model=current_model,
                messages=[
                    {
                        "role": "system",
                        "content": (
                            f"Kamu adalah Belinda AI, asisten cerdas buatan Studio 234 oleh Danta.\n"
                            f"Waktu real-time: {waktu_sekarang}.{milidetik}"
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
            return f"⚠️ Terjadi gangguan teknis pada server AI Belinda: {str(e)}"
    return get_ai_response(msg)