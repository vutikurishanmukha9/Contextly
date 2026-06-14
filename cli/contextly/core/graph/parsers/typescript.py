import os
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
    Enterprise TypeScript/JavaScript parser using Tree-Sitter.
    Extracts exports and resolves import paths accurately without regex.
    """
    
    def __init__(self):
        self.parser = None
        if HAS_TREE_SITTER:
            try:
                # Use TSX language to handle both TS and TSX
                self.language = get_language('tsx')
                self.parser = get_parser('tsx')
            except Exception:
                pass

    def parse(self, file_path: str, content: str, root_dir: str) -> ParsedFileDTO:
        if not HAS_TREE_SITTER or not self.parser:
            return ParsedFileDTO(file_path=file_path, exports=[], imports=[], error="Tree-sitter not available")
            
        try:
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
            # Absolute alias (like src/foo) or node_module
            imports_list.append(module)
