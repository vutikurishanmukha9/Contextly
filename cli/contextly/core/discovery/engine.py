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

    def _get_evaluation_paths(self, file_paths: Optional[List[str]] = None):
        """Yields the paths to evaluate against, constructing path mappings dynamically."""
        if file_paths is not None:
            # LOCAL list for targeted scans.
            seen = set()
            for rel_path in file_paths:
                full_rel = rel_path.replace("\\", "/")
                path_obj = Path(full_rel)
                for parent in [path_obj] + list(path_obj.parents):
                    partial = parent.as_posix()
                    if partial != "." and partial not in seen:
                        seen.add(partial)
                        yield partial
            return

        # Full repo scans are cheap enough for correctness and avoid stale state
        # when a long-lived engine instance observes filesystem changes.
        from ...utils.config import load_config_model
        config = load_config_model(self.root_dir)
        discovery_depth = config.depth_limits.discovery
        
        walker = RepoWalker(self.root_dir, max_depth=discovery_depth, skip_predicate=is_skippable)

        for dirpath, dirnames, filenames in walker.walk():
            rel_path = Path(dirpath).relative_to(self.root_dir)
            
            # Add directories
            for dirname in dirnames:
                yield (rel_path / dirname).as_posix()
                
            # Add files
            for filename in filenames:
                yield (rel_path / filename).as_posix()

    def evaluate_registry(
        self, 
        registry: Dict[str, List[BaseRule]], 
        discovery_class: type = Discovery,
        source_name: str = "DiscoveryEngine",
        file_paths: Optional[List[str]] = None
    ) -> List[Any]:
        """
        Evaluates a dictionary mapping names to rulesets using bounded chunk pipelines.
        """
        path_generator = self._get_evaluation_paths(file_paths)
        
        from itertools import islice
        def get_chunks(iterable, size):
            it = iter(iterable)
            while True:
                chunk = list(islice(it, size))
                if not chunk:
                    break
                yield chunk

        # Track evidence and maximum score seen for each rule per target
        target_states = {
            name: {
                'evidence': set(),
                'rule_scores': [0.0] * len(rules)
            }
            for name, rules in registry.items()
        }

        for chunk in get_chunks(path_generator, 1000):
            for target_name, rules in registry.items():
                state = target_states[target_name]
                for idx, rule in enumerate(rules):
                    result = rule.evaluate(chunk)
                    # We max the score to avoid double-counting if a rule matches multiple chunks
                    state['rule_scores'][idx] = max(state['rule_scores'][idx], result.score_delta)
                    state['evidence'].update(result.matched_evidence)

        results = []
        for target_name, state in target_states.items():
            total_score = sum(state['rule_scores'])
            if total_score > 0:
                confidence = min(1.0, total_score)
                # Keep top 5 evidence to avoid giant JSON files
                limited_evidence = sorted(list(state['evidence']), key=lambda x: str(x))[:5]
                
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
