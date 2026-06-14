import os
from pathlib import Path
from typing import List

from .base import BaseScanner, ScannerError
from ..types.models import ArchitectureKnowledge, Discovery
from ..utils.walker import RepoWalker

class ArchitectureScanner(BaseScanner):
    @property
    def name(self) -> str:
        return "Architecture Scanner"

    def scan(self, root_dir: Path, **kwargs) -> ArchitectureKnowledge:
        try:
            pattern_scores = {
                "Feature-Based": {"score": 0.0, "evidence": []},
                "Layered": {"score": 0.0, "evidence": []},
                "MVC": {"score": 0.0, "evidence": []},
                "Monolith": {"score": 0.1, "evidence": ["Default fallback"]}
            }
            
            layers = []

            _ALWAYS_SKIP = {
                ".git", "node_modules", "venv", ".venv", "__pycache__",
                ".contextly", "dist", "build", ".next", ".tox", ".eggs"
            }

            def skip_predicate(path: Path) -> bool:
                name = path.name.lower()
                return name in _ALWAYS_SKIP or name.endswith(".egg-info")

            walker = RepoWalker(root_dir, max_depth=3, skip_predicate=skip_predicate)

            for dirpath, dirnames, _filenames in walker.walk():
                rel_path = str(Path(dirpath).relative_to(root_dir))
                
                for dirname in dirnames:
                    name = dirname.lower()
                    full_rel = os.path.join(rel_path, dirname).replace("\\", "/")
                    if full_rel.startswith("./"):
                        full_rel = full_rel[2:]
                    elif full_rel == ".":
                        full_rel = dirname

                    # Feature-based hints
                    if name in ("features", "modules", "domains"):
                        pattern_scores["Feature-Based"]["score"] += 0.5
                        pattern_scores["Feature-Based"]["evidence"].append(full_rel)
                        
                    # MVC hints
                    if name in ("controllers", "views", "models"):
                        pattern_scores["MVC"]["score"] += 0.3
                        pattern_scores["MVC"]["evidence"].append(full_rel)
                        
                    # Layered hints
                    if name in ("services", "repositories", "core", "infrastructure"):
                        pattern_scores["Layered"]["score"] += 0.2
                        pattern_scores["Layered"]["evidence"].append(full_rel)
                        
                    # Layer Discoveries
                    if name == "services":
                        layers.append(Discovery(
                            name="Service Layer",
                            confidence=0.9,
                            evidence=[full_rel],
                            generated_by="ArchitectureScanner"
                        ))
                    elif name == "repositories":
                        layers.append(Discovery(
                            name="Repository Layer",
                            confidence=0.9,
                            evidence=[full_rel],
                            generated_by="ArchitectureScanner"
                        ))

            candidates = []
            for pat_name, data in pattern_scores.items():
                if data["score"] > 0:
                    candidates.append(Discovery(
                        name=pat_name,
                        confidence=min(1.0, data["score"]),
                        evidence=data["evidence"],
                        generated_by="ArchitectureScanner"
                    ))
            
            candidates.sort(key=lambda x: x.confidence, reverse=True)
            
            primary = candidates[0] if candidates else Discovery(
                name="Unknown", confidence=0.0, evidence=[], generated_by="ArchitectureScanner"
            )

            return ArchitectureKnowledge(
                primary_pattern=primary,
                pattern_candidates=candidates,
                layers=layers
            )

        except Exception as e:
            raise ScannerError(f"Architecture scan failed: {str(e)}")
