import typer
import pyperclip
from pathlib import Path
from datetime import datetime
from ..utils.console import console

def export_cmd(
    pack_name: str = typer.Argument(..., help="The name of the context pack to export (e.g., 'frontend')")
):
    """Fuses intelligence and context packs, copying the result to your clipboard."""
    root_dir = Path.cwd()
    project_context_path = root_dir / "PROJECT_CONTEXT.md"
    pack_path = root_dir / ".contextly" / "packs" / f"{pack_name}.contextpack.md"
    export_dir = root_dir / ".contextly" / "exports"
    
    # 1. Validation
    if not project_context_path.exists():
        console.print("[bold red]Error:[/bold red] PROJECT_CONTEXT.md not found.")
        console.print("Please run [bold cyan]contextly analyze[/bold cyan] first to generate project intelligence.")
        raise typer.Exit(code=1)
        
    if not pack_path.exists():
        console.print(f"[bold red]Error:[/bold red] Context Pack '{pack_name}' not found at {pack_path.relative_to(root_dir)}.")
        console.print(f"Please run [bold cyan]contextly pack <dir>[/bold cyan] to generate it.")
        raise typer.Exit(code=1)
        
    export_dir.mkdir(parents=True, exist_ok=True)
    
    # 2. Read contents
    try:
        with open(project_context_path, "r", encoding="utf-8") as f:
            intelligence_layer = f.read()
            
        with open(pack_path, "r", encoding="utf-8") as f:
            pack_layer = f.read()
    except Exception as e:
        console.print(f"[bold red]Error reading files:[/bold red] {e}")
        raise typer.Exit(code=1)
        
    # 3. Fuse content
    fused_content = f"""{intelligence_layer}

<context_pack name="{pack_name}">
{pack_layer}
</context_pack>
"""

    # 4. Save Export
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    export_filename = f"export_{pack_name}_{timestamp}.md"
    export_path = export_dir / export_filename
    
    try:
        with open(export_path, "w", encoding="utf-8") as f:
            f.write(fused_content)
    except Exception as e:
        console.print(f"[bold red]Error writing export file:[/bold red] {e}")
        raise typer.Exit(code=1)
        
    # 5. Clipboard Integration
    try:
        pyperclip.copy(fused_content)
        clipboard_status = "[green]Successfully copied to clipboard![/green]"
    except Exception as e:
        clipboard_status = "[yellow]Could not copy to clipboard. Ensure a display server/clipboard utility is running.[/yellow]"
        
    # 6. Success Output
    console.print(f"\n[bold green][OK][/bold green] Export Generation Complete!")
    console.print(f"  - [cyan]Intelligence:[/cyan] PROJECT_CONTEXT.md")
    console.print(f"  - [cyan]Context Pack:[/cyan] {pack_name}")
    console.print(f"  - [cyan]Local Export:[/cyan] {export_path.relative_to(root_dir)}")
    console.print(f"\n{clipboard_status}")
    console.print("\nYou can now paste the contents directly into Claude or ChatGPT.")
