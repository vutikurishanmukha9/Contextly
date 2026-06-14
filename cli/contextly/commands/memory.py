from pathlib import Path
from rich.table import Table
from ..utils.console import console
from ..core.memory import MemoryEngine
from ..utils.exceptions import ValidationError
from ..utils.validation import require_contextly_initialized
from ..utils.fs import find_project_root
import typer

def memory_cmd():
    """Inspect the persistently stored team memory and conventions."""
    root_dir = find_project_root(Path.cwd())
    
    try:
        require_contextly_initialized(root_dir)
    except ValidationError as e:
        console.print(f"[bold red]Error:[/bold red] {e}")
        raise typer.Exit(code=1)
        
    engine = MemoryEngine(root_dir)
    
    memory = engine.load_memory()
    
    if not memory.rules:
        console.print("[yellow]Context-Ly memory is currently empty.[/yellow]")
        console.print("Run [bold cyan]contextly learn --auto[/bold cyan] to discover and save team conventions.")
        return
        
    console.print(f"[bold green]Stored Memory[/bold green] (Found {len(memory.rules)} rules)\n")
    
    # Group by category
    categories = {}
    for rule in memory.rules:
        if rule.category not in categories:
            categories[rule.category] = []
        categories[rule.category].append(rule)
        
    for category, rules in sorted(categories.items()):
        console.print(f"[bold cyan]{category}[/bold cyan]")
        sorted_rules = sorted(rules, key=lambda r: r.confidence, reverse=True)
        for rule in sorted_rules:
            conf_str = "High" if rule.confidence >= 0.9 else "Medium" if rule.confidence >= 0.7 else "Low"
            conf_color = "green" if rule.confidence >= 0.9 else "yellow"
            source_tag = f"[dim]({rule.source})[/dim]"
            
            console.print(f"  - [dim]\\[{rule.id}][/dim] {rule.rule} ([{conf_color}]{conf_str}[/{conf_color}] conf) {source_tag}")
        console.print()
