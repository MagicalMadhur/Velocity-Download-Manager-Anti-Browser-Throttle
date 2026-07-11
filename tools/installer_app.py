import os
import sys
import shutil
import threading
import subprocess
import ctypes
import argparse
import customtkinter as ctk
from pathlib import Path

def is_admin():
    try:
        return ctypes.windll.shell32.IsUserAnAdmin()
    except:
        return False

class InstallerApp(ctk.CTk):
    def __init__(self):
        super().__init__()
        
        parser = argparse.ArgumentParser()
        parser.add_argument('--auto-install', action='store_true')
        parser.add_argument('--path', type=str, default="")
        parser.add_argument('--all-users', action='store_true')
        self.args, _ = parser.parse_known_args()

        self.title("Velocity Download Manager - Setup")
        self.geometry("500x420")
        self.resizable(False, False)
        ctk.set_appearance_mode("dark")
        ctk.set_default_color_theme("blue")
        
        self.single_user_dir = os.path.join(os.environ.get('LOCALAPPDATA', os.path.expanduser('~')), 'Programs', 'Velocity')
        self.all_users_dir = os.path.join(os.environ.get('PROGRAMFILES', 'C:\\Program Files'), 'Velocity')
        
        self.install_dir = self.args.path if self.args.path else self.single_user_dir
        
        # UI Elements
        self.lbl_title = ctk.CTkLabel(self, text="Velocity Setup", font=("Segoe UI", 28, "bold"))
        self.lbl_title.pack(pady=(20, 10))
        
        self.lbl_desc = ctk.CTkLabel(self, text="This will install Velocity Download Manager on your computer.", font=("Segoe UI", 14))
        self.lbl_desc.pack(pady=(0, 20))
        
        # User Type Frame
        self.user_type_var = ctk.StringVar(value="single")
        if self.args.all_users:
             self.user_type_var.set("all")
        
        user_frame = ctk.CTkFrame(self, fg_color="transparent")
        user_frame.pack(fill="x", padx=40, pady=(0, 15))
        
        ctk.CTkRadioButton(user_frame, text="Install for me only", variable=self.user_type_var, value="single", command=self._on_user_type_change).pack(anchor="w", pady=5)
        
        all_text = "Install for all users (Requires Admin)" if not is_admin() else "Install for all users"
        ctk.CTkRadioButton(user_frame, text=all_text, variable=self.user_type_var, value="all", command=self._on_user_type_change).pack(anchor="w", pady=5)

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
        
        if self.args.auto_install:
            # Disable UI elements if auto installing
            self.btn_install.configure(state="disabled")
            for child in user_frame.winfo_children():
                child.configure(state="disabled")
            for child in entry_frame.winfo_children():
                child.configure(state="disabled")
            self.after(500, self.start_install)

    def _on_user_type_change(self):
        if self.user_type_var.get() == "single":
            self.path_var.set(self.single_user_dir)
        else:
            self.path_var.set(self.all_users_dir)

    def _browse(self):
        import tkinter.filedialog as fd
        path = fd.askdirectory(initialdir=self.path_var.get())
        if path:
            self.install_dir = os.path.join(path, "Velocity")
            self.path_var.set(self.install_dir)

    def start_install(self):
        self.install_dir = self.path_var.get()
        if self.user_type_var.get() == "all" and not is_admin():
            # Relaunch as admin
            try:
                exe_path = sys.executable
                params = f'--auto-install --all-users --path "{self.install_dir}"'
                
                res = ctypes.windll.shell32.ShellExecuteW(None, "runas", exe_path, params, None, 1)
                
                if res <= 32:
                    raise Exception(f"Elevation failed with code {res}")
                    
                self.destroy()
                return
            except Exception as e:
                self.lbl_status.configure(text="Error: Administrator privileges required.")
                self.lbl_status.pack(pady=(0, 10))
                self.btn_install.configure(state="normal")
                return

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
            
            self._update_status("Copying files...", 0.4)
            if os.path.exists(self.install_dir):
                try:
                    shutil.rmtree(self.install_dir)
                except Exception as e:
                    self._update_status(f"Error removing old files: {str(e)}", 0)
                    return
            
            try:
                shutil.copytree(payload_dir, self.install_dir)
            except PermissionError:
                self._update_status("Error: Administrator privileges required. Please select 'Install for all users'.", 0)
                self.btn_install.configure(state="normal")
                return
            except Exception as e:
                self._update_status(f"Error copying files: {str(e)}", 0)
                self.btn_install.configure(state="normal")
                return
                
            self._update_status("Files copied.", 0.8)
            
            self._update_status("Creating Desktop Shortcut...", 0.9)
            exe_path = os.path.join(self.install_dir, 'Velocity.exe')
            
            if self.user_type_var.get() == "all":
                desktop_dir = os.environ.get('PUBLIC', 'C:\\Users\\Public') + '\\Desktop'
            else:
                desktop_dir = os.path.join(os.path.expanduser('~'), 'Desktop')
                
            shortcut_path = os.path.join(desktop_dir, 'Velocity Download Manager.lnk')
            
            ps_cmd = f"$wshell = New-Object -ComObject WScript.Shell; $shortcut = $wshell.CreateShortcut('{shortcut_path}'); $shortcut.TargetPath = '{exe_path}'; $shortcut.WorkingDirectory = '{self.install_dir}'; $shortcut.IconLocation = '{exe_path}'; $shortcut.Save()"
            subprocess.run(["powershell", "-NoProfile", "-Command", ps_cmd], capture_output=True)
            
            self._update_status("Installation Complete!", 1.0)
            
            self.after(0, self._show_finish)
            
        except Exception as e:
            self._update_status(f"Error: {str(e)}", 0)
            self.btn_install.configure(state="normal")
            
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
