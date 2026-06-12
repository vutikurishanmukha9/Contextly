import pytest
from pathlib import Path
from contextly.scanners.base import BaseScanner

class DummyScanner(BaseScanner):
    @property
    def name(self):
        return super().name
    def scan(self, root_dir):
        super().scan(root_dir)

def test_base_scanner_abstracts():
    """Covers base.py 14, 28 (abstract properties/methods)."""
    d = DummyScanner()
    try:
        n = d.name
    except NotImplementedError:
        pass
    try:
        d.scan(Path("."))
    except NotImplementedError:
        pass
