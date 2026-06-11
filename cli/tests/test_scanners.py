import pytest
import tempfile
import json
from pathlib import Path

from contextly.scanners.dependencies import DependencyScanner
from contextly.scanners.language import LanguageScanner

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

def test_language_scanner(temp_project_dir):
    (temp_project_dir / "main.py").write_text("print('hello')")
    (temp_project_dir / "utils.py").write_text("pass")
    (temp_project_dir / "index.js").write_text("console.log('hi')")
    
    scanner = LanguageScanner()
    result = scanner.scan(temp_project_dir)
    
    assert result.primary == "Python"
    assert result.breakdown['.py'] == 2
    assert result.breakdown['.js'] == 1
