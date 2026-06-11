import typer
from rich.console import Console

# Import commands (we will create these modules next)
from .commands import init, analyze, inspect, pack, discover, memory, learn

app = typer.Typer(
    name="contextly",
    help="Context Intelligence Engine for LLMs",
    add_completion=False,
)

# Add commands
app.command(name="init", help="Initialize Context-as-Code in the current directory")(init.init_cmd)
app.command(name="analyze", help="Automatically analyze and map the repository")(analyze.analyze_cmd)
app.command(name="discover", help="Statically analyze the repository to discover conventions")(discover.discover_cmd)
app.command(name="learn", help="Teach Context-Ly new conventions (use --auto to discover)")(learn.learn_cmd)
app.command(name="memory", help="Inspect persistently stored team memory and conventions")(memory.memory_cmd)
app.command(name="inspect", help="Deep dive into repository complexity and structure")(inspect.inspect_cmd)
app.command(name="pack", help="Bundle a directory into an LLM-ready Context Pack")(pack.pack_cmd)

console = Console()

if __name__ == "__main__":
    app()
