import os
import zipfile
import logging

logger = logging.getLogger(__name__)

class Extractor:
    def __init__(self, lib_dir="lib"):
        self.lib_dir = lib_dir
        self.native_dir = os.path.join(self.lib_dir, "native")
        
        if not os.path.exists(self.native_dir):
            os.makedirs(self.native_dir, exist_ok=True)

    def extract_native_libs(self, jar_path):
        logger.info(f"Extracting native libraries from {jar_path} to {self.native_dir}...")
        try:
            extracted_files = []
            with zipfile.ZipFile(jar_path, 'r') as zip_ref:
                for member in zip_ref.namelist():
                    # Extract DLLs on Windows (or .so / .jnilib on others)
                    if member.endswith(".dll") or member.endswith(".so") or member.endswith(".jnilib"):
                        try:
                            zip_ref.extract(member, self.native_dir)
                            extracted_files.append(member)
                            logger.info(f"Extracted: {member}")
                        except PermissionError:
                            logger.warning(f"Native library {member} is locked, bypassing extraction.")
                            extracted_files.append(member)
            return self.native_dir
        except Exception as e:
            logger.error(f"Failed to extract native libs from {jar_path}: {e}")
            raise
