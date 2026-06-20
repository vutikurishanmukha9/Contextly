import pytest
from contextly.core.graph.parsers.python import PythonASTParser

def test_python_parser_exhaustive(tmp_path):
    parser = PythonASTParser()
    content = """
__all__ = ["MyClass", "my_func", "unsupported_" + "string"]

import sys
from . import local_mod
from ..parent import other_mod
from .. import parent_mod
from .local_mod import specific

class Base1: pass

@route("/path")
@dec_name
class MyClass(sys.modules['mod'].Base, Base1):
    \"\"\"MyClass docstring\"\"\"
    field1: int
    field2: list[str] = []
    
    @classmethod
    @cache(maxsize=128)
    def my_method(self, arg1: str) -> bool:
        obj.method()
        func_call()
        return True

@deco1
@deco2(arg=1)
async def my_func(a: dict[str, int]) -> list:
    pass

complex_assign.attr = 1
my_var: int = 1
unsupported_ann.attr: str = "test"
"""
    file_path = "src/nested/module.py"
    root_dir = str(tmp_path)
    
    dto = parser.parse(file_path, content, root_dir)
    assert dto.error is None
    
    # Check __all__ parsing
    assert "MyClass" in dto.exports
    assert "my_func" in dto.exports
    
    # Check imports
    assert "sys" in dto.imports
    
    # Check classes
    my_class = next(e for e in dto.entities if e.name == "MyClass")
    assert "Base1" in my_class.parent_classes
    assert any("sys.modules" in p for p in my_class.parent_classes)
    
    assert "route" in my_class.decorators
    assert "dec_name" in my_class.decorators
    
    assert any(f.name == "field1" and f.type == "int" for f in my_class.fields)
    assert any(f.name == "field2" and f.type == "list[str]" for f in my_class.fields)
    
    method = my_class.methods[0]
    assert method.name == "my_method"
    assert method.returns == "bool"
    assert "classmethod" in method.decorators
    assert "cache" in method.decorators
    
    # Check calls
    assert "obj.method" in my_class.called_entities or "method" in my_class.called_entities
    assert "func_call" in my_class.called_entities
    
    # Check functions
    my_func = next(e for e in dto.entities if e.name == "my_func")
    assert my_func.outputs == "list"
    assert "deco1" in my_func.decorators
    assert "deco2" in my_func.decorators
    
def test_python_parser_syntax_error():
    parser = PythonASTParser()
    dto = parser.parse("test.py", "def my_func(++): pass", "/root")
    assert dto.error is not None
    assert "SyntaxError" in dto.error

def test_python_parser_size_limit():
    parser = PythonASTParser()
    content = "a = 1\n" * 100000 # > 500KB
    dto = parser.parse("test.py", content, "/root")
    assert dto.error is not None
    assert "500KB" in dto.error

def test_python_parser_relative_out_of_bounds(tmp_path):
    parser = PythonASTParser()
    content = "from ....... import x"
    dto = parser.parse("test.py", content, str(tmp_path))
    # It will fallback gracefully to the unresolvable import
    assert "x" in dto.imports or dto.error is None
