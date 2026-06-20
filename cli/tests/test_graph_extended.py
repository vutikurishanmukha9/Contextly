import pytest
from contextly.core.graph.validator import GraphValidator
from contextly.types.models import KnowledgeGraph, KnowledgeNode, Relationship, NodeType, RelationshipType
from contextly.core.graph.assembler import GraphAssembler
from contextly.core.graph.parsers.base import ParsedFileDTO, ExtractedEntity

def test_validator_dead_edges():
    graph = KnowledgeGraph(nodes=[
        KnowledgeNode(id="n1", type=NodeType.FILE, name="f1", path="f1"),
    ], relationships=[
        Relationship(source_id="n1", target_id="n2", type=RelationshipType.CALLS),
        Relationship(source_id="n3", target_id="n1", type=RelationshipType.IMPORTS)
    ])
    
    validator = GraphValidator()
    graph = validator.validate(graph)
    
    assert len(graph.relationships) == 0
    msgs = validator.diagnostics._messages
    assert any("Dead edge: target n2 does not exist" in m.message for m in msgs)
    assert any("Dead edge: source n3 does not exist" in m.message for m in msgs)

def test_validator_duplicates():
    graph = KnowledgeGraph(nodes=[
        KnowledgeNode(id="n1", type=NodeType.CLASS, name="C", path="f1", metadata={"fqn": "mod.C"}),
        KnowledgeNode(id="n2", type=NodeType.CLASS, name="C", path="f2", metadata={"fqn": "mod.C"}),
    ], relationships=[])
    
    validator = GraphValidator()
    validator.validate(graph)
    
    msgs = validator.diagnostics._messages
    assert any("Duplicate FQN detected: mod.C" in m.message for m in msgs)

def test_validator_orphans():
    graph = KnowledgeGraph(nodes=[
        KnowledgeNode(id="n1", type=NodeType.CLASS, name="C", path="f1", metadata={}),
    ], relationships=[])
    
    validator = GraphValidator()
    validator.validate(graph)
    
    msgs = validator.diagnostics._messages
    assert any("Orphaned Entity detected" in m.message for m in msgs)

def test_validator_cycles():
    graph = KnowledgeGraph(nodes=[
        KnowledgeNode(id="n1", type=NodeType.CLASS, name="C1", path="f1", metadata={}),
        KnowledgeNode(id="n2", type=NodeType.CLASS, name="C2", path="f1", metadata={}),
        KnowledgeNode(id="n3", type=NodeType.CLASS, name="C3", path="f1", metadata={}),
    ], relationships=[
        Relationship(source_id="n1", target_id="n2", type=RelationshipType.CALLS),
        Relationship(source_id="n2", target_id="n1", type=RelationshipType.CALLS),
        Relationship(source_id="n2", target_id="n3", type=RelationshipType.IMPORTS),
        Relationship(source_id="n3", target_id="n2", type=RelationshipType.IMPORTS),
    ])
    
    validator = GraphValidator()
    # Trigger unknown severity fallback for coverage
    validator._find_cycles({"n1": ["n1"]}, "UNKNOWN", "ERROR")
    validator.validate(graph)
    
    msgs = validator.diagnostics._messages
    assert any("Circular dependency (CALLS)" in m.message for m in msgs)
    assert any("Circular dependency (IMPORTS)" in m.message for m in msgs)
    assert any("Circular dependency (UNKNOWN)" in m.message for m in msgs)

def test_assembler_fuzzy_resolution():
    assembler = GraphAssembler()
    dto1 = ParsedFileDTO(
        file_path="src/components/button.ts",
        exports=["ButtonComponent"],
        imports=[],
        entities=[ExtractedEntity(name="ButtonComponent", kind="CLASS", parent_classes=[], called_entities=[], returns=[])]
    )
    dto2 = ParsedFileDTO(
        file_path="src/app.ts",
        exports=[],
        imports=["src/components/button", "unknown_module"],
        entities=[ExtractedEntity(name="App", kind="CLASS", parent_classes=[], called_entities=["ButtonComponent", "UnknownFn"], returns=[])]
    )
    
    assembler.add_node(dto1)
    assembler.add_node(dto2)
    assembler.build_relationships([dto1, dto2])
    
    rel_types = [r.type for r in assembler.graph.relationships]
    assert RelationshipType.CALLS in rel_types
    assert RelationshipType.IMPORTS in rel_types
    
    # Check that unresolved external was created
    nodes = assembler.graph.nodes
    unresolved = [n for n in nodes if n.type == NodeType.UNRESOLVED_EXTERNAL]
    assert len(unresolved) > 0

def test_assembler_deep_relationships():
    assembler = GraphAssembler()
    
    from contextly.core.graph.parsers.base import EntityMethod
    
    dto1 = ParsedFileDTO(
        file_path="src/base.ts",
        exports=["BaseModel", "db", "auth"],
        imports=[],
        entities=[
            ExtractedEntity(name="BaseModel", kind="CLASS", parent_classes=[], called_entities=[], returns=[]),
            ExtractedEntity(name="db", kind="UNKNOWN", parent_classes=[], called_entities=[], returns=[]),
            ExtractedEntity(name="auth", kind="UNKNOWN", parent_classes=[], called_entities=[], returns=[])
        ]
    )
    
    dto3 = ParsedFileDTO(
        file_path="src/auth.ts",
        exports=["login"],
        imports=[],
        entities=[
            ExtractedEntity(name="login", kind="FUNCTION", parent_classes=[], called_entities=[], returns=[])
        ]
    )
    
    # We will simulate multiple candidates for "db" to hit fuzzy_global_multiple_candidates
    dto1_dup = ParsedFileDTO(
        file_path="src/other/db.ts",
        exports=["db"],
        imports=[],
        entities=[ExtractedEntity(name="db", kind="UNKNOWN", parent_classes=[], called_entities=[], returns=[])]
    )
    
    dto2 = ParsedFileDTO(
        file_path="src/models/user.ts",
        exports=["UserModel", "getUser"],
        imports=[],
        entities=[
            ExtractedEntity(
                name="UserModel", kind="CLASS", parent_classes=["BaseModel"], called_entities=["auth.login"], returns=[],
                methods=[EntityMethod(name="save", returns="UserDTO")]
            ),
            ExtractedEntity(
                name="getUser", kind="FUNCTION", parent_classes=[], called_entities=["db"], returns="UserDTO", outputs="UserDTO"
            )
        ]
    )
    
    assembler.add_node(dto1)
    assembler.add_node(dto1_dup)
    assembler.add_node(dto2)
    assembler.add_node(dto3)
    assembler.build_relationships([dto1, dto1_dup, dto2, dto3])
    
    rels = assembler.graph.relationships
    types = {r.type for r in rels}
    methods = {r.resolution_method for r in rels if hasattr(r, 'resolution_method')}
    
    assert RelationshipType.EXTENDS in types
    assert RelationshipType.RETURNS in types
    assert RelationshipType.CALLS in types
    
    # "auth.login" should hit fuzzy_suffix_match because auth exists
    assert "fuzzy_suffix_match" in methods
    
    # "db" should hit fuzzy_global_multiple_candidates because there are two db entities
    assert "fuzzy_global_multiple_candidates" in methods

