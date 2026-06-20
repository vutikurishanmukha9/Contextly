import json
from typer.testing import CliRunner
from contextly.main import app

runner = CliRunner()

def test_stats_command_json(tmp_path):
    # Create some mock files
    (tmp_path / "src").mkdir()
    (tmp_path / "src" / "test.py").write_text("def my_func(): return True\ndef another_func(): my_func()")
    
    result = runner.invoke(app, ["stats", "--path", str(tmp_path), "--json"])
    assert result.exit_code == 0
    
    data = json.loads(result.stdout)
    assert isinstance(data, list)
    
    # Check that we have the expected providers and metrics
    providers = {item["provider"] for item in data}
    assert "Topology" in providers
    assert "Resolution" in providers
    assert "Validation" in providers
    assert "Complexity" in providers
    assert "Health" in providers
    assert "Performance" in providers
    
    # Check that graph topology found our files
    files_analyzed = next((m for m in data if m["metric"] == "files_analyzed"), None)
    assert files_analyzed is not None
    assert files_analyzed["value"] >= 1

def test_stats_command_rich(tmp_path):
    (tmp_path / "src").mkdir()
    (tmp_path / "src" / "test.py").write_text("class MyClass:\n  pass\n")
    
    result = runner.invoke(app, ["stats", "--path", str(tmp_path)])
    assert result.exit_code == 0
    
    output = result.stdout
    assert "Repository Health Report" in output
    assert "Repository Health Score:" in output
    assert "Graph Topology" in output
    assert "Performance" in output
    assert "Resolution Quality" in output
    assert "Diagnostics & Quality Gate" in output
