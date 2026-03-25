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

# --- APP_VERSION ---
APP_VERSION = "1.4.7.2-Arch"


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
        self.on_exit = self.handle_app_exit # Register exit handler
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
        
        # Settings labels color update
        self.lbl_sett_title.style.color = t['text']
        self.settings_content.style.background_color = t['bg']
        
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
        t = DARK_THEME if self.settings.data["theme"] == "Dark" else LIGHT_THEME
        
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
            self.settings_content.clear()
            self.settings_content.add(self.lbl_sett_title)
            
            # Helper to create themed rows
            def create_sett_row(label_text, widget):
                return toga.Box(children=[
                    toga.Label(label_text, style=Pack(flex=1, color=t['text'])),
                    widget
                ], style=Pack(direction=ROW, margin=5))

            self.settings_content.add(create_sett_row("Language", self.lang_sel))
            self.settings_content.add(create_sett_row("Theme", self.theme_sel))
            self.settings_content.add(self.env_box)
            self.settings_content.add(self.btn_save_sett)
            self.refresh_env_list()
            self.container.add(self.settings_scroll)
            self.container.add(self.nav_box)

    async def delayed_startup(self):
        await asyncio.sleep(2.0)
        # 1. Pop up dialog to allow notifications
        if await self.main_window.question_dialog("Permissions", "Allow Belinda AI to send system notifications and alerts?"):
            self.show_notification("Permissions", "Notification access granted.")
        
        # 2. Check for Administrative (Root) access
        self.check_root_status()
        if self.is_rooted:
            self.log_append(">>> Administrative Access (Root) detected.\n")
            
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
        
        # Default template structure with keys and their default values
        template = [
            ("--- Flask Backend Settings ---", None),
            ("GROQ_API_KEY", ""),
            ("FLASK_PORT", "8000"),
            ("--- Bridge Settings ---", None),
            ("PYTHON_URL", "http://localhost:8000"),
            ("SESSION_NAME", "auth_info"),
            ("--- Connection Tuning ---", None),
            ("BRIDGE_HOST", "127.0.0.1"),
            ("BRIDGE_PORT", "9000")
        ]

        # Load existing values from .env if it exists
        current_values = {}
        if os.path.exists(".env"):
            try:
                with open(".env", "r") as f:
                    for line in f:
                        if "=" in line and not line.startswith("#"):
                            k, v = line.strip().split("=", 1)
                            current_values[k.strip()] = v.strip()
            except: pass

        for key, default_val in template:
            if default_val is None:
                # This is a header
                header_lbl = toga.Label(key, style=Pack(font_size=12, font_weight='bold', color=ACCENT_BLUE, margin_top=15, margin_bottom=5))
                self.env_box.add(header_lbl)
            else:
                # This is an input field
                val = current_values.get(key, default_val)
                is_sensitive = any(word in key.upper() for word in ["KEY", "TOKEN", "SECRET", "PASS"])
                
                row_box = toga.Box(style=Pack(direction=COLUMN, margin=5))
                row_box.add(toga.Label(key, style=Pack(font_size=10, color=t['text_sec'])))
                
                if is_sensitive:
                    inp = toga.PasswordInput(value=val, style=Pack(margin_bottom=5))
                    inp.placeholder = f"Enter {key}..."
                else:
                    inp = toga.TextInput(value=val, style=Pack(margin_bottom=5))
                    inp.placeholder = f"Enter {key}..."
                
                row_box.add(inp)
                self.env_box.add(row_box)
                self.env_inputs[key] = inp
                        
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
        # Check for 'su' which is the Android/Linux equivalent of sudo/administration
        self.is_rooted = False
        self.su_bin = shutil.which("su")
        if self.su_bin:
            self.is_rooted = True

    def check_termux_and_api(self):
        return True

    # --- ARCH LINUX CONTAINER LOGIC ---
    def get_arch_cmd(self, cmd_str):
        # Constructs the PRoot command to run a command inside Arch Linux
        base_path = os.path.abspath(os.getcwd())
        proot_bin = os.path.join(base_path, "proot")
        arch_root = os.path.join(base_path, "arch_linux")
        
        # PRoot arguments
        # -0: Force root user
        # -r: Rootfs path
        # -b: Bind mounts (dev, proc, sys, and project dir)
        # -w: Working directory
        proot_args = [
            proot_bin,
            "-0",
            "-r", arch_root,
            "-b", "/dev",
            "-b", "/proc",
            "-b", "/sys",
            "-b", f"{base_path}:/root/project",
            "-w", "/root/project",
            "/bin/bash", "-c", cmd_str
        ]
        
        # If rooted, wrap in SU to bypass Android 16 W^X
        if self.is_rooted:
            # Join args for shell execution
            flat_cmd = " ".join([f"'{a}'" for a in proot_args])
            return ["su", "-c", flat_cmd]
        
        return proot_args

    async def run_arch_container(self, cmd, background=False):
        # Helper to run commands inside the container
        full_cmd = self.get_arch_cmd(cmd)
        
        if background:
            # For long running processes (Start Bot)
            return subprocess.Popen(
                full_cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                cwd=os.getcwd(),
                env=os.environ.copy()
            )
        else:
            # For one-off commands (Deployment)
            if self.is_rooted:
                # Use shell for SU
                flat_cmd = " ".join(full_cmd) if isinstance(full_cmd, list) else full_cmd
                return await asyncio.create_subprocess_shell(
                    flat_cmd,
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.STDOUT
                )
            else:
                # Direct execution
                return await asyncio.create_subprocess_exec(
                    *full_cmd,
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.STDOUT
                )

    def handle_start(self, widget):
        if not self.settings.data.get("deployed", False):
            self.show_toast("Run Deployment first!")
            return
            
        if hasattr(self, 'bot_process') and self.bot_process and self.bot_process.poll() is None:
            self.show_toast("Bot is already running!")
            return

        self.lbl_status_val.text = "STARTING..."
        self.lbl_status_val.style.color = "#FFA500" # Orange
        
        # Run app.py INSIDE the Arch Linux Container
        try:
            # Check if Belinda_AI is ready
            if not os.path.exists("proot") or not os.path.isdir("arch_linux"):
                self.log_append(">>> Belinda_AI components not found. Please run Full Deployment.\n")
                self.lbl_status_val.text = "DEPLOY FIRST"
                return

            self.log_append(">>> Starting Bot Process (Inside Belinda_AI/Arch)...\n")
            
            # The command to run python from within the Arch environment
            cmd = "python /root/project/app.py"
            cmd_list = self.get_arch_cmd(cmd)
            
            # Use Popen for non-blocking background execution
            self.bot_process = subprocess.Popen(
                cmd_list,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                cwd=os.getcwd(),
                env=os.environ.copy()
            )
            
            # Monitor output in background thread
            threading.Thread(target=self._monitor_bot_output, daemon=True).start()
            
            self.lbl_status_val.text = "ONLINE"
            self.lbl_status_val.style.color = SUCCESS_GREEN
            self.show_notification("Belinda AI", "Bot Started & Running in Virtual Environment")
                
        except Exception as e:
            self.log_append(f">>> Start Error: {traceback.format_exc()}\n")
            self.lbl_status_val.text = "ERROR"
            self.lbl_status_val.style.color = DANGER_RED

    def _monitor_bot_output(self):
        # Reads bot logs in real-time and appends to the UI console
        if hasattr(self, 'bot_process') and self.bot_process and self.bot_process.stdout:
            try:
                for line in self.bot_process.stdout:
                    if line:
                        # Schedule UI update on main thread for stability
                        self.add_background_task(self._async_log_append(line))
            except Exception as e:
                self.add_background_task(self._async_log_append(f">>> Log Monitor Error: {e}\n"))

    async def _async_log_append(self, text):
        self.log_append(text)

    def handle_app_exit(self, widget):
        # Cleanup process when app closes
        if hasattr(self, 'bot_process') and self.bot_process:
            try:
                self.bot_process.terminate()
            except: pass
        return True
    
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
        # This is the core of the "Belinda_AI" engine
        import urllib.request
        import tarfile
        import io
        import stat

        PROOT_URL = "https://github.com/proot-me/proot/releases/download/v5.3.0/proot-v5.3.0-aarch64-static"
        ARCH_URL = "http://os.archlinuxarm.org/os/ArchLinuxARM-aarch64-latest.tar.gz"
        PROOT_BIN = "proot"
        ARCH_ROOT = "arch_linux"

        self.log_append(">>> Initializing Belinda_AI (Arch Linux Engine)...\n")
        
        try:
            # --- Phase 1: Setup PRoot (The Virtual Engine) ---
            if not os.path.exists(PROOT_BIN):
                self.log_append("> Downloading PRoot Engine...\n")
                await asyncio.to_thread(urllib.request.urlretrieve, PROOT_URL, PROOT_BIN)
                # Set executable permissions
                os.chmod(PROOT_BIN, stat.S_IRWXU)
            else:
                self.log_append("> PRoot Engine already exists.\n")

            # --- Phase 2: Setup Arch Linux Root Filesystem (The OS) ---
            if not os.path.isdir(ARCH_ROOT):
                self.log_append(f"> Downloading Arch Linux ARM (~200MB)... Please be patient.\n")
                
                def download_and_extract():
                    with urllib.request.urlopen(ARCH_URL) as response:
                        with tarfile.open(fileobj=io.BytesIO(response.read()), mode="r:gz") as tar:
                            tar.extractall(ARCH_ROOT)
                
                await asyncio.to_thread(download_and_extract)
                self.log_append("> Arch Linux System Extracted.\n")
                
                # --- Phase 2a: Configure Arch Environment ---
                # Fix DNS for pacman
                resolv_path = os.path.join(ARCH_ROOT, "etc", "resolv.conf")
                with open(resolv_path, "w") as f:
                    f.write("nameserver 8.8.8.8\nnameserver 8.8.4.4\n")

                # Disable pacman signature checks for simplicity and reliability
                pacman_conf_path = os.path.join(ARCH_ROOT, "etc", "pacman.conf")
                with open(pacman_conf_path, "r") as f: content = f.read()
                content = content.replace("SigLevel    = Required DatabaseOptional", "SigLevel = Never")
                with open(pacman_conf_path, "w") as f: f.write(content)
            else:
                 self.log_append("> Arch Linux environment already exists.\n")

            # --- Phase 3: Install Dependencies via Pacman ---
            self.log_append("\n>>> [pacman] Initializing and Installing Dependencies...\n")
            # Update keyring and install core packages
            install_cmd = "pacman-key --init && pacman-key --populate archlinuxarm && pacman -Syu --noconfirm python python-pip nodejs npm git make gcc"
            proc = await self.run_arch_container(install_cmd)
            while True:
                line = await proc.stdout.readline()
                if not line: break
                self.log_append(f"[pacman] {line.decode()}")
            await proc.wait()

            # --- Phase 4: Install Python Requirements (Inside Arch) ---
            self.log_append("\n>>> [pip] Installing Python Libraries...\n")
            pip_cmd = "pip install -r requirements.txt --break-system-packages"
            proc = await self.run_arch_container(pip_cmd)
            while True:
                line = await proc.stdout.readline()
                if not line: break
                self.log_append(f"[pip] {line.decode()}")
            await proc.wait()

            # --- Phase 5: Install NPM Packages (Inside Arch) ---
            self.log_append("\n>>> [npm] Installing Node.js Packages...\n")
            npm_cmd = "npm install"
            proc = await self.run_arch_container(npm_cmd)
            while True:
                line = await proc.stdout.readline()
                if not line: break
                self.log_append(f"[npm] {line.decode()}")
            await proc.wait()

            # --- Deployment Complete ---
            self.log_append("\n>>> Belinda_AI Ready! Deployment Successful.\n")
            self.settings.data["deployed"] = True
            self.settings.save()
            self.lbl_status_val.text = "READY"
            self.lbl_status_val.style.color = ACCENT_BLUE
            self.btn_start.enabled = True
            self.show_toast("Deployment Complete. Ready to Start Bot.")

        except PermissionError:
            self.log_append("\n>>> FATAL: ANDROID SECURITY BLOCK <<<\n")
            self.log_append("The PRoot engine was blocked by Android's security policy (W^X).\n")
            self.log_append("Solution: \n1. Use a ROOTED device and grant SU access.\n2. On non-root, this feature cannot run on Android 10+.\n")
        except Exception as e:
            self.log_append(f"> Deployment Error: {traceback.format_exc()}\n")
            self.lbl_status_val.text = "DEPLOY FAILED"
            self.lbl_status_val.style.color = DANGER_RED
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
