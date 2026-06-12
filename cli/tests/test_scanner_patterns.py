import pytest
from pathlib import Path
from contextly.scanners.patterns import PatternScanner
from contextly.types.models import DependencyScanResult

def test_patterns_scanner_edge_cases(tmp_path, monkeypatch):
    """Covers patterns.py multiple lines."""
    s = PatternScanner()
    assert s.name == "Pattern Discovery Engine"
    
    deps = DependencyScanResult()
    deps.npm.extend(["zustand", "redux", "@reduxjs/toolkit", "jotai", "tailwindcss", "styled-components"])
    deps.python.extend(["pydantic", "pytest"])
    
    # Architectures
    (tmp_path / "services").mkdir()
    (tmp_path / "repositories").mkdir()
    (tmp_path / "use_cases").mkdir()
    (tmp_path / "components").mkdir()
    
    res = s.scan(tmp_path, dependencies=deps)
    names = [p.name for p in res.patterns]
    assert "Zustand" in names
    assert "TailwindCSS" in names
    assert "Pydantic" in names
    assert "Pytest" in names
    assert "Service Layer" in names
    assert "Repository Pattern" in names
    assert "Clean Architecture (Use Cases)" in names
    assert "Component-Based UI" in names

def test_pattern_scanner_missing_branches(tmp_path):
    """Covers patterns.py 25, 27, 33, 48, 50, 53-54, 78-79."""
    s = PatternScanner()
    deps = DependencyScanResult()
    deps.npm.extend(["redux", "@reduxjs/toolkit", "jotai", "styled-components", "graphql"])
    deps.python.extend(["django", "celery", "sqlalchemy", "alembic"])
    
    (tmp_path / "src" / "actions").mkdir(parents=True)
    (tmp_path / "src" / "reducers").mkdir(parents=True)
    (tmp_path / "migrations").mkdir(parents=True)
    (tmp_path / "models").mkdir(parents=True)
    
    res = s.scan(tmp_path, dependencies=deps)
    names = [p.name for p in res.patterns]
    assert "Redux" in names or "Jotai" in names
    assert "Styled Components" in names or "GraphQL" in names
    
    # 78-79 is empty dir handled gracefully
    empty_dir = tmp_path / "empty"
    empty_dir.mkdir()
    res_empty = s.scan(empty_dir, dependencies=DependencyScanResult())
    assert len(res_empty.patterns) == 0
