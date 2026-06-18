from pathlib import Path
from typing import List, Tuple

from ...utils.ignore import IgnoreEngine

class InspectorEngine:
    def __init__(self, root_dir: Path, no_default_excludes: bool = False):
        self.root_dir = root_dir
        self.ignorer = IgnoreEngine(root_dir, no_default_excludes=no_default_excludes)

    def inspect(self) -> List[Tuple[int, Path]]:
        """
        Returns a list of (size_in_bytes, file_path) sorted by size descending.
        """
        import os
        file_sizes = []
        for root, dirs, files in os.walk(self.root_dir, followlinks=False):
            root_path = Path(root)
            
            # Prune ignored directories in-place
            dirs[:] = [d for d in dirs if not self.ignorer.is_ignored(root_path / d)]
            
            for f in files:
                file_path = root_path / f
                if self.ignorer.is_ignored(file_path):
                    continue
                try:
                    size = file_path.stat().st_size
                    file_sizes.append((size, file_path))
                except (FileNotFoundError, PermissionError, OSError):
                    pass
                    
        file_sizes.sort(key=lambda x: x[0], reverse=True)
        return file_sizes
