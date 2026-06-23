import pytest
from pathlib import Path
from contextly.scanners.dependencies import DependencyScanner
from contextly.scanners.base import ScannerError
import json
from unittest.mock import patch

def test_dependencies_package_json_not_relative(tmp_path):
    scanner = DependencyScanner()
    pkg = tmp_path / "package.json"
    root = tmp_path / "other"
    root.mkdir()
    
    # Not relative - FileNotFoundError branch
    scanner._parse_package_json(pkg, root, set(), strict=False)
    
    # Not relative - Exception branch
    pkg.write_text("{invalid")
    scanner._parse_package_json(pkg, root, set(), strict=False)

def test_dependencies_req_recursive(tmp_path):
    scanner = DependencyScanner()
    r1 = tmp_path / "req1.txt"
    r2 = tmp_path / "req2.txt"
    
    r1.write_text("-r req2.txt\nrequests")
    r2.write_text("-r req1.txt\nurllib3") # cyclic
    
    deps = set()
    scanner._parse_requirements_txt(r1, tmp_path, deps, strict=False)
    assert "requests" in deps
    assert "urllib3" in deps

def test_dependencies_pipfile_other_blocks(tmp_path):
    scanner = DependencyScanner()
    p = tmp_path / "Pipfile"
    p.write_text("[packages]\nrequests=1\n[dev-packages]\npytest=2\n[other]\nflask=3")
    deps = set()
    scanner._parse_pipfile(p, tmp_path, deps, strict=False)
    assert "requests" in deps
    assert "pytest" in deps
    assert "flask" not in deps

def test_dependencies_generic_exceptions(tmp_path):
    scanner = DependencyScanner()
    
    with patch("builtins.open", side_effect=ValueError("mock error")):
        with pytest.raises(ScannerError):
            scanner._parse_requirements_txt(tmp_path / "req.txt", tmp_path, set(), strict=True)
            
        with pytest.raises(ScannerError):
            scanner._parse_pyproject_toml(tmp_path / "pyproject.toml", tmp_path, set(), strict=True)
            
        with pytest.raises(ScannerError):
            scanner._parse_pipfile(tmp_path / "Pipfile", tmp_path, set(), strict=True)
