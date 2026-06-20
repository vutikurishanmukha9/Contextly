from typing import List, Dict, Any
from collections import defaultdict

from contextly.core.graph.builder import KnowledgeGraph
from contextly.core.diagnostics import DiagnosticsContext
from contextly.types.models import NodeType, RelationshipType
from contextly.core.metrics.base import MetricsProvider, MetricOutput

class GraphTopologyProvider(MetricsProvider):
    @property
    def name(self) -> str:
        return "Topology"

    def compute(self, graph: KnowledgeGraph, diagnostics: DiagnosticsContext) -> List[MetricOutput]:
        files_count = sum(1 for n in graph.nodes if n.type == NodeType.FILE)
        entities_count = len(graph.nodes) - files_count
        
        type_counts = defaultdict(int)
        for n in graph.nodes:
            if n.type != NodeType.FILE:
                type_counts[n.type.value] += 1
                
        edge_counts = defaultdict(int)
        for r in graph.relationships:
            edge_counts[r.type.value] += 1
            
        total_edges = len(graph.relationships)
        
        # Calculate graph density for logical entities (ignore FILES and CONTAINS edges if possible)
        # We'll calculate simple density V and E
        v = len(graph.nodes)
        e = len(graph.relationships)
        density = e / (v * (v - 1)) if v > 1 else 0.0
        
        # Determine density label
        if density < 0.05:
            label = "Low"
        elif density < 0.2:
            label = "Moderate"
        else:
            label = "High"

        return [
            MetricOutput(
                provider=self.name,
                metric="files_analyzed",
                value=files_count,
                severity="INFO",
                metadata={}
            ),
            MetricOutput(
                provider=self.name,
                metric="entities_discovered",
                value=entities_count,
                severity="INFO",
                metadata={"type_counts": dict(type_counts)}
            ),
            MetricOutput(
                provider=self.name,
                metric="total_edges",
                value=total_edges,
                severity="INFO",
                metadata={"edge_counts": dict(edge_counts)}
            ),
            MetricOutput(
                provider=self.name,
                metric="graph_density",
                value=round(density, 4),
                severity="INFO",
                metadata={"label": label}
            )
        ]

class ResolutionQualityProvider(MetricsProvider):
    @property
    def name(self) -> str:
        return "Resolution"

    def compute(self, graph: KnowledgeGraph, diagnostics: DiagnosticsContext) -> List[MetricOutput]:
        high, medium, low = 0, 0, 0
        total = len(graph.relationships)
        
        for r in graph.relationships:
            if r.confidence >= 0.9:
                high += 1
            elif r.confidence >= 0.4:
                medium += 1
            else:
                low += 1
                
        high_pct = (high / total * 100) if total > 0 else 0
        medium_pct = (medium / total * 100) if total > 0 else 0
        low_pct = (low / total * 100) if total > 0 else 0
        
        return [
            MetricOutput(
                provider=self.name,
                metric="high_confidence_edges",
                value=high_pct,
                severity="INFO",
                metadata={"count": high}
            ),
            MetricOutput(
                provider=self.name,
                metric="medium_confidence_edges",
                value=medium_pct,
                severity="INFO",
                metadata={"count": medium}
            ),
            MetricOutput(
                provider=self.name,
                metric="low_confidence_edges",
                value=low_pct,
                severity="INFO",
                metadata={"count": low}
            )
        ]

class ValidationMetricsProvider(MetricsProvider):
    @property
    def name(self) -> str:
        return "Validation"

    def compute(self, graph: KnowledgeGraph, diagnostics: DiagnosticsContext) -> List[MetricOutput]:
        messages = diagnostics.get_messages()
        cycles_critical = sum(1 for m in messages if "Circular dependency" in m.message and m.severity == "ERROR")
        cycles_warning = sum(1 for m in messages if "Circular dependency" in m.message and m.severity == "WARNING")
        cycles_info = sum(1 for m in messages if "Circular dependency" in m.message and m.severity == "INFO")
        
        orphans = sum(1 for m in messages if "Orphaned Entity" in m.message)
        
        unresolved = sum(1 for n in graph.nodes if n.type == NodeType.UNRESOLVED_EXTERNAL)
        
        return [
            MetricOutput(
                provider=self.name,
                metric="circular_dependencies_critical",
                value=cycles_critical,
                severity="CRITICAL" if cycles_critical > 0 else "INFO",
                metadata={}
            ),
            MetricOutput(
                provider=self.name,
                metric="circular_dependencies_warning",
                value=cycles_warning,
                severity="WARNING" if cycles_warning > 0 else "INFO",
                metadata={}
            ),
            MetricOutput(
                provider=self.name,
                metric="circular_dependencies_info",
                value=cycles_info,
                severity="INFO",
                metadata={}
            ),
            MetricOutput(
                provider=self.name,
                metric="potential_orphans",
                value=orphans,
                severity="WARNING" if orphans > 0 else "INFO",
                metadata={}
            ),
            MetricOutput(
                provider=self.name,
                metric="unresolved_symbols",
                value=unresolved,
                severity="INFO",
                metadata={}
            )
        ]

class ComplexityMetricsProvider(MetricsProvider):
    @property
    def name(self) -> str:
        return "Complexity"

    def compute(self, graph: KnowledgeGraph, diagnostics: DiagnosticsContext) -> List[MetricOutput]:
        # Exclude CONTAINS and IMPORTS for true logical complexity
        logical_edges = {RelationshipType.CALLS, RelationshipType.EXTENDS, RelationshipType.IMPLEMENTS, RelationshipType.RETURNS, RelationshipType.USES}
        
        incoming = defaultdict(int)
        outgoing = defaultdict(int)
        
        for r in graph.relationships:
            if r.type in logical_edges:
                outgoing[r.source_id] += 1
                incoming[r.target_id] += 1
                
        # Get node id -> name mapping
        node_names = {n.id: n.name for n in graph.nodes}
        
        # Most connected (incoming + outgoing)
        total_connections = {node_id: incoming[node_id] + outgoing[node_id] for node_id in node_names.keys()}
        most_connected = sorted(total_connections.items(), key=lambda x: x[1], reverse=True)
        
        # Most depended-on (incoming only)
        most_depended_on = sorted(incoming.items(), key=lambda x: x[1], reverse=True)
        
        return [
            MetricOutput(
                provider=self.name,
                metric="most_connected",
                value=[{"id": k, "name": node_names.get(k, k), "edges": v} for k, v in most_connected],
                severity="INFO",
                metadata={}
            ),
            MetricOutput(
                provider=self.name,
                metric="most_depended_on",
                value=[{"id": k, "name": node_names.get(k, k), "incoming_edges": v} for k, v in most_depended_on],
                severity="INFO",
                metadata={}
            )
        ]

class HealthScoreProvider(MetricsProvider):
    @property
    def name(self) -> str:
        return "Health"

    def compute(self, graph: KnowledgeGraph, diagnostics: DiagnosticsContext) -> List[MetricOutput]:
        # Start with a perfect 100
        score = 100.0
        
        messages = diagnostics.get_messages()
        cycles_critical = sum(1 for m in messages if "Circular dependency" in m.message and m.severity == "ERROR")
        cycles_warning = sum(1 for m in messages if "Circular dependency" in m.message and m.severity == "WARNING")
        orphans = sum(1 for m in messages if "Orphaned Entity" in m.message)
        unresolved = sum(1 for n in graph.nodes if n.type == NodeType.UNRESOLVED_EXTERNAL)
        
        # Penalties
        score -= (cycles_critical * 5.0)
        score -= (cycles_warning * 2.0)
        
        # Penalize orphans proportionally (max 15 points)
        entities_count = len([n for n in graph.nodes if n.type != NodeType.FILE])
        if entities_count > 0:
            orphan_ratio = orphans / entities_count
            score -= min(15.0, orphan_ratio * 100.0)
            
        # Penalize unresolved (max 10 points)
        if entities_count > 0:
            unresolved_ratio = unresolved / entities_count
            score -= min(10.0, unresolved_ratio * 50.0)
            
        score = max(0.0, round(score, 1))
        
        return [
            MetricOutput(
                provider=self.name,
                metric="repository_health_score",
                value=score,
                severity="CRITICAL" if score < 60 else "WARNING" if score < 80 else "INFO",
                metadata={"max_score": 100}
            )
        ]
