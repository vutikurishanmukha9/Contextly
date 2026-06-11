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
            if depth > 2: # Max depth
                return
            if not dir_path.is_dir():
                return
                
            items = sorted(list(dir_path.iterdir()), key=lambda x: (x.is_file(), x.name))
            valid_items = [item for item in items if not self.ignorer.is_ignored(item)]
            
            for index, item in enumerate(valid_items):
                is_last = index == len(valid_items) - 1
                connector = "└── " if is_last else "├── "
                
                if item.is_dir():
                    tree.append(f"{prefix}{connector}{item.name}/")
                    extension = "    " if is_last else "│   "
                    _controlled_walk(item, prefix + extension, depth + 1)
                else:
                    if depth == 0:
                        tree.append(f"{prefix}{connector}{item.name}")
                        
        tree.append(self.root_dir.name + "/")
        _controlled_walk(self.root_dir)
        return "\n".join(tree)

    @abstractmethod
    def generate(self) -> str:
        """Composes the final document format optimized for a specific LLM."""
        pass
