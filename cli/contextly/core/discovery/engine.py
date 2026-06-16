import os
from pathlib import Path
from typing import Dict, List, Set, Tuple, Optional, Any

from .rules.base import BaseRule
from ...types.models import Discovery, RepositoryCapability, PatternScanResult
from ...utils.walker import RepoWalker
from ...utils.constants import is_skippable

class DiscoveryEngine:
    """
    Engine for evaluating arbitrary Discovery Rules against a codebase.
    Decouples the file system traversal from the heuristic logic.
    """
    
    def __init__(self, root_dir: Path):
        self.root_dir = root_dir
        self._paths_cache: List[str] = []
        self._is_loaded = False

    def invalidate_cache(self) -> None:
        """Clears cached full-repository evaluation paths."""
        self._paths_cache = []
        self._is_loaded = False

    def discover(self) -> PatternScanResult:
        """
        Runs dependency and pattern scanners to discover conventions.
        Legacy method for Context-Ly learn/discover commands.
        """
        from ...scanners.dependencies import DependencyScanner
        from ...scanners.patterns import PatternScanner
        
        dep_scanner = DependencyScanner()
        pat_scanner = PatternScanner()
        
        deps_result = dep_scanner.scan(self.root_dir)
        patterns_result = pat_scanner.scan(self.root_dir, dependencies=deps_result)
        
        return patterns_result

    def _get_evaluation_paths(self, file_paths: Optional[List[str]] = None) -> List[str]:
        """Returns the paths to evaluate against, using caching for full-repo scans."""
        if file_paths is not None:
            # LOCAL list for targeted scans. Do NOT touch self._paths_cache.
            local_cache = []
            seen = set()
            for rel_path in file_paths:
                full_rel = rel_path.replace("\\", "/")
                path_obj = Path(full_rel)
                for parent in [path_obj] + list(path_obj.parents):
                    partial = parent.as_posix()
                    if partial != "." and partial not in seen:
                        local_cache.append(partial)
                        seen.add(partial)
            return local_cache

        # Full repo scans are cheap enough for correctness and avoid stale state
        # when a long-lived engine instance observes filesystem changes.
        self.invalidate_cache()

        walker = RepoWalker(self.root_dir, max_depth=4, skip_predicate=is_skippable)

        for dirpath, dirnames, filenames in walker.walk():
            rel_path = Path(dirpath).relative_to(self.root_dir)
            
            # Add directories
            for dirname in dirnames:
                self._paths_cache.append((rel_path / dirname).as_posix())
                
            # Add files
            for filename in filenames:
                self._paths_cache.append((rel_path / filename).as_posix())

        self._is_loaded = True
            
        return self._paths_cache.copy()

    def evaluate_registry(
        self, 
        registry: Dict[str, List[BaseRule]], 
        discovery_class: type = Discovery,
        source_name: str = "DiscoveryEngine",
        file_paths: Optional[List[str]] = None
    ) -> List[Any]:
        """
        Evaluates a dictionary mapping names to rulesets.
        
        Args:
            registry: Dict of "Target Name" -> [Rules]
            discovery_class: Pydantic model to construct (Discovery or RepositoryCapability)
            source_name: Tag for provenance auditing
            file_paths: Optional list of file paths to restrict evaluation
            
        Returns:
            List of constructed discovery_class instances.
        """
        paths_to_evaluate = self._get_evaluation_paths(file_paths)
        results = []

        for target_name, rules in registry.items():
            total_score = 0.0
            all_evidence: Set[str] = set()

            for rule in rules:
                result = rule.evaluate(paths_to_evaluate)
                total_score += result.score_delta
                all_evidence.update(result.matched_evidence)

            if total_score > 0:
                confidence = min(1.0, total_score)
                # Keep top 5 evidence to avoid giant JSON files
                limited_evidence = sorted(list(all_evidence))[:5]
                
                if discovery_class == RepositoryCapability:
                    results.append(RepositoryCapability(
                        capability=target_name,
                        confidence=confidence,
                        evidence=limited_evidence,
                        node_ids=[]
                    ))
                else:
                    results.append(Discovery(
                        name=target_name,
                        confidence=confidence,
                        evidence=limited_evidence,
                        generated_by=source_name
                    ))
                    
        # Sort by highest confidence
        results.sort(key=lambda x: x.confidence, reverse=True)
        return results
