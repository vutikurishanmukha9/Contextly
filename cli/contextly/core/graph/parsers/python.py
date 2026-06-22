import ast
import os
import sys
import contextlib
from pathlib import Path
from typing import List, Optional
from .base import BaseASTParser, ParsedFileDTO, ExtractedEntity, EntityKind, EntityField, EntityMethod

def _get_type_name(node: Optional[ast.AST]) -> Optional[str]:
    if node is None:
        return None
    if isinstance(node, ast.Name):
        return node.id
    if hasattr(ast, 'unparse'):
        try:
            return ast.unparse(node)
        except Exception:
            return None
    return None

def _extract_called_entities(node: ast.AST) -> List[str]:
    called = []
    for child in ast.walk(node):
        if isinstance(child, ast.Call):
            if isinstance(child.func, ast.Name):
                called.append(child.func.id)
            elif isinstance(child.func, ast.Attribute):
                if hasattr(ast, 'unparse'):
                    try:
                        called.append(ast.unparse(child.func))
                    except Exception:
                        called.append(child.func.attr)
                else:
                    called.append(child.func.attr)
    return called



class PythonASTParser(BaseASTParser):
    """
    Python parser using the native AST module.
    Safely resolves relative imports to their absolute paths within the repository.
    """
    
    def parse(self, file_path: str, content: str, root_dir: str) -> ParsedFileDTO:
        try:
            # Prevent zip-bomb/DoS attacks by limiting AST parseable file size
            if len(content) > 500 * 1024:
                return ParsedFileDTO(file_path=file_path, exports=[], imports=[], error="File exceeds 500KB AST parse limit")
                
            tree = ast.parse(content, filename=file_path)
            
            exports: List[str] = []
            imports: List[str] = []
            
            # Helper to resolve relative imports to absolute repo paths
            file_dir = os.path.dirname(os.path.abspath(os.path.join(root_dir, file_path)))
            
            explicit_all = None
            entities: List[ExtractedEntity] = []
            
            for node in ast.iter_child_nodes(tree):
                if isinstance(node, ast.Assign):
                    for target in node.targets:
                        if isinstance(target, ast.Name) and target.id == "__all__":
                            if isinstance(node.value, (ast.List, ast.Tuple)):
                                explicit_all = []
                                for elt in node.value.elts:
                                    if isinstance(elt, ast.Constant) and isinstance(elt.value, str):
                                        explicit_all.append(elt.value)
                                    elif hasattr(ast, 'Str') and isinstance(elt, getattr(ast, 'Str')):
                                        explicit_all.append(elt.s)
                                        
                # Extract Exports (Classes and Top-Level Functions)
                if isinstance(node, (ast.ClassDef, ast.FunctionDef, ast.AsyncFunctionDef)):
                    if not node.name.startswith("_"):
                        exports.append(node.name)
                elif isinstance(node, ast.Assign):
                    for target in node.targets:
                        if isinstance(target, ast.Name) and not target.id.startswith("_"):
                            exports.append(target.id)
                elif isinstance(node, ast.AnnAssign):
                    if isinstance(node.target, ast.Name) and not node.target.id.startswith("_"):
                        exports.append(node.target.id)
                        
                # Extract Entities (Knowledge Graph V2)
                if isinstance(node, ast.ClassDef):
                    entity = ExtractedEntity(
                        name=node.name,
                        kind=EntityKind.CLASS,
                        purpose=ast.get_docstring(node),
                        called_entities=list(set(_extract_called_entities(node)))
                    )
                    for base in node.bases:
                        if isinstance(base, ast.Name):
                            entity.parent_classes.append(base.id)
                        elif hasattr(ast, 'unparse'):
                            try:
                                entity.parent_classes.append(ast.unparse(base))
                            except Exception:
                                pass
                                
                    for dec in node.decorator_list:
                        if isinstance(dec, ast.Name):
                            entity.decorators.append(dec.id)
                        elif isinstance(dec, ast.Call) and isinstance(dec.func, ast.Name):
                            entity.decorators.append(dec.func.id)
                            
                    for child in node.body:
                        if isinstance(child, ast.AnnAssign):
                            if isinstance(child.target, ast.Name):
                                entity.fields.append(EntityField(
                                    name=child.target.id,
                                    type=_get_type_name(child.annotation)
                                ))
                        elif isinstance(child, (ast.FunctionDef, ast.AsyncFunctionDef)):
                            inputs = []
                            for arg in child.args.args:
                                inputs.append(EntityField(
                                    name=arg.arg,
                                    type=_get_type_name(arg.annotation)
                                ))
                            method_decs = []
                            for dec in child.decorator_list:
                                if isinstance(dec, ast.Name):
                                    method_decs.append(dec.id)
                                elif isinstance(dec, ast.Call) and isinstance(dec.func, ast.Name):
                                    method_decs.append(dec.func.id)
                            
                            method = EntityMethod(
                                name=child.name,
                                inputs=inputs,
                                returns=_get_type_name(child.returns),
                                decorators=method_decs,
                                docstring=ast.get_docstring(child)
                            )
                            entity.methods.append(method)
                    entities.append(entity)
                    
                elif isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                    inputs = []
                    for arg in node.args.args:
                        inputs.append(EntityField(
                            name=arg.arg,
                            type=_get_type_name(arg.annotation)
                        ))
                    func_decs = []
                    for dec in node.decorator_list:
                        if isinstance(dec, ast.Name):
                            func_decs.append(dec.id)
                        elif isinstance(dec, ast.Call) and isinstance(dec.func, ast.Name):
                            func_decs.append(dec.func.id)
                            
                    entity = ExtractedEntity(
                        name=node.name,
                        kind=EntityKind.FUNCTION,
                        purpose=ast.get_docstring(node),
                        inputs=inputs,
                        outputs=_get_type_name(node.returns),
                        decorators=func_decs,
                        called_entities=list(set(_extract_called_entities(node)))
                    )
                    entities.append(entity)
                        
            if explicit_all is not None:
                exports = explicit_all

            for node in ast.walk(tree):
                # Extract Standard Imports
                if isinstance(node, ast.Import):
                    for alias in node.names:
                        imports.append(alias.name)
                        
                # Extract From Imports (and resolve relative)
                elif isinstance(node, ast.ImportFrom):
                    level = node.level
                    base_module = node.module or ""
                    
                    if level > 0:
                        # Resolve relative import (. = level 1, .. = level 2)
                        current_path = Path(file_dir)
                        for _ in range(level - 1):
                            current_path = current_path.parent
                            
                        # If we have a base_module (e.g. from .utils import x)
                        if base_module:
                            resolved = current_path / base_module.replace(".", "/")
                            try:
                                rel_to_root = str(resolved.resolve().relative_to(Path(root_dir).resolve())).replace("\\", "/")
                                imports.append(rel_to_root)
                            except ValueError:
                                imports.append(base_module)
                        else:
                            # e.g. from . import utils
                            for alias in node.names:
                                resolved = current_path / alias.name
                                try:
                                    rel_to_root = str(resolved.resolve().relative_to(Path(root_dir).resolve())).replace("\\", "/")
                                    imports.append(rel_to_root)
                                except ValueError:
                                    imports.append(alias.name)
                    else:
                        imports.append(base_module)

            # Deduplicate
            return ParsedFileDTO(
                file_path=file_path,
                exports=list(set(exports)),
                imports=list(set(imports)),
                entities=entities
            )
            
        except SyntaxError as e:
            return ParsedFileDTO(file_path=file_path, exports=[], imports=[], error=f"SyntaxError: {str(e)}")
        except Exception as e:
            return ParsedFileDTO(file_path=file_path, exports=[], imports=[], error=f"ParseError: {str(e)}")
