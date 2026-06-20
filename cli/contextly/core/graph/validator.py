from typing import Dict, List, Set
from collections import defaultdict

from ...types.models import KnowledgeGraph, RelationshipType, NodeType
from ..diagnostics import DiagnosticsContext

class GraphValidator:
    """
    Enterprise-grade Graph Validator.
    Acts as a quality gate (Pass 3) before Graph metrics/finalization.
    Detects integrity issues, orphans, duplicates, and cycles.
    """
    
    def __init__(self):
        self.diagnostics = DiagnosticsContext()
        
    def validate(self, graph: KnowledgeGraph) -> KnowledgeGraph:
        """Runs all validations and returns the cleaned graph."""
        self._check_integrity(graph)
        self._detect_duplicates(graph)
        self._detect_orphans(graph)
        self._detect_cycles(graph)
        return graph
        
    def _check_integrity(self, graph: KnowledgeGraph):
        """Ensures no relationships point to non-existent nodes. Drops dead edges."""
        node_ids = {n.id for n in graph.nodes}
        valid_edges = []
        
        for rel in graph.relationships:
            if rel.source_id not in node_ids:
                self.diagnostics.add_warning("GraphValidator", f"Dead edge: source {rel.source_id} does not exist.")
                continue
            if rel.target_id not in node_ids:
                self.diagnostics.add_warning("GraphValidator", f"Dead edge: target {rel.target_id} does not exist.")
                continue
            valid_edges.append(rel)
            
        graph.relationships = valid_edges

    def _detect_duplicates(self, graph: KnowledgeGraph):
        """Detects duplicate entities by checking FQN metadata."""
        fqns: Dict[str, List[str]] = defaultdict(list)
        for node in graph.nodes:
            fqn = node.metadata.get("fqn")
            if fqn:
                fqns[fqn].append(node.id)
                
        for fqn, ids in fqns.items():
            if len(ids) > 1:
                self.diagnostics.add_warning("GraphValidator", f"Duplicate FQN detected: {fqn} registered {len(ids)} times.")

    def _detect_orphans(self, graph: KnowledgeGraph):
        """Finds entity nodes that have no incoming or outgoing logical edges (dead code candidates)."""
        # Exclude CONTAINS and FILE imports from logical linkage
        logical_edges = {RelationshipType.CALLS, RelationshipType.USES, RelationshipType.EXTENDS, RelationshipType.IMPLEMENTS, RelationshipType.RETURNS}
        
        connected_nodes: Set[str] = set()
        for rel in graph.relationships:
            if rel.type in logical_edges:
                connected_nodes.add(rel.source_id)
                connected_nodes.add(rel.target_id)
                
        for node in graph.nodes:
            # We only care if functions/classes are orphaned
            if node.type in {NodeType.CLASS, NodeType.FUNCTION, NodeType.INTERFACE}:
                if node.id not in connected_nodes:
                    self.diagnostics.add_info("GraphValidator", f"Orphaned Entity detected (no logical links): {node.name}")

    def _detect_cycles(self, graph: KnowledgeGraph):
        """Detects cyclic dependencies in the graph and reports by severity."""
        # Build adjacency list for CALLS and IMPORTS separately
        calls_adj = defaultdict(list)
        imports_adj = defaultdict(list)
        
        for rel in graph.relationships:
            if rel.type == RelationshipType.CALLS:
                calls_adj[rel.source_id].append(rel.target_id)
            elif rel.type == RelationshipType.IMPORTS:
                imports_adj[rel.source_id].append(rel.target_id)
                
        self._find_cycles(calls_adj, "CALLS", "WARNING")
        self._find_cycles(imports_adj, "IMPORTS", "INFO")
        
    def _find_cycles(self, adj: Dict[str, List[str]], cycle_type: str, severity: str):
        visited = set()
        path = set()
        
        def dfs(node_id):
            visited.add(node_id)
            path.add(node_id)
            
            for neighbor in adj.get(node_id, []):
                if neighbor not in visited:
                    dfs(neighbor)
                elif neighbor in path:
                    msg = f"Circular dependency ({cycle_type}) involving node {node_id}"
                    if severity == "WARNING":
                        self.diagnostics.add_warning("GraphValidator", msg)
                    elif severity == "INFO":
                        self.diagnostics.add_info("GraphValidator", msg)
                    else:
                        self.diagnostics.add_error("GraphValidator", msg)
            path.remove(node_id)
            
        for n in list(adj.keys()):
            if n not in visited:
                dfs(n)
