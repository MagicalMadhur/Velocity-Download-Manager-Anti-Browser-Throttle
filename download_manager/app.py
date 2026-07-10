import os
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

class App:
    def __init__(self):
        # Init DB
        init_db()
        self.repo = DownloadRepository()
        
        # Init Queue
        self.queue_manager = QueueManager(max_concurrent_downloads=3)
        self.queue_manager.set_callbacks(self._on_progress, self._on_status)
        
        # Init UI
        self.root = ctk.CTk()
        self.root.title("Velocity Download Manager")
        self.root.geometry("1000x650")
        apply_theme(self.root, "dark-blue")
        
        icon_path = os.path.join(os.path.dirname(__file__), "velocity.ico")
        if os.path.exists(icon_path):
            self.root.iconbitmap(icon_path)
        
        self.root.protocol("WM_DELETE_WINDOW", self.hide_to_tray)
        self.tray_icon = None
        
        callbacks = {
            'on_add': self.add_download,
            'on_pause': self.pause_download,
            'on_resume': self.resume_download,
            'on_cancel': self.cancel_download,
            'on_delete': self.delete_download,
            'on_refresh_url': self.refresh_url
        }
        
        self.main_window = MainWindow(self.root, callbacks)
        
        # Load history
        self._load_history()
        
        # Clipboard monitoring
        self.last_clipboard = ""
        self.running = True
        threading.Thread(target=self._clipboard_monitor, daemon=True).start()
        
        # Browser Integration Server
        self.browser_server = BrowserIntegrationServer(self.add_download_from_browser)
        self.browser_server.start()
        
        # Start speed calculation thread
        self.speed_history = {}
        threading.Thread(target=self._speed_calculator_loop, daemon=True).start()

    def _load_history(self):
        items = self.repo.get_all_downloads()
        # Reset statuses if closed abruptly
        for item in items:
            if item.status in ["Downloading", "Starting"]:
                item.status = "Paused"
                self.repo.update_status(item.id, "Paused")
        self.main_window.load_items(items)

    def add_download(self, url: str, path: str, filename: str = None, is_ydl: bool = False, ydl_format_id: str = None):
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

    def _clipboard_monitor(self):
        url_regex = re.compile(
            r'^(?:http|ftp)s?://' # http:// or https://
            r'(?:(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+(?:[A-Z]{2,6}\.?|[A-Z0-9-]{2,}\.?)|' #domain...
            r'localhost|' #localhost...
            r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})' # ...or ip
            r'(?::\d+)?' # optional port
            r'(?:/?|[/?]\S+)$', re.IGNORECASE)
            
        while self.running:
            try:
                text = pyperclip.paste().strip()
                if text != self.last_clipboard:
                    self.last_clipboard = text
                    if url_regex.match(text):
                        # Ask user if they want to download
                        # In a real app this would be a system notification or a small popup,
                        # For now, we can just open the add dialog directly via Tkinter event
                        self.root.after(0, lambda: self.add_download_from_clipboard(text))
            except:
                pass
            time.sleep(1)
            
    def _bring_to_front(self):
        if self.root.state() == 'withdrawn':
            if self.tray_icon:
                self.tray_icon.stop()
                self.tray_icon = None
            self.root.deiconify()
            
        self.root.attributes('-topmost', True)
        self.root.attributes('-topmost', False)
        self.root.focus_force()
        if self.root.state() == 'iconic' or self.root.state() == 'icon':
            self.root.state('normal')

    def hide_to_tray(self):
        self.root.withdraw() 
        
        if self.tray_icon is None:
            import pystray
            from PIL import Image, ImageDraw
            
            # Generate a simple icon
            image = Image.new('RGB', (64, 64), color = (0, 123, 255))
            dc = ImageDraw.Draw(image)
            dc.rectangle((16, 16, 48, 48), fill=(255, 255, 255))
            
            menu = pystray.Menu(
                pystray.MenuItem("Show Velocity", self.show_from_tray, default=True),
                pystray.MenuItem("Quit", self._quit_app)
            )
            
            self.tray_icon = pystray.Icon("Velocity", image, "Velocity Download Manager", menu)
            
        # Run tray in a separate thread
        threading.Thread(target=self.tray_icon.run, daemon=True).start()

    def show_from_tray(self, icon=None, item=None):
        if self.tray_icon:
            self.tray_icon.stop()
            self.tray_icon = None
        self.root.after(0, self.root.deiconify)
        self.root.after(0, self._bring_to_front)

    def _quit_app(self, icon=None, item=None):
        if self.tray_icon:
            self.tray_icon.stop()
            self.tray_icon = None
        self.running = False
        self.queue_manager.shutdown()
        self.browser_server.stop()
        self.root.after(0, self.root.quit)

    def add_download_from_clipboard(self, url: str):
        self.root.after(0, self._bring_to_front)
        self.root.after(0, lambda: self.main_window._show_add_frame(url=url))

    def add_download_from_browser(self, url: str, filename: str = None, req_type: str = 'file'):
        self.root.after(0, self._bring_to_front)
        
        if req_type == 'video_page':
            from download_manager.services.video_extractor import extract_video_info
            from download_manager.gui.dialogs import VideoFormatDialog
            
            loading = ctk.CTkToplevel(self.root)
            loading.title("Sniffing Video")
            loading.geometry("350x100")
            loading.transient(self.root)
            loading.attributes('-topmost', True)
            ctk.CTkLabel(loading, text="Extracting video formats... Please wait.").pack(expand=True)
            
            def on_success(info):
                self.root.after(0, loading.destroy)
                self.root.after(0, lambda: VideoFormatDialog(self.root, info, self._add_video_to_ui))
                
            def on_error(err):
                self.root.after(0, loading.destroy)
                import tkinter.messagebox
                tkinter.messagebox.showerror("Extraction Error", f"Failed to extract video: {err}")
                
            extract_video_info(url, on_success, on_error)
        else:
            self.root.after(0, lambda: self.main_window._show_add_frame(url=url, filename=filename))

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
