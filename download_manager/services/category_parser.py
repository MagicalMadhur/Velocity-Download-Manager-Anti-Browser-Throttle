import os

CATEGORIES = {
    "Videos": [".mp4", ".mkv", ".avi", ".mov", ".wmv", ".flv"],
    "Documents": [".pdf", ".doc", ".docx", ".txt", ".rtf", ".xls", ".xlsx", ".ppt", ".pptx"],
    "Images": [".jpg", ".jpeg", ".png", ".gif", ".bmp", ".svg", ".webp"],
    "Archives": [".zip", ".rar", ".7z", ".tar", ".gz", ".bz2"],
    "Software": [".exe", ".msi", ".apk", ".dmg", ".iso"],
    "Music": [".mp3", ".wav", ".flac", ".aac", ".ogg"]
}

def get_category(filename: str) -> str:
    ext = os.path.splitext(filename)[1].lower()
    for cat, extensions in CATEGORIES.items():
        if ext in extensions:
            return cat
    return "Uncategorized"
