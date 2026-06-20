import pytest
from unittest.mock import patch
from contextly.core.memory.engine import MemoryEngine
from contextly.utils.exceptions import MemoryVaultError, MemoryVaultCorruptionError
from contextly.types.models import ProjectMemory

def test_load_memory_corrupted(tmp_path):
    engine = MemoryEngine(tmp_path)
    engine.memory_file.write_text("invalid: [yaml: :", encoding="utf-8")
    with pytest.raises(MemoryVaultCorruptionError):
        engine.load_memory()

def test_load_memory_os_error(tmp_path):
    engine = MemoryEngine(tmp_path)
    with patch("builtins.open", side_effect=OSError("Disk full")):
        with pytest.raises(OSError, match="Disk full"):
            engine.load_memory()

def test_save_memory_io_error(tmp_path):
    engine = MemoryEngine(tmp_path)
    with patch("contextly.core.memory.engine.yaml.dump", side_effect=Exception("YAML Error")):
        with pytest.raises(MemoryVaultError, match="Failed to save memory rules"):
            engine._save_memory(ProjectMemory())

def test_load_memory_validation_error(tmp_path):
    engine = MemoryEngine(tmp_path)
    engine.memory_file.write_text("rules: 'not a list'", encoding="utf-8")
    with pytest.raises(MemoryVaultCorruptionError, match="Memory file is corrupt"):
        engine.load_memory()
