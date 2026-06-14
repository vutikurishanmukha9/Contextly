from pathlib import Path
from typing import List

from .base import BaseScanner, ScannerError
from ..types.models import ArchitectureKnowledge, Discovery
from ..core.discovery.engine import DiscoveryEngine
from ..core.discovery.registry import Registry

class ArchitectureScanner(BaseScanner):
    """
    Enterprise-grade Architecture Scanner. 
    Delegates pattern and layer detection to the Discovery Engine and Registry rules.
    """
    
    @property
    def name(self) -> str:
        return "Architecture Scanner"

    def scan(self, root_dir: Path, **kwargs) -> ArchitectureKnowledge:
        try:
            engine = DiscoveryEngine(root_dir)
            
            # Evaluate Architecture Patterns
            candidates = engine.evaluate_registry(
                registry=Registry.ARCHITECTURE_PATTERNS,
                discovery_class=Discovery,
                source_name="ArchitectureScanner"
            )
            
            # Evaluate Architecture Layers
            layers = engine.evaluate_registry(
                registry=Registry.ARCHITECTURE_LAYERS,
                discovery_class=Discovery,
                source_name="ArchitectureScanner"
            )

            # Fallback handling
            if not candidates:
                candidates.append(Discovery(
                    name="Monolith",
                    confidence=0.1,
                    evidence=["Default fallback"],
                    generated_by="ArchitectureScanner"
                ))
            
            primary = candidates[0]

            return ArchitectureKnowledge(
                primary_pattern=primary,
                pattern_candidates=candidates,
                layers=layers
            )

        except Exception as e:
            raise ScannerError(f"Architecture scan failed: {str(e)}")
