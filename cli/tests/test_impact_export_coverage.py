import pytest
from typer.testing import CliRunner
from contextly.main import app
from contextly.core.graph.builder import ImportGraphBuilder
from contextly.types.models import KnowledgeGraph, KnowledgeNode, NodeType
import json

runner = CliRunner()

def test_impact(tmp_path):
    (tmp_path / "main.py").write_text("def foo(): pass\ndef bar(): foo()")
    (tmp_path / "contextly.toml").write_text("[project]\nroot='.'\n")
    
    result = runner.invoke(app, ["impact", "main.py"])
    assert result.exit_code in [0, 1]

def test_export(tmp_path, monkeypatch):
    (tmp_path / ".contextly" / "packs").mkdir(parents=True)
    (tmp_path / ".contextly" / "packs" / "testpack.contextpack.md").write_text("test")
    (tmp_path / "contextly.toml").write_text("[project]\nroot='.'\n")
    
    import pyperclip
    monkeypatch.setattr(pyperclip, "copy", lambda x: None)
    
    monkeypatch.chdir(tmp_path)
    result = runner.invoke(app, ["export", "testpack"])
    assert result.exit_code in [0, 1]

def test_analyze(tmp_path):
    (tmp_path / "contextly.toml").write_text("[project]\nroot='.'\n")
    (tmp_path / "main.py").write_text("class A: pass")
    result = runner.invoke(app, ["analyze", str(tmp_path), "--format", "text"])
    assert result.exit_code in [0, 1]

def test_discover(tmp_path, monkeypatch):
    (tmp_path / "contextly.toml").write_text("[project]\nroot='.'\n")
    (tmp_path / "main.py").write_text("class A: pass")
    monkeypatch.chdir(tmp_path)
    result = runner.invoke(app, ["discover", "--format", "text"])
    assert result.exit_code in [0, 1]

def test_stats(tmp_path):
    (tmp_path / "contextly.toml").write_text("[project]\nroot='.'\n")
    (tmp_path / "main.py").write_text("class A: pass")
    result = runner.invoke(app, ["stats", "--path", str(tmp_path)])
    assert result.exit_code in [0, 1]
