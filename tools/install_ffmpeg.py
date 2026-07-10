import urllib.request
import zipfile
import os
import shutil

url = "https://github.com/BtbN/FFmpeg-Builds/releases/download/latest/ffmpeg-master-latest-win64-gpl.zip"
zip_path = "ffmpeg.zip"
extract_dir = "ffmpeg_temp"

print("Downloading FFmpeg...")
urllib.request.urlretrieve(url, zip_path)

print("Extracting...")
with zipfile.ZipFile(zip_path, 'r') as zip_ref:
    zip_ref.extractall(extract_dir)

print("Moving binaries...")
bin_dir = None
for root, dirs, files in os.walk(extract_dir):
    if "ffmpeg.exe" in files:
        bin_dir = root
        break

if bin_dir:
    shutil.copy(os.path.join(bin_dir, "ffmpeg.exe"), "download_manager/ffmpeg.exe")
    shutil.copy(os.path.join(bin_dir, "ffprobe.exe"), "download_manager/ffprobe.exe")
    print("Done! ffmpeg.exe and ffprobe.exe are in download_manager/")
else:
    print("Failed to find ffmpeg.exe in zip.")

# Cleanup
os.remove(zip_path)
shutil.rmtree(extract_dir)
