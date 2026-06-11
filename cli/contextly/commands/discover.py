from pathlib import Path
from rich.table import Table
from ..utils.console import console
from ..scanners.dependencies import DependencyScanner
from ..scanners.patterns import PatternScanner

def discover_cmd():
    """Statically analyze the repository to discover architectural patterns and conventions"""
    root_dir = Path.cwd()
    
    with console.status("[bold blue]Running Pattern Discovery Engine...", spinner="dots"):
        dep_scanner = DependencyScanner()
        pat_scanner = PatternScanner()
        
        # We need dependencies first to infer patterns
        deps_result = dep_scanner.scan(root_dir)
        patterns_result = pat_scanner.scan(root_dir, dependencies=deps_result)
        
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
        
    for category, patterns in categories.items():
        console.print(f"[bold cyan]{category}:[/bold cyan]")
        for p in patterns:
            console.print(f"  [green]\\[OK][/green] [bold]{p.name}[/bold] ({p.description})")
        console.print()
