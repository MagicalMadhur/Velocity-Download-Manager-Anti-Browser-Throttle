import customtkinter as ctk
import os
from typing import Callable, List
from download_manager.models.download_item import DownloadItem
from download_manager.utils.formatter import format_size, format_speed
from download_manager.gui.dialogs import RecoverURLDialog

class DownloadCard(ctk.CTkFrame):
    def __init__(self, master, item: DownloadItem, callbacks):
        super().__init__(master, corner_radius=12, fg_color=("gray85", "gray17"))
        self.item = item
        self.callbacks = callbacks
        
        self.grid_columnconfigure(1, weight=1)
        
        # Icon / Status indicator
        self.status_indicator = ctk.CTkLabel(self, text="📥", font=("Segoe UI", 28))
        self.status_indicator.grid(row=0, column=0, rowspan=3, padx=(20, 15), pady=20)
        
        # File Name
        self.name_label = ctk.CTkLabel(self, text=item.filename or "Unknown File", font=("Segoe UI", 16, "bold"), anchor="w")
        self.name_label.grid(row=0, column=1, sticky="ew", padx=10, pady=(20, 0))
        
        # Progress Bar
        self.progress_bar = ctk.CTkProgressBar(self, height=8, corner_radius=4)
        self.progress_bar.grid(row=1, column=1, sticky="ew", padx=10, pady=(8, 8))
        self.progress_bar.set(0)
        
        # Metrics Label
        self.metrics_label = ctk.CTkLabel(self, text="0 MB / 0 MB • 0 B/s • Pending", font=("Segoe UI", 12), text_color="gray")
        self.metrics_label.grid(row=2, column=1, sticky="w", padx=10, pady=(0, 20))
        
        # Buttons Frame
        self.btn_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.btn_frame.grid(row=0, column=2, rowspan=3, padx=20, pady=20, sticky="e")
        
        self.btn_pause = ctk.CTkButton(self.btn_frame, text="⏸", width=45, height=45, corner_radius=22, 
                                       command=lambda: self.callbacks['on_pause'](self.item.id))
        self.btn_pause.pack(side="left", padx=5)
        
        self.btn_resume = ctk.CTkButton(self.btn_frame, text="▶", width=45, height=45, corner_radius=22,
                                        command=lambda: self.callbacks['on_resume'](self.item.id))
        self.btn_resume.pack(side="left", padx=5)
        
        self.btn_cancel = ctk.CTkButton(self.btn_frame, text="⏹", width=45, height=45, corner_radius=22, fg_color="#C21807", hover_color="#910F03",
                                        command=lambda: self.callbacks['on_cancel'](self.item.id))
        self.btn_cancel.pack(side="left", padx=5)
        
        self.btn_delete = ctk.CTkButton(self.btn_frame, text="🗑", width=45, height=45, corner_radius=22, fg_color="gray", hover_color="#555",
                                        command=lambda: self.callbacks['on_delete'](self.item.id))
        self.btn_delete.pack(side="left", padx=5)
        
        self.update_ui()
        
    def update_ui(self):
        pct = 0.0
        if self.item.filesize > 0:
            pct = self.item.downloaded_size / self.item.filesize
            
        self.progress_bar.set(pct)
        
        size_str = format_size(self.item.filesize) if self.item.filesize else "Unknown"
        dl_str = format_size(self.item.downloaded_size)
        speed_str = format_speed(self.item.speed)
        pct_str = f"{pct*100:.1f}%"
        
        self.metrics_label.configure(text=f"{dl_str} / {size_str} ({pct_str}) • {speed_str} • {self.item.status}")
        
        if self.item.status == "Completed":
            self.status_indicator.configure(text="✅", text_color="#28a745")
        elif self.item.status == "Error":
            self.status_indicator.configure(text="❌", text_color="#dc3545")
        elif self.item.status in ["Paused", "Cancelled"]:
            self.status_indicator.configure(text="⏸", text_color="gray")
        else:
            self.status_indicator.configure(text="📥", text_color="#007bff")

class MainWindow(ctk.CTkFrame):
    def __init__(self, master, callbacks: dict):
        super().__init__(master, fg_color="transparent")
        self.master = master
        self.pack(fill=ctk.BOTH, expand=True, padx=20, pady=20)
        
        self.callbacks = callbacks
        self.items = {}
        self.cards = {}
        self.current_category = "All Downloads"
        
        from download_manager.services.settings import settings
        self.settings = settings
        
        # Intercept delete to also destroy UI
        self.original_delete = self.callbacks['on_delete']
        self.callbacks['on_delete'] = self._custom_delete
        
        self._build_sidebar()
        
        self.main_area = ctk.CTkFrame(self, fg_color="transparent")
        self.main_area.pack(side="right", fill="both", expand=True, padx=(20, 0))
        
        self._build_toolbar()
        self._build_add_frame()
        self._build_scrollable_list()
        
        self.master.after(500, self._update_ui_loop)
        
    def _custom_delete(self, item_id):
        self.original_delete(item_id)
        if item_id in self.items:
            del self.items[item_id]
        if item_id in self.cards:
            self.cards[item_id].destroy()
            del self.cards[item_id]
            
    def _build_sidebar(self):
        self.sidebar_frame = ctk.CTkFrame(self, width=200, corner_radius=15)
        self.sidebar_frame.pack(side="left", fill="y")
        self.sidebar_frame.pack_propagate(False)
        
        ctk.CTkLabel(self.sidebar_frame, text="Categories", font=("Segoe UI", 20, "bold")).pack(pady=(20, 20), padx=20, anchor="w")
        
        categories = ["All Downloads", "Videos", "Music", "Documents", "Archives", "Software", "Images", "Uncategorized"]
        self.cat_buttons = {}
        
        for cat in categories:
            btn = ctk.CTkButton(self.sidebar_frame, text=cat, fg_color="transparent", 
                                text_color=("gray10", "gray90"), hover_color=("gray70", "gray30"),
                                anchor="w", font=("Segoe UI", 14),
                                command=lambda c=cat: self._set_category(c))
            btn.pack(fill="x", padx=10, pady=5)
            self.cat_buttons[cat] = btn
            
        # Add spacer and Settings button
        ctk.CTkFrame(self.sidebar_frame, height=2, fg_color=("gray70", "gray30")).pack(fill="x", padx=20, pady=20)
        
        self.btn_settings = ctk.CTkButton(self.sidebar_frame, text="⚙ Settings", fg_color="transparent", 
                            text_color=("gray10", "gray90"), hover_color=("gray70", "gray30"),
                            anchor="w", font=("Segoe UI", 14, "bold"), command=self._open_settings)
        self.btn_settings.pack(fill="x", padx=10, pady=5)
            
        self._set_category("All Downloads")
        
    def _open_settings(self):
        from download_manager.gui.dialogs import SettingsDialog
        SettingsDialog(self.master)

    def _set_category(self, category_name):
        self.current_category = category_name
        
        # Highlight active button
        for cat, btn in self.cat_buttons.items():
            if cat == category_name:
                btn.configure(fg_color=("gray75", "gray25"))
            else:
                btn.configure(fg_color="transparent")
                
        # Filter cards
        self._refresh_card_visibility()

    def _refresh_card_visibility(self):
        for item_id, card in self.cards.items():
            card.pack_forget()
            
        # Repack in order
        for item_id, card in self.cards.items():
            if self.current_category == "All Downloads" or card.item.category == self.current_category:
                card.pack(fill=ctk.X, pady=(0, 15))

    def _build_toolbar(self):
        toolbar = ctk.CTkFrame(self.main_area, fg_color="transparent")
        toolbar.pack(fill=ctk.X, pady=(0, 20))
        
        title = ctk.CTkLabel(toolbar, text="Downloads", font=("Segoe UI", 32, "bold"))
        title.pack(side=ctk.LEFT)
        
        ctk.CTkButton(toolbar, text="➕ New Download", font=("Segoe UI", 15, "bold"), 
                      height=45, corner_radius=10, command=self._toggle_add_frame).pack(side=ctk.RIGHT)
                      
    def _build_add_frame(self):
        self.add_frame = ctk.CTkFrame(self.main_area, corner_radius=12)
        
        self.url_var = ctk.StringVar()
        self.path_var = ctk.StringVar(value=self.settings.get("default_download_path"))
        self.name_var = ctk.StringVar()
        
        self.add_frame.grid_columnconfigure(1, weight=1)
        
        ctk.CTkLabel(self.add_frame, text="URL:").grid(row=0, column=0, sticky="w", pady=15, padx=20)
        ctk.CTkEntry(self.add_frame, textvariable=self.url_var, height=35).grid(row=0, column=1, columnspan=2, sticky="ew", pady=15, padx=(0, 20))
        
        ctk.CTkLabel(self.add_frame, text="Save To:").grid(row=1, column=0, sticky="w", pady=10, padx=20)
        ctk.CTkEntry(self.add_frame, textvariable=self.path_var, height=35).grid(row=1, column=1, sticky="ew", pady=10, padx=(0, 10))
        ctk.CTkButton(self.add_frame, text="Browse", width=100, height=35, command=self._browse_path).grid(row=1, column=2, padx=(0, 20), pady=10)
        
        btn_frame = ctk.CTkFrame(self.add_frame, fg_color="transparent")
        btn_frame.grid(row=2, column=1, columnspan=2, sticky="e", pady=20, padx=20)
        ctk.CTkButton(btn_frame, text="Download Now", command=self._submit_new_download, width=150, height=40, font=("", 14, "bold")).pack(side=ctk.RIGHT, padx=5)
        ctk.CTkButton(btn_frame, text="Cancel", command=self._hide_add_frame, fg_color="gray", hover_color="#555", width=100, height=40).pack(side=ctk.RIGHT, padx=5)

    def _build_scrollable_list(self):
        self.scroll_frame = ctk.CTkScrollableFrame(self.main_area, fg_color="transparent")
        self.scroll_frame.pack(fill=ctk.BOTH, expand=True)

    def load_items(self, items: List[DownloadItem]):
        for item in items:
            self.items[item.id] = item
            self._insert_item(item)
            
    def _insert_item(self, item: DownloadItem):
        card = DownloadCard(self.scroll_frame, item, self.callbacks)
        self.cards[item.id] = card
        if self.current_category == "All Downloads" or item.category == self.current_category:
            card.pack(fill=ctk.X, pady=(0, 15))

    def _update_ui_loop(self):
        for item_id, item in self.items.items():
            if item.status in ["Downloading", "Starting", "Pending", "Completed", "Paused", "Cancelled", "Error"]:
                if item_id in self.cards:
                    self.cards[item_id].update_ui()
        self.master.after(500, self._update_ui_loop)

    def _toggle_add_frame(self):
        if self.add_frame.winfo_ismapped():
            self._hide_add_frame()
        else:
            self._show_add_frame()
            
    def _show_add_frame(self, url=None, filename=None, is_ydl=False, ydl_format_id=None):
        if url:
            self.url_var.set(url)
        if filename:
            self.name_var.set(filename)
            
        self._pending_is_ydl = is_ydl
        self._pending_ydl_format_id = ydl_format_id
        
        # Refresh default path in case settings changed
        if not self.path_var.get() or self.path_var.get() == os.path.expanduser("~/Downloads"):
            self.path_var.set(self.settings.get("default_download_path"))
            
        self.scroll_frame.pack_forget()
        self.add_frame.pack(fill=ctk.X, pady=(0, 20))
        self.scroll_frame.pack(fill=ctk.BOTH, expand=True)
        
    def _hide_add_frame(self):
        self.add_frame.pack_forget()
        self.url_var.set("")
        self.name_var.set("")
        
    def _browse_path(self):
        import tkinter.filedialog as fd
        path = fd.askdirectory(initialdir=self.path_var.get())
        if path:
            self.path_var.set(path)
            
    def _submit_new_download(self):
        url = self.url_var.get().strip()
        path = self.path_var.get().strip()
        name = self.name_var.get().strip()
        
        is_ydl = getattr(self, '_pending_is_ydl', False)
        ydl_format_id = getattr(self, '_pending_ydl_format_id', None)
        
        if url and path:
            self.callbacks['on_add'](url, path, name if name else None, is_ydl, ydl_format_id)
            self._hide_add_frame()
