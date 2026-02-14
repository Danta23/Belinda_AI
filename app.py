import os
from flask import Flask, request, jsonify
from groq import Groq
from datetime import datetime  # Import modul waktu
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)

# Masukkan API Key Groq kamu di sini
client = Groq(api_key=os.getenv("GROQ_API_KEY"))

# Daftar model gratis dari Groq (Auto Fallback)
MODEL_LIST = [
    "llama-3.3-70b-versatile",
    "llama-3.1-70b-versatile",
    "llama3-70b-8192",
    "llama3-8b-8192",
    "gemma2-9b-it"
]

bot_status = {}

@app.route('/status', methods=['POST'])
def status():
    data = request.json
    sender = data.get('sender')
    action = data.get('action')
    if sender not in bot_status: bot_status[sender] = True
    if action == "toggle": bot_status[sender] = not bot_status[sender]
    return jsonify({"active": bot_status[sender]})

@app.route('/chat', methods=['POST'])
def chat():
    data = request.json
    msg = data.get('msg')
    
    # Ambil Waktu Real-Time Sekarang
    now = datetime.now()
    waktu_sekarang = now.strftime("%A, %d %B %Y | %H:%M:%S")
    milidetik = now.strftime("%f")[:3] # Ambil 3 angka awal milidetik

    def get_ai_response(message, model_index=0):
        if model_index >= len(MODEL_LIST):
            return "⚠️ Maaf, semua jalur AI Belinda sedang sibuk. Coba beberapa saat lagi."

        current_model = MODEL_LIST[model_index]
        try:
            completion = client.chat.completions.create(
                model=current_model,
                messages=[
                    {
                        "role": "system", 
                        "content": (
                            f"Kamu adalah Belinda AI, asisten cerdas buatan Studio 234 oleh Danta (The River). "
                            f"Website: https://danta23.github.io/Studio-234/index.html\n\n"
                            f"WAKTU REAL-TIME SAAT INI:\n"
                            f"Tahun: {now.year}\n"
                            f"Bulan: {now.strftime('%B')}\n"
                            f"Hari/Minggu: {now.strftime('%A')}\n"
                            f"Jam/Waktu: {now.strftime('%H:%M:%S')}.{milidetik}\n"
                            f"Gunakan data waktu ini jika pengguna bertanya tentang jam atau tanggal."
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
            return "⚠️ Terjadi gangguan teknis pada server AI Belinda."

    return get_ai_response(msg)

if __name__ == '__main__':
    PORT = int(os.getenv("FLASK_PORT", 8000))
    app.run(port=PORT)