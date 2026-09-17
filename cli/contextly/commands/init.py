import typer
from pathlib import Path
from ..utils.console import console
from ..core.initializer.engine import InitEngine
from ..utils.exceptions import ContextlyError
from ..utils.fs import find_project_root

def init_cmd(
    quick: bool = typer.Option(False, "--quick", "-q", help="Initialize non-interactively with auto-detected stack profiles"),
    force: bool = typer.Option(False, "--force", "-f", help="Re-initialize configuration even if already present")
):
    """Initialize Context-as-Code in the current directory with intelligent stack profiling."""
    root_dir = find_project_root(Path.cwd())
    engine = InitEngine(root_dir)
    
    try:
        success = engine.initialize(force=force)
        if not success:
            console.print("[yellow]Contextly is already initialized in this repository.[/yellow]")
            console.print("Use [bold cyan]contextly init --force[/bold cyan] to overwrite configuration.")
            return
            
        console.print("[bold green][OK][/bold green] Contextly initialized successfully!")
        console.print(f"Created configuration at [cyan].contextly/config.yaml[/cyan]")
        
        detected = engine.detect_stack()
        langs = ", ".join(detected["languages"]) if detected["languages"] else "Generic"
        frameworks = f" ({', '.join(detected['frameworks'])})" if detected["frameworks"] else ""
        console.print(f"Detected Stack: [bold cyan]{langs}{frameworks}[/bold cyan]")
        if detected.get("profiles"):
            profile_keys = ", ".join(detected["profiles"].keys())
            console.print(f"Auto-configured Profiles: [cyan]{profile_keys}[/cyan]")
        
        console.print("\n[bold]Next Steps:[/bold]")
        console.print("  1. [bold cyan]contextly analyze[/bold cyan]       - Map repo architecture and health")
        console.print("  2. [bold cyan]contextly pack src[/bold cyan]      - Pack and copy prompt directly to clipboard")
        console.print("  3. [bold cyan]contextly memory --auto[/bold cyan] - Discover and learn team coding conventions\n")
        
    except ContextlyError as e:
        console.print(f"[bold red]Error initializing Contextly:[/bold red] {str(e)}")
        raise typer.Exit(code=1)

