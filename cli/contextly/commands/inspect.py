from pathlib import Path
from rich.table import Table
from ..utils.console import console
from ..utils.exceptions import ValidationError, ContextlyError
from ..utils.fs import find_project_root
from ..utils.validation import require_directory_exists
from ..core.inspector.engine import InspectorEngine
import typer

def inspect_cmd():
    """Deep dive into repository complexity and structure"""
    try:
        root_dir = find_project_root(Path.cwd())
        require_directory_exists(str(root_dir))
    except ValidationError as e:
        console.print(f"[bold red]Error:[/bold red] {e}")
        raise typer.Exit(code=1)
        
    engine = InspectorEngine(root_dir)
    
    with console.status("[bold blue]Inspecting repository file tree...", spinner="bouncingBar"):
        file_sizes = engine.inspect()
    
    console.print("\n[bold green][OK][/bold green] Inspection complete!\n")
    
    table = Table(title="Top 5 Largest Files (Potential Token Hogs)")
    table.add_column("Size (KB)", justify="right", style="cyan")
    table.add_column("File Path", style="magenta")
    
    for size, path in file_sizes[:5]:
        rel_path = path.relative_to(root_dir)
        kb_size = size / 1024
        
        # Highlight massive files that shouldn't go to LLMs
        style = "red" if kb_size > 100 else "yellow" if kb_size > 50 else "white"
        
        table.add_row(f"{kb_size:.1f}", f"[{style}]{rel_path}[/{style}]")
        
    console.print(table)
    console.print("\n[dim]Tip: Files over 50KB (yellow) or 100KB (red) consume massive LLM context windows. Keep them out of your Context Packs if possible.[/dim]\n")

