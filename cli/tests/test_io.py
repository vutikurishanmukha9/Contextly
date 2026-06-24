import pytest
import os
import time
from pathlib import Path
from contextly.utils.io import _cleanup_stale_parts, atomic_write, sanitize_filename, save_command_result

def test_cleanup_stale_parts(tmp_path):
    stale_file = tmp_path / ".tmp-123.part"
    stale_file.touch()
    
    # Set modify time to 2 days ago
    os.utime(stale_file, (time.time() - 100000, time.time() - 100000))
    
    fresh_file = tmp_path / ".tmp-456.part"
    fresh_file.touch()
    
    _cleanup_stale_parts(tmp_path)
    
    assert not stale_file.exists()
    assert fresh_file.exists()

def test_cleanup_stale_parts_oserror_suppressed(tmp_path, monkeypatch):
    stale_file = tmp_path / ".tmp-123.part"
    stale_file.touch()
    os.utime(stale_file, (time.time() - 100000, time.time() - 100000))
    
    def mock_unlink(self, *args, **kwargs):
        raise OSError("Permission denied")
        
    monkeypatch.setattr(Path, "unlink", mock_unlink)
    
    # Should not raise
    _cleanup_stale_parts(tmp_path)

def test_atomic_write_success(tmp_path):
    target = tmp_path / "target.txt"
    atomic_write(target, "hello world")
    
    assert target.read_text() == "hello world"

def test_atomic_write_exception_cleanup(tmp_path, monkeypatch):
    target = tmp_path / "target.txt"
    
    def mock_replace(src, dst):
        raise OSError("Replace failed")
        
    monkeypatch.setattr(os, "replace", mock_replace)
    
    with pytest.raises(OSError):
        atomic_write(target, "fail")
        
    # temp file should be cleaned up
    parts = list(tmp_path.glob("*.part"))
    assert len(parts) == 0

def test_sanitize_filename():
    assert sanitize_filename('invalid/name?here*') == 'invalid_name_here_'
    assert sanitize_filename('  name .  ') == '  name'

def test_save_command_result_empty(tmp_path):
    out = save_command_result("test", [], "", tmp_path)
    assert out.read_text() == "No output was generated."

def test_save_command_result_long_args(tmp_path):
    out = save_command_result("test", ["a" * 100], "content", tmp_path)
    assert out.read_text() == "content"
