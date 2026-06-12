import pytest
from pathlib import Path
from contextly.core.packer.compression import CompressionEngine

def test_compression_python():
    engine = CompressionEngine()
    code = '''
def add(a, b):
    """Adds two numbers."""
    return a + b
    
class MathHelper:
    def subtract(self, a, b):
        return a - b
'''
    compressed = engine.compress(Path("test.py"), code)
    
    assert "Adds two numbers." in compressed
    assert "return a + b" not in compressed
    assert "return a - b" not in compressed
    assert "..." in compressed
    assert "def add(a, b):" in compressed
    assert "class MathHelper:" in compressed
    assert "def subtract(self, a, b):" in compressed

def test_compression_js():
    engine = CompressionEngine()
    code = '''
/*
This is a multiline
comment
*/
function add(a, b) {
    return a + b;   
}
'''
    compressed = engine.compress(Path("test.js"), code)
    
    assert compressed == code # Returns verbatim
    
def test_compression_syntax_error():
    engine = CompressionEngine()
    code = 'def invalid_python('
    
    compressed = engine.compress(Path("test.py"), code)
    assert compressed == code # Returns verbatim if syntax error

def test_compression_other():
    engine = CompressionEngine()
    code = "hello world"
    compressed = engine.compress(Path("test.txt"), code)
    assert compressed == code
