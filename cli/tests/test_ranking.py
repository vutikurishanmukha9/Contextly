import pytest
from pathlib import Path
from contextly.core.packer.ranking import RankingEngine

def test_ranking_logic():
    engine = RankingEngine(Path("/fake/root"))
    
    files = [
        Path("/fake/root/src/utils/helpers.py"),
        Path("/fake/root/README.md"),
        Path("/fake/root/src/main.py"),
        Path("/fake/root/tests/test_main.py"),
        Path("/fake/root/package.json")
    ]
    
    ranked = engine.rank(files)
    
    # Expected order based on scoring:
    # README.md (+100 +40 for root)
    # package.json (+100 +40 for root)
    # src/main.py (+40 for src)
    # tests/test_main.py (-10 for test)
    # src/utils/helpers.py (+40 for src, -20 for utils = +20) Wait, let's verify exact scores.
    
    assert ranked[0].name == "package.json" or ranked[0].name == "README.md"
    assert ranked[1].name == "package.json" or ranked[1].name == "README.md"
    assert ranked[2].name == "main.py"
    assert ranked[3].name == "helpers.py" # score: +40 - 20 = 20
    assert ranked[4].name == "test_main.py" # score: -10
    
def test_ranking_relative_fallback():
    # If file doesn't have root, it falls back to parsing name
    engine = RankingEngine(Path("/fake/root"))
    
    files = [
        Path("README.md"),
        Path("src/app.js"),
    ]
    
    ranked = engine.rank(files)
    assert ranked[0].name == "README.md"
