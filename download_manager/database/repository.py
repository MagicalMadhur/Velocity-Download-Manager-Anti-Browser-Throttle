from download_manager.database.db import get_connection
from download_manager.models.download_item import DownloadItem
from typing import List, Optional
import datetime

class DownloadRepository:
    def __init__(self):
        pass

    def add_download(self, item: DownloadItem) -> int:
        conn = get_connection()
        cursor = conn.cursor()
        
        add_time = datetime.datetime.now().isoformat()
        
        cursor.execute('''
            INSERT INTO downloads 
            (url, filename, filepath, filesize, downloaded_size, status, chunks_info, etag, last_modified, sha256, category, add_time, is_ydl, ydl_format_id)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            item.url, item.filename, item.filepath, item.filesize, 
            item.downloaded_size, item.status, item.chunks_info,
            item.etag, item.last_modified, item.sha256, item.category, add_time,
            1 if item.is_ydl else 0, item.ydl_format_id
        ))
        
        conn.commit()
        item_id = cursor.lastrowid
        conn.close()
        return item_id

    def update_download(self, item: DownloadItem):
        if not item.id:
            return
            
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute('''
            UPDATE downloads 
            SET url=?, filename=?, filepath=?, filesize=?, downloaded_size=?, 
                status=?, chunks_info=?, etag=?, last_modified=?, sha256=?, 
                category=?, completion_time=?, is_ydl=?, ydl_format_id=?
            WHERE id=?
        ''', (
            item.url, item.filename, item.filepath, item.filesize, 
            item.downloaded_size, item.status, item.chunks_info,
            item.etag, item.last_modified, item.sha256, item.category, 
            item.completion_time, 1 if item.is_ydl else 0, item.ydl_format_id, item.id
        ))
        conn.commit()
        conn.close()

    def update_progress(self, item_id: int, downloaded_size: int, chunks_info: str):
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute('''
            UPDATE downloads 
            SET downloaded_size=?, chunks_info=?
            WHERE id=?
        ''', (downloaded_size, chunks_info, item_id))
        conn.commit()
        conn.close()
        
    def update_status(self, item_id: int, status: str):
        conn = get_connection()
        cursor = conn.cursor()
        if status == 'Completed':
            comp_time = datetime.datetime.now().isoformat()
            cursor.execute('UPDATE downloads SET status=?, completion_time=? WHERE id=?', (status, comp_time, item_id))
        else:
            cursor.execute('UPDATE downloads SET status=? WHERE id=?', (status, item_id))
        conn.commit()
        conn.close()

    def get_all_downloads(self) -> List[DownloadItem]:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM downloads ORDER BY id DESC')
        rows = cursor.fetchall()
        conn.close()
        
        items = []
        for row in rows:
            d = dict(row)
            d['is_ydl'] = bool(d.get('is_ydl', 0))
            items.append(DownloadItem(**d))
        return items

    def get_download(self, item_id: int) -> Optional[DownloadItem]:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM downloads WHERE id=?', (item_id,))
        row = cursor.fetchone()
        conn.close()
        
        if row:
            d = dict(row)
            d['is_ydl'] = bool(d.get('is_ydl', 0))
            return DownloadItem(**d)
        return None

    def delete_download(self, item_id: int):
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute('DELETE FROM downloads WHERE id=?', (item_id,))
        conn.commit()
        conn.close()
