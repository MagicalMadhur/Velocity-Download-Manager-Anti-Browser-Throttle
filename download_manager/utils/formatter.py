def format_size(bytes_size: int) -> str:
    if bytes_size == 0:
        return "0 B"
    units = ["B", "KB", "MB", "GB", "TB"]
    i = 0
    while bytes_size >= 1024 and i < len(units) - 1:
        bytes_size /= 1024.0
        i += 1
    return f"{bytes_size:.2f} {units[i]}"

def format_speed(bytes_per_sec: int) -> str:
    return format_size(bytes_per_sec) + "/s"

def format_time(seconds: int) -> str:
    if seconds < 0:
        return "Unknown"
    if seconds == 0:
        return "0s"
        
    h = seconds // 3600
    m = (seconds % 3600) // 60
    s = seconds % 60
    
    if h > 0:
        return f"{int(h)}h {int(m)}m {int(s)}s"
    elif m > 0:
        return f"{int(m)}m {int(s)}s"
    else:
        return f"{int(s)}s"
