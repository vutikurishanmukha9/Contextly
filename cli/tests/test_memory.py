import pytest
import yaml
from typer.testing import CliRunner
from contextly.main import app
from conftest import runner

def test_memory_uninitialized(temp_repo):
    """Verifies memory command fails when not initialized."""
    res = runner.invoke(app, ["memory"])
    assert res.exit_code == 1
    assert "Context-Ly is not initialized" in res.stdout or "Error:" in res.stdout


def test_memory_cmd_empty(temp_repo):
    """Tests memory command initially when no conventions have been stored."""
    runner.invoke(app, ["init"])
    runner.invoke(app, ["analyze"]) # Initialize first
    
    result = runner.invoke(app, ["memory"])
    assert result.exit_code == 0
    assert "memory is currently empty" in result.stdout


def test_memory_cmd_with_rules(temp_repo):
    """Tests memory command when rules of varying confidence levels are stored."""
    runner.invoke(app, ["init"])
    runner.invoke(app, ["analyze"])
    
    # Learn some rules
    runner.invoke(app, ["learn", "--auto"], input="y\n")
    
    # Verify memory lists the rules
    result = runner.invoke(app, ["memory"])
    assert result.exit_code == 0
    assert "Stored Memory" in result.stdout
    assert "Found" in result.stdout
    assert "TailwindCSS" in result.stdout or "React" in result.stdout


def test_memory_cmd_corrupted_yaml(temp_repo):
    """Tests that MemoryEngine loads safely if rules.yaml is corrupted or has bad format."""
    runner.invoke(app, ["init"])
    runner.invoke(app, ["analyze"]) # Initialize first
    
    rules_file = temp_repo / ".contextly" / "memory" / "rules.yaml"
    rules_file.parent.mkdir(parents=True, exist_ok=True)
    rules_file.write_text("{corrupt-yaml : [ invalid }", encoding="utf-8")
    
    # Gracefully loads empty memory
    result = runner.invoke(app, ["memory"])
    assert result.exit_code == 0
    assert "memory is currently empty" in result.stdout
