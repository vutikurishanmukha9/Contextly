import typer
from pathlib import Path
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.columns import Columns

from ..utils.console import console
from ..utils.fs import find_project_root
from ..utils.validation import require_contextly_initialized
from ..utils.exceptions import ValidationError, ContextlyError
from ..core.graph.builder import ImportGraphBuilder
from ..core.graph.validator import GraphValidator
import collections

def summary_cmd():
    """Generate a human-readable repository summary"""
    root_dir = find_project_root(Path.cwd())
    
    try:
        require_contextly_initialized(root_dir)
    except (ValidationError, ContextlyError) as e:
        console.print(f"[bold red]Error:[/bold red] {e}")
        raise typer.Exit(1)
        
    status_ctx = console.status("[dim]Analyzing repository architecture...[/dim]")
    status_ctx.start()
    
    try:
        builder = ImportGraphBuilder(root_dir)
        graph = builder.build()
        validator = GraphValidator()
        graph = validator.validate(graph)
    except (ValidationError, ContextlyError) as e:
        status_ctx.stop()
        console.print(f"[bold red]Error:[/bold red] {e}")
        raise typer.Exit(1)
        
    status_ctx.stop()
    
    # 1. Compute in-degree and out-degree
    in_degree = collections.defaultdict(int)
    out_degree = collections.defaultdict(int)
    for edge in graph.relationships:
        out_degree[edge.source_id] += 1
        in_degree[edge.target_id] += 1
        
    # 2. Identify Entry Points and Core Hubs
    # Entry points: Nodes that import things, but are rarely imported themselves (in_degree == 0 or out_degree >> in_degree)
    # Plus common heuristics: main, index, cli, app
    entry_points = []
    core_hubs = []
    
    file_nodes = [n for n in graph.nodes if n.type.value == "FILE"]
    for node in file_nodes:
        # Hubs: High in_degree
        if in_degree[node.id] > 0:
            core_hubs.append((node, in_degree[node.id]))
            
        # Entry points: 0 in_degree but >0 out_degree, OR matches names
        path_lower = node.path.lower() if node.path else ""
        if (in_degree[node.id] == 0 and out_degree[node.id] > 0) or any(name in path_lower for name in ["main", "index", "cli", "app", "server"]):
            if in_degree[node.id] < 3: # Keep out generic utils that happen to be named "app_utils"
                entry_points.append(node)
                
    core_hubs.sort(key=lambda x: x[1], reverse=True)
    entry_points = list({n.id: n for n in entry_points}.values()) # deduplicate
    
    # 3. Identify Domains (Top-level directories in src or root)
    domains = set()
    for node in file_nodes:
        if not node.path: continue
        
        path_obj = Path(node.path)
        if path_obj.is_absolute():
            try:
                rel = path_obj.relative_to(root_dir)
            except ValueError:
                continue
        else:
            rel = path_obj
            
        parts = rel.parts
        if len(parts) > 1:
            # If it's in src or app, the domain is the next level
            if parts[0] in ("src", "app", "lib", "cli", "frontend", "backend"):
                if len(parts) > 2:
                    domains.add(f"{parts[0]}/{parts[1]}")
            else:
                domains.add(parts[0])
            
    # Print Summary
    console.print(f"\n[bold green]Repository Summary[/bold green] ({root_dir.name})\n")
    
    # Stats row
    total_files = len(file_nodes)
    total_funcs = len([n for n in graph.nodes if n.type.value == "FUNCTION"])
    total_classes = len([n for n in graph.nodes if n.type.value == "CLASS"])
    
    stats_table = Table(show_header=False, box=None)
    stats_table.add_row("[bold]Total Files:[/bold]", str(total_files))
    stats_table.add_row("[bold]Total Classes:[/bold]", str(total_classes))
    stats_table.add_row("[bold]Total Functions:[/bold]", str(total_funcs))
    console.print(Panel(stats_table, title="[cyan]Scale[/cyan]", border_style="cyan", expand=False))
    
    # Domains
    console.print("\n[bold]Primary Domains / Modules:[/bold]")
    for d in sorted(list(domains))[:15]:
        console.print(f"  - [cyan]{d}[/cyan]")
    if len(domains) > 15:
        console.print(f"  - ... and {len(domains) - 15} more")
        
    # Entry Points
    console.print("\n[bold]Likely Entry Points (Executable / Routes):[/bold]")
    for e in entry_points[:10]:
        try:
            rel = Path(e.path).relative_to(root_dir)
        except ValueError:
            rel = e.path
        console.print(f"  - {rel}")
        
    # Core Hubs
    console.print("\n[bold]Core Hubs (Most Depended-Upon Files):[/bold]")
    for h, deg in core_hubs[:10]:
        try:
            rel = Path(h.path).relative_to(root_dir)
        except ValueError:
            rel = h.path
        console.print(f"  - {rel} [dim]({deg} incoming imports)[/dim]")
    
    console.print("\n[dim]Hint: Run `contextly impact <file>` on a core hub to see its blast radius.[/dim]\n")
