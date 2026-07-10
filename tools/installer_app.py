import os
import sys
import shutil
import threading
import subprocess
import customtkinter as ctk
from pathlib import Path

class InstallerApp(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("Velocity Download Manager - Setup")
        self.geometry("500x350")
        self.resizable(False, False)
        ctk.set_appearance_mode("dark")
        ctk.set_default_color_theme("blue")
        
        self.install_dir = os.path.join(os.environ.get('LOCALAPPDATA', os.path.expanduser('~')), 'Programs', 'Velocity')
        
        # UI Elements
        self.lbl_title = ctk.CTkLabel(self, text="Velocity Setup", font=("Segoe UI", 28, "bold"))
        self.lbl_title.pack(pady=(30, 10))
        
        self.lbl_desc = ctk.CTkLabel(self, text="This will install Velocity Download Manager on your computer.", font=("Segoe UI", 14))
        self.lbl_desc.pack(pady=(0, 20))
        
        path_frame = ctk.CTkFrame(self, fg_color="transparent")
        path_frame.pack(fill="x", padx=40, pady=(0, 15))
        
        self.path_var = ctk.StringVar(value=self.install_dir)
        ctk.CTkLabel(path_frame, text="Install Location:", font=("Segoe UI", 12)).pack(anchor="w")
        
        entry_frame = ctk.CTkFrame(path_frame, fg_color="transparent")
        entry_frame.pack(fill="x")
        ctk.CTkEntry(entry_frame, textvariable=self.path_var).pack(side="left", fill="x", expand=True, padx=(0, 10))
        ctk.CTkButton(entry_frame, text="Browse", width=70, command=self._browse).pack(side="left")
        
        self.progress = ctk.CTkProgressBar(self, width=400)
        self.progress.set(0)
        
        self.lbl_status = ctk.CTkLabel(self, text="", font=("Segoe UI", 12))
        
        self.btn_install = ctk.CTkButton(self, text="Install", font=("Segoe UI", 16, "bold"), height=45, command=self.start_install)
        self.btn_install.pack(pady=10)

    def _browse(self):
        import tkinter.filedialog as fd
        path = fd.askdirectory(initialdir=self.path_var.get())
        if path:
            self.install_dir = os.path.join(path, "Velocity")
            self.path_var.set(self.install_dir)

    def start_install(self):
        self.btn_install.configure(state="disabled")
        self.progress.pack(pady=(0, 10))
        self.lbl_status.pack(pady=(0, 10))
        threading.Thread(target=self._install_process, daemon=True).start()
        
    def _install_process(self):
        try:
            self._update_status("Preparing installation...", 0.1)
            
            # 1. Find payload
            if getattr(sys, 'frozen', False):
                base_path = sys._MEIPASS
            else:
                base_path = os.path.dirname(os.path.abspath(__file__))
                
            payload_dir = os.path.join(base_path, 'Velocity_Payload')
            
            if not os.path.exists(payload_dir):
                self._update_status("Error: Payload not found!", 0)
                return
                
            self._update_status("Stopping running instances...", 0.2)
            subprocess.run(['taskkill', '/F', '/IM', 'Velocity.exe'], capture_output=True)
            
            # Use the selected install directory
            self.install_dir = self.path_var.get()
            
            self._update_status("Copying files...", 0.4)
            if os.path.exists(self.install_dir):
                try:
                    shutil.rmtree(self.install_dir)
                except:
                    pass
            
            shutil.copytree(payload_dir, self.install_dir)
            self._update_status("Files copied.", 0.8)
            
            self._update_status("Creating Desktop Shortcut...", 0.9)
            exe_path = os.path.join(self.install_dir, 'Velocity.exe')
            shortcut_path = os.path.join(os.path.expanduser('~'), 'Desktop', 'Velocity Download Manager.lnk')
            
            ps_cmd = f"$wshell = New-Object -ComObject WScript.Shell; $shortcut = $wshell.CreateShortcut('{shortcut_path}'); $shortcut.TargetPath = '{exe_path}'; $shortcut.WorkingDirectory = '{self.install_dir}'; $shortcut.IconLocation = '{exe_path}'; $shortcut.Save()"
            subprocess.run(["powershell", "-NoProfile", "-Command", ps_cmd], capture_output=True)
            
            self._update_status("Installation Complete!", 1.0)
            
            self.after(0, self._show_finish)
            
        except Exception as e:
            self._update_status(f"Error: {str(e)}", 0)
            
    def _update_status(self, text, val):
        self.after(0, lambda: self.lbl_status.configure(text=text))
        self.after(0, lambda: self.progress.set(val))
        
    def _show_finish(self):
        self.btn_install.configure(text="Launch Velocity", state="normal", command=self.launch_app)
        
    def launch_app(self):
        exe_path = os.path.join(self.install_dir, 'Velocity.exe')
        subprocess.Popen([exe_path], cwd=self.install_dir)
        self.destroy()

if __name__ == "__main__":
    app = InstallerApp()
    app.mainloop()
