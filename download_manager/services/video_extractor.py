import yt_dlp
import threading
from urllib.parse import urlparse

# In-memory cache for extracted video info to make repeated lookups instant
_VIDEO_CACHE = {}

def is_video_url(url: str) -> bool:
    """Detects whether a URL is from a known video hosting platform."""
    if not url or not isinstance(url, str):
        return False
    try:
        parsed = urlparse(url.strip())
        netloc = parsed.netloc.lower()
        for prefix in ['www.', 'm.', 'music.']:
            if netloc.startswith(prefix):
                netloc = netloc[len(prefix):]
                
        video_domains = {
            'youtube.com', 'youtu.be', 'vimeo.com', 'dailymotion.com',
            'tiktok.com', 'twitter.com', 'x.com', 'facebook.com', 'fb.watch',
            'instagram.com', 'twitch.tv', 'reddit.com'
        }
        
        for vd in video_domains:
            if netloc == vd or netloc.endswith('.' + vd):
                return True
        return False
    except Exception:
        return False

def extract_video_info(url, callback, error_callback):
    """Runs in a background thread to prevent blocking the UI with ultra-fast extraction options"""
    # 1. Check in-memory cache for instant response
    if url in _VIDEO_CACHE:
        callback(_VIDEO_CACHE[url])
        return

    def _extract():
        # High performance options: avoid slow checks, probing, and external node runtime startup latency
        ydl_opts = {
            'quiet': True,
            'no_warnings': True,
            'noplaylist': True,
            'skip_download': True,
            'check_formats': False, # Avoid probing every individual stream URL
            'youtube_include_dash_manifest': False, # Avoid slow extra manifest requests
            'youtube_include_hls_manifest': False,
            'extract_flat': False,
            'socket_timeout': 8,
        }
        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=False)
                raw_title = info.get('title', 'video')
                
                # Sanitize title for Windows filename
                clean_title = "".join(c for c in raw_title if c.isalnum() or c in (' ', '-', '_', '.', '(', ')')).strip()
                if not clean_title:
                    clean_title = "downloaded_video"
                
                formats = []
                
                # 1. Best Quality Available (Max resolution + audio merged)
                formats.append({
                    'label': 'Best Quality Available (Max Resolution + Audio)',
                    'ext': 'mp4',
                    'res': 99999,
                    'format_id': 'bestvideo+bestaudio/best'
                })
                
                # 2. Group all video formats by height
                res_map = {}
                for f in info.get('formats', []):
                    h = f.get('height')
                    if not h or h <= 0:
                        continue
                    if f.get('vcodec') == 'none':
                        continue
                    if h not in res_map:
                        res_map[h] = []
                    res_map[h].append(f)
                
                for h in sorted(res_map.keys(), reverse=True):
                    flist = res_map[h]
                    # Score formats: prefer direct HTTPS/HTTP streams, then mp4 extension, known size, and highest bitrate
                    def _score_format(f):
                        proto = (f.get('protocol') or '').lower()
                        is_direct = 1 if (proto in ('https', 'http') and not proto.startswith('m3u8')) else 0
                        is_mp4 = 1 if f.get('ext') == 'mp4' else 0
                        has_size = 1 if (f.get('filesize') or f.get('filesize_approx')) else 0
                        tbr = f.get('tbr') or 0
                        return (is_direct, is_mp4, has_size, tbr)

                    flist.sort(key=_score_format, reverse=True)
                    best_f = flist[0]
                    fid = best_f.get('format_id')
                    has_audio = best_f.get('acodec') != 'none'
                    
                    if h >= 2160:
                        res_tag = f"4K ({h}p)"
                    elif h >= 1440:
                        res_tag = f"2K ({h}p)"
                    elif h >= 1080:
                        res_tag = f"Full HD ({h}p)"
                    elif h >= 720:
                        res_tag = f"HD ({h}p)"
                    else:
                        res_tag = f"{h}p"
                        
                    if has_audio:
                        label = f"{res_tag} Video ({best_f.get('ext', 'mp4')})"
                        fmt_id = f"{fid}/bestvideo[height<={h}]+bestaudio/best[height<={h}]/best"
                    else:
                        label = f"{res_tag} Video (Merged with Audio) (mp4)"
                        fmt_id = f"{fid}+bestaudio/bestvideo[height<={h}]+bestaudio/best[height<={h}]/best"
                        
                    formats.append({
                        'label': label,
                        'ext': 'mp4',
                        'res': h,
                        'format_id': fmt_id
                    })
                
                # 3. Audio Only option
                formats.append({
                    'label': 'Audio Only (Best Quality Audio)',
                    'ext': 'm4a',
                    'res': 0,
                    'format_id': 'bestaudio/best'
                })
                
                result_data = {
                    'original_url': url,
                    'title': clean_title,
                    'formats': formats
                }
                _VIDEO_CACHE[url] = result_data
                callback(result_data)
        except Exception as e:
            error_callback(str(e))
            
    threading.Thread(target=_extract, daemon=True).start()
