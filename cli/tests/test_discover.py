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

    result = runner.invoke(app, ["discover"])
    assert result.exit_code == 0
    assert "Pattern Discovery Complete" in result.stdout
    assert "TailwindCSS" in result.stdout or "React" in result.stdout


def test_discover_cmd_no_patterns(temp_repo):
    """Tests discovery output when no patterns can be inferred."""
    runner.invoke(app, ["init"])

    pkg_json = temp_repo / "package.json"
    if pkg_json.exists():
        pkg_json.unlink()

    result = runner.invoke(app, ["discover"])
    assert result.exit_code == 0
    assert "No recognizable architectural patterns or conventions discovered" in result.stdout


def test_discover_cmd_scanner_error(temp_repo, monkeypatch):
    """Tests pattern discovery when dependency/pattern scanner throws ScannerError."""
    runner.invoke(app, ["init"])

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

    from contextly.scanners.patterns import PatternScanner
    from contextly.utils.exceptions import ContextlyError

    def mock_scan(*args, **kwargs):
        raise ContextlyError("Internal contextly failure")

    monkeypatch.setattr(PatternScanner, "scan", mock_scan)

    result = runner.invoke(app, ["discover"])
    assert result.exit_code == 1
    assert "Context-Ly Error" in result.stdout


def test_discover_cmd_sorting(tmp_path, monkeypatch):
    """Tests that patterns are sorted by category alphabetically, and by confidence level descending within categories."""
    monkeypatch.chdir(tmp_path)
    runner.invoke(app, ["init"])

    from contextly.scanners.patterns import PatternScanner
    from contextly.scanners.dependencies import DependencyScanner
    from contextly.types.models import PatternScanResult, Pattern, DependencyScanResult

    def mock_scan_patterns(*args, **kwargs):
        res = PatternScanResult()
        # Out of order insertion across categories
        res.patterns.append(Pattern(name="LowStylingPattern", category="Styling", confidence="Low", description="Low styling description"))
        res.patterns.append(Pattern(name="HighStylingPattern", category="Styling", confidence="High", description="High styling description"))
        res.patterns.append(Pattern(name="MedStylingPattern", category="Styling", confidence="Medium", description="Medium styling description"))
        
        res.patterns.append(Pattern(name="LowStatePattern", category="State Management", confidence="Low", description="Low state description"))
        res.patterns.append(Pattern(name="HighStatePattern", category="State Management", confidence="High", description="High state description"))
        return res

    monkeypatch.setattr(DependencyScanner, "scan", lambda *args, **kwargs: DependencyScanResult())
    monkeypatch.setattr(PatternScanner, "scan", mock_scan_patterns)

    result = runner.invoke(app, ["discover"])
    assert result.exit_code == 0

    # Assert category printing order (State Management before Styling)
    state_cat_idx = result.stdout.index("State Management:")
    styling_cat_idx = result.stdout.index("Styling:")
    assert state_cat_idx < styling_cat_idx

    # Assert printing order of patterns within State Management (HighStatePattern before LowStatePattern)
    high_state_idx = result.stdout.index("HighStatePattern")
    low_state_idx = result.stdout.index("LowStatePattern")
    assert high_state_idx < low_state_idx

    # Assert printing order of patterns within Styling (High before Medium before Low)
    high_styling_idx = result.stdout.index("HighStylingPattern")
    med_styling_idx = result.stdout.index("MedStylingPattern")
    low_styling_idx = result.stdout.index("LowStylingPattern")
    assert high_styling_idx < med_styling_idx < low_styling_idx
