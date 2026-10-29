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
    def __init__(self, parent, info, callback, default_path=None):
        super().__init__(parent)
        self.title("Download Video - Velocity")
        self.geometry("560x420")
        self.callback = callback
        self.info = info
        
        if default_path:
            self.default_path = default_path
        else:
            try:
                from download_manager.services.settings import settings
                self.default_path = settings.get("default_download_path")
            except Exception:
                self.default_path = os.path.expanduser("~/Downloads")
                
        self.path_var = ctk.StringVar(value=self.default_path)
        self.name_var = ctk.StringVar()
        
        # Make the dialog modal
        self.transient(parent)
        try:
            self.grab_set()
        except Exception:
            pass
        
        self._build_ui()
        
    def _build_ui(self):
        frame = ctk.CTkFrame(self)
        frame.pack(fill=ctk.BOTH, expand=True, padx=20, pady=20)
        
        ctk.CTkLabel(frame, text="Found Video Stream!", font=("Segoe UI", 18, "bold")).pack(anchor="w", pady=(0, 5))
        
        title_text = self.info.get('title', 'Video')
        title_label = ctk.CTkLabel(frame, text=title_text, wraplength=500, justify="left", font=("Segoe UI", 12))
        title_label.pack(anchor="w", pady=(0, 15))
        
        ctk.CTkLabel(frame, text="Select Quality:", font=("Segoe UI", 13, "bold")).pack(anchor="w", pady=(5, 3))
        
        formats = self.info.get('formats', [])
        if not formats:
            ctk.CTkLabel(frame, text="No media formats found for this video.", text_color="red").pack(anchor="w")
            btn_frame = ctk.CTkFrame(frame, fg_color="transparent")
            btn_frame.pack(fill="x", pady=20)
            ctk.CTkButton(btn_frame, text="Close", command=self.destroy, fg_color="gray", width=100).pack(side="right")
            return
            
        options = [f['label'] for f in formats]
        self.format_map = {f['label']: f for f in formats}
        
        self.combo = ctk.CTkOptionMenu(frame, values=options, width=500, command=self._on_format_changed)
        self.combo.pack(anchor="w", pady=(0, 15))
        self.combo.set(options[0])
        
        # Save To path
        ctk.CTkLabel(frame, text="Save To:", font=("Segoe UI", 13, "bold")).pack(anchor="w", pady=(5, 3))
        path_box = ctk.CTkFrame(frame, fg_color="transparent")
        path_box.pack(fill="x", pady=(0, 15))
        ctk.CTkEntry(path_box, textvariable=self.path_var, width=410).pack(side=ctk.LEFT, padx=(0, 10))
        ctk.CTkButton(path_box, text="Browse", width=80, command=self._browse).pack(side=ctk.LEFT)
        
        # Initial file name
        first_fmt = self.format_map.get(options[0])
        ext = first_fmt.get('ext', 'mp4') if first_fmt else 'mp4'
        self.name_var.set(f"{title_text}.{ext}")
        
        # Buttons
        btn_frame = ctk.CTkFrame(frame, fg_color="transparent")
        btn_frame.pack(fill="x", pady=(15, 0))
        
        ctk.CTkButton(btn_frame, text="Download Now", command=self._submit, width=150, height=38, 
                       font=("Segoe UI", 14, "bold"), fg_color="#28a745", hover_color="#218838").pack(side=ctk.RIGHT, padx=5)
        ctk.CTkButton(btn_frame, text="Cancel", command=self.destroy, fg_color="gray", hover_color="#555", width=90, height=38).pack(side=ctk.RIGHT, padx=5)
        
    def _browse(self):
        path = fd.askdirectory(initialdir=self.path_var.get())
        if path:
            self.path_var.set(path)
            
    def _on_format_changed(self, choice):
        f = self.format_map.get(choice)
        if f:
            ext = f.get('ext', 'mp4')
            title_text = self.info.get('title', 'Video')
            self.name_var.set(f"{title_text}.{ext}")
        
    def _submit(self):
        selected_label = self.combo.get()
        f = self.format_map.get(selected_label)
        if f:
            ext = f.get('ext', 'mp4')
            filename = self.name_var.get().strip() or f"{self.info.get('title')}.{ext}"
            save_path = self.path_var.get().strip() or self.default_path
            format_id = f.get('format_id', 'bestvideo+bestaudio/best')
            
            try:
                self.callback(self.info['original_url'], save_path, filename, is_ydl=True, ydl_format_id=format_id)
            except TypeError:
                self.callback(self.info['original_url'], filename, is_ydl=True, ydl_format_id=format_id)
                
            self.destroy()

class SniffingDialog(ctk.CTkToplevel):
    def __init__(self, parent, url: str, callback, default_path=None):
        super().__init__(parent)
        self.title("Sniffing Video - Velocity")
        self.geometry("460x200")
        self.resizable(False, False)
        
        self.parent = parent
        self.url = url
        self.callback = callback
        self.is_closed = False
        
        if default_path:
            self.default_path = default_path
        else:
            try:
                from download_manager.services.settings import settings
                self.default_path = settings.get("default_download_path")
            except Exception:
                self.default_path = os.path.expanduser("~/Downloads")
                
        self.transient(parent)
        self.attributes('-topmost', True)
        try:
            self.grab_set()
        except Exception:
            pass
        
        try:
            self.update_idletasks()
            pw = parent.winfo_width()
            ph = parent.winfo_height()
            px = parent.winfo_rootx()
            py = parent.winfo_rooty()
            w, h = 460, 200
            x = px + max(0, (pw - w) // 2)
            y = py + max(0, (ph - h) // 2)
            self.geometry(f"{w}x{h}+{x}+{y}")
        except Exception:
            pass

        self._build_ui()
        self._start_sniffing()

    def _build_ui(self):
        frame = ctk.CTkFrame(self)
        frame.pack(fill=ctk.BOTH, expand=True, padx=20, pady=20)
        
        ctk.CTkLabel(frame, text="🔍 Extracting video stream info...", font=("Segoe UI", 15, "bold")).pack(anchor="w", pady=(2, 2))
        ctk.CTkLabel(frame, text="Checking available qualities up to 4K...", font=("Segoe UI", 11), text_color="#aaaaaa").pack(anchor="w", pady=(0, 12))
        
        # Animated Progress Bar
        self.progress_bar = ctk.CTkProgressBar(frame, mode="indeterminate", height=10)
        self.progress_bar.pack(fill="x", pady=(0, 18))
        self.progress_bar.start()
        
        # Action Buttons frame
        btn_frame = ctk.CTkFrame(frame, fg_color="transparent")
        btn_frame.pack(fill="x")
        
        # Quick Download button - skips format inspection, downloads max quality immediately
        self.quick_btn = ctk.CTkButton(
            btn_frame,
            text="⚡ Quick Download (Max Quality)",
            command=self._quick_download,
            font=("Segoe UI", 12, "bold"),
            fg_color="#1f538d",
            hover_color="#14375e",
            height=36
        )
        self.quick_btn.pack(side="left")
        
        # Cancel button
        self.cancel_btn = ctk.CTkButton(
            btn_frame,
            text="Cancel",
            command=self._cancel,
            fg_color="gray",
            hover_color="#555",
            width=80,
            height=36
        )
        self.cancel_btn.pack(side="right")
        
        self.protocol("WM_DELETE_WINDOW", self._cancel)

    def _start_sniffing(self):
        from download_manager.services.video_extractor import extract_video_info
        extract_video_info(self.url, self._on_success, self._on_error)

    def _quick_download(self):
        if self.is_closed:
            return
        self.is_closed = True
        try:
            self.progress_bar.stop()
        except Exception:
            pass
        self.destroy()
        
        try:
            self.callback(self.url, self.default_path, filename=None, is_ydl=True, ydl_format_id='bestvideo+bestaudio/best')
        except TypeError:
            self.callback(self.url, None, is_ydl=True, ydl_format_id='bestvideo+bestaudio/best')

    def _cancel(self):
        if self.is_closed:
            return
        self.is_closed = True
        try:
            self.progress_bar.stop()
        except Exception:
            pass
        self.destroy()

    def _on_success(self, info):
        if self.is_closed:
            return
            
        def _open_format_dialog():
            if self.is_closed:
                return
            self.is_closed = True
            try:
                self.progress_bar.stop()
            except Exception:
                pass
            self.destroy()
            VideoFormatDialog(self.parent, info, self.callback, default_path=self.default_path)
            
        self.parent.after(0, _open_format_dialog)

    def _on_error(self, err):
        if self.is_closed:
            return
            
        def _show_error():
            if self.is_closed:
                return
            self.is_closed = True
            try:
                self.progress_bar.stop()
            except Exception:
                pass
            self.destroy()
            import tkinter.messagebox
            tkinter.messagebox.showerror("Video Extraction Error", f"Failed to extract video streams:\n\n{err}")
            
        self.parent.after(0, _show_error)

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
        self.start_minimized_var = ctk.BooleanVar(value=self.settings.get("start_minimized_to_tray", True))
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
        
        ctk.CTkSwitch(tab_general, text="Launch Velocity on Windows Startup", variable=self.startup_var).pack(anchor="w", padx=10, pady=(15, 5))
        ctk.CTkSwitch(tab_general, text="Start Minimized in System Tray on Startup", variable=self.start_minimized_var).pack(anchor="w", padx=30, pady=(0, 15))
        
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
                    cmd = f'"{exe_path}" --startup' if self.start_minimized_var.get() else f'"{exe_path}"'
                    winreg.SetValueEx(key, "VelocityDownloadManager", 0, winreg.REG_SZ, cmd)
                else:
                    try:
                        winreg.DeleteValue(key, "VelocityDownloadManager")
                    except FileNotFoundError:
                        pass
                winreg.CloseKey(key)
            except Exception as e:
                print(f"Failed to set startup registry key: {e}")
                
            self.settings.set("launch_on_startup", self.startup_var.get())
            self.settings.set("start_minimized_to_tray", self.start_minimized_var.get())
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
        ctk.CTkLabel(frame, text="Version 1.0.3", font=("Segoe UI", 12)).pack(pady=(0, 10))
        
        ctk.CTkLabel(frame, text="Author: Madhur Chavan\nAll rights reserved.", font=("Segoe UI", 14)).pack(pady=5)
        
        ctk.CTkLabel(frame, text='"With love, to destroy IDM."', font=("Segoe UI", 14, "italic"), text_color="#007bff").pack(pady=15)
        
        ctk.CTkButton(frame, text="Close", command=self.destroy, width=100).pack(pady=10)
