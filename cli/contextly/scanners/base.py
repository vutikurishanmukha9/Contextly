from abc import ABC, abstractmethod
from pathlib import Path
from pydantic import BaseModel

class ScannerError(Exception):
    """Raised when a scanner fails unexpectedly."""
    pass

class BaseScanner(ABC):
    @property
    @abstractmethod
    def name(self) -> str:
        """The human-readable name of the scanner"""
        pass

    @abstractmethod
    def scan(self, root_dir: Path, **kwargs) -> BaseModel:
        """
        Executes the scan on the repository.
        
        Args:
            root_dir: The root Path of the repository.
            **kwargs: Additional context if a scanner depends on another (e.g. framework depends on dependencies).
            
        Returns:
            A strictly validated Pydantic model representing the scan results.
        """
        pass
