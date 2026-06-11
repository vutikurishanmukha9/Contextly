import os
import yaml
from pathlib import Path
from ..utils.console import console

def init_cmd():
    """Initialize Context-as-Code in the current directory"""
    target_dir = Path.cwd() / ".contextly"
    
    if target_dir.exists():
        console.print("[yellow]Contextly is already initialized in this repository.[/yellow]")
        return
        
    try:
        # Create directories
        target_dir.mkdir(parents=True)
        (target_dir / "memory").mkdir()
        (target_dir / "packs").mkdir()
        
        # Create default config.yaml
        config = {
            "project": {
                "name": Path.cwd().name,
            },
            "stack": {
                "frontend": "",
                "backend": ""
            },
            "rules": [
                "add your coding standards here",
                "e.g., typescript-only",
                "e.g., no-any"
            ],
            "ai": {
                "preferredModel": "claude"
            }
        }
        
        config_path = target_dir / "config.yaml"
        with open(config_path, "w") as f:
            yaml.dump(config, f, default_flow_style=False, sort_keys=False)
            
        console.print("[bold green][OK][/bold green] Contextly initialized successfully!")
        console.print(f"Created configuration at [cyan].contextly/config.yaml[/cyan]")
        console.print("Edit this file to define your Context-as-Code rules.")
        
    except Exception as e:
        console.print(f"[bold red]Error initializing Contextly:[/bold red] {str(e)}")
