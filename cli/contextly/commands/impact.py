import os
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
from ..core.explainer.engine import ExplainerEngine
from ..utils.io import save_command_result
import pyperclip

def impact_cmd(
    target: str = typer.Argument(..., help="Target file or entity to analyze blast radius for, or domain name to explain"),
    explain: bool = typer.Option(False, "--explain", "-e", help="Generate an offline domain context payload for an AI tool"),
    visual: bool = typer.Option(False, "--visual", "-v", help="Display visual cascade tree diagram of affected dependents"),
    no_clipboard: bool = typer.Option(False, "--no-clipboard", help="Skip copying context to clipboard in explain mode")
):
    """Analyze the blast radius of modifying a target file, or explain domain architecture"""
    root_dir = find_project_root(Path.cwd())
    
    try:
        require_contextly_initialized(root_dir)
    except Exception as e:
        console.print(f"[bold red]Error:[/bold red] {e}")
        raise typer.Exit(1)

    if explain:
        engine = ExplainerEngine(root_dir=root_dir)
        try:
            prompt = engine.explain(target)
            out_file = save_command_result("explain", [target], prompt, root_dir)
            console.print(f"[bold green][OK][/bold green] [bold]Context payload saved to: {out_file}[/bold]")
            if not no_clipboard and not os.environ.get("CI"):
                try:
                    pyperclip.copy(prompt)
                    console.print("[yellow]Notice: Proprietary source architecture has also been copied to your OS clipboard. Clear it when finished if on a shared/synced device.[/yellow]")
                except Exception as e:
                    console.print(f"[yellow]Warning: Could not copy to clipboard. ({e})[/yellow]")
            return
        except Exception as e:
            console.print(f"[bold red]Error explaining domain '{target}':[/bold red] {e}")
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
    
    if visual:
        tree = engine.generate_visual_tree(target, impact)
        console.print(Panel(tree, title="[bold]Blast Radius Dependency Cascade[/bold]", border_style="cyan"))
        console.print()
    
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
