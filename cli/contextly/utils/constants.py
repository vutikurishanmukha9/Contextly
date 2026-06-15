from pathlib import Path

ALWAYS_SKIP_DIRS = {
    ".git", "node_modules", "venv", ".venv", "__pycache__",
    ".contextly", "dist", "build", ".next", ".tox", ".eggs",
    ".mypy_cache", ".pytest_cache", "htmlcov"
}

def is_skippable(path: Path) -> bool:
    """
    Returns True if the path represents a common build artifact, cache, 
    or virtual environment directory that should be ignored by Contextly scanners.
    """
    name = path.name.lower()
    return name in ALWAYS_SKIP_DIRS or name.endswith(".egg-info")
