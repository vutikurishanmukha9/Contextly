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


