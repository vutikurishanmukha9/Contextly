import pytest
import tempfile
import json
from pathlib import Path

from contextly.scanners.dependencies import DependencyScanner
from contextly.scanners.base import ScannerError
from contextly.types.models import DependencyScanResult

@pytest.fixture
def temp_project_dir():
    with tempfile.TemporaryDirectory() as d:
        yield Path(d)

def test_dependency_scanner_empty(temp_project_dir):
    scanner = DependencyScanner()
    result = scanner.scan(temp_project_dir)
    assert len(result.npm) == 0
    assert len(result.python) == 0

def test_dependency_scanner_package_json(temp_project_dir):
    pkg_json = temp_project_dir / "package.json"
    pkg_json.write_text(json.dumps({
        "dependencies": {"react": "18.0.0"},
        "devDependencies": {"typescript": "5.0.0"}
    }))
    
    scanner = DependencyScanner()
    result = scanner.scan(temp_project_dir)
    assert "react" in result.npm
    assert "typescript" in result.npm

def test_dependency_scanner_malformed_json(temp_project_dir):
    pkg_json = temp_project_dir / "package.json"
    pkg_json.write_text("{ malformed: true ") # Invalid JSON
    
    # Should not crash
    scanner = DependencyScanner()
    result = scanner.scan(temp_project_dir)
    assert len(result.npm) == 0

def test_dependency_scanner_pyproject_toml(temp_project_dir):
    toml_path = temp_project_dir / "pyproject.toml"
    toml_path.write_text('''
[project]
name = "test"
dependencies = [
    "typer>=0.12.0",
    "rich"
]
    ''')
    
    scanner = DependencyScanner()
    result = scanner.scan(temp_project_dir)
    assert "typer" in result.python
    assert "rich" in result.python

def test_dependency_scanner_malformed_toml(temp_project_dir):
    toml_path = temp_project_dir / "pyproject.toml"
    toml_path.write_text('[project\ninvalid') # Invalid TOML
    
    # Should not crash
    scanner = DependencyScanner()
    result = scanner.scan(temp_project_dir)
    assert len(result.python) == 0

def test_dependency_scanner_edge_cases(tmp_path):
    """Covers dependencies.py 11-12, 17, 35-36, 47-49, 61-64, 81, 83, 90-91."""
    s = DependencyScanner()
    assert s.name == "Dependency Scanner"
    
    # Invalid package.json
    pkg = tmp_path / "package.json"
    pkg.write_text("{invalid_json}")
    s.scan(tmp_path)
    
    # valid package.json with devDeps
    pkg.write_text(json.dumps({"dependencies": {"react": "1"}, "devDependencies": {"jest": "1"}}))
    
    # pyproject.toml valid
    pyproj = tmp_path / "pyproject.toml"
    pyproj.write_text('[project]\ndependencies=["requests"]')
    
    # requirements.txt
    req = tmp_path / "requirements.txt"
    req.write_text("flask==1.0\n# comment\ndjango")
    
    s.scan(tmp_path)
    
    # Missing dependencies
    
    # 47-49: Cargo.toml
    cargo = tmp_path / "Cargo.toml"
    cargo.write_text("[dependencies]\nreqwest = \"1.0\"")
    
    # 61-64: go.mod
    gomod = tmp_path / "go.mod"
    gomod.write_text("module test\nrequire (\n gin v1.0\n)")
    
    # 81, 83, 90-91: pipfile, poetry
    pipfile = tmp_path / "Pipfile"
    pipfile.write_text("[packages]\nflask = \"*\"")
    
    poetry = tmp_path / "poetry.lock"
    poetry.write_text("[[package]]\nname = \"fastapi\"")
    
    # package.json
    pkg = tmp_path / "package.json"
    pkg.write_text(json.dumps({"dependencies": {"react": "1"}, "devDependencies": {"jest": "1"}}))
    
    s.scan(tmp_path)

def test_dependency_scanner_exceptions(tmp_path, monkeypatch):
    """Covers dependencies.py multiple lines."""
    s = DependencyScanner()
    
    # Permission error while reading pyproject.toml
    import builtins
    original_open = builtins.open
    def mock_open(*args, **kwargs):
        if "pyproject.toml" in str(args[0]):
            raise PermissionError("Denied")
        return original_open(*args, **kwargs)
    monkeypatch.setattr(builtins, "open", mock_open)
    
    (tmp_path / "pyproject.toml").write_text('[project]')
    s.scan(tmp_path)
    monkeypatch.undo()
    
    # tomli is None
    import contextly.scanners.dependencies as dep_module
    monkeypatch.setattr(dep_module, "tomli", None)
    s.scan(tmp_path)
    monkeypatch.undo()
    
    # sub-dir package.json
    sub = tmp_path / "frontend"
    sub.mkdir()
    (sub / "package.json").write_text('{"dependencies": {"lodash": "1"}}')
    s.scan(tmp_path)
    
    # global exception
    import pathlib
    def mock_iterdir(*args, **kwargs):
        raise Exception("Global crash")
    monkeypatch.setattr(pathlib.Path, "iterdir", mock_iterdir)
    try:
        with pytest.raises(ScannerError):
            s.scan(tmp_path)
    finally:
        monkeypatch.undo()
    
    # Test permission error in iterdir
    original_iterdir = pathlib.Path.iterdir
    def mock_iterdir2(self):
        if self.name == "forbidden_dir":
            raise PermissionError("Access denied")
        return original_iterdir(self)
    monkeypatch.setattr(pathlib.Path, "iterdir", mock_iterdir2)
    
    f_dir = tmp_path / "forbidden_dir"
    f_dir.mkdir()
    s.scan(tmp_path)
