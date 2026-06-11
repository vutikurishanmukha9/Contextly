from pathlib import Path
from rich.table import Table
from ..utils.console import console
from ..utils.memory import MemoryEngine
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
        
    for category, rules in categories.items():
        console.print(f"[bold cyan]{category}[/bold cyan]")
        for rule in rules:
            source_tag = f"[dim]({rule.source})[/dim]"
            conf_color = "green" if rule.confidence.lower() == "high" else "yellow"
            conf_tag = f"[{conf_color}][{rule.confidence}][/{conf_color}]"
            
            console.print(f"  - {rule.rule} {conf_tag} {source_tag}")
        console.print()
