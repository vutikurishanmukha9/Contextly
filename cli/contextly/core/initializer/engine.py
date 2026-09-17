import yaml
from pathlib import Path
from ...utils.exceptions import ContextlyError

class InitEngine:
    def __init__(self, root_dir: Path):
        self.root_dir = root_dir

    def detect_stack(self) -> dict:
        """Detects languages, frameworks, and directories in the repository."""
        detected = {"languages": [], "frameworks": [], "profiles": {}}
        
        # Languages & frameworks
        if (self.root_dir / "pyproject.toml").exists() or (self.root_dir / "requirements.txt").exists():
            detected["languages"].append("Python")
        if (self.root_dir / "package.json").exists():
            detected["languages"].append("TypeScript/JavaScript")
            try:
                pkg_text = (self.root_dir / "package.json").read_text(encoding="utf-8")
                if "react" in pkg_text:
                    detected["frameworks"].append("React")
                if "next" in pkg_text:
                    detected["frameworks"].append("Next.js")
                if "vite" in pkg_text:
                    detected["frameworks"].append("Vite")
            except Exception:
                pass
        if (self.root_dir / "Cargo.toml").exists():
            detected["languages"].append("Rust")
        if (self.root_dir / "go.mod").exists():
            detected["languages"].append("Go")
            
        # Discover existing directory profiles
        profiles = {}
        candidate_dirs = {
            "frontend": ["frontend", "client", "ui", "web"],
            "backend": ["backend", "server", "api", "cli"],
            "core": ["src", "lib", "core", "pkg"],
            "tests": ["tests", "test", "__tests__", "spec"]
        }
        for profile_name, options in candidate_dirs.items():
            for opt in options:
                p = self.root_dir / opt
                if p.exists() and p.is_dir():
                    profiles[profile_name] = [opt]
                    break
                    
        if not profiles:
            profiles = {
                "frontend": ["src/components", "src/pages"],
                "backend": ["src/api", "src/models"]
            }
        detected["profiles"] = profiles
        return detected

    def initialize(self, force: bool = False) -> bool:
        """
        Initializes Contextly config.
        Returns True if initialized successfully, False if already initialized.
        Raises ContextlyError on IO errors.
        """
        target_dir = self.root_dir / ".contextly"
        config_path = target_dir / "config.yaml"
        
        if target_dir.is_file():
            raise ContextlyError("Cannot initialize Context-Ly: a file named '.contextly' already exists")
            
        if config_path.exists() and not force:
            return False
            
        try:
            target_dir.mkdir(parents=True, exist_ok=True)
            (target_dir / "memory").mkdir(exist_ok=True)
            (target_dir / "packs").mkdir(exist_ok=True)
            
            detected = self.detect_stack()
            
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
                    "languages": detected["languages"],
                    "frameworks": detected["frameworks"]
                },
                "profiles": detected["profiles"],
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
