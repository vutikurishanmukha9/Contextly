from pathlib import Path
import typer
from rich.table import Table

from ..utils.console import console
from ..utils.validation import require_directory_exists, require_contextly_initialized
from ..utils.exceptions import ValidationError, ContextlyError
from ..core.packer.engine import PackerEngine

from ..utils.config import load_config
from typing import List, Optional

def pack_cmd(
    target: Optional[str] = typer.Argument(None, help="Directory to pack (e.g., 'src/auth' or '.')"),
    name: str = typer.Option(None, "--name", "-n", help="Name of the context pack (defaults to directory name)"),
    profile: str = typer.Option(None, "--profile", "-p", help="Use a profile defined in .contextly/config.yaml"),
    max_tokens: int = typer.Option(None, "--max-tokens", help="Drop least relevant files to fit within this limit")
):
    """Bundle a directory into an LLM-ready Context Pack markdown file"""
    root_dir = Path.cwd().resolve()
    

    if not target and not profile:
        target = "."

    target_paths: List[Path] = []
    pack_name = name

    try:
        require_contextly_initialized(root_dir)
        
        if profile:
            config = load_config(root_dir)
            if not config or "profiles" not in config or profile not in config["profiles"]:
                raise ValidationError(f"Profile '{profile}' not found in .contextly/config.yaml")
                
            for p in config["profiles"][profile]:
                path = root_dir / p
                if not path.exists():
                    console.print(f"[yellow]Warning:[/yellow] Profile path '{p}' does not exist. Skipping.")
                    continue
                try:
                    path.resolve().relative_to(root_dir)
                    target_paths.append(path.resolve())
                except ValueError:
                    raise ValidationError(f"Profile path '{p}' must be inside the project root directory.")
            
            if not target_paths:
                raise ValidationError(f"No valid paths found for profile '{profile}'.")
                
            if not pack_name:
                pack_name = f"profile_{profile}"
                
        else:
            target_path = require_directory_exists(target)
            try:
                target_path.relative_to(root_dir)
                target_paths.append(target_path)
            except ValueError:
                raise ValidationError("Target directory must be inside the project root directory.")
                
            if not pack_name:
                pack_name = target_path.name
                
        if pack_name == "" or pack_name == ".":
            pack_name = root_dir.name
                    
    except ValidationError as e:
        console.print(f"[bold red]Error:[/bold red] {e}")
        raise typer.Exit(1)
        
    engine = PackerEngine(root_dir)
    
    target_str = f"profile '{profile}'" if profile else f"'{target}'"
    with console.status(f"[bold blue]Packing {target_str} into '{pack_name}'...", spinner="point"):
        try:
            token_estimate, token_type, file_count, output_file, skipped_files, excluded_count = engine.pack(target_paths, pack_name, max_tokens)
        except ContextlyError as e:
            console.print(f"[bold red]Error:[/bold red] {e}")
            raise typer.Exit(1)
    
    console.print(f"\n[bold green][OK][/bold green] Context Pack '{pack_name}' created!\n")

    if skipped_files:
        for path in skipped_files:
            console.print(f"[yellow]Warning:[/yellow] Could not read {path.relative_to(root_dir)}")
        console.print()
    
    table = Table(title="Pack Summary", show_header=False, box=None)
    table.add_column("Metric", style="cyan", justify="right")
    table.add_column("Value", style="magenta")
    
    table.add_row("Source", target_str)
    table.add_row("Files Packed", str(file_count))
    table.add_row(token_type, f"{token_estimate:,}")
    table.add_row("Output Location", str(output_file.relative_to(root_dir)))
    
    if max_tokens and excluded_count > 0:
        table.add_row("Files Excluded (Token Limit)", str(excluded_count), style="red")
        
    console.print(table)
    
    if max_tokens and excluded_count > 0:
        console.print(f"\n[bold yellow]Note:[/bold yellow] {excluded_count} files were automatically excluded to fit within the {max_tokens} token limit.")
    elif token_estimate > 100000:
        console.print("\n[bold red]Warning:[/bold red] This pack is massive (>100k tokens). Make sure your LLM supports large context windows!")
    console.print()

