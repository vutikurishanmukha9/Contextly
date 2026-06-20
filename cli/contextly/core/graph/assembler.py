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
        self._path_to_priority: Dict[str, int] = {}
        # We also need a mapping from full extensions (e.g. 'src/index.ts') to node_id
        self._exact_to_node_id: Dict[str, str] = {}

    def add_node(self, dto: ParsedFileDTO) -> str:
        """
        Converts a DTO into a node and stores it in the graph.
        Returns the stable node ID.
        """
        node_hash = hashlib.sha256(dto.file_path.encode("utf-8")).hexdigest()[:12]
        node_id = f"node_{node_hash}"
        
        # Determine basic Node Type using strict segment-level and suffix checks
        dir_parts = [p.lower() for p in Path(dto.file_path).parent.parts]
        file_stem = Path(dto.file_path).stem.lower()
        
        is_service_dir = any("service" in p for p in dir_parts)
        is_service_file = file_stem == "service" or file_stem.endswith("service") or file_stem.endswith("_service") or file_stem.endswith(".service")
        
        is_model_dir = any(x in p for p in dir_parts for x in ("model", "schema"))
        is_model_file = file_stem in ("model", "schema") or file_stem.endswith("model") or file_stem.endswith("_model") or file_stem.endswith(".model") or file_stem.endswith("schema") or file_stem.endswith("_schema") or file_stem.endswith(".schema")
        
        node_type = NodeType.COMPONENT
        if is_service_dir or is_service_file:
            node_type = NodeType.SERVICE
        elif is_model_dir or is_model_file:
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
        base_path = dto.file_path
        ext = ""
        if "." in dto.file_path:
            base_path = dto.file_path.rsplit(".", 1)[0]
            ext = dto.file_path.rsplit(".", 1)[1].lower()
            
        EXT_PRIORITY = {
            "ts": 100, "tsx": 90, "py": 80, "js": 70, "jsx": 60,
            "css": 10, "scss": 10, "test": 0, "spec": 0, "md": 0,
            "json": 0, "yaml": 0, "yml": 0
        }
        priority = EXT_PRIORITY.get(ext, 50)
        
        current_priority = self._path_to_priority.get(base_path, -1)
        if priority > current_priority:
            self._path_to_node_id[base_path] = node_id
            self._path_to_priority[base_path] = priority
            
        self._exact_to_node_id[dto.file_path] = node_id
        
        return node_id

    def build_relationships(self, dtos: List[ParsedFileDTO]):
        """
        Processes all imports from all DTOs and establishes relationships
        after all nodes have been registered.
        """
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
