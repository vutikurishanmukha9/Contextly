from pathlib import Path
from conftest import runner, app


def test_init_cmd(temp_repo):
    result = runner.invoke(app, ["init"], catch_exceptions=False)
    assert result.exit_code == 0
    assert "Contextly initialized successfully!" in result.stdout
    assert (temp_repo / ".contextly" / "config.yaml").exists()


def test_init_cmd_already_exists(temp_repo):
    runner.invoke(app, ["init"])
    result = runner.invoke(app, ["init"])
    assert result.exit_code == 0
    assert "already initialized" in result.stdout.lower() or "already exists" in result.stdout.lower()


def test_init_cmd_os_error(temp_repo, monkeypatch):
    import pathlib
    original_mkdir = pathlib.Path.mkdir
    def mock_mkdir(self, *args, **kwargs):
        if self.name == ".contextly" or ".contextly" in self.parts:
            raise PermissionError("Access denied")
        return original_mkdir(self, *args, **kwargs)
        
    monkeypatch.setattr(pathlib.Path, "mkdir", mock_mkdir, raising=False)
    if hasattr(pathlib, "PosixPath"):
        monkeypatch.setattr(pathlib.PosixPath, "mkdir", mock_mkdir, raising=False)
    if hasattr(pathlib, "WindowsPath"):
        monkeypatch.setattr(pathlib.WindowsPath, "mkdir", mock_mkdir, raising=False)
        
    result = runner.invoke(app, ["init"])
    assert result.exit_code == 1
    assert "Error initializing" in result.stdout
