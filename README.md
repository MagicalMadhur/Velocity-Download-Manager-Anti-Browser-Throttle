<p align="center">
  <img src="./download_manager/velocity.ico" alt="Velocity Logo" width="100" height="100">
</p>

<h1 align="center">Velocity Download Manager</h1>

<p align="center">
  <strong>A multi-threaded desktop download manager built to bypass browser throttling, with native browser integration and unlimited-quality video extraction.</strong>
</p>

<p align="center">
  <img src="https://img.shields.io/badge/python-3.10+-3776AB?style=for-the-badge&logo=python&logoColor=white" alt="Python Version">
  <img src="https://img.shields.io/badge/platform-windows-0078D6?style=for-the-badge&logo=windows&logoColor=white" alt="Platform">
  <img src="https://img.shields.io/badge/license-MIT-blue?style=for-the-badge" alt="License">
  <img src="https://img.shields.io/badge/version-1.0.2-green?style=for-the-badge" alt="Version">
</p>

---

## Why Velocity Exists

Every major browser artificially limits download speeds. They use a single connection per file, ignore `Accept-Ranges` headers, and give you zero control over how your bandwidth is used. Paid download managers like IDM solve this problem — but charge you for it.

**Velocity is the free, open-source alternative.** It splits every download into up to 32 parallel connections, saturates your available bandwidth, and gives you full control over speed limits, concurrent downloads, and file organization. It also integrates directly into your browser through a lightweight extension, so downloads are intercepted automatically — no copy-pasting URLs.

For video downloads, Velocity goes further. Instead of being limited to whatever resolution the browser hands you (typically 720p), Velocity uses `yt-dlp` under the hood to extract every available format from a video page — including 1080p, 1440p, 4K, and 8K streams that browsers intentionally withhold. When a high-resolution stream separates video and audio into different files (as YouTube and most platforms do), Velocity automatically merges them using a bundled copy of `FFmpeg`. No manual steps, no quality loss.

---

## Table of Contents

- [Key Features](#key-features)
- [Quick Installation](#quick-installation)
- [Browser Extension](#browser-extension)
- [How It Works](#how-it-works)
- [Project Structure](#project-structure)
- [Configuration & Settings](#configuration--settings)
- [Developer Setup](#developer-setup)
- [Building From Source](#building-from-source)
- [Troubleshooting](#troubleshooting)
- [License](#license)

---

## Key Features

### Multi-Threaded Download Acceleration

Velocity splits every download into multiple concurrent byte-range requests (up to 32 threads per file). Each thread downloads a different segment of the file simultaneously, then the segments are assembled on disk using preallocated file writes with precise `seek` offsets. This approach bypasses the single-connection bottleneck that browsers enforce, and in practice delivers **3–5x faster downloads** on most servers that support HTTP range requests.

If a server doesn't support range requests, Velocity gracefully falls back to single-threaded streaming mode.

### Token-Bucket Rate Limiting

A global rate limiter built on the [token-bucket algorithm](https://en.wikipedia.org/wiki/Token_bucket) governs all active downloads. You can set a maximum download speed (in KB/s) from the Settings panel, and every chunk written to disk — across every active thread, across every active download — consumes tokens from the same shared bucket. This means your speed limit is a true global cap, not a per-download approximation. Setting it to `0` disables the limiter entirely.

### Unlimited Video Quality Extraction

When the browser extension detects a `<video>` element on a page, it injects a download button directly onto the player. Clicking this button sends the page URL to Velocity, which uses `yt-dlp` to extract **every available format** — including muted high-resolution streams (1080p+) that are normally hidden from browsers.

For streams where the video and audio are served separately (which is the standard for 1080p+ on YouTube and most platforms), Velocity automatically merges them into a single file using a pre-bundled copy of `FFmpeg`. An optional loudness normalization filter (`loudnorm`) can be applied during the merge to match YouTube's playback volume, preventing jarring volume differences between downloaded videos.

### Smart File Categorization

Downloaded files are automatically sorted into categories based on their file extension:

| Category | Extensions |
|---|---|
| **Videos** | `.mp4`, `.mkv`, `.avi`, `.mov`, `.wmv`, `.flv` |
| **Music** | `.mp3`, `.wav`, `.flac`, `.aac`, `.ogg` |
| **Documents** | `.pdf`, `.doc`, `.docx`, `.txt`, `.rtf`, `.xls`, `.xlsx`, `.ppt`, `.pptx` |
| **Images** | `.jpg`, `.jpeg`, `.png`, `.gif`, `.bmp`, `.svg`, `.webp` |
| **Archives** | `.zip`, `.rar`, `.7z`, `.tar`, `.gz`, `.bz2` |
| **Software** | `.exe`, `.msi`, `.apk`, `.dmg`, `.iso` |

Files that don't match any category are labeled **Uncategorized**. The sidebar in the main window lets you filter your download history by category.

### Native Browser Integration

A Chromium-based browser extension (Chrome, Edge, Brave, etc.) intercepts download events at the browser level. When you click a download link, the extension sends the URL to Velocity's local HTTP server (running on `127.0.0.1:6800`), and then cancels the browser's built-in download. From the user's perspective, downloads simply appear in Velocity instead of the browser's download bar.

The extension also injects a visual "Download Video" button onto any `<video>` element on the page (ignoring thumbnails and small previews under 300×150px). This button can be toggled on or off by clicking the extension icon in the browser toolbar, which opens a popup with an Enable/Disable checkbox.

### Windows System Tray Integration

Closing the main window doesn't kill the application — it minimizes Velocity to the Windows system tray. A tray icon with a right-click menu lets you restore the window or quit entirely. This means Velocity can silently run in the background, catching browser downloads even when the window isn't visible.

### Resumable Downloads with Integrity Validation

Every download's progress is persisted to a local SQLite database, including per-chunk byte offsets. If the application crashes or the network drops, you can resume the download from exactly where it left off. Velocity also stores the server's `ETag` and `Last-Modified` headers — if the file has changed on the server since your last attempt, Velocity detects the mismatch and restarts the download cleanly instead of producing a corrupted file.

### Automatic Retry with Exponential Backoff

Each download thread independently retries on failure, up to 10 times. The wait between retries doubles each time (2s, 4s, 8s, ...), reducing pressure on the server and giving transient network issues time to resolve. If all 10 retries are exhausted for any single thread, the entire download is marked as `Error`.

### Post-Download Automation

- **Completion sound**: A system chime plays when a download finishes (can be toggled off).
- **Auto-shutdown**: When enabled, Velocity will issue a `shutdown /s /t 60` command once the download queue is completely empty — useful for overnight batch downloads.

---

## Quick Installation

> [!TIP]
> The standalone installer includes everything — Python runtime, all dependencies, FFmpeg binaries, and the UI toolkit. No prerequisites needed.

1. Go to the **[Releases](../../releases/latest)** page.
2. Download `Velocity_Setup.exe`.
3. Run the installer and follow the Setup Wizard.
4. Click **Launch Velocity** when installation finishes.

That's it. The application is fully self-contained.

---

## Browser Extension

> [!IMPORTANT]
> Developer Mode must be enabled in your browser's extension settings to load an unpacked extension.

### Installation

1. Download [`Velocity_Extension.zip`](./Velocity_Extension.zip) from this repository and extract it to a permanent folder.
2. Open your Chromium-based browser and navigate to the extensions page:
   - **Chrome**: `chrome://extensions/`
   - **Edge**: `edge://extensions/`
   - **Brave**: `brave://extensions/`
3. Enable **Developer Mode** (toggle in the top-right corner).
4. Click **Load unpacked** and select the extracted folder.

### How it works

The extension has two responsibilities:

1. **Download Interception** (`background.js`): Listens for the `chrome.downloads.onDeterminingFilename` event. When a download starts, it sends the URL and filename to `http://127.0.0.1:6800/download` via a POST request. If the local server responds with `200 OK`, the browser's download is cancelled. If the server is unreachable (Velocity isn't running), the browser download proceeds normally.

2. **Video Button Injection** (`content.js`): Uses a `MutationObserver` to watch for `<video>` elements added to the DOM. When one is found (and it's large enough to not be a thumbnail), a floating "📥 Download Video" button is injected at the top-right of the player. Clicking it sends the current page URL to Velocity, which extracts available formats and presents a quality picker dialog.

### Toggle On/Off

Click the Velocity extension icon in your browser toolbar to open the popup. Uncheck **Enable** to hide all injected download buttons across all tabs. This setting persists across browser sessions using `chrome.storage.local`.

---

## How It Works

### Download Lifecycle

1. **URL submitted** — either manually through the "New Download" form, or automatically via the browser extension.
2. **Connection probe** — Velocity sends an HTTP `HEAD` request to determine file size, range support, `ETag`, and `Last-Modified`. If `HEAD` is rejected (HTTP 405), it falls back to a streaming `GET`.
3. **File preallocation** — The target file is created at its full expected size on disk, so all threads can write to their assigned byte ranges without conflicts.
4. **Thread dispatch** — The file is divided into `N` equal parts (default `N=32`). Each part is downloaded by a dedicated thread using HTTP `Range` headers. All threads share a single `requests.Session` for connection pooling.
5. **Rate limiting** — Every chunk written passes through the global token-bucket limiter before being flushed to disk.
6. **Progress tracking** — A background loop calculates download speed from the last 5 samples (using a sliding window), and the UI refreshes at 2 FPS.
7. **Completion** — Once all threads finish, the file is complete on disk (no assembly step needed, since each thread writes directly to the correct offset). The status is updated to `Completed`, the database is synced, and a sound plays if enabled.

### Video Download Lifecycle

1. **Page URL received** — The browser extension sends the page URL (not a direct video file URL) with `type: 'video_page'`.
2. **Format extraction** — Velocity runs `yt-dlp` in a background thread to extract all available formats. This includes muxed streams (video + audio), video-only streams, and audio-only streams.
3. **Quality picker** — A dialog presents all formats sorted by resolution. For video-only streams at 1080p+, Velocity automatically adds a `bestaudio` merge option.
4. **Download** — If the selected format is a direct URL, Velocity uses its own multi-threaded engine. If it requires `yt-dlp` merging (separate video + audio), it delegates to the `YtdlpDownloadTask` engine, which handles the download and `FFmpeg` merge in one step.

### Queue Management

The `QueueManager` runs a background thread that continuously checks:
- How many downloads are currently active (configurable, default 3).
- Whether there are pending items in the queue.
- Whether all downloads have completed (triggers auto-shutdown if enabled).

When a slot opens up, the next item in the queue is started automatically. Pausing a download removes it from the active pool, freeing a slot for the next queued item.

---

## Project Structure

```
.
├── browser_extension/                # Chromium browser extension
│   ├── manifest.json                 # Extension manifest (Manifest V3)
│   ├── background.js                 # Download interception service worker
│   ├── content.js                    # Video button injection content script
│   ├── popup.html                    # Extension popup UI
│   └── popup.js                      # Popup toggle logic
│
├── download_manager/                 # Main Python application package
│   ├── app.py                        # Application entry point — wires everything together
│   ├── velocity.ico                  # Application icon
│   │
│   ├── database/
│   │   ├── db.py                     # SQLite database initialization and connection factory
│   │   └── repository.py            # Data access layer — CRUD operations for downloads
│   │
│   ├── downloader/
│   │   ├── connection.py             # HTTP HEAD probe — extracts file size, range support, ETag
│   │   ├── engine.py                 # Multi-threaded download engine with rate limiter
│   │   ├── file_manager.py           # File preallocation utility
│   │   └── ydl_engine.py            # yt-dlp download engine — handles video/audio merge
│   │
│   ├── gui/
│   │   ├── dialogs.py                # Settings, About, Video Format, and URL Recovery dialogs
│   │   ├── main_window.py            # Main window layout — sidebar, toolbar, download cards
│   │   └── themes.py                # CustomTkinter theme configuration
│   │
│   ├── models/
│   │   └── download_item.py          # DownloadItem dataclass — the core data model
│   │
│   ├── services/
│   │   ├── browser_integration.py    # Local HTTP server on port 6800 for browser comms
│   │   ├── category_parser.py        # File extension to category mapping
│   │   ├── queue_manager.py          # Download queue with concurrency control
│   │   ├── settings.py               # Singleton settings manager with JSON persistence
│   │   └── video_extractor.py        # yt-dlp format extraction (runs in background thread)
│   │
│   └── utils/
│       ├── formatter.py              # Human-readable size and speed formatting
│       └── sys_integration.py        # Windows-specific OS utilities
│
├── tools/                            # Build and development utilities
│   ├── build.py                      # PyInstaller build script for Velocity.exe
│   ├── build_installer.py            # Packages Velocity.exe into a Setup Wizard
│   ├── extract_yt_dlp_imports.py     # Scans yt-dlp for hidden imports (PyInstaller compat)
│   ├── install_ffmpeg.py             # Downloads and extracts FFmpeg binaries
│   └── installer_app.py             # Tkinter-based Setup Wizard GUI
│
├── requirements.txt                  # Python dependencies
├── Velocity_Extension.zip            # Pre-packaged browser extension
├── LICENSE                           # MIT License
└── README.md
```

---

## Configuration & Settings

Settings are stored as JSON at `%LOCALAPPDATA%\VelocityDownloadManager\settings.json` and are accessible from the **⚙ Settings** button in the sidebar.

| Setting | Default | Description |
|---|---|---|
| **Default Download Path** | `~/Downloads` | Where files are saved by default. |
| **Launch on Startup** | `Off` | Adds/removes a Windows Registry entry under `HKCU\Software\Microsoft\Windows\CurrentVersion\Run`. |
| **Max Concurrent Downloads** | `3` | How many downloads can run simultaneously (1–10). |
| **Speed Limit (KB/s)** | `0` (Unlimited) | Global bandwidth cap enforced by the token-bucket rate limiter. |
| **Max Threads per Download** | `32` | Number of parallel connections per file (8, 16, or 32). |
| **Play Sound on Complete** | `On` | Plays a Windows system chime when a download finishes. |
| **Shutdown After Download** | `Off` | Issues `shutdown /s /t 60` when the queue empties. |
| **Normalize Audio** | `On` | Applies FFmpeg `loudnorm` filter during video/audio merge. |

---

## Developer Setup

### Prerequisites

- **Python 3.10+**
- **Git**
- **FFmpeg** — `ffmpeg.exe` and `ffprobe.exe` must be placed in the `download_manager/` directory.

### Steps

```bash
# Clone the repository
git clone https://github.com/MagicalMadhur/Velocity-Download-Manager-Anti-Browser-Throttle.git
cd Velocity-Download-Manager-Anti-Browser-Throttle

# Create a virtual environment
python -m venv .venv

# Activate (Windows)
.venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Download FFmpeg binaries
python tools/install_ffmpeg.py

# Launch
python run.py
```

### Dependencies

| Package | Purpose |
|---|---|
| `requests` | HTTP connections and streaming downloads |
| `customtkinter` | Modern dark-themed UI toolkit (built on Tkinter) |
| `yt-dlp` | Video format extraction and download engine |
| `pystray` | Windows system tray icon integration |
| `Pillow` | Image processing for tray icon generation |
| `pyperclip` | Clipboard access for URL pasting |

---

## Building From Source

### Build the main executable

```bash
python tools/build.py
```

This runs PyInstaller with `Velocity.spec` to produce a standalone `Velocity.exe` in the `dist/` folder. The spec file bundles `ffmpeg.exe`, `ffprobe.exe`, the application icon, and all hidden imports from `yt-dlp`.

### Build the installer

```bash
python tools/build_installer.py
```

This packages `Velocity.exe` and all required assets into a single `Velocity_Setup.exe` installer using a custom Tkinter-based Setup Wizard (`tools/installer_app.py`). The wizard handles installation path selection, desktop shortcut creation, and first-launch.

---

## Troubleshooting

### The browser extension doesn't catch downloads

Make sure Velocity is running (check your system tray). The extension communicates with a local HTTP server on `127.0.0.1:6800`. If Velocity is closed or the port is blocked by Windows Firewall, the extension will fail silently and let the browser handle the download normally.

### Video downloads fail to merge or produce no audio

This means FFmpeg isn't found. If you installed via `Velocity_Setup.exe`, FFmpeg is pre-bundled. If running from source, make sure `ffmpeg.exe` and `ffprobe.exe` are in the `download_manager/` directory. Run `python tools/install_ffmpeg.py` to download them automatically.

### Downloads are slow despite using multiple threads

Some servers don't support HTTP range requests. When this happens, Velocity falls back to a single-threaded download. You can verify by checking if the server returns an `Accept-Ranges: bytes` header. CDN-hosted files almost always support range requests; direct links from smaller servers may not.

### The "Download Video" button doesn't appear on a video

The content script only injects the button on `<video>` elements larger than 300×150 pixels. If the video uses an `<iframe>` embed (common on social media), the content script can't access it due to cross-origin restrictions. Additionally, make sure the extension is enabled — click the Velocity icon in the toolbar and check that the **Enable** checkbox is checked.

### Can I use Velocity on Linux or macOS?

Velocity was designed for Windows. It uses Windows-specific APIs for system tray integration (`pystray` with Windows backends), startup registry keys (`winreg`), and completion sounds (`winsound`). The core download engine and UI (CustomTkinter) are cross-platform in theory, but the OS integration layer would need to be adapted.

---

## License

This project is licensed under the **MIT License**. See the [LICENSE](LICENSE) file for details.

---

<p align="center">
  Built by <a href="https://github.com/MagicalMadhur">Madhur Chavan</a><br>
  <em>"With love, to destroy IDM."</em>
</p>
