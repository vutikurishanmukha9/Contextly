from abc import ABC, abstractmethod
from typing import List, Set, Tuple
from pydantic import BaseModel

class RuleResult(BaseModel):
    """
    Represents the deterministic outcome of a single rule evaluation.
    """
    score_delta: float
    matched_evidence: List[str]

class BaseRule(ABC):
    """
    Abstract Base Class representing a single, deterministic discovery heuristic.
    Implementations should ensure thread-safety and side-effect-free execution.
    """
    
    @abstractmethod
    def evaluate(self, paths: List[str], contents: List[str] = None) -> RuleResult:
        """
        Evaluates the rule against a provided context.
        
        Args:
            paths: A list of repository-relative string paths to evaluate.
            contents: Optional file contents corresponding to the paths for deep scanning.
            
        Returns:
            A RuleResult containing the confidence delta and specific evidence found.
        """
        pass
