import os
import sys
import traceback

# Redirect stderr to a file on Android for easier debugging
if 'PYTHON_SERVICE_ARGUMENT' in os.environ or os.path.exists('/sdcard'):
    sys.stderr = open('android_error.log', 'w')

try:
    from kivy.app import App
    from kivy.uix.boxlayout import BoxLayout
    from kivy.uix.button import QPushButton
    from kivy.uix.label import QLabel
    from kivy.uix.textinput import TextInput
    from kivy.uix.scrollview import ScrollView  # Fixed: was QScrollView
    from kivy.clock import Clock
    from kivy.utils import get_color_from_hex
    from kivy.core.window import Window
except Exception as e:
    with open('crash_log.txt', 'w') as f:
        f.write(f"Kivy Import Error: {str(e)}\n")
        f.write(traceback.format_exc())
    sys.exit(1)

# Dummy SettingsManager for Mobile
class SettingsManager:
    def __init__(self, path): self.path = path
    def get(self, key, default=""): return default
    def set(self, key, val): pass

class BelindaAndroidApp(App):
    def build(self):
        try:
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
                font_size='12sp'
            )
            layout.addWidget(self.console)

            # Button Grid
            btn_layout = BoxLayout(orientation='vertical', spacing=10, size_hint_y=None, height='220dp')
            
            row1 = BoxLayout(spacing=10)
            row1.addWidget(self.create_btn("START BOT", '#36BCF7', self.start_bot))
            row1.addWidget(self.create_btn("STOP BOT", '#FF4B4B', self.stop_bot))
            
            row2 = BoxLayout(spacing=10)
            row2.addWidget(self.create_btn("RESET", '#4CAF50', self.reset_bot))
            row2.addWidget(self.create_btn("RESET SESSION", '#FF9800', self.reset_session))
            
            btn_layout.addWidget(row1)
            btn_layout.addWidget(row2)
            layout.addWidget(btn_layout)

            return layout
        except Exception as e:
            self.log(f"Build Error: {str(e)}")
            return QLabel(text=f"CRASH: {str(e)}")

    def create_btn(self, text, color_hex, callback):
        btn = QPushButton(text=text)
        btn.background_normal = ''
        btn.background_color = get_color_from_hex(color_hex)
        btn.bind(on_press=callback)
        return btn

    def log(self, message):
        self.console.text += f"> {message}\n"
        self.console.cursor = (len(self.console.text), 0)

    def start_bot(self, instance):
        self.log("Starting Belinda AI...")
        self.status_label.text = "Status: Running"
        
    def stop_bot(self, instance):
        self.log("Stopping bot...")
        self.status_label.text = "Status: Stopped"

    def reset_bot(self, instance):
        self.log("Resetting system...")

    def reset_session(self, instance):
        self.log("Wiping session data...")

if __name__ == '__main__':
    try:
        BelindaAndroidApp().run()
    except Exception as e:
        with open('final_crash.log', 'w') as f:
            f.write(traceback.format_exc())
