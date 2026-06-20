from typing import TypedDict, Any, List
from abc import ABC, abstractmethod

from contextly.core.graph.builder import KnowledgeGraph
from contextly.core.diagnostics import DiagnosticsContext

class MetricOutput(TypedDict):
    """
    Stable JSON schema for metric outputs.
    """
    provider: str
    metric: str
    value: Any
    severity: str
    metadata: dict[str, Any]

class MetricsProvider(ABC):
    """
    Abstract base class for all pluggable metric providers.
    Providers should be read-only consumers of the KnowledgeGraph and DiagnosticsContext.
    """
    
    @property
    @abstractmethod
    def name(self) -> str:
        """Name of the provider, used for the JSON schema."""
        pass
        
    @abstractmethod
    def compute(self, graph: KnowledgeGraph, diagnostics: DiagnosticsContext) -> List[MetricOutput]:
        """
        Compute metrics and return a list of MetricOutput objects adhering to the stable schema.
        """
        pass
