import pytest
from unittest.mock import patch, MagicMock
from pathlib import Path
import os

from contextly.utils.io import atomic_write
from contextly.utils.config import ContextlyConfig, load_config, load_config_model
from contextly.utils.exceptions import ConfigurationError

def test_atomic_write_error_cleanup(tmp_path):
    f = tmp_path / "target.txt"
    with patch("os.replace", side_effect=Exception("Replace failed")), patch("os.remove") as mock_remove:
        with pytest.raises(Exception, match="Replace failed"):
            atomic_write(f, "data")
        mock_remove.assert_called_once()

def test_atomic_write_error_cleanup_os_error(tmp_path):
    f = tmp_path / "target.txt"
    with patch("os.replace", side_effect=Exception("Replace failed")), patch("os.remove", side_effect=OSError("Already deleted")):
        with pytest.raises(Exception, match="Replace failed"):
            atomic_write(f, "data")

def test_config_pre_validate():
    cfg = ContextlyConfig.pre_validate([])
    assert cfg == {}
    
    cfg = ContextlyConfig.pre_validate({"test": None, "rules": None})
    assert cfg == {"test": {}, "rules": []}

def test_load_config_yaml_error(tmp_path):
    cfg_dir = tmp_path / ".contextly"
    cfg_dir.mkdir()
    cfg_file = cfg_dir / "config.yaml"
    cfg_file.write_text("invalid: [yaml: :", encoding="utf-8")
    
    assert load_config(tmp_path) is None

def test_load_config_model_not_dict(tmp_path):
    cfg_dir = tmp_path / ".contextly"
    cfg_dir.mkdir()
    cfg_file = cfg_dir / "config.yaml"
    cfg_file.write_text("- list item", encoding="utf-8")
    
    cfg = load_config_model(tmp_path)
    assert isinstance(cfg, ContextlyConfig)

def test_load_config_model_validation_error(tmp_path):
    cfg_dir = tmp_path / ".contextly"
    cfg_dir.mkdir()
    cfg_file = cfg_dir / "config.yaml"
    cfg_file.write_text("depth_limits:\n  analyzer: 'not an int'", encoding="utf-8")
    
    with pytest.raises(ConfigurationError):
        load_config_model(tmp_path)
        
def test_load_config_model_os_error(tmp_path):
    cfg_dir = tmp_path / ".contextly"
    cfg_dir.mkdir()
    cfg_file = cfg_dir / "config.yaml"
    cfg_file.write_text("depth_limits: {}", encoding="utf-8")
    
    with patch("builtins.open", side_effect=OSError("Permission denied")):
        with pytest.raises(OSError, match="Permission denied"):
            load_config_model(tmp_path)

def test_load_config_model_yaml_error(tmp_path):
    cfg_dir = tmp_path / ".contextly"
    cfg_dir.mkdir()
    cfg_file = cfg_dir / "config.yaml"
    cfg_file.write_text("invalid: [yaml: :", encoding="utf-8")
    
    with pytest.raises(ConfigurationError):
        load_config_model(tmp_path)
