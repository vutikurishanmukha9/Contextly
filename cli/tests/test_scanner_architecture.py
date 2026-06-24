import pytest
from pathlib import Path
from contextly.scanners.architecture import ArchitectureScanner
from contextly.scanners.base import ScannerError

def test_architecture_scanner_name():
    scanner = ArchitectureScanner()
    assert scanner.name == "Architecture Scanner"

def test_architecture_scanner_basic(tmp_path):
    (tmp_path / "src").mkdir()
    (tmp_path / "src" / "main.py").write_text("pass")
    
    scanner = ArchitectureScanner()
    res = scanner.scan(tmp_path)
    
    assert res.primary_pattern.name == "Monolith"

def test_architecture_scanner_domains(tmp_path):
    class MockDomain:
        def __init__(self, name, node_ids):
            self.name = name
            self.node_ids = node_ids
            
    domains = [
        MockDomain("api", [1, 2, 3, 4]),
        MockDomain("core", [1, 2, 3, 4]),
        MockDomain("db", [1, 2, 3, 4])
    ]
    
    scanner = ArchitectureScanner()
    res = scanner.scan(tmp_path, domains=domains)
    
    # Clean Architecture is inserted first, then Modular Architecture
    assert res.primary_pattern.name == "Clean Architecture"
    assert res.pattern_candidates[1].name == "Modular Architecture"

def test_architecture_scanner_exception(tmp_path, monkeypatch):
    from contextly.core.discovery.engine import DiscoveryEngine
    
    def mock_eval(*args, **kwargs):
        raise RuntimeError("Engine failed")
        
    monkeypatch.setattr(DiscoveryEngine, "evaluate_registry", mock_eval)
    
    scanner = ArchitectureScanner()
    with pytest.raises(ScannerError, match="failed"):
        scanner.scan(tmp_path)
