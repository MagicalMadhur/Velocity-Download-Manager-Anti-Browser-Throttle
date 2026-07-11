import customtkinter as ctk
import tkinter.filedialog as fd
import os

class AddDownloadDialog(ctk.CTkToplevel):
    def __init__(self, parent, callback):
        super().__init__(parent)
        self.title("Add New Download")
        self.geometry("550x250")
        self.callback = callback
        
        self.url_var = ctk.StringVar()
        self.path_var = ctk.StringVar(value=os.path.expanduser("~/Downloads"))
        self.name_var = ctk.StringVar()
        
        self._build_ui()
        
    def _build_ui(self):
        frame = ctk.CTkFrame(self)
        frame.pack(fill=ctk.BOTH, expand=True, padx=20, pady=20)
        
        # URL
        ctk.CTkLabel(frame, text="URL:").grid(row=0, column=0, sticky="w", pady=5, padx=5)
        url_entry = ctk.CTkEntry(frame, textvariable=self.url_var, width=350)
        url_entry.grid(row=0, column=1, columnspan=2, sticky="ew", pady=5, padx=5)
        
        # Save Path
        ctk.CTkLabel(frame, text="Save To:").grid(row=1, column=0, sticky="w", pady=5, padx=5)
        ctk.CTkEntry(frame, textvariable=self.path_var, width=280).grid(row=1, column=1, sticky="ew", pady=5, padx=5)
        ctk.CTkButton(frame, text="Browse", width=60, command=self._browse).grid(row=1, column=2, padx=5, pady=5)
        
        # File Name (Optional)
        ctk.CTkLabel(frame, text="File Name:").grid(row=2, column=0, sticky="w", pady=5, padx=5)
        ctk.CTkEntry(frame, textvariable=self.name_var, width=350).grid(row=2, column=1, columnspan=2, sticky="ew", pady=5, padx=5)
        ctk.CTkLabel(frame, text="(Leave blank to auto-detect)", text_color="gray").grid(row=3, column=1, sticky="w", padx=5)
        
        # Buttons
        btn_frame = ctk.CTkFrame(frame, fg_color="transparent")
        btn_frame.grid(row=4, column=1, columnspan=2, sticky="e", pady=15)
        
        ctk.CTkButton(btn_frame, text="Download Now", command=self._submit, width=120).pack(side=ctk.RIGHT, padx=5)
        ctk.CTkButton(btn_frame, text="Cancel", command=self.destroy, fg_color="gray", hover_color="#555", width=80).pack(side=ctk.RIGHT, padx=5)
        
    def _browse(self):
        path = fd.askdirectory(initialdir=self.path_var.get())
        if path:
            self.path_var.set(path)
            
    def _submit(self):
        url = self.url_var.get().strip()
        path = self.path_var.get().strip()
        name = self.name_var.get().strip()
        
        if url and path:
            self.callback(url, path, name if name else None)
            self.destroy()

class RecoverURLDialog(ctk.CTkToplevel):
    def __init__(self, parent, callback):
        super().__init__(parent)
        self.title("Refresh Expired URL")
        self.geometry("500x150")
        self.callback = callback
        self.url_var = ctk.StringVar()
        
        self._build_ui()
        
    def _build_ui(self):
        frame = ctk.CTkFrame(self)
        frame.pack(fill=ctk.BOTH, expand=True, padx=20, pady=20)
        
        ctk.CTkLabel(frame, text="The download URL expired. Please provide a new URL:").pack(anchor="w", pady=5)
        ctk.CTkEntry(frame, textvariable=self.url_var, width=450).pack(fill="x", pady=5)
        
        btn_frame = ctk.CTkFrame(frame, fg_color="transparent")
        btn_frame.pack(fill="x", pady=10)
        ctk.CTkButton(btn_frame, text="Resume", command=self._submit, width=100).pack(side="right", padx=5)
        ctk.CTkButton(btn_frame, text="Cancel", command=self.destroy, fg_color="gray", hover_color="#555", width=80).pack(side="right", padx=5)
        
    def _submit(self):
        url = self.url_var.get().strip()
        if url:
            self.callback(url)
            self.destroy()

class VideoFormatDialog(ctk.CTkToplevel):
    def __init__(self, parent, info, callback):
        super().__init__(parent)
        self.title("Download Video")
        self.geometry("500x350")
        self.callback = callback
        self.info = info
        
        # Make the dialog modal
        self.transient(parent)
        self.grab_set()
        
        self._build_ui()
        
    def _build_ui(self):
        frame = ctk.CTkFrame(self)
        frame.pack(fill=ctk.BOTH, expand=True, padx=20, pady=20)
        
        ctk.CTkLabel(frame, text="Found Video!", font=("Segoe UI", 20, "bold")).pack(anchor="w", pady=(0, 10))
        
        title_label = ctk.CTkLabel(frame, text=self.info.get('title', ''), wraplength=450, justify="left")
        title_label.pack(anchor="w", pady=5)
        
        ctk.CTkLabel(frame, text="Select Quality:", font=("Segoe UI", 14, "bold")).pack(anchor="w", pady=(20, 5))
        
        formats = self.info.get('formats', [])
        
        if not formats:
            ctk.CTkLabel(frame, text="No direct media formats found for this video.", text_color="red").pack(anchor="w")
            btn_frame = ctk.CTkFrame(frame, fg_color="transparent")
            btn_frame.pack(fill="x", pady=20)
            ctk.CTkButton(btn_frame, text="Close", command=self.destroy, fg_color="gray", width=100).pack(side="right")
            return
            
        options = [f['label'] for f in formats]
        self.format_map = {f['label']: f for f in formats}
        
        self.combo = ctk.CTkOptionMenu(frame, values=options, width=450)
        self.combo.pack(anchor="w", pady=5)
        self.combo.set(options[0])
        
        btn_frame = ctk.CTkFrame(frame, fg_color="transparent")
        btn_frame.pack(fill="x", pady=30)
        
        ctk.CTkButton(btn_frame, text="Download Now", command=self._submit, width=150, height=40, font=("", 14, "bold")).pack(side="right", padx=5)
        ctk.CTkButton(btn_frame, text="Cancel", command=self.destroy, fg_color="gray", hover_color="#555", width=100, height=40).pack(side="right", padx=5)
        
    def _submit(self):
        selected_label = self.combo.get()
        f = self.format_map.get(selected_label)
        if f:
            filename = f"{self.info.get('title')}.{f['ext']}"
            
            if 'format_id' in f:
                # Use Yt-dlp Engine
                self.callback(self.info['original_url'], filename, is_ydl=True, ydl_format_id=f['format_id'])
            else:
                # Use standard Request Engine
                self.callback(f['url'], filename, is_ydl=False, ydl_format_id=None)
                
            self.destroy()

class SettingsDialog(ctk.CTkToplevel):
    def __init__(self, parent):
        super().__init__(parent)
        self.title("Settings")
        self.geometry("600x500")
        
        # Make the dialog modal
        self.transient(parent)
        self.grab_set()
        
        from download_manager.services.settings import settings
        self.settings = settings
        
        # Variables
        self.path_var = ctk.StringVar(value=self.settings.get("default_download_path"))
        self.startup_var = ctk.BooleanVar(value=self.settings.get("launch_on_startup"))
        self.max_downloads_var = ctk.IntVar(value=self.settings.get("max_concurrent_downloads"))
        
        self.speed_limit_var = ctk.IntVar(value=self.settings.get("speed_limit_kbps"))
        self.threads_var = ctk.IntVar(value=self.settings.get("max_threads_per_download"))
        
        self.shutdown_var = ctk.BooleanVar(value=self.settings.get("shutdown_after_download"))
        self.sound_var = ctk.BooleanVar(value=self.settings.get("play_sound_on_complete"))
        self.normalize_var = ctk.BooleanVar(value=self.settings.get("normalize_audio"))
        
        self._build_ui()
        
    def _build_ui(self):
        tabview = ctk.CTkTabview(self)
        tabview.pack(fill=ctk.BOTH, expand=True, padx=20, pady=(20, 10))
        
        tab_general = tabview.add("General")
        tab_network = tabview.add("Network")
        tab_auto = tabview.add("Automation")
        
        # --- General Tab ---
        ctk.CTkLabel(tab_general, text="Default Download Path:", font=("", 14, "bold")).pack(anchor="w", pady=(10, 5), padx=10)
        path_frame = ctk.CTkFrame(tab_general, fg_color="transparent")
        path_frame.pack(fill="x", padx=10, pady=5)
        ctk.CTkEntry(path_frame, textvariable=self.path_var).pack(side="left", fill="x", expand=True, padx=(0, 10))
        ctk.CTkButton(path_frame, text="Browse", width=80, command=self._browse_path).pack(side="right")
        
        ctk.CTkSwitch(tab_general, text="Launch Velocity on Windows Startup", variable=self.startup_var).pack(anchor="w", padx=10, pady=20)
        
        ctk.CTkLabel(tab_general, text="Max Concurrent Downloads (1-10):", font=("", 14, "bold")).pack(anchor="w", padx=10, pady=(10, 5))
        slider_frame = ctk.CTkFrame(tab_general, fg_color="transparent")
        slider_frame.pack(fill="x", padx=10, pady=5)
        self.lbl_downloads = ctk.CTkLabel(slider_frame, text=str(self.max_downloads_var.get()), width=30)
        self.lbl_downloads.pack(side="left")
        slider = ctk.CTkSlider(slider_frame, from_=1, to=10, number_of_steps=9, variable=self.max_downloads_var, command=lambda v: self.lbl_downloads.configure(text=str(int(v))))
        slider.pack(side="left", fill="x", expand=True, padx=10)
        
        # --- Network Tab ---
        ctk.CTkLabel(tab_network, text="Speed Limiter", font=("", 14, "bold")).pack(anchor="w", padx=10, pady=(10, 5))
        speed_frame = ctk.CTkFrame(tab_network, fg_color="transparent")
        speed_frame.pack(fill="x", padx=10, pady=5)
        ctk.CTkLabel(speed_frame, text="Maximum Speed (KB/s):").pack(side="left")
        ctk.CTkEntry(speed_frame, textvariable=self.speed_limit_var, width=100).pack(side="left", padx=10)
        ctk.CTkLabel(speed_frame, text="(0 = Unlimited)", text_color="gray").pack(side="left")
        
        ctk.CTkLabel(tab_network, text="Max Threads per Download:", font=("", 14, "bold")).pack(anchor="w", padx=10, pady=(20, 5))
        threads_combo = ctk.CTkOptionMenu(tab_network, values=["8", "16", "32"], 
            command=lambda v: self.threads_var.set(int(v)))
        threads_combo.pack(anchor="w", padx=10, pady=5)
        threads_combo.set(str(self.threads_var.get()))
        
        # --- Automation Tab ---
        ctk.CTkSwitch(tab_auto, text="Play sound when download completes", variable=self.sound_var).pack(anchor="w", padx=10, pady=20)
        ctk.CTkSwitch(tab_auto, text="Turn off PC when download queue is empty", variable=self.shutdown_var).pack(anchor="w", padx=10, pady=20)
        ctk.CTkSwitch(tab_auto, text="Normalize Audio Volume (Matches YouTube playback)", variable=self.normalize_var).pack(anchor="w", padx=10, pady=20)
        
        # Buttons
        btn_frame = ctk.CTkFrame(self, fg_color="transparent")
        btn_frame.pack(fill="x", padx=20, pady=(0, 20))
        ctk.CTkButton(btn_frame, text="Save Settings", command=self._save, width=150, height=40, font=("", 14, "bold")).pack(side="right", padx=5)
        ctk.CTkButton(btn_frame, text="Cancel", command=self.destroy, fg_color="gray", hover_color="#555", width=100, height=40).pack(side="right", padx=5)
        
    def _browse_path(self):
        import tkinter.filedialog as fd
        path = fd.askdirectory(initialdir=self.path_var.get())
        if path:
            self.path_var.set(path)
            
    def _save(self):
        try:
            # Parse inputs
            speed = int(self.speed_limit_var.get())
            if speed < 0:
                speed = 0
            self.settings.set("speed_limit_kbps", speed)
            self.settings.set("default_download_path", self.path_var.get())
            # Handle Windows Startup
            import sys
            import winreg
            
            key_path = r"Software\Microsoft\Windows\CurrentVersion\Run"
            try:
                key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, key_path, 0, winreg.KEY_ALL_ACCESS)
                if self.startup_var.get():
                    if getattr(sys, 'frozen', False):
                        exe_path = sys.executable
                    else:
                        exe_path = os.path.abspath(sys.argv[0])
                    winreg.SetValueEx(key, "VelocityDownloadManager", 0, winreg.REG_SZ, f'"{exe_path}"')
                else:
                    try:
                        winreg.DeleteValue(key, "VelocityDownloadManager")
                    except FileNotFoundError:
                        pass
                winreg.CloseKey(key)
            except Exception as e:
                print(f"Failed to set startup registry key: {e}")
                
            self.settings.set("launch_on_startup", self.startup_var.get())
            self.settings.set("max_concurrent_downloads", int(self.max_downloads_var.get()))
            self.settings.set("max_threads_per_download", self.threads_var.get())
            self.settings.set("shutdown_after_download", self.shutdown_var.get())
            self.settings.set("play_sound_on_complete", self.sound_var.get())
            self.settings.set("normalize_audio", self.normalize_var.get())
            self.destroy()
        except ValueError:
            import tkinter.messagebox
            tkinter.messagebox.showerror("Invalid Input", "Please enter valid numbers for settings.")

class AboutDialog(ctk.CTkToplevel):
    def __init__(self, parent):
        super().__init__(parent)
        self.title("About Velocity")
        self.geometry("400x250")
        
        self.transient(parent)
        self.grab_set()
        
        frame = ctk.CTkFrame(self)
        frame.pack(fill=ctk.BOTH, expand=True, padx=20, pady=20)
        
        ctk.CTkLabel(frame, text="Velocity Download Manager", font=("Segoe UI", 20, "bold")).pack(pady=(10, 5))
        ctk.CTkLabel(frame, text="Version 1.0.2", font=("Segoe UI", 12)).pack(pady=(0, 10))
        
        ctk.CTkLabel(frame, text="Author: Madhur Chavan\nAll rights reserved.", font=("Segoe UI", 14)).pack(pady=5)
        
        ctk.CTkLabel(frame, text='"With love, to destroy IDM."', font=("Segoe UI", 14, "italic"), text_color="#007bff").pack(pady=15)
        
        ctk.CTkButton(frame, text="Close", command=self.destroy, width=100).pack(pady=10)
