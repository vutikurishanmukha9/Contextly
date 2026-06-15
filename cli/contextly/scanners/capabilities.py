from pathlib import Path
from typing import List, Optional

from .base import BaseScanner, ScannerError
from ..types.models import RepositoryCapability
from ..core.discovery.engine import DiscoveryEngine
from ..core.discovery.registry import Registry

class CapabilityDetector(BaseScanner):
    """
    Capability Detector.
    Delegates heuristic detection to the generic Discovery Engine.
    """
    
    @property
    def name(self) -> str:
        return "Capability Detector"

    def scan(self, root_dir: Path, file_paths: Optional[List[str]] = None, **kwargs) -> List[RepositoryCapability]:
        try:
            engine = DiscoveryEngine(root_dir)
            
            capabilities = engine.evaluate_registry(
                registry=Registry.CAPABILITIES,
                discovery_class=RepositoryCapability,
                source_name="CapabilityDetector",
                file_paths=file_paths
            )

            return capabilities

        except Exception as e:
            raise ScannerError(f"Capability scan failed: {str(e)}")
