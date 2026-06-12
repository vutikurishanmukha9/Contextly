import yaml
from pathlib import Path
from typing import Dict, Any, Optional

def load_config(root_dir: Path) -> Optional[Dict[str, Any]]:
    """Loads the .contextly/config.yaml file if it exists."""
    config_path = root_dir / ".contextly" / "config.yaml"
    if not config_path.exists():
        return None
        
    try:
        with open(config_path, "r", encoding="utf-8") as f:
            return yaml.safe_load(f)
    except Exception:
        return None
