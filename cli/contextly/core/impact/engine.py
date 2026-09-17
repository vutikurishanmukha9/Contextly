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
        target_path_posix = target_path.replace('\\', '/').lower()
        if target_path_posix.startswith('./'):
            target_path_posix = target_path_posix[2:]
            
        exact_matches = []
        suffix_matches = []
        for node in self.graph.nodes:
            if node.path:
                normalized_node_path = node.path.replace('\\', '/').lower()
                if normalized_node_path == target_path_posix:
                    exact_matches.append(node.id)
                elif normalized_node_path.endswith('/' + target_path_posix):
                    suffix_matches.append((node.path, node.id))
                
        if exact_matches:
            start_nodes = exact_matches
        elif suffix_matches:
            distinct_files = {p for p, _ in suffix_matches}
            if len(distinct_files) > 1:
                matches_str = ", ".join(sorted(distinct_files))
                raise ContextlyError(
                    f"Ambiguous target '{target_path}'. Multiple matching files found: {matches_str}. "
                    "Please specify the full relative path."
                )
            start_nodes = [nid for _, nid in suffix_matches]
                
        if not start_nodes:
            # Provide a clearer error message since only supported extensions are added to the graph by default
            from ..graph.parsers.registry import ParserRegistry
            supported = ", ".join(ParserRegistry.supported_extensions())
            raise ContextlyError(f"Target file not found in graph: {target_path}. Note: Only source files ({supported}) are currently tracked in the dependency graph.")
            
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
                    
            if len(visited) > 2000:
                # Halt the traversal early if the blast radius exceeds this threshold
                # to prevent memory exhaustion and CPU saturation on massively connected hub nodes.
                import sys
                print("WARNING: Blast radius traversal exceeded 2000 nodes. Halting early as this is a core hub dependency.", file=sys.stderr)
                break
                
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

    def generate_visual_tree(self, target_path: str, impact: Dict[str, Dict[str, List[KnowledgeNode]]]) -> str:
        """Generates a hierarchical visual cascade tree of the blast radius."""
        lines = [f"[bold red]*[/bold red] [bold white]{target_path}[/bold white] (Modified Target)"]
        
        high_files = impact.get("HIGH", {}).get("files", [])
        med_files = impact.get("MEDIUM", {}).get("files", [])
        low_files = impact.get("LOW", {}).get("files", [])
        
        if not high_files and not med_files and not low_files:
            lines.append("  └── [dim](No dependent files affected - isolated component)[/dim]")
            return "\n".join(lines)
            
        for i, hf in enumerate(high_files[:8]):
            is_last_high = (i == len(high_files[:8]) - 1) and not med_files and not low_files
            prefix = "└──" if is_last_high else "├──"
            lines.append(f"  {prefix} [bold red][HIGH][/bold red] {hf.path or hf.name}")
            
        if len(high_files) > 8:
            lines.append(f"  ├── [dim]... and {len(high_files) - 8} more HIGH risk files[/dim]")
            
        for j, mf in enumerate(med_files[:6]):
            is_last_med = (j == len(med_files[:6]) - 1) and not low_files
            prefix = "└──" if is_last_med else "├──"
            lines.append(f"  {prefix} [bold yellow][MEDIUM][/bold yellow] {mf.path or mf.name}")
            
        if len(med_files) > 6:
            lines.append(f"  ├── [dim]... and {len(med_files) - 6} more MEDIUM risk files[/dim]")
            
        for k, lf in enumerate(low_files[:4]):
            is_last_low = (k == len(low_files[:4]) - 1)
            prefix = "└──" if is_last_low else "├──"
            lines.append(f"  {prefix} [bold cyan][LOW][/bold cyan] {lf.path or lf.name}")
            
        if len(low_files) > 4:
            lines.append(f"  └── [dim]... and {len(low_files) - 4} more LOW risk files[/dim]")
            
        return "\n".join(lines)

