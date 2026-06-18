from pathlib import Path

def find_project_root(start_path: Path) -> Path:
    """
    Traverses upwards from start_path to find the project root.
    A project root is defined as the directory containing '.contextly' or '.git'.
    If neither is found before reaching the filesystem root, returns start_path.resolve().
    """
    current = start_path.resolve()
    
    while True:
        if (current / ".contextly").is_dir() or (current / ".git").is_dir():
            return current
        if current.parent == current:
            break
        current = current.parent
        
    return start_path.resolve()
