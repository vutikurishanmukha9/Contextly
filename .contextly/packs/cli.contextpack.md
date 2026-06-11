# Context Pack: cli

## File: `cli/pyproject.toml`
```toml
[build-system]
requires = ["setuptools>=61.0"]
build-backend = "setuptools.build_meta"

[project]
name = "contextly"
version = "0.1.0"
description = "Context Intelligence Engine for LLMs"
readme = "README.md"
authors = [
    { name = "Contextly Team" }
]
requires-python = ">=3.9"
dependencies = [
    "typer>=0.12.0",
    "rich>=13.7.0",
    "pyyaml>=6.0.1",
    "pydantic>=2.0.0",
    "pathspec>=0.12.0"
]

[project.scripts]
contextly = "contextly.main:app"

```

## File: `cli/README.md`
```md
# Contextly CLI
Context Intelligence Engine.

```

## File: `cli/contextly/main.py`
```py
import typer
from rich.console import Console

# Import commands (we will create these modules next)
from .commands import init, analyze, inspect, pack

app = typer.Typer(
    name="contextly",
    help="Context Intelligence Engine for LLMs",
    add_completion=False,
)

# Add commands
app.command(name="init", help="Initialize Context-as-Code in the current directory")(init.init_cmd)
app.command(name="analyze", help="Automatically analyze and map the repository")(analyze.analyze_cmd)
app.command(name="inspect", help="Deep dive into repository complexity and structure")(inspect.inspect_cmd)
app.command(name="pack", help="Bundle a directory into an LLM-ready Context Pack")(pack.pack_cmd)

console = Console()

if __name__ == "__main__":
    app()

```

## File: `cli/contextly/__init__.py`
```py
# Contextly CLI Package

```

## File: `cli/contextly.egg-info/dependency_links.txt`
```txt


```

## File: `cli/contextly.egg-info/entry_points.txt`
```txt
[console_scripts]
contextly = contextly.main:app

```

## File: `cli/contextly.egg-info/PKG-INFO`
```
Metadata-Version: 2.4
Name: contextly
Version: 0.1.0
Summary: Context Intelligence Engine for LLMs
Author: Contextly Team
Requires-Python: >=3.9
Description-Content-Type: text/markdown
Requires-Dist: typer>=0.12.0
Requires-Dist: rich>=13.7.0
Requires-Dist: pyyaml>=6.0.1
Requires-Dist: pydantic>=2.0.0
Requires-Dist: pathspec>=0.12.0

# Contextly CLI
Context Intelligence Engine.

```

## File: `cli/contextly.egg-info/requires.txt`
```txt
typer>=0.12.0
rich>=13.7.0
pyyaml>=6.0.1
pydantic>=2.0.0
pathspec>=0.12.0

```

## File: `cli/contextly.egg-info/SOURCES.txt`
```txt
README.md
pyproject.toml
contextly/__init__.py
contextly/main.py
contextly.egg-info/PKG-INFO
contextly.egg-info/SOURCES.txt
contextly.egg-info/dependency_links.txt
contextly.egg-info/entry_points.txt
contextly.egg-info/requires.txt
contextly.egg-info/top_level.txt
contextly/commands/__init__.py
contextly/commands/analyze.py
contextly/commands/init.py
contextly/commands/inspect.py
contextly/scanners/__init__.py
contextly/scanners/base.py
contextly/scanners/dependencies.py
contextly/scanners/framework.py
contextly/scanners/language.py
contextly/types/__init__.py
contextly/types/models.py
contextly/utils/__init__.py
contextly/utils/console.py
```

## File: `cli/contextly.egg-info/top_level.txt`
```txt
contextly

```

## File: `cli/contextly/commands/analyze.py`
```py
import time
from pathlib import Path
import concurrent.futures
from rich.table import Table
from ..utils.console import console

from ..scanners.dependencies import DependencyScanner
from ..scanners.language import LanguageScanner
from ..scanners.framework import FrameworkScanner
from ..scanners.base import ScannerError
from ..types.models import RepositoryIntelligence

from ..generators.context import ContextGenerator

def analyze_cmd():
    """Automatically analyze and map the repository"""
    root_dir = Path.cwd()
    
    with console.status("[bold blue]Scanning repository intelligence (Max Level)...", spinner="dots"):
        # We will use ThreadPoolExecutor to run the IO-bound dependency and language scanners concurrently
        lang_scanner = LanguageScanner()
        dep_scanner = DependencyScanner()
        fw_scanner = FrameworkScanner()
        
        try:
            with concurrent.futures.ThreadPoolExecutor(max_workers=2) as executor:
                lang_future = executor.submit(lang_scanner.scan, root_dir)
                dep_future = executor.submit(dep_scanner.scan, root_dir)
                
                lang_data = lang_future.result()
                dep_data = dep_future.result()
                
            # Framework depends on dependencies being resolved first
            fw_data = fw_scanner.scan(root_dir, deps=dep_data)
            
            # Aggregate into the strict Pydantic model
            intelligence = RepositoryIntelligence(
                language=lang_data,
                dependencies=dep_data,
                frameworks=fw_data
            )
        except ScannerError as e:
            console.print(f"\n[bold red]Scanner Error:[/bold red] {e}")
            return
        except Exception as e:
            console.print(f"\n[bold red]Unexpected Error:[/bold red] {e}")
            return
            
    console.print("\n[bold green][OK][/bold green] Repository scan complete!\n")
    
    # Build output table
    table = Table(title="Repository Intelligence (Max Level)", show_header=False, box=None)
    table.add_column("Category", style="cyan", justify="right")
    table.add_column("Value", style="magenta")
    
    table.add_row("Primary Language", f"[bold]{intelligence.language.primary}[/bold]")
    table.add_row("Frontend Framework", intelligence.frameworks.frontend)
    table.add_row("Backend/Tooling", intelligence.frameworks.backend)
    
    npm_count = len(intelligence.dependencies.npm)
    py_count = len(intelligence.dependencies.python)
    
    if npm_count > 0:
        table.add_row("NPM Dependencies", str(npm_count))
    if py_count > 0:
        table.add_row("Python Dependencies", str(py_count))
        
    console.print(table)
    console.print()
    
    # Generate Advanced PROJECT_CONTEXT.md
    generator = ContextGenerator(root_dir, intelligence)
    ctx_content = generator.generate()
    
    try:
        with open("PROJECT_CONTEXT.md", "w", encoding="utf-8") as f:
            f.write(ctx_content)
        console.print("[dim]Generated advanced PROJECT_CONTEXT.md in current directory.[/dim]")
    except Exception as e:
        console.print(f"[red]Failed to write PROJECT_CONTEXT.md: {e}[/red]")

```

## File: `cli/contextly/commands/init.py`
```py
import os
import yaml
from pathlib import Path
from ..utils.console import console

def init_cmd():
    """Initialize Context-as-Code in the current directory"""
    target_dir = Path.cwd() / ".contextly"
    
    if target_dir.exists():
        console.print("[yellow]Contextly is already initialized in this repository.[/yellow]")
        return
        
    try:
        # Create directories
        target_dir.mkdir(parents=True)
        (target_dir / "memory").mkdir()
        (target_dir / "packs").mkdir()
        
        # Create default config.yaml
        config = {
            "project": {
                "name": Path.cwd().name,
            },
            "stack": {
                "frontend": "",
                "backend": ""
            },
            "rules": [
                "add your coding standards here",
                "e.g., typescript-only",
                "e.g., no-any"
            ],
            "ai": {
                "preferredModel": "claude"
            }
        }
        
        config_path = target_dir / "config.yaml"
        with open(config_path, "w") as f:
            yaml.dump(config, f, default_flow_style=False, sort_keys=False)
            
        console.print("[bold green][OK][/bold green] Contextly initialized successfully!")
        console.print(f"Created configuration at [cyan].contextly/config.yaml[/cyan]")
        console.print("Edit this file to define your Context-as-Code rules.")
        
    except Exception as e:
        console.print(f"[bold red]Error initializing Contextly:[/bold red] {str(e)}")

```

## File: `cli/contextly/commands/inspect.py`
```py
from pathlib import Path
from rich.table import Table
from ..utils.console import console
from ..utils.ignore import IgnoreEngine

def inspect_cmd():
    """Deep dive into repository complexity and structure"""
    root_dir = Path.cwd()
    ignorer = IgnoreEngine(root_dir)
    
    file_sizes = []
    
    with console.status("[bold blue]Inspecting repository file tree...", spinner="bouncingBar"):
        for path in root_dir.rglob('*'):
            if path.is_file():
                if ignorer.is_ignored(path):
                    continue
                try:
                    size = path.stat().st_size
                    file_sizes.append((size, path))
                except Exception:
                    pass
                    
    # Sort by size descending
    file_sizes.sort(key=lambda x: x[0], reverse=True)
    
    console.print("\n[bold green][OK][/bold green] Inspection complete!\n")
    
    table = Table(title="Top 5 Largest Files (Potential Token Hogs)")
    table.add_column("Size (KB)", justify="right", style="cyan")
    table.add_column("File Path", style="magenta")
    
    for size, path in file_sizes[:5]:
        rel_path = path.relative_to(root_dir)
        kb_size = size / 1024
        
        # Highlight massive files that shouldn't go to LLMs
        style = "red" if kb_size > 100 else "yellow" if kb_size > 50 else "white"
        
        table.add_row(f"{kb_size:.1f}", f"[{style}]{rel_path}[/{style}]")
        
    console.print(table)
    console.print("\n[dim]Tip: Files over 50KB consume massive LLM context windows. Keep them out of your Context Packs if possible.[/dim]\n")

```

## File: `cli/contextly/commands/pack.py`
```py
from pathlib import Path
import typer
from rich.table import Table
from ..utils.console import console
from ..utils.ignore import IgnoreEngine

def pack_cmd(
    target: str = typer.Argument(..., help="Directory to pack (e.g., 'src/auth' or '.')"),
    name: str = typer.Option(None, "--name", "-n", help="Name of the context pack (defaults to directory name)")
):
    """Bundle a directory into an LLM-ready Context Pack markdown file"""
    root_dir = Path.cwd()
    ignorer = IgnoreEngine(root_dir)
    
    target_path = Path(target).resolve()
    
    if not target_path.exists():
        console.print(f"[bold red]Error:[/bold red] Target directory '{target}' does not exist.")
        raise typer.Exit(1)
        
    if not target_path.is_dir():
        console.print(f"[bold red]Error:[/bold red] Target '{target}' is not a directory.")
        raise typer.Exit(1)
        
    pack_name = name if name else target_path.name
    if pack_name == "" or pack_name == ".":
        pack_name = root_dir.name
        
    # Create packs directory
    packs_dir = root_dir / ".contextly" / "packs"
    packs_dir.mkdir(parents=True, exist_ok=True)
    
    output_file = packs_dir / f"{pack_name}.contextpack.md"
    
    file_count = 0
    total_chars = 0
    
    with console.status(f"[bold blue]Packing '{target}' into '{pack_name}'...", spinner="point"):
        with open(output_file, "w", encoding="utf-8") as out_f:
            out_f.write(f"# Context Pack: {pack_name}\n\n")
            
            for path in target_path.rglob('*'):
                if path.is_file():
                    if ignorer.is_ignored(path):
                        continue
                    
                    try:
                        with open(path, "r", encoding="utf-8") as in_f:
                            content = in_f.read()
                            
                        rel_path = path.relative_to(root_dir).as_posix()
                        out_f.write(f"## File: `{rel_path}`\n")
                        # Simple language inference from extension for syntax highlighting
                        ext = path.suffix.replace('.', '')
                        out_f.write(f"```{ext}\n{content}\n```\n\n")
                        
                        file_count += 1
                        total_chars += len(content)
                    except UnicodeDecodeError:
                        # Skip binary files or unreadable encodings silently
                        pass
                    except Exception as e:
                        console.print(f"[yellow]Warning:[/yellow] Could not read {path}: {e}")
                        
    # Rough token estimation (1 token ≈ 4 chars)
    token_estimate = total_chars // 4
    
    console.print(f"\n[bold green][OK][/bold green] Context Pack '{pack_name}' created!\n")
    
    table = Table(title="Pack Summary", show_header=False, box=None)
    table.add_column("Metric", style="cyan", justify="right")
    table.add_column("Value", style="magenta")
    
    table.add_row("Source Directory", str(target_path.relative_to(root_dir)))
    table.add_row("Files Packed", str(file_count))
    table.add_row("Estimated Tokens", f"{token_estimate:,}")
    table.add_row("Output Location", str(output_file.relative_to(root_dir)))
    
    console.print(table)
    
    if token_estimate > 100000:
        console.print("\n[bold red]Warning:[/bold red] This pack is massive (>100k tokens). Make sure your LLM supports large context windows!")
    console.print()

```

## File: `cli/contextly/commands/__init__.py`
```py
# Init commands

```

## File: `cli/contextly/generators/context.py`
```py
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

        markdown = f"""# Project Context Intelligence

## Overview
{readme}

## Architecture Map
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

```

## File: `cli/contextly/generators/__init__.py`
```py
# Init generators

```

## File: `cli/contextly/scanners/base.py`
```py
from abc import ABC, abstractmethod
from pathlib import Path
from pydantic import BaseModel

class ScannerError(Exception):
    """Raised when a scanner fails unexpectedly."""
    pass

class BaseScanner(ABC):
    @property
    @abstractmethod
    def name(self) -> str:
        """The human-readable name of the scanner"""
        pass

    @abstractmethod
    def scan(self, root_dir: Path, **kwargs) -> BaseModel:
        """
        Executes the scan on the repository.
        
        Args:
            root_dir: The root Path of the repository.
            **kwargs: Additional context if a scanner depends on another (e.g. framework depends on dependencies).
            
        Returns:
            A strictly validated Pydantic model representing the scan results.
        """
        pass

```

## File: `cli/contextly/scanners/dependencies.py`
```py
import json
from pathlib import Path
from .base import BaseScanner, ScannerError
from ..types.models import DependencyScanResult
from ..utils.ignore import IgnoreEngine

class DependencyScanner(BaseScanner):
    @property
    def name(self) -> str:
        return "Dependency Scanner"

    def scan(self, root_dir: Path, **kwargs) -> DependencyScanResult:
        try:
            result = DependencyScanResult()
            ignorer = IgnoreEngine(root_dir)
            
            # Helper to safely parse package.json dependencies
            def _parse_package_json(filepath: Path):
                try:
                    with open(filepath, 'r') as f:
                        data = json.load(f)
                        deps = list(data.get("dependencies", {}).keys()) + list(data.get("devDependencies", {}).keys())
                        result.npm.extend(deps)
                except Exception:
                    pass

            # Root package.json
            if (root_dir / "package.json").exists():
                _parse_package_json(root_dir / "package.json")
                
            # Quick sub-directory scan for package.json (to catch mono-repos like "frontend/")
            # We don't do full rglob to save time, just one level deep
            for item in root_dir.iterdir():
                if item.is_dir() and not ignorer.is_ignored(item):
                    if (item / "package.json").exists():
                        _parse_package_json(item / "package.json")
                
            # Check python (requirements.txt)
            req_txt = root_dir / "requirements.txt"
            if req_txt.exists():
                try:
                    with open(req_txt, 'r') as f:
                        lines = f.readlines()
                        result.python.extend([line.split("==")[0].strip() for line in lines if line.strip() and not line.startswith("#")])
                except Exception:
                    pass
                    
            # Check python (pyproject.toml)
            pyproject = root_dir / "pyproject.toml"
            if pyproject.exists():
                try:
                    with open(pyproject, 'r') as f:
                        content = f.read()
                        if "typer" in content: result.python.append("typer")
                        if "rich" in content: result.python.append("rich")
                        if "pyyaml" in content: result.python.append("pyyaml")
                        if "pydantic" in content: result.python.append("pydantic")
                except Exception:
                    pass

            # De-duplicate
            result.npm = list(set(result.npm))
            result.python = list(set(result.python))
            
            return result
            
        except Exception as e:
            raise ScannerError(f"Dependency scan failed: {str(e)}")

```

## File: `cli/contextly/scanners/framework.py`
```py
from pathlib import Path
from .base import BaseScanner, ScannerError
from ..types.models import DependencyScanResult, FrameworkScanResult

class FrameworkScanner(BaseScanner):
    @property
    def name(self) -> str:
        return "Framework Scanner"

    def scan(self, root_dir: Path, **kwargs) -> FrameworkScanResult:
        try:
            deps: DependencyScanResult = kwargs.get("deps", DependencyScanResult())
            
            framework = "None detected"
            backend = "None detected"
            
            # Frontend
            if "next" in deps.npm:
                framework = "Next.js"
            elif "react" in deps.npm:
                framework = "React (SPA)"
            elif "vue" in deps.npm:
                framework = "Vue.js"
            elif "nuxt" in deps.npm:
                framework = "Nuxt.js"
            elif "svelte" in deps.npm:
                framework = "SvelteKit"
                
            # Backend (Node)
            if "express" in deps.npm:
                backend = "Express.js"
            elif "nestjs" in deps.npm or "@nestjs/core" in deps.npm:
                backend = "NestJS"
                
            # Backend (Python)
            if "fastapi" in deps.python:
                backend = "FastAPI"
            elif "django" in deps.python:
                backend = "Django"
            elif "flask" in deps.python:
                backend = "Flask"
                
            # Python CLI
            if "typer" in deps.python or "click" in deps.python:
                framework = "Python CLI"
                
            return FrameworkScanResult(
                frontend=framework,
                backend=backend
            )
        except Exception as e:
            raise ScannerError(f"Framework scan failed: {str(e)}")

```

## File: `cli/contextly/scanners/language.py`
```py
from pathlib import Path
from collections import Counter
from .base import BaseScanner, ScannerError
from ..types.models import LanguageScanResult
from ..utils.ignore import IgnoreEngine

class LanguageScanner(BaseScanner):
    @property
    def name(self) -> str:
        return "Language Scanner"

    def scan(self, root_dir: Path, **kwargs) -> LanguageScanResult:
        try:
            exts = Counter()
            ignorer = IgnoreEngine(root_dir)
            
            for path in root_dir.rglob('*'):
                if path.is_file():
                    if ignorer.is_ignored(path):
                        continue
                    if path.suffix:
                        exts[path.suffix.lower()] += 1
                        
            total = sum(exts.values())
            if total == 0:
                return LanguageScanResult(primary="Unknown", breakdown={})
                
            primary_ext = exts.most_common(1)[0][0]
            ext_map = {
                '.ts': 'TypeScript',
                '.tsx': 'TypeScript (React)',
                '.js': 'JavaScript',
                '.jsx': 'JavaScript (React)',
                '.py': 'Python',
                '.go': 'Go',
                '.rs': 'Rust',
                '.java': 'Java',
                '.md': 'Markdown'
            }
            
            primary_lang = ext_map.get(primary_ext, primary_ext)
            
            if primary_ext in ['.ts', '.tsx']:
                primary_lang = 'TypeScript'
                
            return LanguageScanResult(
                primary=primary_lang,
                breakdown=dict(exts.most_common(5))
            )
        except Exception as e:
            raise ScannerError(f"Language scan failed: {str(e)}")

```

## File: `cli/contextly/scanners/__init__.py`
```py
# Init scanners

```

## File: `cli/contextly/types/models.py`
```py
from typing import Dict, List, Optional
from pydantic import BaseModel, Field

class LanguageScanResult(BaseModel):
    primary: str = Field(..., description="The primary language of the repository")
    breakdown: Dict[str, int] = Field(default_factory=dict, description="Extension breakdown counts")

class DependencyScanResult(BaseModel):
    npm: List[str] = Field(default_factory=list, description="List of NPM dependencies")
    python: List[str] = Field(default_factory=list, description="List of Python dependencies")
    go: List[str] = Field(default_factory=list, description="List of Go dependencies")
    rust: List[str] = Field(default_factory=list, description="List of Rust dependencies")

class FrameworkScanResult(BaseModel):
    frontend: str = Field(..., description="Detected frontend framework (e.g., Next.js, React)")
    backend: str = Field(..., description="Detected backend framework (e.g., Express, FastAPI)")

class RepositoryIntelligence(BaseModel):
    language: LanguageScanResult
    dependencies: DependencyScanResult
    frameworks: FrameworkScanResult

```

## File: `cli/contextly/types/__init__.py`
```py
# Init types

```

## File: `cli/contextly/utils/console.py`
```py
from rich.console import Console

console = Console()

```

## File: `cli/contextly/utils/ignore.py`
```py
import os
from pathlib import Path
import pathspec

class IgnoreEngine:
    """Centralized ignore logic for Context-Ly"""
    
    def __init__(self, root_dir: Path):
        self.root_dir = root_dir
        
        # Hardcoded defaults that should never be scanned
        self.default_ignores = [
            ".git/",
            "node_modules/",
            "venv/",
            ".venv/",
            "__pycache__/",
            ".contextly/",
            "dist/",
            "build/",
            ".next/"
        ]
        
        self.spec = self._build_spec()
        
    def _build_spec(self) -> pathspec.PathSpec:
        """Reads .gitignore and .contextlyignore and merges with defaults"""
        patterns = list(self.default_ignores)
        
        # Read .gitignore
        gitignore_path = self.root_dir / ".gitignore"
        if gitignore_path.exists():
            try:
                with open(gitignore_path, "r") as f:
                    patterns.extend(f.readlines())
            except Exception:
                pass
                
        # Read .contextlyignore
        contextlyignore_path = self.root_dir / ".contextlyignore"
        if contextlyignore_path.exists():
            try:
                with open(contextlyignore_path, "r") as f:
                    patterns.extend(f.readlines())
            except Exception:
                pass
                
        # Filter empty lines
        patterns = [p.strip() for p in patterns if p.strip()]
        
        return pathspec.PathSpec.from_lines(pathspec.patterns.GitWildMatchPattern, patterns)
        
    def is_ignored(self, path: Path) -> bool:
        """
        Checks if a file or directory path is ignored.
        """
        # Convert path to a relative POSIX string for matching (pathspec requires POSIX style)
        try:
            rel_path = path.relative_to(self.root_dir)
        except ValueError:
            # If path is not relative to root_dir, don't scan it
            return True
            
        str_path = rel_path.as_posix()
        
        if path.is_dir() and not str_path.endswith('/'):
            str_path += '/'
            
        return self.spec.match_file(str_path)

```

## File: `cli/contextly/utils/__init__.py`
```py
# Init utils

```

