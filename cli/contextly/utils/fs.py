from pathlib import Path

def find_project_root(start_path: Path) -> Path:
    """
    Traverses upwards from start_path to find the project root.
    A project root is defined as the directory containing '.contextly/config.yaml'.
    If not found before reaching the filesystem root, returns start_path.resolve().
    """
    try:
        current = start_path.resolve()
    except Exception:
        current = start_path.absolute()

    seen = set()
    try:
        for parent in [current] + list(current.parents):
            if parent in seen:
                break
            seen.add(parent)
            try:
                if (parent / ".contextly" / "config.yaml").exists() or (parent / ".contextly").is_dir() or (parent / ".git").exists():
                    return parent
            except (PermissionError, OSError):
                pass
    except Exception:
        pass
            
    return current
