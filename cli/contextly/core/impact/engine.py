import collections
from typing import List, Dict, Set, Tuple
from ...types.models import KnowledgeGraph, KnowledgeNode
from ...utils.exceptions import ContextlyError

class ImpactEngine:
    """Calculates the blast radius of modifying a target file by traversing reverse dependencies."""
    
    def __init__(self, graph: KnowledgeGraph):
        self.graph = graph
        self.node_lookup = {n.id: n for n in graph.nodes}
        
        # Build reverse adjacency list: target_id -> list of source_ids
        self.reverse_adj = collections.defaultdict(list)
        for edge in graph.relationships:
            self.reverse_adj[edge.target_id].append(edge.source_id)

    def analyze_impact(self, target_path: str) -> Dict[str, Dict[str, List[KnowledgeNode]]]:
        """
        Finds all nodes affected by modifying the target_path.
        Returns grouped by risk level:
        {
            "HIGH": {"files": [...], "entities": [...]},
            "MEDIUM": {...},
            "LOW": {...}
        }
        """
        # 1. Find all nodes that belong to the target_path
        # target_path might be an exact node ID, or part of a path
        start_nodes = []
        target_path_lower = target_path.lower().replace('\\', '/')
        
        for node in self.graph.nodes:
            if node.path and node.path.lower().replace('\\', '/').endswith(target_path_lower):
                start_nodes.append(node.id)
                
        if not start_nodes:
            raise ContextlyError(f"Target file not found in graph: {target_path}")
            
        # 2. BFS to find reverse dependencies and their depths
        queue = collections.deque()
        visited = set()
        depths = {}
        
        for n_id in start_nodes:
            queue.append((n_id, 0))
            visited.add(n_id)
            
        while queue:
            current_id, depth = queue.popleft()
            
            # Record depth for non-start nodes
            if depth > 0:
                if current_id not in depths:
                    depths[current_id] = depth
                else:
                    depths[current_id] = min(depths[current_id], depth)
                    
            if depth >= 5: # Limit blast radius depth to prevent whole-repo explosion
                continue
                
            for source_id in self.reverse_adj[current_id]:
                if source_id not in visited:
                    visited.add(source_id)
                    queue.append((source_id, depth + 1))
                    
        # 3. Categorize by risk
        impact = {
            "HIGH": {"files": [], "entities": []},
            "MEDIUM": {"files": [], "entities": []},
            "LOW": {"files": [], "entities": []}
        }
        
        for node_id, depth in depths.items():
            if depth == 1:
                risk = "HIGH"
            elif depth == 2:
                risk = "MEDIUM"
            else:
                risk = "LOW"
                
            node = self.node_lookup.get(node_id)
            if not node:
                continue
                
            if node.type.value == "FILE":
                impact[risk]["files"].append(node)
            elif node.type.value in ["UNRESOLVED_EXTERNAL"]:
                continue
            else:
                impact[risk]["entities"].append(node)
                
        # Deduplicate files (if multiple entities in the same file are affected)
        for risk in impact:
            unique_files = {f.id: f for f in impact[risk]["files"]}
            impact[risk]["files"] = list(unique_files.values())
            
        return impact
