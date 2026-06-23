import pytest
from typer.testing import CliRunner
from contextly.main import app
from unittest.mock import patch, MagicMock

@pytest.fixture
def runner():
    return CliRunner()

from contextly.utils.exceptions import ValidationError

@patch("contextly.commands.summary.require_contextly_initialized")
def test_summary_no_db(mock_req, runner, tmp_path):
    mock_req.side_effect = ValidationError("No active context memory found")
    with runner.isolated_filesystem(temp_dir=tmp_path):
        result = runner.invoke(app, ["summary"])
        assert result.exit_code == 1
        assert "No active context memory found" in result.output

@patch("contextly.commands.summary.require_contextly_initialized")
@patch("contextly.commands.summary.ImportGraphBuilder")
@patch("contextly.commands.summary.GraphValidator")
def test_summary_success(mock_validator, mock_builder, mock_req, runner, tmp_path):
    # Mock ImportGraphBuilder methods
    mock_instance = mock_builder.return_value
    
    # Create fake graph
    from contextly.types.models import KnowledgeGraph, KnowledgeNode, Relationship
    node_a = KnowledgeNode(id="src/app/main.py", name="main", path="src/app/main.py", type="FILE", size=10)
    node_b = KnowledgeNode(id="src/lib/utils.py", name="utils", path="src/lib/utils.py", type="FILE", size=10)
    node_c = KnowledgeNode(id="frontend/index.js", name="index", path="frontend/index.js", type="FILE", size=10)
    node_func = KnowledgeNode(id="src/app/main.py::func", name="func", path="src/app/main.py", type="FUNCTION", size=0)
    
    # Many imports to b to make it a hub
    edge_1 = Relationship(source_id="src/app/main.py", target_id="src/lib/utils.py", type="IMPORTS")
    edge_2 = Relationship(source_id="frontend/index.js", target_id="src/lib/utils.py", type="IMPORTS")
    
    # 20 domains to trigger the >15 branches
    extra_nodes = []
    for i in range(20):
        extra_nodes.append(KnowledgeNode(id=f"src/domain{i}/file.py", name="file", path=f"src/domain{i}/file.py", type="FILE", size=0))
    
    mock_graph = KnowledgeGraph(nodes=[node_a, node_b, node_c, node_func] + extra_nodes, relationships=[edge_1, edge_2])
    
    mock_instance.build.return_value = mock_graph
    mock_validator.return_value.validate.return_value = mock_graph

    with runner.isolated_filesystem(temp_dir=tmp_path):
        result = runner.invoke(app, ["summary"])
        assert result.exit_code == 0
        assert "Repository Summary" in result.output
        assert "Total Files" in result.output
