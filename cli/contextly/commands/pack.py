from pathlib import Path
import typer
from rich.table import Table

from ..utils.console import console
from ..utils.validation import require_directory_exists, require_contextly_initialized
from ..utils.exceptions import ValidationError, ContextlyError
from ..core.packer.engine import PackerEngine

def pack_cmd(
    target: str = typer.Argument(..., help="Directory to pack (e.g., 'src/auth' or '.')"),
    name: str = typer.Option(None, "--name", "-n", help="Name of the context pack (defaults to directory name)")
):
    """Bundle a directory into an LLM-ready Context Pack markdown file"""
    root_dir = Path.cwd().resolve()
    
    try:
        require_contextly_initialized(root_dir)
        target_path = require_directory_exists(target)
        try:
            target_path.relative_to(root_dir)
        except ValueError:
            raise ValidationError("Target directory must be inside the project root directory.")
    except ValidationError as e:
        console.print(f"[bold red]Error:[/bold red] {e}")
        raise typer.Exit(1)
        
    pack_name = name if name else target_path.name
    if pack_name == "" or pack_name == ".":
        pack_name = root_dir.name
        
    engine = PackerEngine(root_dir)
    
    with console.status(f"[bold blue]Packing '{target}' into '{pack_name}'...", spinner="point"):
        try:
            token_estimate, token_type, file_count, output_file = engine.pack(target_path, pack_name)
        except ContextlyError as e:
            console.print(f"[bold red]Error:[/bold red] {e}")
            raise typer.Exit(1)
    
    console.print(f"\n[bold green][OK][/bold green] Context Pack '{pack_name}' created!\n")
    
    table = Table(title="Pack Summary", show_header=False, box=None)
    table.add_column("Metric", style="cyan", justify="right")
    table.add_column("Value", style="magenta")
    
    table.add_row("Source Directory", str(target_path.relative_to(root_dir)))
    table.add_row("Files Packed", str(file_count))
    table.add_row(token_type, f"{token_estimate:,}")
    table.add_row("Output Location", str(output_file.relative_to(root_dir)))
    
    console.print(table)
    
    if token_estimate > 100000:
        console.print("\n[bold red]Warning:[/bold red] This pack is massive (>100k tokens). Make sure your LLM supports large context windows!")
    console.print()

