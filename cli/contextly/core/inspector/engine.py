from pathlib import Path
from typing import List, Tuple

from ...utils.ignore import IgnoreEngine

class InspectorEngine:
    def __init__(self, root_dir: Path):
        self.root_dir = root_dir
        self.ignorer = IgnoreEngine(root_dir)

    def inspect(self) -> List[Tuple[int, Path]]:
        """
        Recursively scans the directory to evaluate file sizes.
        Returns a list of (size_in_bytes, file_path) sorted by size descending.
        """
        file_sizes = []
        for path in self.root_dir.rglob('*'):
            if path.is_file():
                if self.ignorer.is_ignored(path):
                    continue
                try:
                    size = path.stat().st_size
                    file_sizes.append((size, path))
                except (FileNotFoundError, PermissionError, OSError):
                    pass
                    
        file_sizes.sort(key=lambda x: x[0], reverse=True)
        return file_sizes
