import pytest
from contextly.core.packer.formatter import KnowledgeFormatter
from contextly.core.graph.parsers.base import ParsedFileDTO, ExtractedEntity, EntityKind, EntityMethod, EntityField

def test_formatter_basic():
    # Setup dummy nodes
    func = ExtractedEntity(
        name="test_func",
        kind=EntityKind.FUNCTION,
        purpose="Test function",
        inputs=[EntityField(name="a"), EntityField(name="b")],
        outputs="int"
    )
    
    cls = ExtractedEntity(
        name="TestClass",
        kind=EntityKind.CLASS,
        purpose="Test class",
        parent_classes=["Base"],
        methods=[EntityMethod(name="test_method", inputs=[], returns="None")]
    )
    
    parsed = ParsedFileDTO(
        file_path="src/test.py",
        exports=[],
        imports=["os"],
        entities=[cls, func],
        error=None
    )
    
    # We will test formatting directly or assume it uses standard representation
    result = KnowledgeFormatter.format_file_knowledge(parsed)
    
    assert "TestClass" in result
    assert "test_func" in result
    assert "os" in result

def test_formatter_fallback():
    result = KnowledgeFormatter.format_metadata_fallback("src/test.txt", "hello world")
    assert "Content omitted" in result
    assert "txt" in result
