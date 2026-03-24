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
APP_VERSION = "1.4.7.2-5"

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
        self.settings = SettingsManager(self)
        self.main_window = toga.MainWindow(title="Belinda AI Manager", size=(400, 700))
        self.container = toga.Box(style=Pack(direction=COLUMN))
        
        # Dashboard Components
        self.status_box = toga.Box(style=Pack(direction=COLUMN, margin=10))
        self.lbl_sys_status = toga.Label("SYSTEM STATUS", style=Pack(font_size=10))
        self.lbl_status_val = toga.Label("READY", style=Pack(font_size=20, font_weight='bold'))
        self.status_box.add(self.lbl_sys_status)
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
        
        self.btn_deploy.text = self.get_text("btn_deploy")
        self.btn_start.text = self.get_text("btn_start")
        self.btn_stop.text = self.get_text("btn_stop")
        self.btn_reset.text = self.get_text("btn_reset")
        self.btn_factory.text = self.get_text("btn_factory")
        self.btn_nav_dash.text = self.get_text("nav_dash")
        self.btn_nav_sett.text = self.get_text("nav_sett")

    def switch_view(self, view_name):
        self.container.clear()
        if view_name == "splash":
            splash = toga.Box(style=Pack(direction=COLUMN, flex=1, alignment=CENTER, justify_content=CENTER))
            splash.add(toga.Label("BELINDA AI", style=Pack(font_size=40, font_weight='bold', color=ACCENT_BLUE)))
            splash.add(toga.Label(random.choice(TAGLINES), style=Pack(font_size=14, color="#AAAAAA", margin_top=10)))
            splash.add(toga.Label(f"v{APP_VERSION}", style=Pack(font_size=10, color="#888888", margin_top=20)))
            self.container.add(splash)
        elif view_name == "setup":
            t = DARK_THEME if self.settings.data["theme"] == "Dark" else LIGHT_THEME
            setup = toga.Box(style=Pack(direction=COLUMN, margin=30))
            setup.add(toga.Label(self.get_text("title_setup"), style=Pack(font_size=24, font_weight='bold', color=t['text'])))
            setup.add(toga.Label(self.get_text("desc_setup"), style=Pack(margin_top=20, color=t['text_sec'])))
            self.btn_clone = toga.Button(self.get_text("btn_clone"), on_press=self.start_clone, style=Pack(margin_top=40, font_size=16, background_color=ACCENT_BLUE, color="#FFFFFF"))
            setup.add(self.btn_clone)
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

    def show_notification(self, title, message):
        try:
            subprocess.run(["termux-notification", "-t", title, "-c", message, "--id", "belinda_ai_msg"], capture_output=True)
        except:
            pass

    def check_root_status(self):
        self.is_rooted = False
        self.root_cmd = None
        for cmd in ['tsu', 'su']:
            if shutil.which(cmd):
                self.is_rooted = True
                self.root_cmd = cmd
                break

    def check_termux_and_api(self):
        is_termux = os.path.isdir("/data/data/com.termux")
        if not is_termux:
            self.show_toast("Termux not found! Please install it.")
            return False
        is_api = False
        try:
            res = subprocess.run(["pm", "list", "packages", "com.termux.api"], capture_output=True, text=True)
            if "com.termux.api" in res.stdout: is_api = True
        except: pass
        if not is_api:
            self.show_toast("Termux:API missing! Please install from GitHub")
            webbrowser.open("https://github.com/termux/termux-api/releases")
            return False
        self.show_notification("System Ready", "Termux API is available.")
        return True

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
        if self.env_inputs:
            lines = []
            for k, w in self.env_inputs.items():
                val = w.value
                lines.append(f"{k}={val}\n")
            with open(".env", "w") as f: f.writelines(lines)

        if self.settings.data.get("deployed", False):
            self.btn_start.enabled = True
            self.show_toast(self.get_text("toast_saved"))
            self.switch_view("dash")
        else:
            self.show_toast("Saved. Run Deployment first.")
        self.settings.save()

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
        if not self.check_termux_and_api(): return
        repo_url = "https://github.com/Danta23/Belinda_AI.git"
        target_dir = "Belinda_AI"

        try:
            git_path = shutil.which('git')
            if git_path:
                self.log_append("> Found git. Running direct clone...\n")
                process = await asyncio.create_subprocess_exec(
                    git_path, "clone", repo_url, target_dir,
                    stdout=subprocess.PIPE, stderr=subprocess.STDOUT
                )
                while True:
                    line = await process.stdout.readline()
                    if not line: break
                    text = line.decode()
                    self.log_append(text)
                    if "%" in text:
                        try:
                            parts = text.split('%')[0].split()
                            if parts:
                                percent = int(parts[-1])
                                await self.update_clone_progress(percent)
                        except: pass
                await process.wait()
                if process.returncode == 0 and os.path.isdir(target_dir):
                    await self.finish_clone(True)
                    return

            if os.path.exists('/system/bin/am'):
                self.log_append("> Using Android Termux:API Intent...\n")
                full_cmd = f"pkg install git -y && git clone {repo_url} {target_dir}"
                am_cmd = [
                    "am", "startservice", "--user", "0",
                    "-n", "com.termux/.app.TermuxService",
                    "-e", "com.termux.execute.background", "true",
                    "-e", "com.termux.execute.command", full_cmd
                ]
                subprocess.run(am_cmd, capture_output=True)
                for i in range(90):
                    await self.update_clone_progress(int((i/90)*100))
                    if os.path.isdir(target_dir) and os.path.exists(os.path.join(target_dir, "bridge.js")):
                        self.log_append(">>> Folder detected! Termux clone SUCCESS.\n")
                        await self.finish_clone(True)
                        return
                    await asyncio.sleep(1)

            if self.root_cmd:
                self.log_append("> Attempting forced clone via ROOT...\n")
                subprocess.run(f"{self.root_cmd} 'pkg install git -y && git clone {repo_url} {target_dir}'", shell=True)
                if os.path.isdir(target_dir):
                    await self.finish_clone(True)
                    return
            
            os.system(f"git clone {repo_url} {target_dir}")
            if os.path.isdir(target_dir):
                await self.finish_clone(True)
                return

            await self.finish_clone(False, "Clone Failed.")
        except Exception as e:
            await self.finish_clone(False, str(e))

    async def run_cmd_async(self, cmd, task_name="command"):
        self.log_append(f">>> Executing {cmd}...\n")
        process = await asyncio.create_subprocess_shell(
            f"bash {cmd}",
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.STDOUT
        )
        while True:
            line = await process.stdout.readline()
            if not line: break
            self.log_append(line.decode())
        await process.wait()
        self.log_append(f">>> Task {task_name} finished with code {process.returncode}\n")
        return process.returncode == 0

    def handle_start(self, widget):
        if not self.settings.data.get("deployed", False):
            self.show_toast("Run Deployment first!")
            return
        cmd = 'start_termux.sh' if os.path.exists('start_termux.sh') else 'start.sh'
        self.lbl_status_val.text = "WORKING..."
        asyncio.create_task(self._monitor_cmd(cmd, "start", success_str="ONLINE"))

    def handle_stop(self, widget):
        cmd = 'stop_termux.sh' if os.path.exists('stop_termux.sh') else 'stop.sh'
        self.lbl_status_val.text = "WORKING..."
        asyncio.create_task(self._monitor_cmd(cmd, "stop", success_str="STOPPED"))

    def handle_reset(self, widget):
        cmd = 'reset_termux.sh' if os.path.exists('reset_termux.sh') else 'reset.sh'
        self.lbl_status_val.text = "WORKING..."
        asyncio.create_task(self._monitor_cmd(cmd, "reset", success_str="READY"))

    async def _monitor_cmd(self, cmd, task_name, success_str):
        ok = await self.run_cmd_async(cmd, task_name)
        if ok: 
            self.lbl_status_val.text = success_str
            self.lbl_status_val.style.color = SUCCESS_GREEN
        else:
            self.lbl_status_val.text = "STOPPED"
            self.lbl_status_val.style.color = DANGER_RED

    def handle_deploy(self, widget):
        self.lbl_status_val.text = "DEPLOYING..."
        asyncio.create_task(self.deploy_task())

    async def deploy_task(self):
        self.log_append(">>> Starting Full Deployment...\n")
        
        # 1. Environment
        self.log_append("installing dependencies...\n")
        await asyncio.create_subprocess_shell("pkg install python nodejs-lts git -y", stdout=subprocess.DEVNULL)
        await asyncio.create_subprocess_shell("python3 -m venv .venv")
        
        pip_cmd = ".venv/bin/pip" if os.name != 'nt' else ".venv\\Scripts\\pip"
        
        # 2. Python Packages
        p1 = await asyncio.create_subprocess_shell(f"{pip_cmd} install -r requirements.txt", stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.STDOUT)
        while True:
            line = await p1.stdout.readline()
            if not line: break
            self.log_append(line.decode())
        
        # 3. Node Packages
        p2 = await asyncio.create_subprocess_shell("npm install", stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.STDOUT)
        while True:
            line = await p2.stdout.readline()
            if not line: break
            self.log_append(line.decode())
        
        self.log_append("\n>>> Deployment Successful!\n")
        self.settings.data["deployed"] = True
        self.settings.save()
        self.lbl_status_val.text = "READY"
        self.lbl_status_val.style.color = ACCENT_BLUE
        self.show_toast(self.get_text("toast_deploy_done"))
        self.switch_view("sett")

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
