import os
from flask import Flask, request
from handlers import handle_status, handle_chat
from dotenv import load_dotenv  # support .env

# Load variabel dari file .env
load_dotenv()

app = Flask(__name__)

# Ambil port dari .env (default 8000 kalau tidak ada)
FLASK_PORT = int(os.getenv("FLASK_PORT", 8000))

@app.route("/status", methods=["POST"])
def status():
    data = request.get_json(force=True)
    return handle_status(data)

@app.route("/chat", methods=["POST"])
def chat():
    data = request.get_json(force=True)
    return handle_chat(data)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=FLASK_PORT, debug=True)