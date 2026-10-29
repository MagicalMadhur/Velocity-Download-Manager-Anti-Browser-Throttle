import os
import sys
import time
import threading
import customtkinter as ctk
import download_manager.ydl_imports

from download_manager.database.db import init_db
from download_manager.database.repository import DownloadRepository
from download_manager.services.queue_manager import QueueManager
from download_manager.services.category_parser import get_category
from download_manager.models.download_item import DownloadItem
from download_manager.gui.main_window import MainWindow
from download_manager.gui.themes import apply_theme
from download_manager.services.browser_integration import BrowserIntegrationServer
import download_manager.gui.dialogs
import pyperclip
import re

def get_app_icon_path(ext=".ico") -> str:
    filename = f"velocity{ext}"
    if hasattr(sys, '_MEIPASS'):
        for sub in ['download_manager', '']:
            p = os.path.join(sys._MEIPASS, sub, filename)
            if os.path.exists(p):
                return os.path.abspath(p)
    if getattr(sys, 'frozen', False):
        exe_dir = os.path.dirname(sys.executable)
        for p in [
            os.path.join(exe_dir, '_internal', 'download_manager', filename),
            os.path.join(exe_dir, '_internal', filename),
            os.path.join(exe_dir, 'download_manager', filename),
            os.path.join(exe_dir, filename),
        ]:
            if os.path.exists(p):
                return os.path.abspath(p)
    try:
        this_dir = os.path.dirname(os.path.abspath(__file__))
        for p in [
            os.path.join(this_dir, filename),
            os.path.join(this_dir, '..', 'download_manager', filename),
            os.path.abspath(os.path.join('download_manager', filename)),
            os.path.abspath(filename),
        ]:
            if os.path.exists(p):
                return os.path.abspath(p)
    except Exception:
        pass
    return None

class App:
    def __init__(self):
        # Init DB
        init_db()
        self.repo = DownloadRepository()
        
        # Init Settings
        from download_manager.services.settings import settings
        self.settings = settings
        
        # Init Queue
        self.queue_manager = QueueManager(max_concurrent_downloads=3)
        self.queue_manager.set_callbacks(self._on_progress, self._on_status)
        
        # Check if launched on Windows startup / background mode
        self.is_startup_mode = any(arg.lower() in ('--startup', '--minimized', '--background', '-m', '/startup', '/minimized') for arg in sys.argv)
        
        # Init UI
        self.root = ctk.CTk()
        self.root.title("Velocity Download Manager")
        self.root.geometry("1000x650")
        apply_theme(self.root, "dark-blue")
        
        ico_path = get_app_icon_path(".ico")
        if ico_path and os.path.exists(ico_path):
            try:
                self.root.iconbitmap(ico_path)
            except Exception:
                pass
        
        self.root.protocol("WM_DELETE_WINDOW", self.hide_to_tray)
        self.tray_icon = None
        
        # If started on startup or minimized, withdraw immediately to sit silently in background
        if self.is_startup_mode:
            self.root.withdraw()
            self.setup_tray()
        
        callbacks = {
            'on_add': self.add_download,
            'on_pause': self.pause_download,
            'on_resume': self.resume_download,
            'on_cancel': self.cancel_download,
            'on_delete': self.delete_download,
            'on_refresh_url': self.refresh_url,
            'on_sniff_video': self.sniff_and_prompt_video
        }
        
        self.main_window = MainWindow(self.root, callbacks)
        
        # Load history
        self._load_history()
        
        self.running = True
        
        # Browser Integration Server
        self.browser_server = BrowserIntegrationServer(self.add_download_from_browser)
        self.browser_server.start()
        
        # Ensure startup registry key has --startup flag if enabled
        self._ensure_startup_registry_flag()
        
        # Start speed calculation thread
        self.speed_history = {}
        threading.Thread(target=self._speed_calculator_loop, daemon=True).start()

    def _load_history(self):
        items = self.repo.get_all_downloads()
        # Reset statuses if closed abruptly or mark finished
        for item in items:
            if item.filesize > 0 and item.downloaded_size >= item.filesize:
                item.status = "Completed"
                item.speed = 0
                self.repo.update_status(item.id, "Completed")
            elif item.status in ["Downloading", "Starting"]:
                item.status = "Paused"
                self.repo.update_status(item.id, "Paused")
        self.main_window.load_items(items)

    def add_download(self, url: str, path: str, filename: str = None, is_ydl: bool = False, ydl_format_id: str = None, headers: dict = None):
        from download_manager.services.video_extractor import is_video_url
        if not is_ydl and is_video_url(url):
            self.sniff_and_prompt_video(url, default_path=path)
            return

        if not filename:
            from urllib.parse import urlparse
            filename = os.path.basename(urlparse(url).path) or "downloaded_file"
            
        filepath = os.path.join(path, filename)
        category = get_category(filename)
        
        item = DownloadItem(
            url=url,
            filename=filename,
            filepath=filepath,
            category=category,
            is_ydl=is_ydl,
            ydl_format_id=ydl_format_id
        )
        if headers:
            item.set_headers(headers)
        
        item.id = self.repo.add_download(item)
        self.main_window.items[item.id] = item
        self.main_window._insert_item(item)
        
        # Auto start
        self.resume_download(item.id)

    def pause_download(self, item_id: int):
        self.queue_manager.pause_task(item_id)
        self.repo.update_status(item_id, "Paused")
        
    def resume_download(self, item_id: int):
        item = self.main_window.items.get(item_id)
        if item:
            item.status = "Pending"
            self.repo.update_status(item_id, "Pending")
            self.queue_manager.add_to_queue(item)
            
    def cancel_download(self, item_id: int):
        self.queue_manager.cancel_task(item_id)
        self.repo.update_status(item_id, "Cancelled")
        
    def delete_download(self, item_id: int):
        self.queue_manager.cancel_task(item_id)
        self.repo.delete_download(item_id)

    def refresh_url(self, item_id: int, new_url: str):
        item = self.main_window.items.get(item_id)
        if item:
            item.url = new_url
            self.repo.update_download(item)
            self.resume_download(item_id)

    def _on_progress(self, item_id: int, downloaded: int, chunks_info: str):
        item = self.main_window.items.get(item_id)
        if item:
            item.downloaded_size = downloaded
            item.chunks_info = chunks_info
            
            # Record for speed calculation
            if item_id not in self.speed_history:
                self.speed_history[item_id] = []
            self.speed_history[item_id].append((time.time(), downloaded))
            # Keep last 5 samples
            if len(self.speed_history[item_id]) > 5:
                self.speed_history[item_id].pop(0)

    def _on_status(self, item_id: int, status: str):
        item = self.main_window.items.get(item_id)
        if item:
            item.status = status
            if status == "Completed":
                item.speed = 0
                if item.filesize > 0:
                    item.downloaded_size = item.filesize
                if not item.completion_time:
                    import datetime
                    item.completion_time = datetime.datetime.now().isoformat()
            self.repo.update_download(item)
            # The UI update loop in main_window will pick this up automatically

    def _speed_calculator_loop(self):
        while self.running:
            for item_id, history in list(self.speed_history.items()):
                if len(history) >= 2:
                    t1, b1 = history[0]
                    t2, b2 = history[-1]
                    if t2 > t1:
                        speed = (b2 - b1) / (t2 - t1)
                        item = self.main_window.items.get(item_id)
                        if item:
                            item.speed = int(speed)
            time.sleep(1)
            # Sync DB periodically for active downloads
            for item_id, task in list(self.queue_manager.active_tasks.items()):
                item = task.item
                self.repo.update_progress(item_id, item.downloaded_size, item.chunks_info)


    def _bring_to_front(self):
        if self.root.state() == 'withdrawn':
            self.root.deiconify()
            
        self.root.attributes('-topmost', True)
        self.root.attributes('-topmost', False)
        self.root.focus_force()
        if self.root.state() in ('iconic', 'icon'):
            self.root.state('normal')

    def setup_tray(self):
        if self.tray_icon is not None:
            return
            
        import pystray
        from PIL import Image
        
        # Load app icon (checks .png then .ico using get_app_icon_path)
        image = None
        for ext in ('.png', '.ico'):
            icon_file = get_app_icon_path(ext)
            if icon_file and os.path.exists(icon_file):
                try:
                    img = Image.open(icon_file)
                    image = img.resize((64, 64), Image.Resampling.LANCZOS).convert('RGBA')
                    break
                except Exception as e:
                    print(f"Error loading icon {icon_file}: {e}")
                    
        if image is None:
            from PIL import ImageDraw
            image = Image.new('RGBA', (64, 64), color=(0, 123, 255, 255))
            dc = ImageDraw.Draw(image)
            dc.rectangle((16, 16, 48, 48), fill=(255, 255, 255, 255))
            
        menu = pystray.Menu(
            pystray.MenuItem("Show Velocity", self.show_from_tray, default=True),
            pystray.MenuItem("Quit", self._quit_app)
        )
        
        self.tray_icon = pystray.Icon("Velocity", image, "Velocity Download Manager", menu)
        threading.Thread(target=self.tray_icon.run, daemon=True).start()

    def hide_to_tray(self):
        self.root.withdraw()
        self.setup_tray()

    def show_from_tray(self, icon=None, item=None):
        self.root.after(0, self._bring_to_front)

    def _ensure_startup_registry_flag(self):
        try:
            import winreg
            key_path = r"Software\Microsoft\Windows\CurrentVersion\Run"
            key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, key_path, 0, winreg.KEY_ALL_ACCESS)
            try:
                val, _ = winreg.QueryValueEx(key, "VelocityDownloadManager")
                if val and "--startup" not in val.lower():
                    clean_val = val.strip()
                    winreg.SetValueEx(key, "VelocityDownloadManager", 0, winreg.REG_SZ, f'{clean_val} --startup')
            except FileNotFoundError:
                pass
            winreg.CloseKey(key)
        except Exception:
            pass

    def _quit_app(self, icon=None, item=None):
        self.running = False
        self.queue_manager.shutdown()
        self.browser_server.stop()
        if self.tray_icon:
            try:
                self.tray_icon.stop()
            except Exception:
                pass
            self.tray_icon = None
        self.root.after(0, self.root.quit)
        self.root.after(0, self.root.destroy)

    def _bring_to_front(self):
        try:
            self.root.deiconify()
            self.root.state('normal')
            self.root.lift()
            self.root.attributes('-topmost', True)
            self.root.after_idle(lambda: self.root.attributes('-topmost', False))
            self.root.focus_force()
        except Exception:
            try:
                self.root.deiconify()
            except Exception:
                pass

    def add_download_from_browser(self, url: str, filename: str = None, req_type: str = 'file', headers: dict = None):
        from download_manager.services.video_extractor import is_video_url
        self.root.after(0, self._bring_to_front)
        
        if req_type == 'video_page' or is_video_url(url):
            self.sniff_and_prompt_video(url)
        else:
            self.root.after(0, lambda: self.main_window._show_add_frame(url=url, filename=filename, headers=headers))

    def sniff_and_prompt_video(self, url: str, default_path: str = None):
        self.root.after(0, self._bring_to_front)
        from download_manager.gui.dialogs import SniffingDialog
        from download_manager.services.settings import settings
        save_path = default_path or settings.get("default_download_path")
        self.root.after(0, lambda: SniffingDialog(self.root, url, self.add_download, default_path=save_path))

    def _add_video_to_ui(self, url, filename, is_ydl=False, ydl_format_id=None):
        self.root.after(0, lambda: self.main_window._show_add_frame(url=url, filename=filename, is_ydl=is_ydl, ydl_format_id=ydl_format_id))

    def run(self):
        try:
            self.root.mainloop()
        finally:
            self.running = False
            self.queue_manager.shutdown()
            self.browser_server.stop()
            if self.tray_icon:
                self.tray_icon.stop()

if __name__ == "__main__":
    app = App()
    app.run()
