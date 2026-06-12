import ast
from pathlib import Path
import re

class ASTBodyStripper(ast.NodeTransformer):
    """
    Strips function and method bodies from Python AST,
    replacing them with `...` (Ellipsis) while preserving docstrings.
    """
    def visit_FunctionDef(self, node: ast.FunctionDef):
        return self._strip_body(node)
        
    def visit_AsyncFunctionDef(self, node: ast.AsyncFunctionDef):
        return self._strip_body(node)
        
    def _strip_body(self, node):
        # Keep docstring if it exists
        new_body = []
        if ast.get_docstring(node):
            new_body.append(node.body[0])
            
        new_body.append(ast.Expr(value=ast.Constant(value=Ellipsis)))
        node.body = new_body
        return self.generic_visit(node)

class CompressionEngine:
    """Handles semantic compression of code files before packing."""
    
    def compress(self, path: Path, code: str) -> str:
        ext = path.suffix.lower()
        if ext == ".py":
            return self._compress_python(code)
        return code
        
    def _compress_python(self, code: str) -> str:
        try:
            tree = ast.parse(code)
            transformer = ASTBodyStripper()
            modified_tree = transformer.visit(tree)
            ast.fix_missing_locations(modified_tree)
            # unparse is available in Python 3.9+
            if hasattr(ast, "unparse"):
                return ast.unparse(modified_tree)
            return code
        except SyntaxError:
            # Fallback if there's a syntax error in the python file
            return code
            
