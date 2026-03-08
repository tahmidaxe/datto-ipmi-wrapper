# Datto IPMI KVM Viewer Wrapper

A modern, fast, and completely standalone Python/PyQt6 wrapper for the Datto (Gigabyte MB10-DATTO) MergePoint EMS vKVM Viewer. 

This project was built to bypass the frustration of legacy `DATTO_IPMI.jnlp` files. Instead of endlessly installing old versions of Java, struggling with security exceptions, or waiting for clunky browser downloads, this wrapper completely automates the connection securely and perfectly embeds the KVM display within a beautiful native dark-mode window.

![Datto KVM Wrapper Viewer Demo](https://via.placeholder.com/800x600.png?text=Datto+KVM+Wrapper+Screenshot)

## Features
- **Zero Dependencies**: Bypasses the need for system Java. A portable OpenJDK 8 JRE is completely bundled inside the app folder, letting you run it strictly offline/air-gapped.
- **Modern UI**: A beautifully crafted, sleek dark-mode GUI built with PyQt6.
- **Embedded Viewer**: The actual Java AWT rendering canvas is natively reparented into the PyQt window using `win32gui` tricks, yielding a unified, seamless control window. 
- **Auto-Bypass Security Prompts**: Connects to your BMC HTTP API directly to download the necessary proprietary `.jar` and native libraries automatically on the fly, skipping the JNLP `.jnlp` execution phase entirely.
- **Credential Saving**: Locally securely saves IPMI connection credentials.

## Setup & Running from Source
If bringing your own Python environment:
1. Clone the repository:
   ```cmd
   git clone https://github.com/your-username/datto-ipmi-wrapper.git
   cd datto-ipmi-wrapper
   ```
2. Install the required dependencies:
   ```cmd
   pip install PyQt6 requests pywin32
   ```
3. Since the Python application needs Java OpenJDK 8 to launch the `.jar` binaries, download a portable JDK/JRE into a `jre` folder inside the project root:
   ```cmd
   python -c "import requests, zipfile, os; url='https://api.adoptium.net/v3/binary/latest/8/ga/windows/x64/jre/hotspot/normal/eclipse?project=jdk'; zip_path='jre.zip'; print('downloading...'); r=requests.get(url); open(zip_path, 'wb').write(r.content); print('extracting...'); os.makedirs('jre', exist_ok=True); zipfile.ZipFile(zip_path).extractall('jre'); os.remove(zip_path)"
   ```
4. Run the launcher:
   ```cmd
   python launcher.py
   ```

## Compiling for Distribution

To bundle this utility into a single standalone directory (so you can send it to friends/coworkers without requiring them to install Python or Java):

1. Install PyInstaller:
   ```cmd
   pip install pyinstaller
   ```
2. Build the executable in `--onedir` mode (this ensures the Java runtime folder is perfectly preserved alongside the executable):
   ```cmd
   python -m PyInstaller --noconfirm --onedir --windowed --icon "app_icon.ico" --add-data "app_icon.ico;." --add-data "jre;jre" launcher.py
   ```
3. The generated standalone folder will be sitting in `dist/launcher`. Compress that folder to a `.zip` file for distribution!

## Compatibility 
This project currently expects a **Windows** environment to execute due to `win32gui` DLL injection for window embedding and specifically targets AST2400-based Gigabyte MergePoint EMS v8.88 platforms. It will dynamically pull down `avctKVMIOWin64.jar` for native operations but theoretically supports Mac/Linux `.so`/`.jnilib` downloads if ported away from the Win32 UI embedding.

## Licensing
This tool strictly acts as a wrapper around Datto's proprietary `.jar` binary payloads pulled transparently from the user's local BMC interface. This code does not distribute the `.jar` files themselves. Ensure you have the rights to interface with your hardware before use.
