from dataclasses import dataclass, field
from typing import Optional, Dict
import json

@dataclass
class DownloadItem:
    id: Optional[int] = None
    url: str = ""
    filename: str = ""
    filepath: str = ""
    filesize: int = 0
    downloaded_size: int = 0
    status: str = "Pending"  # Pending, Downloading, Paused, Completed, Error, Cancelled
    chunks_info: str = "{}"  # JSON string of chunk progress {chunk_id: bytes_downloaded}
    etag: Optional[str] = None
    last_modified: Optional[str] = None
    sha256: Optional[str] = None
    category: str = "Uncategorized"
    speed: int = 0
    eta: str = ""
    add_time: str = ""
    completion_time: Optional[str] = None
    is_ydl: bool = False
    ydl_format_id: Optional[str] = None
    headers: str = "{}"  # JSON string of custom HTTP headers (cookies, referer, user-agent)

    def get_chunks(self) -> Dict[str, int]:
        try:
            return json.loads(self.chunks_info)
        except json.JSONDecodeError:
            return {}

    def set_chunks(self, chunks: Dict[str, int]):
        self.chunks_info = json.dumps(chunks)

    def get_headers(self) -> Dict[str, str]:
        try:
            return json.loads(self.headers) if self.headers else {}
        except (json.JSONDecodeError, TypeError):
            return {}

    def set_headers(self, headers: Dict[str, str]):
        self.headers = json.dumps(headers) if headers else "{}"
