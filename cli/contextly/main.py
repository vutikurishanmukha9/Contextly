import sys
import typer
from pathlib import Path

# Import commands (we will create these modules next)
from contextly.commands import (
    init, analyze, discover, learn, memory,
    pack, export, inspect, explain, stats
)
from contextly.utils.io import save_command_result
from contextly.utils.fs import find_project_root
from contextly.utils.console import console

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
app.command(name="stats", help="Generate an enterprise repository health report")(stats.stats_cmd)

def main():
    try:
        app()
    except Exception as e:
        from .utils.exceptions import ConfigurationError
        
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
        import os
        from datetime import datetime
        
        if sys.platform == "win32":
            base_dir = Path(os.environ.get("LOCALAPPDATA", Path.home() / "AppData" / "Local"))
        else:
            base_dir = Path(os.environ.get("XDG_STATE_HOME", Path.home() / ".local" / "state"))
            
        log_dir = base_dir / "contextly" / "logs"
        
        try:
            log_dir.mkdir(parents=True, exist_ok=True)
            if sys.platform != "win32":
                os.chmod(log_dir, 0o700)
            
            crash_log = log_dir / "crash.log"
            if not crash_log.exists():
                if sys.platform != "win32":
                    crash_log.touch(mode=0o600)
                else:
                    crash_log.touch()
            else:
                if sys.platform != "win32":
                    os.chmod(crash_log, 0o600)
                
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
    finally:
        # Save command terminal transcript for commands that don't output a payload
        try:
            if len(sys.argv) > 1:
                cmd = sys.argv[1]
                args = sys.argv[2:]
                
                # Exclude commands that manually save their own large payloads
                if cmd not in ("explain", "export", "--help", "-h", "--version", "-v"):
                    text = console.export_text(clear=False)
                    if text.strip():
                        try:
                            # Might be outside a repo, fallback to cwd if so
                            root_dir = find_project_root(Path.cwd())
                        except Exception:
                            root_dir = Path.cwd()
                            
                        save_command_result(cmd, args, text, root_dir)
        except Exception as e:
            import traceback
            traceback.print_exc()
        
if __name__ == "__main__":
    main()
