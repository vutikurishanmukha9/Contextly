import pytest
from contextly.core.graph.cluster import DomainClusterer
from contextly.types.models import KnowledgeGraph, KnowledgeNode, NodeType, Relationship, RelationshipType, DomainType

def test_domain_clusterer_heuristics():
    graph = KnowledgeGraph()
    
    # Node in features -> 'auth' domain
    n1 = KnowledgeNode(id="n1", type=NodeType.COMPONENT, name="login", path="src/features/auth/login.tsx")
    # Node in services -> 'payment' domain
    n2 = KnowledgeNode(id="n2", type=NodeType.SERVICE, name="stripe", path="src/services/payment/stripe.ts")
    # Node in shared
    n3 = KnowledgeNode(id="n3", type=NodeType.COMPONENT, name="button", path="src/shared/ui/button.tsx")
    # Unassigned node imported ONLY by auth
    n4 = KnowledgeNode(id="n4", type=NodeType.UNKNOWN, name="authHelper", path="src/hooks/authHelper.ts")
    # Unassigned node imported by auth and payment
    n5 = KnowledgeNode(id="n5", type=NodeType.UNKNOWN, name="formatDate", path="src/formatters/date.ts")
    # Completely orphan node
    n6 = KnowledgeNode(id="n6", type=NodeType.UNKNOWN, name="orphan", path="script.py")
    
    graph.nodes = [n1, n2, n3, n4, n5, n6]
    
    # n1 imports n4 (auth imports authHelper)
    graph.relationships.append(Relationship(source_id="n1", target_id="n4", type=RelationshipType.IMPORTS))
    
    # n1 imports n5 and n2 imports n5 (both import formatDate)
    graph.relationships.append(Relationship(source_id="n1", target_id="n5", type=RelationshipType.IMPORTS))
    graph.relationships.append(Relationship(source_id="n2", target_id="n5", type=RelationshipType.IMPORTS))
    
    clusterer = DomainClusterer()
    domains = clusterer.cluster(graph)
    
    domain_map = {d.name: d for d in domains}
    
    assert "auth" in domain_map
    assert "payment" in domain_map
    assert "shared" in domain_map
    assert "global" in domain_map
    
    # n1 and n4 should be in auth
    assert "n1" in domain_map["auth"].node_ids
    assert "n4" in domain_map["auth"].node_ids
    assert domain_map["auth"].type == DomainType.DOMAIN
    
    # n2 should be in payment
    assert "n2" in domain_map["payment"].node_ids
    
    # n3 and n5 should be in shared
    assert "n3" in domain_map["shared"].node_ids
    assert "n5" in domain_map["shared"].node_ids
    assert domain_map["shared"].type == DomainType.SHARED
    
    # n6 should be in global
    assert "n6" in domain_map["global"].node_ids


def test_domain_clusterer_direct_boundary_files_are_semantic_and_deterministic():
    graph = KnowledgeGraph(
        nodes=[
            KnowledgeNode(id="n1", type=NodeType.SERVICE, name="stripe", path="src/services/stripe.ts"),
            KnowledgeNode(id="n2", type=NodeType.SERVICE, name="paypal", path="src/services/paypal.ts"),
        ]
    )

    first = DomainClusterer().cluster(graph)
    second = DomainClusterer().cluster(graph)
    first_map = {domain.name: domain for domain in first}
    second_map = {domain.name: domain for domain in second}

    assert set(first_map) == {"stripe", "paypal"}
    assert first_map["stripe"].id == second_map["stripe"].id
    assert first_map["paypal"].id == second_map["paypal"].id


def test_domain_clusterer_propagation_convergence():
    graph = KnowledgeGraph(
        nodes=[
            KnowledgeNode(id="n1", type=NodeType.COMPONENT, name="feat1", path="src/features/auth/feat1.ts"),
            KnowledgeNode(id="n2", type=NodeType.COMPONENT, name="feat2", path="src/features/payment/feat2.ts"),
            KnowledgeNode(id="n3", type=NodeType.COMPONENT, name="helper", path="src/helpers/helper.ts"),
        ],
        relationships=[
            Relationship(source_id="n1", target_id="n3", type=RelationshipType.IMPORTS),
            Relationship(source_id="n2", target_id="n3", type=RelationshipType.IMPORTS),
        ]
    )

    domains = DomainClusterer().cluster(graph)
    domain_map = {d.name: d for d in domains}
    
    assert "auth" in domain_map
    assert "payment" in domain_map
    assert "shared" in domain_map
    assert "n3" in domain_map["shared"].node_ids
