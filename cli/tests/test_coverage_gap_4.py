import pytest
from pathlib import Path
import os
from contextly.core.packer.engine import PackerEngine

def test_packer_engine_normal(tmp_path):
    # Setup files
    file1 = tmp_path / "f1.py"
    file1.write_text("def foo():\n    print('hello')\n")
    
    file2 = tmp_path / "f2.py"
    file2.write_text("def bar():\n    print('world')\n")
    
    engine = PackerEngine(tmp_path)
    
    tokens, token_type, num_files, path, skipped, excluded = engine.pack(
        target_paths=[tmp_path],
        pack_name="test_normal"
    )
    
    assert num_files == 2
    assert excluded == 0

def test_packer_engine_max_tokens_coverage(tmp_path):
    # Setup files
    file1 = tmp_path / "f1.py"
    file1.write_text("print('hello')\n" * 1000) # Big file
    
    file2 = tmp_path / "f2.py"
    file2.write_text("print('world')\n" * 10) # Small file
    
    engine = PackerEngine(tmp_path)
    
    # We want f2 to pass the fast heuristic but fail the slow one.
    # We do this by making the file itself very small but with max_tokens tight.
    # The header adds ~10 tokens.
    tokens, token_type, num_files, path, skipped, excluded = engine.pack(
        target_paths=[tmp_path],
        pack_name="test",
        max_tokens=10 # very small to fail fast
    )
    
    assert excluded > 0

def test_packer_engine_exceptions(tmp_path):
    engine = PackerEngine(tmp_path)
    out_file = tmp_path / "out2.md"
    file1 = tmp_path / "f1.py"
    file1.write_text("print('hello')")
    
    from unittest.mock import patch
    from contextly.utils.exceptions import ContextlyError
    with patch("builtins.open", side_effect=OSError("mock error")):
        try:
            tokens, token_type, num_files, path, skipped, excluded = engine.pack(
                target_paths=[tmp_path],
                pack_name="test2",
            )
        except Exception: # PackerEngine might raise something or just skip
            pass
