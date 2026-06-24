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
    
    console.print(f"\n[bold]Blast Radius[/bold]\n")
    
    total_files = sum(len(impact[risk]["files"]) for risk in impact)
    if total_files == 0:
        console.print("[dim]No blast radius detected (no dependents found).[/dim]\n")
        raise typer.Exit(0)
        
    overall_risk = "LOW"
    for r in ["HIGH", "MEDIUM", "LOW"]:
        if impact[r]["files"]:
            overall_risk = r
            break
            
    domains = set()
    for risk in impact:
        for f in impact[risk]["files"]:
            try:
                rel = Path(f.path).relative_to(root_dir).as_posix()
                parts = rel.split('/')
                if len(parts) > 1:
                    if parts[0] in ('src', 'lib', 'app', 'packages') and len(parts) > 2:
                        domains.add(parts[1])
                    else:
                        domains.add(parts[0])
            except:
                pass
                
    critical = impact["HIGH"]["files"]
    if not critical:
        critical = impact["MEDIUM"]["files"]
        
    console.print(f"[bold]Files Affected:[/bold] {total_files}\n")
    
    if domains:
        console.print(f"[bold]Domains:[/bold]")
        for d in sorted(domains)[:10]:
            console.print(f"- {d}")
        if len(domains) > 10:
            console.print(f"- ... and {len(domains) - 10} more")
        console.print("")
        
    color = {"HIGH": "red", "MEDIUM": "yellow", "LOW": "green"}[overall_risk]
    console.print(f"[bold]Risk:[/bold]\n[{color}]{overall_risk}[/{color}]\n")
    
    if critical:
        console.print(f"[bold]Most Critical Dependents:[/bold]")
        for f in critical[:10]:
            try:
                rel = Path(f.path).relative_to(root_dir).name
            except ValueError:
                rel = f.name
            console.print(f"- {rel}")
        if len(critical) > 10:
            console.print(f"- ... and {len(critical) - 10} more")
        console.print("")
