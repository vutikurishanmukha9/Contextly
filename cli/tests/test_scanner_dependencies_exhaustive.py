import pytest
from pathlib import Path
from contextly.scanners.dependencies import DependencyScanner

def test_dependency_scanner_all_languages(tmp_path: Path):
    # Python (requirements.txt)
    reqs = "requests==2.28.1\npydantic\nfastapi"
    (tmp_path / "requirements.txt").write_text(reqs)

    # Node (package.json)
    pkg = '{"dependencies": {"react": "^18.0"}, "devDependencies": {"jest": "^27"}}'
    (tmp_path / "package.json").write_text(pkg)

    scanner = DependencyScanner()
    result = scanner.scan(tmp_path)

    assert len(result.python) == 3
    assert len(result.npm) == 2
    assert "requests" in result.python
    assert "react" in result.npm
