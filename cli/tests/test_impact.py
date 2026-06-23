import pytest
from pathlib import Path
from typer.testing import CliRunner
from unittest.mock import patch, MagicMock
from contextly.main import app
from contextly.core.impact.engine import ImpactEngine

@pytest.fixture
def runner():
    return CliRunner()

def test_impact_engine_basic(tmp_path):
    from contextly.types.models import KnowledgeGraph, KnowledgeNode
    node_a = KnowledgeNode(id="src/a.py", name="a", path="src/a.py", type="FILE", size=10)
    node_b = KnowledgeNode(id="src/b.py", name="b", path="src/b.py", type="FILE", size=10)
    graph = KnowledgeGraph(nodes=[node_a, node_b])
    
    engine = ImpactEngine(graph)
    assert engine.node_lookup["src/a.py"] == node_a
    
    # We can just call analyze_impact and check the structure
    result = engine.analyze_impact("src/a.py")
    assert "HIGH" in result
    assert "MEDIUM" in result
    assert "LOW" in result

def test_impact_engine_advanced(tmp_path):
    from contextly.types.models import KnowledgeGraph, KnowledgeNode, Relationship
    from contextly.utils.exceptions import ContextlyError
    
    node_a = KnowledgeNode(id="src/a.py", name="a", path="src/a.py", type="FILE", size=10)
    node_b = KnowledgeNode(id="src/b.py", name="b", path="src/b.py", type="FILE", size=10)
    node_c = KnowledgeNode(id="src/c.py", name="c", path="src/c.py", type="FILE", size=10)
    node_d = KnowledgeNode(id="ext/lib", name="ext", path="", type="UNRESOLVED_EXTERNAL", size=0)
    node_e = KnowledgeNode(id="src/b.py::func", name="func", path="src/b.py", type="FUNCTION", size=0)
    
    edge_1 = Relationship(source_id="src/b.py", target_id="src/a.py", type="IMPORTS") # Depth 1, HIGH
    edge_2 = Relationship(source_id="src/c.py", target_id="src/b.py", type="IMPORTS") # Depth 2, MEDIUM
    edge_3 = Relationship(source_id="ext/lib", target_id="src/a.py", type="IMPORTS") # Depth 1, HIGH but ignored
    edge_4 = Relationship(source_id="src/b.py::func", target_id="src/a.py", type="IMPORTS") # Depth 1, Entity
    
    graph = KnowledgeGraph(nodes=[node_a, node_b, node_c, node_d, node_e], relationships=[edge_1, edge_2, edge_3, edge_4])
    
    engine = ImpactEngine(graph)
    
    # Missing target
    with pytest.raises(ContextlyError, match="Target file not found in graph"):
        engine.analyze_impact("nonexistent.py")
        
    result = engine.analyze_impact("src/a.py")
    
    assert any(f.id == "src/b.py" for f in result["HIGH"]["files"])
    assert any(e.id == "src/b.py::func" for e in result["HIGH"]["entities"])
    
    assert any(f.id == "src/c.py" for f in result["MEDIUM"]["files"])

@patch("contextly.commands.impact.require_contextly_initialized")
def test_impact_command_no_db(mock_req, runner, tmp_path, monkeypatch):
    mock_req.side_effect = Exception("No active context memory found")
    monkeypatch.chdir(tmp_path)
    # Create dummy file
    (tmp_path / "src").mkdir()
    (tmp_path / "src" / "file.py").write_text("pass")
    
    result = runner.invoke(app, ["impact", "src/file.py"])
    assert result.exit_code == 1
    assert "No active context memory found" in result.output

@patch("contextly.commands.impact.require_contextly_initialized")
@patch("contextly.commands.impact.ImportGraphBuilder")
@patch("contextly.commands.impact.GraphValidator")
@patch("contextly.commands.impact.ImpactEngine")
def test_impact_command_success(mock_impact, mock_validator, mock_builder, mock_req, runner, tmp_path, monkeypatch):
    # Setup graph builder mocks
    mock_graph = MagicMock()
    mock_builder.return_value.build.return_value = mock_graph
    mock_validator.return_value.validate.return_value = mock_graph
    
    # Setup ImpactEngine mocks
    mock_impact.return_value.analyze_impact.return_value = {
        "HIGH": {"files": [], "entities": []},
        "MEDIUM": {"files": [], "entities": []},
        "LOW": {"files": [], "entities": []}
    }
    
    monkeypatch.chdir(tmp_path)
    # Setup fake file
    (tmp_path / "src").mkdir()
    file_path = tmp_path / "src" / "b.py"
    file_path.write_text("pass")
    
    result = runner.invoke(app, ["impact", "src/b.py"])
    assert result.exit_code == 0
    assert "Change Impact Analysis (Blast Radius)" in result.output
