from pathlib import Path
from rich.table import Table
from ..utils.console import console
from ..utils.ignore import IgnoreEngine

def inspect_cmd():
    """Deep dive into repository complexity and structure"""
    root_dir = Path.cwd()
    ignorer = IgnoreEngine(root_dir)
    
    file_sizes = []
    
    with console.status("[bold blue]Inspecting repository file tree...", spinner="bouncingBar"):
        for path in root_dir.rglob('*'):
            if path.is_file():
                if ignorer.is_ignored(path):
                    continue
                try:
                    size = path.stat().st_size
                    file_sizes.append((size, path))
                except (FileNotFoundError, PermissionError, OSError):
                    pass
                    
    # Sort by size descending
    file_sizes.sort(key=lambda x: x[0], reverse=True)
    
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
    console.print("\n[dim]Tip: Files over 50KB consume massive LLM context windows. Keep them out of your Context Packs if possible.[/dim]\n")
