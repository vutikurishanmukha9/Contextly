import json
from pathlib import Path
from rich.table import Table
import typer

from ..utils.console import console
from ..scanners.base import ScannerError
from ..utils.exceptions import ContextlyError
from ..utils.fs import find_project_root
from ..utils.validation import require_directory_exists, require_contextly_initialized
from ..core.analyzer.engine import AnalyzerEngine
from ..utils.exceptions import ValidationError

def analyze_cmd(
    target: str = typer.Argument(".", help="Directory to analyze"),
    model: str = typer.Option("chatgpt", "--model", "-m", help="Target LLM format ('chatgpt' or 'claude')"),
    no_default_excludes: bool = typer.Option(False, "--no-default-excludes", help="Do not exclude default skip lists (like node_modules, dist, etc.)"),
    output_format: str = typer.Option("text", "--format", help="Output format ('text' or 'json')")
):
    """Analyze a repository and print intelligence summary"""
    root_dir = find_project_root(Path.cwd())
    
    try:
        require_contextly_initialized(root_dir)
        target_path = Path(target).resolve(strict=False)
        try:
            target_path.relative_to(root_dir)
        except (ValueError, RuntimeError, OSError):
            raise ValidationError("Target directory must be inside the project root directory.")
        if not target_path.exists() or not target_path.is_dir():
            raise ValidationError(f"Target is not a valid directory: {target}")
    except ValidationError as e:
        if output_format == "json":
            console.print(json.dumps({"error": str(e)}, indent=2))
        else:
            console.print(f"\n[bold red]Error:[/bold red] {e}")
        raise typer.Exit(1)
        
    try:
        engine = AnalyzerEngine(root_dir, no_default_excludes=no_default_excludes)
        
        intelligence = engine.analyze(model)
        
    except ScannerError as e:
        if output_format != "json":
            console.print(f"\n[bold red]Scanner Error:[/bold red] {e}")
        else:
            print(json.dumps({"error": f"Scanner Error: {str(e)}"}, indent=2))
        raise typer.Exit(1)
    except ContextlyError as e:
        if output_format != "json":
            console.print(f"\n[bold red]Context-Ly Error:[/bold red] {e}")
        else:
            print(json.dumps({"error": f"Context-Ly Error: {str(e)}"}, indent=2))
        raise typer.Exit(1)
    except Exception as e:
        if output_format != "json":
            console.print(f"\n[bold red]Unexpected Error:[/bold red] {e}")
        else:
            print(json.dumps({"error": f"Unexpected Error: {str(e)}"}, indent=2))
        raise typer.Exit(1)
        
    if output_format != "json":
        console.print("\n[bold green][OK][/bold green] Repository scan complete!\n")
        
        table = Table(title="Repository Intelligence", show_header=False, box=None)
        table.add_column("Category", style="cyan", justify="right")
        table.add_column("Value", style="magenta")
        
        table.add_row("Primary Language", f"[bold]{intelligence.language.primary}[/bold]")
        table.add_row("Frontend Framework", ", ".join(intelligence.frameworks.frontend) if intelligence.frameworks.frontend else "None detected")
        table.add_row("Backend/Tooling", ", ".join(intelligence.frameworks.backend) if intelligence.frameworks.backend else "None detected")
        
        npm_count = len(intelligence.dependencies.npm)
        py_count = len(intelligence.dependencies.python)
        
        if npm_count > 0:
            table.add_row("NPM Dependencies", str(npm_count))
        if py_count > 0:
            table.add_row("Python Dependencies", str(py_count))
            
        console.print(table)
        console.print()
        console.print(f"[dim]Generated advanced PROJECT_CONTEXT.md ({model.lower()} format) in current directory.[/dim]")
    else:
        console.print(json.dumps({
            "language": intelligence.language.primary,
            "frameworks": {
                "frontend": intelligence.frameworks.frontend,
                "backend": intelligence.frameworks.backend
            },
            "dependencies": {
                "npm_count": len(intelligence.dependencies.npm),
                "python_count": len(intelligence.dependencies.python)
            },
            "output_file": f"PROJECT_CONTEXT.md"
        }, indent=2))

