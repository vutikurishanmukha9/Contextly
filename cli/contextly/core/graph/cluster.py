import hashlib
from typing import List, Dict, Set
from pathlib import Path

from contextly.types.models import KnowledgeGraph, DomainKnowledge, DomainType, RelationshipType

BOUNDARY_MARKERS = {"features", "services", "modules", "packages", "domains", "apps"}
INFRA_MARKERS = {"core", "infrastructure", "infra"}
SHARED_MARKERS = {"shared", "common", "utils", "helpers", "lib"}

class DomainClusterer:
    """
    Domain Clustering Engine.
    Uses path heuristics combined with Graph Edge analysis to determine logical boundaries.
    """
    
    def cluster(self, graph: KnowledgeGraph) -> List[DomainKnowledge]:
        node_to_domain: Dict[str, str] = {}
        domain_types: Dict[str, DomainType] = {}
        
        # Build adjacency for propagation
        incoming_edges: Dict[str, Set[str]] = {node.id: set() for node in graph.nodes}
        for rel in graph.relationships:
            if rel.type == RelationshipType.IMPORTS:
                # If A imports B, B has an incoming edge from A
                if rel.target_id in incoming_edges:
                    incoming_edges[rel.target_id].add(rel.source_id)

        # Pass 1: Structural Heuristics
        for node in graph.nodes:
            parts = Path(node.path).parts
            assigned = False
            
            for i, part in enumerate(parts):
                if part.lower() in BOUNDARY_MARKERS and i + 1 < len(parts):
                    if i + 1 == len(parts) - 1:
                        domain_name = Path(parts[i + 1]).stem.lower()
                    else:
                        domain_name = parts[i + 1].lower()
                    node_to_domain[node.id] = domain_name
                    
                    if domain_name in INFRA_MARKERS:
                        domain_types.setdefault(domain_name, DomainType.INFRASTRUCTURE)
                    elif domain_name in SHARED_MARKERS:
                        domain_types.setdefault(domain_name, DomainType.SHARED)
                    else:
                        domain_types.setdefault(domain_name, DomainType.DOMAIN)
                        
                    assigned = True
                    break
                
                if part.lower() in INFRA_MARKERS:
                    domain_name = "infrastructure"
                    domain_types.setdefault(domain_name, DomainType.INFRASTRUCTURE)
                    node_to_domain[node.id] = domain_name
                    assigned = True
                    break
                    
                elif part.lower() in SHARED_MARKERS:
                    domain_name = "shared"
                    domain_types.setdefault(domain_name, DomainType.SHARED)
                    node_to_domain[node.id] = domain_name
                    assigned = True
                    break
                    
        structural_nodes = set(node_to_domain.keys())

        # Pass 2: Graph Propagation (Assign isolated/utility nodes based on who uses them)
        import collections
        
        # Build outgoing edges for BFS propagation
        outgoing_edges: Dict[str, Set[str]] = {node.id: set() for node in graph.nodes}
        for rel in graph.relationships:
            if rel.type == RelationshipType.IMPORTS:
                outgoing_edges[rel.source_id].add(rel.target_id)
                
        queue = collections.deque(structural_nodes)
        
        while queue:
            caller_id = queue.popleft()
            
            for callee_id in outgoing_edges.get(caller_id, set()):
                if callee_id in structural_nodes:
                    continue
                
                # Look at who imports this callee node
                callers = incoming_edges.get(callee_id, set())
                caller_domains = set()
                for cid in callers:
                    if cid in node_to_domain:
                        caller_domains.add(node_to_domain[cid])
                        
                current_domain = node_to_domain.get(callee_id)
                new_domain = current_domain
                
                if len(caller_domains) == 1:
                    new_domain = list(caller_domains)[0]
                elif len(caller_domains) > 1:
                    new_domain = "shared"
                    domain_types["shared"] = DomainType.SHARED
                    
                if new_domain != current_domain:
                    node_to_domain[callee_id] = new_domain
                    # Enqueue callee to propagate its new domain to its own callees
                    queue.append(callee_id)

        # Pass 3: Fallback for orphans
        for node in graph.nodes:
            if node.id not in node_to_domain:
                node_to_domain[node.id] = "global"
                domain_types["global"] = DomainType.SHARED
                
        # Group into DomainKnowledge
        clusters: Dict[str, List[str]] = {}
        for node_id, domain_name in node_to_domain.items():
            if domain_name not in clusters:
                clusters[domain_name] = []
            clusters[domain_name].append(node_id)
            
        result = []
        for name, node_ids in sorted(clusters.items()):
            dtype = domain_types.get(name, DomainType.DOMAIN)
            stable_source = f"{name}:{','.join(sorted(node_ids))}"
            domain_id = f"domain_{hashlib.sha256(stable_source.encode('utf-8')).hexdigest()[:12]}"
            result.append(DomainKnowledge(
                id=domain_id,
                name=name,
                type=dtype,
                node_ids=sorted(node_ids)
            ))
            
        return result
