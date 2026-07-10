import threading
import yt_dlp
import os
from download_manager.models.download_item import DownloadItem

class YtdlpDownloadTask:
    def __init__(self, item: DownloadItem, report_progress_cb, report_status_cb):
        self.item = item
        self.report_progress_cb = report_progress_cb
        self.report_status_cb = report_status_cb
        self.is_cancelled = False
        self.is_paused = False

    def start(self):
        self.thread = threading.Thread(target=self._run, daemon=True)
        self.thread.start()

    def cancel(self):
        self.is_cancelled = True

    def pause(self):
        self.is_paused = True

    def _run(self):
        self.report_status_cb(self.item.id, "Starting")
        
        from download_manager.services.settings import settings
        
        ydl_opts = {
            'format': self.item.ydl_format_id,
            'outtmpl': self.item.filepath,
            'concurrent_fragment_downloads': settings.get("max_threads_per_download"),
            'progress_hooks': [self._progress_hook],
            'ffmpeg_location': os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'ffmpeg.exe')),
            'quiet': True,
            'noprogress': True
        }
        
        limit_kbps = settings.get("speed_limit_kbps")
        if limit_kbps and limit_kbps > 0:
            ydl_opts['ratelimit'] = limit_kbps * 1024

        try:
            self.report_status_cb(self.item.id, "Downloading")
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                ydl.download([self.item.url])
                
            if self.is_cancelled:
                self.report_status_cb(self.item.id, "Cancelled")
            elif self.is_paused:
                self.report_status_cb(self.item.id, "Paused")
            else:
                self.report_progress_cb(self.item.id, self.item.filesize, self.item.chunks_info)
                self.report_status_cb(self.item.id, "Completed")
                
        except Exception as e:
            if "Aborted by user" in str(e):
                if self.is_cancelled:
                    self.report_status_cb(self.item.id, "Cancelled")
                elif self.is_paused:
                    self.report_status_cb(self.item.id, "Paused")
            else:
                self.report_status_cb(self.item.id, "Error")

    def _progress_hook(self, d):
        if self.is_cancelled or self.is_paused:
            raise Exception("Aborted by user")
            
        if d['status'] == 'downloading':
            downloaded = d.get('downloaded_bytes', 0)
            total = d.get('total_bytes') or d.get('total_bytes_estimate', 0)
            
            if total > 0:
                self.item.filesize = max(self.item.filesize, total)
                self.report_progress_cb(self.item.id, downloaded, self.item.chunks_info)
                
        elif d['status'] == 'finished':
            self.report_status_cb(self.item.id, "Merging...")
