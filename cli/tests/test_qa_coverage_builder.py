import pytest
from unittest.mock import patch, MagicMock
from contextly.core.graph.builder import ImportGraphBuilder

def test_builder_fallback_to_threadpool_and_sequential(tmp_path):
    builder = ImportGraphBuilder(tmp_path)
    f1 = tmp_path / "test1.py"
    f1.write_text("import os", encoding="utf-8")
    
    # Mock pebble.ProcessPool and concurrent.futures.ThreadPoolExecutor
    with patch("pebble.ProcessPool", side_effect=Exception("ProcessPool failed")), \
         patch("concurrent.futures.ThreadPoolExecutor", side_effect=Exception("ThreadPool failed")), \
         patch("contextly.core.graph.builder.ParserRegistry") as mock_registry:
         
        mock_parser = MagicMock()
        mock_parser.parse.return_value = MagicMock(file_path="test1.py", imports=[], exports=[], error=None)
        mock_registry.get_parser.return_value = mock_parser
        
        # Trigger ProcessPool -> fail -> ThreadPool -> fail -> Sequential
        builder.build([str(f1)])
        
        mock_registry.get_parser.assert_called()
        mock_parser.parse.assert_called()

def test_builder_process_chunk_fallback_pool_initialized(tmp_path):
    builder = ImportGraphBuilder(tmp_path)
    f1 = tmp_path / "test1.py"
    f1.write_text("import os", encoding="utf-8")
    
    mock_pool_instance = MagicMock()
    mock_pool_instance.schedule.side_effect = Exception("Pool schedule failed after init")
    
    mock_pool_context = MagicMock()
    mock_pool_context.__enter__.return_value = mock_pool_instance
    mock_pool_context.__exit__.return_value = False
    
    with patch("pebble.ProcessPool", return_value=mock_pool_context), \
         patch("concurrent.futures.ThreadPoolExecutor") as mock_threadpool, \
         patch("contextly.core.graph.builder.ParserRegistry") as mock_registry, \
         patch.dict('sys.modules', {'pytest': None}):
        
        mock_parser = MagicMock()
        mock_parser.parse.return_value = MagicMock(file_path="test1.py", imports=[], exports=[], error=None)
        mock_registry.get_parser.return_value = mock_parser
        
        builder.build([str(f1)])
        
        mock_threadpool.assert_not_called()
        mock_registry.get_parser.assert_called()
        mock_parser.parse.assert_called()
