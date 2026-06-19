import pytest
import tempfile
import json
from pathlib import Path
from typer.testing import CliRunner

from contextly.main import app

runner = CliRunner()


@pytest.fixture
def temp_repo(monkeypatch):
    d = tempfile.TemporaryDirectory()
    try:
        path = Path(d.name).resolve()
        (path / "src").mkdir()
        (path / "src" / "index.js").write_text("console.log('test')")
        (path / "package.json").write_text(json.dumps({"dependencies": {"react": "18.0.0", "tailwindcss": "3.0.0"}}))
        
        monkeypatch.chdir(path)
        yield path
    finally:
        monkeypatch.undo()
        try:
            d.cleanup()
        except Exception:
            pass


@pytest.fixture
def temp_python_repo(monkeypatch):
    """A temp repo with Python deps to cover the py_count > 0 branch in analyze.py."""
    d = tempfile.TemporaryDirectory()
    try:
        path = Path(d.name).resolve()
        (path / "src").mkdir()
        (path / "src" / "main.py").write_text("print('hello')")
        (path / "requirements.txt").write_text("flask==2.0.0\nrequests==2.28.0")
        
        monkeypatch.chdir(path)
        yield path
    finally:
        monkeypatch.undo()
        try:
            d.cleanup()
        except Exception:
            pass

@pytest.fixture(autouse=True)
def disable_process_pool(monkeypatch):
    """
    Globally forces all ProcessPoolExecutor and ThreadPoolExecutor usage
    to use a single-threaded ThreadPoolExecutor during tests.
    This entirely prevents pytest-cov Linux CI hangs and tree-sitter thread-safety deadlocks.
    """
    import concurrent.futures
    class SingleThreadExecutor(concurrent.futures.ThreadPoolExecutor):
        def __init__(self, max_workers=None, mp_context=None, initializer=None, initargs=()):
            super().__init__(max_workers=1, initializer=initializer, initargs=initargs)
            
    monkeypatch.setattr(concurrent.futures, "ProcessPoolExecutor", SingleThreadExecutor)
    monkeypatch.setattr(concurrent.futures, "ThreadPoolExecutor", SingleThreadExecutor)


