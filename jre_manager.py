import os
import sys
import logging
import platform

logger = logging.getLogger(__name__)

class JREManager:
    def __init__(self):
        # When running frozen in --onedir mode, data files are in sys._MEIPASS
        if getattr(sys, 'frozen', False):
            # Try MEIPASS first (PyInstaller standard)
            if hasattr(sys, '_MEIPASS'):
                self.jre_dir = os.path.join(sys._MEIPASS, "jre")
            else:
                self.jre_dir = os.path.join(os.path.dirname(sys.executable), "jre")
        else:
            self.jre_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "jre")

    def get_java_exe(self):
        if not os.path.exists(self.jre_dir):
            return None
            
        target = "java.exe" if platform.system() == "Windows" else "java"
        
        # Searching through the bundled JRE directory
        for root, dirs, files in os.walk(self.jre_dir):
            if target in files:
                exe = os.path.join(root, target)
                return exe
        return None

    def ensure_jre(self, progress_callback=None):
        if progress_callback:
            progress_callback(100) # Instantly complete since it's bundled
            
        exe = self.get_java_exe()
        if not exe:
            raise Exception(f"Bundled Java executable not found inside {self.jre_dir}!")
        return exe
