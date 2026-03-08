import os
import requests
import urllib3
import logging

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

logger = logging.getLogger(__name__)

class Fetcher:
    def __init__(self, ip, lib_dir="lib"):
        self.ip = ip
        self.lib_dir = lib_dir
        self.base_url = f"https://{self.ip}:443/software/"
        
        if not os.path.exists(self.lib_dir):
            os.makedirs(self.lib_dir, exist_ok=True)

    def download_jar(self, jar_name, progress_callback=None):
        url = self.base_url + jar_name
        dest_path = os.path.join(self.lib_dir, jar_name)
        
        logger.info(f"Downloading {jar_name} from {url}...")
        try:
            response = requests.get(url, verify=False, stream=True, timeout=10)
            response.raise_for_status()
            
            total_size = int(response.headers.get('content-length', 0))
            downloaded = 0
            
            try:
                with open(dest_path, "wb") as f:
                    for chunk in response.iter_content(chunk_size=8192):
                        if chunk:
                            f.write(chunk)
                            downloaded += len(chunk)
                            if progress_callback and total_size > 0:
                                progress_callback(int((downloaded / total_size) * 100))
            except PermissionError:
                logger.warning(f"{jar_name} is locked in use. Reusing existing file.")
                if progress_callback:
                    progress_callback(100)
            
            logger.info(f"Successfully guaranteed {jar_name} at {dest_path}")
            return dest_path
        except Exception as e:
            logger.error(f"Failed to download {jar_name}: {e}")
            raise
