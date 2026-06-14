from abc import ABC, abstractmethod
from typing import List, Optional
from pydantic import BaseModel

class ParsedFileDTO(BaseModel):
    """
    Data Transfer Object (DTO) representing a successfully parsed file.
    Designed for zero-overhead pickling across process boundaries.
    """
    file_path: str
    exports: List[str]
    imports: List[str] # Absolute repository paths or third-party module names
    error: Optional[str] = None

class BaseASTParser(ABC):
    """
    Enterprise abstract interface for AST parsers.
    Implementations must be thread-safe and free of persistent state.
    """
    
    @abstractmethod
    def parse(self, file_path: str, content: str, root_dir: str) -> ParsedFileDTO:
        """
        Parses a file's content and extracts imports/exports safely.
        
        Args:
            file_path: Absolute or relative path to the file.
            content: The raw string source code.
            root_dir: The repository root for resolving relative imports.
            
        Returns:
            A strictly validated ParsedFileDTO.
        """
        pass
