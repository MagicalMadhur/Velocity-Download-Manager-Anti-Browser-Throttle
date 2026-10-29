import requests
import urllib.parse
import os
import re

def get_file_info(url: str, session: requests.Session = None, custom_headers: dict = None) -> dict:
    """
    Fetches the headers for a URL and extracts info like file size, name, etag, and range support.
    """
    if session is None:
        session = requests.Session()
    
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    }
    if custom_headers:
        headers.update(custom_headers)
    
    try:
        response = None
        # Try HEAD request first
        try:
            head_resp = session.head(url, headers=headers, allow_redirects=True, timeout=10)
            if head_resp.status_code < 400:
                response = head_resp
        except Exception:
            pass

        # If HEAD failed, wasn't allowed, or returned an error status (like 403/405), fallback to GET stream
        if response is None:
            response = session.get(url, headers=headers, stream=True, allow_redirects=True, timeout=12)
            
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
            # Check for RFC 5987 format (filename*=UTF-8''...)
            fname_star = re.findall(r"filename\*\s*=\s*(?:UTF-8''|utf-8'')([^;]+)", cd, re.IGNORECASE)
            if fname_star:
                filename = urllib.parse.unquote(fname_star[0].strip().strip('"\''))
            else:
                fname_match = re.findall(r'filename\s*=\s*"?([^";]+)"?', cd)
                if fname_match:
                    filename = fname_match[0].strip().strip('"\'')
                
        if not filename:
            # Fallback to url parsing
            parsed = urllib.parse.urlparse(response.url)
            filename = os.path.basename(urllib.parse.unquote(parsed.path))
            
        if not filename or filename.strip() == "":
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

