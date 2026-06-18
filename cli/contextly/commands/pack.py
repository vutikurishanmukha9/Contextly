from pathlib import Path
import typer
from rich.table import Table

from ..utils.console import console
from ..utils.validation import require_directory_exists, require_contextly_initialized
from ..utils.exceptions import ValidationError, ContextlyError
from ..core.packer.engine import PackerEngine

from ..utils.config import load_config_model
from ..utils.fs import find_project_root
from typing import List, Optional

def pack_cmd(
    target: Optional[str] = typer.Argument(None, help="Directory to pack (e.g., 'src/auth' or '.')"),
    name: str = typer.Option(None, "--name", "-n", help="Name of the context pack (defaults to directory name)"),
    profile: str = typer.Option(None, "--profile", "-p", help="Use a profile defined in .contextly/config.yaml"),
    max_tokens: int = typer.Option(None, "--max-tokens", help="Drop least relevant files to fit within this limit"),
    compress: bool = typer.Option(False, "--compress", "-c", help="Compress AST representations to save tokens"),
    no_default_excludes: bool = typer.Option(False, "--no-default-excludes", help="Do not exclude default skip lists (like node_modules, dist, etc.)")
):
    """Bundle a directory into an LLM-ready Context Pack markdown file"""
    root_dir = find_project_root(Path.cwd())
    

    if not target and not profile:
        target = "."

    target_paths: List[Path] = []
    pack_name = name

    try:
        require_contextly_initialized(root_dir)
        
        if profile:
            config = load_config_model(root_dir)
            if profile not in config.profiles:
                raise ValidationError(f"Profile '{profile}' not found in .contextly/config.yaml")
                
            for p in config.profiles[profile]:
                path = root_dir / p
                try:
                    resolved_path = path.resolve(strict=False)
                    resolved_path.relative_to(root_dir)
                except (ValueError, RuntimeError, OSError):
                    raise ValidationError(f"Profile path '{p}' must be inside the project root directory.")
                
                if not resolved_path.exists():
                    console.print(f"[yellow]Warning:[/yellow] Profile path '{p}' does not exist. Skipping.")
                    continue
                
                target_paths.append(resolved_path)
            
            if not target_paths:
                raise ValidationError(f"No valid paths found for profile '{profile}'.")
                
            if not pack_name:
                pack_name = f"profile_{profile}"
                
        else:
            target_path = Path(target).resolve(strict=False)
            try:
                target_path.relative_to(root_dir)
            except (ValueError, RuntimeError, OSError):
                raise ValidationError("Target directory must be inside the project root directory.")
                
            if not target_path.exists():
                raise ValidationError(f"Target directory does not exist: {target}")
            if not target_path.is_dir():
                raise ValidationError(f"Target is not a directory: {target}")
                
            target_paths.append(target_path)
                
            if not pack_name:
                pack_name = target_path.name
                
        if pack_name == "" or pack_name == ".":
            pack_name = root_dir.name
                    
    except ValidationError as e:
        console.print(f"[bold red]Error:[/bold red] {e}")
        raise typer.Exit(1)
        
    engine = PackerEngine(root_dir, no_default_excludes=no_default_excludes)
    
    target_str = f"profile '{profile}'" if profile else f"'{target}'"
    with console.status(f"[bold blue]Packing {target_str} into '{pack_name}'...", spinner="point"):
        try:
            token_estimate, token_type, file_count, output_file, skipped_files, excluded_count = engine.pack(target_paths, pack_name, max_tokens, compress)
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

