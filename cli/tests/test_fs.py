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

def test_find_project_root_fallback(tmp_path, monkeypatch):
    root = tmp_path / "no_project"
    root.mkdir()
    
    deep_dir = root / "deep" / "dir"
    deep_dir.mkdir(parents=True)
    
    original_is_dir = Path.is_dir
    original_exists = Path.exists
    
    def mock_is_dir(self):
        if self.parent == Path("C:/Users/V SHANMUKH") or self.parent.parent == Path("C:/Users/V SHANMUKH"):
            return False
        return original_is_dir(self)
        
    def mock_exists(self):
        if self.parent == Path("C:/Users/V SHANMUKH") or self.parent.parent == Path("C:/Users/V SHANMUKH"):
            return False
        return original_exists(self)
        
    monkeypatch.setattr(Path, "is_dir", mock_is_dir)
    monkeypatch.setattr(Path, "exists", mock_exists)
    
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

def test_find_project_root_resolve_fails(tmp_path, monkeypatch):
    root = tmp_path / "project"
    root.mkdir()
    (root / ".git").mkdir()
    
    # Mock Path.resolve to throw an exception so it falls back to absolute()
    original_resolve = Path.resolve
    def mock_resolve(self):
        raise RuntimeError("Resolve failed")
    
    monkeypatch.setattr(Path, "resolve", mock_resolve)
    
    found = find_project_root(root)
    assert found == root.absolute()

def test_find_project_root_permission_error_on_exists(tmp_path, monkeypatch):
    root = tmp_path / "project"
    root.mkdir()
    
    original_exists = Path.exists
    def mock_exists(self):
        if "config.yaml" in self.name and "project" in str(self):
            raise PermissionError("Denied")
        return False
        
    monkeypatch.setattr(Path, "exists", mock_exists)
    monkeypatch.setattr(Path, "is_dir", lambda self: False)
    
    found = find_project_root(root)
    assert found == root.resolve()

def test_find_project_root_parents_loop(tmp_path):
    root = tmp_path / "project"
    root.mkdir()
    
    class LoopPath:
        def __init__(self, p):
            self.p = p
        def resolve(self):
            return self
        def absolute(self):
            return self
        @property
        def parents(self):
            # Return ourselves to cause the 'seen' break
            return [self]
        def __truediv__(self, other):
            return self.p / other
        def __hash__(self):
            return hash(str(self.p))
        def __eq__(self, other):
            if isinstance(other, LoopPath):
                return self.p == other.p
            return False
            
    p = LoopPath(root)
    found = find_project_root(p) # type: ignore
    assert found == p
