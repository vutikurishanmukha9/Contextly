import pytest
import yaml
from typer.testing import CliRunner
from contextly.main import app
from conftest import runner

def test_learn_uninitialized(temp_repo):
    """Verifies learn fails when not initialized."""
    res = runner.invoke(app, ["learn", "--auto"])
    assert res.exit_code == 1
    assert "Context-Ly is not initialized" in res.stdout or "Error:" in res.stdout


def test_learn_cmd_manual_disabled(temp_repo):
    """Tests that learn command without --auto outputs manual learning disabled warning."""
    runner.invoke(app, ["init"])
    runner.invoke(app, ["analyze"]) # Initialize first
    
    result = runner.invoke(app, ["learn"])
    assert result.exit_code == 0
    assert "Manual learning is currently disabled" in result.stdout


def test_learn_cmd_auto_confirm_all(temp_repo):
    """Tests learn --auto with interactive confirmation to save conventions."""
    runner.invoke(app, ["init"])
    runner.invoke(app, ["analyze"])
    
    result = runner.invoke(app, ["learn", "--auto"], input="y\n")
    assert result.exit_code == 0
    assert "Discovered Conventions:" in result.stdout
    assert "Saved to memory." in result.stdout
    assert "Successfully saved" in result.stdout
    
    rules_file = temp_repo / ".contextly" / "memory" / "rules.yaml"
    assert rules_file.exists()
    
    content = yaml.safe_load(rules_file.read_text(encoding="utf-8"))
    assert "rules" in content
    assert len(content["rules"]) > 0


def test_learn_cmd_auto_skip(temp_repo):
    """Tests learn --auto when user chooses to skip conventions."""
    runner.invoke(app, ["init"])
    runner.invoke(app, ["analyze"])
    
    result = runner.invoke(app, ["learn", "--auto"], input="n\n")
    assert result.exit_code == 0
    assert "Skipped." in result.stdout
    assert "No new rules were saved" in result.stdout


def test_learn_cmd_auto_duplicate(temp_repo):
    """Tests that duplicate conventions are skipped and not saved repeatedly."""
    runner.invoke(app, ["init"])
    runner.invoke(app, ["analyze"])
    
    runner.invoke(app, ["learn", "--auto"], input="y\n")
    
    result = runner.invoke(app, ["learn", "--auto"], input="y\n")
    assert result.exit_code == 0
    assert "Already in memory" in result.stdout


def test_learn_cmd_auto_no_patterns(temp_repo):
    """Tests learn --auto when no recognizable conventions are found in the codebase."""
    runner.invoke(app, ["init"])
    runner.invoke(app, ["analyze"])
    
    pkg_json = temp_repo / "package.json"
    if pkg_json.exists():
        pkg_json.unlink()
        
    result = runner.invoke(app, ["learn", "--auto"])
    assert result.exit_code == 0
    assert "No new recognizable conventions discovered to learn" in result.stdout


def test_learn_cmd_auto_save_permission_error(temp_repo, monkeypatch):
    """Tests permission error exception propagation when writing learned rules to rules.yaml."""
    runner.invoke(app, ["init"])
    runner.invoke(app, ["analyze"])
    
    import builtins
    original_open = builtins.open
    def mock_open(*args, **kwargs):
        path_str = str(args[0]) if args else ""
        if "rules.yaml" in path_str:
            mode = kwargs.get("mode", "")
            if not mode and len(args) > 1:
                mode = str(args[1])
            if "w" in mode:
                raise PermissionError("Write Permission Denied")
        return original_open(*args, **kwargs)
        
    monkeypatch.setattr(builtins, "open", mock_open)
    
    result = runner.invoke(app, ["learn", "--auto"], input="y\n")
    assert result.exit_code == 1 or "Error" in result.stdout or result.exception is not None


def test_learn_cmd_scanner_error(temp_repo, monkeypatch):
    """Tests learn command scanner error exception handling."""
    runner.invoke(app, ["init"])
    runner.invoke(app, ["analyze"])
    
    import contextly.scanners.patterns as pat_mod
    from contextly.scanners.base import ScannerError
    
    def mock_scan(*args, **kwargs):
        raise ScannerError("Scanner mock failed")
        
    monkeypatch.setattr(pat_mod.PatternScanner, "scan", mock_scan)
    result = runner.invoke(app, ["learn", "--auto"])
    assert result.exit_code == 1
    assert "Scanner Error" in result.stdout


def test_learn_cmd_contextly_error(temp_repo, monkeypatch):
    """Tests learn command contextly error exception handling."""
    runner.invoke(app, ["init"])
    runner.invoke(app, ["analyze"])
    
    import contextly.scanners.patterns as pat_mod
    from contextly.utils.exceptions import ContextlyError
    
    def mock_scan(*args, **kwargs):
        raise ContextlyError("Contextly mock failed")
        
    monkeypatch.setattr(pat_mod.PatternScanner, "scan", mock_scan)
    result = runner.invoke(app, ["learn", "--auto"])
    assert result.exit_code == 1
    assert "Context-Ly Error" in result.stdout

