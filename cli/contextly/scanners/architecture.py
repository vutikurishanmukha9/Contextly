from pathlib import Path
from typing import List, Optional

from .base import BaseScanner, ScannerError
from ..types.models import ArchitectureKnowledge, Discovery
from ..core.discovery.engine import DiscoveryEngine
from ..core.discovery.registry import Registry

class ArchitectureScanner(BaseScanner):
    """
    Architecture Scanner. 
    Delegates pattern and layer detection to the Discovery Engine and Registry rules.
    """
    
    @property
    def name(self) -> str:
        return "Architecture Scanner"

    def scan(self, root_dir: Path, file_paths: Optional[List[str]] = None, ast_graph=None, domains=None, **kwargs) -> ArchitectureKnowledge:
        try:
            engine = DiscoveryEngine(root_dir)
            
            # Evaluate Architecture Patterns
            candidates = engine.evaluate_registry(
                registry=Registry.ARCHITECTURE_PATTERNS,
                discovery_class=Discovery,
                source_name="ArchitectureScanner",
                file_paths=file_paths
            )
            
            # Evaluate Architecture Layers
            layers = engine.evaluate_registry(
                registry=Registry.ARCHITECTURE_LAYERS,
                discovery_class=Discovery,
                source_name="ArchitectureScanner",
                file_paths=file_paths
            )

            # Advanced Domain-based Detection
            if domains and len(domains) > 1:
                significant_domains = [d.name for d in domains if len(d.node_ids) > 3 and d.name != "root"]
                
                if len(significant_domains) > 2:
                    candidates.insert(0, Discovery(
                        name="Modular Architecture",
                        confidence=0.9,
                        evidence=[f"Detected {len(significant_domains)} significant structural domains via AST clustering ({', '.join(significant_domains[:3])})."],
                        generated_by="ArchitectureScanner"
                    ))
                    
                if any("api" in d.name.lower() for d in domains) and any("core" in d.name.lower() for d in domains):
                    candidates.insert(0, Discovery(
                        name="Clean Architecture",
                        confidence=0.85,
                        evidence=["Detected distinct 'api' and 'core' layer boundaries."],
                        generated_by="ArchitectureScanner"
                    ))

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
