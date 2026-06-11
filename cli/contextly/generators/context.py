from pathlib import Path
from ..types.models import RepositoryIntelligence
from ..utils.ignore import IgnoreEngine

class ContextGenerator:
    """Generates the advanced PROJECT_CONTEXT.md intelligence document."""

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
                    # Return the first 1000 characters to avoid massive dumps
                    return content[:1000] + ("...\n[truncated]" if len(content) > 1000 else "")
            except Exception:
                pass
        return "No README.md found."

    def _generate_tree(self) -> str:
        """Generates a high-level ASCII directory tree."""
        tree = []
        
        def _walk(dir_path: Path, prefix: str = ""):
            if not dir_path.is_dir():
                return
                
            items = sorted(list(dir_path.iterdir()), key=lambda x: (x.is_file(), x.name))
            
            # Filter out ignored items
            valid_items = [item for item in items if not self.ignorer.is_ignored(item)]
            
            for index, item in enumerate(valid_items):
                is_last = index == len(valid_items) - 1
                connector = "└── " if is_last else "├── "
                
                tree.append(f"{prefix}{connector}{item.name}")
                
                if item.is_dir():
                    extension = "    " if is_last else "│   "
                    _walk(item, prefix + extension)
                    
        tree.append(self.root_dir.name + "/")
        # To avoid massive trees, only map root level and one level down
        # Actually, let's just do a controlled walk
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
                    # Only show files at root depth to keep it clean, or all if we want
                    if depth == 0:
                        tree.append(f"{prefix}{connector}{item.name}")
                        
        _controlled_walk(self.root_dir)
        return "\n".join(tree)

    def generate(self) -> str:
        """Composes the final markdown document."""
        readme = self._get_readme_content()
        tree = self._generate_tree()
        
        npm_count = len(self.intelligence.dependencies.npm)
        py_count = len(self.intelligence.dependencies.python)

        # Build patterns & memory section
        conventions_md = ""
        
        has_memory = bool(self.intelligence.memory.rules)
        has_patterns = bool(self.intelligence.patterns.patterns)
        
        if has_memory or has_patterns:
            conventions_md = "## Team Conventions\n\n"
            
            # Explicit Rules (Memory)
            if has_memory:
                conventions_md += "### Explicit Rules\n_(source: memory)_\n\n"
                categories = {}
                for rule in self.intelligence.memory.rules:
                    if rule.category not in categories:
                        categories[rule.category] = []
                    categories[rule.category].append(rule)
                
                for category, rules in categories.items():
                    conventions_md += f"**{category}**\n"
                    for r in rules:
                        conventions_md += f"- {r.rule}\n"
                conventions_md += "\n"
                
            # Inferred Conventions (Discovery)
            if has_patterns:
                # Filter out patterns that are already manually saved in memory to avoid duplication
                saved_descriptions = {r.rule for r in self.intelligence.memory.rules}
                filtered_patterns = [p for p in self.intelligence.patterns.patterns if p.description not in saved_descriptions]
                
                if filtered_patterns:
                    conventions_md += "### Inferred Conventions\n_(source: discovery)_\n\n"
                    categories = {}
                    for p in filtered_patterns:
                        if p.category not in categories:
                            categories[p.category] = []
                        categories[p.category].append(p)
                        
                    for category, patterns in categories.items():
                        conventions_md += f"**{category}**\n"
                        for p in patterns:
                            conventions_md += f"- {p.name}: {p.description}\n"
                    conventions_md += "\n"

        markdown = f"""# Project Context Intelligence

## Overview
{readme}

{conventions_md}## Architecture Map
```text
{tree}
```

## Stack Identity
- **Primary Language**: {self.intelligence.language.primary}
- **Frontend Framework**: {self.intelligence.frameworks.frontend}
- **Backend/Tooling**: {self.intelligence.frameworks.backend}

## Dependency Weight
- **NPM Packages**: {npm_count}
- **Python Packages**: {py_count}

*Generated automatically by Context-Ly (Max Level Architecture).*
"""
        return markdown
