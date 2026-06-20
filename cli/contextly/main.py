import typer
from rich.console import Console

# Import commands (we will create these modules next)
from .commands import init, analyze, inspect, pack, discover, memory, learn, export, explain

app = typer.Typer(
    name="contextly",
    help="Context Intelligence Engine for LLMs",
    add_completion=False,
)

def version_callback(value: bool):
    if value:
        try:
            from importlib.metadata import version
            ver = version("contextly")
        except Exception:
            ver = "unknown"
        typer.echo(f"contextly version {ver}")
        raise typer.Exit()

@app.callback()
def common(
    version: bool = typer.Option(None, "--version", "-v", callback=version_callback, is_eager=True, help="Show version and exit.")
):
    pass

# Add commands
app.command(name="init", help="Initialize Context-as-Code in the current directory")(init.init_cmd)
app.command(name="analyze", help="Automatically analyze and map the repository")(analyze.analyze_cmd)
app.command(name="discover", help="Statically analyze the repository to discover conventions")(discover.discover_cmd)
app.command(name="learn", help="Teach Context-Ly new conventions (use --auto to discover)")(learn.learn_cmd)
app.command(name="memory", help="Inspect persistently stored team memory and conventions")(memory.memory_cmd)
app.command(name="pack", help="Bundle a directory into an LLM-ready Context Pack")(pack.pack_cmd)
app.command(name="export", help="Fuse intelligence and context packs into the clipboard")(export.export_cmd)
app.command(name="inspect", help="Deep dive into repository complexity and structure")(inspect.inspect_cmd)
app.command(name="explain", help="Explain repository concepts and structure")(explain.explain_cmd)

console = Console()

def main():
    try:
        app()
    except Exception as e:
        from .utils.exceptions import ConfigurationError
        import sys
        
        if isinstance(e, ConfigurationError):
            console.print(f"[bold red]Fatal Error:[/bold red] {e}")
            sys.exit(1)
        
        # Determine if we're in a completely unhandled crash scenario
        console.print(f"[bold red]CRASH REPORT[/bold red]: An unhandled exception occurred.")
        console.print(f"[red]Exception Type:[/red] {type(e).__name__}")
        console.print(f"[red]Message:[/red] {str(e)}")
        
        # Write full traceback to a secure log file instead of exposing
        # internal paths and dependency versions to stdout/CI logs.
        import traceback
        from pathlib import Path
        from datetime import datetime
        
        log_dir = Path.home() / ".contextly" / "logs"
        try:
            log_dir.mkdir(parents=True, exist_ok=True)
            crash_log = log_dir / "crash.log"
            with open(crash_log, "a", encoding="utf-8") as lf:
                lf.write(f"\n--- {datetime.now().isoformat()} ---\n")
                traceback.print_exc(file=lf)
            console.print(f"\n[dim]Full crash details written to: {crash_log}[/dim]")
        except OSError:
            # If we can't write the log file, fall back to showing the traceback
            console.print("\n[dim]--- Traceback ---[/dim]")
            traceback.print_exc()
            console.print("[dim]-------------------[/dim]\n")
        
        console.print("[yellow]Please report this issue to the Contextly maintainers.[/yellow]")
        sys.exit(1)

if __name__ == "__main__":
    main()
