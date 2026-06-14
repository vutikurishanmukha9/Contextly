import pytest
import json
from pathlib import Path

from contextly.core.explainer.engine import ExplainerEngine
from contextly.types.models import RepositoryKnowledge, DomainKnowledge, KnowledgeGraph, DomainType

def test_explainer_engine_extracts_subgraph(tmp_path):
    mock_knowledge = RepositoryKnowledge(
        repository_hash="hash",
        generated_at="2026-06-14T00:00:00",
        contextly_version="1.0.0",
        technologies={"frameworks": [], "languages": [], "libraries": []},
        architecture={"primary_pattern": {"name": "MVC", "confidence": 1.0, "evidence": []}, "pattern_candidates": [], "layers": []},
        capabilities=[],
        domains=[
            DomainKnowledge(id="d1", name="auth", type=DomainType.DOMAIN, node_ids=["n1"]),
            DomainKnowledge(id="d2", name="payment", type=DomainType.DOMAIN, node_ids=["n2"])
        ],
        graph=KnowledgeGraph(
            nodes=[
                {"id": "n1", "type": "COMPONENT", "name": "Auth", "path": "auth.py"},
                {"id": "n2", "type": "COMPONENT", "name": "Pay", "path": "pay.py"},
                {"id": "n3", "type": "SERVICE", "name": "External", "path": "ext.py"}
            ],
            relationships=[
                {"source_id": "n1", "target_id": "n2", "type": "IMPORTS"},
                {"source_id": "n3", "target_id": "n1", "type": "IMPORTS"}
            ]
        )
    )
    
    contextly_dir = tmp_path / ".contextly"
    contextly_dir.mkdir()
    with open(contextly_dir / "repository.json", "w") as f:
        f.write(mock_knowledge.model_dump_json())
        
    engine = ExplainerEngine(root_dir=str(tmp_path))
    prompt = engine.explain("auth")
    
    assert "# Domain Context: auth" in prompt
    assert "This is a compressed knowledge graph subset for the 'auth' domain" in prompt
    assert "auth.py" in prompt
    assert "pay.py" in prompt
    assert "ext.py" in prompt
    
def test_explainer_engine_domain_not_found(tmp_path):
    mock_knowledge = RepositoryKnowledge(
        repository_hash="hash", generated_at="2026-06-14T00:00:00", contextly_version="1.0.0",
        technologies={"frameworks": [], "languages": [], "libraries": []},
        architecture={"primary_pattern": {"name": "MVC", "confidence": 1.0, "evidence": []}, "pattern_candidates": [], "layers": []},
        capabilities=[], domains=[], graph=KnowledgeGraph()
    )
    contextly_dir = tmp_path / ".contextly"
    contextly_dir.mkdir()
    with open(contextly_dir / "repository.json", "w") as f:
        f.write(mock_knowledge.model_dump_json())
        
    engine = ExplainerEngine(root_dir=str(tmp_path))
    with pytest.raises(ValueError, match="Domain 'missing' not found"):
        engine.explain("missing")
