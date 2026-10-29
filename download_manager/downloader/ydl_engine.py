import threading
import yt_dlp
import os
import sys
from download_manager.models.download_item import DownloadItem

def get_ffmpeg_path() -> str:
    """Finds the ffmpeg executable across dev, PyInstaller onedir, or onefile environments."""
    if hasattr(sys, '_MEIPASS'):
        p = os.path.join(sys._MEIPASS, 'download_manager', 'ffmpeg.exe')
        if os.path.exists(p):
            return p
            
    if getattr(sys, 'frozen', False):
        exe_dir = os.path.dirname(sys.executable)
        candidates = [
            os.path.join(exe_dir, '_internal', 'download_manager', 'ffmpeg.exe'),
            os.path.join(exe_dir, 'download_manager', 'ffmpeg.exe'),
            os.path.join(exe_dir, 'ffmpeg.exe'),
        ]
        for c in candidates:
            if os.path.exists(c):
                return os.path.abspath(c)
                
    this_dir = os.path.dirname(os.path.abspath(__file__))
    candidates = [
        os.path.join(this_dir, '..', 'ffmpeg.exe'),
        os.path.join(this_dir, 'ffmpeg.exe'),
        os.path.abspath('download_manager/ffmpeg.exe')
    ]
    for c in candidates:
        if os.path.exists(c):
            return os.path.abspath(c)
            
    return 'ffmpeg.exe'

class YtdlpDownloadTask:
    def __init__(self, item: DownloadItem, report_progress_cb, report_status_cb):
        self.item = item
        self.report_progress_cb = report_progress_cb
        self.report_status_cb = report_status_cb
        self.is_cancelled = False
        self.is_paused = False
        self._stream_sizes = {}
        self._stream_downloaded = {}

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
        
        is_audio_only = self.item.ydl_format_id and ('audio' in self.item.ydl_format_id and 'video' not in self.item.ydl_format_id)
        
        outtmpl = self.item.filepath
        if not self.item.filename or self.item.filename.lower() in ('watch', 'downloaded_file', 'video', 'video.mp4', 'watch.mp4'):
            save_dir = os.path.dirname(self.item.filepath) if os.path.dirname(self.item.filepath) else "."
            outtmpl = os.path.join(save_dir, '%(title)s.%(ext)s')

        # Cap concurrent fragments to 4 to prevent YouTube CDN 403 rate-limiting
        cfg_threads = settings.get("max_threads_per_download") or 4
        frag_threads = min(max(1, cfg_threads), 4)

        fmt = self.item.ydl_format_id or 'bestvideo+bestaudio/best'
        # Ensure format selector has a safe fallback chain so downloads never stall if a format ID is restricted
        if fmt and '/best' not in fmt:
            fmt = f"{fmt}/bestvideo+bestaudio/best"

        ydl_opts = {
            'format': fmt,
            'outtmpl': outtmpl,
            'concurrent_fragment_downloads': frag_threads,
            'retries': 10,
            'fragment_retries': 10,
            'progress_hooks': [self._progress_hook],
            'ffmpeg_location': get_ffmpeg_path(),
            'quiet': True,
            'noprogress': True,
            'noplaylist': True,
        }
        
        if not is_audio_only:
            ydl_opts['merge_output_format'] = 'mp4'
        
        limit_kbps = settings.get("speed_limit_kbps")
        if limit_kbps and limit_kbps > 0:
            ydl_opts['ratelimit'] = limit_kbps * 1024
            
        if settings.get("normalize_audio"):
            filter_args = ['-af', 'loudnorm=I=-14:LRA=11:TP=-1.5']
            ydl_opts['postprocessor_args'] = {
                'Merger': ['-c:a', 'aac'] + filter_args,
                'ExtractAudio': filter_args
            }
            if self.item.ydl_format_id and '+' not in self.item.ydl_format_id:
                ydl_opts['postprocessors'] = [{
                    'key': 'FFmpegExtractAudio',
                    'preferredcodec': 'best'
                }]

        try:
            self.report_status_cb(self.item.id, "Downloading")
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(self.item.url, download=True)
                if info:
                    try:
                        prep = ydl.prepare_filename(info)
                        if not is_audio_only and not prep.endswith('.mp4'):
                            mp4_cand = os.path.splitext(prep)[0] + '.mp4'
                            if os.path.exists(mp4_cand):
                                prep = mp4_cand
                        if os.path.exists(prep):
                            self.item.filepath = prep
                            self.item.filename = os.path.basename(prep)
                    except Exception:
                        pass
                
            if self.is_cancelled:
                self.report_status_cb(self.item.id, "Cancelled")
            elif self.is_paused:
                self.report_status_cb(self.item.id, "Paused")
            else:
                # Detect the final file on disk in case container format was merged to mp4
                if not os.path.exists(self.item.filepath):
                    base_no_ext = os.path.splitext(self.item.filepath)[0]
                    dir_path = os.path.dirname(self.item.filepath)
                    if os.path.exists(dir_path):
                        for f in os.listdir(dir_path):
                            full_f = os.path.join(dir_path, f)
                            if os.path.splitext(full_f)[0] == base_no_ext:
                                self.item.filepath = full_f
                                self.item.filename = f
                                break
                                
                if os.path.exists(self.item.filepath):
                    actual_size = os.path.getsize(self.item.filepath)
                    self.item.filesize = actual_size
                    self.item.downloaded_size = actual_size
                    
                self.report_progress_cb(self.item.id, self.item.downloaded_size, self.item.chunks_info)
                self.report_status_cb(self.item.id, "Completed")
                
        except Exception as e:
            if "Aborted by user" in str(e):
                if self.is_cancelled:
                    self.report_status_cb(self.item.id, "Cancelled")
                elif self.is_paused:
                    self.report_status_cb(self.item.id, "Paused")
            else:
                print(f"yt-dlp download error: {e}")
                self.report_status_cb(self.item.id, "Error")

    def _progress_hook(self, d):
        if self.is_cancelled or self.is_paused:
            raise Exception("Aborted by user")
            
        status = d.get('status')
        if status == 'downloading':
            stream_key = d.get('filename') or d.get('tmpfilename') or 'main_stream'
            dl = d.get('downloaded_bytes', 0)
            tot = d.get('total_bytes') or d.get('total_bytes_estimate', 0) or 0
            
            # For fragment downloads without total_bytes, estimate from fragment_count if available
            frag_idx = d.get('fragment_index')
            frag_count = d.get('fragment_count')
            if tot <= 0 and frag_idx is not None and frag_count is not None and frag_idx > 0:
                tot = int((dl / max(1, frag_idx)) * frag_count)

            if tot > 0:
                self._stream_sizes[stream_key] = tot
            self._stream_downloaded[stream_key] = dl
            
            total_dl = sum(self._stream_downloaded.values())
            total_exp = sum(self._stream_sizes.values())
            
            if total_exp > 0:
                self.item.filesize = max(self.item.filesize, total_exp)
                
            self.item.downloaded_size = total_dl
            self.report_progress_cb(self.item.id, total_dl, self.item.chunks_info)
            
        elif status == 'finished':
            stream_key = d.get('filename') or d.get('tmpfilename') or 'main_stream'
            tot = d.get('total_bytes') or self._stream_sizes.get(stream_key, 0)
            if tot > 0:
                self._stream_sizes[stream_key] = tot
                self._stream_downloaded[stream_key] = tot
                self.item.downloaded_size = sum(self._stream_downloaded.values())
            self.report_status_cb(self.item.id, "Merging...")
