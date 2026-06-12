from pathlib import Path
import typer
from rich.table import Table
from ..utils.console import console
from ..utils.ignore import IgnoreEngine

from ..utils.validation import require_directory_exists, require_contextly_initialized
from ..utils.exceptions import ValidationError

try:
    import tiktoken
    tokenizer = tiktoken.get_encoding("cl100k_base")
except ImportError:  # pragma: no cover
    tokenizer = None

def pack_cmd(
    target: str = typer.Argument(..., help="Directory to pack (e.g., 'src/auth' or '.')"),
    name: str = typer.Option(None, "--name", "-n", help="Name of the context pack (defaults to directory name)")
):
    """Bundle a directory into an LLM-ready Context Pack markdown file"""
    root_dir = Path.cwd().resolve()
    ignorer = IgnoreEngine(root_dir)
    
    try:
        require_contextly_initialized(root_dir)
        target_path = require_directory_exists(target)
    except ValidationError as e:
        console.print(f"[bold red]Error:[/bold red] {e}")
        raise typer.Exit(1)
        
    pack_name = name if name else target_path.name
    if pack_name == "" or pack_name == ".":
        pack_name = root_dir.name
        
    # Create packs directory
    packs_dir = root_dir / ".contextly" / "packs"
    packs_dir.mkdir(parents=True, exist_ok=True)
    
    output_file = packs_dir / f"{pack_name}.contextpack.md"
    
    file_count = 0
    total_chars = 0
    total_tokens = 0
    
    with console.status(f"[bold blue]Packing '{target}' into '{pack_name}'...", spinner="point"):
        with open(output_file, "w", encoding="utf-8") as out_f:
            out_f.write(f"# Context Pack: {pack_name}\n\n")
            
            # Using try block for path iteration to catch directory permission errors
            try:
                for path in target_path.rglob('*'):
                    try:
                        if path.is_file():
                            if ignorer.is_ignored(path):
                                continue
                            
                            try:
                                rel_path = path.relative_to(root_dir).as_posix()
                                out_f.write(f"## File: `{rel_path}`\n")
                                ext = path.suffix.replace('.', '')
                                out_f.write(f"```{ext}\n")
                                
                                with open(path, "r", encoding="utf-8") as in_f:
                                    for line in in_f:
                                        out_f.write(line)
                                        if tokenizer:
                                            total_tokens += len(tokenizer.encode(line, disallowed_special=()))
                                        else:
                                            total_chars += len(line)
                                            
                                out_f.write(f"\n```\n\n")
                                file_count += 1
                                
                            except UnicodeDecodeError:
                                # Skip binary files or unreadable encodings silently
                                pass
                            except (FileNotFoundError, PermissionError, OSError) as e:
                                console.print(f"[yellow]Warning:[/yellow] Could not read {path.relative_to(root_dir)}: {e}")
                    except PermissionError:
                        continue
            except PermissionError:
                console.print(f"[yellow]Warning:[/yellow] Permission error while traversing directories in {target_path}")
                        
    # Rough token estimation if tiktoken fails, otherwise exact
    if tokenizer:
        token_estimate = total_tokens
        token_type = "Exact Tokens (cl100k_base)"
    else:
        token_estimate = total_chars // 4
        token_type = "Estimated Tokens (chars / 4)"
    
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
