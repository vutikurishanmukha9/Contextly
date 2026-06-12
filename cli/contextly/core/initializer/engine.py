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
        
        if target_dir.exists():
            return False
            
        try:
            target_dir.mkdir(parents=True)
            (target_dir / "memory").mkdir()
            (target_dir / "packs").mkdir()
            
            config = {
                "project": {
                    "name": self.root_dir.name,
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
            with open(config_path, "w", encoding="utf-8") as f:
                yaml.dump(config, f, default_flow_style=False, sort_keys=False)
                
            return True
        except (OSError, PermissionError) as e:
            raise ContextlyError(f"Failed to initialize Contextly: {str(e)}")
