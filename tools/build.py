import PyInstaller.__main__
import customtkinter
import os
import sys
import yt_dlp

ctk_path = os.path.dirname(customtkinter.__file__)
yt_dlp_path = os.path.dirname(yt_dlp.__file__)

args = [
    'download_manager/app.py',
    '--name=Velocity',
    '--windowed',
    '--noconfirm',
    '--icon=download_manager/velocity.ico',
    f'--add-data={ctk_path};customtkinter/',
    f'--add-data={yt_dlp_path};yt_dlp/',
    '--add-data=download_manager/velocity.ico;download_manager/',
    '--add-data=download_manager/ffmpeg.exe;download_manager/',
    '--add-data=download_manager/ffprobe.exe;download_manager/',
    '--exclude-module=yt_dlp',
    '--hidden-import=pystray',
    '--hidden-import=Pillow',
    '--hidden-import=requests',
    '--hidden-import=sqlite3',
    '--hidden-import=tkinter',
    '--hidden-import=customtkinter',
    '--hidden-import=download_manager.ydl_imports'
]

print("Running PyInstaller...")
PyInstaller.__main__.run(args)
print("Build Complete! Check the 'dist/Velocity' folder.")
