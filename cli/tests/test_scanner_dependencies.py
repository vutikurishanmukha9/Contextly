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
[project.optional-dependencies]
dev = ["pytest>=7.0", "black"]
''')
    
    scanner = DependencyScanner()
    result = scanner.scan(temp_project_dir)
    assert "typer" in result.python
    assert "rich" in result.python
    assert "pytest" in result.python
    assert "black" in result.python

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
    
    # No longer creating dead files that are not parsed by the scanner
    
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
    
    import contextly.scanners.dependencies as dep_module
    monkeypatch.setattr(dep_module, "tomllib", None)
    with pytest.raises(ScannerError):
        s.scan(tmp_path)
    monkeypatch.undo()
    
    # sub-dir package.json
    sub = tmp_path / "frontend"
    sub.mkdir()
    (sub / "package.json").write_text('{"dependencies": {"lodash": "1"}}')
    s.scan(tmp_path)
    
    # global exception - mock os.walk since the scanner uses it
    import os as _os
    def mock_walk(*args, **kwargs):
        raise Exception("Global crash")
    monkeypatch.setattr(_os, "walk", mock_walk)
    try:
        with pytest.raises(ScannerError):
            s.scan(tmp_path)
    finally:
        monkeypatch.undo()

    # Test Exception blocks in _parse_* methods
    import builtins
    
    # Mock open to raise Exception for package.json
    def mock_open_gen_exception(*args, **kwargs):
        if "package.json" in str(args[0]):
            raise Exception("Unexpected error")
        elif "requirements.txt" in str(args[0]):
            raise Exception("Unexpected error req")
        elif "pyproject.toml" in str(args[0]):
            raise Exception("Unexpected error toml")
        elif "Pipfile" in str(args[0]):
            raise Exception("Unexpected error pipfile")
        return original_open(*args, **kwargs)
        
    monkeypatch.setattr(builtins, "open", mock_open_gen_exception)
    (tmp_path / "package.json").write_text('{}')
    (tmp_path / "requirements.txt").write_text('flask')
    (tmp_path / "pyproject.toml").write_text('')
    (tmp_path / "Pipfile").write_text('')
    
    s.scan(tmp_path)
    monkeypatch.undo()
    
    # Test PermissionError for requirements.txt, pyproject.toml, Pipfile
    def mock_open_permission_error(*args, **kwargs):
        if "requirements.txt" in str(args[0]):
            raise PermissionError("Denied req")
        elif "pyproject.toml" in str(args[0]):
            raise PermissionError("Denied toml")
        elif "Pipfile" in str(args[0]):
            raise PermissionError("Denied pipfile")
        return original_open(*args, **kwargs)
        
    monkeypatch.setattr(builtins, "open", mock_open_permission_error)
    s.scan(tmp_path)
    monkeypatch.undo()

def test_dependency_scanner_file_paths(tmp_path):
    s = DependencyScanner()
    
    # Create the files
    (tmp_path / "package.json").write_text('{"dependencies": {"react": "1"}}')
    (tmp_path / "requirements.txt").write_text("flask!=1.0\n# comment")
    (tmp_path / "pyproject.toml").write_text('[project]\ndependencies=["requests~=2.0"]')
    (tmp_path / "Pipfile").write_text('[packages]\ndjango = "*"\n')
    
    file_paths = [
        "package.json",
        "requirements.txt",
        "pyproject.toml",
        "Pipfile"
    ]
    
    res = s.scan(tmp_path, file_paths=file_paths)
    assert "react" in res.npm
    assert "flask" in res.python
    assert "requests" in res.python
    assert "django" in res.python
    
    # Also test Poetry tools.poetry.dependencies
    (tmp_path / "pyproject.toml").write_text('[tool.poetry.dependencies]\nfastapi="0.100.0"\n')
    res2 = s.scan(tmp_path, file_paths=["pyproject.toml"])
    assert "fastapi" in res2.python
    
    # Also test Pipfile with missing packages section
    (tmp_path / "Pipfile").write_text('[dev-packages]\npytest = "*"\n')
    res3 = s.scan(tmp_path, file_paths=["Pipfile"])
    assert "pytest" in res3.python

