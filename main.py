import os
import sys
import threading
import subprocess
import time
import json
import traceback
from datetime import datetime

# Redirect stderr/stdout to a log file for debugging on Android
if 'ANDROID_ARGUMENT' in os.environ:
    sys.stdout = open('android_stdout.log', 'w')
    sys.stderr = open('android_stderr.log', 'w')

# Kivy Imports
try:
    from kivy.app import App
    from kivy.core.window import Window
    from kivy.uix.boxlayout import BoxLayout
    from kivy.uix.floatlayout import FloatLayout
    from kivy.uix.anchorlayout import AnchorLayout
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
    # Fallback for PC development without Kivy installed
    print("CRITICAL: Kivy is not installed. Please run 'pip install kivy'.")
    sys.exit(1)

# --- CONFIG & CONSTANTS ---
GLASS_BG = get_color_from_hex('#1A1A2E')  # Deep dark blue
GLASS_CARD = (0.1, 0.1, 0.2, 0.6)         # Translucent glass
GLASS_BORDER = (0.4, 0.6, 1.0, 0.3)       # Subtle shine
ACCENT_COLOR = get_color_from_hex('#36BCF7') # Cyan
ACCENT_DANGER = get_color_from_hex('#FF4B4B') # Red
ACCENT_SUCCESS = get_color_from_hex('#00E676') # Green
TEXT_PRIMARY = (1, 1, 1, 1)
TEXT_SECONDARY = (1, 1, 1, 0.6)

# --- CUSTOM UI WIDGETS (LIQUID GLASS STYLE) ---

class LiquidBackground(Widget):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        with self.canvas:
            Color(rgba=get_color_from_hex('#0F0F14'))
            self.rect = Rectangle(pos=self.pos, size=self.size)
            
            # Decorative Orbs
            Color(0.2, 0.1, 0.4, 0.2)
            self.orb1 = RoundedRectangle(pos=(0, 0), size=(300, 300), radius=[150])
            
            Color(0.1, 0.3, 0.4, 0.15)
            self.orb2 = RoundedRectangle(pos=(200, 400), size=(400, 400), radius=[200])

        self.bind(pos=self.update_rect, size=self.update_rect)

    def update_rect(self, *args):
        self.rect.pos = self.pos
        self.rect.size = self.size
        # Simple movement for orbs based on screen size
        self.orb1.pos = (self.width * 0.1, self.height * 0.2)
        self.orb2.pos = (self.width * 0.5, self.height * 0.6)

class LiquidCard(BoxLayout):
    radius = ListProperty([dp(20)])
    bg_color = ListProperty(GLASS_CARD)
    stroke_color = ListProperty(GLASS_BORDER)
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.padding = dp(15)
        self.background_normal = ''
        self.background_color = (0,0,0,0)
        with self.canvas.before:
            Color(*self.bg_color)
            self.rect = RoundedRectangle(pos=self.pos, size=self.size, radius=self.radius)
            Color(*self.stroke_color)
            self.border = Line(rounded_rectangle=(self.x, self.y, self.width, self.height, self.radius[0]), width=1.2)
        
        self.bind(pos=self.update_rect, size=self.update_rect)

    def update_rect(self, *args):
        self.rect.pos = self.pos
        self.rect.size = self.size
        self.border.rounded_rectangle = (self.x, self.y, self.width, self.height, self.radius[0])

class LiquidButton(Button):
    bg_color = ListProperty(ACCENT_COLOR)
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.background_normal = ''
        self.background_down = ''
        self.background_color = (0,0,0,0)
        self.font_size = '16sp'
        self.bold = True
        self.color = TEXT_PRIMARY
        
    def on_press(self):
        anim = Animation(opacity=0.7, duration=0.1)
        anim.start(self)

    def on_release(self):
        anim = Animation(opacity=1.0, duration=0.1)
        anim.start(self)

    def on_size(self, *args):
        self.redraw()
            
    def on_pos(self, *args):
        self.redraw()
        
    def redraw(self):
        if not hasattr(self, 'canvas') or self.canvas is None:
            return
        self.canvas.before.clear()
        with self.canvas.before:
            Color(*self.bg_color)
            RoundedRectangle(pos=self.pos, size=self.size, radius=[dp(12)])
            # Glossy shine
            Color(1, 1, 1, 0.15)
            RoundedRectangle(pos=(self.x, self.y + self.height/2), size=(self.width, self.height/2), radius=[dp(12), dp(12), 0, 0])

class LiquidNavButton(Button):
    active = BooleanProperty(False)
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.background_normal = ''
        self.background_down = ''
        self.background_color = (0,0,0,0)
        self.font_size = '14sp'
        self.color = TEXT_SECONDARY
        
    def on_size(self, *args):
        self.redraw()
        
    def on_pos(self, *args):
        self.redraw()
        
    def on_active(self, *args):
        self.redraw()
        
    def redraw(self):
        if not hasattr(self, 'canvas') or self.canvas is None:
            return
        self.canvas.before.clear()
        with self.canvas.before:
            if self.active:
                Color(0.2, 0.8, 1.0, 0.15)
                RoundedRectangle(pos=self.pos, size=self.size, radius=[dp(10)])
                self.color = ACCENT_COLOR
            else:
                self.color = TEXT_SECONDARY

# --- SCREENS ---

class DashboardScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        
        main = BoxLayout(orientation='vertical', padding=dp(20), spacing=dp(20))
        
        # Header
        header = Label(text="BELINDA AI", font_size='28sp', bold=True, color=ACCENT_COLOR, size_hint_y=None, height=dp(50))
        main.add_widget(header)

        # Status Card
        status_card = LiquidCard(orientation='vertical', size_hint_y=None, height=dp(100))
        
        lbl_title = Label(text="SYSTEM STATUS", font_size='12sp', color=TEXT_SECONDARY, size_hint_y=None, height=dp(20))
        self.lbl_status = Label(text="READY", font_size='24sp', bold=True, color=ACCENT_SUCCESS)
        
        status_card.add_widget(lbl_title)
        status_card.add_widget(self.lbl_status)
        main.add_widget(status_card)
        
        # Controls Grid
        grid = GridLayout(cols=2, spacing=dp(15), size_hint_y=None, height=dp(140))
        
        self.btn_start = LiquidButton(text="START", bg_color=ACCENT_COLOR)
        self.btn_start.bind(on_release=lambda x: App.get_running_app().run_task('start'))
        
        self.btn_stop = LiquidButton(text="STOP", bg_color=ACCENT_DANGER)
        self.btn_stop.bind(on_release=lambda x: App.get_running_app().run_task('stop'))
        
        self.btn_reset = LiquidButton(text="RESET", bg_color=get_color_from_hex('#7B1FA2'))
        self.btn_reset.bind(on_release=lambda x: App.get_running_app().run_task('reset'))

        self.btn_session = LiquidButton(text="WIPE DATA", bg_color=get_color_from_hex('#FF9800'))
        self.btn_session.bind(on_release=lambda x: App.get_running_app().run_task('session'))
        
        grid.add_widget(self.btn_start)
        grid.add_widget(self.btn_stop)
        grid.add_widget(self.btn_reset)
        grid.add_widget(self.btn_session)
        
        main.add_widget(grid)
        
        # Recent Logs Preview
        log_card = LiquidCard(orientation='vertical')
        log_label = Label(text="LIVE CONSOLE", font_size='12sp', color=TEXT_SECONDARY, size_hint_y=None, height=dp(20))
        self.log_preview = TextInput(
            text="Initializing...", 
            readonly=True, 
            background_color=(0,0,0,0), 
            foreground_color=get_color_from_hex('#00FF00'), 
            font_size='10sp'
        )
        
        log_card.add_widget(log_label)
        log_card.add_widget(self.log_preview)
        
        main.add_widget(log_card)
        
        self.add_widget(main)

    def update_log(self, text):
        self.log_preview.text += text
        if len(self.log_preview.text) > 5000:
             self.log_preview.text = self.log_preview.text[-5000:]
        # Auto-scroll
        self.log_preview.cursor = (0, len(self.log_preview.text))

class LiquidSettingRow(BoxLayout):
    def __init__(self, key_name, value, **kwargs):
        super().__init__(**kwargs)
        self.orientation = 'vertical'
        self.size_hint_y = None
        self.height = dp(80)
        self.spacing = dp(5)
        
        # Determine if this should be masked (API Keys, etc)
        is_sensitive = any(word in key_name.upper() for word in ["KEY", "TOKEN", "SECRET", "PASS"])
        
        lbl = Label(
            text=key_name.replace("_", " "), 
            font_size='12sp', 
            color=TEXT_SECONDARY, 
            halign='left', 
            size_hint_x=1
        )
        lbl.bind(size=lbl.setter('text_size'))
        
        self.input = TextInput(
            text=value,
            multiline=False,
            password=is_sensitive,
            background_color=(0,0,0,0.2),
            foreground_color=(1,1,1,1),
            padding=[dp(10), dp(10)],
            font_size='14sp'
        )
        # Style the input a bit more
        with self.input.canvas.after:
            Color(*GLASS_BORDER)
            self.line = Line(points=[self.input.x, self.input.y, self.input.x + self.input.width, self.input.y], width=1)
        self.input.bind(pos=self.update_line, size=self.update_line)

        self.add_widget(lbl)
        self.add_widget(self.input)

    def update_line(self, *args):
        self.line.points = [self.input.x, self.input.y, self.input.x + self.input.width, self.input.y]

class SettingsScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.rows = {}
        
        main = BoxLayout(orientation='vertical', padding=dp(20), spacing=dp(15))
        
        title = Label(text="CONFIGURATION", font_size='24sp', bold=True, size_hint_y=None, height=dp(50), color=ACCENT_COLOR)
        main.add_widget(title)
        
        self.scroll = ScrollView(do_scroll_x=False)
        self.content = BoxLayout(orientation='vertical', spacing=dp(20), size_hint_y=None)
        self.content.bind(minimum_height=self.content.setter('height'))
        
        self.scroll.add_widget(self.content)
        main.add_widget(self.scroll)
        
        # Action Buttons
        btn_layout = BoxLayout(size_hint_y=None, height=dp(55), spacing=dp(15))
        
        btn_save = LiquidButton(text="SAVE CHANGES", bg_color=ACCENT_SUCCESS)
        btn_save.bind(on_release=self.save_settings)
        
        btn_layout.add_widget(btn_save)
        main.add_widget(btn_layout)
        
        self.add_widget(main)
        self.on_pre_enter = self.refresh_gui

    def refresh_gui(self, *args):
        self.content.clear_widgets()
        self.rows = {}
        
        env_data = self.load_env_dict()
        for k, v in env_data.items():
            row = LiquidSettingRow(key_name=k, value=v)
            self.content.add_widget(row)
            self.rows[k] = row

    def load_env_dict(self):
        data = {}
        if os.path.exists(".env"):
            try:
                with open(".env", "r") as f:
                    for line in f:
                        line = line.strip()
                        if line and "=" in line and not line.startswith("#"):
                            k, v = line.split("=", 1)
                            data[k.strip()] = v.strip().strip('"').strip("'")
            except: pass
        return data
        
    def save_settings(self, instance):
        try:
            lines = []
            for k, row in self.rows.items():
                val = row.input.text
                lines.append(f"{k}={val}\n")
            
            with open(".env", "w") as f:
                f.writelines(lines)
            
            App.get_running_app().show_toast("Configuration Updated!")
        except Exception as e:
            App.get_running_app().show_toast(f"Error: {str(e)}")

# --- WORKER THREAD ---

class TaskWorker(threading.Thread):
    def __init__(self, task, callback_log, callback_done):
        super().__init__()
        self.task = task
        self.callback_log = callback_log
        self.callback_done = callback_done
        self.daemon = True

    def run(self):
        try:
            if self.task == 'session':
                self.callback_log(">>> Wiping session folder...\n")
                import shutil
                if os.path.exists("auth_info"):
                    shutil.rmtree("auth_info")
                self.callback_log(">>> Session wiped. Please restart bot to scan QR again.\n")
                self.callback_done(True)
                return

            # Determine script based on OS
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

            # Ensure executable
            try:
                subprocess.run(['chmod', '+x', cmd])
            except: pass

            self.callback_log(f">>> Executing {cmd}...\n")
            
            # Run process
            process = subprocess.Popen(
                ['bash', cmd],
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                bufsize=1,
                universal_newlines=True
            )
            
            for line in process.stdout:
                if line:
                    self.callback_log(line)
                
            process.wait()
            self.callback_log(f">>> Task {self.task} finished with code {process.returncode}\n")
            self.callback_done(process.returncode == 0)

        except Exception as e:
            self.callback_log(f"CRITICAL ERROR: {str(e)}\n")
            self.callback_done(False)

# --- MAIN APP ---

class BelindaApp(App):
    def build(self):
        Window.clearcolor = get_color_from_hex('#0F0F14')
        
        # Root Layout
        self.root_layout = FloatLayout()
        
        # Background
        self.bg = LiquidBackground()
        self.root_layout.add_widget(self.bg)
        
        # Main Container
        self.main_container = BoxLayout(orientation='vertical')
        
        # Content Area
        self.sm = ScreenManager(transition=FadeTransition())
        self.dashboard = DashboardScreen(name='dashboard')
        self.settings = SettingsScreen(name='settings')
        self.sm.add_widget(self.dashboard)
        self.sm.add_widget(self.settings)
        
        self.main_container.add_widget(self.sm)
        
        # Bottom Navigation
        nav_bar = LiquidCard(size_hint_y=None, height=dp(60), radius=[dp(20), dp(20), 0, 0])
        nav_bar.padding = dp(10)
        nav_bar.spacing = dp(10)
        
        self.nav_dash = LiquidNavButton(text="DASHBOARD", active=True)
        self.nav_dash.bind(on_release=lambda x: self.switch_tab('dashboard'))
        
        self.nav_settings = LiquidNavButton(text="SETTINGS")
        self.nav_settings.bind(on_release=lambda x: self.switch_tab('settings'))
        
        nav_bar.add_widget(self.nav_dash)
        nav_bar.add_widget(self.nav_settings)
        
        self.main_container.add_widget(nav_bar)
        
        self.root_layout.add_widget(self.main_container)
        
        # Toast Label (Hidden by default)
        self.toast = Label(
            text="", 
            font_size='14sp', 
            color=(1,1,1,1),
            size_hint=(None, None),
            size=(dp(200), dp(40)),
            pos_hint={'center_x': 0.5, 'y': 0.1},
            opacity=0
        )
        self.root_layout.add_widget(self.toast)
        
        return self.root_layout

    def switch_tab(self, name):
        self.sm.current = name
        self.nav_dash.active = (name == 'dashboard')
        self.nav_settings.active = (name == 'settings')

    def run_task(self, task):
        self.dashboard.lbl_status.text = "WORKING..."
        self.dashboard.lbl_status.color = ACCENT_COLOR
        
        def log_cb(text):
            Clock.schedule_once(lambda dt: self.dashboard.update_log(text))
            
        def done_cb(success):
            Clock.schedule_once(lambda dt: self.on_task_done(success))
        
        worker = TaskWorker(task, log_cb, done_cb)
        worker.start()

    def on_task_done(self, success):
        if success:
            self.dashboard.lbl_status.text = "ONLINE"
            self.dashboard.lbl_status.color = ACCENT_SUCCESS
        else:
            self.dashboard.lbl_status.text = "STOPPED"
            self.dashboard.lbl_status.color = ACCENT_DANGER

    def show_toast(self, text):
        self.toast.text = text
        anim = Animation(opacity=1, duration=0.2) + Animation(duration=2) + Animation(opacity=0, duration=0.2)
        anim.start(self.toast)

if __name__ == '__main__':
    try:
        BelindaApp().run()
    except Exception as e:
        # Fallback crash logger
        with open("crash.log", "w") as f:
            f.write(traceback.format_exc())
