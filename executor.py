import os
import subprocess
import logging
import platform

logger = logging.getLogger(__name__)

class Executor:
    def __init__(self, lib_dir="lib"):
        self.lib_dir = lib_dir
        self.native_dir = os.path.join(self.lib_dir, "native")
        self.main_jar = os.path.join(self.lib_dir, "avctKVM.jar")

    def run_viewer(self, java_exe, ip, username, password):
        # We use the isolated, portable java_exe
        args = [
            java_exe,
            f"-Djava.library.path={self.native_dir}",
            "-Dsun.java2d.d3d=false",
            "-Dsun.java2d.noddraw=true",
            "-cp", self.main_jar,
            "com.avocent.kvm.client.Main",
            f"title=- {ip}",
            f"ip={ip}",
            "platform=ast2400",
            "vmprivilege=true",
            f"user={username}",
            f"passwd={password}",
            "kmport=2068",
            "vport=2068",
            "apcp=1",
            "version=2",
            "platform=ASPEED",
            "color=0",
            "chat=1",
            "softkeys=1",
            "statusbar=ip,un,fr,bw,kp,led",
            "power=1",
            "language=en"
        ]
        
        logger.info(f"Executing Java Viewer with args: {' '.join(args)}")
        
        try:
            # We use Popen so we don't block the UI
            startupinfo = None
            if platform.system() == "Windows":
                startupinfo = subprocess.STARTUPINFO()
                startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
            
            # Not discarding stdout/stderr so we can potentially capture Java errors if needed
            process = subprocess.Popen(
                args,
                startupinfo=startupinfo
            )
            return process
        except Exception as e:
            logger.error(f"Failed to execute Java viewer: {e}")
            raise
