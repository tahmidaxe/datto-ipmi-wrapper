import sys
import os
import json
import traceback
import platform
import subprocess
from PyQt6.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QLineEdit, QPushButton, QProgressBar, QMessageBox, QFrame,
    QFormLayout, QCheckBox, QStackedWidget
)
from PyQt6.QtCore import Qt, QThread, pyqtSignal, QTimer
from PyQt6.QtGui import QFont, QIcon, QColor, QPalette, QWindow

from fetcher import Fetcher
from extractor import Extractor
from executor import Executor
from jre_manager import JREManager

try:
    import win32gui
except ImportError:
    win32gui = None

CONFIG_FILE = "config.json"

class DownloadThread(QThread):
    progress = pyqtSignal(int, str)
    error = pyqtSignal(str)
    finished_download = pyqtSignal(str) # Emits the path to java_exe

    def __init__(self, ip):
        super().__init__()
        self.ip = ip

    def run(self):
        try:
            self.progress.emit(0, "Ensuring Standalone JRE is available...")
            jre_mgr = JREManager()
            java_path = jre_mgr.ensure_jre(lambda p: self.progress.emit(p, "Downloading portable JRE..."))
            
            fetcher = Fetcher(self.ip)
            
            self.progress.emit(0, "Downloading avctKVM.jar...")
            main_jar = fetcher.download_jar("avctKVM.jar", lambda p: self.progress.emit(p, "Downloading avctKVM.jar..."))
            
            # Determine correct native jar based on os
            system = platform.system()
            machine = platform.machine().lower()
            native_jar_name = ""
            
            if system == "Windows":
                native_jar_name = "avctKVMIOWin64.jar" if "64" in machine or machine == "amd64" else "avctKVMIOWin32.jar"
            elif system == "Linux":
                if "64" in machine or machine == "amd64" or machine == "x86_64":
                    native_jar_name = "avctKVMIOLinux64.jar"
                else:
                    native_jar_name = "avctKVMIOLinux32.jar"
            elif system == "Darwin":
                native_jar_name = "avctKVMIOMac64.jar"
            else:
                self.error.emit(f"Unsupported OS: {system}")
                return
            
            self.progress.emit(0, f"Downloading {native_jar_name}...")
            native_jar = fetcher.download_jar(native_jar_name, lambda p: self.progress.emit(p, f"Downloading {native_jar_name}..."))
            
            self.progress.emit(100, "Extracting native libraries...")
            extractor = Extractor()
            extractor.extract_native_libs(native_jar)
            
            self.progress.emit(100, "Ready to launch!")
            self.finished_download.emit(java_path)
            
        except Exception as e:
            self.error.emit(str(e))
            traceback.print_exc()

class LoginWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Datto IPMI Viewer Launcher")
        self.resize(450, 400)
        
        # Determine paths properly when frozen (PyInstaller)
        if getattr(sys, 'frozen', False):
            base_path = sys._MEIPASS
        else:
            base_path = os.path.dirname(os.path.abspath(__file__))
            
        icon_path = os.path.join(base_path, 'app_icon.ico')
        if os.path.exists(icon_path):
            self.setWindowIcon(QIcon(icon_path))
            
        self.target_ip = ""
        self.setup_ui()
        self.load_config()
        
        self.embed_timer = QTimer(self)
        self.embed_timer.timeout.connect(self.check_java_window)
        self.embed_attempts = 0

    def setup_ui(self):
        # Modern styling with Dark Mode
        app_palette = self.palette()
        app_palette.setColor(QPalette.ColorRole.Window, QColor(30, 30, 30))
        app_palette.setColor(QPalette.ColorRole.WindowText, Qt.GlobalColor.white)
        app_palette.setColor(QPalette.ColorRole.Base, QColor(45, 45, 45))
        app_palette.setColor(QPalette.ColorRole.Text, Qt.GlobalColor.white)
        app_palette.setColor(QPalette.ColorRole.Button, QColor(53, 53, 53))
        app_palette.setColor(QPalette.ColorRole.ButtonText, Qt.GlobalColor.white)
        self.setPalette(app_palette)
        
        self.root_layout = QVBoxLayout(self)
        self.root_layout.setContentsMargins(0, 0, 0, 0)
        
        self.stacked_widget = QStackedWidget()
        self.root_layout.addWidget(self.stacked_widget)
        
        # --- LOGIN PAGE ---
        self.login_page = QWidget()
        main_layout = QVBoxLayout(self.login_page)
        main_layout.setContentsMargins(40, 40, 40, 40)
        main_layout.setSpacing(20)
        
        title_label = QLabel("Datto IPMI Login")
        title_font = QFont("Segoe UI", 20, QFont.Weight.Bold)
        title_label.setFont(title_font)
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title_label.setStyleSheet("color: #ffffff; margin-bottom: 20px;")
        main_layout.addWidget(title_label)
        
        form_layout = QFormLayout()
        form_layout.setVerticalSpacing(15)
        
        self.ip_input = QLineEdit()
        self.ip_input.setPlaceholderText("192.168.0.5")
        self.style_input(self.ip_input)
        
        self.user_input = QLineEdit()
        self.user_input.setPlaceholderText("admin")
        self.style_input(self.user_input)
        
        self.pass_input = QLineEdit()
        self.pass_input.setPlaceholderText("password")
        self.pass_input.setEchoMode(QLineEdit.EchoMode.Password)
        self.style_input(self.pass_input)
        
        self.save_pass_checkbox = QCheckBox("Save Password")
        self.save_pass_checkbox.setStyleSheet("color: #dddddd; margin-top: 5px;")
        
        form_layout.addRow(self.create_label("IPMI IP:"), self.ip_input)
        form_layout.addRow(self.create_label("Username:"), self.user_input)
        form_layout.addRow(self.create_label("Password:"), self.pass_input)
        form_layout.addRow("", self.save_pass_checkbox)
        
        main_layout.addLayout(form_layout)
        
        self.progress_bar = QProgressBar()
        self.progress_bar.setTextVisible(True)
        self.progress_bar.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.progress_bar.setStyleSheet("""
            QProgressBar {
                border: 1px solid #555;
                border-radius: 5px;
                text-align: center;
                background-color: #2d2d2d;
            }
            QProgressBar::chunk {
                background-color: #0d6efd;
            }
        """)
        self.progress_bar.hide()
        main_layout.addWidget(self.progress_bar)
        
        self.status_label = QLabel("")
        self.status_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.status_label.setStyleSheet("color: #aaaaaa;")
        self.status_label.hide()
        main_layout.addWidget(self.status_label)
        
        self.login_btn = QPushButton("Connect && Launch")
        self.login_btn.setFixedHeight(45)
        self.login_btn.setFont(QFont("Segoe UI", 12, QFont.Weight.Bold))
        self.login_btn.setStyleSheet("""
            QPushButton {
                background-color: #0d6efd;
                color: white;
                border-radius: 6px;
                border: none;
            }
            QPushButton:hover {
                background-color: #0b5ed7;
            }
            QPushButton:pressed {
                background-color: #0a58ca;
            }
            QPushButton:disabled {
                background-color: #6c757d;
                color: #d3d3d3;
            }
        """)
        self.login_btn.clicked.connect(self.on_login)
        main_layout.addWidget(self.login_btn)
        
        self.stacked_widget.addWidget(self.login_page)

    def create_label(self, text):
        lbl = QLabel(text)
        lbl.setFont(QFont("Segoe UI", 11))
        lbl.setStyleSheet("color: #dddddd;")
        return lbl

    def style_input(self, widget):
        widget.setFixedHeight(38)
        widget.setFont(QFont("Segoe UI", 11))
        widget.setStyleSheet("""
            QLineEdit {
                border: 1px solid #555;
                border-radius: 5px;
                padding: 5px 10px;
                background-color: #2d2d2d;
                color: white;
            }
            QLineEdit:focus {
                border: 1px solid #0d6efd;
                background-color: #383838;
            }
        """)

    def load_config(self):
        if os.path.exists(CONFIG_FILE):
            try:
                with open(CONFIG_FILE, "r") as f:
                    data = json.load(f)
                    self.ip_input.setText(data.get("ip", ""))
                    self.user_input.setText(data.get("username", ""))
                    if data.get("save_pass"):
                        self.save_pass_checkbox.setChecked(True)
                        self.pass_input.setText(data.get("password", ""))
            except Exception:
                pass

    def on_login(self):
        ip = self.ip_input.text().strip()
        user = self.user_input.text().strip()
        password = self.pass_input.text().strip()
        
        if not ip or not user or not password:
            QMessageBox.warning(self, "Input Error", "Please fill in all fields.")
            return
            
        self.target_ip = ip
        
        # Save config
        try:
            config_data = {
                "ip": ip,
                "username": user,
                "save_pass": self.save_pass_checkbox.isChecked()
            }
            if self.save_pass_checkbox.isChecked():
                config_data["password"] = password
            else:
                config_data["password"] = ""
                
            with open(CONFIG_FILE, "w") as f:
                json.dump(config_data, f)
        except Exception:
            pass
            
        self.login_btn.setEnabled(False)
        self.progress_bar.setValue(0)
        self.progress_bar.show()
        self.status_label.setText("Starting download...")
        self.status_label.show()
        
        self.thread = DownloadThread(ip)
        self.thread.progress.connect(self.update_progress)
        self.thread.error.connect(self.on_error)
        self.thread.finished_download.connect(lambda java_path: self.launch_viewer(java_path, ip, user, password))
        self.thread.start()

    def update_progress(self, val, text):
        self.progress_bar.setValue(val)
        self.status_label.setText(text)

    def on_error(self, err_msg):
        self.login_btn.setEnabled(True)
        self.progress_bar.hide()
        self.status_label.hide()
        QMessageBox.critical(self, "Error", f"An error occurred:\n{err_msg}")

    def launch_viewer(self, java_path, ip, user, password):
        self.status_label.setText("Launching Java Viewer...")
        try:
            executor = Executor()
            self.viewer_process = executor.run_viewer(java_path, ip, user, password)
            self.status_label.setText("Viewer launched successfully. Embedding window...")
            
            # Start timer to try and embed the Java window
            self.embed_attempts = 0
            self.embed_timer.start(500)
            
        except Exception as e:
            self.on_error(f"Failed to launch viewer:\n{str(e)}")

    def closeEvent(self, event):
        # Kill the java process when the UI closes
        if hasattr(self, 'viewer_process') and self.viewer_process:
            try:
                self.viewer_process.terminate()
            except Exception:
                pass
        event.accept()

    def check_java_window(self):
        if not win32gui:
            self.embed_timer.stop()
            self.status_label.setText("pywin32 not installed. Java Viewer is running externally.")
            # Automatically close or stay open
            return

        self.embed_attempts += 1
        
        # The Java window sets its title to "Video Viewer - <IP>"
        title = f"Video Viewer - {self.target_ip}"
        hwnd = win32gui.FindWindow(None, title)
        
        if hwnd:
            self.embed_timer.stop()
            self.embed_window(hwnd)
        elif self.embed_attempts > 40: # 20 seconds
            self.embed_timer.stop()
            self.status_label.setText("Window not embedded, running externally.")
            self.login_btn.setEnabled(True)

    def embed_window(self, hwnd):
        try:
            self.embedded_hwnd = hwnd
            window = QWindow.fromWinId(hwnd)
            self.video_widget = QWidget.createWindowContainer(window)
            
            # Create a new page in the stacked widget
            self.video_page = QWidget()
            vid_layout = QVBoxLayout(self.video_page)
            vid_layout.setContentsMargins(0, 0, 0, 0)
            vid_layout.addWidget(self.video_widget)
            
            self.stacked_widget.addWidget(self.video_page)
            self.stacked_widget.setCurrentWidget(self.video_page)
            
            self.setWindowTitle(f"Datto KVM - {self.target_ip}")
            # Resize app to fit the KVM nicely
            self.resize(1024, 768)
            
            # The Java KVM client takes several seconds to negotiate the connection.
            # We need to poke the window size periodically so it repaints as soon as the feed goes live.
            self.poke_count = 0
            self.poke_timer = QTimer(self)
            self.poke_timer.timeout.connect(self.poke_window_size)
            self.poke_timer.start(1000) # Every 1 second
            
        except Exception as e:
            self.status_label.setText(f"Failed to embed window: {str(e)}")
            self.login_btn.setEnabled(True)

    def poke_window_size(self):
        self.poke_count += 1
        if self.poke_count > 10: # Stop poking after 10 seconds
            self.poke_timer.stop()
            return
            
        # Physically alter the window size by 1 pixel to force the layout engine and Java
        # to process a real resize event through the entire stack, fixing the grey screen.
        w, h = self.width(), self.height()
        self.resize(w, h + 1)
        QTimer.singleShot(100, lambda: self.resize(w, h))

    # Keep trigger_java_repaint around for normal resize events
    def trigger_java_repaint(self):
        if hasattr(self, 'embedded_hwnd') and self.embedded_hwnd and win32gui:
            # Send a fake resize event to the Java window to force it to render its buffer
            # SWP_NOMOVE | SWP_NOSIZE | SWP_NOZORDER | SWP_FRAMECHANGED
            try:
                import win32con
                win32gui.SetWindowPos(self.embedded_hwnd, 0, 0, 0, 0, 0, 
                    win32con.SWP_NOMOVE | win32con.SWP_NOSIZE | 
                    win32con.SWP_NOZORDER | win32con.SWP_FRAMECHANGED)
                # Also invalidate rect to force paint
                import win32api
                win32gui.InvalidateRect(self.embedded_hwnd, None, True)
            except Exception as e:
                pass

    def resizeEvent(self, event):
        super().resizeEvent(event)
        # When PyQt resizes, ensure the internal Java window knows to repaint
        if self.stacked_widget.currentWidget() == getattr(self, 'video_page', None):
            # A tiny delay lets Qt finish its layout pass before we kick Java
            QTimer.singleShot(50, self.trigger_java_repaint)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setStyle("Fusion")
    window = LoginWindow()
    window.show()
    sys.exit(app.exec())
