import os
import platform

def shutdown_pc():
    if platform.system() == "Windows":
        os.system("shutdown /s /t 1")
    elif platform.system() == "Linux" or platform.system() == "Darwin":
        os.system("shutdown now")

def sleep_pc():
    if platform.system() == "Windows":
        os.system("rundll32.exe powrprof.dll,SetSuspendState 0,1,0")
    elif platform.system() == "Linux":
        os.system("systemctl suspend")
    elif platform.system() == "Darwin":
        os.system("pmset sleepnow")
