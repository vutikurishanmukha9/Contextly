import typer
from pathlib import Path
from rich.prompt import Confirm
from ..utils.console import console
from ..utils.memory import MemoryEngine
from ..scanners.dependencies import DependencyScanner
from ..scanners.patterns import PatternScanner
from ..scanners.base import ScannerError
from ..utils.exceptions import ValidationError, ContextlyError
from ..utils.validation import require_contextly_initialized

def learn_cmd(
    auto: bool = typer.Option(False, "--auto", help="Automatically discover and interactively learn conventions.")
):
    """Teach Context-Ly new conventions, or use --auto to discover them."""
    root_dir = Path.cwd()
    try:
        require_contextly_initialized(root_dir)
    except ValidationError as e:
        console.print(f"[bold red]Error:[/bold red] {e}")
        raise typer.Exit(code=1)
        
    engine = MemoryEngine(root_dir)
    
    if not auto:
        console.print("[yellow]Manual learning is currently disabled in favor of automated discovery.[/yellow]")
        console.print("Please use [bold cyan]contextly learn --auto[/bold cyan]")
        return
        
    with console.status("[bold blue]Running Pattern Discovery Engine...", spinner="dots"):
        try:
            dep_scanner = DependencyScanner()
            pat_scanner = PatternScanner()
            
            deps_result = dep_scanner.scan(root_dir)
            patterns_result = pat_scanner.scan(root_dir, dependencies=deps_result)
        except ScannerError as e:
            console.print(f"\n[bold red]Scanner Error:[/bold red] {e}")
            raise typer.Exit(code=1)
        except ContextlyError as e:
            console.print(f"\n[bold red]Context-Ly Error:[/bold red] {e}")
            raise typer.Exit(code=1)
        
    if not patterns_result.patterns:
        console.print("[yellow]No new recognizable conventions discovered to learn.[/yellow]")
        return
        
    console.print("\n[bold green]Discovered Conventions:[/bold green]\n")
    
    saved_count = 0
    for p in patterns_result.patterns:
        # Prompt for each
        if Confirm.ask(f"Save convention: [cyan]{p.name}[/cyan] ({p.description})?"):
            added = engine.add_rule(
                category=p.category,
                rule_text=p.description,
                confidence=p.confidence,
                source=p.source
            )
            if added:
                saved_count += 1
                console.print(f"  [green]\\[OK][/green] Saved to memory.")
            else:
                console.print(f"  [dim]Skipped (Already in memory).[/dim]")
        else:
            console.print(f"  [dim]Skipped.[/dim]")
            
    if saved_count > 0:
        console.print(f"\n[bold green][OK][/bold green] Successfully saved {saved_count} rules to persistent memory!")
        console.print("Run [bold cyan]contextly memory[/bold cyan] to view them.")
    else:
        console.print("\n[dim]No new rules were saved.[/dim]")
