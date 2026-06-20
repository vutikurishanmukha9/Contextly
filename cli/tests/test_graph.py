import pytest
import os
from pathlib import Path
from contextly.core.graph.builder import ImportGraphBuilder, _parse_file
from contextly.core.graph.assembler import GraphAssembler
from contextly.core.graph.parsers.python import PythonASTParser
from contextly.core.graph.parsers.typescript import TypeScriptASTParser, HAS_TREE_SITTER
from contextly.core.graph.parsers.base import ParsedFileDTO

def test_python_ast_parser(tmp_path):
    parser = PythonASTParser()
    content = """
import os
from .local import helper
from ..parent import other

def my_func():
    pass

class MyClass:
    def method(self):
        def inner():
            pass
"""
    file_path = "src/main.py"
    (tmp_path / "src").mkdir()
    (tmp_path / "src" / "main.py").write_text(content)
    
    dto = parser.parse(file_path, content, str(tmp_path))
    assert dto.file_path == file_path
    assert not dto.error
    assert "MyClass" in dto.exports
    assert "my_func" in dto.exports
    assert "method" not in dto.exports
    assert "inner" not in dto.exports
    assert "os" in dto.imports
    assert "src/local" in dto.imports # .local -> src/local
    assert "parent" in dto.imports # ..parent -> parent
    
def test_python_ast_parser_syntax_error():
    parser = PythonASTParser()
    dto = parser.parse("broken.py", "def broken(", "/tmp")
    assert dto.error
    assert "SyntaxError" in dto.error

def test_typescript_ast_parser(tmp_path):
    if not HAS_TREE_SITTER:
        pytest.skip("Tree-sitter not installed")
        
    parser = TypeScriptASTParser()
    content = """
import { Something } from './helper';
import defaultExport from '../parent/utils';
import * as path from 'path';

export const MyVar = 1;
export function myFunc() {}
export class MyClass {}
"""
    file_path = "src/index.ts"
    (tmp_path / "src").mkdir()
    (tmp_path / "src" / "index.ts").write_text(content)
    
    dto = parser.parse(file_path, content, str(tmp_path))
    assert not dto.error
    assert "MyVar" in dto.exports
    assert "myFunc" in dto.exports
    assert "MyClass" in dto.exports
    
    assert "src/helper" in dto.imports
    assert "parent/utils" in dto.imports
    assert "path" in dto.imports
    
def test_typescript_ast_parser_error():
    if not HAS_TREE_SITTER:
        pytest.skip("Tree-sitter not installed")
    parser = TypeScriptASTParser()
    dto = parser.parse("src/index.ts", "import {", "/tmp")
    # Tree-sitter is forgiving but should not throw Python exceptions
    assert not dto.error
    assert len(dto.exports) == 0

def test_graph_assembler_index_resolution():
    assembler = GraphAssembler()
    dto1 = ParsedFileDTO(file_path="src/utils/index.ts", exports=["func"], imports=[])
    dto2 = ParsedFileDTO(file_path="src/main.ts", exports=[], imports=["src/utils"])
    dto3 = ParsedFileDTO(file_path="src/lib/__init__.py", exports=["libfunc"], imports=[])
    dto4 = ParsedFileDTO(file_path="src/app.py", exports=[], imports=["src/lib"])
    
    id1 = assembler.add_node(dto1)
    id2 = assembler.add_node(dto2)
    id3 = assembler.add_node(dto3)
    id4 = assembler.add_node(dto4)
    
    assembler.build_relationships([dto1, dto2, dto3, dto4])
    
    # main -> utils/index
    assert any(r.source_id == id2 and r.target_id == id1 for r in assembler.graph.relationships)
    # app -> lib/__init__
    assert any(r.source_id == id4 and r.target_id == id3 for r in assembler.graph.relationships)

def test_parse_file_typescript():
    import tempfile
    tmp = Path(tempfile.mkdtemp())
    (tmp / "src").mkdir()
    (tmp / "src" / "index.ts").write_text("export const x = 1;")
    res = _parse_file("src/index.ts", str(tmp))
    assert res is not None
    assert "x" in res.exports
    
def test_python_ast_parser_relative():
    parser = PythonASTParser()
    content = "from .. import parent\nfrom .sibling import obj"
    dto = parser.parse("src/nested/module.py", content, "/tmp")
    assert "parent" in dto.imports or "src/parent" in dto.imports


def test_graph_assembler():
    assembler = GraphAssembler()
    
    dto1 = ParsedFileDTO(
        file_path="src/index.ts",
        exports=["App"],
        imports=["src/components/Button"]
    )
    
    dto2 = ParsedFileDTO(
        file_path="src/components/Button.ts",
        exports=["Button"],
        imports=[]
    )
    
    id1 = assembler.add_node(dto1)
    id2 = assembler.add_node(dto2)
    
    assembler.build_relationships([dto1, dto2])
    
    assert len(assembler.graph.nodes) == 2
    assert len(assembler.graph.relationships) == 1
    
    rel = assembler.graph.relationships[0]
    assert rel.source_id == id1
    assert rel.target_id == id2


def test_graph_assembler_node_ids_are_deterministic():
    dto = ParsedFileDTO(file_path="src/index.ts", exports=["App"], imports=[])

    first = GraphAssembler().add_node(dto)
    second = GraphAssembler().add_node(dto)

    assert first == second
    assert first.startswith("file_")

def test_import_graph_builder(tmp_path):
    (tmp_path / "src").mkdir()
    (tmp_path / "src" / "main.py").write_text("import sys\nfrom . import utils")
    (tmp_path / "src" / "utils.py").write_text("def helper(): pass")
    
    builder = ImportGraphBuilder(tmp_path)
    graph = builder.build()
    
    assert len(graph.nodes) == 3
    # Ensure relationships are correctly formed
    # Relationships count should be 1 (main.py -> utils.py)
    # Plus possibly 0 since sys is not a local node
    
    # Check if a relationship between main and utils was created
    rel = None
    for r in graph.relationships:
        source_node = next(n for n in graph.nodes if n.id == r.source_id)
        target_node = next(n for n in graph.nodes if n.id == r.target_id)
        if "main.py" in source_node.path and "utils.py" in target_node.path:
            rel = r
            break
            
    assert rel is not None

def test_parse_file_module_function():
    # Test the standalone function used by ProcessPoolExecutor
    res = _parse_file("nonexistent.py", "/tmp/does/not/exist")
    assert res is None # Should swallow file not found exception

def test_typescript_ast_parser_tsconfig(tmp_path):
    if not HAS_TREE_SITTER:
        pytest.skip("Tree-sitter not installed")
        
    parser = TypeScriptASTParser()
    
    # Create a fake tsconfig.json
    tsconfig_content = """
    {
      "compilerOptions": {
        "paths": {
          "@/*": ["./src/*"],
          "~/*": ["./lib/*"]
        }
      }
    }
    """
    (tmp_path / "tsconfig.json").write_text(tsconfig_content)
    (tmp_path / "src").mkdir()
    
    content = """
    import { Button } from "@/components/ui/button";
    import { util } from "~/utils/helpers";
    """
    file_path = "src/index.ts"
    (tmp_path / "src" / "index.ts").write_text(content)
    
    dto = parser.parse(file_path, content, str(tmp_path))
    assert not dto.error
    assert "src/components/ui/button" in dto.imports
    assert "lib/utils/helpers" in dto.imports


def test_typescript_ast_parser_tsconfig_depth_limit(tmp_path):
    parser = TypeScriptASTParser()
    
    # Root level
    tsconfig_root = '{"compilerOptions": {"paths": {"@root/*": ["./root/*"]}}}'
    (tmp_path / "tsconfig.json").write_text(tsconfig_root)
    
    # Depth 1: src/
    (tmp_path / "src").mkdir()
    tsconfig_depth1 = '{"compilerOptions": {"paths": {"@src/*": ["./src/*"]}}}'
    (tmp_path / "src" / "tsconfig.json").write_text(tsconfig_depth1)
    
    # Depth 2: src/components/
    (tmp_path / "src" / "components").mkdir()
    tsconfig_depth2 = '{"compilerOptions": {"paths": {"@nested/*": ["./nested/*"]}}}'
    (tmp_path / "src" / "components" / "tsconfig.json").write_text(tsconfig_depth2)
    
    parser._load_tsconfig(str(tmp_path))
    aliases = [p[0] for p in parser._tsconfig_paths]
    
    assert "@root/" in aliases
    assert "@src/" in aliases
    assert "@nested/" not in aliases


def test_graph_assembler_node_type_segment_classification():
    from contextly.types.models import NodeType
    assembler = GraphAssembler()
    
    # userService.py
    dto1 = ParsedFileDTO(file_path="src/components/userService.py", exports=["UserService"], imports=[])
    node_id1 = assembler.add_node(dto1)
    node1 = next(n for n in assembler.graph.nodes if n.id == node_id1)
    assert node1.type == NodeType.FILE
    
    # service_worker_bootstrap.py
    dto2 = ParsedFileDTO(file_path="src/auth/service_worker_bootstrap.py", exports=["run"], imports=[])
    node_id2 = assembler.add_node(dto2)
    node2 = next(n for n in assembler.graph.nodes if n.id == node_id2)
    assert node2.type == NodeType.FILE
    
    # model inside a model folder
    dto3 = ParsedFileDTO(file_path="src/models/user.py", exports=["User"], imports=[])
    node_id3 = assembler.add_node(dto3)
    node3 = next(n for n in assembler.graph.nodes if n.id == node_id3)
    assert node3.type == NodeType.FILE


def test_import_graph_builder_thread_safety(tmp_path):
    (tmp_path / "src").mkdir()
    for i in range(50):
        (tmp_path / "src" / f"file_{i}.py").write_text("def run(): pass")
        
    builder = ImportGraphBuilder(tmp_path)
    # Verify parsing handles files safely
    graph = builder.build()
    assert len(graph.nodes) == 100

def test_python_ast_parser_explicit_all(tmp_path):
    parser = PythonASTParser()
    content = """
__all__ = ["foo", "bar"]

def foo():
    pass

def bar():
    pass

def baz():
    pass
"""
    file_path = "src/main.py"
    (tmp_path / "src").mkdir(exist_ok=True)
    (tmp_path / "src" / "main.py").write_text(content)
    
    dto = parser.parse(file_path, content, str(tmp_path))
    assert not dto.error
    assert set(dto.exports) == {"foo", "bar"}
    assert "baz" not in dto.exports

    content_tuple = """
__all__ = ('single_item',)

def single_item():
    pass
"""
    dto_tuple = parser.parse(file_path, content_tuple, str(tmp_path))
    assert not dto_tuple.error
    assert dto_tuple.exports == ["single_item"]

