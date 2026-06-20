from __future__ import annotations
import uuid
import yaml
from pathlib import Path
from datetime import datetime, timezone
from ...types.models import ProjectMemory, MemoryRule
from ...utils.console import console
from ...utils.exceptions import MemoryVaultError, MemoryVaultCorruptionError
from contextlib import contextmanager
import time

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

    @contextmanager
    def _lock(self):
        """Cross-platform atomic locking using filelock."""
        from filelock import FileLock, Timeout
        lock_file = self.memory_dir / "rules.lock"
        try:
            with FileLock(lock_file, timeout=5):
                yield
        except Timeout:
            raise MemoryVaultError("Could not acquire memory lock after 5 seconds. Vault is deadlocked.")
            
    def _save_memory(self, memory: ProjectMemory):
        """Serializes the ProjectMemory model to YAML and writes it atomically."""
        try:
            from ...utils.io import atomic_write
            data = memory.model_dump()
            yaml_str = yaml.dump(data, default_flow_style=False, sort_keys=False)
            atomic_write(self.memory_file, yaml_str)
        except Exception as e:
            raise MemoryVaultError(f"Failed to save memory rules: {e}")
            
    def load_memory(self) -> ProjectMemory:
        """Loads and validates the memory from YAML."""
        try:
            with open(self.memory_file, "r", encoding="utf-8") as f:
                data = yaml.safe_load(f)
                if not data:
                    return ProjectMemory()
                if not isinstance(data, dict):
                    console.print("[yellow]Warning: Memory file is corrupt (not a mapping). Falling back to empty memory.[/yellow]")
                    return ProjectMemory()
                return ProjectMemory.model_validate(data)
        except (yaml.YAMLError, ValueError) as e:
            raise MemoryVaultCorruptionError(f"Memory file is corrupt ({e}).") from e
        except Exception as e:
            import pydantic
            if isinstance(e, pydantic.ValidationError):
                raise MemoryVaultCorruptionError(f"Memory file validation failed ({e}).") from e
            # Allow OS/IO errors to propagate and abort operations to prevent data destruction
            raise
            
    def add_rule(self, category: str, rule_text: str, confidence: float, source: str, name: str | None = None) -> bool:
        """Adds a rule to memory, avoiding exact duplicates."""
        with self._lock():
            memory = self.load_memory()
            
            # Upsert logic: deduplicate or update
            for rule in memory.rules:
                if rule.category != category:
                    continue
                
                if name and rule.name == name:
                    if rule.rule != rule_text:
                        # Update existing rule content
                        rule.rule = rule_text
                        rule.confidence = confidence
                        rule.source = source
                        rule.created_at = datetime.now(timezone.utc).isoformat()
                        self._save_memory(memory)
                        return True
                    return False
                    
                if rule.rule == rule_text:
                    # If existing rule has no name, but the new one does, "upgrade" it by adding the name.
                    if name and not rule.name:
                        rule.name = name
                        rule.confidence = max(rule.confidence, confidence)
                        rule.source = source
                        rule.created_at = datetime.now(timezone.utc).isoformat()
                        self._save_memory(memory)
                        return True
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
                created_at=datetime.now(timezone.utc).isoformat()
            )
            
            memory.rules.append(new_rule)
            self._save_memory(memory)
            return True
