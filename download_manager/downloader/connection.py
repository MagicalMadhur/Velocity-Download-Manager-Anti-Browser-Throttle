import requests
import urllib.parse
import os
import re

def get_file_info(url: str, session: requests.Session = None) -> dict:
    """
    Fetches the headers for a URL and extracts info like file size, name, etag, and range support.
    """
    if session is None:
        session = requests.Session()
    
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    }
    
    try:
        response = session.head(url, headers=headers, allow_redirects=True, timeout=10)
        if response.status_code == 405:
            # Some servers don't support HEAD
            response = session.get(url, headers=headers, stream=True, allow_redirects=True, timeout=10)
            
        response.raise_for_status()
        
        # Check range support
        accept_ranges = response.headers.get("Accept-Ranges", "")
        range_supported = accept_ranges.lower() == "bytes"
        
        # Filesize
        content_length = response.headers.get("Content-Length")
        filesize = int(content_length) if content_length and content_length.isdigit() else 0
        
        if filesize == 0:
            range_supported = False
            
        # Filename extraction
        filename = None
        cd = response.headers.get("Content-Disposition")
        if cd:
            # e.g., attachment; filename="foo.ext"
            fname_match = re.findall('filename="?([^"]+)"?', cd)
            if fname_match:
                filename = fname_match[0]
                
        if not filename:
            # Fallback to url parsing
            parsed = urllib.parse.urlparse(response.url)
            filename = os.path.basename(urllib.parse.unquote(parsed.path))
            
        if not filename:
            filename = "downloaded_file"
            
        # Meta
        etag = response.headers.get("ETag")
        last_modified = response.headers.get("Last-Modified")
        
        return {
            "url": response.url,
            "filename": filename,
            "filesize": filesize,
            "range_supported": range_supported,
            "etag": etag,
            "last_modified": last_modified
        }
        
    except Exception as e:
        raise Exception(f"Failed to fetch file info: {str(e)}")
