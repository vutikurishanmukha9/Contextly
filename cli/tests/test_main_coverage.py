import pytest
import sys
from unittest.mock import patch
from contextly.main import main
from contextly.utils.exceptions import ConfigurationError

def test_main_exception_handler():
    with patch("contextly.main.app", side_effect=ValueError("Test error for coverage")):
        with pytest.raises(SystemExit) as excinfo:
            main()
        assert excinfo.value.code == 1

def test_main_configuration_error_handler():
    with patch("contextly.main.app", side_effect=ConfigurationError("Test configuration error")):
        with pytest.raises(SystemExit) as excinfo:
            main()
        assert excinfo.value.code == 1
