from typing import Dict, List, Optional
import hashlib

from .parsers.base import ParsedFileDTO
from ...types.models import (
    KnowledgeGraph, 
    KnowledgeNode, 
    NodeType, 
    Relationship, 
    RelationshipType
)
from pathlib import Path

class GraphAssembler:
    """
    Knowledge Graph Assembler.
    Consumes parsed DTOs, creates strictly-typed nodes and relationships, 
    and maintains an O(1) symbol table for O(N) graph resolution.
    """
    
    def __init__(self):
        self.graph = KnowledgeGraph(nodes=[], relationships=[])
        # Mapping from module absolute repository paths (e.g., 'src/index') to node_id
        self._path_to_node_id: Dict[str, str] = {}
        # We also need a mapping from full extensions (e.g. 'src/index.ts') to node_id
        self._exact_to_node_id: Dict[str, str] = {}

    def add_node(self, dto: ParsedFileDTO) -> str:
        """
        Converts a DTO into a node and stores it in the graph.
        Returns the stable node ID.
        """
        node_hash = hashlib.sha256(dto.file_path.encode("utf-8")).hexdigest()[:12]
        node_id = f"node_{node_hash}"
        
        # Determine basic Node Type (Implementation would use a Registry here too)
        node_type = NodeType.COMPONENT
        if "service" in dto.file_path.lower():
            node_type = NodeType.SERVICE
        elif "model" in dto.file_path.lower() or "schema" in dto.file_path.lower():
            node_type = NodeType.MODEL
            
        node = KnowledgeNode(
            id=node_id,
            type=node_type,
            name=Path(dto.file_path).stem,
            path=dto.file_path,
            metadata={"exports": dto.exports} if dto.exports else {}
        )
        
        self.graph.nodes.append(node)
        
        # Add to resolution tables
        # Strip extension for module imports
        base_path = dto.file_path
        if "." in dto.file_path:
            base_path = dto.file_path.rsplit(".", 1)[0]
            
        self._path_to_node_id[base_path] = node_id
        self._exact_to_node_id[dto.file_path] = node_id
        
        return node_id

    def build_relationships(self, dtos: List[ParsedFileDTO]):
        """
        Processes all imports from all DTOs and establishes relationships
        after all nodes have been registered.
        """
        # Map file paths back to their node DTOs
        path_to_dto = {dto.file_path: dto for dto in dtos}
        
        for dto in dtos:
            source_id = self._exact_to_node_id.get(dto.file_path)
            if not source_id:
                continue
                
            for imp in dto.imports:
                target_id = self._resolve_target_id(imp)
                
                if target_id:
                    self.graph.relationships.append(Relationship(
                        source_id=source_id,
                        target_id=target_id,
                        type=RelationshipType.IMPORTS,
                        confidence=1.0 # Static imports are 100% confidence
                    ))
                    
    def _resolve_target_id(self, import_path: str) -> Optional[str]:
        """
        Attempts to resolve an import string into a node ID in O(1) time.
        """
        # Direct exact match (e.g. index.ts)
        if import_path in self._exact_to_node_id:
            return self._exact_to_node_id[import_path]
            
        # Module match (e.g. without extension)
        if import_path in self._path_to_node_id:
            return self._path_to_node_id[import_path]
            
        # Index resolution (e.g. import from 'src/services' -> 'src/services/index')
        index_path = f"{import_path}/index"
        if index_path in self._path_to_node_id:
            return self._path_to_node_id[index_path]
            
        index_path2 = f"{import_path}/__init__"
        if index_path2 in self._path_to_node_id:
            return self._path_to_node_id[index_path2]
            
        return None
