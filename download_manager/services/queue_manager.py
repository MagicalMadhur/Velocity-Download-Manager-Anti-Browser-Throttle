import threading
import time
from typing import Dict, List, Callable
from download_manager.downloader.engine import DownloadTask
from download_manager.models.download_item import DownloadItem
from download_manager.downloader.ydl_engine import YtdlpDownloadTask

class QueueManager:
    def __init__(self, max_concurrent_downloads: int = 3):
        self.max_concurrent_downloads = max_concurrent_downloads
        self.active_tasks: Dict[int, DownloadTask] = {}
        self.queue: List[DownloadItem] = []
        self._lock = threading.RLock()
        self.progress_callback = None
        self.status_callback = None
        
        self.is_running = True
        self.download_occurred = False
        self._worker_thread = threading.Thread(target=self._process_queue, daemon=True)
        self._worker_thread.start()

    def set_callbacks(self, progress_cb: Callable, status_cb: Callable):
        self.progress_callback = progress_cb
        self.status_callback = status_cb

    def add_to_queue(self, item: DownloadItem):
        with self._lock:
            if item.status == "Downloading" or item.status == "Paused":
                # Already in system, let's start it if not active
                if item.id not in self.active_tasks:
                    self.queue.append(item)
            else:
                item.status = "Pending"
                self.queue.append(item)

    def start_task(self, item: DownloadItem, num_threads: int = 32):
        with self._lock:
            if item.id in self.active_tasks:
                return # Already active
                
            item.status = "Starting"
            self._on_status(item.id, "Starting")
            
            if item.is_ydl:
                task = YtdlpDownloadTask(item, self._on_progress, self._on_status)
            else:
                task = DownloadTask(item, num_threads=num_threads, progress_callback=self._on_progress, status_callback=self._on_status)
                
            self.active_tasks[item.id] = task
            task.start()

    def pause_task(self, item_id: int):
        with self._lock:
            if item_id in self.active_tasks:
                self.active_tasks[item_id].pause()
                del self.active_tasks[item_id]

    def pause_all(self):
        with self._lock:
            for task in list(self.active_tasks.values()):
                task.pause()
            self.active_tasks.clear()
            self.queue.clear()

    def cancel_task(self, item_id: int):
        with self._lock:
            if item_id in self.active_tasks:
                self.active_tasks[item_id].cancel()
                del self.active_tasks[item_id]

    def _on_progress(self, item_id: int, downloaded: int, chunks_info: str):
        if self.progress_callback:
            self.progress_callback(item_id, downloaded, chunks_info)

    def _on_status(self, item_id: int, status: str):
        if status in ["Completed", "Error", "Cancelled", "Paused"]:
            with self._lock:
                if item_id in self.active_tasks:
                    del self.active_tasks[item_id]
            if status == "Completed":
                self.download_occurred = True
                from download_manager.services.settings import settings
                if settings.get("play_sound_on_complete"):
                    import winsound
                    winsound.MessageBeep(winsound.MB_ICONASTERISK)
                    
        if self.status_callback:
            self.status_callback(item_id, status)

    def _process_queue(self):
        import os
        from download_manager.services.settings import settings
        while self.is_running:
            with self._lock:
                max_concurrent = settings.get("max_concurrent_downloads")
                
                # Start new tasks if we have capacity
                while len(self.active_tasks) < max_concurrent and self.queue:
                    next_item = self.queue.pop(0)
                    self.start_task(next_item)
                    
                # Check for shutdown
                if self.download_occurred and len(self.active_tasks) == 0 and len(self.queue) == 0:
                    if settings.get("shutdown_after_download"):
                        os.system("shutdown /s /t 60")
                        self.download_occurred = False # Prevent looping shutdown command
                    
            time.sleep(1)

    def shutdown(self):
        self.is_running = False
        self.pause_all()
