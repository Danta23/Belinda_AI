import sys
import os
import json
import subprocess
import math
import platform
import re
import warnings
import shutil
from PyQt5.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
                             QLabel, QPushButton, QStackedWidget, QFrame, QGraphicsDropShadowEffect,
                             QLineEdit, QProgressBar, QFileDialog, QSpacerItem, QSizePolicy, QTextEdit, QComboBox)
from PyQt5.QtCore import Qt, QPropertyAnimation, QEasingCurve, QSize, pyqtSignal, QThread, QPoint, QTimer
from PyQt5.QtGui import QColor, QPainter, QLinearGradient, QBrush, QIcon, QPen

# Mute deprecation warnings from PyQt dependencies
warnings.filterwarnings("ignore", category=DeprecationWarning)

# Import styles and settings
from styles import DARK_STYLE_TEMPLATE, LIGHT_STYLE_TEMPLATE
from settings_manager import SettingsManager
from translations import TRANSLATIONS

class LogTailer(QThread):
    new_log = pyqtSignal(str)

    def __init__(self, root_dir):
        super().__init__()
        self.root_dir = root_dir
        self.log_file = os.path.join(root_dir, "task.log")
        self.running = True
        self._last_size = 0

    def run(self):
        while self.running:
            if os.path.exists(self.log_file):
                try:
                    curr_size = os.path.getsize(self.log_file)
                    if curr_size < self._last_size:
                        self._last_size = 0
                    if curr_size > self._last_size:
                        with open(self.log_file, 'r', encoding='utf-8', errors='ignore') as f:
                            f.seek(self._last_size)
                            new_content = f.read()
                            if new_content:
                                self.new_log.emit(new_content)
                        self._last_size = curr_size
                except:
                    pass
            self.msleep(200)

class FluidGradientWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.offset = 0
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_gradient)
        self.timer.start(50)
        self.dark_mode = True

    def update_gradient(self):
        self.offset += 0.01
        if self.offset > 2 * math.pi:
            self.offset = 0
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        rect = self.rect()
        gradient = QLinearGradient(rect.topLeft(), rect.bottomRight())
        if self.dark_mode:
            c1 = QColor(54, 188, 247, 40)
            c2 = QColor(153, 50, 204, 40)
            bg = QColor(15, 15, 20, 220)
        else:
            c1 = QColor(54, 188, 247, 30)
            c2 = QColor(153, 50, 204, 30)
            bg = QColor(245, 245, 250, 220)
        gradient.setColorAt(0, c1)
        gradient.setColorAt(1, c2)
        painter.setBrush(QBrush(bg))
        painter.setPen(Qt.NoPen)
        painter.drawRoundedRect(rect, 20, 20)
        painter.setBrush(QBrush(gradient))
        painter.drawRoundedRect(rect, 20, 20)

class Worker(QThread):
    progress = pyqtSignal(int, str)
    finished = pyqtSignal(bool, str)
    log_output = pyqtSignal(str)

    def __init__(self, task, root_dir, settings_mgr, api_key=None):
        super().__init__()
        self.task = task
        self.root_dir = root_dir
        self.sm = settings_mgr
        self.api_key = api_key

    def get_scripts(self):
        os_name = platform.system().lower()
        mode = self.sm.get("EXECUTION_MODE", "local")
        if mode == "docker":
            return {
                "start": "docker-compose up -d --build && docker-compose logs -f",
                "stop": "docker-compose down",
                "reset": "docker-compose down -v",
                "shell": "docker"
            }
        if os_name == "windows":
            return {"start": "start.ps1", "stop": "stop.ps1", "reset": "reset.ps1", "shell": "powershell"}
        else:
            return {"start": "start.sh", "stop": "stop.sh", "reset": "reset.sh", "shell": "sh"}

    def run(self):
        scripts = self.get_scripts()
        log_file = os.path.join(self.root_dir, "task.log")
        engine_dir = getattr(self, 'engine_dir', self.root_dir)
        try:
            if os.path.exists(log_file):
                with open(log_file, 'a', encoding='utf-8') as f:
                    f.write(f"\n\n--- NEW TASK: {self.task.upper()} ---\n")
            else:
                with open(log_file, 'w', encoding='utf-8') as f:
                    f.write(f"--- Task Started: {self.task} ---\n")
        except: pass

        try:
            if self.task == "install":
                self.progress.emit(10, "status_env")
                if self.api_key:
                    self.sm.set("GROQ_API_KEY", self.api_key)
                
                # Setup .env
                env_proto = os.path.join(self.root_dir, ".env.example")
                env_file = os.path.join(self.root_dir, ".env")
                if os.path.exists(env_proto) and not os.path.exists(env_file):
                    shutil.copy(env_proto, env_file)

                # Pip install
                self.progress.emit(40, "status_pip")
                pip_path = os.path.join(self.root_dir, ".venv", "Scripts", "pip") if os.name == 'nt' else os.path.join(self.root_dir, ".venv", "bin", "pip")
                subprocess.run(f'"{pip_path}" install -r requirements.txt', cwd=self.root_dir, shell=True)
                
                # Npm install
                self.progress.emit(70, "status_npm")
                subprocess.run("npm install --no-audit --no-fund", cwd=self.root_dir, shell=True)
                
                self.progress.emit(100, "task_finished")
                self.finished.emit(True, "Installation completed!")

            elif self.task in ["start", "stop", "reset"]:
                cmd = scripts[self.task]
                if scripts["shell"] == "powershell":
                    cmd = f"powershell -ExecutionPolicy Bypass -File ./{cmd}"
                process = subprocess.Popen(cmd, cwd=self.root_dir, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, shell=True)
                while True:
                    line = process.stdout.readline()
                    if not line and process.poll() is not None: break
                    if line: self.log_output.emit(line)
                self.finished.emit(True, "task_finished")
        except Exception as e:
            self.finished.emit(False, f"Error: {str(e)}")

class CloneWorker(QThread):
    progress = pyqtSignal(int, str)
    finished = pyqtSignal(bool, str)

    def __init__(self, target_dir):
        super().__init__()
        self.target_dir = target_dir
        self.running = True

    def stop(self):
        self.running = False

    def run(self):
        try:
            repo_url = "https://github.com/Danta23/Belinda_AI.git"
            self.progress.emit(10, "status_detecting")
            
            # Check for Git
            try:
                subprocess.run(["git", "--version"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)
            except:
                self.finished.emit(False, "Git not found! Please install Git for Windows.")
                return

            if os.path.exists(self.target_dir):
                # If it's a valid repo, we are done
                if os.path.exists(os.path.join(self.target_dir, ".git")):
                    self.finished.emit(True, "Project already exists.")
                    return
                # If not a valid repo, try to remove it if empty, otherwise we clone into it
                try:
                    if not os.listdir(self.target_dir):
                        os.rmdir(self.target_dir)
                except: pass

            self.progress.emit(30, "status_cloning")
            process = subprocess.Popen(
                f"git clone --progress {repo_url} \"{self.target_dir}\"",
                stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, shell=True, universal_newlines=True
            )
            
            while self.running:
                line = process.stdout.readline()
                if not line and process.poll() is not None: break
                if line:
                    match = re.search(r"(\d+)%", line)
                    if match:
                        percent = int(match.group(1))
                        app_percent = 30 + int(percent * 0.65)
                        self.progress.emit(app_percent, "status_cloning")
            
            if not self.running:
                process.terminate()
                return

            if process.returncode != 0:
                self.finished.emit(False, "Clone failed. Check internet.")
                return

            if not os.path.exists(os.path.join(self.target_dir, "bridge.js")):
                self.finished.emit(False, "clone_incomplete: bridge.js missing")
                return

            self.progress.emit(100, "task_finished")
            self.finished.emit(True, "Project ready.")
        except Exception as e:
            self.finished.emit(False, str(e))

class BelindaSetup(QMainWindow):
    def __init__(self):
        super().__init__()
        if getattr(sys, 'frozen', False):
            self.base_dir = os.path.dirname(sys.executable)
        else:
            self.base_dir = os.path.dirname(os.path.abspath(__file__))
            if os.path.basename(self.base_dir) == "installer":
                self.base_dir = os.path.dirname(self.base_dir)
            
        self.root_dir = os.path.join(self.base_dir, "Belinda_AI")
        os.makedirs(self.base_dir, exist_ok=True)
        
        # Use base_dir for settings so they persist even if Belinda_AI is wiped
        self.sm = SettingsManager(self.base_dir)
        
        self.setWindowFlags(Qt.FramelessWindowHint)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setMinimumSize(1000, 720)
        self._drag_pos = QPoint()

        self.init_ui()
        self.apply_theme()
        
        if not self.is_project_ready():
            self.content_area.setCurrentWidget(self.page_setup)
        else:
            self.content_area.setCurrentIndex(1)
            self.page_installer.check_dependencies(self.root_dir)

    def is_project_ready(self):
        return os.path.exists(os.path.join(self.root_dir, "bridge.js"))

    def start_setup_clone(self):
        self.page_setup.clone_btn.setEnabled(False)
        self.page_setup.progress_bar.setVisible(True)
        self.setup_worker = CloneWorker(self.root_dir)
        self.setup_worker.progress.connect(self.update_setup_progress)
        self.setup_worker.finished.connect(self.setup_finished)
        self.setup_worker.start()

    def update_setup_progress(self, val, msg_key):
        self.page_setup.progress_bar.setValue(val)
        self.page_setup.status_label.setText(self.get_text(msg_key))

    def setup_finished(self, success, msg):
        if success:
            self.content_area.setCurrentIndex(1)
            self.page_installer.check_dependencies(self.root_dir)
        else:
            self.page_setup.status_label.setText(msg)
            self.page_setup.clone_btn.setEnabled(True)

    def init_ui(self):
        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        self.main_layout = QHBoxLayout(self.central_widget)
        self.bg_widget = FluidGradientWidget()
        self.container_layout = QHBoxLayout(self.bg_widget)
        self.main_layout.addWidget(self.bg_widget)

        self.sidebar = QFrame()
        self.sidebar.setFixedWidth(240)
        self.sidebar_layout = QVBoxLayout(self.sidebar)
        
        logo = QLabel("BELINDA")
        logo.setStyleSheet("font-size: 24px; font-weight: 900; color: #36BCF7;")
        logo.setAlignment(Qt.AlignCenter)
        self.sidebar_layout.addWidget(logo)
        
        self.sidebar_layout.addSpacing(30)
        import qtawesome as qta
        self.btns = []
        self.add_nav_button("nav_dashboard", "fa5s.tachometer-alt", 0)
        self.add_nav_button("nav_console", "fa5s.terminal", 1)
        self.add_nav_button("nav_config", "fa5s.tools", 2)
        self.sidebar_layout.addStretch()
        
        self.exit_btn = QPushButton("TERMINATE")
        self.exit_btn.setStyleSheet("color: #FF4B4B; font-weight: bold;")
        self.exit_btn.clicked.connect(self.close)
        self.sidebar_layout.addWidget(self.exit_btn)
        self.container_layout.addWidget(self.sidebar)

        self.content_area = QStackedWidget()
        from translations import TRANSLATIONS
        self.page_setup = PageSetup(self.start_setup_clone, self.get_text)
        self.page_installer = PageInstaller(self.root_dir, self.start_worker_task, self.get_text)
        self.page_logs = PageLogs(self.root_dir, self.get_text)
        self.page_settings = PageSettings(self.sm, self.apply_changes, self.get_text)
        
        self.content_area.addWidget(self.page_setup)
        self.content_area.addWidget(self.page_installer)
        self.content_area.addWidget(self.page_logs)
        self.content_area.addWidget(self.page_settings)
        self.container_layout.addWidget(self.content_area)

    def get_text(self, key):
        lang = self.sm.get("APP_LANGUAGE", "English")
        return TRANSLATIONS.get(lang, TRANSLATIONS["English"]).get(key, key)

    def add_nav_button(self, text_key, icon_name, index):
        import qtawesome as qta
        btn = QPushButton(self.get_text(text_key))
        btn.setIcon(qta.icon(icon_name, color="#36BCF7"))
        btn.clicked.connect(lambda: self.switch_page(index))
        self.sidebar_layout.addWidget(btn)
        self.btns.append(btn)

    def switch_page(self, index):
        self.content_area.setCurrentIndex(index + 1)

    def apply_changes(self):
        self.apply_theme()
        self.retranslate_all()

    def retranslate_all(self):
        self.page_setup.retranslate()
        self.page_installer.retranslate()
        self.page_logs.retranslate()
        self.page_settings.retranslate()

    def apply_theme(self):
        theme = self.sm.get("APP_THEME", "dark")
        self.bg_widget.dark_mode = (theme == "dark")
        template = DARK_STYLE_TEMPLATE if theme == "dark" else LIGHT_STYLE_TEMPLATE
        style = template.format(font_family="Segoe UI", font_size="14", title_size="24")
        self.setStyleSheet(style)

    def start_worker_task(self, task):
        self.worker = Worker(task, self.root_dir, self.sm)
        self.worker.progress.connect(self.update_progress)
        self.worker.finished.connect(self.task_finished)
        self.worker.start()

    def update_progress(self, val, msg):
        self.page_installer.progress_bar.setValue(val)
        self.page_installer.status_label.setText(self.get_text(msg))

    def task_finished(self, success, msg):
        self.page_installer.status_label.setText(self.get_text(msg))

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self._drag_pos = event.globalPos() - self.frameGeometry().topLeft()
            event.accept()

    def mouseMoveEvent(self, event):
        if event.buttons() == Qt.LeftButton:
            self.move(event.globalPos() - self._drag_pos)
            event.accept()

class PageSetup(QWidget):
    def __init__(self, start_clone_callback, get_text_func):
        super().__init__()
        self.get_text = get_text_func
        layout = QVBoxLayout(self)
        self.title = QLabel("Initial Project Setup")
        layout.addWidget(self.title)
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        layout.addWidget(self.progress_bar)
        self.status_label = QLabel("")
        layout.addWidget(self.status_label)
        self.clone_btn = QPushButton("CLONE & SETUP PROJECT")
        self.clone_btn.clicked.connect(start_clone_callback)
        layout.addWidget(self.clone_btn)
    def retranslate(self): pass

class PageInstaller(QWidget):
    def __init__(self, root_dir, start_task_callback, get_text_func):
        super().__init__()
        self.get_text = get_text_func
        layout = QVBoxLayout(self)
        self.status_label = QLabel("Ready")
        layout.addWidget(self.status_label)
        self.progress_bar = QProgressBar()
        layout.addWidget(self.progress_bar)
        self.start_btn = QPushButton("START BOT")
        self.start_btn.clicked.connect(lambda: start_task_callback("start"))
        layout.addWidget(self.start_btn)
    def check_dependencies(self, path): pass
    def retranslate(self): pass

class PageLogs(QWidget):
    def __init__(self, root_dir, get_text_func):
        super().__init__()
        layout = QVBoxLayout(self)
        self.log_view = QTextEdit()
        layout.addWidget(self.log_view)
    def retranslate(self): pass

class PageSettings(QWidget):
    def __init__(self, settings_mgr, reload_callback, get_text_func):
        super().__init__()
        layout = QVBoxLayout(self)
        self.save_btn = QPushButton("SAVE")
        self.save_btn.clicked.connect(reload_callback)
        layout.addWidget(self.save_btn)
    def retranslate(self): pass

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = BelindaSetup()
    window.show()
    sys.exit(app.exec_())
