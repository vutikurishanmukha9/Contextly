import pytest
from pathlib import Path
from contextly.core.packer.engine import PackerEngine

def test_packer_engine_max_tokens_coverage(tmp_path):
    # Setup a valid project
    (tmp_path / "pyproject.toml").write_text("[project]\nname='test'")
    
    file1 = tmp_path / "f1.py"
    file1.write_text("print('hello')\n" * 1000) # Big file
    
    file2 = tmp_path / "f2.py"
    file2.write_text("print('world')\n" * 10) # Small file
    
    engine = PackerEngine(tmp_path)
    out_file = tmp_path / "out.md"
    
    tokens, token_type, num_files, path, skipped, excluded = engine.pack(
        target_paths=[tmp_path],
        pack_name="test",
        max_tokens=10 # Very small to force exclusion
    )
    
    assert excluded > 0
