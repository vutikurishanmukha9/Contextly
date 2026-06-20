from abc import ABC, abstractmethod
from typing import List, Optional, Dict, Any
from enum import Enum
from pydantic import BaseModel, Field

class EntityKind(str, Enum):
    CLASS = "CLASS"
    FUNCTION = "FUNCTION"
    INTERFACE = "INTERFACE"
    SCHEMA = "SCHEMA"
    ENUM = "ENUM"
    UNKNOWN = "UNKNOWN"

class EntityField(BaseModel):
    name: str
    type: Optional[str] = None
    default_value: Optional[str] = None

class EntityMethod(BaseModel):
    name: str
    inputs: List[EntityField] = Field(default_factory=list)
    returns: Optional[str] = None
    decorators: List[str] = Field(default_factory=list)
    docstring: Optional[str] = None

class ExtractedEntity(BaseModel):
    name: str
    kind: EntityKind
    purpose: Optional[str] = None # Docstring or comment
    fields: List[EntityField] = Field(default_factory=list)
    methods: List[EntityMethod] = Field(default_factory=list)
    inputs: List[EntityField] = Field(default_factory=list) # For functions
    outputs: Optional[str] = None # For functions
    imports: List[str] = Field(default_factory=list)
    dependencies: List[str] = Field(default_factory=list)
    parent_classes: List[str] = Field(default_factory=list)
    decorators: List[str] = Field(default_factory=list)
    called_entities: List[str] = Field(default_factory=list)

class ParsedFileDTO(BaseModel):
    """
    Data Transfer Object (DTO) representing a successfully parsed file.
    Designed for zero-overhead pickling across process boundaries.
    """
    file_path: str
    exports: List[str]
    imports: List[str] # Absolute repository paths or third-party module names
    entities: List[ExtractedEntity] = Field(default_factory=list)
    error: Optional[str] = None

class BaseASTParser(ABC):
    """
    Abstract interface for AST parsers.
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

# Alias for backward compatibility with registry and other consumers
BaseParser = BaseASTParser

