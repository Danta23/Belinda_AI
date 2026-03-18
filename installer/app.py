import sys
import os
import json
import subprocess
import math
import platform
import re
import warnings
from PyQt5.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
                             QLabel, QPushButton, QStackedWidget, QFrame, QGraphicsDropShadowEffect,
                             QLineEdit, QProgressBar, QFileDialog, QSpacerItem, QSizePolicy, QTextEdit, QComboBox)
from PyQt5.QtCore import Qt, QPropertyAnimation, QEasingCurve, QSize, pyqtSignal, QThread, QPoint, QTimer
from PyQt5.QtGui import QColor, QPainter, QLinearGradient, QBrush, QIcon, QPen

# Mute deprecation warnings from PyQt dependencies
warnings.filterwarnings("ignore", category=DeprecationWarning)

# Import styles and settings - Using absolute imports for EXE compatibility
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
                self.progress.emit(5, "status_env")
                
                # --- Setup .env ---
                env_proto = os.path.join(self.root_dir, ".env.example")
                env_file = os.path.join(self.root_dir, ".env")
                if os.path.exists(env_proto) and not os.path.exists(env_file):
                    import shutil
                    shutil.copy(env_proto, env_file)

                if self.api_key:
                    self.sm.set("GROQ_API_KEY", self.api_key)
                
                if self.sm.get("EXECUTION_MODE") == "docker":
                    self.progress.emit(50, "Pulling/Building Docker Containers...")
                    subprocess.run("docker-compose build", cwd=self.root_dir, shell=True, check=True)
                    self.progress.emit(100, "Docker Ready!")
                    self.finished.emit(True, "Installation completed!")
                    return

                # --- Python venv ---
                self.progress.emit(30, "status_venv")
                venv_dir = os.path.join(self.root_dir, ".venv")
                if not os.path.exists(venv_dir):
                    subprocess.run(f'python -m venv "{venv_dir}"', shell=True, check=True)

                # --- pip install ---
                self.progress.emit(60, "status_pip")
                pip_path = os.path.join(self.root_dir, ".venv", "Scripts", "pip") if os.name == 'nt' else os.path.join(self.root_dir, ".venv", "bin", "pip")
                subprocess.run(f'"{pip_path}" install -r requirements.txt', cwd=self.root_dir, shell=True)
                
                # --- npm install ---
                self.progress.emit(80, "status_npm")
                subprocess.run("npm install --no-audit --no-fund", cwd=self.root_dir, shell=True)
                
                self.progress.emit(100, "task_finished")
                self.finished.emit(True, "Installation completed!")

            elif self.task in ["start", "stop", "reset"]:
                script_dir = self.root_dir
                cmd = scripts[self.task]
                if scripts["shell"] == "powershell":
                    cmd = f"powershell -ExecutionPolicy Bypass -File ./{cmd}"
                
                process = subprocess.Popen(cmd, cwd=script_dir, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, shell=True)
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

    def run(self):
        try:
            import shutil
            repo_url = "https://github.com/Danta23/Belinda_AI.git"
            self.progress.emit(10, "status_detecting")
            
            if os.path.exists(self.target_dir) and not os.path.exists(os.path.join(self.target_dir, ".git")):
                try:
                    if not os.listdir(self.target_dir):
                        os.rmdir(self.target_dir)
                except: pass

            self.progress.emit(30, "status_cloning")
            process = subprocess.Popen(
                f"git clone --progress {repo_url} \"{self.target_dir}\"",
                stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, shell=True, universal_newlines=True
            )
            
            while True:
                line = process.stdout.readline()
                if not line and process.poll() is not None: break
                if line:
                    match = re.search(r"(\d+)%", line)
                    if match:
                        percent = int(match.group(1))
                        app_percent = 30 + int(percent * 0.65)
                        self.progress.emit(app_percent, "status_cloning")
            
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

class PageSetup(QWidget):
    def __init__(self, start_clone_callback, get_text_func):
        super().__init__()
        self.get_text = get_text_func
        layout = QVBoxLayout(self)
        layout.setContentsMargins(60, 60, 60, 60)
        layout.setSpacing(30)

        self.title = QLabel("Initial Project Setup")
        self.title.setObjectName("TitleLabel")
        self.title.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.title)

        self.progress_bar = QProgressBar()
        self.progress_bar.setFixedHeight(6)
        self.progress_bar.setVisible(False)
        layout.addWidget(self.progress_bar)

        self.status_label = QLabel("")
        self.status_label.setAlignment(Qt.AlignCenter)
        self.status_label.setStyleSheet("color: #36BCF7;")
        layout.addWidget(self.status_label)

        layout.addStretch()

        self.clone_btn = QPushButton("CLONE & SETUP PROJECT")
        self.clone_btn.setFixedHeight(55)
        self.clone_btn.clicked.connect(start_clone_callback)
        self.clone_btn.setStyleSheet("font-weight: bold; background-color: #36BCF7; color: white;")
        layout.addWidget(self.clone_btn)
        
    def retranslate(self):
        self.title.setText(self.get_text("title_setup"))
        self.clone_btn.setText(self.get_text("btn_clone_now"))

class PageInstaller(QWidget):
    def __init__(self, root_dir, start_task_callback, get_text_func):
        super().__init__()
        self.get_text = get_text_func
        layout = QVBoxLayout(self)
        layout.setContentsMargins(40, 40, 40, 40)
        layout.setSpacing(20)

        self.title = QLabel("System Dashboard")
        self.title.setObjectName("TitleLabel")
        layout.addWidget(self.title)

        self.card = QFrame()
        self.card.setObjectName("Card")
        card_layout = QVBoxLayout(self.card)
        
        self.status_label = QLabel("System Status: Ready")
        card_layout.addWidget(self.status_label)
        
        self.progress_bar = QProgressBar()
        self.progress_bar.setFixedHeight(10)
        card_layout.addWidget(self.progress_bar)
        layout.addWidget(self.card)

        self.warning_label = QLabel("")
        self.warning_label.setStyleSheet("color: #FF4B4B; font-weight: bold;")
        self.warning_label.setWordWrap(True)
        self.warning_label.setVisible(False)
        layout.addWidget(self.warning_label)

        btn_layout = QHBoxLayout()
        self.start_btn = QPushButton("START BOT")
        self.start_btn.setFixedHeight(45)
        self.start_btn.clicked.connect(lambda: start_task_callback("start"))
        
        self.stop_btn = QPushButton("STOP BOT")
        self.stop_btn.setFixedHeight(45)
        self.stop_btn.clicked.connect(lambda: start_task_callback("stop"))
        
        self.reset_btn = QPushButton("RESET")
        self.reset_btn.setFixedHeight(45)
        self.reset_btn.clicked.connect(lambda: start_task_callback("reset"))
        
        self.session_btn = QPushButton("RESET SESSION")
        self.session_btn.setFixedHeight(45)
        self.session_btn.clicked.connect(lambda: start_task_callback("session"))

        btn_layout.addWidget(self.start_btn)
        btn_layout.addWidget(self.stop_btn)
        btn_layout.addWidget(self.reset_btn)
        btn_layout.addWidget(self.session_btn)
        layout.addLayout(btn_layout)

        layout.addStretch()

        self.install_btn = QPushButton("FULL DEPLOYMENT / REINSTALL")
        self.install_btn.setFixedHeight(50)
        self.install_btn.clicked.connect(lambda: start_task_callback("install"))
        layout.addWidget(self.install_btn)

    def retranslate(self):
        self.title.setText(self.get_text("title_dashboard"))
        self.start_btn.setText(self.get_text("btn_start"))
        self.stop_btn.setText(self.get_text("btn_stop"))
        self.reset_btn.setText(self.get_text("btn_reset"))
        self.session_btn.setText(self.get_text("btn_reset_session"))
        self.install_btn.setText(self.get_text("btn_deploy"))

    def check_dependencies(self, root_dir):
        has_venv = os.path.exists(os.path.join(root_dir, ".venv"))
        has_node_modules = os.path.exists(os.path.join(root_dir, "node_modules"))
        has_env = os.path.exists(os.path.join(root_dir, ".env"))
        
        missing = []
        if not has_venv: missing.append("Python VENV")
        if not has_node_modules: missing.append("Node modules")
        if not has_env: missing.append(".env Config")
        
        if missing:
            self.warning_label.setText(f"⚠ Missing dependencies: {', '.join(missing)}. Please run FULL DEPLOYMENT.")
            self.warning_label.setVisible(True)
            self.start_btn.setEnabled(False)
        else:
            self.warning_label.setVisible(False)
            self.start_btn.setEnabled(True)

class PageLogs(QWidget):
    def __init__(self, root_dir, get_text_func):
        super().__init__()
        self.get_text = get_text_func
        layout = QVBoxLayout(self)
        self.title = QLabel("System Console")
        self.title.setObjectName("TitleLabel")
        layout.addWidget(self.title)
        self.log_view = QTextEdit()
        self.log_view.setReadOnly(True)
        layout.addWidget(self.log_view)
        self.tailer = LogTailer(root_dir)
        self.tailer.new_log.connect(lambda t: self.log_view.insertPlainText(t))
        self.tailer.start()
    def retranslate(self):
        self.title.setText(self.get_text("title_console"))

class PageSettings(QWidget):
    def __init__(self, settings_mgr, reload_callback, get_text_func):
        super().__init__()
        self.sm = settings_mgr
        self.reload_callback = reload_callback
        self.get_text = get_text_func
        layout = QVBoxLayout(self)
        self.title = QLabel("Application Config")
        self.title.setObjectName("TitleLabel")
        layout.addWidget(self.title)
        self.save_btn = QPushButton("SAVE & APPLY CHANGES")
        self.save_btn.setFixedHeight(50)
        self.save_btn.clicked.connect(self.reload_callback)
        layout.addWidget(self.save_btn)
    def retranslate(self):
        self.title.setText(self.get_text("title_config"))
        self.save_btn.setText(self.get_text("btn_save"))

class BelindaSetup(QMainWindow):
    def __init__(self):
        super().__init__()
        if getattr(sys, 'frozen', False):
            base_dir = os.path.dirname(sys.executable)
        else:
            base_dir = os.path.dirname(os.path.abspath(__file__))
            
        # Target Belinda_AI subfolder for project files
        self.root_dir = os.path.join(base_dir, "Belinda_AI")
        # Use base_dir for installer settings
        self.sm = SettingsManager(base_dir)
        
        self.setWindowFlags(Qt.FramelessWindowHint)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setMinimumSize(1000, 720)
        self._drag_pos = QPoint()

        self.init_ui()
        self.apply_theme()
        
        # Enable sidebar so terminate button always works
        self.sidebar.setEnabled(True)
        
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
        os.makedirs(self.root_dir, exist_ok=True)
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
        self.main_layout.setContentsMargins(10, 10, 10, 10)

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
        api_key = None
        if task == "install":
            from PyQt5.QtWidgets import QInputDialog, QLineEdit
            key, ok = QInputDialog.getText(self, self.get_text("prompt_api_title"), self.get_text("prompt_api_desc"), QLineEdit.Password, "")
            if not ok or not key.strip(): return
            api_key = key.strip()

        self.worker = Worker(task, self.root_dir, self.sm, api_key)
        self.worker.progress.connect(self.update_progress)
        self.worker.finished.connect(self.task_finished)
        self.worker.start()
        self.set_controls_enabled(False)

    def set_controls_enabled(self, enabled):
        self.page_installer.install_btn.setEnabled(enabled)
        self.page_installer.start_btn.setEnabled(enabled)

    def update_progress(self, val, msg):
        self.page_installer.progress_bar.setValue(val)
        self.page_installer.status_label.setText(self.get_text(msg))

    def task_finished(self, success, msg):
        self.page_installer.status_label.setText(self.get_text(msg))
        self.page_installer.check_dependencies(self.root_dir)
        self.set_controls_enabled(True)

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self._drag_pos = event.globalPos() - self.frameGeometry().topLeft()
            event.accept()

    def mouseMoveEvent(self, event):
        if event.buttons() == Qt.LeftButton:
            self.move(event.globalPos() - self._drag_pos)
            event.accept()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = BelindaSetup()
    window.show()
    sys.exit(app.exec_())
