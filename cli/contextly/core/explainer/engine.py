import json
from typing import Optional, List, Dict, Set
from pathlib import Path

from contextly.core.memory.engine import MemoryEngine
from contextly.types.models import RepositoryKnowledge, KnowledgeNode, Relationship

class ExplainerEngine:

    def __init__(self, root_dir: str | Path):
        self.root_dir = Path(root_dir)
        self.memory_engine = MemoryEngine(self.root_dir)
        
    def _load_knowledge(self) -> RepositoryKnowledge:
        knowledge_file = self.root_dir / ".contextly" / "repository.json"
        if not knowledge_file.exists():
            raise FileNotFoundError("Repository knowledge not found. Please run 'contextly analyze' first.")
            
        with open(knowledge_file, "r", encoding="utf-8") as f:
            data = json.load(f)
            return RepositoryKnowledge(**data)

    def explain(self, domain_name: str) -> None:
        """
        Extracts a focused subgraph for the requested domain and asks the LLM to explain it.
        """
        knowledge = self._load_knowledge()
        
        # 1. Find Domain
        target_domain = next((d for d in knowledge.domains if d.name.lower() == domain_name.lower()), None)
        if not target_domain:
            raise ValueError(f"Domain '{domain_name}' not found. Available domains: {', '.join(d.name for d in knowledge.domains)}")
            
        # 2. Extract Sub-Graph
        domain_node_ids = set(target_domain.node_ids)
        
        domain_nodes: List[KnowledgeNode] = []
        outgoing_edges: List[Relationship] = []
        incoming_edges: List[Relationship] = []
        
        # O(N) lookup maps
        node_map = {n.id: n for n in knowledge.graph.nodes}
        
        for node_id in domain_node_ids:
            if node_id in node_map:
                domain_nodes.append(node_map[node_id])
                
        for rel in knowledge.graph.relationships:
            if rel.source_id in domain_node_ids and rel.target_id not in domain_node_ids:
                outgoing_edges.append(rel)
            elif rel.target_id in domain_node_ids and rel.source_id not in domain_node_ids:
                incoming_edges.append(rel)
                
        # 3. Construct Context Payload
        context_data = {
            "domain_name": target_domain.name,
            "domain_type": target_domain.type.value,
            "internal_nodes": [
                {
                    "path": n.path,
                    "type": n.type.value,
                    "exports": n.metadata.get("exports", [])
                }
                for n in domain_nodes
            ],
            "dependencies_out": [
                {
                    "from_node": node_map[r.source_id].path if r.source_id in node_map else r.source_id,
                    "to_node": node_map[r.target_id].path if r.target_id in node_map else r.target_id,
                    "type": r.type.value
                }
                for r in outgoing_edges
            ],
            "dependents_in": [
                {
                    "from_node": node_map[r.source_id].path if r.source_id in node_map else r.source_id,
                    "to_node": node_map[r.target_id].path if r.target_id in node_map else r.target_id,
                    "type": r.type.value
                }
                for r in incoming_edges
            ]
        }
        
        # 4. Format as pure context payload (no prompts/instructions)
        payload = (
            f"# Domain Context: {domain_name}\n\n"
            f"This is a compressed knowledge graph subset for the '{domain_name}' domain.\n"
            "Use this context to understand the structural boundaries, internal components, and external dependencies of this domain.\n\n"
            "## Architecture Graph\n"
            f"```json\n{json.dumps(context_data, indent=2)}\n```\n"
        )
        
        return payload
