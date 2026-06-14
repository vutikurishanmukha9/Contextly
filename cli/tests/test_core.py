import pytest
from pathlib import Path
from typer.testing import CliRunner

from contextly.main import app, version_callback
from contextly.core.memory.engine import MemoryEngine
from contextly.utils.validation import require_directory_exists, ValidationError
from contextly.utils.ignore import IgnoreEngine

runner = CliRunner()

def test_main_version_exception(monkeypatch):
    """Covers main.py lines 18-19: exception during version retrieval."""
    import importlib.metadata
    monkeypatch.setattr(importlib.metadata, "version", lambda x: 1 / 0)
    
    result = runner.invoke(app, ["--version"])
    assert result.exit_code == 0
    assert "contextly version unknown" in result.stdout

def test_engine_mkdir(tmp_path):
    """Covers engine.py line 21: mkdir when memory dir does not exist."""
    # Instantiating MemoryEngine on a fresh path creates the directory and file
    engine = MemoryEngine(tmp_path)
    assert engine.memory_dir.exists()
    assert engine.memory_file.exists()

def test_engine_empty_yaml(tmp_path):
    """Covers engine.py line 41: returning empty ProjectMemory when YAML is empty."""
    engine = MemoryEngine(tmp_path)
    engine.memory_file.write_text("")
    memory = engine.load_memory()
    assert not memory.rules

def test_validation_not_a_dir(tmp_path):
    """Covers validation.py line 25: target exists but is not a directory."""
    f = tmp_path / "test.txt"
    f.write_text("hello")
    with pytest.raises(ValidationError, match="Target is not a directory"):
        require_directory_exists(str(f))

def test_ignore_gitignore_errors(tmp_path, monkeypatch):
    """Covers ignore.py lines 32-36, 41-45: exceptions when reading ignore files."""
    (tmp_path / ".gitignore").write_text("node_modules")
    (tmp_path / ".contextlyignore").write_text("secrets")
    
    import builtins
    original_open = builtins.open
    def mock_open(*args, **kwargs):
        if ".gitignore" in str(args[0]) or ".contextlyignore" in str(args[0]):
            raise PermissionError("Access denied")
        return original_open(*args, **kwargs)
        
    monkeypatch.setattr(builtins, "open", mock_open)
    
    # Instantiate engine, should silently pass permission errors
    engine = IgnoreEngine(tmp_path)
    assert not engine.is_ignored(tmp_path / "node_modules")

def test_ignore_outside_root(tmp_path):
    """Covers ignore.py lines 60-62: ValueError when relative_to fails."""
    engine = IgnoreEngine(tmp_path)
    # Give a path outside root_dir
    outside_path = tmp_path.parent / "outside.txt"
    assert engine.is_ignored(outside_path) == True

def test_ignore_dir_append_slash(tmp_path):
    """Covers ignore.py lines 68-69: append / to dir paths."""
    engine = IgnoreEngine(tmp_path)
    d = tmp_path / "test_dir"
    d.mkdir()
    # It should correctly identify it as a dir and match if there's a rule
    engine.default_ignores.append("test_dir/")
    engine.spec = engine._build_spec()
    assert engine.is_ignored(d) == True


