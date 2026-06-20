from pathlib import Path
from rich.table import Table
from ..utils.console import console
from ..utils.exceptions import ValidationError, ContextlyError
from ..utils.fs import find_project_root
from ..utils.validation import require_directory_exists
from ..core.inspector.engine import InspectorEngine
import typer

def inspect_cmd(
    no_default_excludes: bool = typer.Option(False, "--no-default-excludes", help="Do not exclude default skip lists (like node_modules, dist, etc.)"),
    output_format: str = typer.Option("text", "--format", help="Output format ('text' or 'json')")
):
    """Deep dive into repository complexity and structure"""
    try:
        root_dir = find_project_root(Path.cwd())
        require_directory_exists(str(root_dir))
    except ValidationError as e:
        if output_format == "json":
            import json
            console.print(json.dumps({"error": str(e)}, indent=2))
        else:
            console.print(f"[bold red]Error:[/bold red] {e}")
        raise typer.Exit(code=1)
        
    engine = InspectorEngine(root_dir, no_default_excludes=no_default_excludes)
    
    if output_format != "json":
        status_ctx = console.status("[bold blue]Inspecting repository file tree...", spinner="bouncingBar")
        status_ctx.start()
        
    try:
        file_sizes = engine.inspect()
    except Exception as e:
        if output_format != "json":
            status_ctx.stop()
        if output_format == "json":
            import json
            console.print(json.dumps({"error": str(e)}, indent=2))
        else:
            console.print(f"\n[bold red]Error:[/bold red] {e}")
        raise typer.Exit(code=1)
    
    if output_format != "json":
        status_ctx.stop()
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
    else:
        import json
        console.print(json.dumps([
            {
                "file": str(path.relative_to(root_dir)),
                "size_bytes": size,
                "size_kb": round(size / 1024, 2)
            } for size, path in file_sizes
        ], indent=2))

