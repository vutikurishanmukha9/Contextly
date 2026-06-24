import pytest
import os
from pathlib import Path
from contextly.utils.fs import find_project_root
from contextly.utils.paths import safe_resolve
from contextly.utils.exceptions import ValidationError

def test_find_project_root_git(tmp_path):
    (tmp_path / ".git").mkdir()
    assert find_project_root(tmp_path) == tmp_path

def test_find_project_root_contextly(tmp_path):
    (tmp_path / ".contextly").mkdir()
    assert find_project_root(tmp_path) == tmp_path

def test_find_project_root_not_found(tmp_path, monkeypatch):
    monkeypatch.setattr(Path, "exists", lambda self: False)
    monkeypatch.setattr(Path, "is_dir", lambda self: False)
    assert find_project_root(tmp_path) == tmp_path

def test_safe_resolve(tmp_path):
    file_path = tmp_path / "test.txt"
    file_path.write_text("hello")
    assert safe_resolve(file_path, tmp_path) == file_path.resolve()
    
    # Path traversal
    with pytest.raises(ValidationError):
        safe_resolve(tmp_path / ".." / "outside.txt", tmp_path)

def test_safe_resolve_symlink_cycle(tmp_path, monkeypatch):
    p = tmp_path / "link"
    
    # Mock is_symlink and realpath to simulate a cycle
    monkeypatch.setattr(Path, "is_symlink", lambda self: True)
    monkeypatch.setattr(os.path, "realpath", lambda x: str(p))
    
    with pytest.raises(ValidationError, match="cycle"):
        safe_resolve(p, tmp_path)

def test_safe_resolve_symlink_depth(tmp_path, monkeypatch):
    p = tmp_path / "link"
    
    # Mock is_symlink and realpath to simulate infinite depth without exact cycle
    counter = [0]
    def mock_realpath(x):
        counter[0] += 1
        return str(tmp_path / f"link_{counter[0]}")
        
    monkeypatch.setattr(Path, "is_symlink", lambda self: True)
    monkeypatch.setattr(os.path, "realpath", mock_realpath)
    
    with pytest.raises(ValidationError, match="depth"):
        safe_resolve(p, tmp_path)
