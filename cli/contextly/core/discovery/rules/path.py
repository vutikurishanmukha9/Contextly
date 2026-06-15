import re
from typing import List, Optional
from .base import BaseRule, RuleResult

class PathRegexRule(BaseRule):
    """
    Evaluates repository paths using a strict regular expression to avoid false positives.
    Optimized for large-scale path boundary detection (e.g., matching \bauth\b, not author).
    """
    
    def __init__(self, pattern: str, weight: float, limit: int = 5):
        """
        Args:
            pattern: The regular expression string to evaluate.
            weight: The confidence delta to apply if matches are found.
            limit: The maximum number of evidence strings to retain to prevent payload bloat.
        """
        # Pre-compile for performance across large file trees
        self._regex = re.compile(pattern, re.IGNORECASE)
        self.weight = weight
        self.limit = limit

    def evaluate(self, paths: List[str], contents: Optional[List[str]] = None) -> RuleResult:
        matched_evidence = []
        score = 0.0
        
        for path in paths:
            # Normalize path for boundary matching (snake_case, kebab-case, PascalCase)
            # e.g., AuthService.ts -> Auth Service.ts, auth_service.py -> auth service.py
            normalized = re.sub(r'([a-z])([A-Z])', r'\1 \2', path)
            normalized = normalized.replace('_', ' ').replace('-', ' ')
            
            if self._regex.search(normalized):
                if len(matched_evidence) < self.limit:
                    matched_evidence.append(path)
                # Apply weight only once per rule to prevent a massive folder 
                # (e.g. 100 auth files) from generating 100x weight.
                score = self.weight
                
        # If we found any evidence, we return the configured rule weight once.
        return RuleResult(
            score_delta=score if matched_evidence else 0.0,
            matched_evidence=matched_evidence
        )
