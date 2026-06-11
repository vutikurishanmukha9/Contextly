import pytest
import tempfile
import json
from pathlib import Path
from typer.testing import CliRunner

from contextly.main import app

runner = CliRunner()

@pytest.fixture
def temp_repo(monkeypatch):
    with tempfile.TemporaryDirectory() as d:
        path = Path(d)
        (path / "src").mkdir()
        (path / "src" / "index.js").write_text("console.log('test')")
        (path / "package.json").write_text(json.dumps({"dependencies": {"react": "18.0.0", "tailwindcss": "3.0.0"}}))
        
        # Patch the working directory so CLI commands run inside temp_repo
        monkeypatch.chdir(path)
        
        yield path

def test_init_cmd(temp_repo):
    result = runner.invoke(app, ["init"], catch_exceptions=False)
    assert result.exit_code == 0
    assert "Contextly initialized successfully!" in result.stdout
    assert (temp_repo / ".contextly" / "config.yaml").exists()

def test_analyze_cmd_claude(temp_repo):
    print("running init")
    runner.invoke(app, ["init"])
    print("running analyze")
    result = runner.invoke(app, ["analyze", "--model", "claude"])
    print("analyze done", result.stdout, result.exception)
    assert result.exit_code == 0
    assert "Repository scan complete" in result.stdout
    
    ctx_path = temp_repo / "PROJECT_CONTEXT.md"
    assert ctx_path.exists()
    
    content = ctx_path.read_text(encoding="utf-8")
    assert "<project_context>" in content

def test_analyze_cmd_chatgpt(temp_repo):
    runner.invoke(app, ["init"])
    result = runner.invoke(app, ["analyze", "--model", "chatgpt"])
    assert result.exit_code == 0
    
    ctx_path = temp_repo / "PROJECT_CONTEXT.md"
    assert ctx_path.exists()
    
    content = ctx_path.read_text(encoding="utf-8")
    assert "## Stack Identity" in content

def test_pack_cmd(temp_repo):
    runner.invoke(app, ["init"])
    result = runner.invoke(app, ["pack", "src", "--name", "frontend"])
    assert result.exit_code == 0
    assert "Context Pack 'frontend' created!" in result.stdout
    
    pack_path = temp_repo / ".contextly" / "packs" / "frontend.contextpack.md"
    assert pack_path.exists()
    content = pack_path.read_text(encoding="utf-8")
    assert "## File: `src/index.js`" in content

def test_export_cmd_validation(temp_repo):
    # Try exporting without PROJECT_CONTEXT.md
    result = runner.invoke(app, ["export", "frontend"])
    assert result.exit_code == 1
    assert "Context-Ly is not initialized" in result.stdout

def test_export_cmd_success(temp_repo):
    runner.invoke(app, ["init"])
    runner.invoke(app, ["analyze"])
    runner.invoke(app, ["pack", "src", "--name", "frontend"])
    
    result = runner.invoke(app, ["export", "frontend"])
    assert result.exit_code == 0
    
    exports_dir = temp_repo / ".contextly" / "exports"
    exports = list(exports_dir.glob("*.md"))
    assert len(exports) == 1
    
    fused_content = exports[0].read_text(encoding="utf-8")
    assert "Architecture Map" in fused_content
    assert "<context_pack name=\"frontend\">" in fused_content

def test_discover_cmd(temp_repo):
    runner.invoke(app, ["init"])
    result = runner.invoke(app, ["discover"])
    assert result.exit_code == 0
    assert "Pattern Discovery Complete" in result.stdout
    assert "TailwindCSS" in result.stdout

def test_inspect_cmd(temp_repo):
    runner.invoke(app, ["init"])
    result = runner.invoke(app, ["inspect"])
    assert result.exit_code == 0
    assert "Inspection complete" in result.stdout
    assert "package.json" in result.stdout

def test_learn_cmd_auto(temp_repo):
    runner.invoke(app, ["init"])
    # We provide 'y\n' to simulate confirming the discovered 'TailwindCSS' pattern
    result = runner.invoke(app, ["learn", "--auto"], input="y\n")
    assert result.exit_code == 0
    assert "Successfully saved 1 rules" in result.stdout

def test_memory_cmd(temp_repo):
    runner.invoke(app, ["init"])
    # Empty memory initially
    res1 = runner.invoke(app, ["memory"])
    assert res1.exit_code == 0
    assert "memory is currently empty" in res1.stdout
    
    # Learn a convention
    runner.invoke(app, ["learn", "--auto"], input="y\n")
    
    # Now it should have 1 rule
    res2 = runner.invoke(app, ["memory"])
    assert res2.exit_code == 0
    assert "Stored Memory" in res2.stdout
    assert "Found 1 rules" in res2.stdout
    assert "TailwindCSS" in res2.stdout
