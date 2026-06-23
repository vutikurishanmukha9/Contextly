import pytest
from contextly.core.packer.relevance import TaskLexicalEngine, GraphRelevanceEngine
from contextly.types.models import KnowledgeGraph, KnowledgeNode, Relationship, RelationshipType

def test_task_lexical_engine():
    engine = TaskLexicalEngine("test task terms")
    assert "test" in engine.terms
    assert "task" in engine.terms
    assert "terms" in engine.terms
    
    node1 = KnowledgeNode(id="n1", name="test", path="src/test.py", type="FILE", size=100)
    node2 = KnowledgeNode(id="n2", name="other", path="src/other.py", type="FILE", size=100)
    
    scores = engine.score_nodes([node1, node2])
    assert scores["n1"] > scores["n2"]

def test_graph_relevance_engine():
    node1 = KnowledgeNode(id="n1", name="test", path="src/test.py", type="FILE", size=100)
    node2 = KnowledgeNode(id="n2", name="other", path="src/other.py", type="FILE", size=100)
    node3 = KnowledgeNode(id="n3", name="far", path="src/far.py", type="FILE", size=100)
    
    rel1 = Relationship(source_id="n1", target_id="n2", type=RelationshipType.IMPORTS)
    rel2 = Relationship(source_id="n2", target_id="n3", type=RelationshipType.IMPORTS)
    
    graph = KnowledgeGraph(nodes=[node1, node2, node3], relationships=[rel1, rel2])
    
    engine = GraphRelevanceEngine(graph)
    start_scores = {"n1": 100.0}
    
    final_scores = engine.compute_distance_relevance(start_scores)
    
    assert final_scores["n1"] == 100.0
    assert final_scores["n2"] == 50.0  # 100 * 0.5
    assert final_scores["n3"] == 25.0  # 50 * 0.5
