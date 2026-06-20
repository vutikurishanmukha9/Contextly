import typer
from pathlib import Path
from ..utils.console import console
from ..core.exporter.engine import ExporterEngine
from ..utils.fs import find_project_root
from ..utils.validation import require_contextly_initialized
from ..utils.exceptions import ValidationError, ContextlyError

def export_cmd(
    pack_name: str = typer.Argument(..., help="The name of the context pack to export (e.g., 'frontend')")
):
    """Fuses intelligence and context packs, copying the result to your clipboard."""
    root_dir = find_project_root(Path.cwd())
    
    try:
        require_contextly_initialized(root_dir)
    except ValidationError as e:
        console.print(f"[bold red]Error:[/bold red] {e}")
        raise typer.Exit(code=1)
        
    engine = ExporterEngine(root_dir)
    
    try:
        export_path, clipboard_success = engine.export(pack_name)
    except ContextlyError as e:
        console.print(f"[bold red]Error:[/bold red] {e}")
        raise typer.Exit(code=1)
        
    if clipboard_success:
        clipboard_status = "[green]Successfully copied to clipboard![/green]\n[yellow]Notice: Proprietary source code has been copied to your OS clipboard. Clear it when finished if on a shared/synced device.[/yellow]"
    else:
        clipboard_status = "[yellow]Could not copy to clipboard. The export file was saved successfully.[/yellow]"
        
    console.print(f"\n[bold green][OK][/bold green] Export Generation Complete!")
    console.print(f"  - [cyan]Intelligence:[/cyan] PROJECT_CONTEXT.md")
    console.print(f"  - [cyan]Context Pack:[/cyan] {pack_name}")
    console.print(f"  - [cyan]Local Export:[/cyan] {export_path.relative_to(root_dir)}")
    console.print(f"\n{clipboard_status}")
    if clipboard_success:
        console.print("\nYou can now paste the contents directly into Claude or ChatGPT.")
    else:
        console.print("\nOpen the local export file to copy the contents manually.")

