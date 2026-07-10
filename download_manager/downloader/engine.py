import os
import time
import requests
import threading
import concurrent.futures
from typing import Callable, Dict

from download_manager.models.download_item import DownloadItem
from download_manager.downloader.connection import get_file_info
from download_manager.downloader.file_manager import FileManager
from download_manager.services.settings import settings

class GlobalRateLimiter:
    def __init__(self):
        self.lock = threading.Lock()
        self.tokens = 0.0
        self.last_update = time.time()

    def consume(self, amount: int):
        rate_kbps = settings.get("speed_limit_kbps")
        if not rate_kbps or rate_kbps <= 0:
            return
            
        rate_bps = rate_kbps * 1024
        capacity = rate_bps
        
        while True:
            with self.lock:
                now = time.time()
                elapsed = now - self.last_update
                self.tokens = min(capacity, self.tokens + elapsed * rate_bps)
                self.last_update = now

                if self.tokens >= amount:
                    self.tokens -= amount
                    return
                sleep_time = (amount - self.tokens) / rate_bps
                
            time.sleep(min(sleep_time, 0.1))

global_limiter = GlobalRateLimiter()

class DownloadTask:
    def __init__(self, item: DownloadItem, num_threads: int = None, 
                 progress_callback: Callable = None, 
                 status_callback: Callable = None):
        self.item = item
        self.num_threads = num_threads if num_threads else settings.get("max_threads_per_download")
        self.progress_callback = progress_callback
        self.status_callback = status_callback
        self.session = requests.Session()
        self.session.headers.update({
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/120.0.0.0"
        })
        
        self.is_paused = False
        self.is_cancelled = False
        self.has_error = False
        self._lock = threading.RLock()
        
        self.chunk_size = 1024 * 1024  # 1MB chunk sizes logically for splitting
        self.executor = None
        self.futures = []

    def pause(self):
        self.is_paused = True
        self._update_status("Paused")

    def cancel(self):
        self.is_cancelled = True
        self.is_paused = True
        self._update_status("Cancelled")
        
    def _update_status(self, status: str):
        self.item.status = status
        if self.status_callback:
            self.status_callback(self.item.id, status)

    def start(self):
        threading.Thread(target=self._run, daemon=True).start()

    def _run(self):
        try:
            self._update_status("Starting")
            
            # 1. Fetch info
            info = get_file_info(self.item.url, self.session)
            
            # If size changed or it's a completely new file, reset progress
            if self.item.filesize != 0 and self.item.filesize != info['filesize']:
                # The file changed on server! Restart
                self.item.downloaded_size = 0
                self.item.set_chunks({})
            elif self.item.etag and info['etag'] and self.item.etag != info['etag']:
                self.item.downloaded_size = 0
                self.item.set_chunks({})
            elif self.item.last_modified and info['last_modified'] and self.item.last_modified != info['last_modified']:
                self.item.downloaded_size = 0
                self.item.set_chunks({})
                
            self.item.filesize = info['filesize']
            self.item.etag = info['etag']
            self.item.last_modified = info['last_modified']
            range_supported = info['range_supported']
            
            # 2. Preallocate
            FileManager.preallocate_file(self.item.filepath, self.item.filesize)
            
            if self.item.filesize == 0:
                # Unknown size, single thread mode
                range_supported = False
                
            self._update_status("Downloading")
            
            if not range_supported:
                self._download_single_thread()
            else:
                self._download_multi_thread()
                
            if self.has_error:
                self._update_status("Error")
            elif not self.is_paused and not self.is_cancelled:
                self._update_status("Completed")
                
        except Exception as e:
            if not self.is_paused and not self.is_cancelled:
                print(f"Download error: {e}")
                self._update_status("Error")

    def _download_single_thread(self):
        try:
            response = self.session.get(self.item.url, stream=True, timeout=10)
            response.raise_for_status()
            
            with open(self.item.filepath, 'wb') as f:
                downloaded = 0
                for chunk in response.iter_content(chunk_size=8192):
                    if self.is_paused or self.is_cancelled:
                        break
                    if chunk:
                        global_limiter.consume(len(chunk))
                        f.write(chunk)
                        downloaded += len(chunk)
                        self.item.downloaded_size = downloaded
                        if self.progress_callback:
                            self.progress_callback(self.item.id, downloaded, "{}")
        except Exception as e:
            raise e

    def _download_multi_thread(self):
        # Calculate parts
        part_size = max(1024 * 1024, self.item.filesize // self.num_threads)
        
        ranges = []
        for i in range(self.num_threads):
            start = i * part_size
            end = start + part_size - 1 if i < self.num_threads - 1 else self.item.filesize - 1
            ranges.append((i, start, end))
            
        self.chunks_info_dict = self.item.get_chunks()
        
        # Calculate remaining
        tasks = []
        for i, start, end in ranges:
            str_i = str(i)
            downloaded = self.chunks_info_dict.get(str_i, 0)
            current_start = start + downloaded
            if current_start <= end:
                tasks.append((str_i, current_start, end))

        self.executor = concurrent.futures.ThreadPoolExecutor(max_workers=self.num_threads)
        self.futures = []
        
        for task_id, start, end in tasks:
            future = self.executor.submit(self._download_part, task_id, start, end)
            self.futures.append(future)
            
        # Monitor
        last_update_time = time.time()
        while any(not f.done() for f in self.futures):
            if self.is_paused or self.is_cancelled or self.has_error:
                break
                
            current_time = time.time()
            if current_time - last_update_time > 0.5: # 2 FPS update
                if self.progress_callback:
                    with self._lock:
                        self.item.downloaded_size = sum(self.chunks_info_dict.values())
                        self.item.set_chunks(self.chunks_info_dict)
                        self.progress_callback(self.item.id, self.item.downloaded_size, self.item.chunks_info)
                last_update_time = current_time
            time.sleep(0.1)

        # Final progress update
        if self.progress_callback:
            with self._lock:
                self.item.downloaded_size = sum(self.chunks_info_dict.values())
                self.item.set_chunks(self.chunks_info_dict)
                self.progress_callback(self.item.id, self.item.downloaded_size, self.item.chunks_info)

        self.executor.shutdown(wait=True)

    def _download_part(self, task_id: str, start: int, end: int):
        retries = 0
        max_retries = 10
        
        while retries < max_retries:
            if self.is_paused or self.is_cancelled or self.has_error:
                break
                
            current_start = start + self.chunks_info_dict.get(task_id, 0)
            if current_start > end:
                break  # Finished
                
            headers = {"Range": f"bytes={current_start}-{end}"}
            try:
                response = self.session.get(self.item.url, headers=headers, stream=True, timeout=15)
                response.raise_for_status()
                
                # Open file specifically for this thread
                with open(self.item.filepath, 'rb+') as f:
                    f.seek(current_start)
                    
                    for chunk in response.iter_content(chunk_size=1048576): # 1MB chunk sizes to reduce lock overhead
                        if self.is_paused or self.is_cancelled or self.has_error:
                            break
                        if chunk:
                            global_limiter.consume(len(chunk))
                            f.write(chunk)
                            self.chunks_info_dict[task_id] = self.chunks_info_dict.get(task_id, 0) + len(chunk)
                
                # If finished without exception, break out of retry loop
                if not (self.is_paused or self.is_cancelled or self.has_error):
                    break
                    
            except Exception as e:
                retries += 1
                print(f"Part {task_id} failed: {e}. Retrying {retries}/{max_retries}...")
                time.sleep(2 * retries) # Exponential backoff
                
        if retries >= max_retries:
            self.has_error = True
