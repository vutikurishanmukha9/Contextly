from typing import Dict, Type, Any
from .base import BaseScanner
from .language import LanguageScanner
from .dependencies import DependencyScanner
from .framework import FrameworkScanner
from .patterns import PatternScanner
from .architecture import ArchitectureScanner
from .capabilities import CapabilityDetector

class ScannerRegistry:
    """
    Registry for repository scanners.
    Manages the order of execution and dynamically resolves dependencies between scanners.
    """
    _registry: Dict[str, Type[BaseScanner]] = {}
    _order: list[str] = []

    @classmethod
    def register(cls, key: str, scanner_class: Type[BaseScanner]) -> None:
        if key not in cls._registry:
            cls._order.append(key)
        cls._registry[key] = scanner_class

    @classmethod
    def register_defaults(cls) -> None:
        """Register defaults in strict dependency order."""
        cls.register('language', LanguageScanner)
        cls.register('dependencies', DependencyScanner)
        cls.register('frameworks', FrameworkScanner)
        cls.register('patterns', PatternScanner)
        cls.register('architecture', ArchitectureScanner)
        cls.register('capabilities', CapabilityDetector)

    @classmethod
    def execute_pipeline(cls, root_dir, file_paths, ast_graph=None, domains=None) -> Dict[str, Any]:
        """
        Executes all registered scanners in order, passing accumulated results
        forward to satisfy scanner dependencies.
        """
        results = {}
        for key in cls._order:
            scanner = cls._registry[key]()
            
            # Dynamically build kwargs based on what scanners expect
            kwargs = {
                'file_paths': file_paths,
                'ast_graph': ast_graph,
                'domains': domains
            }
            
            if key == 'frameworks':
                kwargs['deps'] = results.get('dependencies')
            elif key == 'patterns':
                kwargs['dependencies'] = results.get('dependencies')
                
            results[key] = scanner.scan(root_dir, **kwargs)
                
        return results

# Auto-register defaults on module load
ScannerRegistry.register_defaults()
