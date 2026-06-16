import pytest
import yaml
from typer.testing import CliRunner
from contextly.main import app
from conftest import runner
from contextly.core.memory.engine import MemoryEngine

def test_memory_uninitialized(temp_repo):
    """Verifies memory command fails when not initialized."""
    res = runner.invoke(app, ["memory"])
    assert res.exit_code == 1
    assert "Context-Ly is not initialized" in res.stdout or "Error:" in res.stdout


def test_memory_cmd_empty(temp_repo):
    """Tests memory command initially when no conventions have been stored."""
    runner.invoke(app, ["init"])

    result = runner.invoke(app, ["memory"])
    assert result.exit_code == 0
    assert "memory is currently empty" in result.stdout


def test_memory_cmd_with_rules(temp_repo):
    """Tests memory command when rules of varying confidence levels are stored."""
    runner.invoke(app, ["init"])

    # Learn some rules
    runner.invoke(app, ["learn", "--auto"], input="y\n")

    # Verify memory lists the rules
    result = runner.invoke(app, ["memory"])
    assert result.exit_code == 0
    assert "Stored Memory" in result.stdout
    assert "Found" in result.stdout
    assert "[rule_" in result.stdout
    assert "TailwindCSS" in result.stdout or "React" in result.stdout


def test_memory_cmd_corrupted_yaml(temp_repo):
    """Tests that MemoryEngine loads safely if rules.yaml is corrupted or has bad format."""
    runner.invoke(app, ["init"])

    rules_file = temp_repo / ".contextly" / "memory" / "rules.yaml"
    rules_file.parent.mkdir(parents=True, exist_ok=True)
    rules_file.write_text("{corrupt-yaml : [ invalid }", encoding="utf-8")

    # Gracefully loads empty memory
    result = runner.invoke(app, ["memory"])
    assert result.exit_code == 0
    assert "memory is currently empty" in result.stdout


def test_memory_cmd_sorting(temp_repo):
    """Tests that memory command sorts categories alphabetically and rules within them by confidence descending."""
    runner.invoke(app, ["init"])

    # Manually write out-of-order categories/rules to rules.yaml
    rules_file = temp_repo / ".contextly" / "memory" / "rules.yaml"
    rules_file.parent.mkdir(parents=True, exist_ok=True)
    
    mock_rules = {
        "rules": [
            {
                "id": "rule_low_styling",
                "category": "Styling",
                "rule": "Low Styling Rule",
                "confidence": 0.5,
                "source": "discovered",
                "created_at": "2026-06-12"
            },
            {
                "id": "rule_high_styling",
                "category": "Styling",
                "rule": "High Styling Rule",
                "confidence": 1.0,
                "source": "discovered",
                "created_at": "2026-06-12"
            },
            {
                "id": "rule_high_state",
                "category": "State Management",
                "rule": "High State Rule",
                "confidence": 1.0,
                "source": "discovered",
                "created_at": "2026-06-12"
            }
        ]
    }
    with open(rules_file, "w", encoding="utf-8") as f:
        yaml.dump(mock_rules, f)

    result = runner.invoke(app, ["memory"])
    assert result.exit_code == 0

    # State Management (starts with Sta) comes before Styling (starts with Sty)
    state_idx = result.stdout.index("State Management")
    styling_idx = result.stdout.index("Styling")
    assert state_idx < styling_idx

    # High Styling Rule comes before Low Styling Rule
    high_styling_idx = result.stdout.index("High Styling Rule")
    low_styling_idx = result.stdout.index("Low Styling Rule")
    assert high_styling_idx < low_styling_idx


def test_memory_add_rule_deduplicates_named_and_unnamed_rules(temp_repo):
    runner.invoke(app, ["init"])
    engine = MemoryEngine(temp_repo)

    assert engine.add_rule("Styling", "Uses TailwindCSS.", 1.0, "test", name="TailwindCSS")
    assert not engine.add_rule("Styling", "Uses TailwindCSS.", 1.0, "test")

    memory = engine.load_memory()
    assert len(memory.rules) == 1
    assert "+" in memory.rules[0].created_at
