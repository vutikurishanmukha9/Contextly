import typer
from pathlib import Path
from ..utils.console import console
from ..core.initializer.engine import InitEngine
from ..utils.exceptions import ContextlyError
from ..utils.fs import find_project_root

def init_cmd():
    """Initialize Context-as-Code in the current directory"""
    root_dir = find_project_root(Path.cwd())
    engine = InitEngine(root_dir)
    
    try:
        success = engine.initialize()
        if not success:
            console.print("[yellow]Contextly is already initialized in this repository.[/yellow]")
            return
            
        console.print("[bold green][OK][/bold green] Contextly initialized successfully!")
        console.print(f"Created configuration at [cyan].contextly/config.yaml[/cyan]")
        console.print("Edit this file to define your Context-as-Code rules.")
        
    except ContextlyError as e:
        console.print(f"[bold red]Error initializing Contextly:[/bold red] {str(e)}")
        raise typer.Exit(code=1)
