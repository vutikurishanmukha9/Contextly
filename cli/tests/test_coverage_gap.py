import pytest
from pathlib import Path
from contextly.scanners.dependencies import DependencyScanner
from contextly.scanners.base import ScannerError
from contextly.core.packer.engine import PackerEngine

def test_dependencies_strict_errors(tmp_path):
    scanner = DependencyScanner()
    
    # Missing package.json
    with pytest.raises(ScannerError):
        scanner._parse_package_json(tmp_path / "package.json", tmp_path, set(), strict=True)
    
    # Invalid package.json
    invalid_pkg = tmp_path / "invalid_pkg.json"
    invalid_pkg.write_text("{invalid")
    with pytest.raises(ScannerError):
        scanner._parse_package_json(invalid_pkg, tmp_path, set(), strict=True)

    # Missing requirements.txt
    with pytest.raises(ScannerError):
        scanner._parse_requirements_txt(tmp_path / "req.txt", tmp_path, set(), strict=True)

    # Missing pyproject.toml
    with pytest.raises(ScannerError):
        scanner._parse_pyproject_toml(tmp_path / "pyproject.toml", tmp_path, set(), strict=True)
        
    # Invalid Pipfile
    with pytest.raises(ScannerError):
        scanner._parse_pipfile(tmp_path / "Pipfile", tmp_path, set(), strict=True)

def test_packer_engine_max_tokens(tmp_path):
    engine = PackerEngine(tmp_path)
    file1 = tmp_path / "f1.py"
    file1.write_text("print('hello')\n" * 100)
    
    file2 = tmp_path / "f2.py"
    file2.write_text("print('world')\n" * 100)
    
    out_file = tmp_path / "out.md"
    
    # test max_tokens edge cases to hit lines 364-377
    tokens, token_type, num_files, path, skipped, excluded = engine.pack(
        target_paths=[file1, file2],
        pack_name="test",
        max_tokens=10 # Very small max tokens to exclude file
    )
    assert excluded > 0
