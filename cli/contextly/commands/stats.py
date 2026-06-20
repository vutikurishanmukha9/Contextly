import time
import json
import tracemalloc
from typing import List, Optional
from pathlib import Path
import typer
from rich.console import Console
from rich.table import Table
from rich.panel import Panel

from contextly.core.graph.builder import ImportGraphBuilder
from contextly.core.graph.validator import GraphValidator
from contextly.core.metrics import (
    GraphTopologyProvider,
    ResolutionQualityProvider,
    ValidationMetricsProvider,
    ComplexityMetricsProvider,
    HealthScoreProvider,
)
from contextly.core.diagnostics import DiagnosticsContext
from contextly.utils.console import console

def stats_cmd(
    path: str = typer.Option(".", "--path", "-p", help="Path to the repository to analyze"),
    as_json: bool = typer.Option(False, "--json", help="Output the stats as a stable JSON schema"),
    ignore: List[str] = typer.Option(None, "--ignore", "-i", help="Additional paths or patterns to ignore"),
    top: int = typer.Option(3, "--top", help="Number of hotspots to show"),
):
    """
    Generate an enterprise repository health report.
    """
    diagnostics = DiagnosticsContext()
    diagnostics.clear()

    if not as_json:
        console.print("[dim]Analyzing repository health...[/dim]")

    tracemalloc.start()
    start_time = time.time()

    # 1. Build Graph (Pass 1 & 2)
    builder = ImportGraphBuilder(Path(path))
    graph = builder.build()

    # 2. Validate Graph (Pass 3)
    validator = GraphValidator()
    graph = validator.validate(graph)

    end_time = time.time()
    _, peak_memory = tracemalloc.get_traced_memory()
    tracemalloc.stop()

    execution_time = end_time - start_time
    peak_memory_mb = peak_memory / (1024 * 1024)

    # 3. Compute Metrics
    providers = [
        GraphTopologyProvider(),
        ResolutionQualityProvider(),
        ValidationMetricsProvider(),
        ComplexityMetricsProvider(),
        HealthScoreProvider()
    ]

    all_metrics = []
    for provider in providers:
        all_metrics.extend(provider.compute(graph, diagnostics))

    # 4. Output
    if as_json:
        # Inject performance metrics into JSON
        all_metrics.append({
            "provider": "Performance",
            "metric": "execution_time_seconds",
            "value": round(execution_time, 2),
            "severity": "INFO",
            "metadata": {}
        })
        all_metrics.append({
            "provider": "Performance",
            "metric": "peak_memory_mb",
            "value": round(peak_memory_mb, 2),
            "severity": "INFO",
            "metadata": {}
        })
        typer.echo(json.dumps(all_metrics, indent=2))
        return

    # Render Rich Report
    _render_rich_report(path, all_metrics, execution_time, peak_memory_mb, top)


def _render_rich_report(path: str, metrics: List[dict], time_sec: float, mem_mb: float, top: int):
    # Find specific metrics
    def get_metric(name: str):
        return next((m for m in metrics if m["metric"] == name), None)

    score_metric = get_metric("repository_health_score")
    score = score_metric["value"] if score_metric else 100

    # Determine score color
    score_color = "red" if score < 60 else "yellow" if score < 80 else "green"

    console.print(Panel(
        f"[bold]Contextly Repository Health Report:[/bold] {path}",
        expand=False,
        border_style="blue"
    ))

    console.print(f"\n[bold {score_color}][ Repository Health Score: {score}/100 ][/bold {score_color}]")

    console.print("\n[bold cyan][ Performance ][/bold cyan]")
    console.print(f"• Execution Time:       {time_sec:.2f}s")
    console.print(f"• Peak Memory:          {mem_mb:.2f}MB")

    # Topology
    topology = [m for m in metrics if m["provider"] == "Topology"]
    if topology:
        console.print("\n[bold cyan][ Graph Topology ][/bold cyan]")
        files = get_metric("files_analyzed")
        entities = get_metric("entities_discovered")
        edges = get_metric("total_edges")
        density = get_metric("graph_density")
        
        console.print(f"• Files Analyzed:       {files['value']}")
        # Format entity classes breakdown
        type_str = ", ".join(f"{k}: {v}" for k, v in entities["metadata"].get("type_counts", {}).items())
        console.print(f"• Entities Discovered:  {entities['value']} ({type_str})")
        console.print(f"• Total Edges:          {edges['value']}")
        console.print(f"• Graph Density:        {density['value']} ({density['metadata'].get('label', '')})")

    # Resolution Quality
    resolution = [m for m in metrics if m["provider"] == "Resolution"]
    if resolution:
        console.print("\n[bold cyan][ Resolution Quality ][/bold cyan]")
        high = get_metric("high_confidence_edges")
        medium = get_metric("medium_confidence_edges")
        low = get_metric("low_confidence_edges")
        
        console.print(f"• High Confidence:      {high['value']:.1f}% (Exact Match / Imported Symbol)")
        console.print(f"• Medium Confidence:    {medium['value']:.1f}% (Fuzzy Match / Suffix Match)")
        console.print(f"• Low Confidence:       {low['value']:.1f}%  (Unresolved / External)")

    # Complexity
    complexity = [m for m in metrics if m["provider"] == "Complexity"]
    if complexity:
        console.print(f"\n[bold cyan][ Architectural Hotspots (Top {top}) ][/bold cyan]")
        connected = get_metric("most_connected")
        depended = get_metric("most_depended_on")
        
        console.print("• Most Connected:")
        for idx, item in enumerate(connected["value"][:top]):
            console.print(f"  {idx+1}. {item['name']:<20} ({item['edges']} edges)")
            
        console.print("• Most Depended-On (Choke Points):")
        for idx, item in enumerate(depended["value"][:top]):
            console.print(f"  {idx+1}. {item['name']:<20} ({item['incoming_edges']} incoming edges)")

    # Validation
    console.print("\n[bold cyan][ Diagnostics & Quality Gate ][/bold cyan]")
    
    crit_cycles = get_metric("circular_dependencies_critical")["value"]
    warn_cycles = get_metric("circular_dependencies_warning")["value"]
    orphans = get_metric("potential_orphans")["value"]
    unresolved = get_metric("unresolved_symbols")["value"]

    if crit_cycles > 0:
        console.print("[bold red][ CRITICAL ][/bold red]")
        console.print(f"• Circular Dependencies: {crit_cycles}")
        
    warnings = []
    if warn_cycles > 0:
        warnings.append(f"Circular Dependencies: {warn_cycles}")
    if orphans > 0:
        warnings.append(f"Potential Orphans:    {orphans} (May be indirectly used e.g., @app.get)")
        
    if warnings:
        console.print("[bold yellow][ WARNING ][/bold yellow]")
        for w in warnings:
            console.print(f"• {w}")

    if unresolved > 0:
        console.print("[bold blue][ INFO ][/bold blue]")
        console.print(f"• Unresolved Symbols:   {unresolved} (External library calls)")

    console.print("")
