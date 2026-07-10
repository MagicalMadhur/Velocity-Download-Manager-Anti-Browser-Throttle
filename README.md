<p align="center">
  <img src="https://readme-typing-svg.herokuapp.com?font=Fira+Code&weight=800&size=40&pause=1000&color=00F0FF&center=true&vCenter=true&width=800&lines=Velocity+Download+Manager;Accelerate+Your+Downloads;Multi-Threaded.+Fast.+Open-Source." alt="Typing SVG" />
</p>

<p align="center">
  <img src="./download_manager/velocity.ico" alt="Velocity Logo" width="120" height="120">
</p>

<p align="center">
  <strong>A high-performance, multi-threaded desktop download manager with native browser integration, real-time speed throttling, and unlimited quality video extraction.</strong>
</p>

<p align="center">
  <img src="https://img.shields.io/badge/python-3.10+-3776AB?style=for-the-badge&logo=python&logoColor=white" alt="Python Version">
  <img src="https://img.shields.io/badge/platform-windows-0078D6?style=for-the-badge&logo=windows&logoColor=white" alt="Platform">
  <img src="https://img.shields.io/badge/ui-customtkinter-005C97?style=for-the-badge" alt="UI Theme">
  <img src="https://img.shields.io/badge/license-MIT-blue?style=for-the-badge" alt="License">
</p>

<p align="center">
  <img src="https://img.shields.io/badge/🔥_Built_for_Speed-FF0055?style=flat-square">
  <img src="https://img.shields.io/badge/🚀_Fully_Open_Source-00E5FF?style=flat-square">
  <img src="https://img.shields.io/badge/🎨_Dark_Mode_UI-8A2BE2?style=flat-square">
</p>

---

## <img src="https://img.shields.io/badge/📖_Table_of_Contents-1A1A2E?style=for-the-badge" />
- [💎 Key Features](#-key-features)
- [⚡ Quick Installation](#-quick-installation)
- [🌐 Browser Extension](#-browser-extension)
- [🏗️ Architecture](#️-architecture)
- [📂 Directory Structure](#-directory-structure)
- [🛠️ Developer Setup](#️-developer-setup)
- [❓ Troubleshooting](#-troubleshooting)

---

## <img src="https://img.shields.io/badge/💎_Key_Features-FF007F?style=for-the-badge" />

- ![Speed](https://img.shields.io/badge/⚡_Speed-500%25_Faster-00FF88?style=flat-square) **Multi-Threaded Acceleration:** Splits downloads into multiple concurrent connection chunks, bypassing server throttling to saturate your bandwidth!
- ![Video](https://img.shields.io/badge/🎬_Video-4K_&_8K-FF3300?style=flat-square) **Unlimited Video Resolutions:** Unlike standard downloaders, Velocity auto-stitches high-resolution video streams with separate HQ audio using pre-packaged **FFmpeg**.
- ![Throttling](https://img.shields.io/badge/⚙️_Throttling-Dynamic-00E5FF?style=flat-square) **Speed Throttling:** Throttle your download speed in real-time using a custom-built token-bucket rate limiter.
- ![Routing](https://img.shields.io/badge/📁_Routing-Smart_Categorization-8A2BE2?style=flat-square) **Smart File Categorization:** Auto-routes downloaded files into organized subfolders (`Video`, `Audio`, `Documents`, `Compressed`, `Programs`).
- ![Browser](https://img.shields.io/badge/🌐_Browser-Seamless_Catching-FFaa00?style=flat-square) **Browser Interceptor:** Integrates directly with your browser to automatically capture download links!
- ![Tray](https://img.shields.io/badge/🚀_Windows-Native_Tray-0078D6?style=flat-square) **Windows Native:** Minimizes to System Tray, registers on startup, and supports auto-shutdown upon completion.

---

## <img src="https://img.shields.io/badge/⚡_Quick_Installation-00E5FF?style=for-the-badge" />

> [!TIP]
> **No installation dependencies required!** The standalone package includes Python runtimes, UI kits, and video merging binaries out of the box.

1. **[Download Velocity_Setup.exe](./Velocity_Setup.exe)** directly from this repository.
2. Double-click the downloaded `Velocity_Setup.exe` file.
3. Follow the Setup Wizard instructions to choose your custom installation path and create a desktop shortcut.
4. Click **Launch Velocity** when the installer finishes!

---

## <img src="https://img.shields.io/badge/🌐_Browser_Extension-FFAA00?style=for-the-badge" />

> [!IMPORTANT]
> **Developer Mode must be enabled** in your browser settings to load the unpacked extension folder.

1. **[Download Velocity_Extension.zip](./Velocity_Extension.zip)** and extract it to a permanent folder on your computer.
2. Open any Chromium-based browser (Google Chrome, Microsoft Edge, Brave, etc.).
3. Navigate to the Extensions panel (`chrome://extensions/` or `edge://extensions/`).
4. Toggle the **Developer Mode** switch in the top-right corner.
5. Click the **Load unpacked** button in the top-left.
6. Select the folder where you extracted the extension.
7. *Done!* The extension will now communicate silently with the Velocity local server on port `6800`.

---

## <img src="https://img.shields.io/badge/🏗️_Architecture-00FF88?style=for-the-badge" />

```mermaid
%%{init: {'theme': 'dark', 'themeVariables': { 'primaryColor': '#005C97', 'primaryTextColor': '#fff', 'primaryBorderColor': '#7C0000', 'lineColor': '#00F0FF', 'secondaryColor': '#0078D6', 'tertiaryColor': '#333'}}}%%
graph TD
    Browser[🌐 Browser Extension] -- TCP:6800 --> IntegrationServer[🔌 Browser Integration Server]
    IntegrationServer --> UI[💻 AddDownloadDialog GUI]
    UI -- Add Item --> DB[(🗄️ SQLite Database)]
    UI -- Enqueue --> Queue[📥 Queue Manager]
    Queue -- Dispatch --> Task[⚙️ Download Task Thread]
    Task --> Engine[🚀 Multi-Threaded Engine]
    Engine -- Fetch Chunks --> Net[🌍 Internet / Web Servers]
    Engine -- Rate Control --> Limiter[⏱️ Token Bucket Rate Limiter]
    Engine --> Merger[🎬 File Assembly / FFmpeg]
    Tray[📥 Windows System Tray] --> UI
```

---

## <img src="https://img.shields.io/badge/📂_Directory_Structure-555555?style=for-the-badge" />

```directory
.
├── browser_extension/        # Browser extension source code (interceptor)
├── download_manager/         # Main desktop application Python package
│   ├── database/             # Database initialization and queries
│   ├── downloader/           # Multi-threaded download algorithms & engines
│   ├── gui/                  # Theme configurations and CustomTkinter layouts
│   ├── models/               # SQLite DB schemas and data structures
│   ├── services/             # TCP socket server, settings manager, registries
│   ├── utils/                # Standard helper modules
│   ├── app.py                # Main application entry point
│   └── velocity.ico          # Application branding icon
├── tools/                    # Developer tools and build pipelines
│   ├── build.py              # Compiles main payload (Velocity.exe)
│   ├── build_installer.py    # Packages app and assets into Setup Wizard (Velocity_Setup.exe)
│   ├── extract_yt_dlp_imports.py # Dependency scanning engine for PyInstaller
│   ├── install_ffmpeg.py     # Script to automate local FFmpeg installations
│   └── installer_app.py      # Tkinter code for the Setup Wizard GUI installer
├── .gitignore                # Custom ignore parameters for Python / PyInstaller
├── LICENSE                   # Standard MIT License
├── README.md                 # Product documentation
├── requirements.txt          # Python runtime requirements list
├── Velocity_Extension.zip    # Pre-packaged browser extension for direct download
└── Velocity_Setup.exe        # Pre-compiled standalone installer for direct execution
```

---

## <img src="https://img.shields.io/badge/🛠️_Developer_Setup-FF3300?style=for-the-badge" />

> [!NOTE]
> Make sure to install FFmpeg using our setup script if you're running the source code directly. High-resolution stream merging requires it.

### Prerequisites:
- **Python 3.10+** installed on your system.
- **Git** to clone the repository.
- **FFmpeg** binaries (`ffmpeg.exe`, `ffprobe.exe`) placed in the `download_manager/` directory. You can run our automated utility:
  ```bash
  python tools/install_ffmpeg.py
  ```

### Steps:
1. **Clone the repository:**
   ```bash
   git clone https://github.com/yourusername/velocity-download-manager.git
   cd velocity-download-manager
   ```
2. **Create and activate a virtual environment:**
   ```bash
   python -m venv .venv
   # Windows:
   .venv\Scripts\activate
   # macOS/Linux:
   source .venv/bin/activate
   ```
3. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```
4. **Launch the application:**
   ```bash
   python -m download_manager.app
   ```

---

## <img src="https://img.shields.io/badge/❓_Troubleshooting-6A0572?style=for-the-badge" />

> [!WARNING]
> If you close the desktop client or block port `6800`, the browser extension will show connection errors.

#### Q: The Chrome extension doesn't catch my downloads. How do I fix it?
Make sure Velocity is currently running in your system tray. The extension relies on a TCP server listening on port `6800`. If Velocity is closed or blocked by Windows Firewall, the extension won't be able to forward downloads.

#### Q: Why are YouTube downloads failing to merge?
Ensure `ffmpeg.exe` and `ffprobe.exe` are present in your application root folder. If you installed via `Velocity_Setup.exe`, they are already pre-bundled. If running from source, execute `python tools/install_ffmpeg.py` to acquire them automatically.

#### Q: Can I run Velocity on Linux/macOS?
Velocity has been built with native Windows integrations (Registry hooks for startup, taskkill subprocesses, and custom chimes). While the GUI and core engine can run on other platforms, certain OS-specific utilities are optimized for Windows environment deployment.

---

## <img src="https://img.shields.io/badge/📄_License-MIT-blue?style=for-the-badge" />
This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.
