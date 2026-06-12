from pathlib import Path
from rich.table import Table
from ..utils.console import console
from ..core.memory import MemoryEngine
from ..utils.exceptions import ValidationError
from ..utils.validation import require_contextly_initialized
import typer

def memory_cmd():
    """Inspect the persistently stored team memory and conventions."""
    root_dir = Path.cwd()
    
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
        # Sort by confidence descending (High -> Medium -> Low)
        sorted_rules = sorted(rules, key=lambda r: {"high": 0, "medium": 1, "low": 2}.get(r.confidence.lower(), 3))
        for rule in sorted_rules:
            source_tag = f"[dim]({rule.source})[/dim]"
            conf_color = "green" if rule.confidence.lower() == "high" else "yellow"
            conf_tag = f"[{conf_color}][{rule.confidence}][/{conf_color}]"
            
            console.print(f"  - [dim]\\[{rule.id}][/dim] {rule.rule} {conf_tag} {source_tag}")
        console.print()
