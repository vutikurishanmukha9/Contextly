from pathlib import Path

def find_project_root(start_path: Path) -> Path:
    """
    Traverses upwards from start_path to find the project root.
    A project root is defined as the directory containing '.contextly/config.toml'.
    If not found before reaching the filesystem root, returns start_path.resolve().
    """
    current = start_path.resolve()
    for parent in [current] + list(current.parents):
        if (parent / ".contextly" / "config.toml").exists() or (parent / ".contextly").is_dir() or (parent / ".git").is_dir():
            return parent
            
    return start_path.resolve()
