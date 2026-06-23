import pytest
import os
from unittest.mock import patch, MagicMock
from pathlib import Path
from contextly.core.graph.builder import _parse_file, ImportGraphBuilder

def test_builder_parse_file_utf16_bom(tmp_path):
    import codecs
    # valid utf-16 with BOM
    file_path = tmp_path / "test_utf16.js"
    file_path.write_bytes(codecs.BOM_UTF16_LE + "console.log('utf16')".encode("utf-16-le"))
    
    # Should not silently skip binaries because it is valid UTF-16
    # But it will fall through to charset_normalizer because builder.py doesn't decode utf-16 directly
    class MockDetection:
        encoding = "utf-16"
        coherence = 0.9
        def __str__(self):
            return "parsed_utf16"
    
    class MockNormalizer:
        def best(self):
            return MockDetection()
            
    with patch("charset_normalizer.from_bytes", return_value=MockNormalizer()):
        with patch("contextly.core.graph.parsers.registry.ParserRegistry.get_parser") as mock_get_parser:
            mock_parser = MagicMock()
            mock_parser.parse.return_value = "parsed_utf16"
            mock_get_parser.return_value = mock_parser
            
            res = _parse_file("test_utf16.js", str(tmp_path))
            assert res == "parsed_utf16"

def test_builder_parse_file_utf16_no_bom_but_high_ascii(tmp_path):
    file_path = tmp_path / "test_high_ascii.js"
    # Null byte present, but no BOM, valid utf-16 chars > 30% ascii
    file_path.write_bytes("console.log('utf16')\n".encode("utf-16-le"))
    
    with patch("contextly.core.graph.parsers.registry.ParserRegistry.get_parser") as mock_get_parser:
        mock_parser = MagicMock()
        mock_parser.parse.return_value = "parsed_high_ascii"
        mock_get_parser.return_value = mock_parser
        
        res = _parse_file("test_high_ascii.js", str(tmp_path))
        assert res == "parsed_high_ascii"

def test_builder_parse_file_charset_normalizer_low_coherence(tmp_path):
    file_path = tmp_path / "test_charset.js"
    # Write something that isn't utf-8 and has no null byte
    file_path.write_bytes(b"\xc3\x28")
    
    class MockDetection:
        encoding = "mac_roman"
        coherence = 0.1
        def __str__(self):
            return "text"
            
    class MockNormalizer:
        def best(self):
            return MockDetection()
            
    with patch("charset_normalizer.from_bytes", return_value=MockNormalizer()):
        res = _parse_file("test_charset.js", str(tmp_path))
        assert res and "low encoding confidence" in res.error

def test_builder_parse_file_charset_normalizer_success(tmp_path):
    file_path = tmp_path / "test_charset.js"
    file_path.write_bytes(b"\xc3\x28")
    
    class MockDetection:
        encoding = "mac_roman"
        coherence = 0.9
        def __str__(self):
            return "valid_text"
            
    class MockNormalizer:
        def best(self):
            return MockDetection()
            
    with patch("charset_normalizer.from_bytes", return_value=MockNormalizer()):
        with patch("contextly.core.graph.parsers.registry.ParserRegistry.get_parser") as mock_get_parser:
            mock_parser = MagicMock()
            mock_parser.parse.return_value = "parsed_mac_roman"
            mock_get_parser.return_value = mock_parser
            
            res = _parse_file("test_charset.js", str(tmp_path))
            assert res == "parsed_mac_roman"

def test_builder_parse_file_charset_normalizer_no_detection(tmp_path):
    file_path = tmp_path / "test_charset.js"
    file_path.write_bytes(b"\xc3\x28")
            
    class MockNormalizer:
        def best(self):
            return None
            
    with patch("charset_normalizer.from_bytes", return_value=MockNormalizer()):
        res = _parse_file("test_charset.js", str(tmp_path))
        assert res and "undetectable encoding" in res.error

def test_builder_parse_file_unknown_extension(tmp_path):
    file_path = tmp_path / "test.unknown"
    file_path.write_text("hello")
    res = _parse_file("test.unknown", str(tmp_path))
    assert res is None

def test_builder_parse_file_unexpected_exception(tmp_path):
    file_path = tmp_path / "test.js"
    file_path.write_text("hello")
    
    with patch("contextly.core.graph.parsers.registry.ParserRegistry.get_parser", side_effect=Exception("mocked parser error")):
        res = _parse_file("test.js", str(tmp_path))
        assert res and "ParseError: mocked parser error" in res.error

def test_builder_timeout_in_wait(tmp_path, monkeypatch):
    import concurrent.futures
    file_path = tmp_path / "test.js"
    file_path.write_text("hello")
    
    builder = ImportGraphBuilder(tmp_path)
    # mock concurrent.futures.wait to return not done
    def mock_wait(*args, **kwargs):
        # returns (done, not_done)
        return set(), {MagicMock()}
        
    monkeypatch.setattr(concurrent.futures, "wait", mock_wait)
    # mock _parse_file so submit doesn't do much
    monkeypatch.setattr("contextly.core.graph.builder._parse_file", MagicMock())
    
    builder.build(["test.js"])
    
    from contextly.core.diagnostics import DiagnosticsContext
    assert any("File parsing exceeded global 120s timeout" in str(m.message) for m in DiagnosticsContext()._messages)

def test_builder_sequential_fallback_error(tmp_path, monkeypatch):
    import concurrent.futures
    file_path = tmp_path / "test.js"
    file_path.write_text("hello")
    
    builder = ImportGraphBuilder(tmp_path)
    
    def mock_pool(*args, **kwargs):
        raise RuntimeError("force fallback")
        
    def mock_parse_file(*args, **kwargs):
        raise Exception("sequential error")
        
    monkeypatch.setattr(concurrent.futures, "ProcessPoolExecutor", mock_pool)
    monkeypatch.setattr("contextly.core.graph.builder._parse_file", mock_parse_file)
    
    builder.build(["test.js"])
    
    assert builder.failed_files["test.js"] == "SequentialError: sequential error"

def test_builder_oserror_on_remove(tmp_path, monkeypatch):
    file_path = tmp_path / "test.js"
    file_path.write_text("hello")
    
    builder = ImportGraphBuilder(tmp_path)
    
    def mock_remove(*args, **kwargs):
        raise OSError("mock oserror")
        
    monkeypatch.setattr("os.remove", mock_remove)
    
    # Should not raise
    builder.build(["test.js"])
