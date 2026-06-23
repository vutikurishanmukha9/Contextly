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

import re

def sanitize_filename(name: str) -> str:
    """Replaces invalid filename characters with underscores and removes trailing dots/spaces."""
    name = re.sub(r'[\\/*?:"<>|]', '_', name)
    return name.rstrip('. ')[:100]

def save_command_result(command_name: str, args: list[str], content: str, root_dir: Path) -> Path:
    """
    Saves the command output payload or transcript to the centralized exports directory.
    Format: .contextly/exports/contextly <command_name>[ <args>]/contextly <command_name>[ <args>]_result.md
    """
    if not content:
        content = "No output was generated."
        
    cmd_full_name = f"contextly {command_name}"
    if args:
        args_str = " ".join(args)
        if len(args_str) > 50:
            args_str = args_str[:47] + "..."
        cmd_full_name += f" {args_str}"
        
    safe_name = sanitize_filename(cmd_full_name)
        
    cmd_dir = root_dir / ".contextly" / "exports" / safe_name
    cmd_dir.mkdir(parents=True, exist_ok=True)
    
    out_file = cmd_dir / f"{safe_name}_result.md"
    atomic_write(out_file, content)
    
    return out_file
