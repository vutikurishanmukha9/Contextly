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
        (path / ".git").mkdir()
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
        (path / ".git").mkdir()
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
    class SyncExecutor:
        def submit(self, fn, *args, **kwargs):
            class MockFuture(concurrent.futures.Future):
                def __init__(self):
                    super().__init__()
                    try:
                        self.set_result(fn(*args, **kwargs))
                    except Exception as e:
                        self.set_exception(e)
            return MockFuture()
        def map(self, fn, *iterables, timeout=None, chunksize=1):
            return [fn(*args) for args in zip(*iterables)]
        def shutdown(self, wait=True, *, cancel_futures=False):
            pass
        def __enter__(self): return self
        def __exit__(self, *args): pass
            
    monkeypatch.setattr(concurrent.futures, "ProcessPoolExecutor", SyncExecutor)
    monkeypatch.setattr(concurrent.futures, "ThreadPoolExecutor", SyncExecutor)

    try:
        import pebble
        
        class MockPebbleFuture(concurrent.futures.Future):
            def __init__(self, fn):
                super().__init__()
                try:
                    self.set_result(fn())
                except Exception as e:
                    self.set_exception(e)

        class SinglePebblePool:
            __name__ = "ProcessPool"
            def __init__(self, *args, **kwargs):
                pass
            def schedule(self, fn, args=(), kwargs=None, timeout=None):
                import sys
                kwargs = kwargs or {}
                return MockPebbleFuture(lambda: fn(*args, **kwargs))
            def submit(self, fn, *args, **kwargs):
                return MockPebbleFuture(lambda: fn(*args, **kwargs))
            def __enter__(self):
                return self
            def __exit__(self, exc_type, exc_val, exc_tb):
                pass
                
        monkeypatch.setattr(pebble, "ProcessPool", SinglePebblePool)
        monkeypatch.setattr(pebble, "ThreadPool", SinglePebblePool)
    except ImportError:
        pass
        
    # Mock rich console.status to prevent background thread deadlocks with pytest stdout capture
    import contextly.utils.console as console_mod
    class DummyStatus:
        def __init__(self, *args, **kwargs): pass
        def start(self): pass
        def stop(self): pass
        def update(self, *args, **kwargs): pass
        def __enter__(self): return self
        def __exit__(self, *args): pass
    monkeypatch.setattr(console_mod.console, "status", DummyStatus)
    
    # Mock multiprocessing.get_context to prevent deadlocks on Windows under pytest
    import multiprocessing
    monkeypatch.setattr(multiprocessing, "get_context", lambda *args, **kwargs: None)


