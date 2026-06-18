from typing import Dict, List, Any
from enum import Enum
from pydantic import BaseModel, Field

class LanguageScanResult(BaseModel):
    primary: str = Field(..., description="The primary language of the repository")
    breakdown: Dict[str, int] = Field(default_factory=dict, description="Extension breakdown counts")

class DependencyScanResult(BaseModel):
    npm: List[str] = Field(default_factory=list, description="List of NPM dependencies")
    python: List[str] = Field(default_factory=list, description="List of Python dependencies")

class FrameworkScanResult(BaseModel):
    frontend: List[str] = Field(default_factory=list)
    backend: List[str] = Field(default_factory=list)

class Pattern(BaseModel):
    name: str
    category: str
    confidence: float
    description: str
    source: str = "discovered"

class PatternScanResult(BaseModel):
    patterns: List[Pattern] = Field(default_factory=list)

class MemoryRule(BaseModel):
    id: str = Field(..., max_length=100)
    name: str | None = Field(default=None, max_length=200)
    category: str = Field(..., max_length=100)
    rule: str = Field(..., max_length=5000)
    confidence: float
    source: str = Field(..., max_length=100)
    created_at: str = Field(..., max_length=50)

class ProjectMemory(BaseModel):
    rules: List[MemoryRule] = Field(default_factory=list)

class RepositoryIntelligence(BaseModel):
    language: LanguageScanResult
    dependencies: DependencyScanResult
    frameworks: FrameworkScanResult
    patterns: PatternScanResult = Field(default_factory=PatternScanResult)
    memory: ProjectMemory = Field(default_factory=ProjectMemory)

# --- Knowledge Graph Schema (V2) ---

class Discovery(BaseModel):
    name: str
    confidence: float
    evidence: List[str]
    generated_by: str = "UnknownScanner"

class RepositoryCapability(BaseModel):
    capability: str
    confidence: float
    evidence: List[str]
    node_ids: List[str] = Field(default_factory=list)

class NodeType(str, Enum):
    COMPONENT = "COMPONENT"
    SERVICE = "SERVICE"
    STORE = "STORE"
    ROUTE = "ROUTE"
    CONTROLLER = "CONTROLLER"
    REPOSITORY = "REPOSITORY"
    MODEL = "MODEL"
    UNKNOWN = "UNKNOWN"

class KnowledgeNode(BaseModel):
    id: str
    type: NodeType
    name: str
    path: str
    metadata: Dict[str, Any] = Field(default_factory=dict)

class RelationshipType(str, Enum):
    IMPORTS = "IMPORTS"
    CALLS = "CALLS"
    USES = "USES"
    EXTENDS = "EXTENDS"

class Relationship(BaseModel):
    source_id: str
    target_id: str
    type: RelationshipType
    confidence: float = 1.0

class KnowledgeGraph(BaseModel):
    nodes: List[KnowledgeNode] = Field(default_factory=list)
    relationships: List[Relationship] = Field(default_factory=list)

class DomainType(str, Enum):
    DOMAIN = "DOMAIN"
    SHARED = "SHARED"
    INFRASTRUCTURE = "INFRASTRUCTURE"

class DomainKnowledge(BaseModel):
    id: str
    name: str
    type: DomainType
    node_ids: List[str] = Field(default_factory=list)

class TechnologyKnowledge(BaseModel):
    frameworks: List[str] = Field(default_factory=list)
    languages: List[str] = Field(default_factory=list)
    libraries: List[str] = Field(default_factory=list)

class ArchitectureKnowledge(BaseModel):
    primary_pattern: Discovery
    pattern_candidates: List[Discovery] = Field(default_factory=list)
    layers: List[Discovery] = Field(default_factory=list)

class RepositoryKnowledge(BaseModel):
    repository_hash: str
    generated_at: str
    contextly_version: str
    technologies: TechnologyKnowledge
    architecture: ArchitectureKnowledge
    capabilities: List[RepositoryCapability] = Field(default_factory=list)
    domains: List[DomainKnowledge] = Field(default_factory=list)
    graph: KnowledgeGraph
