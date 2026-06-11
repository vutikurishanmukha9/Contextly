from pathlib import Path
import typer
from rich.table import Table
from ..utils.console import console
from ..utils.ignore import IgnoreEngine

def pack_cmd(
    target: str = typer.Argument(..., help="Directory to pack (e.g., 'src/auth' or '.')"),
    name: str = typer.Option(None, "--name", "-n", help="Name of the context pack (defaults to directory name)")
):
    """Bundle a directory into an LLM-ready Context Pack markdown file"""
    root_dir = Path.cwd()
    ignorer = IgnoreEngine(root_dir)
    
    target_path = Path(target).resolve()
    
    if not target_path.exists():
        console.print(f"[bold red]Error:[/bold red] Target directory '{target}' does not exist.")
        raise typer.Exit(1)
        
    if not target_path.is_dir():
        console.print(f"[bold red]Error:[/bold red] Target '{target}' is not a directory.")
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
    
    with console.status(f"[bold blue]Packing '{target}' into '{pack_name}'...", spinner="point"):
        with open(output_file, "w", encoding="utf-8") as out_f:
            out_f.write(f"# Context Pack: {pack_name}\n\n")
            
            for path in target_path.rglob('*'):
                if path.is_file():
                    if ignorer.is_ignored(path):
                        continue
                    
                    try:
                        with open(path, "r", encoding="utf-8") as in_f:
                            content = in_f.read()
                            
                        rel_path = path.relative_to(root_dir).as_posix()
                        out_f.write(f"## File: `{rel_path}`\n")
                        # Simple language inference from extension for syntax highlighting
                        ext = path.suffix.replace('.', '')
                        out_f.write(f"```{ext}\n{content}\n```\n\n")
                        
                        file_count += 1
                        total_chars += len(content)
                    except UnicodeDecodeError:
                        # Skip binary files or unreadable encodings silently
                        pass
                    except Exception as e:
                        console.print(f"[yellow]Warning:[/yellow] Could not read {path}: {e}")
                        
    # Rough token estimation (1 token ≈ 4 chars)
    token_estimate = total_chars // 4
    
    console.print(f"\n[bold green][OK][/bold green] Context Pack '{pack_name}' created!\n")
    
    table = Table(title="Pack Summary", show_header=False, box=None)
    table.add_column("Metric", style="cyan", justify="right")
    table.add_column("Value", style="magenta")
    
    table.add_row("Source Directory", str(target_path.relative_to(root_dir)))
    table.add_row("Files Packed", str(file_count))
    table.add_row("Estimated Tokens", f"{token_estimate:,}")
    table.add_row("Output Location", str(output_file.relative_to(root_dir)))
    
    console.print(table)
    
    if token_estimate > 100000:
        console.print("\n[bold red]Warning:[/bold red] This pack is massive (>100k tokens). Make sure your LLM supports large context windows!")
    console.print()
