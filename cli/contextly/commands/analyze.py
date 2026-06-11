import time
from pathlib import Path
import concurrent.futures
from rich.table import Table
from ..utils.console import console

from ..scanners.dependencies import DependencyScanner
from ..scanners.language import LanguageScanner
from ..scanners.framework import FrameworkScanner
from ..scanners.patterns import PatternScanner
from ..scanners.base import ScannerError
from ..types.models import RepositoryIntelligence
from ..utils.memory import MemoryEngine

from ..generators.context import ContextGenerator

def analyze_cmd():
    """Automatically analyze and map the repository"""
    root_dir = Path.cwd()
    
    with console.status("[bold blue]Scanning repository intelligence (Max Level)...", spinner="dots"):
        # We will use ThreadPoolExecutor to run the IO-bound dependency and language scanners concurrently
        lang_scanner = LanguageScanner()
        dep_scanner = DependencyScanner()
        fw_scanner = FrameworkScanner()
        pat_scanner = PatternScanner()
        
        try:
            # Running sequentially instead of concurrently due to GIL limitations 
            # and to prevent disk thrashing on mechanical drives during rglob
            lang_data = lang_scanner.scan(root_dir)
            dep_data = dep_scanner.scan(root_dir)
                
            # Framework and Pattern scanners depend on dependencies being resolved first
            fw_data = fw_scanner.scan(root_dir, deps=dep_data)
            pat_data = pat_scanner.scan(root_dir, dependencies=dep_data)
            
            # Aggregate into the strict Pydantic model
            engine = MemoryEngine(root_dir)
            memory_data = engine.load_memory()
            
            intelligence = RepositoryIntelligence(
                language=lang_data,
                dependencies=dep_data,
                frameworks=fw_data,
                patterns=pat_data,
                memory=memory_data
            )
        except ScannerError as e:
            console.print(f"\n[bold red]Scanner Error:[/bold red] {e}")
            return
        except Exception as e:
            console.print(f"\n[bold red]Unexpected Error:[/bold red] {e}")
            return
            
    console.print("\n[bold green][OK][/bold green] Repository scan complete!\n")
    
    # Build output table
    table = Table(title="Repository Intelligence (Max Level)", show_header=False, box=None)
    table.add_column("Category", style="cyan", justify="right")
    table.add_column("Value", style="magenta")
    
    table.add_row("Primary Language", f"[bold]{intelligence.language.primary}[/bold]")
    table.add_row("Frontend Framework", intelligence.frameworks.frontend)
    table.add_row("Backend/Tooling", intelligence.frameworks.backend)
    
    npm_count = len(intelligence.dependencies.npm)
    py_count = len(intelligence.dependencies.python)
    
    if npm_count > 0:
        table.add_row("NPM Dependencies", str(npm_count))
    if py_count > 0:
        table.add_row("Python Dependencies", str(py_count))
        
    console.print(table)
    console.print()
    
    # Generate Advanced PROJECT_CONTEXT.md
    generator = ContextGenerator(root_dir, intelligence)
    ctx_content = generator.generate()
    
    try:
        with open("PROJECT_CONTEXT.md", "w", encoding="utf-8") as f:
            f.write(ctx_content)
        console.print("[dim]Generated advanced PROJECT_CONTEXT.md in current directory.[/dim]")
    except (FileNotFoundError, PermissionError) as e:
        console.print(f"[red]Failed to write PROJECT_CONTEXT.md: {e}[/red]")
