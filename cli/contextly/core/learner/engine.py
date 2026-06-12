from pathlib import Path
from typing import List
from ...core.memory.engine import MemoryEngine
from ...core.discovery.engine import DiscoveryEngine
from ...types.models import Pattern

class LearnEngine:
    def __init__(self, root_dir: Path):
        self.root_dir = root_dir
        self.memory_engine = MemoryEngine(root_dir)
        self.discovery_engine = DiscoveryEngine(root_dir)

    def discover_conventions(self) -> List[Pattern]:
        """Discovers patterns and returns them sorted by confidence."""
        patterns_result = self.discovery_engine.discover()
        
        if not patterns_result.patterns:
            return []
            
        # Sort by confidence
        sorted_patterns = sorted(
            patterns_result.patterns,
            key=lambda p: {"high": 0, "medium": 1, "low": 2}.get(p.confidence.lower(), 3)
        )
        return sorted_patterns

    def save_convention(self, pattern: Pattern) -> bool:
        """Saves a single convention to memory. Returns True if saved, False if already existed."""
        return self.memory_engine.add_rule(
            category=pattern.category,
            rule_text=pattern.description,
            confidence=pattern.confidence,
            source=pattern.source
        )
