import yaml
from pathlib import Path
from ...utils.exceptions import ContextlyError

class InitEngine:
    def __init__(self, root_dir: Path):
        self.root_dir = root_dir

    def initialize(self) -> bool:
        """
        Initializes Contextly config.
        Returns True if initialized successfully, False if already initialized.
        Raises ContextlyError on IO errors.
        """
        target_dir = self.root_dir / ".contextly"
        config_path = target_dir / "config.yaml"
        
        if target_dir.is_file():
            raise ContextlyError("Cannot initialize Context-Ly: a file named '.contextly' already exists")
            
        if config_path.exists():
            return False
            
        try:
            target_dir.mkdir(parents=True, exist_ok=True)
            (target_dir / "memory").mkdir(exist_ok=True)
            (target_dir / "packs").mkdir(exist_ok=True)
            
            config = {
                "project": {
                    "name": self.root_dir.name,
                },
                "depth_limits": {
                    "analyzer": 6,
                    "generator_tree": 4,
                    "scanners": 4,
                    "discovery": 4
                },
                "packer": {
                    "max_file_size_mb": 5
                },
                "stack": {
                    "frontend": "",
                    "backend": ""
                },
                "profiles": {
                    "frontend": ["src/components", "src/pages"],
                    "backend": ["src/api", "src/models"]
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
            with open(config_path, "w", encoding="utf-8") as f:
                yaml.dump(config, f, default_flow_style=False, sort_keys=False)
                
            ignore_path = self.root_dir / ".contextlyignore"
            if not ignore_path.exists():
                with open(ignore_path, "w", encoding="utf-8") as f:
                    f.write("""# Context-Ly Ignore File
# Add directories and file patterns to exclude from context packing.

# Dependencies
node_modules/
venv/
env/
.venv/
__pycache__/

# Build and Dist
dist/
build/
out/
.next/

# IDEs
.idea/
.vscode/

# Media and Binaries
*.png
*.jpg
*.jpeg
*.gif
*.ico
*.pdf
*.zip
*.tar.gz
""")
                
            return True
        except (OSError, PermissionError) as e:
            raise ContextlyError(f"Failed to initialize Contextly: {str(e)}")
