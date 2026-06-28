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
        
        # Calculate graph density for logical entities (ignore FILES and CONTAINS edges)
        logical_nodes = [n for n in graph.nodes if n.type != NodeType.FILE]
        logical_edges = [r for r in graph.relationships if r.type != RelationshipType.CONTAINS]
        v = len(logical_nodes)
        e = len(logical_edges)
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
        
        BUILTIN_IGNORE = {
            "str", "int", "float", "bool", "len", "print", "list", "dict", "set", "tuple",
            "Exception", "ValueError", "TypeError", "super", "isinstance", "getattr", "setattr", "hasattr",
            "open", "type", "range", "enumerate", "zip", "map", "filter", "any", "all",
            "console", "console.log", "console.error", "console.warn", "String", "Number", 
            "Boolean", "Array", "Object", "Math", "JSON", "Promise", "Error", "window", "document"
        }
        
        unresolved = sum(1 for n in graph.nodes if n.type == NodeType.UNRESOLVED_EXTERNAL and n.name not in BUILTIN_IGNORE)
        
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
        
        # Use sets to count UNIQUE connections (prevent inflation from multiple calls)
        incoming_sets = defaultdict(set)
        outgoing_sets = defaultdict(set)
        
        for r in graph.relationships:
            if r.type in logical_edges:
                outgoing_sets[r.source_id].add(r.target_id)
                incoming_sets[r.target_id].add(r.source_id)
                
        incoming = {k: len(v) for k, v in incoming_sets.items()}
        outgoing = {k: len(v) for k, v in outgoing_sets.items()}
                
        BUILTIN_IGNORE = {
            "str", "int", "float", "bool", "len", "print", "list", "dict", "set", "tuple",
            "Exception", "ValueError", "TypeError", "super", "isinstance", "getattr", "setattr", "hasattr",
            "open", "type", "range", "enumerate", "zip", "map", "filter", "any", "all",
            "console", "console.log", "console.error", "console.warn", "String", "Number", 
            "Boolean", "Array", "Object", "Math", "JSON", "Promise", "Error", "window", "document"
        }
        
        # Get node id -> name mapping, excluding builtins
        node_names = {}
        for n in graph.nodes:
            if n.type == NodeType.UNRESOLVED_EXTERNAL and n.name in BUILTIN_IGNORE:
                continue
            node_names[n.id] = n.name
        
        # Most connected (incoming + outgoing)
        # Hub score = incoming * 2 + outgoing to weight incoming dependencies higher
        total_connections = {node_id: (incoming.get(node_id, 0) * 2) + outgoing.get(node_id, 0) for node_id in node_names.keys()}
        most_connected = sorted([(k, v) for k, v in total_connections.items() if v > 0], key=lambda x: x[1], reverse=True)
        
        # Most depended-on (incoming only)
        most_depended_on = sorted([(k, incoming.get(k, 0)) for k in node_names.keys() if incoming.get(k, 0) > 0], key=lambda x: x[1], reverse=True)
        
        return [
            MetricOutput(
                provider=self.name,
                metric="most_connected",
                value=[{"id": k, "name": node_names.get(k, k), "hub_score": v} for k, v in most_connected],
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
        BUILTIN_IGNORE = {
            "str", "int", "float", "bool", "len", "print", "list", "dict", "set", "tuple",
            "Exception", "ValueError", "TypeError", "super", "isinstance", "getattr", "setattr", "hasattr",
            "open", "type", "range", "enumerate", "zip", "map", "filter", "any", "all",
            "console", "console.log", "console.error", "console.warn", "String", "Number", 
            "Boolean", "Array", "Object", "Math", "JSON", "Promise", "Error", "window", "document"
        }
        unresolved = sum(1 for n in graph.nodes if n.type == NodeType.UNRESOLVED_EXTERNAL and n.name not in BUILTIN_IGNORE)
        
        # Penalties
        penalties = []
        
        if cycles_critical > 0:
            deduction = cycles_critical * 5.0
            score -= deduction
            penalties.append(f"-{deduction} points for {cycles_critical} critical circular dependencies")
            
        if cycles_warning > 0:
            deduction = cycles_warning * 2.0
            score -= deduction
            penalties.append(f"-{deduction} points for {cycles_warning} circular dependencies (warnings)")
        
        # Count strictly internal entities as denominator to avoid dilution by external libraries
        internal_entities_count = len([n for n in graph.nodes if n.type not in (NodeType.FILE, NodeType.UNRESOLVED_EXTERNAL)])
        
        # Penalize orphans proportionally (max 15 points)
        if internal_entities_count > 0 and orphans > 0:
            orphan_ratio = orphans / internal_entities_count
            deduction = min(15.0, orphan_ratio * 100.0)
            score -= deduction
            penalties.append(f"-{round(deduction, 1)} points for {orphans} potential orphans")
            
        # Penalize unresolved (max 10 points)
        if internal_entities_count > 0 and unresolved > 0:
            unresolved_ratio = unresolved / internal_entities_count
            deduction = min(10.0, unresolved_ratio * 50.0)
            score -= deduction
            penalties.append(f"-{round(deduction, 1)} points for {unresolved} unresolved external symbols")
            
        score = max(0.0, round(score, 1))
        
        return [
            MetricOutput(
                provider=self.name,
                metric="repository_health_score",
                value=score,
                severity="CRITICAL" if score < 60 else "WARNING" if score < 80 else "INFO",
                metadata={"max_score": 100, "penalties": penalties}
            )
        ]

class ModularityMetricsProvider(MetricsProvider):
    @property
    def name(self) -> str:
        return "Modularity"

    def compute(self, graph: KnowledgeGraph, diagnostics: DiagnosticsContext) -> List[MetricOutput]:
        from pathlib import Path
        
        # Calculate module coupling based on directory
        modules = defaultdict(lambda: {"in": set(), "out": set()})
        
        file_to_module = {}
        for n in graph.nodes:
            if n.type == NodeType.FILE:
                try:
                    path = Path(n.file_path)
                    module = path.parent.name if path.parent.name else "root"
                except:
                    module = "unknown"
                file_to_module[n.id] = module
        
        node_to_module = {}
        for r in graph.relationships:
            if r.type == RelationshipType.CONTAINS and r.source_id in file_to_module:
                node_to_module[r.target_id] = file_to_module[r.source_id]
                
        logical_edges = {RelationshipType.CALLS, RelationshipType.EXTENDS, RelationshipType.IMPLEMENTS, RelationshipType.USES}
        for r in graph.relationships:
            if r.type in logical_edges:
                src_mod = node_to_module.get(r.source_id)
                dst_mod = node_to_module.get(r.target_id)
                if src_mod and dst_mod and src_mod != dst_mod:
                    modules[src_mod]["out"].add(dst_mod)
                    modules[dst_mod]["in"].add(src_mod)
                    
        module_metrics = []
        for mod, data in modules.items():
            ca = len(data["in"])
            ce = len(data["out"])
            total = ca + ce
            instability = (ce / total) if total > 0 else 0.0
            module_metrics.append({
                "module": mod,
                "afferent": ca,
                "efferent": ce,
                "instability": round(instability, 2)
            })
            
        module_metrics = sorted(module_metrics, key=lambda x: x["instability"], reverse=True)
        
        return [
            MetricOutput(
                provider=self.name,
                metric="module_coupling",
                value=module_metrics,
                severity="INFO",
                metadata={"total_modules": len(module_metrics)}
            )
        ]

class MaintainabilityMetricsProvider(MetricsProvider):
    @property
    def name(self) -> str:
        return "Maintainability"

    def compute(self, graph: KnowledgeGraph, diagnostics: DiagnosticsContext) -> List[MetricOutput]:
        file_entities = defaultdict(int)
        functions = 0
        classes = 0
        
        for r in graph.relationships:
            if r.type == RelationshipType.CONTAINS:
                file_entities[r.source_id] += 1
                
        files = sum(1 for n in graph.nodes if n.type == NodeType.FILE)
        
        for n in graph.nodes:
            if n.type == NodeType.FUNCTION:
                functions += 1
            elif n.type == NodeType.CLASS:
                classes += 1
                
        avg_funcs = (functions / files) if files > 0 else 0
        avg_classes = (classes / files) if files > 0 else 0
        
        file_nodes = {n.id: n.name for n in graph.nodes if n.type == NodeType.FILE}
        
        fat_modules = []
        for file_id, count in sorted(file_entities.items(), key=lambda x: x[1], reverse=True)[:3]:
            fat_modules.append({
                "file": file_nodes.get(file_id, "unknown"),
                "entities": count
            })
            
        return [
            MetricOutput(
                provider=self.name,
                metric="component_density",
                value={"avg_functions": round(avg_funcs, 1), "avg_classes": round(avg_classes, 1)},
                severity="INFO",
                metadata={}
            ),
            MetricOutput(
                provider=self.name,
                metric="fat_modules",
                value=fat_modules,
                severity="WARNING" if any(m["entities"] > 20 for m in fat_modules) else "INFO",
                metadata={}
            )
        ]
