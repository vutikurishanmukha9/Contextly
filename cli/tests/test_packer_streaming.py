import pytest
from pathlib import Path
from unittest.mock import patch
from contextly.core.packer.engine import PackerEngine

def test_packer_engine_streaming(tmp_path):
    # Setup dummy repo
    repo_dir = tmp_path / "repo"
    repo_dir.mkdir()
    
    # Text file
    txt_file = repo_dir / "test.txt"
    txt_file.write_text("Hello " * 1000)
    
    # Binary file
    bin_file = repo_dir / "test.bin"
    bin_file.write_bytes(b"\x00\x01\x02\x03" * 100 + b"\x00")
    
    # Large file
    large_file = repo_dir / "large.txt"
    large_file.write_text("A" * 200000)
    
    # Mock config to change max_file_size
    with patch("contextly.utils.config.load_config_model") as mock_load:
        mock_load.return_value.packer.max_file_size_mb = 0.1 # 100KB
        engine = PackerEngine(repo_dir)
        
        engine.ranker.rank_files = lambda paths: [txt_file, bin_file, large_file]
        
        engine.pack(
            target_paths=[repo_dir],
            pack_name="test_pack",
            max_tokens=None,
            raw=True
        )
        
        out_file = repo_dir / ".contextly" / "packs" / "test_pack.contextpack.md"
        assert out_file.exists()
        
        content = out_file.read_text(encoding="utf-8")
        assert "Hello " in content
        assert "test.txt" in content
        assert "test.bin" not in content # Skipped because binary
        assert "large.txt" not in content # Skipped because size

def test_packer_engine_token_limit(tmp_path):
    repo_dir = tmp_path / "repo"
    repo_dir.mkdir()
    
    f1 = repo_dir / "f1.txt"
    f1.write_text("word " * 1000)
    
    f2 = repo_dir / "f2.txt"
    f2.write_text("test " * 1000)
    
    engine = PackerEngine(repo_dir)
    engine.ranker.rank_files = lambda paths: [f1, f2]
    
    engine.pack(
        target_paths=[repo_dir],
        pack_name="test_pack_2",
        max_tokens=1500, # f1 is ~1000 tokens, so f1+f2 > 1500
        raw=True
    )
    
    out_file = repo_dir / ".contextly" / "packs" / "test_pack_2.contextpack.md"
    content = out_file.read_text(encoding="utf-8")
    
    assert "f1.txt" in content
    assert "Excluded Files (Token Limit)" in content
    assert "f2.txt" in content # Will be listed under excluded

def test_packer_engine_toctou_exists(tmp_path):
    repo_dir = tmp_path / "repo"
    repo_dir.mkdir()
    packs_dir = repo_dir / ".contextly" / "packs"
    packs_dir.mkdir(parents=True)
    
    (packs_dir / "test_pack.contextpack.md").write_text("exists")
    
    txt_file = repo_dir / "test.txt"
    txt_file.write_text("Hello")
    
    engine = PackerEngine(repo_dir)
    engine.ranker.rank_files = lambda paths: [txt_file]
    
    token_est, token_type, file_count, out_path, skipped, excluded = engine.pack(
        target_paths=[repo_dir],
        pack_name="test_pack",
        max_tokens=None,
        raw=True
    )
    
    assert out_path.exists()
    assert out_path.name != "test_pack.contextpack.md"
    assert out_path.name.startswith("test_pack_")
