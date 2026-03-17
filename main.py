import os
import sys
from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import QPushButton
from kivy.uix.label import QLabel
from kivy.uix.textinput import TextInput
from kivy.uix.scrollview import QScrollView
from kivy.clock import Clock
from kivy.utils import get_color_from_hex
from kivy.core.window import Window

# Try to import settings manager if possible, otherwise use a simple dict
try:
    from installer.settings_manager import SettingsManager
except ImportError:
    class SettingsManager:
        def __init__(self, path): self.path = path
        def get(self, key, default=""): return default
        def set(self, key, val): pass

class BelindaAndroidApp(App):
    def build(self):
        Window.clearcolor = get_color_from_hex('#0F0F14')
        self.title = "Belinda AI Installer"
        
        # Main Layout
        layout = BoxLayout(orientation='vertical', padding=20, spacing=15)
        
        # Header
        header = QLabel(
            text="BELINDA AI", 
            font_size='32sp', 
            bold=True, 
            color=get_color_from_hex('#36BCF7'),
            size_hint_y=None,
            height='60dp'
        )
        layout.addWidget(header)
        
        sub_header = QLabel(
            text="MOBILE ECOSYSTEM", 
            font_size='12sp', 
            color=[1, 1, 1, 0.4],
            size_hint_y=None,
            height='20dp'
        )
        layout.addWidget(sub_header)

        # Status Card
        self.status_label = QLabel(
            text="System Status: Ready",
            size_hint_y=None,
            height='40dp'
        )
        layout.addWidget(self.status_label)

        # Console Log View
        self.console = TextInput(
            text="--- Mobile Console Initialized ---\n",
            readonly=True,
            background_color=[0, 0, 0, 0.6],
            foreground_color=[0, 1, 0, 1],
            font_name='Roboto', # Standard Kivy font
            font_size='12sp'
        )
        layout.addWidget(self.console)

        # Button Grid (2x2)
        btn_layout = BoxLayout(orientation='vertical', spacing=10, size_hint_y=None, height='220dp')
        
        row1 = BoxLayout(spacing=10)
        self.start_btn = self.create_btn("START BOT", '#36BCF7', self.start_bot)
        self.stop_btn = self.create_btn("STOP BOT", '#FF4B4B', self.stop_bot)
        row1.addWidget(self.start_btn)
        row1.addWidget(self.stop_btn)
        
        row2 = BoxLayout(spacing=10)
        self.reset_btn = self.create_btn("RESET", '#4CAF50', self.reset_bot)
        self.session_btn = self.create_btn("RESET SESSION", '#FF9800', self.reset_session)
        row2.addWidget(self.reset_btn)
        row2.addWidget(self.session_btn)
        
        btn_layout.addWidget(row1)
        btn_layout.addWidget(row2)
        layout.addWidget(btn_layout)

        return layout

    def create_btn(self, text, color_hex, callback):
        btn = QPushButton(text=text)
        btn.background_normal = ''
        btn.background_color = get_color_from_hex(color_hex)
        btn.bind(on_press=callback)
        return btn

    def log(self, message):
        self.console.text += f"> {message}\n"
        # Scroll to bottom
        self.console.cursor = (len(self.console.text), 0)

    def start_bot(self, instance):
        self.log("Starting Belinda AI...")
        self.status_label.text = "Status: Running"
        # Actual subprocess logic would go here, 
        # but requires Termux or similar environment on Android to run Node.js/Python
        
    def stop_bot(self, instance):
        self.log("Stopping bot...")
        self.status_label.text = "Status: Stopped"

    def reset_bot(self, instance):
        self.log("Resetting system...")

    def reset_session(self, instance):
        self.log("Wiping session data...")

if __name__ == '__main__':
    BelindaAndroidApp().run()
