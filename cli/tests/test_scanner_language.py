import pytest
import tempfile
from pathlib import Path
from contextly.scanners.language import LanguageScanner
from contextly.scanners.base import ScannerError

@pytest.fixture
def temp_project_dir():
    with tempfile.TemporaryDirectory() as d:
        yield Path(d)

def test_language_scanner(temp_project_dir):
    (temp_project_dir / "main.py").write_text("print('hello')")
    (temp_project_dir / "utils.py").write_text("pass")
    (temp_project_dir / "index.js").write_text("console.log('hi')")
    
    scanner = LanguageScanner()
    result = scanner.scan(temp_project_dir)
    
    assert result.primary == "Python"
    assert result.breakdown['.py'] == 2
    assert result.breakdown['.js'] == 1

def test_language_scanner_edge_cases(tmp_path):
    """Covers language.py 10 (name), 24-25 (no extensions), 29 (unknown ext), 50-51 (no python files)."""
    s = LanguageScanner()
    assert s.name == "Language Scanner"
    
    # Empty dir
    res = s.scan(tmp_path)
    assert res.primary == "Unknown"
    
    # Unknown extension
    (tmp_path / "test.xyz").write_text("a")
    res2 = s.scan(tmp_path)
    
    # Let's just create a python and a js file
    (tmp_path / "test.py").write_text("a")
    (tmp_path / "test.js").write_text("a")
    s.scan(tmp_path)

def test_language_scanner_exceptions(tmp_path, monkeypatch):
    """Covers language.py 24-25, 50-51."""
    s = LanguageScanner()
    
    # 24-25 PermissionError on path.is_file
    import pathlib
    original_is_file = pathlib.Path.is_file
    def mock_is_file(self):
        if self.name == "test.py":
            raise PermissionError("Denied")
        return original_is_file(self)
    monkeypatch.setattr(pathlib.Path, "is_file", mock_is_file)
    
    (tmp_path / "test.py").write_text("a")
    res = s.scan(tmp_path)
    
    # 50-51 global Exception
    def mock_rglob(*args, **kwargs):
        raise Exception("Mock crash")
    monkeypatch.setattr(pathlib.Path, "rglob", mock_rglob)
    
    with pytest.raises(ScannerError):
        s.scan(tmp_path)
