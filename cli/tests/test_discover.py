import pytest
from typer.testing import CliRunner
from contextly.main import app
from conftest import runner

def test_discover_uninitialized(temp_repo):
    """Verifies discover fails when not initialized."""
    res = runner.invoke(app, ["discover"])
    assert res.exit_code == 1
    assert "Context-Ly is not initialized" in res.stdout or "Error:" in res.stdout


def test_discover_cmd_success(temp_repo):
    """Tests successful pattern discovery when a repo has dependencies and matched conventions."""
    runner.invoke(app, ["init"])
    runner.invoke(app, ["analyze"])
    
    result = runner.invoke(app, ["discover"])
    assert result.exit_code == 0
    assert "Pattern Discovery Complete" in result.stdout
    assert "TailwindCSS" in result.stdout or "React" in result.stdout


def test_discover_cmd_no_patterns(temp_repo):
    """Tests discovery output when no patterns can be inferred."""
    runner.invoke(app, ["init"])
    runner.invoke(app, ["analyze"])
    
    pkg_json = temp_repo / "package.json"
    if pkg_json.exists():
        pkg_json.unlink()
        
    result = runner.invoke(app, ["discover"])
    assert result.exit_code == 0
    assert "No recognizable architectural patterns or conventions discovered" in result.stdout


def test_discover_cmd_scanner_error(temp_repo, monkeypatch):
    """Tests pattern discovery when dependency/pattern scanner throws ScannerError."""
    runner.invoke(app, ["init"])
    runner.invoke(app, ["analyze"]) # Initialize first
    
    from contextly.scanners.dependencies import DependencyScanner
    from contextly.scanners.base import ScannerError
    
    def mock_scan(*args, **kwargs):
        raise ScannerError("Failed scanner system call")
        
    monkeypatch.setattr(DependencyScanner, "scan", mock_scan)
    
    result = runner.invoke(app, ["discover"])
    assert result.exit_code == 1
    assert "Scanner Error" in result.stdout


def test_discover_cmd_contextly_error(temp_repo, monkeypatch):
    """Tests pattern discovery when dependency/pattern scanner throws ContextlyError."""
    runner.invoke(app, ["init"])
    runner.invoke(app, ["analyze"]) # Initialize first
    
    from contextly.scanners.patterns import PatternScanner
    from contextly.utils.exceptions import ContextlyError
    
    def mock_scan(*args, **kwargs):
        raise ContextlyError("Internal contextly failure")
        
    monkeypatch.setattr(PatternScanner, "scan", mock_scan)
    
    result = runner.invoke(app, ["discover"])
    assert result.exit_code == 1
    assert "Context-Ly Error" in result.stdout


def test_discover_cmd_sorting(temp_repo, monkeypatch):
    """Tests that patterns are sorted by confidence level descending within categories."""
    runner.invoke(app, ["init"])
    
    from contextly.scanners.patterns import PatternScanner
    from contextly.types.models import PatternScanResult, Pattern
    
    def mock_scan(*args, **kwargs):
        res = PatternScanResult()
        # Out of order insertion
        res.patterns.append(Pattern(name="LowPattern", category="Styling", confidence="Low", description="Low description"))
        res.patterns.append(Pattern(name="HighPattern", category="Styling", confidence="High", description="High description"))
        res.patterns.append(Pattern(name="MediumPattern", category="Styling", confidence="Medium", description="Medium description"))
        return res
        
    monkeypatch.setattr(PatternScanner, "scan", mock_scan)
    
    result = runner.invoke(app, ["discover"])
    assert result.exit_code == 0
    
    # Assert printing order of patterns in stdout
    high_idx = result.stdout.index("HighPattern")
    med_idx = result.stdout.index("MediumPattern")
    low_idx = result.stdout.index("LowPattern")
    assert high_idx < med_idx < low_idx

