from abc import ABC, abstractmethod
from pathlib import Path
from ..types.models import RepositoryIntelligence
from ..utils.ignore import IgnoreEngine

class BaseGenerator(ABC):
    """Abstract base class for LLM-specific context generators."""

    def __init__(self, root_dir: Path, intelligence: RepositoryIntelligence):
        self.root_dir = root_dir
        self.intelligence = intelligence
        self.ignorer = IgnoreEngine(root_dir)

    def _get_readme_content(self) -> str:
        """Extracts content from root README.md if it exists."""
        readme_path = self.root_dir / "README.md"
        if readme_path.exists():
            try:
                with open(readme_path, "r", encoding="utf-8") as f:
                    content = f.read()
                    return content[:1000] + ("...\n[truncated]" if len(content) > 1000 else "")
            except (FileNotFoundError, PermissionError, UnicodeDecodeError):
                pass
        return "No README.md found."

    def _generate_tree(self) -> str:
        """Generates a high-level ASCII directory tree."""
        tree = []
        
        def _controlled_walk(dir_path: Path, prefix: str = "", depth: int = 0):
            if depth > 4: # Limit depth to 4 levels to provide a meaningful but constrained tree
                return
                
            try:
                raw_items = list(dir_path.iterdir())
            except OSError:
                return
                
            classified = []
            for item in raw_items:
                if not self.ignorer.is_ignored(item):
                    try:
                        # Single syscall to determine directory status
                        is_dir = item.is_dir()
                        classified.append((is_dir, item))
                    except OSError:
                        pass
            
            # Sort: Directories first (not True -> False, False < True), then by case-insensitive name
            classified.sort(key=lambda x: (not x[0], x[1].name.lower()))
            
            for index, (is_dir, item) in enumerate(classified):
                is_last = index == len(classified) - 1
                connector = "`-- " if is_last else "|-- "
                
                if is_dir:
                    tree.append(f"{prefix}{connector}{item.name}/")
                    extension = "    " if is_last else "|   "
                    _controlled_walk(item, prefix + extension, depth + 1)
                else:
                    tree.append(f"{prefix}{connector}{item.name}")
                        
        tree.append(self.root_dir.name + "/")
        _controlled_walk(self.root_dir)
        return "\n".join(tree)

    @abstractmethod
    def generate(self) -> str:
        """Composes the final document format optimized for a specific LLM."""
        pass
