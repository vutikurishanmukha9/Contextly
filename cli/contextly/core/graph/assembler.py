from typing import Dict, List, Optional, Set
import hashlib
from pathlib import Path

from .parsers.base import ParsedFileDTO, ExtractedEntity, EntityKind
from ...types.models import (
    KnowledgeGraph, 
    KnowledgeNode, 
    NodeType, 
    Relationship, 
    RelationshipType
)

class GraphAssembler:
    """
    Knowledge Graph Assembler.
    Two-pass assembler using Fast LSP pattern with FQN-based symbol resolution.
    Pass 1: Node Registration (Files & Entities)
    Pass 2: Relationship Resolution (Imports, Calls, Extends, Implements, Returns)
    """
    
    def __init__(self):
        self.graph = KnowledgeGraph(nodes=[], relationships=[])
        # Mapping from module absolute repository paths to file node_id
        self._path_to_node_id: Dict[str, str] = {}
        self._path_to_priority: Dict[str, int] = {}
        self._exact_to_node_id: Dict[str, str] = {}
        
        # Symbol Tables for Entities
        self._fqn_to_node_id: Dict[str, str] = {}
        # Simple name to list of FQNs (for fuzzy matching when exact isn't possible)
        self._name_to_fqns: Dict[str, List[str]] = {}
        # Suffix matching cache to avoid O(N) ends-with searches
        self._suffix_to_fqn: Dict[str, str] = {}
        
        # Track unresolved nodes we create to avoid duplicates
        self._unresolved_nodes: Dict[str, str] = {}

    def _get_module_path(self, file_path: str) -> str:
        """Convert a file path to a module path (e.g. src/utils.py -> src.utils)"""
        p = Path(file_path)
        # Strip extension
        module_path = p.with_suffix('').as_posix()
        return module_path.replace('/', '.')

    def add_node(self, dto: ParsedFileDTO) -> str:
        """
        Pass 1: Registers a file and all its extracted entities into the graph.
        Returns the stable node ID of the file.
        """
        # 1. Create File Node
        if dto.file_path in self._exact_to_node_id:
            return self._exact_to_node_id[dto.file_path]
            
        file_hash = hashlib.sha256(dto.file_path.encode("utf-8")).hexdigest()[:12]
        file_node_id = f"file_{file_hash}"
        
        file_node = KnowledgeNode(
            id=file_node_id,
            type=NodeType.FILE,
            name=Path(dto.file_path).stem,
            path=dto.file_path,
            metadata={"exports": dto.exports} if dto.exports else {}
        )
        self.graph.nodes.append(file_node)
        
        # 2. Register File in resolution tables
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
            self._path_to_node_id[base_path] = file_node_id
            self._path_to_priority[base_path] = priority
            
        self._exact_to_node_id[dto.file_path] = file_node_id
        
        # 3. Create Entity Nodes
        module_path = self._get_module_path(dto.file_path)
        for entity in dto.entities:
            fqn = f"{module_path}.{entity.name}"
            if fqn in self._fqn_to_node_id:
                continue
                
            entity_hash = hashlib.sha256(fqn.encode("utf-8")).hexdigest()[:12]
            entity_node_id = f"entity_{entity_hash}"
            
            # Map EntityKind to NodeType
            kind_map = {
                EntityKind.CLASS: NodeType.CLASS,
                EntityKind.FUNCTION: NodeType.FUNCTION,
                EntityKind.INTERFACE: NodeType.INTERFACE,
                EntityKind.SCHEMA: NodeType.SCHEMA,
                EntityKind.ENUM: NodeType.ENUM,
            }
            node_type = kind_map.get(entity.kind, NodeType.UNKNOWN)
            
            entity_node = KnowledgeNode(
                id=entity_node_id,
                type=node_type,
                name=entity.name,
                path=dto.file_path,
                metadata={"fqn": fqn, "purpose": entity.purpose}
            )
            self.graph.nodes.append(entity_node)
            
            # Add CONTAINS relationship
            self.graph.relationships.append(Relationship(
                source_id=file_node_id,
                target_id=entity_node_id,
                type=RelationshipType.CONTAINS,
                confidence=1.0,
                resolution_method="ast_containment"
            ))
            
            # Add to entity symbol tables
            self._fqn_to_node_id[fqn] = entity_node_id
            if entity.name not in self._name_to_fqns:
                self._name_to_fqns[entity.name] = []
            self._name_to_fqns[entity.name].append(fqn)
            
            # Cache all dotted suffixes for fast resolution
            parts = fqn.split('.')
            if len(parts) > 1:
                for i in range(1, len(parts)):
                    suffix = '.'.join(parts[i:])
                    if suffix not in self._suffix_to_fqn:
                        self._suffix_to_fqn[suffix] = fqn
            
        return file_node_id

    def build_relationships(self, dtos: List[ParsedFileDTO]):
        """
        Pass 2: Establishes relationships (Imports, Calls, Extends, Implements, Returns).
        """
        for dto in dtos:
            file_node_id = self._exact_to_node_id.get(dto.file_path)
            if not file_node_id:
                continue
                
            # File-level IMPORTS
            imported_file_ids = set()
            for imp in dto.imports:
                target_id = self._resolve_file_target_id(imp)
                if target_id:
                    self.graph.relationships.append(Relationship(
                        source_id=file_node_id,
                        target_id=target_id,
                        type=RelationshipType.IMPORTS,
                        confidence=1.0,
                        resolution_method="static_import"
                    ))
                    imported_file_ids.add(target_id)
            
            # Entity-level relationships
            module_path = self._get_module_path(dto.file_path)
            for entity in dto.entities:
                fqn = f"{module_path}.{entity.name}"
                entity_node_id = self._fqn_to_node_id.get(fqn)
                if not entity_node_id:
                    continue
                    
                # CALLS
                for called in entity.called_entities:
                    self._resolve_and_add_relationship(
                        entity_node_id, called, module_path, RelationshipType.CALLS
                    )
                    
                # EXTENDS / IMPLEMENTS
                for parent in entity.parent_classes:
                    rel_type = RelationshipType.EXTENDS
                    if entity.kind == EntityKind.INTERFACE or entity.kind == EntityKind.CLASS:
                        # TypeScript interface might extend, but could implement. Default to EXTENDS. 
                        # To perfectly distinguish, parser needs to flag it. We'll use EXTENDS generally.
                        pass 
                    self._resolve_and_add_relationship(
                        entity_node_id, parent, module_path, rel_type
                    )
                    
                # RETURNS (from functions)
                if entity.outputs:
                    self._resolve_and_add_relationship(
                        entity_node_id, entity.outputs, module_path, RelationshipType.RETURNS
                    )
                # RETURNS (from methods)
                for method in entity.methods:
                    if method.returns:
                        self._resolve_and_add_relationship(
                            entity_node_id, method.returns, module_path, RelationshipType.RETURNS
                        )

    def _resolve_and_add_relationship(self, source_id: str, target_name: str, current_module: str, rel_type: RelationshipType):
        """Resolves a symbol name to an Entity Node ID or creates an UNRESOLVED_EXTERNAL."""
        # 1. Exact local match
        local_fqn = f"{current_module}.{target_name}"
        if local_fqn in self._fqn_to_node_id:
            self.graph.relationships.append(Relationship(
                source_id=source_id,
                target_id=self._fqn_to_node_id[local_fqn],
                type=rel_type,
                confidence=1.0,
                resolution_method="file_local_match"
            ))
            return
            
        # 2. Heuristic/Fuzzy match globally
        # (A real LSP would track exactly which import gave us this name. We do a global fuzzy lookup.)
        if target_name in self._name_to_fqns:
            candidates = self._name_to_fqns[target_name]
            if len(candidates) == 1:
                self.graph.relationships.append(Relationship(
                    source_id=source_id,
                    target_id=self._fqn_to_node_id[candidates[0]],
                    type=rel_type,
                    confidence=0.8,
                    resolution_method="fuzzy_global_exact_name"
                ))
                return
            else:
                # Multiple candidates, we pick the first one but with lower confidence
                self.graph.relationships.append(Relationship(
                    source_id=source_id,
                    target_id=self._fqn_to_node_id[candidates[0]],
                    type=rel_type,
                    confidence=0.5,
                    resolution_method="fuzzy_global_multiple_candidates"
                ))
                return
                
        # 3. Handle dot-separated attributes (e.g. sqlalchemy.create_engine)
        if "." in target_name:
            if target_name in self._suffix_to_fqn:
                self.graph.relationships.append(Relationship(
                    source_id=source_id,
                    target_id=self._fqn_to_node_id[self._suffix_to_fqn[target_name]],
                    type=rel_type,
                    confidence=0.6,
                    resolution_method="fuzzy_suffix_match"
                ))
                return

        # 4. Unresolved Fallback
        unresolved_id = self._get_or_create_unresolved(target_name)
        self.graph.relationships.append(Relationship(
            source_id=source_id,
            target_id=unresolved_id,
            type=rel_type,
            confidence=1.0,
            resolution_method="unresolved_external"
        ))

    def _get_or_create_unresolved(self, name: str) -> str:
        if name in self._unresolved_nodes:
            return self._unresolved_nodes[name]
            
        ext_hash = hashlib.sha256(name.encode("utf-8")).hexdigest()[:12]
        ext_id = f"ext_{ext_hash}"
        
        self.graph.nodes.append(KnowledgeNode(
            id=ext_id,
            type=NodeType.UNRESOLVED_EXTERNAL,
            name=name,
            path="external",
            metadata={"fqn": name}
        ))
        self._unresolved_nodes[name] = ext_id
        return ext_id

    def _resolve_file_target_id(self, import_path: str) -> Optional[str]:
        if import_path in self._exact_to_node_id:
            return self._exact_to_node_id[import_path]
        if import_path in self._path_to_node_id:
            return self._path_to_node_id[import_path]
        
        index_path = f"{import_path}/index"
        if index_path in self._path_to_node_id:
            return self._path_to_node_id[index_path]
            
        index_path2 = f"{import_path}/__init__"
        if index_path2 in self._path_to_node_id:
            return self._path_to_node_id[index_path2]
            
        return None
