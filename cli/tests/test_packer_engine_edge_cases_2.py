import pytest
import os
from pathlib import Path
from contextly.core.packer.engine import PackerEngine
from contextly.utils.exceptions import ContextlyError

@pytest.fixture
def packer_engine(tmp_path):
    return PackerEngine(root_dir=tmp_path)

def test_large_file_estimated_tokens_error(packer_engine, tmp_path):
    # Test that > 100k estimated tokens without --force throws error
    (tmp_path / "huge.txt").write_text("a" * (350000 + 1000)) # roughly 100k tokens since multiplier is 3.5
    
    with pytest.raises(ContextlyError, match="Estimated context size"):
        packer_engine.pack(target_paths=[tmp_path], pack_name="out")

def test_large_file_estimated_tokens_force(packer_engine, tmp_path):
    # Test that --force bypasses the check
    (tmp_path / "huge.txt").write_text("a" * 350000)
    
    # max_file_size is 5MB by default, so it's not skipped entirely.
    packer_engine.pack(target_paths=[tmp_path], pack_name="out_forced", force=True)
    assert (tmp_path / ".contextly" / "packs" / "out_forced.contextpack.md").exists()

def test_file_read_grows_beyond_max_size(packer_engine, tmp_path, monkeypatch):
    # simulate file growing between stat and read
    file_path = tmp_path / "grow.txt"
    file_path.write_text("test")
    
    # Mock stat to return small size
    original_stat = Path.stat
    def mock_stat(self, *args, **kwargs):
        if self.name == "grow.txt":
            class MockStat:
                st_size = 10
                st_mode = 33188
            return MockStat()
        return original_stat(self, *args, **kwargs)
        
    monkeypatch.setattr(Path, "stat", mock_stat)
    
    # Set max file size small so the actual read fails it
    packer_engine.max_file_size = 1
    
    _, _, count, out, skipped, _ = packer_engine.pack([tmp_path], "out_grow")
    assert file_path in skipped

def test_decode_error_handling(packer_engine, tmp_path):
    # simulate invalid utf-8 read
    file_path = tmp_path / "bad.txt"
    with open(file_path, "wb") as f:
        f.write(b'\x80\x81\x82')
        
    # skip binary check so we force decode error
    packer_engine._is_binary_file = lambda x: False
    
    _, _, count, out, skipped, _ = packer_engine.pack([tmp_path], "out_bad")
    assert file_path in skipped

def test_decode_error_handling_raw_mode(packer_engine, tmp_path):
    file_path = tmp_path / "bad_raw.txt"
    with open(file_path, "wb") as f:
        f.write(b'\x80\x81\x82')
    packer_engine._is_binary_file = lambda x: False
    _, _, count, out, skipped, _ = packer_engine.pack([tmp_path], "out_bad_raw", raw=True)
    # raw mode doesn't read the whole file to decode early, it streams and handles errors as replace
    assert file_path not in skipped

def test_task_filtering_basic(packer_engine, tmp_path, monkeypatch):
    (tmp_path / "src").mkdir()
    (tmp_path / "src" / "a.py").write_text("pass")
    
    # Test pack with task
    from contextly.core.packer.ranking import RankingEngine
    class MockRanker:
        def __init__(self, *args, **kwargs):
            self.task = kwargs.get("task")
        def rank(self, files):
            return files
    
    monkeypatch.setattr("contextly.core.packer.engine.RankingEngine", MockRanker)
    monkeypatch.setattr("contextly.core.packer.engine.ImportGraphBuilder.build", lambda self: None)
    monkeypatch.setattr("contextly.core.packer.engine.GraphValidator.validate", lambda self, g: None)
    
    _, _, count, out, skipped, _ = packer_engine.pack([tmp_path], "out_task", task="Find bugs")
    assert out.exists()
    
    content = out.read_text()
    assert "Navigation Guidance" in content
