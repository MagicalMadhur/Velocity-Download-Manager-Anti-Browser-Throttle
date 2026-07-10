import PyInstaller.__main__
import os
import customtkinter

ctk_path = os.path.dirname(customtkinter.__file__)

args = [
    'tools/installer_app.py',
    '--name=Velocity_Setup',
    '--onefile',
    '--windowed',
    '--noconfirm',
    '--icon=download_manager/velocity.ico',
    f'--add-data={ctk_path};customtkinter/',
    '--add-data=dist/Velocity;Velocity_Payload/',
    '--hidden-import=customtkinter'
]

print("Building Setup Wizard...")
PyInstaller.__main__.run(args)
print("Setup Wizard Build Complete! Check the 'dist/Velocity_Setup.exe' file.")
