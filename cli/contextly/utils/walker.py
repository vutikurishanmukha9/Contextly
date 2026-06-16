import os
from pathlib import Path
from typing import Callable, Optional, Generator, Tuple, List

class RepoWalker:
    """
    Utility for walking a repository with configurable depth limits and skip predicates.
    Provides a consistent way to traverse project structures across different scanners.
    """
    
    def __init__(
        self, 
        root_dir: Path, 
        max_depth: Optional[int] = None, 
        skip_predicate: Optional[Callable[[Path], bool]] = None
    ):
        """
        Args:
            root_dir: The root directory to start walking from.
            max_depth: The maximum depth to traverse. 0 means only root_dir. None means infinite.
            skip_predicate: A callable that takes a Path and returns True if the directory should be skipped.
        """
        self.root_dir = root_dir
        self.max_depth = max_depth
        self.skip_predicate = skip_predicate

    def walk(self) -> Generator[Tuple[str, List[str], List[str]], None, None]:
        """
        Yields (root, dirs, files) tuples just like os.walk, but adhering to the depth
        and skip rules provided in the constructor.
        """
        start_depth = len(self.root_dir.parts)
        
        for root, dirs, files in os.walk(self.root_dir, followlinks=False):
            root_path = Path(root)
            current_depth = len(root_path.parts) - start_depth
            
            # Prune directories matching the skip predicate
            if self.skip_predicate:
                dirs[:] = [d for d in dirs if not self.skip_predicate(root_path / d)]
                
            # Prune directories if we've reached max_depth
            if self.max_depth is not None and current_depth >= self.max_depth:
                dirs.clear()
                
            yield root, dirs, files
