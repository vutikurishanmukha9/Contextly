from pathlib import Path
from ..utils.console import console
from ..scanners.dependencies import DependencyScanner
from ..scanners.patterns import PatternScanner
from ..scanners.base import ScannerError
from ..utils.exceptions import ValidationError, ContextlyError
from ..utils.validation import require_contextly_initialized
import typer

def discover_cmd():
    """Statically analyze the repository to discover architectural patterns and conventions"""
    root_dir = Path.cwd()
    
    try:
        require_contextly_initialized(root_dir)
    except ValidationError as e:
        console.print(f"[bold red]Error:[/bold red] {e}")
        raise typer.Exit(code=1)
        
    with console.status("[bold blue]Running Pattern Discovery Engine...", spinner="dots"):
        try:
            dep_scanner = DependencyScanner()
            pat_scanner = PatternScanner()
            
            # We need dependencies first to infer patterns
            deps_result = dep_scanner.scan(root_dir)
            patterns_result = pat_scanner.scan(root_dir, dependencies=deps_result)
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
        # Sort by confidence descending (High -> Medium -> Low)
        sorted_patterns = sorted(patterns, key=lambda p: {"high": 0, "medium": 1, "low": 2}.get(p.confidence.lower(), 3))
        for p in sorted_patterns:
            console.print(f"  [green]\\[OK][/green] [bold]{p.name}[/bold] ({p.description})")
        console.print()
