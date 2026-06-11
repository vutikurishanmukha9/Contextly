from typing import Dict, List, Optional
from pydantic import BaseModel, Field

class LanguageScanResult(BaseModel):
    primary: str = Field(..., description="The primary language of the repository")
    breakdown: Dict[str, int] = Field(default_factory=dict, description="Extension breakdown counts")

class DependencyScanResult(BaseModel):
    npm: List[str] = Field(default_factory=list, description="List of NPM dependencies")
    python: List[str] = Field(default_factory=list, description="List of Python dependencies")
    go: List[str] = Field(default_factory=list, description="List of Go dependencies")
    rust: List[str] = Field(default_factory=list, description="List of Rust dependencies")

class FrameworkScanResult(BaseModel):
    frontend: str = "None detected"
    backend: str = "None detected"

class Pattern(BaseModel):
    name: str
    category: str
    confidence: str
    description: str
    source: str = "discovered"

class PatternScanResult(BaseModel):
    patterns: List[Pattern] = Field(default_factory=list)

class MemoryRule(BaseModel):
    id: str
    category: str
    rule: str
    confidence: str
    source: str
    created_at: str

class ProjectMemory(BaseModel):
    rules: List[MemoryRule] = Field(default_factory=list)

class RepositoryIntelligence(BaseModel):
    language: LanguageScanResult
    dependencies: DependencyScanResult
    frameworks: FrameworkScanResult
    patterns: PatternScanResult = Field(default_factory=PatternScanResult)
    memory: ProjectMemory = Field(default_factory=ProjectMemory)
