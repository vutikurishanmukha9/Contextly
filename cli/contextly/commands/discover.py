from pathlib import Path
import typer

from ..utils.console import console
from ..core.discovery.engine import DiscoveryEngine
from ..scanners.base import ScannerError
from ..utils.exceptions import ValidationError, ContextlyError
from ..utils.fs import find_project_root
from ..utils.validation import require_contextly_initialized

def discover_cmd():
    """Auto-discover technical patterns and update knowledge base"""
    root_dir = find_project_root(Path.cwd())
    
    try:
        require_contextly_initialized(root_dir)
    except ValidationError as e:
        console.print(f"[bold red]Error:[/bold red] {e}")
        raise typer.Exit(code=1)
        
    engine = DiscoveryEngine(root_dir)
        
    with console.status("[bold blue]Running Pattern Discovery Engine...", spinner="dots"):
        try:
            patterns_result = engine.discover()
        except ScannerError as e:
            console.print(f"\n[bold red]Scanner Error:[/bold red] {e}")
            raise typer.Exit(code=1)
        except ContextlyError as e:
            console.print(f"\n[bold red]Context-Ly Error:[/bold red] {e}")
            raise typer.Exit(code=1)
        
    console.print("[bold green][OK][/bold green] Pattern Discovery Complete:\n")
    
    if not patterns_result.patterns:
        console.print("[yellow]No recognizable architectural patterns or conventions discovered.[/yellow]")
        return

    # Group by category
    categories = {}
    for p in patterns_result.patterns:
        if p.category not in categories:
            categories[p.category] = []
        categories[p.category].append(p)
        
    for category, patterns in sorted(categories.items()):
        console.print(f"[bold cyan]{category}:[/bold cyan]")
        # Sort by confidence descending
        sorted_patterns = sorted(patterns, key=lambda p: p.confidence, reverse=True)
        for p in sorted_patterns:
            conf_str = "High" if p.confidence >= 0.9 else "Medium" if p.confidence >= 0.7 else "Low"
            console.print(f"  [green]\\[OK][/green] [bold]{p.name}[/bold] ({conf_str} Confidence) - {p.description}")
        console.print()
