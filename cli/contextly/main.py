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

# =======================================================================
# 5 POWERHOUSE COMMANDS CONSOLIDATION
# Context-Ly operates on a philosophy of "Few Commands, High Intelligence".
# The CLI exposes 5 core powerhouse commands. Legacy commands are preserved
# as hidden aliases for seamless backward compatibility.
# =======================================================================

# 5 Core Powerhouse Commands
app.command(name="init", help="Initialize Context-as-Code with auto-detected stack profiles")(init.init_cmd)
app.command(name="analyze", help="Analyze architecture, health scorecard, hubs, and complexity")(analyze.analyze_cmd)
app.command(name="pack", help="Bundle, optimize, and fuse repository context for instant LLM export")(pack.pack_cmd)
app.command(name="impact", help="Analyze blast radius of modifying a target file or explain domain architecture")(impact.impact_cmd)
app.command(name="memory", help="Inspect, learn, and discover persistently stored team conventions")(memory.memory_cmd)

# Legacy Commands (Preserved as Hidden Aliases for 100% Backward Compatibility)
app.command(name="export", hidden=True, help="Alias: Fuse intelligence and context packs into the clipboard")(export.export_cmd)
app.command(name="explain", hidden=True, help="Alias: Explain repository concepts and structure")(explain.explain_cmd)
app.command(name="stats", hidden=True, help="Alias: Generate an enterprise repository health report")(stats.stats_cmd)
app.command(name="summary", hidden=True, help="Alias: Generate a human-readable repository summary")(summary.summary_cmd)
app.command(name="inspect", hidden=True, help="Alias: Deep dive into repository complexity and structure")(inspect.inspect_cmd)
app.command(name="learn", hidden=True, help="Alias: Teach Context-Ly new conventions")(learn.learn_cmd)
app.command(name="discover", hidden=True, help="Alias: Statically analyze the repository to discover conventions")(discover.discover_cmd)

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
                        debug_log = root_dir / ".contextly" / "debug.log"
                        with open(debug_log, "a", encoding="utf-8") as f:
                            f.write(f"CMD: {cmd}, ARGV: {args}, TEXT LEN: {len(text)}, TEXT: {repr(text[:50])}\n")
                        if sys.platform != "win32":
                            os.chmod(debug_log, 0o600)
                    except OSError:
                        # Debug logging must never change a command's result.
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
        except Exception:
            # Transcript persistence is best-effort; do not leak command details on failure.
            pass

if __name__ == "__main__":
    main()
