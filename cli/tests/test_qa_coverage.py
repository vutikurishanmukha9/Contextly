import pytest
import os
import json
from unittest.mock import patch, mock_open
from pathlib import Path
from contextly.core.graph.parsers.python import PythonASTParser
from contextly.core.graph.parsers.typescript import TypeScriptASTParser
from contextly.core.packer.engine import PackerEngine

def test_python_parser_file_size_exceeded(tmp_path):
    # Test the size guardrail
    parser = PythonASTParser()
    test_file = tmp_path / "huge.py"
    content = "A" * (501 * 1024)
    dto = parser.parse(str(test_file), content, str(tmp_path))
    assert dto is not None
    assert dto.error is not None
    assert "File exceeds 500KB AST parse limit" in dto.error

def test_typescript_parser_file_size_exceeded(tmp_path):
    parser = TypeScriptASTParser()
    test_file = tmp_path / "huge.ts"
    content = "A" * (501 * 1024)
    dto = parser.parse(str(test_file), content, str(tmp_path))
    assert dto is not None
    assert dto.error is not None
    assert "File exceeds 500KB AST parse limit" in dto.error

def test_packer_engine_stream_rollback(tmp_path):
    # Test that when unicode decode fails for python file, packer truncates back to start_pos
    packer = PackerEngine(tmp_path)
    
    # create invalid python file
    bad_py = tmp_path / "bad.py"
    bad_py.write_bytes(b"def \xff(): pass")
    
    # pack it
    packer.pack([bad_py], "testpack", raw=False)
    
    # Verify it skipped the file
    pack_file = tmp_path / ".contextly" / "packs" / "testpack.contextpack.md"
    assert pack_file.exists()
    content = pack_file.read_text("utf-8")
    assert "bad.py" not in content

def test_packer_engine_max_tokens_rollback(tmp_path):
    # Test max_tokens exceeded inside python compression
    packer = PackerEngine(tmp_path)
    
    # create large python file
    big_py = tmp_path / "big.py"
    big_py.write_text("def f():\n" + "    pass\n" * 1000, "utf-8")
    
    # Set max_tokens very low
    packer.pack([big_py], "testpack2", max_tokens=10, raw=False)
    
    # Verify it excluded the file contents
    pack_file = tmp_path / ".contextly" / "packs" / "testpack2.contextpack.md"
    content = pack_file.read_text("utf-8")
    assert "def f():" not in content
