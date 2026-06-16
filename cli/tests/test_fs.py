import pytest
from pathlib import Path
from contextly.utils.fs import find_project_root
from contextly.utils.ignore import IgnoreEngine

def test_find_project_root_with_contextly(tmp_path):
    root = tmp_path / "project"
    root.mkdir()
    (root / ".contextly").mkdir()
    
    deep_dir = root / "src" / "components" / "auth"
    deep_dir.mkdir(parents=True)
    
    found_root = find_project_root(deep_dir)
    assert found_root == root.resolve()

def test_find_project_root_with_git(tmp_path):
    root = tmp_path / "git_project"
    root.mkdir()
    (root / ".git").mkdir()
    
    deep_dir = root / "src" / "utils"
    deep_dir.mkdir(parents=True)
    
    found_root = find_project_root(deep_dir)
    assert found_root == root.resolve()

def test_find_project_root_fallback(tmp_path):
    root = tmp_path / "no_project"
    root.mkdir()
    
    deep_dir = root / "deep" / "dir"
    deep_dir.mkdir(parents=True)
    
    found_root = find_project_root(deep_dir)
    # Should fallback to the start_path because it hit the top without finding a root marker
    assert found_root == deep_dir.resolve()


def test_ignore_engine_matches_directory_pattern_when_is_dir_denied(tmp_path, monkeypatch):
    ignored_dir = tmp_path / "node_modules"
    ignored_dir.mkdir()
    engine = IgnoreEngine(tmp_path)

    original_is_dir = Path.is_dir

    def mock_is_dir(self):
        if self == ignored_dir:
            raise PermissionError("denied")
        return original_is_dir(self)

    monkeypatch.setattr(Path, "is_dir", mock_is_dir)

    assert engine.is_ignored(ignored_dir)
