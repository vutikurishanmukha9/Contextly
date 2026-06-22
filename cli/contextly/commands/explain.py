import typer
from pathlib import Path
from rich.console import Console
from rich.markdown import Markdown
from typing import Optional

from contextly.core.explainer.engine import ExplainerEngine
from contextly.utils.fs import find_project_root
from contextly.utils.io import save_command_result
import pyperclip

console = Console()
app = typer.Typer(help="Explain repository architectural domains.")

def explain_cmd(
    domain: str = typer.Argument(..., help="The domain name to explain (e.g. 'auth', 'payment')."),
    path: str = typer.Option(".", "--path", "-p", help="Path to the repository")
):
    """
    Generate an offline Domain Context Payload containing the isolated architecture of a specific domain.
    The generated context is copied directly to your clipboard to provide to an AI tool.
    Requires 'contextly analyze' to have been run first.
    """
    root_dir = find_project_root(Path(path).resolve())
        
    engine = ExplainerEngine(root_dir=root_dir)
    
    try:
        prompt = engine.explain(domain)
        try:
            out_file = save_command_result("explain", [domain], prompt, root_dir)
            console.print(f"[bold green][OK][/bold green] [bold]Context payload saved to: {out_file}[/bold]")
            
            try:
                pyperclip.copy(prompt)
                console.print("[yellow]Notice: Proprietary source architecture has also been copied to your OS clipboard. Clear it when finished if on a shared/synced device.[/yellow]")
            except Exception as e:
                console.print(f"[yellow]Warning: Could not copy to clipboard. ({e})[/yellow]")
                
        except Exception as e:
            console.print(f"[red]Error saving result: {e}[/red]")
            console.print("Here is the context payload you can copy manually:")
            console.print("="*40)
            console.print(prompt)
            console.print("="*40)
            
    except FileNotFoundError as e:
        console.print(f"[red]Error: {str(e)}[/red]")
        raise typer.Exit(1)
    except ValueError as e:
        console.print(f"[red]Error: {str(e)}[/red]")
        raise typer.Exit(1)
    except Exception as e:
        console.print(f"[red]An unexpected error occurred: {str(e)}[/red]")
        raise typer.Exit(1)
