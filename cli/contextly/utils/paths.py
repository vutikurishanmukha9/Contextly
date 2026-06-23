import os
from pathlib import Path
from .exceptions import ValidationError

def safe_symlink_resolve(path: Path, max_depth: int = 40) -> Path:
    """
    Resolves symlinks with a hard depth limit to prevent infinite loops.
    Tracks visited paths to prevent cycles.
    """
    seen = set()
    current = Path(path)
    depth = 0
    
    while current.is_symlink():
        if depth >= max_depth:
            raise ValidationError(f"Symlink depth limit exceeded resolving {path}")
            
        real_path = os.path.realpath(current)
        if real_path in seen:
            raise ValidationError(f"Symlink cycle detected at {current}")
            
        seen.add(real_path)
        current = Path(real_path)
        depth += 1
        
    return current.resolve(strict=False)

def safe_resolve(path: Path, root_dir: Path) -> Path:
    """
    Safely resolves a path and ensures it remains within the root directory.
    Prevents path traversal attacks and accidental leaks.
    """
    resolved_path = safe_symlink_resolve(path)
    resolved_root = safe_symlink_resolve(root_dir)
    
    try:
        resolved_path.relative_to(resolved_root)
    except ValueError:
        raise ValidationError(f"Path traversal blocked: {resolved_path} is outside root {resolved_root}")
        
    return resolved_path
