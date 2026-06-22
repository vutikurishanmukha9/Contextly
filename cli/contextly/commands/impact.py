import typer
from pathlib import Path
from rich.table import Table
from rich.panel import Panel

from ..utils.console import console
from ..utils.fs import find_project_root
from ..utils.validation import require_contextly_initialized
from ..core.graph.builder import ImportGraphBuilder
from ..core.graph.validator import GraphValidator
from ..core.impact.engine import ImpactEngine

def impact_cmd(
    target: str = typer.Argument(..., help="Target file or entity to analyze blast radius for"),
):
    """Analyze the blast radius of modifying a target file"""
    root_dir = find_project_root(Path.cwd())
    
    try:
        require_contextly_initialized(root_dir)
    except Exception as e:
        console.print(f"[bold red]Error:[/bold red] {e}")
        raise typer.Exit(1)
        
    status_ctx = console.status("[dim]Building graph and calculating blast radius...[/dim]")
    status_ctx.start()
    
    try:
        builder = ImportGraphBuilder(root_dir)
        graph = builder.build()
        validator = GraphValidator()
        graph = validator.validate(graph)
        
        engine = ImpactEngine(graph)
        impact = engine.analyze_impact(target)
        
    except Exception as e:
        status_ctx.stop()
        console.print(f"[bold red]Error:[/bold red] {e}")
        raise typer.Exit(1)
        
    status_ctx.stop()
    
    console.print(f"\n[bold]Change Impact Analysis (Blast Radius)[/bold]")
    console.print(f"Target: [cyan]{target}[/cyan]\n")
    
    for risk, color in [("HIGH", "red"), ("MEDIUM", "yellow"), ("LOW", "green")]:
        files = impact[risk]["files"]
        entities = impact[risk]["entities"]
        
        if files or entities:
            console.print(f"[bold {color}]Risk Level: {risk}[/bold {color}]")
            
            if files:
                console.print(f"  [dim]Affected Files:[/dim]")
                for f in files[:10]:
                    try:
                        rel = Path(f.path).relative_to(root_dir).as_posix()
                    except ValueError:
                        rel = f.path
                    console.print(f"    - {rel}")
                if len(files) > 10:
                    console.print(f"    - ... and {len(files) - 10} more files")
                    
            if entities:
                console.print(f"  [dim]Affected Entities:[/dim]")
                for e in entities[:10]:
                    console.print(f"    - {e.name} ({e.type.value})")
                if len(entities) > 10:
                    console.print(f"    - ... and {len(entities) - 10} more entities")
            console.print("")
