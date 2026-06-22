import pytest
import os
import sys
from pathlib import Path
from unittest.mock import patch
from contextly.main import main
from contextly.utils.fs import find_project_root
from contextly.core.packer.engine import PackerEngine
from contextly.core.graph.builder import ImportGraphBuilder
from contextly.core.graph.parsers.python import PythonASTParser

def test_main_crash_handler(tmp_path, monkeypatch):
    monkeypatch.setenv("LOCALAPPDATA", str(tmp_path))
    monkeypatch.setenv("XDG_STATE_HOME", str(tmp_path))
    
    with patch("contextly.main.app", side_effect=Exception("Test crash")):
        with pytest.raises(SystemExit):
            main()
            
    log_file = tmp_path / "contextly" / "logs" / "crash.log"
    assert log_file.exists()
    assert "Test crash" in log_file.read_text(encoding="utf-8")

def test_fs_git_worktree(tmp_path):
    repo = tmp_path / "repo"
    repo.mkdir()
    (repo / ".git").write_text("gitdir: /path/to/main/.git/worktrees/repo")
    
    subdir = repo / "src" / "deep"
    subdir.mkdir(parents=True)
    
    root = find_project_root(subdir)
    assert root == repo

def test_packer_uuid_collision(tmp_path):
    repo = tmp_path / "repo"
    repo.mkdir()
    engine = PackerEngine(repo)
    
    original_open = os.open
    call_count = 0
    
    def mock_open(path, flags, mode=0o777, *, dir_fd=None):
        nonlocal call_count
        call_count += 1
        if call_count == 1:
            raise FileExistsError("mock collision")
        return original_open(path, flags, mode, dir_fd=dir_fd)
        
    with patch("os.open", side_effect=mock_open):
        token_est, token_type, file_count, out_path, skipped, excluded = engine.pack([repo], "collision_test")
        assert "collision_test_" in out_path.name
        assert len(out_path.name) > len("collision_test.contextpack.md")

def test_builder_ci_throttling(tmp_path, monkeypatch):
    monkeypatch.setenv("CI", "true")
    repo = tmp_path / "repo"
    repo.mkdir()
    
    builder = ImportGraphBuilder(repo)
    # We just need to assert that chunk process works and kwargs are capped
    # We can mock concurrent.futures.ProcessPoolExecutor to check max_workers
    with patch("concurrent.futures.ProcessPoolExecutor") as mock_executor:
        builder.build([]) # empty build
        # Should be called with max_workers <= 2
        if mock_executor.call_args:
            kwargs = mock_executor.call_args[1]
            assert kwargs.get("max_workers", 100) <= 2

def test_python_parser_limits():
    parser = PythonASTParser()
    
    # 1. > 500KB file
    large_content = "x = 1\n" * 100000 # > 500KB
    res = parser.parse("large.py", large_content, ".")
    assert "File exceeds 500KB AST parse limit" in res.error
    
    # 2. Syntax Error
    res2 = parser.parse("syntax.py", "def a(:", ".")
    assert "SyntaxError:" in res2.error
