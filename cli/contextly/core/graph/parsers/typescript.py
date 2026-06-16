import os
import json
import re
from typing import List
from .base import BaseASTParser, ParsedFileDTO

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
    
    def __init__(self):
        self.parser = None
        self._tsconfig_paths = None
        self._root_dir = None
        if HAS_TREE_SITTER:
            try:
                # Use typescript language
                self.language = get_language('typescript')
                self.parser = get_parser('typescript')
            except Exception:
                pass

    def _load_tsconfig(self, root_dir: str):
        if self._tsconfig_paths is not None and self._root_dir == root_dir:
            return
            
        self._root_dir = root_dir
        self._tsconfig_paths = []
        
        # Scan for tsconfig.json files in root and immediate subdirs
        try:
            for root, dirs, files in os.walk(root_dir):
                if "tsconfig.json" in files:
                    try:
                        with open(os.path.join(root, "tsconfig.json"), "r", encoding="utf-8") as f:
                            content = f.read()
                            # Strip comments securely without destroying JSON strings
                            safe_regex = r'("(?:\\.|[^"\\])*")|//.*?\n|/\*.*?\*/'
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
                                    
                                self._tsconfig_paths.append((alias_prefix, target_full))
                    except Exception:
                        pass
                # Don't go deeper than 1 level (i.e. root and immediate subdirs)
                try:
                    rel_parts = Path(root).relative_to(root_dir).parts
                    if len(rel_parts) >= 1:
                        dirs.clear()
                except ValueError:
                    dirs.clear()
        except Exception:
            pass

    def parse(self, file_path: str, content: str, root_dir: str) -> ParsedFileDTO:
        if not HAS_TREE_SITTER or not self.parser:
            return ParsedFileDTO(file_path=file_path, exports=[], imports=[], error="Tree-sitter not available")
            
        try:
            self._load_tsconfig(root_dir)
            tree = self.parser.parse(bytes(content, "utf8"))
            
            exports: List[str] = []
            imports: List[str] = []
            
            file_dir = os.path.dirname(os.path.abspath(os.path.join(root_dir, file_path)))
            
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
                
                # Traverse children
                for child in node.children:
                    traverse(child)
                    
            traverse(tree.root_node)
            
            return ParsedFileDTO(
                file_path=file_path,
                exports=list(set(exports)),
                imports=list(set(imports))
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
