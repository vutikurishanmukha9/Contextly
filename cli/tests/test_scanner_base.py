import pytest
from pathlib import Path
from contextly.scanners.base import BaseScanner

class DummyScanner(BaseScanner):
    @property
    def name(self):
        return "dummy"
    def scan(self, root_dir):
        return BaseScanner.scan(self, root_dir)

def test_base_scanner_abstracts():
    """Covers base.py 14, 28 (abstract properties/methods)."""
    d = DummyScanner()
    assert d.scan(Path(".")) is None
    assert BaseScanner.name.fget(d) is None
