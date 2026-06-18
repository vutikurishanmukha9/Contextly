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
        
        from ..utils.config import load_config_model
        self.config = load_config_model(root_dir)
        self.max_tree_depth = self.config.depth_limits.generator_tree

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
            
            if not classified:
                return

            should_truncate = (depth == self.max_tree_depth)

            breadth_limit = getattr(self.config.depth_limits, 'max_tree_breadth', 50)
            if len(classified) > breadth_limit:
                has_truncated_breadth = True
                truncated_count = len(classified) - breadth_limit
                classified = classified[:breadth_limit]
            else:
                has_truncated_breadth = False
                truncated_count = 0

            for index, (is_dir, item) in enumerate(classified):
                is_last = (index == len(classified) - 1) and not has_truncated_breadth
                connector = "`-- " if is_last else "|-- "
                
                if is_dir:
                    tree.append(f"{prefix}{connector}{item.name}/")
                    extension = "    " if is_last else "|   "
                    if not should_truncate:
                        _controlled_walk(item, prefix + extension, depth + 1)
                    else:
                        try:
                            # Only print truncated marker if the directory actually has contents to skip
                            if any(item.iterdir()):
                                tree.append(f"{prefix}{extension}`-- ... (truncated)")
                        except OSError:
                            pass
                else:
                    tree.append(f"{prefix}{connector}{item.name}")

            if has_truncated_breadth:
                tree.append(f"{prefix}`-- ... ({truncated_count} more items)")
                        
        tree.append(self.root_dir.name + "/")
        _controlled_walk(self.root_dir)
        return "\n".join(tree)

    @abstractmethod
    def generate(self) -> str:
        """Composes the final document format optimized for a specific LLM."""
        pass
