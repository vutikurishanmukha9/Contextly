import os
import yaml
from pathlib import Path
from datetime import datetime
from ...types.models import ProjectMemory, MemoryRule

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
        data = memory.model_dump()
        with open(self.memory_file, "w", encoding="utf-8") as f:
            yaml.dump(data, f, default_flow_style=False, sort_keys=False)
            
    def load_memory(self) -> ProjectMemory:
        """Loads and validates the memory from YAML."""
        try:
            with open(self.memory_file, "r", encoding="utf-8") as f:
                data = yaml.safe_load(f)
                if not data:
                    return ProjectMemory()
                return ProjectMemory.model_validate(data)
        except Exception:
            return ProjectMemory()
            
    def add_rule(self, category: str, rule_text: str, confidence: str, source: str) -> bool:
        """Adds a rule to memory, avoiding exact duplicates."""
        memory = self.load_memory()
        
        # Deduplication check
        for rule in memory.rules:
            if rule.category == category and rule.rule == rule_text:
                return False # Already exists
                
        # Generate ID (simple hash or increment)
        rule_id = f"rule_{len(memory.rules) + 1:03d}"
        
        new_rule = MemoryRule(
            id=rule_id,
            category=category,
            rule=rule_text,
            confidence=confidence,
            source=source,
            created_at=datetime.now().strftime("%Y-%m-%d")
        )
        
        memory.rules.append(new_rule)
        self._save_memory(memory)
        return True
