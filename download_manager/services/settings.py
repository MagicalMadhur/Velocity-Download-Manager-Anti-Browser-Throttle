import os
import json
import threading

SETTINGS_DIR = os.path.join(os.environ.get('LOCALAPPDATA', os.path.expanduser('~')), 'VelocityDownloadManager')
SETTINGS_FILE = os.path.join(SETTINGS_DIR, 'settings.json')

class SettingsManager:
    _instance = None
    _lock = threading.Lock()

    def __new__(cls):
        with cls._lock:
            if cls._instance is None:
                cls._instance = super(SettingsManager, cls).__new__(cls)
                cls._instance._init()
            return cls._instance

    def _init(self):
        self.settings = {
            "default_download_path": os.path.expanduser("~/Downloads"),
            "launch_on_startup": False,
            "max_concurrent_downloads": 3,
            "speed_limit_kbps": 0,  # 0 means unlimited
            "max_threads_per_download": 32,
            "shutdown_after_download": False,
            "play_sound_on_complete": True,
            "normalize_audio": True
        }
        self._load()

    def _load(self):
        if not os.path.exists(SETTINGS_DIR):
            os.makedirs(SETTINGS_DIR, exist_ok=True)
            
        if os.path.exists(SETTINGS_FILE):
            try:
                with open(SETTINGS_FILE, 'r') as f:
                    loaded = json.load(f)
                    self.settings.update(loaded)
            except Exception:
                pass

    def save(self):
        try:
            if not os.path.exists(SETTINGS_DIR):
                os.makedirs(SETTINGS_DIR, exist_ok=True)
            with open(SETTINGS_FILE, 'w') as f:
                json.dump(self.settings, f, indent=4)
        except Exception as e:
            print(f"Failed to save settings: {e}")

    def get(self, key):
        return self.settings.get(key)

    def set(self, key, value):
        if key in self.settings:
            self.settings[key] = value
            self.save()

# Global accessor
settings = SettingsManager()
