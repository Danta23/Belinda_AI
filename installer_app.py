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
                        # File was likely cleared or truncated
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
            self.msleep(200) # Faster refresh for real-time console feel

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
    log_output = pyqtSignal(str) # New signal for direct log streaming

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
                "start": "docker-compose up -d --build",
                "stop": "docker-compose down",
                "reset": "docker-compose down -v",
                "shell": "docker"
            }
            
        if os_name == "windows":
            return {"start": "start.ps1", "stop": "stop.ps1", "reset": "reset.ps1", "shell": "powershell"}
        elif os_name == "darwin":
            return {"start": "start_mac.sh", "stop": "stop_mac.sh", "reset": "reset_mac.sh", "session": "rm -rf auth_info", "shell": "sh"}
        else:
            shell_env = os.environ.get("SHELL", "").lower()
            if "fish" in shell_env:
                return {"start": "start.fish", "stop": "stop.fish", "reset": "reset.fish", "session": "rm -rf auth_info", "shell": "fish"}
            else:
                return {"start": "start.sh", "stop": "stop.sh", "reset": "reset.sh", "session": "rm -rf auth_info", "shell": "sh"}

    def run(self):
        scripts = self.get_scripts()
        log_file = os.path.join(self.root_dir, "task.log")
        session_folder = os.path.join(self.root_dir, os.getenv("SESSION_NAME", "auth_info"))
        
        # Try to clear log file, otherwise just append (avoid PermissionError)
        try:
            if os.path.exists(log_file):
                # Don't delete if we can't, just mark the start
                with open(log_file, 'a', encoding='utf-8') as f:
                    f.write(f"\n\n--- NEW TASK: {self.task.upper()} ---\n")
            else:
                with open(log_file, 'w', encoding='utf-8') as f:
                    f.write(f"--- Task Started: {self.task} ---\n")
        except:
            pass # Continue even if log reset fails

        try:
            if self.task == "install":
                self.progress.emit(10, "status_env")
                env_proto = os.path.join(self.root_dir, ".env.example")
                env_file = os.path.join(self.root_dir, ".env")
                if os.path.exists(env_proto) and not os.path.exists(env_file):
                    import shutil
                    shutil.copy(env_proto, env_file)

                if self.api_key:
                    self.sm.set("GROQ_API_KEY", self.api_key)
                
                if self.sm.get("EXECUTION_MODE") == "docker":
                    self.progress.emit(50, "Pulling/Building Docker Containers...")
                    subprocess.run(["docker-compose", "build"], cwd=self.root_dir, shell=True, check=True)
                    self.progress.emit(100, "Docker Ready!")
                    self.finished.emit(True, "Installation completed!")
                    return

                self.progress.emit(30, "status_venv")
                if not os.path.exists(os.path.join(self.root_dir, ".venv")):
                    # Find system python (sys.executable is the EXE when frozen)
                    py_cmd = "python"
                    try:
                        subprocess.run([py_cmd, "--version"], capture_output=True, check=True, shell=True)
                    except:
                        py_cmd = "python3"
                        try:
                            subprocess.run([py_cmd, "--version"], capture_output=True, check=True, shell=True)
                        except:
                            self.finished.emit(False, "System Python not found! Please install Python 3.10+ and add it to PATH.")
                            return
                    
                    subprocess.run([py_cmd, "-m", "venv", ".venv"], cwd=self.root_dir, check=True, shell=True)
                
                self.progress.emit(60, "status_pip")
                pip_path = os.path.join(self.root_dir, ".venv", "Scripts", "pip") if os.name == 'nt' else os.path.join(self.root_dir, ".venv", "bin", "pip")
                # Upgrade pip first
                subprocess.run([pip_path, "install", "--upgrade", "pip"], cwd=self.root_dir, check=False, shell=True)
                # Install requirements
                pip_proc = subprocess.run([pip_path, "install", "-r", "requirements.txt"], cwd=self.root_dir, capture_output=True, text=True, shell=True)
                with open(log_file, 'a', encoding='utf-8') as f:
                    f.write("\n--- PIP INSTALL ---\n" + (pip_proc.stdout or "") + (pip_proc.stderr or ""))
                
                self.progress.emit(80, "status_npm")
                npm_proc = subprocess.run(["npm", "install", "--no-audit", "--no-fund"], cwd=self.root_dir, shell=True, capture_output=True, text=True)
                with open(log_file, 'a', encoding='utf-8') as f:
                    f.write("\n--- NPM INSTALL ---\n" + npm_proc.stdout + npm_proc.stderr)
                
                if pip_proc.returncode != 0 or npm_proc.returncode != 0:
                    self.finished.emit(False, "Dependency installation failed. Check Console for details.")
                    return
                
                self.progress.emit(100, "task_finished")
                self.finished.emit(True, "Installation completed!")
            
            elif self.task == "session":
                self.progress.emit(50, "Clearing session data...")
                session_dir = os.path.join(self.root_dir, os.getenv("SESSION_NAME", "auth_info"))
                if os.path.exists(session_dir):
                    import shutil
                    try:
                        shutil.rmtree(session_dir)
                        self.progress.emit(100, "Session cleared!")
                        self.finished.emit(True, "Session reset successfully! You can now scan a new QR code.")
                    except Exception as e:
                        self.finished.emit(False, f"Failed to reset session: {str(e)}")
                else:
                    self.finished.emit(True, "No session data found to clear.")
            
            elif self.task in ["start", "stop", "reset"]:
                if scripts["shell"] == "docker":
                    cmd = scripts[self.task]
                    self.progress.emit(50, f"Executing Docker: {self.task}...")
                else:
                    script_name = scripts[self.task]
                    self.progress.emit(20, f"Preparing {script_name}...")
                    
                    if scripts["shell"] == "powershell":
                        cmd = f"powershell -ExecutionPolicy Bypass -File ./{script_name}"
                    else:
                        subprocess.run(["chmod", "+x", script_name], cwd=self.root_dir)
                        cmd = f"./{script_name}"
                
                self.log_output.emit(f"> Executing: {cmd}\n")
                
                # Use subprocess.Popen to capture output real-time
                process = subprocess.Popen(
                    cmd,
                    cwd=self.root_dir,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.STDOUT,
                    text=True,
                    encoding='utf-8',
                    errors='replace',
                    bufsize=1,
                    universal_newlines=True,
                    shell=True
                )

                # Capture output loop
                current_prog = 20
                is_connected = False
                while True:
                    line = process.stdout.readline()
                    if not line and process.poll() is not None:
                        break
                    if line:
                        self.log_output.emit(line)
                        
                        # Dynamic progress ramping
                        if not is_connected and current_prog < 90:
                            if "Starting" in line or "Found" in line or "using WA" in line:
                                current_prog += 15
                            else:
                                current_prog += 1
                            self.progress.emit(min(current_prog, 95), "starting_ai")

                        # Success detection for Bridge
                        if "BELINDA ONLINE" in line or "Bridge" in line.split() and "online" in line.lower():
                            if not is_connected:
                                self.progress.emit(100, "bot_online")
                                self.finished.emit(True, "task_finished")
                                is_connected = True
                                # We continue the loop to keep logs flowing

                        # Log to file safely
                        try:
                            with open(log_file, 'a', encoding='utf-8', errors='ignore') as f:
                                f.write(line)
                        except: pass
                
                process.stdout.close()
                rc = process.wait()

                if not is_connected:
                    self.progress.emit(100, "task_finished")
                    self.finished.emit(True, "task_finished")

        except Exception as e:
            with open(log_file, 'a', encoding='utf-8') as f:
                f.write(f"\n[ERROR] {str(e)}\n")
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
            
            parent_dir = os.path.dirname(self.target_dir)
            if not os.path.exists(parent_dir):
                os.makedirs(parent_dir, exist_ok=True)

            self.progress.emit(30, "status_cloning")
            
            # Robust check: If folder exists but is not a git repo, or is empty, remove and re-clone
            is_valid_repo = os.path.exists(os.path.join(self.target_dir, ".git"))
            if os.path.exists(self.target_dir) and not is_valid_repo:
                try:
                    shutil.rmtree(self.target_dir)
                except:
                    # If rmtree fails (e.g. file in use), try to at least clear what we can
                    pass

            if not os.path.exists(self.target_dir):
                self.progress.emit(40, "status_cloning")
                # Use --progress to force progress output even if not a terminal
                process = subprocess.Popen(
                    f"git clone --progress {repo_url} \"{self.target_dir}\"",
                    stdout=subprocess.PIPE,
                    stderr=subprocess.STDOUT,
                    text=True,
                    shell=True,
                    bufsize=1,
                    universal_newlines=True
                )
                
                while True:
                    line = process.stdout.readline()
                    if not line and process.poll() is not None:
                        break
                    if line:
                        # Parse git progress e.g. "Receiving objects:  95% (123/129)"
                        match = re.search(r"(\d+)%", line)
                        if match:
                            percent = int(match.group(1))
                            # Map 0-100 git progress to 40-95 app progress
                            app_percent = 40 + int(percent * 0.55)
                            self.progress.emit(app_percent, "status_cloning")
                
                process.wait()
                if process.returncode != 0:
                    self.finished.emit(False, "clone_fail")
                    return
            
            # Verify cloning succeeded
            if not os.path.exists(os.path.join(self.target_dir, "bridge.js")):
                self.finished.emit(False, "clone_incomplete")
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

        self.desc = QLabel("Welcome to Belinda AI! We need to setup the project files to continue.")
        self.desc.setWordWrap(True)
        self.desc.setAlignment(Qt.AlignCenter)
        self.desc.setStyleSheet("color: rgba(255,255,255,0.6); font-size: 14px;")
        layout.addWidget(self.desc)

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
        self.clone_btn.setCursor(Qt.PointingHandCursor)
        self.clone_btn.clicked.connect(start_clone_callback)
        self.clone_btn.setStyleSheet("font-weight: bold; font-size: 16px; background-color: #36BCF7; color: white;")
        layout.addWidget(self.clone_btn)
        
        self.retranslate()

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
        card_layout.setContentsMargins(25, 25, 25, 25)
        
        self.status_label = QLabel("System Status: Ready")
        card_layout.addWidget(self.status_label)
        
        self.progress_bar = QProgressBar()
        self.progress_bar.setValue(0)
        self.progress_bar.setFixedHeight(10)
        card_layout.addWidget(self.progress_bar)
        
        layout.addWidget(self.card)

        self.warning_label = QLabel("")
        self.warning_label.setStyleSheet("color: #FF4B4B; font-weight: bold;")
        self.warning_label.setWordWrap(True)
        self.warning_label.setVisible(False)
        layout.addWidget(self.warning_label)

        btn_layout = QHBoxLayout()
        btn_layout.setSpacing(15)

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
        self.session_btn.setStyleSheet("QPushButton { color: #FF9800; border-color: rgba(255, 152, 0, 0.3); }")
        self.session_btn.clicked.connect(lambda: start_task_callback("session"))

        btn_layout.addWidget(self.start_btn)
        btn_layout.addWidget(self.stop_btn)
        btn_layout.addWidget(self.reset_btn)
        btn_layout.addWidget(self.session_btn)
        layout.addLayout(btn_layout)

        layout.addStretch()

        self.install_btn = QPushButton("FULL DEPLOYMENT / REINSTALL")
        self.install_btn.setFixedHeight(50)
        self.install_btn.setCursor(Qt.PointingHandCursor)
        self.install_btn.clicked.connect(lambda: start_task_callback("install"))
        layout.addWidget(self.install_btn)
        self.retranslate()

    def retranslate(self):
        self.title.setText(self.get_text("title_dashboard"))
        self.status_label.setText(self.get_text("status_ready"))
        self.start_btn.setText(self.get_text("btn_start"))
        self.stop_btn.setText(self.get_text("btn_stop"))
        self.reset_btn.setText(self.get_text("btn_reset"))
        self.session_btn.setText(self.get_text("btn_reset_session"))
        self.install_btn.setText(self.get_text("btn_deploy"))

    def check_dependencies(self, root_dir):
        # Quick check for .venv and node_modules
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
            self.status_label.setText("Status: Settings Needed")
        else:
            self.warning_label.setVisible(False)
            self.start_btn.setEnabled(True)
            self.status_label.setText(self.get_text("status_ready"))

class PageLogs(QWidget):
    def __init__(self, root_dir, get_text_func):
        super().__init__()
        self.get_text = get_text_func
        layout = QVBoxLayout(self)
        layout.setContentsMargins(40, 40, 40, 40)
        
        self.title = QLabel("System Console")
        self.title.setObjectName("TitleLabel")
        layout.addWidget(self.title)

        self.log_view = QTextEdit()
        self.log_view.setReadOnly(True)
        self.log_view.setStyleSheet("background-color: rgba(0,0,0,150); color: #00FF00; font-family: 'Consolas', monospace; font-size: 11px; border-radius: 10px; padding: 10px;")
        layout.addWidget(self.log_view)

        self.clear_btn = QPushButton("Clear Console")
        self.clear_btn.clicked.connect(self.log_view.clear)
        layout.addWidget(self.clear_btn)

        self.tailer = LogTailer(root_dir)
        self.tailer.new_log.connect(self.append_log)
        self.tailer.start()
        self.retranslate()

    def retranslate(self):
        self.title.setText(self.get_text("title_console"))
        self.clear_btn.setText(self.get_text("btn_clear_console"))

    def append_log(self, text):
        # Detect QR Code patterns in text
        cursor = self.log_view.textCursor()
        cursor.movePosition(cursor.End)
        self.log_view.setTextCursor(cursor)
        self.log_view.insertPlainText(text)
        self.log_view.verticalScrollBar().setValue(self.log_view.verticalScrollBar().maximum())

class PageSettings(QWidget, ):
    def __init__(self, settings_mgr, reload_callback, get_text_func):
        super().__init__()
        self.sm = settings_mgr
        self.reload_callback = reload_callback
        self.get_text = get_text_func
        layout = QVBoxLayout(self)
        layout.setContentsMargins(40, 40, 40, 40)
        layout.setSpacing(10)

        self.title = QLabel("Application Config")
        self.title.setObjectName("TitleLabel")
        layout.addWidget(self.title)

        from PyQt5.QtWidgets import QScrollArea
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("background: transparent; border: none;")
        
        content = QWidget()
        content.setStyleSheet("background: transparent;")
        self.form_layout = QVBoxLayout(content)
        self.form_layout.setSpacing(10)

        self.inputs = {}
        self.sections = []
        self.labels = {}
        
        # UI Appearance
        self.sections.append(self.add_section("section_ui", "fa5s.palette"))
        self.labels["APP_THEME"] = self.add_combo("APP_THEME", "lbl_theme", ["dark", "light"])
        self.labels["APP_FONT_FAMILY"] = self.add_field("APP_FONT_FAMILY", "lbl_font", "Segoe UI")
        self.labels["APP_FONT_SIZE"] = self.add_field("APP_FONT_SIZE", "lbl_font_size", "14")
        self.labels["APP_TITLE_SIZE"] = self.add_field("APP_TITLE_SIZE", "lbl_title_size", "24")
        
        # Localization
        self.sections.append(self.add_section("section_loc", "fa5s.language"))
        self.labels["APP_LANGUAGE"] = self.add_combo("APP_LANGUAGE", "lbl_lang", ["English", "Indonesian", "Japanese"])

        # Deployment
        self.sections.append(self.add_section("section_deployment", "fa5s.rocket"))
        modes = ["local"]
        if self.parent().parent().parent().check_docker() if hasattr(self, "parent") and self.parent() else True:
            # We'll just check it dynamically in init_ui of Setup actually
            pass
        
        # Simpler check: check once and store
        is_docker = False
        try:
            subprocess.run(["docker", "--version"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)
            is_docker = True
        except: pass
        
        modes = ["local", "docker"] if is_docker else ["local"]
        self.labels["EXECUTION_MODE"] = self.add_combo("EXECUTION_MODE", "lbl_execution_mode", modes)

        # AI Identity
        self.sections.append(self.add_section("section_ai", "fa5s.robot"))
        self.labels["AI_NAME"] = self.add_field("AI_NAME", "lbl_ai_name", "Belinda AI")
        self.labels["AI_PERSONALITY"] = self.add_field("AI_PERSONALITY", "lbl_ai_personality", "Intelligent assistant", is_large=True)
        self.labels["AI_MAX_TOKENS"] = self.add_field("AI_MAX_TOKENS", "lbl_ai_tokens", "1024")

        scroll.setWidget(content)
        layout.addWidget(scroll)

        self.save_btn = QPushButton("SAVE & APPLY CHANGES")
        self.save_btn.setFixedHeight(50)
        self.save_btn.clicked.connect(self.save_all)
        layout.addWidget(self.save_btn)
        self.retranslate()

    def add_section(self, text_key, icon=None):
        lbl = QLabel(self.get_text(text_key))
        lbl.setStyleSheet("font-weight: bold; color: #36BCF7; margin-top: 15px; border-bottom: 1px solid rgba(54,188,247,0.3);")
        self.form_layout.addWidget(lbl)
        return (lbl, text_key)

    def add_field(self, key, label_key, placeholder, is_large=False):
        lbl = QLabel(self.get_text(label_key))
        self.form_layout.addWidget(lbl)
        if is_large:
            edit = QTextEdit()
            edit.setPlaceholderText(placeholder)
            edit.setPlainText(self.sm.get(key))
            edit.setFixedHeight(80)
            edit.setStyleSheet("background-color: rgba(0,0,0,50); border: 1px solid rgba(255,255,255,10); border-radius: 6px; color: white; padding: 8px;")
        else:
            edit = QLineEdit()
            edit.setPlaceholderText(placeholder)
            edit.setText(self.sm.get(key))
            edit.setStyleSheet("background-color: rgba(0,0,0,50); border: 1px solid rgba(255,255,255,10); border-radius: 6px; color: white; padding: 8px;")
        
        self.form_layout.addWidget(edit)
        self.inputs[key] = edit
        return (lbl, label_key)

    def add_combo(self, key, label_key, options):
        lbl = QLabel(self.get_text(label_key))
        self.form_layout.addWidget(lbl)
        combo = QComboBox()
        combo.addItems(options)
        combo.setCurrentText(self.sm.get(key))
        combo.setStyleSheet("background-color: rgba(0,0,0,50); color: white; border: 1px solid rgba(255,255,255,10); border-radius: 6px; padding: 5px;")
        self.form_layout.addWidget(combo)
        self.inputs[key] = combo
        return (lbl, label_key)

    def retranslate(self):
        self.title.setText(self.get_text("title_config"))
        self.save_btn.setText(self.get_text("btn_save"))
        for lbl, key in self.sections:
            lbl.setText(self.get_text(key))
        for key, (lbl, label_key) in self.labels.items():
            lbl.setText(self.get_text(label_key))

    def save_all(self):
        for k, widget in self.inputs.items():
            if isinstance(widget, QComboBox):
                val = widget.currentText()
            else:
                val = widget.toPlainText() if isinstance(widget, QTextEdit) else widget.text()
            self.sm.set(k, val)
        self.save_btn.setText(self.get_text("btn_saving"))
        QTimer.singleShot(1000, self.reload_callback)

class BelindaSetup(QMainWindow):
    def __init__(self):
        super().__init__()
        # Dynamic path detection for both DEV and COMPILED (EXE) modes
        if getattr(sys, 'frozen', False):
            # Run as bundled EXE
            base_dir = os.path.dirname(sys.executable)
        else:
            # Run as script
            base_dir = os.path.dirname(os.path.abspath(__file__))
            
        if os.path.basename(base_dir) == "installer":
            self.root_dir = os.path.dirname(base_dir)
        else:
            # If EXE is in a separate folder, look for Belinda_AI next to it
            self.root_dir = os.path.join(base_dir, "Belinda_AI")
            
        self.sm = SettingsManager(self.root_dir)
        
        self.setWindowFlags(Qt.FramelessWindowHint)
        self.setAttribute(Qt.WA_TranslucentBackground)
        
        self.setMinimumSize(1000, 720)
        self._drag_pos = QPoint()

        self.init_ui()
        self.apply_theme()
        
        # Check if project exists, if not, show setup
        if not self.is_project_ready():
            self.content_area.setCurrentWidget(self.page_setup)
            self.sidebar.setEnabled(False)
        else:
            self.sidebar.setEnabled(True)
            self.content_area.setCurrentIndex(1) # Dashboard
            self.page_installer.check_dependencies(self.root_dir)

    def is_project_ready(self):
        # Look for the root folder and bridge.js precisely
        return os.path.exists(os.path.join(self.root_dir, "bridge.js"))

    def check_docker(self):
        try:
            subprocess.run(["docker", "--version"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)
            return True
        except:
            return False

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

    def setup_finished(self, success, msg_key):
        if success:
            # Reload settings from the newly cloned folder
            self.sm = SettingsManager(self.root_dir)
            self.sidebar.setEnabled(True)
            # Switch to Dashboard (index 1 in QStackedWidget)
            self.content_area.setCurrentIndex(1)
            # Clear active buttons and set Dashboard as active
            for btn in self.btns:
                btn.setProperty("active", "false")
                btn.setStyle(btn.style())
            self.btns[0].setProperty("active", "true")
            self.btns[0].setStyle(self.btns[0].style())
            self.retranslate_all()
        else:
            self.page_setup.status_label.setText(self.get_text(msg_key))
            self.page_setup.clone_btn.setEnabled(True)

    def init_ui(self):
        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        
        self.main_layout = QHBoxLayout(self.central_widget)
        self.main_layout.setContentsMargins(10, 10, 10, 10)

        self.bg_widget = FluidGradientWidget()
        self.bg_widget.setObjectName("MainFrame")
        self.container_layout = QHBoxLayout(self.bg_widget)
        self.container_layout.setContentsMargins(0, 0, 0, 0)
        self.container_layout.setSpacing(0)
        self.main_layout.addWidget(self.bg_widget)

        self.sidebar = QFrame()
        self.sidebar.setObjectName("Sidebar")
        self.sidebar.setFixedWidth(240)
        self.sidebar_layout = QVBoxLayout(self.sidebar)
        self.sidebar_layout.setContentsMargins(20, 40, 20, 40)
        self.sidebar_layout.setSpacing(12)
        
        logo = QLabel("BELINDA")
        logo.setStyleSheet("font-size: 24px; font-weight: 900; color: #36BCF7; letter-spacing: 2px;")
        logo.setAlignment(Qt.AlignCenter)
        self.sidebar_layout.addWidget(logo)
        
        self.sub_logo = QLabel("AI ECOSYSTEM")
        self.sub_logo.setStyleSheet("font-size: 10px; font-weight: bold; color: rgba(255,255,255,0.4); margin-top: -10px;")
        self.sub_logo.setAlignment(Qt.AlignCenter)
        self.sidebar_layout.addWidget(self.sub_logo)
        
        self.sidebar_layout.addSpacing(30)

        import qtawesome as qta
        self.btns = []
        self.add_nav_button("nav_dashboard", "fa5s.tachometer-alt", 0)
        self.add_nav_button("nav_console", "fa5s.terminal", 1)
        self.add_nav_button("nav_config", "fa5s.tools", 2)

        self.sidebar_layout.addStretch()
        
        self.exit_btn = QPushButton("TERMINATE")
        self.exit_btn.setStyleSheet("QPushButton { color: #FF4B4B; border-color: rgba(255,75,75,0.2); font-weight: bold; }")
        self.exit_btn.clicked.connect(self.close)
        self.sidebar_layout.addWidget(self.exit_btn)

        self.container_layout.addWidget(self.sidebar)

        self.content_area = QStackedWidget()
        self.page_setup = PageSetup(self.start_setup_clone, self.get_text)
        self.page_installer = PageInstaller(self.root_dir, self.start_worker_task, self.get_text)
        self.page_logs = PageLogs(self.root_dir, self.get_text)
        self.page_settings = PageSettings(self.sm, self.apply_changes, self.get_text)
        
        self.content_area.addWidget(self.page_setup) # Index 0 initially if needed
        self.content_area.addWidget(self.page_installer)
        self.content_area.addWidget(self.page_logs)
        self.content_area.addWidget(self.page_settings)
        
        self.container_layout.addWidget(self.content_area)

        shadow = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(40)
        shadow.setXOffset(0)
        shadow.setYOffset(15)
        shadow.setColor(QColor(0, 0, 0, 180))
        self.bg_widget.setGraphicsEffect(shadow)

    def get_text(self, key):
        lang = self.sm.get("APP_LANGUAGE", "English")
        return TRANSLATIONS.get(lang, TRANSLATIONS["English"]).get(key, key)

    def add_nav_button(self, text_key, icon_name, index):
        import qtawesome as qta
        btn = QPushButton(self.get_text(text_key))
        btn.setObjectName("NavButton")
        btn.setProperty("text_key", text_key)
        btn.setIcon(qta.icon(icon_name, color="#36BCF7"))
        btn.setIconSize(QSize(18, 18))
        btn.clicked.connect(lambda: self.switch_page(index))
        self.sidebar_layout.addWidget(btn)
        self.btns.append(btn)
        if index == 0: btn.setProperty("active", "true")

    def switch_page(self, index):
        # We start indices at 1 for dashboard etc because setup is index 0
        real_index = index + 1
        for i, btn in enumerate(self.btns):
            btn.setProperty("active", "true" if i == index else "false")
            btn.setStyle(btn.style())
        self.content_area.setCurrentIndex(real_index)

    def apply_changes(self):
        # Full UI Refresh for theme and language
        self.apply_theme()
        self.retranslate_all()

    def retranslate_all(self):
        self.sub_logo.setText(self.get_text("ai_eco"))
        self.exit_btn.setText(self.get_text("terminate"))
        for btn in self.btns:
            key = btn.property("text_key")
            if key:
                btn.setText(self.get_text(key))
        
        self.page_setup.retranslate()
        self.page_installer.retranslate()
        self.page_logs.retranslate()
        self.page_settings.retranslate()

    def apply_theme(self):
        theme = self.sm.get("APP_THEME", "dark")
        font_family = self.sm.get("APP_FONT_FAMILY", "Segoe UI")
        font_size = self.sm.get("APP_FONT_SIZE", "14")
        title_size = self.sm.get("APP_TITLE_SIZE", "24")
        
        self.bg_widget.dark_mode = (theme == "dark")
        template = DARK_STYLE_TEMPLATE if theme == "dark" else LIGHT_STYLE_TEMPLATE
        
        style = template.format(
            font_family=font_family,
            font_size=font_size,
            title_size=title_size
        )
        self.setStyleSheet(style)
        QApplication.instance().setStyleSheet(style)
        self.page_settings.save_btn.setText("SAVE & APPLY CHANGES")

    def start_worker_task(self, task):
        api_key = None
        if task == "install":
            current_key = self.sm.get("GROQ_API_KEY", "")
            if not current_key:
                from PyQt5.QtWidgets import QInputDialog, QLineEdit
                key, ok = QInputDialog.getText(
                    self, 
                    self.get_text("prompt_api_title"),
                    self.get_text("prompt_api_desc"),
                    QLineEdit.Password,
                    ""
                )
                if not ok or not key.strip():
                    return
                api_key = key.strip()

        self.worker = Worker(task, self.root_dir, self.sm, api_key)
        self.worker.progress.connect(self.update_progress)
        self.worker.finished.connect(self.task_finished)
        self.worker.start()
        self.set_controls_enabled(False)

    def set_controls_enabled(self, enabled):
        self.page_installer.install_btn.setEnabled(enabled)
        self.page_installer.start_btn.setEnabled(enabled)
        self.page_installer.stop_btn.setEnabled(enabled)
        self.page_installer.reset_btn.setEnabled(enabled)
        self.page_installer.session_btn.setEnabled(enabled)

    def update_progress(self, val, msg_key_or_raw):
        # Try to translate if it's a known key, otherwise use raw
        msg = self.get_text(msg_key_or_raw)
        self.page_installer.progress_bar.setValue(val)
        self.page_installer.status_label.setText(msg)

    def task_finished(self, success, msg_key_or_raw):
        msg = self.get_text(msg_key_or_raw)
        self.page_installer.status_label.setText(msg)
        self.page_installer.progress_bar.setValue(100) 
        self.set_controls_enabled(True)
        self.page_installer.check_dependencies(self.root_dir)

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
    try:
        window = BelindaSetup()
        window.show()
        sys.exit(app.exec_())
    except Exception as e:
        from PyQt5.QtWidgets import QMessageBox
        msg = QMessageBox()
        msg.setIcon(QMessageBox.Critical)
        msg.setText("Application Critical Error")
        msg.setInformativeText(str(e))
        msg.setWindowTitle("Error")
        msg.exec_()
