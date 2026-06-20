import os
import sys
import json
import re
import contextlib
from pathlib import Path
from typing import List
from .base import BaseASTParser, ParsedFileDTO, ExtractedEntity, EntityKind, EntityField, EntityMethod

@contextlib.contextmanager
def scoped_recursion_limit(limit):
    old_limit = sys.getrecursionlimit()
    sys.setrecursionlimit(limit)
    try:
        yield
    finally:
        sys.setrecursionlimit(old_limit)

try:
    from tree_sitter import Language, Parser
    from tree_sitter_languages import get_language, get_parser
    HAS_TREE_SITTER = True
except ImportError:
    HAS_TREE_SITTER = False

class TypeScriptASTParser(BaseASTParser):
    """
    TypeScript/JavaScript parser using Tree-Sitter.
    Extracts exports and resolves import paths accurately without regex.
    """
    
    def __init__(self, extension: str = "ts"):
        self.parser = None
        self._tsconfig_paths = None
        self._root_dir = None
        if HAS_TREE_SITTER:
            try:
                lang_name = 'tsx' if extension.lower() in ('tsx', 'jsx') else 'typescript'
                self.language = get_language(lang_name)
                self.parser = get_parser(lang_name)
            except Exception:
                pass

    def _load_tsconfig(self, root_dir: str):
        if self._tsconfig_paths is not None and self._root_dir == root_dir:
            return
            
        self._root_dir = root_dir
        paths_list = []
        
        # Scan for tsconfig.json files in root and immediate subdirs
        try:
            for root, dirs, files in os.walk(root_dir):
                if "tsconfig.json" in files:
                    try:
                        with open(os.path.join(root, "tsconfig.json"), "r", encoding="utf-8") as f:
                            content = f.read()
                            # Strip comments securely without destroying JSON strings
                            safe_regex = r'("(?:\\.|[^"\\])*")|//.*?(?=\n|$)|/\*.*?\*/'
                            content = re.sub(safe_regex, lambda m: m.group(1) if m.group(1) else '', content, flags=re.S)
                            # Remove trailing commas
                            content = re.sub(r',\s*([\]}])', r'\1', content)
                            data = json.loads(content)
                            paths = data.get("compilerOptions", {}).get("paths", {})
                            
                            for alias, targets in paths.items():
                                if not targets: continue
                                alias_prefix = alias.replace("*", "")
                                target_prefix = targets[0].replace("*", "")
                                
                                rel_root = os.path.relpath(root, root_dir)
                                if rel_root == ".":
                                    rel_root = ""
                                    
                                target_full = os.path.normpath(os.path.join(rel_root, target_prefix)).replace("\\", "/")
                                if target_full and not target_full.endswith("/"):
                                    target_full += "/"
                                    
                                paths_list.append((alias_prefix, target_full))
                    except Exception:
                        pass
                try:
                    rel_path = Path(root).resolve().relative_to(Path(root_dir).resolve())
                    if len(rel_path.parts) >= 1:
                        dirs[:] = []
                except ValueError:
                    dirs[:] = []
        except Exception:
            pass

        self._root_dir = root_dir
        self._tsconfig_paths = paths_list

    def parse(self, file_path: str, content: str, root_dir: str) -> ParsedFileDTO:
        if not HAS_TREE_SITTER or not self.parser:
            return ParsedFileDTO(file_path=file_path, exports=[], imports=[], error="Tree-sitter not available")
            
        try:
            if len(content) > 500 * 1024:
                return ParsedFileDTO(file_path=file_path, exports=[], imports=[], error="File exceeds 500KB AST parse limit")
                
            self._load_tsconfig(root_dir)
            with scoped_recursion_limit(1500):
                tree = self.parser.parse(bytes(content, "utf8"))
            
            exports: List[str] = []
            imports: List[str] = []
            entities: List[ExtractedEntity] = []
            
            file_dir = os.path.dirname(os.path.abspath(os.path.join(root_dir, file_path)))
            
            def _extract_called_entities(n) -> List[str]:
                called = []
                def _walk(child_node):
                    if child_node.type == 'call_expression':
                        func_node = child_node.child_by_field_name('function')
                        if func_node:
                            called.append(content[func_node.start_byte:func_node.end_byte])
                    for sub in child_node.children:
                        _walk(sub)
                _walk(n)
                return called

            def traverse(node):
                # Handle imports
                if node.type == 'import_statement':
                    # Find the string module name
                    for child in node.children:
                        if child.type == 'string':
                            # Remove quotes
                            module = content[child.start_byte+1:child.end_byte-1]
                            self._resolve_import(module, file_dir, root_dir, imports)
                            
                # Handle exports (export const X, export function Y, export class Z)
                elif node.type == 'export_statement':
                    for child in node.children:
                        if child.type == 'lexical_declaration' or child.type == 'variable_declaration':
                            # export const x = 1;
                            for decl in child.children:
                                if decl.type == 'variable_declarator':
                                    name_node = decl.child_by_field_name('name')
                                    if name_node:
                                        exports.append(content[name_node.start_byte:name_node.end_byte])
                        elif child.type in ('function_declaration', 'class_declaration', 'interface_declaration', 'type_alias_declaration'):
                            name_node = child.child_by_field_name('name')
                            if name_node:
                                exports.append(content[name_node.start_byte:name_node.end_byte])
                        elif child.type == 'export_clause':
                            for spec in child.children:
                                if spec.type == 'export_specifier':
                                    name_node = spec.child_by_field_name('name')
                                    if name_node:
                                        exports.append(content[name_node.start_byte:name_node.end_byte])
                        elif child.type == 'default' or child.type == 'identifier':
                            exports.append('default')
                
                # Extract Entities
                if node.type in ('class_declaration', 'interface_declaration', 'type_alias_declaration'):
                    name_node = node.child_by_field_name('name')
                    if name_node:
                        name = content[name_node.start_byte:name_node.end_byte]
                        kind = EntityKind.CLASS if node.type == 'class_declaration' else EntityKind.INTERFACE
                        
                        parent_classes = []
                        for child in node.children:
                            if child.type in ('class_heritage', 'heritage_clause', 'extends_clause', 'implements_clause'):
                                def _get_types(hn):
                                    for hc in hn.children:
                                        if hc.type in ('identifier', 'type_identifier'):
                                            parent_classes.append(content[hc.start_byte:hc.end_byte])
                                        else:
                                            _get_types(hc)
                                _get_types(child)
                                
                        entity = ExtractedEntity(
                            name=name, 
                            kind=kind,
                            called_entities=list(set(_extract_called_entities(node))),
                            parent_classes=list(set(parent_classes))
                        )
                        
                        body_node = node.child_by_field_name('body') or next((c for c in node.children if c.type == 'object_type'), None)
                        if body_node:
                            for member in body_node.children:
                                if member.type in ('public_field_definition', 'property_signature'):
                                    prop_name = member.child_by_field_name('name')
                                    if prop_name:
                                        entity.fields.append(EntityField(name=content[prop_name.start_byte:prop_name.end_byte]))
                                elif member.type in ('method_definition', 'method_signature'):
                                    meth_name = member.child_by_field_name('name')
                                    if meth_name:
                                        ret_type_node = member.child_by_field_name('return_type')
                                        ret_type = content[ret_type_node.start_byte:ret_type_node.end_byte] if ret_type_node else None
                                        method = EntityMethod(
                                            name=content[meth_name.start_byte:meth_name.end_byte],
                                            returns=ret_type
                                        )
                                        params = member.child_by_field_name('parameters')
                                        if params:
                                            for p in params.children:
                                                if p.type in ('required_parameter', 'optional_parameter'):
                                                    pname = p.child_by_field_name('pattern')
                                                    if pname:
                                                        method.inputs.append(EntityField(name=content[pname.start_byte:pname.end_byte]))
                                        entity.methods.append(method)
                        entities.append(entity)
                        
                elif node.type == 'function_declaration':
                    name_node = node.child_by_field_name('name')
                    if name_node:
                        name = content[name_node.start_byte:name_node.end_byte]
                        ret_type_node = node.child_by_field_name('return_type')
                        ret_type = content[ret_type_node.start_byte:ret_type_node.end_byte] if ret_type_node else None
                        
                        entity = ExtractedEntity(
                            name=name, 
                            kind=EntityKind.FUNCTION,
                            outputs=ret_type,
                            called_entities=list(set(_extract_called_entities(node)))
                        )
                        params = node.child_by_field_name('parameters')
                        if params:
                            for p in params.children:
                                if p.type in ('required_parameter', 'optional_parameter'):
                                    pname = p.child_by_field_name('pattern')
                                    if pname:
                                        entity.inputs.append(EntityField(name=content[pname.start_byte:pname.end_byte]))
                        entities.append(entity)
                
                # Traverse children
                for child in node.children:
                    traverse(child)
                    
            traverse(tree.root_node)
            
            return ParsedFileDTO(
                file_path=file_path,
                exports=list(set(exports)),
                imports=list(set(imports)),
                entities=entities
            )
            
        except Exception as e:
            return ParsedFileDTO(file_path=file_path, exports=[], imports=[], error=f"TS ParseError: {str(e)}")
            
    def _resolve_import(self, module: str, file_dir: str, root_dir: str, imports_list: List[str]):
        if module.startswith('.'):
            # It's a relative path. Resolve it manually.
            resolved = os.path.normpath(os.path.join(file_dir, module))
            try:
                rel_to_root = os.path.relpath(resolved, root_dir).replace("\\", "/")
                imports_list.append(rel_to_root)
            except ValueError:
                imports_list.append(module)
        else:
            # Check tsconfig aliases
            resolved = False
            if self._tsconfig_paths:
                for alias_prefix, target_prefix in self._tsconfig_paths:
                    if module.startswith(alias_prefix):
                        aliased = module.replace(alias_prefix, target_prefix, 1)
                        imports_list.append(aliased)
                        resolved = True
                        break
            
            if not resolved:
                # Absolute alias (like src/foo) or node_module
                imports_list.append(module)
