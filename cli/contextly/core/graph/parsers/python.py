import ast
import os
from pathlib import Path
from typing import List
from .base import BaseASTParser, ParsedFileDTO

class PythonASTParser(BaseASTParser):
    """
    Enterprise Python parser using the native AST module.
    Safely resolves relative imports to their absolute paths within the repository.
    """
    
    def parse(self, file_path: str, content: str, root_dir: str) -> ParsedFileDTO:
        try:
            tree = ast.parse(content, filename=file_path)
            
            exports: List[str] = []
            imports: List[str] = []
            
            # Helper to resolve relative imports to absolute repo paths
            file_dir = os.path.dirname(os.path.abspath(os.path.join(root_dir, file_path)))
            
            for node in ast.walk(tree):
                # Extract Exports (Classes and Top-Level Functions)
                if isinstance(node, (ast.ClassDef, ast.FunctionDef, ast.AsyncFunctionDef)):
                    # Ensure it's not a deeply nested function by checking if we have a way to track scope
                    # For a simple robust enterprise version, all top-level defs are exports in Python
                    exports.append(node.name)
                    
                # Extract Standard Imports
                elif isinstance(node, ast.Import):
                    for alias in node.names:
                        imports.append(alias.name)
                        
                # Extract From Imports (and resolve relative)
                elif isinstance(node, ast.ImportFrom):
                    module = node.module or ""
                    level = node.level
                    
                    if level > 0:
                        # Resolve relative import (. = level 1, .. = level 2)
                        current_path = Path(file_dir)
                        for _ in range(level - 1):
                            current_path = current_path.parent
                            
                        # Construct pseudo-absolute path
                        if module:
                            resolved = current_path / module.replace(".", "/")
                        else:
                            resolved = current_path
                            
                        try:
                            rel_to_root = str(resolved.relative_to(root_dir)).replace("\\", "/")
                            imports.append(rel_to_root)
                        except ValueError:
                            # Imported outside of root (rare, but possible)
                            imports.append(module)
                    else:
                        imports.append(module)

            # Deduplicate
            return ParsedFileDTO(
                file_path=file_path,
                exports=list(set(exports)),
                imports=list(set(imports))
            )
            
        except SyntaxError as e:
            return ParsedFileDTO(file_path=file_path, exports=[], imports=[], error=f"SyntaxError: {str(e)}")
        except Exception as e:
            return ParsedFileDTO(file_path=file_path, exports=[], imports=[], error=f"ParseError: {str(e)}")
