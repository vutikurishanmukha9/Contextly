import pytest
from typer.testing import CliRunner
from contextly.main import app
from contextly.scanners.dependencies import DependencyScanner
from contextly.scanners.patterns import PatternScanner
from contextly.core.discovery.engine import DiscoveryEngine
from contextly.scanners.base import ScannerError
from contextly.utils.exceptions import ContextlyError, ValidationError

@pytest.fixture
def runner():
    return CliRunner()

def test_discover_uninitialized_json(temp_repo, runner):
    res = runner.invoke(app, ["discover", "--format", "json"])
    assert res.exit_code == 1
    assert "error" in res.stdout

def test_discover_cmd_success_json(temp_repo, runner):
    runner.invoke(app, ["init"])
    result = runner.invoke(app, ["discover", "--format", "json"])
    assert result.exit_code == 0
    assert "name" in result.stdout

def test_discover_cmd_scanner_error_json(temp_repo, monkeypatch, runner):
    runner.invoke(app, ["init"])
    def mock_scan(*args, **kwargs):
        raise ScannerError("Failed scanner")
    monkeypatch.setattr(DependencyScanner, "scan", mock_scan)
    result = runner.invoke(app, ["discover", "--format", "json"])
    assert result.exit_code == 1
    assert "error" in result.stdout
    assert "Scanner Error" in result.stdout

def test_discover_cmd_contextly_error_json(temp_repo, monkeypatch, runner):
    runner.invoke(app, ["init"])
    def mock_scan(*args, **kwargs):
        raise ContextlyError("Internal")
    monkeypatch.setattr(PatternScanner, "scan", mock_scan)
    result = runner.invoke(app, ["discover", "--format", "json"])
    assert result.exit_code == 1
    assert "error" in result.stdout
    assert "Context-Ly Error" in result.stdout

def test_discover_cmd_general_error(temp_repo, monkeypatch, runner):
    runner.invoke(app, ["init"])
    def mock_discover(self):
        raise RuntimeError("General")
    monkeypatch.setattr(DiscoveryEngine, "discover", mock_discover)
    result = runner.invoke(app, ["discover"])
    assert result.exit_code == 1
    assert "Error: General" in result.stdout

def test_discover_cmd_general_error_json(temp_repo, monkeypatch, runner):
    runner.invoke(app, ["init"])
    def mock_discover(self):
        raise RuntimeError("General")
    monkeypatch.setattr(DiscoveryEngine, "discover", mock_discover)
    result = runner.invoke(app, ["discover", "--format", "json"])
    assert result.exit_code == 1
    assert "error" in result.stdout
    assert "General" in result.stdout
