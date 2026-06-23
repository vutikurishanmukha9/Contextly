import pytest
from contextly.core.packer.ranking import RankingEngine
from pathlib import Path
from contextly.types.models import KnowledgeGraph, KnowledgeNode, NodeType, Relationship, RelationshipType

def test_ranker_disconnected_graph():
    graph = KnowledgeGraph(nodes=[], relationships=[])
    
    # A completely disconnected graph
    n1 = KnowledgeNode(id="n1", type=NodeType.FILE, name="1", path="1", metadata={})
    n2 = KnowledgeNode(id="n2", type=NodeType.FILE, name="2", path="2", metadata={})
    n3 = KnowledgeNode(id="n3", type=NodeType.FILE, name="3", path="3", metadata={})
    
    graph.nodes.extend([n1, n2, n3])
    
    ranker = RankingEngine(Path("."), "some task", graph)
    # The rank method expects Path objects
    paths = [Path(n.path) for n in graph.nodes]
    sorted_files = ranker.rank(paths)
    
    assert len(sorted_files) == 3

def test_ranker_with_edges():
    graph = KnowledgeGraph(nodes=[], relationships=[])
    n1 = KnowledgeNode(id="n1", type=NodeType.FILE, name="1", path="1", metadata={})
    n2 = KnowledgeNode(id="n2", type=NodeType.FILE, name="2", path="2", metadata={})
    graph.nodes.extend([n1, n2])
    
    # n1 imports n2, so n2 should be highly ranked if n1 is important
    graph.relationships.append(Relationship(
        source_id="n1", target_id="n2", type=RelationshipType.IMPORTS, confidence=1.0, resolution_method="mock"
    ))
    
    ranker = RankingEngine(Path("."), "test", graph)
    # Mocking relevance score inside ranker for n1
    ranker.relevance_scores = {"1": 1.0}
    paths = [Path("1"), Path("2")]
    
    sorted_files = ranker.rank(paths)
    # Since n1 has higher relevance, it should be first
    assert sorted_files[0].name == "1"
