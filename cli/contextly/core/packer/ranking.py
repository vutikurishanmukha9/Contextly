from pathlib import Path
from typing import List, Dict

class RankingEngine:
    """Scores and ranks files based on their estimated value to the LLM."""
    
    def __init__(self, root_dir: Path):
        self.root_dir = root_dir
        
    def rank(self, files: List[Path]) -> List[Path]:
        """Returns the list of files sorted by their score (highest first)."""
        scored_files = []
        for file in files:
            score = self._score_file(file)
            scored_files.append((score, file))
            
        # Sort by score descending, then by path length ascending (prefer top-level)
        scored_files.sort(key=lambda x: (-x[0], len(x[1].parts), x[1].name))
        
        return [f[1] for f in scored_files]
        
    def _score_file(self, file: Path) -> int:
        score = 0
        try:
            rel_path = file.relative_to(self.root_dir).as_posix().lower()
        except ValueError:
            rel_path = file.name.lower()
            
        parts = Path(rel_path).parts
        
        # 1. Config / Core Docs
        if file.name.lower() in ["readme.md", "package.json", "pyproject.toml", "cargo.toml", "go.mod"]:
            score += 100
            
        # 2. Top-level files (Entry points)
        if len(parts) == 1:
            score += 40
            
        # 3. Source code
        if any(p in parts for p in ["src", "app", "lib", "core", "main"]):
            score += 40
            
        # 4. Tests
        if any(p in parts for p in ["tests", "test", "spec", "specs", "__tests__"]):
            score -= 10
            
        # 5. Utilities
        if any(p in parts for p in ["utils", "helpers", "misc", "vendor"]):
            score -= 20
            
        return score
