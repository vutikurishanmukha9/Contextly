import sys
import typer
from pathlib import Path

# Import commands (we will create these modules next)
from contextly.commands import (
    init, analyze, discover, learn, memory,
    pack, export, inspect, explain, stats,
    impact, summary
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

# =======================================================================
# COMMAND FREEZE ENFORCEMENT
# Context-Ly operates on a philosophy of "Few Commands, High Intelligence".
# DO NOT add new commands to this file. Before proposing a new command,
# determine how the capability can be absorbed into the intelligence layer
# of an existing command (e.g. analyze, summary, impact).
# =======================================================================

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
app.command(name="impact", help="Analyze the blast radius of modifying a target file")(impact.impact_cmd)
app.command(name="summary", help="Generate a human-readable repository summary")(summary.summary_cmd)

def main():
    print("START")
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
                    
            import logging
            from logging.handlers import RotatingFileHandler
            logger = logging.getLogger("contextly_crash")
            logger.setLevel(logging.ERROR)
            logger.propagate = False
            for h in logger.handlers[:]:
                logger.removeHandler(h)
                
            handler = RotatingFileHandler(str(crash_log), maxBytes=100*1024, backupCount=2, encoding="utf-8")
            handler.setFormatter(logging.Formatter("\n--- %(asctime)s ---\n%(message)s"))
            logger.addHandler(handler)
            
            logger.error(traceback.format_exc())
            handler.flush()
            handler.close()
            console.print(f"\n[dim]Full crash details written to: {crash_log}[/dim]")
        except OSError:
            try:
                import tempfile
                with tempfile.NamedTemporaryFile(mode="a", prefix="contextly_crash_", suffix=".log", delete=False, encoding="utf-8") as lf:
                    lf.write(f"\n--- {datetime.now().isoformat()} ---\n")
                    traceback.print_exc(file=lf)
                    fallback_log_path = lf.name
                console.print(f"\n[dim]Full crash details written to temp log: {fallback_log_path}[/dim]")
            except OSError:
                # If we can't even write to temp, fall back to showing the traceback
                console.print("\n[dim]--- Traceback ---[/dim]")
                traceback.print_exc()
                console.print("[dim]-------------------[/dim]\n")
        
        console.print("[yellow]Please report this issue to the Contextly maintainers.[/yellow]")
        sys.exit(1)
    finally:
        # Centralize Diagnostic Reporting
        from contextly.core.diagnostics import DiagnosticsContext
        DiagnosticsContext().report()
        
        # Save command terminal transcript for commands that don't output a payload
        try:
            if len(sys.argv) > 1:
                cmd = sys.argv[1]
                raw_args = sys.argv[2:]
                
                # SEC-003: Sanitize arguments
                sanitized_args = []
                skip_next = False
                sensitive_flags = {"--api-key", "--token", "--password", "-p", "--secret"}
                for arg in raw_args:
                    if skip_next:
                        sanitized_args.append("********")
                        skip_next = False
                        continue
                    if arg in sensitive_flags:
                        sanitized_args.append(arg)
                        skip_next = True
                    elif any(arg.startswith(f"{flag}=") for flag in sensitive_flags):
                        flag = arg.split("=")[0]
                        sanitized_args.append(f"{flag}=********")
                    else:
                        sanitized_args.append(arg)
                args = sanitized_args
                
                # Exclude commands that manually save their own large payloads
                if cmd not in ("explain", "export", "pack", "--help", "-h", "--version", "-v"):
                    text = console.export_text(clear=False)
                    try:
                        root_dir = find_project_root(Path.cwd())
                        with open(root_dir / ".contextly" / "debug.log", "a") as f:
                            f.write(f"CMD: {cmd}, ARGV: {sys.argv}, TEXT LEN: {len(text)}, TEXT: {repr(text[:50])}\n")
                    except:
                        pass
                        
                    if text.strip():
                        if len(text) > 50000:
                            text = text[:50000] + "\n...[Truncated: Exceeded 50KB limit]..."
                        try:
                            # Might be outside a repo, fallback to cwd if so
                            root_dir = find_project_root(Path.cwd())
                        except Exception:
                            root_dir = Path.cwd()
                            
                        # Ensure secure permissions for exports
                        exports_dir = root_dir / ".contextly" / "exports"
                        exports_dir.mkdir(parents=True, exist_ok=True)
                        if sys.platform != "win32":
                            import os
                            os.chmod(exports_dir, 0o700)
                            
                        save_command_result(cmd, args, text, root_dir)
        except Exception as e:
            import traceback
            traceback.print_exc()

if __name__ == "__main__":
    main()
