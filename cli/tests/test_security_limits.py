import pytest
import os
import json
from pathlib import Path
from contextly.scanners.dependencies import DependencyScanner, ScannerError, MAX_MANIFEST_SIZE
from contextly.core.graph.parsers.typescript import TypeScriptASTParser

def test_dependency_scanner_file_size_limit(tmp_path):
    repo_dir = tmp_path / "repo"
    repo_dir.mkdir()
    
    pkg_json = repo_dir / "package.json"
    # Create a file slightly larger than the limit
    oversized_content = "{" + '"deps":' + '"x"' * (MAX_MANIFEST_SIZE + 10) + "}"
    pkg_json.write_text(oversized_content)
    
    scanner = DependencyScanner()
    
    # Should skip silently when strict=False (default behavior)
    npm_set = set()
    scanner._parse_package_json(pkg_json, repo_dir, npm_set, strict=False)
    assert len(npm_set) == 0
    
    # Should raise when strict=True
    with pytest.raises(ScannerError, match="exceeds"):
        scanner._parse_package_json(pkg_json, repo_dir, npm_set, strict=True)
        
    req_txt = repo_dir / "requirements.txt"
    req_txt.write_text("x" * (MAX_MANIFEST_SIZE + 10))
    python_set = set()
    with pytest.raises(ScannerError, match="exceeds"):
        scanner._parse_requirements_txt(req_txt, repo_dir, python_set, strict=True)

def test_typescript_parser_file_size_limit(tmp_path):
    repo_dir = tmp_path / "repo"
    repo_dir.mkdir()
    
    tsconfig = repo_dir / "tsconfig.json"
    # Create an oversized tsconfig
    oversized_content = "{" + '"compilerOptions":' + '"x"' * (500 * 1024 + 10) + "}"
    tsconfig.write_text(oversized_content)
    
    parser = TypeScriptASTParser()
    parser._load_tsconfig(str(repo_dir))
    
    # Paths should remain empty because it skipped the oversized file
    assert parser._tsconfig_paths == []
