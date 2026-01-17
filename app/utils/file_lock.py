"""
Thread-safe file operations utility.
Mencegah race condition saat multiple request mengakses file .txt secara bersamaan.
"""
import threading
from pathlib import Path
from typing import List, Optional
from contextlib import contextmanager


class FileLock:
    """
    Thread-safe file lock menggunakan threading.Lock.
    Satu lock per file path untuk mencegah concurrent access.
    """
    _locks: dict = {}
    _master_lock = threading.Lock()

    @classmethod
    def get_lock(cls, file_path: str) -> threading.Lock:
        """Get atau create lock untuk file tertentu."""
        with cls._master_lock:
            if file_path not in cls._locks:
                cls._locks[file_path] = threading.Lock()
            return cls._locks[file_path]


@contextmanager
def file_lock(file_path: str):
    """
    Context manager untuk file locking.
    
    Usage:
        with file_lock("/path/to/file.txt"):
            # safe file operations here
    """
    lock = FileLock.get_lock(file_path)
    lock.acquire()
    try:
        yield
    finally:
        lock.release()


def safe_read_file(file_path: str) -> List[str]:
    """
    Thread-safe file reading.
    Returns list of lines (excluding header line).
    """
    path = Path(file_path)
    
    with file_lock(file_path):
        if not path.exists():
            return []
        
        with open(path, "r", encoding="utf-8") as f:
            lines = f.readlines()
            # Skip header line (first line)
            return [line.strip() for line in lines[1:] if line.strip()]


def safe_read_file_with_header(file_path: str) -> tuple:
    """
    Thread-safe file reading dengan header.
    Returns tuple (header, lines).
    """
    path = Path(file_path)
    
    with file_lock(file_path):
        if not path.exists():
            return "", []
        
        with open(path, "r", encoding="utf-8") as f:
            lines = f.readlines()
            if not lines:
                return "", []
            
            header = lines[0].strip()
            data_lines = [line.strip() for line in lines[1:] if line.strip()]
            return header, data_lines


def safe_write_file(file_path: str, header: str, lines: List[str]) -> None:
    """
    Thread-safe file writing.
    Writes header + all data lines.
    """
    path = Path(file_path)
    
    # Ensure directory exists
    path.parent.mkdir(parents=True, exist_ok=True)
    
    with file_lock(file_path):
        with open(path, "w", encoding="utf-8") as f:
            f.write(header + "\n")
            for line in lines:
                f.write(line + "\n")


def safe_append_file(file_path: str, line: str) -> None:
    """
    Thread-safe file appending.
    Appends single line to file.
    """
    path = Path(file_path)
    
    with file_lock(file_path):
        with open(path, "a", encoding="utf-8") as f:
            f.write(line + "\n")
