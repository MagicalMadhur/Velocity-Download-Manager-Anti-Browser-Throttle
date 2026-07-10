import sqlite3
import os
from pathlib import Path

DB_FILE = os.path.join(Path.home(), ".download_manager", "downloads.db")

def get_connection():
    os.makedirs(os.path.dirname(DB_FILE), exist_ok=True)
    conn = sqlite3.connect(DB_FILE, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS downloads (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            url TEXT NOT NULL,
            filename TEXT NOT NULL,
            filepath TEXT NOT NULL,
            filesize INTEGER DEFAULT 0,
            downloaded_size INTEGER DEFAULT 0,
            status TEXT DEFAULT 'Pending',
            chunks_info TEXT DEFAULT '{}',
            etag TEXT,
            last_modified TEXT,
            sha256 TEXT,
            category TEXT DEFAULT 'Uncategorized',
            add_time TEXT,
            completion_time TEXT,
            is_ydl INTEGER DEFAULT 0,
            ydl_format_id TEXT
        )
    ''')
    
    # Configuration table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS config (
            key TEXT PRIMARY KEY,
            value TEXT
        )
    ''')
    
    try:
        cursor.execute("ALTER TABLE downloads ADD COLUMN is_ydl INTEGER DEFAULT 0")
        cursor.execute("ALTER TABLE downloads ADD COLUMN ydl_format_id TEXT")
    except sqlite3.OperationalError:
        pass
    
    conn.commit()
    conn.close()

if __name__ == "__main__":
    init_db()
