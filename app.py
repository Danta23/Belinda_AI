import os
import traceback
import sys
from datetime import datetime
from flask import Flask, request, jsonify
from handlers import handle_status, handle_chat, handle_shell, handle_gen, handle_weather, handle_voice, handle_search
from dotenv import load_dotenv  # support .env

# Load variabel dari file .env
load_dotenv()

app = Flask(__name__)

# Ambil port dari .env (default 8001 kalau tidak ada)
FLASK_PORT = int(os.getenv("FLASK_PORT", 8001))

def log_event(level, event, details=""):
    suffix = f" | {details}" if details else ""
    print(
        f"[{datetime.now().astimezone().isoformat(timespec='seconds')}] "
        f"[{level}] [AI API] [{event}]{suffix}",
        file=sys.stderr,
        flush=True,
    )

@app.before_request
def log_request_info():
    content_length = request.content_length or 0
    log_event("INFO", "REQUEST", f"method={request.method} | path={request.path} | bytes={content_length}")

@app.after_request
def log_response_info(response):
    log_event("INFO", "RESPONSE", f"method={request.method} | path={request.path} | status={response.status_code}")
    return response

@app.errorhandler(Exception)
def handle_exception(e):
    """Log any unhandled exception to the terminal."""
    print("\n!!! UNHANDLED EXCEPTION !!!", file=sys.stderr)
    traceback.print_exc()
    return jsonify({"error": str(e), "traceback": traceback.format_exc()}), 500

@app.route("/health", methods=["GET"])
def health():
    return jsonify({
        "status": "ok",
        "service": "belinda-ai",
        "cloud_ai_configured": bool(os.getenv("GROQ_API_KEY")),
    })

@app.route("/status", methods=["POST"])
def status():
    try:
        data = request.get_json(force=True)
        resp = handle_status(data)
        print(f"Response: {resp.get_data(as_text=True)}", file=sys.stderr)
        return resp
    except Exception as e:
        print(f"Error in /status: {e}", file=sys.stderr)
        traceback.print_exc()
        return jsonify({"error": str(e)}), 500

@app.route("/chat", methods=["POST"])
def chat():
    try:
        data = request.get_json(force=True)
        resp = handle_chat(data)
        # handle_chat might return a string or a response object
        if hasattr(resp, 'get_data'):
             print(f"Response: {resp.get_data(as_text=True)}", file=sys.stderr)
        else:
             print(f"Response: {resp}", file=sys.stderr)
        return resp
    except Exception as e:
        print(f"Error in /chat: {e}", file=sys.stderr)
        traceback.print_exc()
        return jsonify({"error": str(e)}), 500

@app.route("/voice", methods=["POST"])
def voice():
    try:
        resp = handle_voice(request)
        print(f"Response: {resp}", file=sys.stderr)
        return resp
    except Exception as e:
        print(f"Error in /voice: {e}", file=sys.stderr)
        traceback.print_exc()
        return jsonify({"error": str(e)}), 500

@app.route("/shell", methods=["POST"])
def shell():
    try:
        data = request.get_json(force=True)
        resp = handle_shell(data)
        print(f"Response: {resp}", file=sys.stderr)
        return resp
    except Exception as e:
        print(f"Error in /shell: {e}", file=sys.stderr)
        traceback.print_exc()
        return jsonify({"error": str(e)}), 500

@app.route("/gen", methods=["POST"])
def gen():
    try:
        data = request.get_json(force=True)
        resp = handle_gen(data)
        print(f"Response: {resp}", file=sys.stderr)
        return resp
    except Exception as e:
        print(f"Error in /gen: {e}", file=sys.stderr)
        traceback.print_exc()
        return jsonify({"error": str(e)}), 500

@app.route("/weather", methods=["POST"])
def weather():
    try:
        data = request.get_json(force=True)
        resp = handle_weather(data)
        print(f"Response: {resp}", file=sys.stderr)
        return resp
    except Exception as e:
        print(f"Error in /weather: {e}", file=sys.stderr)
        traceback.print_exc()
        return jsonify({"error": str(e)}), 500

@app.route("/search", methods=["POST"])
def search_route():
    try:
        data = request.get_json(force=True)
        resp = handle_search(data)
        print(f"Response: {resp}", file=sys.stderr)
        return resp
    except Exception as e:
        print(f"Error in /search: {e}", file=sys.stderr)
        traceback.print_exc()
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    # Ensure subprocesses in Docker can find python if needed
    os.environ["PATH"] = os.getcwd() + "/venv/bin:" + os.environ["PATH"]
    log_event(
        "INFO",
        "STARTUP",
        f"host=0.0.0.0 | port={FLASK_PORT} | cloud_ai_configured={bool(os.getenv('GROQ_API_KEY'))}",
    )
    app.run(host="0.0.0.0", port=FLASK_PORT, debug=True)
