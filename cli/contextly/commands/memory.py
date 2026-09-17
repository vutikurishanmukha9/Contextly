from pathlib import Path
from rich.table import Table
from ..utils.console import console
from ..core.memory import MemoryEngine
from ..utils.exceptions import ValidationError, ContextlyError
from ..utils.validation import require_contextly_initialized
from ..utils.fs import find_project_root
import typer

from typing import Optional

def memory_cmd(
    auto: bool = typer.Option(False, "--auto", "--discover", help="Automatically discover and learn conventions from the repository"),
    apply_all: bool = typer.Option(False, "--apply-all", help="Automatically accept and save all discovered conventions (non-interactive)"),
    learn: Optional[str] = typer.Option(None, "--learn", "--add", help="Teach a custom convention to the memory vault"),
    category: str = typer.Option("Architecture", "--category", "-c", help="Category for the custom convention"),
    delete: Optional[str] = typer.Option(None, "--delete", help="Delete a convention by ID"),
    clear: bool = typer.Option(False, "--clear", help="Clear all stored memory conventions")
):
    """Inspect and manage the persistently stored team memory and conventions."""
    root_dir = find_project_root(Path.cwd())
    
    try:
        require_contextly_initialized(root_dir)
    except ValidationError as e:
        console.print(f"[bold red]Error:[/bold red] {e}")
        raise typer.Exit(code=1)
        
    engine = MemoryEngine(root_dir)

    if auto or apply_all:
        from .learn import learn_cmd
        return learn_cmd(auto=True, apply_all=apply_all)

    if learn:
        try:
            added = engine.add_rule(category=category, rule_text=learn, confidence=1.0, source="user-taught")
            if added:
                console.print(f"[bold green][OK][/bold green] Convention saved to memory vault under '{category}': {learn}")
            else:
                console.print("[yellow]A matching rule is already present in memory vault.[/yellow]")
            return
        except ContextlyError as e:
            console.print(f"\n[bold red]Memory Error:[/bold red] {e}")
            raise typer.Exit(code=1)

    if delete:
        try:
            memory = engine.load_memory()
            initial_count = len(memory.rules)
            memory.rules = [r for r in memory.rules if r.id != delete]
            if len(memory.rules) == initial_count:
                console.print(f"[yellow]Rule ID '{delete}' not found in memory vault.[/yellow]")
            else:
                engine.save_memory(memory)
                console.print(f"[bold green][OK][/bold green] Rule '{delete}' deleted from memory vault.")
            return
        except ContextlyError as e:
            console.print(f"\n[bold red]Memory Error:[/bold red] {e}")
            raise typer.Exit(code=1)

    if clear:
        try:
            memory = engine.load_memory()
            memory.rules = []
            engine.save_memory(memory)
            console.print("[bold green][OK][/bold green] Memory vault cleared.")
            return
        except ContextlyError as e:
            console.print(f"\n[bold red]Memory Error:[/bold red] {e}")
            raise typer.Exit(code=1)
    
    try:
        memory = engine.load_memory()
    except ContextlyError as e:
        console.print(f"\n[bold red]Memory Error:[/bold red] {e}")
        raise typer.Exit(code=1)
    
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
