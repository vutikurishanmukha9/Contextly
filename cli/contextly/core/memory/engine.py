import uuid
import yaml
from pathlib import Path
from datetime import datetime, timezone
from ...types.models import ProjectMemory, MemoryRule
from ...utils.console import console
from ...utils.exceptions import MemoryVaultError
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
        """Cross-platform directory-based locking mechanism."""
        lock_dir = self.memory_dir / "rules.lock"
        attempts = 0
        while attempts < 50:
            try:
                lock_dir.mkdir()
                break
            except FileExistsError:
                try:
                    # Check for stale lock (older than 10 seconds)
                    if lock_dir.stat().st_mtime < time.time() - 10:
                        lock_dir.rmdir()
                        continue
                except OSError:
                    pass
                time.sleep(0.1)
                attempts += 1
        else:
            console.print("[yellow]Warning: Could not acquire memory lock, proceeding anyway.[/yellow]")
            
        try:
            yield
        finally:
            try:
                lock_dir.rmdir()
            except OSError:
                pass
            
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
                if not isinstance(data, dict):
                    console.print("[yellow]Warning: Memory file is corrupt (not a mapping). Falling back to empty memory.[/yellow]")
                    return ProjectMemory()
                return ProjectMemory.model_validate(data)
        except Exception as e:
            console.print(f"[yellow]Warning: Failed to load memory ({e}). Falling back to empty memory.[/yellow]")
            return ProjectMemory()
            
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
