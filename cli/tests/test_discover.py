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
        res.patterns.append(Pattern(name="LowStylingPattern", category="Styling", confidence=0.5, description="Low styling description"))
        res.patterns.append(Pattern(name="HighStylingPattern", category="Styling", confidence=1.0, description="High styling description"))
        res.patterns.append(Pattern(name="MedStylingPattern", category="Styling", confidence=0.8, description="Medium styling description"))
        
        res.patterns.append(Pattern(name="LowStatePattern", category="State Management", confidence=0.5, description="Low state description"))
        res.patterns.append(Pattern(name="HighStatePattern", category="State Management", confidence=1.0, description="High state description"))
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

def test_path_regex_rule_word_boundaries():
    from contextly.core.discovery.rules.path import PathRegexRule
    
    # Standard \b regex
    rule = PathRegexRule(r'\b(auth|login)\b', 1.0)
    
    # Should match standard words
    res1 = rule.evaluate(["src/auth/index.ts"])
    assert res1.score_delta == 1.0
    
    # Should match snake_case
    res2 = rule.evaluate(["src/services/auth_service.py"])
    assert res2.score_delta == 1.0
    
    # Should match PascalCase
    res3 = rule.evaluate(["src/controllers/LoginController.ts"])
    assert res3.score_delta == 1.0
    
    # Should NOT match partial words
    res4 = rule.evaluate(["src/author/bio.ts"])
    assert res4.score_delta == 0.0

def test_discovery_engine_full_coverage(tmp_path):
    from contextly.core.discovery.engine import DiscoveryEngine
    from contextly.core.discovery.rules.path import PathRegexRule
    from contextly.types.models import RepositoryCapability, Discovery
    
    # Create some files and directories to be walked
    (tmp_path / "src").mkdir()
    (tmp_path / "src" / "main.py").write_text("print('hello')")
    (tmp_path / "node_modules").mkdir()
    (tmp_path / "node_modules" / "ignore.js").write_text("console.log('ignore')")
    (tmp_path / "test.egg-info").mkdir()
    (tmp_path / "test.egg-info" / "PKG-INFO").write_text("info")
    
    engine = DiscoveryEngine(tmp_path)
    
    # Test _load_paths by triggering evaluate_registry
    rule1 = PathRegexRule(r'main\.py', 1.0)
    registry1 = {"PythonMain": [rule1]}
    
    res1 = engine.evaluate_registry(registry1, discovery_class=RepositoryCapability, source_name="Test")
    assert len(res1) == 1
    assert res1[0].capability == "PythonMain"
    assert res1[0].confidence == 1.0
    assert len(res1[0].evidence) == 1
    
    # Test discovery_class == Discovery
    res2 = engine.evaluate_registry(registry1, discovery_class=Discovery, source_name="Test")
    assert len(res2) == 1
    assert res2[0].name == "PythonMain"
    assert res2[0].generated_by == "Test"
    
    # Test top 5 evidence limit
    engine2 = DiscoveryEngine(tmp_path)
    (tmp_path / "utils").mkdir()
    for i in range(10):
        (tmp_path / "utils" / f"file{i}.py").write_text("pass")
        
    rule2 = PathRegexRule(r'file\d+\.py', 0.2)
    res3 = engine2.evaluate_registry({"ManyFiles": [rule2]}, discovery_class=Discovery)
    assert len(res3) == 1
    assert res3[0].confidence == 0.2 # 0.2 * 1 rule = 0.2
    assert len(res3[0].evidence) == 5 # Limited to 5


def test_discovery_engine_refreshes_full_repo_paths(tmp_path):
    from contextly.core.discovery.engine import DiscoveryEngine
    from contextly.core.discovery.rules.path import PathRegexRule

    (tmp_path / "src").mkdir()
    (tmp_path / "src" / "main.py").write_text("print('hello')")

    engine = DiscoveryEngine(tmp_path)
    assert engine.evaluate_registry({"Main": [PathRegexRule(r"main\.py", 1.0)]})

    (tmp_path / "src" / "newfeature.py").write_text("print('new')")
    result = engine.evaluate_registry({"NewFeature": [PathRegexRule(r"newfeature\.py", 1.0)]})

    assert len(result) == 1
    assert result[0].name == "NewFeature"

