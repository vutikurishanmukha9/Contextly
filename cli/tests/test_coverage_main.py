import pytest
from unittest.mock import patch, MagicMock
import sys
from pathlib import Path
from contextly.main import main

def test_main_terminal_transcript_saving(tmp_path):
    with patch("sys.argv", ["contextly", "init"]), \
         patch("contextly.main.find_project_root", return_value=tmp_path):
        try:
            main()
        except SystemExit:
            pass
        
        # Check if the export was attempted
        exports_dir = tmp_path / ".contextly" / "exports"
        assert exports_dir.exists()

def test_main_crash_fallback(tmp_path, monkeypatch):
    import tempfile
    monkeypatch.setattr(tempfile, "tempdir", str(tmp_path))
    # Test the fallback logging in main.py
    with patch("contextly.main.app", side_effect=Exception("mock crash")), \
         patch("sys.argv", ["contextly"]), \
         patch("logging.handlers.RotatingFileHandler", side_effect=OSError("mock rotating error")):
        try:
            main()
        except SystemExit:
            pass
            
        logs = list(tmp_path.glob("contextly_crash_*.log"))
        assert len(logs) > 0

def test_main_crash_ultimate_fallback(tmp_path):
    with patch("contextly.main.app", side_effect=Exception("mock crash")), \
         patch("sys.argv", ["contextly"]), \
         patch("logging.handlers.RotatingFileHandler", side_effect=OSError("mock rotating error")), \
         patch("builtins.open", side_effect=OSError("mock open error")), \
         patch("tempfile.gettempdir", return_value=str(tmp_path)):
        try:
            main()
        except SystemExit:
            pass
