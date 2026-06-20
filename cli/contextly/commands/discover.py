from pathlib import Path
import typer

from ..utils.console import console
from ..core.discovery.engine import DiscoveryEngine
from ..scanners.base import ScannerError
from ..utils.exceptions import ValidationError, ContextlyError
from ..utils.fs import find_project_root
from ..utils.validation import require_contextly_initialized

def discover_cmd(
    output_format: str = typer.Option("text", "--format", help="Output format ('text' or 'json')")
):
    """Auto-discover technical patterns and update knowledge base"""
    root_dir = find_project_root(Path.cwd())
    
    try:
        require_contextly_initialized(root_dir)
    except ValidationError as e:
        if output_format == "json":
            import json
            console.print(json.dumps({"error": str(e)}, indent=2))
        else:
            console.print(f"[bold red]Error:[/bold red] {e}")
        raise typer.Exit(code=1)
        
    engine = DiscoveryEngine(root_dir)
        
    if output_format != "json":
        status_ctx = console.status("[bold blue]Running Pattern Discovery Engine...", spinner="dots")
        status_ctx.start()
        
    try:
        patterns_result = engine.discover()
    except ScannerError as e:
        if output_format != "json":
            status_ctx.stop()
            console.print(f"\n[bold red]Scanner Error:[/bold red] {e}")
        else:
            import json
            console.print(json.dumps({"error": f"Scanner Error: {str(e)}"}, indent=2))
        raise typer.Exit(code=1)
    except ContextlyError as e:
        if output_format != "json":
            status_ctx.stop()
            console.print(f"\n[bold red]Context-Ly Error:[/bold red] {e}")
        else:
            import json
            console.print(json.dumps({"error": f"Context-Ly Error: {str(e)}"}, indent=2))
        raise typer.Exit(code=1)
    except Exception as e:
        if output_format != "json":
            status_ctx.stop()
            console.print(f"\n[bold red]Error:[/bold red] {e}")
        else:
            import json
            console.print(json.dumps({"error": str(e)}, indent=2))
        raise typer.Exit(code=1)
        
    if output_format != "json":
        status_ctx.stop()
        console.print("[bold green][OK][/bold green] Pattern Discovery Complete:\n")
        
        if not patterns_result.patterns:
            console.print("[yellow]No recognizable architectural patterns or conventions discovered.[/yellow]")
            return

        # Group by category
        categories = {}
        for p in patterns_result.patterns:
            if p.category not in categories:
                categories[p.category] = []
            categories[p.category].append(p)
            
        for category, patterns in sorted(categories.items()):
            console.print(f"[bold cyan]{category}:[/bold cyan]")
            # Sort by confidence descending
            sorted_patterns = sorted(patterns, key=lambda p: p.confidence, reverse=True)
            for p in sorted_patterns:
                conf_str = "High" if p.confidence >= 0.9 else "Medium" if p.confidence >= 0.7 else "Low"
                console.print(f"  [green]\\[OK][/green] [bold]{p.name}[/bold] ({conf_str} Confidence) - {p.description}")
            console.print()
    else:
        import json
        console.print(json.dumps([
            {
                "name": p.name,
                "category": p.category,
                "confidence": p.confidence,
                "description": p.description,
                "evidence": p.evidence
            } for p in patterns_result.patterns
        ], indent=2))
