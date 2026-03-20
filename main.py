import os
import sys
import threading
import subprocess
import time
import json
import traceback
import shutil
import webbrowser
from datetime import datetime

# --- APP VERSION ---
APP_VERSION = "1.0.0-4"

# --- GLOBAL EXCEPTION HANDLER ---
def global_exception_handler(exc_type, exc_value, exc_traceback):
    if issubclass(exc_type, KeyboardInterrupt):
        sys.__excepthook__(exc_type, exc_value, exc_traceback)
        return
    
    error_details = "".join(traceback.format_exception(exc_type, exc_value, exc_traceback))
    log_file = "termux_error.log"
    
    # Save to file
    try:
        with open(log_file, "a") as f:
            f.write(f"\n[{datetime.now()}] CRITICAL ERROR:\n{error_details}\n")
    except: pass
    
    # Notify via Termux if possible
    try:
        subprocess.run(["termux-notification", "-t", "Belinda AI Error", "-c", str(exc_value), "--priority", "high"], capture_output=True)
    except: pass
    
    # Show internal toast if app is running
    app = App.get_running_app()
    if app:
        try: Clock.schedule_once(lambda dt: app.show_toast("Error logged to termux_error.log"), 0)
        except: pass

sys.excepthook = global_exception_handler

# --- FORCED LOG REDIRECTION (Android Only) ---
if 'ANDROID_ARGUMENT' in os.environ:
    sys.stdout = open('android_stdout.log', 'w')
    sys.stderr = open('android_stderr.log', 'w')

# Kivy Imports
try:
    from kivy.app import App
    from kivy.core.window import Window
    from kivy.uix.boxlayout import BoxLayout
    from kivy.uix.floatlayout import FloatLayout
    from kivy.uix.gridlayout import GridLayout
    from kivy.uix.button import Button
    from kivy.uix.label import Label
    from kivy.uix.textinput import TextInput
    from kivy.uix.scrollview import ScrollView
    from kivy.uix.screenmanager import ScreenManager, Screen, FadeTransition
    from kivy.uix.widget import Widget
    from kivy.graphics import Color, RoundedRectangle, Line, Rectangle
    from kivy.clock import Clock
    from kivy.animation import Animation
    from kivy.metrics import dp
    from kivy.utils import get_color_from_hex
    from kivy.properties import StringProperty, ListProperty, NumericProperty, BooleanProperty, ObjectProperty
except ImportError:
    print("CRITICAL: Kivy is not installed. Please run 'pip install kivy'.")
    sys.exit(1)

import random

# --- CONFIG & CONSTANTS ---
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

# --- THEMES ---
DARK_THEME = {
    "bg": get_color_from_hex('#0F0F14'),
    "card": (0.1, 0.1, 0.2, 0.6),
    "border": (0.4, 0.6, 1.0, 0.3),
    "text": (1, 1, 1, 1),
    "text_sec": (1, 1, 1, 0.6),
    "input_bg": (0, 0, 0, 0.4),
    "console_text": (0, 1, 0, 1)
}
LIGHT_THEME = {
    "bg": get_color_from_hex('#F8F9FA'),
    "card": (1, 1, 1, 0.95),
    "border": (0, 0, 0, 0.1),
    "text": (0, 0, 0, 0.95),
    "text_sec": (0.1, 0.1, 0.1, 0.7),
    "input_bg": (0, 0, 0, 0.08),
    "console_text": (0, 0, 0, 0.9)
}

# --- UTILS ---
from kivy.uix.popup import Popup

class LiquidPopup(Popup):
    def __init__(self, title_text, desc_text, on_yes, **kwargs):
        super().__init__(**kwargs)
        self.title = title_text
        self.size_hint = (0.85, 0.4)
        self.separator_color = [0.2, 0.8, 1, 1]
        self.background = ""
        
        content = BoxLayout(orientation='vertical', padding=dp(20), spacing=dp(15))
        with content.canvas.before:
            Color(0.1, 0.1, 0.15, 0.95)
            RoundedRectangle(pos=content.pos, size=content.size, radius=[dp(20)])
        
        lbl = Label(text=desc_text, halign='center', font_size='14sp')
        lbl.bind(size=lbl.setter('text_size'))
        
        btns = BoxLayout(size_hint_y=None, height=dp(50), spacing=dp(10))
        btn_no = LiquidButton(text=App.get_running_app().get_text("btn_no"), bg_color=[0.4, 0.4, 0.4, 1])
        btn_no.bind(on_release=self.dismiss)
        
        btn_yes = LiquidButton(text=App.get_running_app().get_text("btn_yes"), bg_color=[1, 0.2, 0.2, 1])
        btn_yes.bind(on_release=lambda x: [on_yes(), self.dismiss()])
        
        btns.add_widget(btn_no)
        btns.add_widget(btn_yes)
        content.add_widget(lbl)
        content.add_widget(btns)
        self.content = content

class SettingsManager:
    def __init__(self):
        self.file = "mobile_settings.json"
        self.data = self.load()

    def load(self):
        if os.path.exists(self.file):
            try:
                with open(self.file, 'r') as f: return json.load(f)
            except: pass
        return {"language": "English", "theme": "Dark", "deployed": False}

    def save(self):
        with open(self.file, 'w') as f: json.dump(self.data, f)

# --- CUSTOM UI WIDGETS ---
class LiquidBackground(Widget):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        with self.canvas:
            self.bg_color = Color(rgba=DARK_THEME["bg"])
            self.rect = Rectangle(pos=self.pos, size=self.size)
            self.orb1_color = Color(0.2, 0.1, 0.4, 0.2)
            self.orb1 = RoundedRectangle(pos=(0, 0), size=(dp(300), dp(300)), radius=[dp(150)])
            self.orb2_color = Color(0.1, 0.3, 0.4, 0.15)
            self.orb2 = RoundedRectangle(pos=(dp(200), dp(400)), size=(dp(400), dp(400)), radius=[dp(200)])
        self.bind(pos=self.update_rect, size=self.update_rect)
        self.animate_orbs()

    def update_rect(self, *args):
        self.rect.pos = self.pos
        self.rect.size = self.size

    def animate_orbs(self):
        anim1 = Animation(pos=(dp(50), dp(100)), duration=10, t='in_out_sine') + \
                Animation(pos=(dp(-50), dp(-50)), duration=10, t='in_out_sine')
        anim1.repeat = True
        anim1.start(self.orb1)
        anim2 = Animation(pos=(dp(100), dp(200)), duration=15, t='in_out_sine') + \
                Animation(pos=(dp(300), dp(500)), duration=15, t='in_out_sine')
        anim2.repeat = True
        anim2.start(self.orb2)

class LiquidCard(BoxLayout):
    radius = ListProperty([dp(20)])
    def __init__(self, **kwargs):
        if 'radius' in kwargs:
            self.radius = kwargs.pop('radius')
        super().__init__(**kwargs)
        self.padding = dp(15)
        self.background_color = (0,0,0,0)
        with self.canvas.before:
            self.color_node = Color(0,0,0,0)
            self.rect = RoundedRectangle(pos=self.pos, size=self.size, radius=self.radius)
            self.line_color = Color(0,0,0,0)
            self.border = Line(rounded_rectangle=(self.x, self.y, self.width, self.height, self.radius[0]), width=1.1)
        self.bind(pos=self.update_rect, size=self.update_rect)

    def update_rect(self, *args):
        self.rect.pos = self.pos
        self.rect.size = self.size
        self.rect.radius = self.radius
        self.border.rounded_rectangle = (self.x, self.y, self.width, self.height, self.radius[0])

class LiquidButton(Button):
    bg_color = ListProperty([0.2, 0.7, 1, 1])
    radius = ListProperty([dp(12)])
    def __init__(self, **kwargs):
        if 'radius' in kwargs:
            self.radius = kwargs.pop('radius')
        super().__init__(**kwargs)
        self.background_normal = ''
        self.background_down = ''
        self.background_color = (0,0,0,0)
        self.bold = True
        with self.canvas.before:
            self.btn_color = Color(*self.bg_color)
            self.btn_rect = RoundedRectangle(pos=self.pos, size=self.size, radius=self.radius)
        self.bind(pos=self.update_btn, size=self.update_btn)

    def update_btn(self, *args):
        self.btn_rect.pos = self.pos
        self.btn_rect.size = self.size
        self.btn_rect.radius = self.radius

# --- WORKER THREAD ---
class TaskWorker(threading.Thread):
    def __init__(self, task, callback_log, callback_done):
        super().__init__()
        self.task = task
        self._log = callback_log
        self.callback_done = callback_done
        self.daemon = True

    def callback_log(self, text):
        Clock.schedule_once(lambda dt: self._log(text))

    def run(self):
        try:
            if self.task == 'session':
                self.callback_log(">>> Wiping session folder...\n")
                if os.path.exists("auth_info"): shutil.rmtree("auth_info")
                self.callback_log(">>> Session wiped. Restart bot.\n")
                self.callback_done(True)
                return
            
            if self.task == 'deploy':
                self.run_deployment()
                return

            script_map = {
                'start': 'start_termux.sh' if os.path.exists('start_termux.sh') else 'start.sh',
                'stop': 'stop_termux.sh' if os.path.exists('stop_termux.sh') else 'stop.sh',
                'reset': 'reset_termux.sh' if os.path.exists('reset_termux.sh') else 'reset.sh'
            }
            cmd = script_map.get(self.task)
            if not cmd:
                self.callback_log(f"Unknown task: {self.task}\n")
                self.callback_done(False)
                return
            try: subprocess.run(['chmod', '+x', cmd])
            except: pass
            self.callback_log(f">>> Executing {cmd}...\n")
            process = subprocess.Popen(['bash', cmd], stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, bufsize=1, universal_newlines=True)
            for line in process.stdout:
                if line: self.callback_log(line)
            process.wait()
            self.callback_log(f">>> Task {self.task} finished with code {process.returncode}\n")
            self.callback_done(process.returncode == 0)
        except Exception as e:
            self.callback_log(f"CRITICAL ERROR: {str(e)}\n")
            self.callback_done(False)

    def run_deployment(self):
        self.callback_log(">>> Starting Full Deployment...\n")
        try:
            subprocess.run(["pkg", "install", "python", "nodejs-lts", "git", "-y"], check=False)
            subprocess.run([sys.executable, "-m", "venv", ".venv"], check=True)
            pip_cmd = ".venv/bin/pip" if os.name != 'nt' else ".venv\\Scripts\\pip"
            subprocess.run([pip_cmd, "install", "-r", "requirements.txt"], check=True)
            subprocess.run(["npm", "install"], check=True)
            self.callback_log(">>> Deployment Successful!\n")
            self.callback_done(True)
        except Exception as e:
            self.callback_log(f"Error during deployment: {e}\n")
            self.callback_done(False)

# --- SCREENS ---
class SplashScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.layout = FloatLayout()
        self.logo_label = Label(text="BELINDA AI", font_size='42sp', bold=True, color=(1,1,1,0), pos_hint={'center_x': 0.5, 'center_y': 0.55})
        tagline = random.choice(TAGLINES)
        self.sub_label = Label(text=tagline, font_size='14sp', color=(1,1,1,0), pos_hint={'center_x': 0.5, 'center_y': 0.45})
        self.ver_label = Label(text=f"v{APP_VERSION}", font_size='12sp', color=(1,1,1,0), pos_hint={'center_x': 0.5, 'y': 0.08})
        self.layout.add_widget(self.logo_label)
        self.layout.add_widget(self.sub_label)
        self.layout.add_widget(self.ver_label)
        self.add_widget(self.layout)

    def on_enter(self):
        anim = Animation(color=(1,1,1,1), pos_hint={'center_y': 0.5}, duration=1.5, t='out_back')
        anim.start(self.logo_label)
        anim_sub = Animation(color=(1,1,1,0.6), duration=2)
        anim_sub.start(self.sub_label)
        anim_ver = Animation(color=(1,1,1,0.85), duration=2)
        anim_ver.start(self.ver_label)
        Clock.schedule_once(lambda dt: App.get_running_app().check_files_and_switch(), 3.5)

class SetupScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.layout = BoxLayout(orientation='vertical', padding=dp(30), spacing=dp(20))
        self.lbl_title = Label(text="INITIAL SETUP", font_size='24sp', bold=True, size_hint_y=None, height=dp(50))
        self.lbl_desc = Label(text="Files not found.", halign='center', size_hint_y=None, height=dp(100))
        self.lbl_desc.bind(size=self.lbl_desc.setter('text_size'))
        self.btn_clone = LiquidButton(text="CLONE PROJECT", size_hint_y=None, height=dp(55))
        self.btn_clone.bind(on_release=self.start_clone)
        self.layout.add_widget(Widget())
        self.layout.add_widget(self.lbl_title)
        self.layout.add_widget(self.lbl_desc)
        self.layout.add_widget(self.btn_clone)
        self.layout.add_widget(Widget())
        self.add_widget(self.layout)

    def start_clone(self, instance):
        self.btn_clone.disabled = True
        self.btn_clone.text = App.get_running_app().get_text("status_cloning")
        threading.Thread(target=self.do_clone, daemon=True).start()

    def do_clone(self):
        app = App.get_running_app()
        # Verify Termux & API first
        if not app.check_termux_and_api():
            return
            
        # Ensure log_callback points to the correct console, with a fallback
        log_callback = app.dash.update_log if hasattr(app, 'dash') else (lambda x: print(f"[CLONE LOG] {x}"))
        
        def safe_log(text):
            Clock.schedule_once(lambda dt: log_callback(text), 0)

        try:
            repo_url = "https://github.com/Danta23/Belinda_AI.git"
            target_dir = "Belinda_AI"

            # 1. Try Direct Git Clone (Best for Desktop or Termux Python shell)
            git_path = shutil.which('git')
            if git_path:
                safe_log(f"> Found git at {git_path}. Running direct clone...\n")
                process = subprocess.Popen(
                    [git_path, "clone", repo_url, target_dir],
                    stdout=subprocess.PIPE,
                    stderr=subprocess.STDOUT,
                    text=True,
                    bufsize=1,
                    universal_newlines=True
                )
                
                for line in process.stdout:
                    if line:
                        safe_log(line)
                        if "%" in line: # Simple progress detection
                            try:
                                parts = line.split('%')[0].split()
                                if parts:
                                    percent = int(parts[-1])
                                    Clock.schedule_once(lambda dt, p=percent: self.update_clone_progress(p), 0)
                            except: pass
                
                process.wait()
                if process.returncode == 0 and os.path.isdir(target_dir):
                    safe_log(">>> Direct Git clone successful!\n")
                    Clock.schedule_once(lambda dt: self.finish_clone(True), 0)
                    return
                else:
                    safe_log(f"! Direct Git clone failed (Code {process.returncode}). Trying alternatives...\n")

            # 2. Try Termux:API (Specific for Android background execution)
            if os.path.exists('/system/bin/am'):
                safe_log("> Detected Android environment. Using Termux:API Intent...\n")
                
                # We use a combined command to install git if missing AND clone
                # Using single quotes for the command string to avoid shell expansion issues
                full_cmd = f"pkg install git -y && git clone {repo_url} {target_dir}"
                am_cmd = [
                    "am", "startservice", "--user", "0",
                    "-n", "com.termux/.app.TermuxService", # Try direct service first
                    "-e", "com.termux.execute.background", "true",
                    "-e", "com.termux.execute.command", full_cmd
                ]
                
                # Alternative Intent for newer Termux:API versions
                am_cmd_v2 = [
                    "am", "startservice", "--user", "0",
                    "-n", "com.termux.service_execute",
                    "-e", "command", full_cmd
                ]

                try:
                    subprocess.run(am_cmd_v2, capture_output=True)
                    safe_log("> Dispatched command to Termux Service. Polling for directory...\n")
                except Exception as e:
                    safe_log(f"! Failed to send Termux intent: {e}. Trying legacy intent...\n")
                    subprocess.run(am_cmd, capture_output=True)

                # Polling for success
                for i in range(90): # 90 seconds timeout
                    progress = int((i / 90) * 100)
                    Clock.schedule_once(lambda dt, p=progress: self.update_clone_progress(p), 0)
                    if os.path.isdir(target_dir) and os.path.exists(os.path.join(target_dir, "bridge.js")):
                        safe_log(">>> Folder detected! Clone SUCCESS via Termux background.\n")
                        Clock.schedule_once(lambda dt: self.finish_clone(True), 0)
                        return
                    time.sleep(1)

            # 3. Try Root/Sudo Fallback (For rooted devices)
            safe_log("> Checking for root (su/tsu) fallback...\n")
            root_cmd = None
            if shutil.which('tsu'): root_cmd = 'tsu -c'
            elif shutil.which('su'): root_cmd = 'su -c'
            
            if root_cmd:
                safe_log(f"> Root access found ({root_cmd.split()[0]}). Attempting forced clone...\n")
                try:
                    # Attempt via root shell
                    full_root_cmd = f"{root_cmd} 'pkg install git -y && git clone {repo_url} {target_dir}'"
                    subprocess.run(full_root_cmd, shell=True, capture_output=True)
                    if os.path.isdir(target_dir):
                        safe_log(">>> Root-forced clone SUCCESS!\n")
                        Clock.schedule_once(lambda dt: self.finish_clone(True), 0)
                        return
                except Exception as e:
                    safe_log(f"! Root clone attempt failed: {e}\n")

            # 4. Final Alternative: Using raw shell commands if possible
            safe_log("> Attempting standard shell clone fallback...\n")
            try:
                os.system(f"git clone {repo_url} {target_dir}")
                if os.path.isdir(target_dir):
                    Clock.schedule_once(lambda dt: self.finish_clone(True), 0)
                    return
            except: pass

            Clock.schedule_once(lambda dt: self.finish_clone(False, "Clone failed. Please ensure Git is installed in Termux and Termux:API is working."), 0)

        except Exception as e:
            traceback.print_exc()
            safe_log(f"CRITICAL ERROR: {str(e)}\n")
            Clock.schedule_once(lambda dt: self.finish_clone(False, f"Crash: {str(e)}"), 0)
            
    def update_clone_progress(self, percentage):
        app = App.get_running_app()
        self.btn_clone.text = f"{app.get_text('status_cloning')} ({percentage}%)"

    def finish_clone(self, success, err=""):
        app = App.get_running_app()
        self.btn_clone.disabled = False
        self.btn_clone.text = app.get_text("btn_clone")
        if success:
            app.show_toast(app.get_text("toast_cloned"))
            app.show_notification("Clone Successful", "Cloning complete. Please click FULL DEPLOYMENT to install dependencies.")
            app.check_files_and_switch()
            # Automatically switch to Dashboard menu
            Clock.schedule_once(lambda dt: app.switch_tab('dash'), 0.5)
        else: self.lbl_desc.text = f"Error: {err}"

class DashboardScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.main = BoxLayout(orientation='vertical', padding=dp(20), spacing=dp(15))
        
        self.card = LiquidCard(orientation='vertical', size_hint_y=None, height=dp(90))
        self.lbl_sys = Label(text="SYSTEM STATUS", font_size='11sp')
        self.lbl_status = Label(text="READY", font_size='22sp', bold=True)
        self.card.add_widget(self.lbl_sys)
        self.card.add_widget(self.lbl_status)
        
        self.console_card = LiquidCard(radius=[dp(15)])
        self.console = TextInput(readonly=True, background_color=(0,0,0,0), foreground_color=(0,1,0,1), font_size='10sp')
        self.console_card.add_widget(self.console)
        
        # New Structured Buttons Layout
        controls = BoxLayout(orientation='vertical', spacing=dp(10), size_hint_y=None, height=dp(170))
        self.btn_grid = GridLayout(cols=2, spacing=dp(10))
        
        self.btn_start = LiquidButton(text="START BOT")
        self.btn_start.bind(on_release=lambda x: App.get_running_app().run_task('start'))
        
        self.btn_stop = LiquidButton(text="STOP BOT", bg_color=[1,0.3,0.3,1])
        self.btn_stop.bind(on_release=lambda x: App.get_running_app().run_task('stop'))
        
        self.btn_reset = LiquidButton(text="RESET BOT", bg_color=[0.5,0.2,0.8,1])
        self.btn_reset.bind(on_release=lambda x: App.get_running_app().run_task('reset'))
        
        self.btn_factory = LiquidButton(text="FACTORY RESET", bg_color=[1,0.2,0.2,1])
        self.btn_factory.bind(on_release=lambda x: App.get_running_app().confirm_factory_reset())
        
        self.btn_grid.add_widget(self.btn_start)
        self.btn_grid.add_widget(self.btn_stop)
        self.btn_grid.add_widget(self.btn_reset)
        self.btn_grid.add_widget(self.btn_factory)
        
        self.btn_deploy = LiquidButton(text="FULL DEPLOYMENT", bg_color=[0.2,0.8,0.4,1], size_hint_y=None, height=dp(55))
        self.btn_deploy.bind(on_release=lambda x: App.get_running_app().run_task('deploy'))
        
        controls.add_widget(self.btn_grid)
        controls.add_widget(self.btn_deploy)
        
        self.main.add_widget(self.card)
        self.main.add_widget(self.console_card)
        self.main.add_widget(controls)
        self.add_widget(self.main)

    def update_log(self, text):
        self.console.text += text
        if len(self.console.text) > 5000: self.console.text = self.console.text[-5000:]
        self.console.cursor = (0, len(self.console.text))

class SettingsScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.main = BoxLayout(orientation='vertical', padding=dp(20), spacing=dp(15))
        self.lbl_title = Label(text="CONFIGURATION", font_size='24sp', bold=True, size_hint_y=None, height=dp(50))
        self.main.add_widget(self.lbl_title)
        self.scroll = ScrollView()
        self.content = BoxLayout(orientation='vertical', spacing=dp(15), size_hint_y=None)
        self.content.bind(minimum_height=self.content.setter('height'))
        
        theme_box = BoxLayout(size_hint_y=None, height=dp(50), spacing=dp(10))
        self.lbl_theme = Label(text="Theme", halign='left', size_hint_x=0.6)
        self.btn_theme_toggle = LiquidButton(text="Dark", size_hint_x=0.4, bg_color=[0.4, 0.4, 0.4, 0.5])
        self.btn_theme_toggle.bind(on_release=self.toggle_theme)
        theme_box.add_widget(self.lbl_theme)
        theme_box.add_widget(self.btn_theme_toggle)
        
        lang_box = BoxLayout(size_hint_y=None, height=dp(50), spacing=dp(10))
        self.lbl_lang = Label(text="Language", halign='left', size_hint_x=0.6)
        self.btn_lang_cycle = LiquidButton(text="English", size_hint_x=0.4, bg_color=[0.4, 0.4, 0.4, 0.5])
        self.btn_lang_cycle.bind(on_release=self.cycle_lang)
        lang_box.add_widget(self.lbl_lang)
        lang_box.add_widget(self.btn_lang_cycle)
        self.content.add_widget(theme_box)
        self.content.add_widget(lang_box)
        self.env_container = BoxLayout(orientation='vertical', spacing=dp(10), size_hint_y=None)
        self.env_container.bind(minimum_height=self.env_container.setter('height'))
        self.content.add_widget(self.env_container)
        self.scroll.add_widget(self.content)
        self.main.add_widget(self.scroll)
        self.btn_save = LiquidButton(text="SAVE CHANGES", size_hint_y=None, height=dp(55), bg_color=[0.2,0.8,0.4,1])
        self.btn_save.bind(on_release=self.save_all)
        self.main.add_widget(self.btn_save)
        self.add_widget(self.main)
        self.on_pre_enter = self.load_ui_data

    def load_ui_data(self, *args):
        app = App.get_running_app()
        self.btn_theme_toggle.text = app.settings.data["theme"]
        self.btn_lang_cycle.text = app.settings.data["language"]
        self.refresh_env_list()

    def toggle_theme(self, instance):
        app = App.get_running_app()
        new_t = "Light" if instance.text == "Dark" else "Dark"
        instance.text = new_t
        app.settings.data["theme"] = new_t
        app.apply_theme()

    def cycle_lang(self, instance):
        app = App.get_running_app()
        langs = list(TRANSLATIONS.keys())
        idx = (langs.index(instance.text) + 1) % len(langs)
        new_l = langs[idx]
        instance.text = new_l
        app.settings.data["language"] = new_l
        app.refresh_language()

    def refresh_env_list(self):
        self.env_container.clear_widgets()
        self.env_inputs = {}
        app = App.get_running_app()
        t = DARK_THEME if app.settings.data["theme"] == "Dark" else LIGHT_THEME
        if os.path.exists(".env"):
            with open(".env", "r") as f:
                for line in f:
                    if "=" in line and not line.startswith("#"):
                        k, v = line.strip().split("=", 1)
                        is_sensitive = any(word in k.upper() for word in ["KEY", "TOKEN", "SECRET", "PASS"])
                        box = BoxLayout(orientation='vertical', size_hint_y=None, height=dp(70))
                        l = Label(text=k, font_size='11sp', halign='left', size_hint_x=1, color=t["text_sec"])
                        l.bind(size=l.setter('text_size'))
                        i = TextInput(text="" if is_sensitive else v, hint_text="Enter value...", multiline=False, password=is_sensitive, background_color=t["input_bg"], foreground_color=t["text"], cursor_color=t["text"])
                        box.add_widget(l); box.add_widget(i)
                        self.env_container.add_widget(box)
                        self.env_inputs[k] = i

    def save_all(self, instance):
        app = App.get_running_app()
        if app.settings.data.get("deployed", False):
            app.dash.btn_start.disabled = False
            app.dash.btn_start.opacity = 1
            app.show_toast(app.get_text("toast_saved"))
            app.switch_tab('dash')
        else: app.show_toast("Saved. Run Deployment first.")
        app.settings.save()
        if self.env_inputs:
            lines = [f"{k}={v.text}\n" for k,v in self.env_inputs.items()]
            with open(".env", "w") as f: f.writelines(lines)

# --- MAIN APP ---
class BelindaApp(App):
    def build(self):
        self.settings = SettingsManager()
        self.root = FloatLayout()
        self.bg = LiquidBackground()
        self.root.add_widget(self.bg)
        self.sm = ScreenManager(transition=FadeTransition(duration=0.5))
        self.splash = SplashScreen(name='splash')
        self.setup = SetupScreen(name='setup'); self.dash = DashboardScreen(name='dash'); self.sett = SettingsScreen(name='sett')
        self.sm.add_widget(self.splash); self.sm.add_widget(self.setup); self.sm.add_widget(self.dash); self.sm.add_widget(self.sett)
        self.main_container = BoxLayout(orientation='vertical')
        self.main_container.add_widget(self.sm)
        self.nav = LiquidCard(size_hint_y=None, height=dp(65), radius=[dp(20), dp(20), 0, 0])
        self.btn_nav_dash = Button(text="DASHBOARD", background_color=(0,0,0,0))
        self.btn_nav_sett = Button(text="SETTINGS", background_color=(0,0,0,0))
        self.btn_nav_dash.bind(on_release=lambda x: self.switch_tab('dash'))
        self.btn_nav_sett.bind(on_release=lambda x: self.switch_tab('sett'))
        self.nav.add_widget(self.btn_nav_dash); self.nav.add_widget(self.btn_nav_sett)
        self.main_container.add_widget(self.nav)
        self.root.add_widget(self.main_container)
        self.nav.opacity = 0 
        self.toast = Label(text="", opacity=0, size_hint=(None,None), size=(dp(200), dp(40)), pos_hint={'center_x': 0.5, 'y': 0.1})
        self.root.add_widget(self.toast)
        self.apply_theme(); self.refresh_language()
        self.check_root_status()
        return self.root

    def check_root_status(self):
        self.is_rooted = False
        self.root_cmd = None
        for cmd in ['tsu', 'su']:
            if shutil.which(cmd):
                self.is_rooted = True
                self.root_cmd = cmd
                break
        if self.is_rooted:
            print(f"DEBUG: Root access detected via {self.root_cmd}")

    def show_notification(self, title, message):
        try:
            subprocess.run(["termux-notification", "-t", title, "-c", message, "--id", "belinda_ai_msg"], capture_output=True)
        except Exception as e:
            print(f"Notification failed: {e}")
            self.show_toast(message)

    def check_termux_and_api(self):
        # 1. Check for Termux
        is_termux = os.path.isdir("/data/data/com.termux")
        if not is_termux:
            self.show_toast("Termux not found! Opening Play Store...")
            try:
                subprocess.run(["am", "start", "-a", "android.intent.action.VIEW", "-d", "market://details?id=com.termux"], capture_output=True)
            except:
                webbrowser.open("https://play.google.com/store/apps/details?id=com.termux")
            return False
            
        # 2. Check for Termux-API
        is_api = False
        try:
            res = subprocess.run(["pm", "list", "packages", "com.termux.api"], capture_output=True, text=True)
            if "com.termux.api" in res.stdout: is_api = True
        except: pass
        
        if not is_api:
            self.show_toast("Termux:API missing! Opening GitHub...")
            webbrowser.open("https://github.com/termux/termux-api/releases")
            return False
            
        self.show_notification("System Ready", "Termux and Termux:API are already installed and verified.")
        return True

    def check_files_and_switch(self):
        if os.path.exists("bridge.js"):
            self.sm.current = 'dash'; self.nav.opacity = 1; self.nav.disabled = False
            if not self.settings.data.get("deployed", False): self.dash.btn_start.disabled = True; self.dash.btn_start.opacity = 0.5
        elif os.path.isdir("Belinda_AI"):
            try:
                os.chdir("Belinda_AI")
                self.sm.current = 'dash'; self.nav.opacity = 1; self.nav.disabled = False
                if not self.settings.data.get("deployed", False): self.dash.btn_start.disabled = True; self.dash.btn_start.opacity = 0.5
            except: self.sm.current = 'setup'
        else: self.sm.current = 'setup'; self.nav.opacity = 0; self.nav.disabled = True

    def perform_factory_reset(self):
        import shutil
        try:
            if os.path.isdir("Belinda_AI"): shutil.rmtree("Belinda_AI")
            elif os.path.exists("bridge.js"):
                for item in [".venv", "node_modules", "auth_info", "bridge.js", ".env", "package.json"]:
                    if os.path.isdir(item): shutil.rmtree(item)
                    elif os.path.exists(item): os.remove(item)
            self.settings.data["deployed"] = False; self.settings.save()
            self.check_files_and_switch()
            self.show_toast("Factory Reset Complete.")
        except Exception as e: self.show_toast(f"Reset Error: {e}")

    def confirm_factory_reset(self):
        LiquidPopup(title_text=self.get_text("pop_title"), desc_text=self.get_text("pop_desc"), on_yes=self.perform_factory_reset).open()

    def get_text(self, key):
        lang = self.settings.data["language"]
        return TRANSLATIONS.get(lang, TRANSLATIONS["English"]).get(key, key)

    def refresh_language(self):
        self.setup.lbl_title.text = self.get_text("title_setup")
        self.setup.lbl_desc.text = self.get_text("desc_setup")
        self.setup.btn_clone.text = self.get_text("btn_clone")
        self.dash.lbl_sys.text = self.get_text("sys_status")
        self.dash.lbl_status.text = self.get_text("status_ready")
        self.dash.btn_start.text = self.get_text("btn_start")
        self.dash.btn_stop.text = self.get_text("btn_stop")
        self.dash.btn_reset.text = self.get_text("btn_reset")
        self.dash.btn_factory.text = self.get_text("btn_factory")
        self.dash.btn_deploy.text = self.get_text("btn_deploy")
        self.btn_nav_dash.text = self.get_text("nav_dash")
        self.btn_nav_sett.text = self.get_text("nav_sett")
        self.sett.lbl_theme.text = self.get_text("lbl_theme")
        self.sett.lbl_lang.text = self.get_text("lbl_lang")
        self.sett.btn_save.text = self.get_text("btn_save")

    def apply_theme(self):
        t = DARK_THEME if self.settings.data["theme"] == "Dark" else LIGHT_THEME
        self.bg.bg_color.rgb = t["bg"]
        self.dash.card.color_node.rgba = t["card"]; self.dash.card.line_color.rgba = t["border"]
        self.dash.console_card.color_node.rgba = t["card"]; self.dash.console_card.line_color.rgba = t["border"]
        self.dash.lbl_sys.color = t["text_sec"]; self.dash.lbl_status.color = [0.2, 0.8, 1, 1] if self.settings.data["theme"] == "Dark" else [0, 0.4, 0.7, 1]
        self.setup.lbl_title.color = t["text"]; self.setup.lbl_desc.color = t["text_sec"]
        self.sett.lbl_title.color = [0.2, 0.8, 1, 1] if self.settings.data["theme"] == "Dark" else [0, 0.4, 0.7, 1]
        self.sett.lbl_theme.color = t["text"]; self.sett.lbl_lang.color = t["text"]
        self.sett.btn_theme_toggle.color = t["text"]; self.sett.btn_lang_cycle.color = t["text"]
        for box in self.sett.env_container.children:
            if isinstance(box, BoxLayout):
                for child in box.children:
                    if isinstance(child, Label): child.color = t["text_sec"]
                    elif isinstance(child, TextInput): child.background_color = t["input_bg"]; child.foreground_color = t["text"]; child.cursor_color = t["text"]
        self.dash.console.background_color = t["input_bg"]; self.dash.console.foreground_color = t["console_text"]
        self.nav.color_node.rgba = t["card"]; self.nav.line_color.rgba = t["border"]
        self.btn_nav_dash.color = t["text"]; self.btn_nav_sett.color = t["text"]

    def switch_tab(self, name): self.sm.current = name
    def show_toast(self, text):
        self.toast.text = text
        anim = Animation(opacity=1, duration=0.2) + Animation(duration=2) + Animation(opacity=0, duration=0.2); anim.start(self.toast)

    def run_task(self, task):
        if task == 'start' and not self.settings.data.get("deployed", False): self.show_toast("Run Deployment first!"); return
        self.dash.lbl_status.text = "WORKING..."
        worker = TaskWorker(task, self.dash.update_log, self.on_task_done); worker.start()

    def on_task_done(self, success):
        app = App.get_running_app()
        if self.dash.console.text.strip().endswith("Deployment Successful!"):
            app.settings.data["deployed"] = True; app.settings.save()
            Clock.schedule_once(lambda dt: app.switch_tab('sett'), 1); app.show_toast(app.get_text("toast_deploy_done"))
        def update(dt):
            self.dash.lbl_status.text = "ONLINE" if success else "STOPPED"
            self.dash.lbl_status.color = [0, 1, 0, 1] if success else [1, 0, 0, 1]
        Clock.schedule_once(update)

if __name__ == '__main__':
    while True:
        try:
            BelindaApp().run()
            break # Exit normally if requested by user
        except Exception as e:
            # Prevent force close: Log and restart if needed, or just sleep
            with open("termux_error.log", "a") as f:
                f.write(f"\n[{datetime.now()}] FATAL LOOP RECOVERY: {traceback.format_exc()}\n")
            
            # Simple cool-down to prevent infinite fast-crash loop
            print("FATAL ERROR RECOVERED. Check termux_error.log")
            time.sleep(3)
            # Depending on the error, we might want to exit, but user requested to stay open.
            # We will attempt to restart the app instance.
            continue
