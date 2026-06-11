from pathlib import Path
from .exceptions import ValidationError

def require_contextly_initialized(root_dir: Path) -> Path:
    """
    Validates that the directory has been initialized with Context-Ly.
    Returns the path to the PROJECT_CONTEXT.md file.
    Raises ValidationError if not initialized.
    """
    context_file = root_dir / "PROJECT_CONTEXT.md"
    if not context_file.exists():
        raise ValidationError(
            "Context-Ly is not initialized in this directory.\n"
            "Run 'contextly init' first to generate PROJECT_CONTEXT.md"
        )
    return context_file

def require_directory_exists(path_str: str) -> Path:
    """
    Validates that a given path string is a valid, existing directory.
    Raises ValidationError if it doesn't exist or isn't a directory.
    """
    target = Path(path_str).resolve()
    if not target.exists():
        raise ValidationError(f"Target directory does not exist: {target}")
    if not target.is_dir():
        raise ValidationError(f"Target is not a directory: {target}")
    return target
