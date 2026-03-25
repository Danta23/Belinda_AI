import os
import sys
import threading
import subprocess
import asyncio
import json
import traceback
import shutil
import webbrowser
import urllib.parse
from datetime import datetime
import time
import random

import toga
from toga.style import Pack
from toga.style.pack import COLUMN, ROW, CENTER, LEFT, RIGHT

# --- APP VERSION ---
APP_VERSION = "1.4.7.2-13"

# --- EARLY CRASH LOG ---
def _write_crash_log(msg):
    try:
        log_dir = os.environ.get('PYTHON_HOME', os.path.dirname(os.path.abspath(__file__)))
        crash_file = os.path.join(log_dir, "crash_report.log")
        with open(crash_file, "a") as f:
            f.write(f"\n[{datetime.now()}] {msg}\n")
    except:
        pass

def global_exception_handler(exc_type, exc_value, exc_traceback):
    try:
        err = "".join(traceback.format_exception(exc_type, exc_value, exc_traceback))
        _write_crash_log(f"GLOBAL EXCEPTION:\n{err}")
    except:
        print(f"CRASH HANDLER FAILED: {exc_value}")

sys.excepthook = global_exception_handler

# --- CONSTANTS ---
TAGLINES = [
    "Liquid Mobile Edition",
    "Your AI Assistant on the Go",
    "Modern. Sleek. Powerful.",
    "Next-Gen Chatbot Interface",
    "The Future of Mobile AI",
    "Optimized for Android & Tablet",
    "Intelligent. Fluent. Smooth.",
    "Crafted with Liquid Glass UI",
    "Redefining Mobile Intelligence",
    "Stay Connected. Stay Smart."
]

# --- TRANSLATIONS ---
TRANSLATIONS = {
    "English": {
        "title_setup": "INITIAL SETUP",
        "desc_setup": "Please ensure Termux is running in the background. Clone the repository to continue.",
        "btn_clone": "CLONE PROJECT",
        "btn_deploy": "FULL DEPLOYMENT",
        "btn_start": "START BOT",
        "btn_stop": "STOP BOT",
        "btn_reset": "RESET BOT",
        "btn_factory": "FACTORY RESET",
        "status_cloning": "Cloning repository...",
        "status_deploying": "System Setup & Installing...",
        "status_ready": "READY",
        "nav_dash": "DASHBOARD",
        "nav_sett": "SETTINGS",
        "lbl_lang": "Language",
        "lbl_theme": "Theme",
        "btn_save": "SAVE CHANGES",
        "toast_saved": "Settings Saved! START enabled.",
        "toast_cloned": "Clone Successful! Run Full Deployment.",
        "toast_deploy_done": "Deployment Complete! Configure API Keys.",
        "sys_status": "SYSTEM STATUS",
        "pop_title": "Confirm Reset",
        "pop_desc": "Are you sure? This will delete all project files and settings.",
        "btn_yes": "YES, RESET",
        "btn_no": "CANCEL"
    },
    "Indonesian": {
        "title_setup": "PENGATURAN AWAL",
        "desc_setup": "Pastikan Termux berjalan di background. Clone repository untuk lanjut.",
        "btn_clone": "CLONE PROJEK",
        "btn_deploy": "DEPLOY TOTAL",
        "btn_start": "MULAI BOT",
        "btn_stop": "HENTIKAN BOT",
        "btn_reset": "RESET BOT",
        "btn_factory": "RESET PABRIK",
        "status_cloning": "Sedang meng-clone...",
        "status_deploying": "Setup Sistem & Instalasi...",
        "status_ready": "SIAP",
        "nav_dash": "PANEL",
        "nav_sett": "PENGATURAN",
        "lbl_lang": "Bahasa",
        "lbl_theme": "Tema",
        "btn_save": "SIMPAN PERUBAHAN",
        "toast_saved": "Disimpan! Tombol START aktif.",
        "toast_cloned": "Clone Berhasil! Jalankan Deploy Total.",
        "toast_deploy_done": "Instalasi Selesai! Atur API Key.",
        "sys_status": "STATUS SISTEM",
        "pop_title": "Konfirmasi Reset",
        "pop_desc": "Apakah Anda yakin? Ini akan menghapus semua file projek dan data.",
        "btn_yes": "YA, RESET",
        "btn_no": "BATAL"
    },
    "Japanese": {
        "title_setup": "初期設定",
        "desc_setup": "Termuxがバックグラウンドで動作していることを確認し、クローンを作成してください。",
        "btn_clone": "クローン作成",
        "btn_deploy": "完全展開",
        "btn_start": "ボットを開始",
        "btn_stop": "ボットを停止",
        "btn_reset": "リセット",
        "btn_factory": "初期化",
        "status_cloning": "クローン中...",
        "status_deploying": "システム設定中...",
        "status_ready": "準備完了",
        "nav_dash": "ダッシュボード",
        "nav_sett": "設定",
        "lbl_lang": "言語",
        "lbl_theme": "テーマ",
        "btn_save": "変更を保存",
        "toast_saved": "保存完了！開始可能です。",
        "toast_cloned": "クローン完了！",
        "toast_deploy_done": "展開完了！APIキーを設定してください。",
        "sys_status": "システム状態",
        "pop_title": "初期化の確認",
        "pop_desc": "本当によろしいですか？すべてのファイルと設定が削除されます。",
        "btn_yes": "はい、リセット",
        "btn_no": "キャンセル"
    }
}

DARK_THEME = {
    "bg": "#0F0F14",
    "card": "#1A1A24",
    "text": "#FFFFFF",
    "text_sec": "#A0A0A0",
    "input_bg": "#000000",
    "console_text": "#33FF33"
}

LIGHT_THEME = {
    "bg": "#F8F9FA",
    "card": "#FFFFFF",
    "text": "#000000",
    "text_sec": "#505050",
    "input_bg": "#E0E0E0",
    "console_text": "#000000"
}

ACCENT_BLUE = "#33CCFF"
DANGER_RED = "#FF4D4D"
SUCCESS_GREEN = "#33CC66"

class SettingsManager:
    def __init__(self, app):
        self.app = app
        self.file = os.path.join(self.app.paths.data, "settings.json")
        self.data = self.load()

    def load(self):
        if os.path.exists(self.file):
            try:
                with open(self.file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except: pass
        return {"language": "English", "theme": "Dark", "deployed": False}

    def save(self):
        try:
            os.makedirs(os.path.dirname(self.file), exist_ok=True)
            with open(self.file, 'w', encoding='utf-8') as f:
                json.dump(self.data, f)
        except: pass

class BelindaApp(toga.App):
    def startup(self):
        # Force the working directory to the app's writable internal data folder
        try:
            os.makedirs(self.paths.data, exist_ok=True)
            os.chdir(self.paths.data)
        except Exception as e:
            _write_crash_log(f"Dir Error: {e}")
            
        self.settings = SettingsManager(self)
        self.main_window = toga.MainWindow(title="Belinda AI Manager", size=(400, 700))
        self.container = toga.Box(style=Pack(direction=COLUMN, flex=1))
        
        # Dashboard Components
        self.status_box = toga.Box(style=Pack(direction=COLUMN, margin=10))
        
        # Header with System Status and Clear Button
        self.lbl_sys_status = toga.Label("SYSTEM STATUS", style=Pack(font_size=10, flex=1))
        self.btn_clear_log = toga.Button("CLEAR", on_press=self.handle_clear_log, style=Pack(width=70, font_size=9))
        self.status_header = toga.Box(children=[self.lbl_sys_status, self.btn_clear_log], style=Pack(direction=ROW, alignment=CENTER))
        
        self.lbl_status_val = toga.Label("READY", style=Pack(font_size=20, font_weight='bold'))
        self.status_box.add(self.status_header)
        self.status_box.add(self.lbl_status_val)
        
        self.console = toga.MultilineTextInput(readonly=True, style=Pack(flex=1, margin=10, font_family='monospace', font_size=10))
        
        self.btn_box = toga.Box(style=Pack(direction=COLUMN, margin=10))
        grid_box = toga.Box(style=Pack(direction=COLUMN))
        row1 = toga.Box(style=Pack(direction=ROW, margin=5))
        self.btn_start = toga.Button("START BOT", on_press=self.handle_start, style=Pack(flex=1, margin=2))
        self.btn_stop = toga.Button("STOP BOT", on_press=self.handle_stop, style=Pack(flex=1, margin=2, color=DANGER_RED))
        row1.add(self.btn_start); row1.add(self.btn_stop)
        row2 = toga.Box(style=Pack(direction=ROW, margin=5))
        self.btn_reset = toga.Button("RESET BOT", on_press=self.handle_reset, style=Pack(flex=1, margin=2))
        self.btn_factory = toga.Button("FACTORY RESET", on_press=self.handle_factory, style=Pack(flex=1, margin=2, color=DANGER_RED))
        row2.add(self.btn_reset); row2.add(self.btn_factory)
        
        self.btn_deploy = toga.Button("FULL DEPLOYMENT", on_press=self.handle_deploy, style=Pack(margin=5, background_color=SUCCESS_GREEN, color="#FFFFFF"))
        grid_box.add(row1); grid_box.add(row2)
        self.btn_box.add(grid_box); self.btn_box.add(self.btn_deploy)
        
        # Navigation
        self.nav_box = toga.Box(style=Pack(direction=ROW, height=60))
        self.btn_nav_dash = toga.Button("DASHBOARD", on_press=lambda x: self.switch_view("dash"), style=Pack(flex=1))
        self.btn_nav_sett = toga.Button("SETTINGS", on_press=lambda x: self.switch_view("sett"), style=Pack(flex=1))
        self.nav_box.add(self.btn_nav_dash); self.nav_box.add(self.btn_nav_sett)
        
        # Settings Components
        self.settings_content = toga.Box(style=Pack(direction=COLUMN, margin=20))
        self.settings_scroll = toga.ScrollContainer(content=self.settings_content, style=Pack(flex=1))
        
        self.lbl_sett_title = toga.Label("CONFIGURATION", style=Pack(font_size=20, font_weight='bold', margin_bottom=20))
        self.theme_sel = toga.Selection(items=["Dark", "Light"], on_change=self.toggle_theme)
        self.lang_sel = toga.Selection(items=list(TRANSLATIONS.keys()), on_change=self.change_lang)
        self.env_box = toga.Box(style=Pack(direction=COLUMN, margin_top=20))
        self.btn_save_sett = toga.Button("SAVE CHANGES", on_press=self.save_settings, style=Pack(margin_top=20, background_color=SUCCESS_GREEN))
        
        self.refresh_ui()
        self.is_deploying_flow = False
        self.switch_view("splash")
        self.main_window.content = self.container
        self.main_window.show()
        
        self.check_root_status()
        asyncio.create_task(self.delayed_startup())

    def get_text(self, key):
        lang = self.settings.data["language"]
        return TRANSLATIONS.get(lang, TRANSLATIONS["English"]).get(key, key)

    def refresh_ui(self):
        t = DARK_THEME if self.settings.data["theme"] == "Dark" else LIGHT_THEME
        self.container.style.background_color = t['bg']
        self.status_box.style.background_color = t['card']
        self.lbl_sys_status.style.color = t['text_sec']
        self.lbl_status_val.style.color = ACCENT_BLUE if self.settings.data["theme"] == "Dark" else "#004470"
        self.console.style.background_color = t['input_bg']
        self.console.style.color = t['console_text']
        self.nav_box.style.background_color = t['card']
        self.btn_clear_log.style.color = t['text_sec']
        
        self.btn_deploy.text = self.get_text("btn_deploy")
        self.btn_start.text = self.get_text("btn_start")
        self.btn_stop.text = self.get_text("btn_stop")
        self.btn_reset.text = self.get_text("btn_reset")
        self.btn_factory.text = self.get_text("btn_factory")
        self.btn_nav_dash.text = self.get_text("nav_dash")
        self.btn_nav_sett.text = self.get_text("nav_sett")

    def handle_clear_log(self, widget):
        self.console.value = ""

    def switch_view(self, view_name):
        if view_name != "sett":
            self.is_deploying_flow = False
        self.container.clear()
        if view_name == "splash":
            # Splash container with flex=1, centered horizontally and vertically
            splash = toga.Box(style=Pack(direction=COLUMN, flex=1, alignment=CENTER, justify_content=CENTER))
            
            # Use text_align=CENTER for labels to ensure they are centered on all screen widths
            title_lbl = toga.Label("BELINDA AI", style=Pack(font_size=40, font_weight='bold', color=ACCENT_BLUE, text_align=CENTER, width=300))
            tag_lbl = toga.Label(random.choice(TAGLINES), style=Pack(font_size=14, color="#AAAAAA", margin_top=10, text_align=CENTER, width=300))
            ver_lbl = toga.Label(f"v{APP_VERSION}", style=Pack(font_size=10, color="#888888", margin_top=20, text_align=CENTER, width=300))
            
            splash.add(title_lbl)
            splash.add(tag_lbl)
            splash.add(ver_lbl)
            self.container.add(splash)
        elif view_name == "setup":
            t = DARK_THEME if self.settings.data["theme"] == "Dark" else LIGHT_THEME
            setup = toga.Box(style=Pack(direction=COLUMN, margin=30))
            setup.add(toga.Label(self.get_text("title_setup"), style=Pack(font_size=24, font_weight='bold', color=t['text'])))
            setup.add(toga.Label(self.get_text("desc_setup"), style=Pack(margin_top=20, color=t['text_sec'])))
            self.btn_clone = toga.Button(self.get_text("btn_clone"), on_press=self.start_clone, style=Pack(margin_top=40, font_size=16, background_color=ACCENT_BLUE, color="#FFFFFF"))
            self.progress_clone = toga.ProgressBar(max=100, style=Pack(margin_top=10))
            setup.add(self.btn_clone)
            setup.add(self.progress_clone)
            self.container.add(setup)
        elif view_name == "dash":
            self.container.add(self.status_box)
            self.container.add(self.console)
            self.container.add(self.btn_box)
            self.container.add(self.nav_box)
        elif view_name == "sett":
            self.settings_content.add(self.lbl_sett_title)
            self.settings_content.add(toga.Box(children=[toga.Label("Language", style=Pack(flex=1)), self.lang_sel], style=Pack(direction=ROW, margin=5)))
            self.settings_content.add(toga.Box(children=[toga.Label("Theme", style=Pack(flex=1)), self.theme_sel], style=Pack(direction=ROW, margin=5)))
            self.settings_content.add(self.env_box)
            self.settings_content.add(self.btn_save_sett)
            self.refresh_env_list()
            self.container.add(self.settings_scroll)
            self.container.add(self.nav_box)

    async def delayed_startup(self):
        await asyncio.sleep(2.0)
        self.check_files_and_switch()

    def check_files_and_switch(self):
        if os.path.exists("bridge.js"):
            self.switch_view("dash")
            if not self.settings.data.get("deployed", False):
                self.btn_start.enabled = False
        elif os.path.isdir("Belinda_AI"):
            try:
                if not os.path.abspath(os.getcwd()).endswith("Belinda_AI"):
                    os.chdir("Belinda_AI")
                self.switch_view("dash")
                if not self.settings.data.get("deployed", False):
                    self.btn_start.enabled = False
            except: self.switch_view("setup")
        else:
            self.switch_view("setup")

    def show_toast(self, text):
        self.main_window.info_dialog("Info", text)

    def toggle_theme(self, widget):
        self.settings.data["theme"] = widget.value
        self.settings.save()
        self.refresh_ui()

    def change_lang(self, widget):
        self.settings.data["language"] = widget.value
        self.settings.save()
        self.refresh_ui()

    def refresh_env_list(self):
        self.env_box.clear()
        self.env_inputs = {}
        t = DARK_THEME if self.settings.data["theme"] == "Dark" else LIGHT_THEME
        
        if not os.path.exists(".env"):
            with open(".env", "w") as f:
                f.write("GROQ_API_KEY=\nFLASK_PORT=3000\nBOT_NAME=Belinda_AI\n")
                
        if os.path.exists(".env"):
            with open(".env", "r") as f:
                for line in f:
                    if "=" in line and not line.startswith("#"):
                        k, v = line.strip().split("=", 1)
                        is_sensitive = any(word in k.upper() for word in ["KEY", "TOKEN", "SECRET", "PASS"])
                        box = toga.Box(style=Pack(direction=COLUMN, margin=5))
                        box.add(toga.Label(k, style=Pack(font_size=10, color=t['text_sec'])))
                        # PasswordInput dynamically if it's sensitive
                        if is_sensitive:
                            inp = toga.PasswordInput(value=v, style=Pack(margin_bottom=5))
                            inp.placeholder = "Enter sensitive value..."
                        else:
                            inp = toga.TextInput(value=v, style=Pack(margin_bottom=5))
                            inp.placeholder = "Enter value..."
                        box.add(inp)
                        self.env_box.add(box)
                        self.env_inputs[k] = inp
                        
        self.settings_scroll.content = self.settings_content

    def save_settings(self, widget):
        try:
            if self.env_inputs:
                lines = []
                for k, w in self.env_inputs.items():
                    val = w.value
                    lines.append(f"{k}={val}\n")
                with open(".env", "w") as f: f.writelines(lines)
    
            if getattr(self, "is_deploying_flow", False):
                self.is_deploying_flow = False
                self.lbl_status_val.text = "DEPLOYING..."
                asyncio.create_task(self.deploy_task())
                self.switch_view("dash")
                self.show_toast("Config Saved. Starting Deployment...")
            elif self.settings.data.get("deployed", False):
                self.btn_start.enabled = True
                self.show_toast(self.get_text("toast_saved"))
                self.switch_view("dash")
            else:
                self.show_toast("Saved. Run Deployment first.")
            self.settings.save()
        except Exception as e:
            self.show_toast(f"Error saving: {e}")
            _write_crash_log(f"Save Settings Error: {e}")

    def log_append(self, text):
        self.console.value += text

    def start_clone(self, widget):
        self.btn_clone.enabled = False
        self.btn_clone.text = self.get_text("status_cloning")
        asyncio.create_task(self.do_clone_task())

    async def update_clone_progress(self, percent):
        self.btn_clone.text = f"{self.get_text('status_cloning')} ({percent}%)"

    async def finish_clone(self, success, err=""):
        self.btn_clone.enabled = True
        self.btn_clone.text = self.get_text("btn_clone")
        if success:
            self.show_toast(self.get_text("toast_cloned"))
            self.show_notification("Clone Successful", "Run Full Deployment next.")
            self.check_files_and_switch()
            self.switch_view('dash')
        else:
            self.btn_clone.text = f"Error: {err}"

    async def do_clone_task(self):
        import urllib.request
        import zipfile
        import io
        import shutil
        
        target_dir = "Belinda_AI"
        repo_url = "https://github.com/Danta23/Belinda_AI/archive/refs/heads/main.zip"
        
        try:
            self.log_append("> Native Python Download Started...\n")
            
            # Streaming download with urllib, wrapped in to_thread to prevent UI freeze (ANR)
            req = await asyncio.to_thread(urllib.request.urlopen, repo_url)
            total_size = int(req.info().get('Content-Length', '5000000'))
            
            downloaded = 0
            chunk_size = 16384
            zip_buffer = io.BytesIO()
            
            while True:
                # Read chunks on a background thread
                chunk = await asyncio.to_thread(req.read, chunk_size)
                if not chunk: break
                zip_buffer.write(chunk)
                downloaded += len(chunk)
                percent = int((downloaded / total_size) * 100)
                if percent > 100: percent = 100
                self.progress_clone.value = percent
                self.btn_clone.text = f"{self.get_text('status_cloning')} ({percent}%)"
                
                # Give UI a chance to render
                await asyncio.sleep(0.005)
                
            self.log_append("> Download complete. Extracting Native ZIP...\n")
            self.btn_clone.text = "Extracting files..."
            await asyncio.sleep(0.1)
            
            # Extract in a background thread to prevent freeze
            def extract_zip():
                with zipfile.ZipFile(zip_buffer) as z:
                    z.extractall(".")
            await asyncio.to_thread(extract_zip)
                
            # Rename the extracted 'Belinda_AI-main' folder to 'Belinda_AI'
            extracted_folder = "Belinda_AI-main"
            if os.path.exists(extracted_folder):
                if os.path.exists(target_dir): shutil.rmtree(target_dir)
                os.rename(extracted_folder, target_dir)
                
            if os.path.isdir(target_dir):
                self.log_append(">>> Native ZIP clone SUCCESS! No Termux needed.\n")
                await self.finish_clone(True)
            else:
                await self.finish_clone(False, "Extracted folder not found.")
                
        except Exception as e:
            await self.finish_clone(False, str(e))

    def show_notification(self, title, message):
        # Native Notification System (No 3rd party apps required)
        # 1. Log to console for background debugging
        self.log_append(f"[{datetime.now().strftime('%H:%M:%S')}] NOTIFICATION: {title} - {message}\n")
        
        # 2. Show Visual Alert if App is Active (Foreground)
        # We use a non-blocking UI update to simulate a notification toast
        try:
            if self.main_window:
                self.main_window.info_dialog(title, message)
        except:
            pass

    def check_root_status(self):
        self.is_rooted = False

    def check_termux_and_api(self):
        return True

    # --- PROCESS MANAGEMENT (PURE PYTHON) ---
    # This removes the need for bash, sh, or Termux
    
    def handle_start(self, widget):
        if not self.settings.data.get("deployed", False):
            self.show_toast("Run Deployment first!")
            return
            
        if hasattr(self, 'bot_process') and self.bot_process:
            self.show_toast("Bot is already running!")
            return

        self.lbl_status_val.text = "STARTING..."
        self.lbl_status_val.style.color = "#FFA500" # Orange
        
        # Run app.py directly using the same Python interpreter
        try:
            self.log_append(">>> Starting Bot Process (Internal Native)...\n")
            
            # Prepare environment
            env = os.environ.copy()
            env["PYTHONUNBUFFERED"] = "1"
            
            # Use sys.executable to ensure we use the working Python
            cmd = [sys.executable, "app.py"]
            
            if os.path.exists("app.py"):
                # Popen allows running in background without freezing UI
                self.bot_process = subprocess.Popen(
                    cmd,
                    cwd=os.getcwd(),
                    env=env,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.STDOUT,
                    text=True
                )
                
                # Monitor output in background
                threading.Thread(target=self._monitor_bot_output, daemon=True).start()
                
                self.lbl_status_val.text = "ONLINE"
                self.lbl_status_val.style.color = SUCCESS_GREEN
                self.show_notification("Belinda AI", "Bot Started & Running in Background")
            else:
                self.log_append(">>> Error: app.py not found. Is deployment complete?\n")
                self.lbl_status_val.text = "ERROR"
                self.lbl_status_val.style.color = DANGER_RED
                
        except Exception as e:
            self.log_append(f">>> Start Error: {e}\n")
            self.lbl_status_val.text = "ERROR"

    def _monitor_bot_output(self):
        # Reads bot logs in real-time
        if hasattr(self, 'bot_process') and self.bot_process and self.bot_process.stdout:
            for line in self.bot_process.stdout:
                # Schedule GUI update on main thread
                # (Simple append for now, Toga usually handles this thread-safely or needs a wrapper, 
                # but direct append is safer than complex dispatch in this context)
                if line:
                    print(line.strip()) # Also print to system stdout
    
    def handle_stop(self, widget):
        self.lbl_status_val.text = "STOPPING..."
        if hasattr(self, 'bot_process') and self.bot_process:
            try:
                self.bot_process.terminate()
                self.bot_process = None
                self.log_append(">>> Bot Process Terminated.\n")
                self.lbl_status_val.text = "STOPPED"
                self.lbl_status_val.style.color = DANGER_RED
                self.show_notification("Belinda AI", "Bot Stopped Successfully")
            except Exception as e:
                self.log_append(f">>> Stop Error: {e}\n")
        else:
            self.lbl_status_val.text = "STOPPED"
            self.log_append(">>> Bot was not running.\n")

    def handle_reset(self, widget):
        # For reset, we just restart the app logic or clear vars
        self.handle_stop(widget)
        self.log_append(">>> Resetting internal state...\n")
        time.sleep(1)
        self.lbl_status_val.text = "READY"
        self.lbl_status_val.style.color = ACCENT_BLUE
        self.show_notification("Belinda AI", "System Reset Ready")

    # Removed deprecated shell monitoring methods to prevent bugs

    def handle_deploy(self, widget):
        self.is_deploying_flow = True
        self.switch_view("sett")

    async def deploy_task(self):
        self.log_append(">>> Starting Termux-Independent Deployment...\n")
        
        # 1. Environment: Native pkg hook just in case they have Termux
        if shutil.which("pkg"):
            self.log_append("> Detected Termux layer. Installing via pkg...\n")
            await asyncio.create_subprocess_shell("pkg install python nodejs-lts git -y", stdout=subprocess.DEVNULL)
        
        # 2. Native Python Packages (using App's own bundled Python)
        self.log_append("\n>>> Installing Python Dependencies...\n")
        try:
            py_bin = shutil.which("python3") or shutil.which("python")
            if py_bin:
                self.log_append(f"> Using external python: {py_bin}\n")
                pip_cmd = [py_bin, "-m", "pip", "install", "-r", "requirements.txt"]
                p1 = await asyncio.create_subprocess_exec(*pip_cmd, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.STDOUT)
                while True:
                    line = await p1.stdout.readline()
                    if not line: break
                    self.log_append(line.decode())
            else:
                self.log_append("> No external python CLI found. Attempting embedded PIP install...\n")
                try:
                    import pip
                    site_pkgs = os.path.join(self.paths.data, "site-packages")
                    if site_pkgs not in sys.path: sys.path.append(site_pkgs)
                    def run_pip():
                        try: pip.main(["install", "-r", "requirements.txt", "--target", site_pkgs])
                        except: pass
                    # Await in thread so we don't freeze UI
                    await asyncio.to_thread(run_pip)
                    self.log_append("> Embedded pip execution completed.\n")
                except ImportError:
                    self.log_append("> Pip module not bundled inside the APK. Skipping purely native python installs.\n")
                except Exception as e:
                    self.log_append(f"> Embedded pip error: {e}\n")
        except Exception as e:
            self.log_append(f"> Python dependency install failed: {e}\n")
            
        # 3. Handle Node.js missing natively on Android
        if not shutil.which("node"):
            self.log_append("\n>>> Node.js not found in PATH! Downloading Official Linux-ARM64 Node...\n")
            # Using official distribution as fallback (Note: might require glibc-compatible layer on Android)
            node_url = "https://nodejs.org/dist/v20.12.2/node-v20.12.2-linux-arm64.tar.xz"
            try:
                import urllib.request, tarfile, io
                
                def download_and_extract_node():
                    req = urllib.request.urlopen(node_url)
                    file_data = req.read()
                    # Open as .tar.xz (mode 'r:xz')
                    with tarfile.open(fileobj=io.BytesIO(file_data), mode="r:xz") as tar:
                        tar.extractall("portable_node")
                
                # Run the heavy download and extraction in a background thread
                await asyncio.to_thread(download_and_extract_node)
                
                node_bin_dir = os.path.abspath("portable_node/node-v20.12.2-linux-arm64/bin")
                if os.path.isdir(node_bin_dir):
                    # Give execution permissions to binaries (crucial for Android/Linux)
                    for bin_file in ["node", "npm", "npx"]:
                        full_path = os.path.join(node_bin_dir, bin_file)
                        if os.path.exists(full_path):
                            os.chmod(full_path, 0o755)
                    
                    os.environ["PATH"] = node_bin_dir + os.pathsep + os.environ["PATH"]
                    self.log_append(f"> Portable Node.js installed at {node_bin_dir}\n")
                else:
                    self.log_append(f"> Error: Node.js binary folder not found at {node_bin_dir}\n")
            except Exception as e:
                self.log_append(f"> Node.js download/extract failed: {e}\n")
                self.log_append("> Hint: If on Android, try installing nodejs via Termux: pkg install nodejs-lts\n")

        # 4. Node Packages
        self.log_append("\n>>> Installing NPM Packages...\n")
        try:
            # Use shell=True via create_subprocess_shell to ensure PATH is respected correctly
            p2 = await asyncio.create_subprocess_shell(
                "npm install",
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.STDOUT
            )
            while True:
                line = await p2.stdout.readline()
                if not line: break
                self.log_append(line.decode())
            await p2.wait()
        except Exception as e:
            self.log_append(f"> NPM Setup (Termux independent) error: {e}\n")
            self.log_append("> Hint: Ensure 'node' and 'npm' are executable.\n")
        
        self.log_append("\n>>> Native Deployment Successful!\n")
        self.settings.data["deployed"] = True
        self.settings.save()
        self.lbl_status_val.text = "READY"
        self.lbl_status_val.style.color = ACCENT_BLUE
        self.btn_start.enabled = True
        self.show_toast(self.get_text("toast_deploy_done"))

    async def factory_reset_task(self):
        if await self.main_window.confirm_dialog(self.get_text("pop_title"), self.get_text("pop_desc")):
            self.log_append(">>> Performing Factory Reset...\n")
            try:
                if os.path.isdir("Belinda_AI"): shutil.rmtree("Belinda_AI")
                for item in [".venv", "node_modules", "auth_info", "bridge.js", ".env", "package.json"]:
                    if os.path.isdir(item): shutil.rmtree(item)
                    elif os.path.exists(item): os.remove(item)
                self.settings.data["deployed"] = False
                self.settings.save()
                self.check_files_and_switch()
                self.show_toast("Factory Reset Complete.")
            except Exception as e:
                self.show_toast(f"Reset Error: {e}")

    def handle_factory(self, widget):
        asyncio.create_task(self.factory_reset_task())


def main():
    return BelindaApp('Belinda AI', 'id.studio234.belinda.ai')

if __name__ == '__main__':
    _write_crash_log("System: Main Entry Point Initiated")
    main().main_loop()
