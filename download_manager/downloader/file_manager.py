import os
import hashlib

class FileManager:
    @staticmethod
    def preallocate_file(filepath: str, size: int):
        """
        Preallocates a file of the given size.
        If the file exists and is the same size, it leaves it alone.
        """
        if size <= 0:
            # Touch file
            with open(filepath, 'wb') as f:
                pass
            return
            
        if os.path.exists(filepath):
            current_size = os.path.getsize(filepath)
            if current_size == size:
                return # Already right size
                
        # On Windows, using truncate or writing a zero at the end is fast enough
        # for sparse files if supported, or at least it allocates the space.
        with open(filepath, 'wb') as f:
            f.seek(size - 1)
            f.write(b'\0')
            
    @staticmethod
    def calculate_sha256(filepath: str) -> str:
        sha256_hash = hashlib.sha256()
        with open(filepath, "rb") as f:
            for byte_block in iter(lambda: f.read(4096), b""):
                sha256_hash.update(byte_block)
        return sha256_hash.hexdigest()
