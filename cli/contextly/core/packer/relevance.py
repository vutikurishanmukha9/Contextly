from typing import List, Dict, Set, Tuple
from pathlib import Path
import math
import collections

from ...types.models import KnowledgeGraph, KnowledgeNode

class TaskLexicalEngine:
    """Simple BM25-style lexical matcher to find start nodes based on task terms."""
    
    def __init__(self, task: str):
        # Normalize and tokenize task into terms
        self.terms = self._tokenize(task)
        
    def _tokenize(self, text: str) -> List[str]:
        text = text.lower().replace("_", " ").replace("-", " ")
        import re
        words = re.findall(r'\b[a-z]{3,}\b', text)
        return list(set(words))
        
    def score_nodes(self, nodes: List[KnowledgeNode]) -> Dict[str, float]:
        """Score each node based on term occurrences in its name and path."""
        if not self.terms:
            return {n.id: 1.0 for n in nodes}
            
        scores = {}
        # Precompute IDF (Inverse Document Frequency)
        doc_count = len(nodes)
        term_df = collections.defaultdict(int)
        
        node_terms = {}
        for node in nodes:
            # combine path and name as document text
            text = f"{node.name} {node.path} {node.metadata.get('docstring', '')}"
            n_terms = self._tokenize(text)
            node_terms[node.id] = n_terms
            
            seen = set()
            for t in n_terms:
                if t in self.terms and t not in seen:
                    term_df[t] += 1
                    seen.add(t)
                    
        idf = {}
        for t in self.terms:
            df = term_df.get(t, 0)
            # BM25 IDF formula
            idf[t] = math.log(1 + (doc_count - df + 0.5) / (df + 0.5))
            
        # Compute TF and final score
        for node in nodes:
            score = 0.0
            n_terms = node_terms[node.id]
            term_freqs = collections.Counter(n_terms)
            
            for t in self.terms:
                tf = term_freqs.get(t, 0)
                if tf > 0:
                    # Simplified BM25 term frequency
                    # k1 = 1.5, b = 0.75, avgdl assumed 10
                    k1 = 1.5
                    score += idf[t] * (tf * (k1 + 1)) / (tf + k1)
                    
            scores[node.id] = score
            
        return scores


class GraphRelevanceEngine:
    """Propagates relevance scores outward from start nodes using Shortest Path distance."""
    
    def __init__(self, graph: KnowledgeGraph):
        self.graph = graph
        self.adj_list = collections.defaultdict(list)
        
        # Build bidirectional adjacency list for distance traversal
        for edge in graph.relationships:
            self.adj_list[edge.source_id].append(edge.target_id)
            self.adj_list[edge.target_id].append(edge.source_id)
            
    def compute_distance_relevance(self, start_scores: Dict[str, float]) -> Dict[str, float]:
        """
        Calculates final relevance based on initial start scores + distance decay.
        """
        final_scores = {node.id: 0.0 for node in self.graph.nodes}
        
        # Start BFS from all nodes with a score > 0
        queue = collections.deque()
        visited = set()
        
        # We process in batches of distance
        # To avoid massive BFS overhead, we only take the top N start nodes
        sorted_starts = sorted([(n_id, score) for n_id, score in start_scores.items() if score > 0], key=lambda x: x[1], reverse=True)
        top_starts = sorted_starts[:50] # Limit to top 50 highly relevant nodes
        
        if not top_starts:
            return final_scores
            
        max_start_score = top_starts[0][1]
        
        for n_id, score in top_starts:
            normalized_score = score / max_start_score * 100.0 # scale 0-100
            final_scores[n_id] = max(final_scores[n_id], normalized_score)
            queue.append((n_id, normalized_score, 0))
            visited.add(n_id)
            
        DECAY_FACTOR = 0.5 # Each hop halves the relevance
        MAX_DEPTH = 3
        
        while queue:
            current_id, current_score, depth = queue.popleft()
            
            if depth >= MAX_DEPTH:
                continue
                
            next_score = current_score * DECAY_FACTOR
            if next_score < 5.0: # Minimum relevance threshold to propagate
                continue
                
            for neighbor_id in self.adj_list[current_id]:
                if neighbor_id not in visited:
                    visited.add(neighbor_id)
                    final_scores[neighbor_id] = max(final_scores[neighbor_id], next_score)
                    queue.append((neighbor_id, next_score, depth + 1))
                    
        return final_scores
