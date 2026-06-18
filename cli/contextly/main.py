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

if __name__ == "__main__":
    try:
        app()
    except Exception as e:
        from .utils.exceptions import ConfigurationError
        if isinstance(e, ConfigurationError):
            console.print(f"[bold red]Fatal Error:[/bold red] {e}")
            import sys
            sys.exit(1)
        raise
