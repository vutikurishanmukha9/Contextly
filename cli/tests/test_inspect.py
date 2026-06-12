import pytest
import pathlib
from typer.testing import CliRunner
from contextly.main import app
from conftest import runner

def test_inspect_cmd_success(temp_repo):
    """Tests inspect command on files of different sizes to verify formatting logic (red/yellow/white)."""
    runner.invoke(app, ["init"])
    
    # Create files of different sizes
    # > 100 KB (Red)
    (temp_repo / "src" / "large_red.js").write_text("a" * (120 * 1024))
    # > 50 KB (Yellow)
    (temp_repo / "src" / "medium_yellow.js").write_text("b" * (60 * 1024))
    # Small (White)
    (temp_repo / "src" / "small_white.js").write_text("c" * 1024)
    
    result = runner.invoke(app, ["inspect"])
    assert result.exit_code == 0
    assert "Inspection complete!" in result.stdout
    assert "large_red.js" in result.stdout
    assert "medium_yellow.js" in result.stdout
    assert "small_white.js" in result.stdout


def test_inspect_cmd_stat_permission_error(temp_repo, monkeypatch):
    """Tests inspect command when a file's metadata is unreadable (PermissionError/OSError)."""
    runner.invoke(app, ["init"])
    (temp_repo / "src" / "forbidden.js").write_text("console.log('secret')")
    
    # Mock is_file to return True for forbidden.js without calling stat
    original_is_file = pathlib.Path.is_file
    def mock_is_file(self):
        if "forbidden.js" in self.name:
            return True
        return original_is_file(self)
        
    # Mock is_dir to return False for forbidden.js without calling stat
    original_is_dir = pathlib.Path.is_dir
    def mock_is_dir(self):
        if "forbidden.js" in self.name:
            return False
        return original_is_dir(self)
        
    # Mock stat to raise PermissionError for forbidden.js
    original_stat = pathlib.Path.stat
    def mock_stat(self, *args, **kwargs):
        if "forbidden.js" in self.name:
            raise PermissionError("Access Denied")
        return original_stat(self, *args, **kwargs)
        
    monkeypatch.setattr(pathlib.Path, "is_file", mock_is_file)
    monkeypatch.setattr(pathlib.Path, "is_dir", mock_is_dir)
    monkeypatch.setattr(pathlib.Path, "stat", mock_stat)
    
    if hasattr(pathlib, "PosixPath"):
        monkeypatch.setattr(pathlib.PosixPath, "is_file", mock_is_file, raising=False)
        monkeypatch.setattr(pathlib.PosixPath, "is_dir", mock_is_dir, raising=False)
        monkeypatch.setattr(pathlib.PosixPath, "stat", mock_stat, raising=False)
    if hasattr(pathlib, "WindowsPath"):
        monkeypatch.setattr(pathlib.WindowsPath, "is_file", mock_is_file, raising=False)
        monkeypatch.setattr(pathlib.WindowsPath, "is_dir", mock_is_dir, raising=False)
        monkeypatch.setattr(pathlib.WindowsPath, "stat", mock_stat, raising=False)
        
    result = runner.invoke(app, ["inspect"])
    assert result.exit_code == 0
    assert "Inspection complete" in result.stdout


def test_inspect_cmd_deep_tree(temp_repo):
    """Tests inspect command on deeply nested directories to ensure proper traversal."""
    runner.invoke(app, ["init"])
    
    # Create nested dir (5 levels) to fit within Windows path length limit
    deep_dir = temp_repo / "src"
    for i in range(5):
        deep_dir = deep_dir / f"nested_{i}"
    deep_dir.mkdir(parents=True, exist_ok=True)
    (deep_dir / "deep_file.js").write_text("hello deep world")
    
    result = runner.invoke(app, ["inspect"])
    assert result.exit_code == 0
    assert "Inspection complete" in result.stdout
    assert "deep_file.js" in result.stdout


def test_inspect_cmd_validation_error(temp_repo, monkeypatch):
    """Tests inspect command validation error handling."""
    import contextly.commands.inspect as insp_mod
    from contextly.utils.exceptions import ValidationError
    
    def mock_req(*args, **kwargs):
        raise ValidationError("Invalid directory mock error")
        
    monkeypatch.setattr(insp_mod, "require_directory_exists", mock_req)
    result = runner.invoke(app, ["inspect"])
    assert result.exit_code == 1
    assert "Error:" in result.stdout

