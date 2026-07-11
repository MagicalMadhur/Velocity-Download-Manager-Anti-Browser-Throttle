import yt_dlp
import threading

def extract_video_info(url, callback, error_callback):
    """Runs in a thread to prevent blocking UI"""
    def _extract():
        ydl_opts = {
            'quiet': True,
            'no_warnings': True,
            'noplaylist': True,
            'js_runtimes': ['node']
        }
        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=False)
                title = info.get('title', 'Unknown_Video')
                
                # Sanitize title for filename
                title = "".join(c for c in title if c.isalnum() or c in (' ', '-', '_')).rstrip()
                
                formats = []
                seen = set()
                
                for f in info.get('formats', []):
                    has_video = f.get('vcodec') != 'none'
                    has_audio = f.get('acodec') != 'none'
                    
                    if has_video and has_audio:
                        res = f.get('height', 0)
                        if res > 0:
                            label = f"{res}p Video ({f.get('ext')})"
                            if label not in seen:
                                seen.add(label)
                                formats.append({
                                    'label': label,
                                    'url': f.get('url'),
                                    'ext': f.get('ext'),
                                    'res': res
                                })
                    elif not has_video and has_audio:
                        label = f"Audio Only ({f.get('ext')})"
                        if label not in seen:
                            seen.add(label)
                            formats.append({
                                'label': label,
                                'url': f.get('url'),
                                'ext': f.get('ext'),
                                'res': 0,
                                'format_id': f.get('format_id')
                            })
                    elif has_video and not has_audio:
                        res = f.get('height', 0)
                        if res >= 1080: # Only bother showing 1080p+ if it's muted
                            # If we use auto-merger, we can pass bestaudio format_id to yt-dlp to merge automatically!
                            # Let's find bestaudio
                            audio_format = 'bestaudio'
                            label = f"{res}p Video (Auto-Merged with Sound) ({f.get('ext')})"
                            if label not in seen:
                                seen.add(label)
                                formats.append({
                                    'label': label,
                                    'url': f.get('url'),
                                    'ext': f.get('ext'),
                                    'res': res,
                                    'format_id': f"{f.get('format_id')}+{audio_format}"
                                })
                            
                # Sort by resolution descending
                formats.sort(key=lambda x: x['res'], reverse=True)
                
                callback({
                    'original_url': url,
                    'title': title,
                    'formats': formats
                })
        except Exception as e:
            error_callback(str(e))
            
    threading.Thread(target=_extract, daemon=True).start()
