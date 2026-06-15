import uuid
import yaml
from pathlib import Path
from datetime import datetime
from ...types.models import ProjectMemory, MemoryRule
from ...utils.console import console
from ...utils.exceptions import MemoryVaultError

class MemoryEngine:
    """Manages the persistence of learned team conventions and architecture hints."""
    
    def __init__(self, root_dir: Path):
        self.root_dir = root_dir
        self.memory_dir = root_dir / ".contextly" / "memory"
        self.memory_file = self.memory_dir / "rules.yaml"
        self._ensure_setup()
        
    def _ensure_setup(self):
        """Ensures the memory directory and file exist."""
        if not self.memory_dir.exists():
            self.memory_dir.mkdir(parents=True, exist_ok=True)
            
        if not self.memory_file.exists():
            self._save_memory(ProjectMemory())
            
    def _save_memory(self, memory: ProjectMemory):
        """Serializes the ProjectMemory model to YAML."""
        try:
            data = memory.model_dump()
            with open(self.memory_file, "w", encoding="utf-8") as f:
                yaml.dump(data, f, default_flow_style=False, sort_keys=False)
        except (OSError, PermissionError) as e:
            raise MemoryVaultError(f"Failed to save memory rules: {e}")
            
    def load_memory(self) -> ProjectMemory:
        """Loads and validates the memory from YAML."""
        try:
            with open(self.memory_file, "r", encoding="utf-8") as f:
                data = yaml.safe_load(f)
                if not data:
                    return ProjectMemory()
                return ProjectMemory.model_validate(data)
        except Exception as e:
            console.print(f"[yellow]Warning: Failed to load memory ({e}). Falling back to empty memory.[/yellow]")
            return ProjectMemory()
            
    def add_rule(self, category: str, rule_text: str, confidence: float, source: str, name: str | None = None) -> bool:
        """Adds a rule to memory, avoiding exact duplicates."""
        memory = self.load_memory()
        
        # Deduplication check
        for rule in memory.rules:
            if rule.category != category:
                continue
            # If name is provided and matches, or fallback to exact description match
            if name and rule.name == name:
                return False
            if rule.name is None and rule.rule == rule_text:
                return False
                
        # Generate ID (unique hash snippet)
        rule_id = f"rule_{uuid.uuid4().hex[:8]}"
        
        new_rule = MemoryRule(
            id=rule_id,
            name=name,
            category=category,
            rule=rule_text,
            confidence=confidence,
            source=source,
            created_at=datetime.utcnow().isoformat() + "Z"
        )
        
        memory.rules.append(new_rule)
        self._save_memory(memory)
        return True
