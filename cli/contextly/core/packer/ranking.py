from pathlib import Path
from typing import List, Dict, Optional

from ...types.models import KnowledgeGraph
from .relevance import TaskLexicalEngine, GraphRelevanceEngine

class RankingEngine:
    """Scores and ranks files based on their estimated value to the LLM or a specific task."""
    
    def __init__(self, root_dir: Path, task: Optional[str] = None, graph: Optional[KnowledgeGraph] = None):
        self.root_dir = root_dir
        self.task = task
        self.graph = graph
        self.relevance_scores: Dict[str, float] = {}
        
        if self.task and self.graph:
            self._compute_graph_relevance()
            
    def _compute_graph_relevance(self):
        # 1. Score nodes lexically
        lex_engine = TaskLexicalEngine(self.task)
        start_scores = lex_engine.score_nodes(self.graph.nodes)
        
        # 2. Propagate via graph distance
        graph_engine = GraphRelevanceEngine(self.graph)
        raw_scores = graph_engine.compute_distance_relevance(start_scores)
        
        # 3. Map node IDs back to file paths
        node_lookup = {n.id: n for n in self.graph.nodes}
        for node_id, score in raw_scores.items():
            if score > 0:
                node = node_lookup.get(node_id)
                if node and node.path:
                    # Keep the maximum score for a given file path
                    # (multiple entities like classes/functions might be in the same file)
                    current = self.relevance_scores.get(node.path, 0.0)
                    self.relevance_scores[node.path] = max(current, score)
        
    def rank(self, files: List[Path]) -> List[Path]:
        """Returns the list of files sorted by their score (highest first)."""
        scored_files = []
        for file in files:
            score = self._score_file(file)
            scored_files.append((score, file))
            
        # Sort by score descending, then by path length ascending (prefer top-level)
        scored_files.sort(key=lambda x: (-x[0], len(x[1].parts), x[1].name))
        
        return [f[1] for f in scored_files]
        
    def _score_file(self, file: Path) -> float:
        try:
            rel_path = file.relative_to(self.root_dir).as_posix()
        except ValueError:
            rel_path = file.name
            
        # If we have task relevance scores, use them as the primary score!
        if self.relevance_scores:
            # The relevance_scores dict uses node IDs which are often the file path.
            # Let's find the matching node.
            # Node IDs in the graph for files are typically the relative path string
            if rel_path in self.relevance_scores:
                return self.relevance_scores[rel_path]
            # fallback if node id doesn't exactly match
            for node_id, score in self.relevance_scores.items():
                if node_id.endswith(rel_path) or rel_path.endswith(node_id):
                    return score
            return 0.0

        # --- Fallback to generic heuristic scoring if no task is provided ---
        score = 0.0
        rel_path_lower = rel_path.lower()
        if rel_path_lower == ".":
            parts = (file.name.lower(),)
        else:
            parts = Path(rel_path_lower).parts
        
        # 1. Config / Core Docs
        if file.name.lower() in ["readme.md", "package.json", "pyproject.toml", "cargo.toml", "go.mod"]:
            score += 100.0
            
        # 2. Top-level files (Entry points)
        if len(parts) == 1:
            score += 40.0
            
        # 3. Source code
        if any(p in parts for p in ["src", "app", "lib", "core", "main"]):
            score += 40.0
            
        # 4. Tests
        if any(p in parts for p in ["tests", "test", "spec", "specs", "__tests__"]):
            score -= 10.0
            
        # 5. Utilities
        if any(p in parts for p in ["utils", "helpers", "misc", "vendor"]):
            score -= 20.0
            
        return score
