import yaml
from pathlib import Path
from typing import Dict, Any, Optional, List
from pydantic import BaseModel, Field, model_validator

class ProjectConfig(BaseModel):
    name: str = ""

class DepthLimitsConfig(BaseModel):
    analyzer: int = 6
    generator_tree: int = 4
    max_tree_breadth: int = 50
    scanners: int = 4
    discovery: int = 4

class PackerConfig(BaseModel):
    max_file_size_mb: float = 5.0

class StackConfig(BaseModel):
    frontend: str = ""
    backend: str = ""

class AIConfig(BaseModel):
    preferredModel: str = "claude"

class ContextlyConfig(BaseModel):
    project: ProjectConfig = Field(default_factory=ProjectConfig)
    depth_limits: DepthLimitsConfig = Field(default_factory=DepthLimitsConfig)
    packer: PackerConfig = Field(default_factory=PackerConfig)
    stack: StackConfig = Field(default_factory=StackConfig)
    profiles: Dict[str, List[str]] = Field(default_factory=dict)
    rules: List[str] = Field(default_factory=list)
    ai: AIConfig = Field(default_factory=AIConfig)

    @model_validator(mode="before")
    @classmethod
    def pre_validate(cls, values: Any) -> Any:
        if not isinstance(values, dict):
            return {}
        cleaned = {}
        for k, v in values.items():
            if v is None:
                if k == "rules":
                    cleaned[k] = []
                else:
                    cleaned[k] = {}
            else:
                cleaned[k] = v
        return cleaned

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

def load_config_model(root_dir: Path) -> ContextlyConfig:
    """Loads and validates the .contextly/config.yaml file into ContextlyConfig."""
    config_path = root_dir / ".contextly" / "config.yaml"
    if not config_path.exists():
        return ContextlyConfig()
    try:
        with open(config_path, "r", encoding="utf-8") as f:
            data = yaml.safe_load(f)
            if not isinstance(data, dict):
                return ContextlyConfig()
            return ContextlyConfig.model_validate(data)
    except Exception as e:
        import pydantic
        if isinstance(e, pydantic.ValidationError):
            try:
                from .console import console
                console.print(f"[red]Configuration Error in .contextly/config.yaml:[/red]\n{e}")
            except Exception:
                pass
            import sys
            sys.exit(1)
        return ContextlyConfig()
