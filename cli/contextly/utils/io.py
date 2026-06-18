import os
import tempfile
from pathlib import Path

def atomic_write(filepath: Path, content: str, encoding: str = "utf-8") -> None:
    """
    Writes content to a file atomically to prevent data corruption during crashes or interrupts.
    Creates a temporary file in the same directory and renames it to the target path.
    """
    filepath = Path(filepath)
    parent_dir = filepath.parent
    parent_dir.mkdir(parents=True, exist_ok=True)

    # Use a temporary file in the exact same directory to ensure they are on the same filesystem
    # This guarantees that os.replace is an atomic operation.
    fd, temp_path = tempfile.mkstemp(dir=parent_dir, prefix=".tmp-", suffix=".part")
    try:
        with os.fdopen(fd, 'w', encoding=encoding) as f:
            f.write(content)
            f.flush()
            os.fsync(f.fileno()) # Force write to disk
            
        os.replace(temp_path, filepath)
    except Exception:
        # Cleanup temp file on failure
        try:
            os.remove(temp_path)
        except OSError:
            pass
        raise
