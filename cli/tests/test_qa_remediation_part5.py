import pytest
import json
from pathlib import Path
import codecs
from contextly.scanners.dependencies import DependencyScanner
from contextly.core.packer.engine import PackerEngine

def test_dependency_scanner_all_files(tmp_path):
    repo_dir = tmp_path / "repo"
    repo_dir.mkdir()
    
    # package.json
    (repo_dir / "package.json").write_text(json.dumps({
        "dependencies": {"lodash": "4.17.21"},
        "devDependencies": {"jest": "27.0.0"},
        "peerDependencies": {"react": "17.0.2"}
    }))
    
    # requirements.txt
    (repo_dir / "requirements.txt").write_text("requests==2.26.0\n")
    
    # pyproject.toml
    (repo_dir / "pyproject.toml").write_text("[tool.poetry.dependencies]\nrequests = '^2.26.0'\n[project]\ndependencies = ['numpy']")
    
    # pom.xml, build.gradle, go.mod, Cargo.toml are not supported by the core contextly scanner directly,
    # so we'll just test the supported ones.
    
    scanner = DependencyScanner()
    deps = scanner.scan(repo_dir)
    
    assert "lodash" in deps.npm
    assert "jest" in deps.npm
    assert "requests" in deps.python
    assert "numpy" in deps.python

def test_packer_utf16_bom(tmp_path):
    repo_dir = tmp_path / "repo"
    repo_dir.mkdir()
    engine = PackerEngine(repo_dir)
    
    # Test UTF-16 with BOM
    assert engine._is_binary_file(codecs.BOM_UTF16_LE + b"a\x00b\x00") == False
    assert engine._is_binary_file(codecs.BOM_UTF16_BE + b"\x00a\x00b") == False

def test_packer_utf16_ascii_density(tmp_path):
    repo_dir = tmp_path / "repo"
    repo_dir.mkdir()
    engine = PackerEngine(repo_dir)
    
    # Test UTF-16 NO BOM with ASCII density > 30%
    # "Hello" in UTF-16-LE
    assert engine._is_binary_file(b"H\x00e\x00l\x00l\x00o\x00") == False

def test_packer_skips_binary_file(tmp_path):
    repo_dir = tmp_path / "repo"
    repo_dir.mkdir()
    
    bin_file = repo_dir / "test.bin"
    bin_file.write_bytes(b"\x00\x99\x00\x99\x00\x99\x00\x99")
    
    engine = PackerEngine(repo_dir)
    token_est, token_type, count, out_path, skipped, exc = engine.pack([repo_dir], "test_pack")
    
    assert count == 0
    assert len(skipped) == 1
    assert skipped[0] == bin_file

def test_estimate_tokens_fallback(tmp_path):
    repo_dir = tmp_path / "repo"
    repo_dir.mkdir()
    engine = PackerEngine(repo_dir)
    
    # Test _exact_token_count fallback
    engine.tokenizer = None
    assert engine._exact_token_count("Hello") == int(5 / 3.5)
