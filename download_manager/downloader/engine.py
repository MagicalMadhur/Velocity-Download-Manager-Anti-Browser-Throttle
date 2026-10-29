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
        self.custom_headers = self.item.get_headers()
        self.session = requests.Session()
        default_ua = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/120.0.0.0"
        self.session.headers.update({
            "User-Agent": self.custom_headers.get("User-Agent", default_ua)
        })
        if self.custom_headers:
            for k, v in self.custom_headers.items():
                if k.lower() != "user-agent":
                    self.session.headers[k] = v
        
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
            info = get_file_info(self.item.url, self.session, self.custom_headers)
            
            # If the URL redirected to a direct pre-signed blob/CDN URL, record it
            if info.get('url') and info['url'] != self.item.url:
                self.item.url = info['url']
            
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
        response = None
        try:
            response = self.session.get(self.item.url, stream=True, timeout=15)
            response.raise_for_status()
            
            with open(self.item.filepath, 'wb') as f:
                downloaded = 0
                for chunk in response.iter_content(chunk_size=131072):
                    if self.is_paused or self.is_cancelled:
                        break
                    if chunk:
                        if self.item.filesize > 0:
                            remaining = self.item.filesize - downloaded
                            if remaining <= 0:
                                break
                            chunk = chunk[:remaining]
                            
                        global_limiter.consume(len(chunk))
                        f.write(chunk)
                        downloaded += len(chunk)
                        self.item.downloaded_size = downloaded
                        if self.progress_callback:
                            self.progress_callback(self.item.id, downloaded, "{}")
                            
                        if self.item.filesize > 0 and downloaded >= self.item.filesize:
                            break
        except Exception as e:
            raise e
        finally:
            if response is not None:
                try:
                    response.close()
                except Exception:
                    pass

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
            part_total = end - start + 1
            downloaded = self.chunks_info_dict.get(str_i, 0)
            if downloaded < part_total:
                current_start = start + downloaded
                tasks.append((str_i, start, end))

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
                
            with self._lock:
                current_total = sum(self.chunks_info_dict.values())
                if self.item.filesize > 0 and current_total >= self.item.filesize:
                    # All bytes received!
                    break
                
            current_time = time.time()
            if current_time - last_update_time > 0.5: # 2 FPS update
                if self.progress_callback:
                    with self._lock:
                        self.item.downloaded_size = current_total
                        self.item.set_chunks(self.chunks_info_dict)
                        self.progress_callback(self.item.id, self.item.downloaded_size, self.item.chunks_info)
                last_update_time = current_time
            time.sleep(0.1)

        # Final progress update
        with self._lock:
            self.item.downloaded_size = sum(self.chunks_info_dict.values())
            self.item.set_chunks(self.chunks_info_dict)
            if self.progress_callback:
                self.progress_callback(self.item.id, self.item.downloaded_size, self.item.chunks_info)

        self.executor.shutdown(wait=False, cancel_futures=True)

    def _download_part(self, task_id: str, start: int, end: int):
        part_total = end - start + 1
        retries = 0
        max_retries = 10
        
        while retries < max_retries:
            if self.is_paused or self.is_cancelled or self.has_error:
                break
                
            current_downloaded = self.chunks_info_dict.get(task_id, 0)
            if current_downloaded >= part_total:
                break  # Already finished this part!
                
            current_start = start + current_downloaded
            headers = {"Range": f"bytes={current_start}-{end}"}
            if self.custom_headers:
                for k, v in self.custom_headers.items():
                    if k.lower() not in ["user-agent", "range"]:
                        headers[k] = v

            response = None
            try:
                response = self.session.get(self.item.url, headers=headers, stream=True, timeout=15)
                response.raise_for_status()
                
                # Open file specifically for this thread
                with open(self.item.filepath, 'rb+') as f:
                    f.seek(current_start)
                    
                    for chunk in response.iter_content(chunk_size=131072): # 128KB chunks
                        if self.is_paused or self.is_cancelled or self.has_error:
                            break
                        if chunk:
                            current_dl = self.chunks_info_dict.get(task_id, 0)
                            remaining = part_total - current_dl
                            if remaining <= 0:
                                break
                            to_write = chunk[:remaining]
                            global_limiter.consume(len(to_write))
                            f.write(to_write)
                            self.chunks_info_dict[task_id] = current_dl + len(to_write)
                            if self.chunks_info_dict[task_id] >= part_total:
                                break  # Finished all bytes for this part!
                
                # Check if this part finished
                if self.chunks_info_dict.get(task_id, 0) >= part_total:
                    break
                    
                if not (self.is_paused or self.is_cancelled or self.has_error):
                    break
                    
            except Exception as e:
                retries += 1
                print(f"Part {task_id} failed: {e}. Retrying {retries}/{max_retries}...")
                time.sleep(2 * retries) # Exponential backoff
            finally:
                if response is not None:
                    try:
                        response.close()
                    except Exception:
                        pass
                
        if retries >= max_retries and self.chunks_info_dict.get(task_id, 0) < part_total:
            self.has_error = True
