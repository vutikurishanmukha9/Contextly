from conftest import runner, app


def test_export_cmd_validation(temp_repo):
    result = runner.invoke(app, ["export", "frontend"])
    assert result.exit_code == 1
    assert "Context-Ly is not initialized" in result.stdout


def test_export_cmd_not_analyzed(temp_repo):
    runner.invoke(app, ["init"])
    result = runner.invoke(app, ["export", "frontend"])
    assert result.exit_code == 1
    assert "PROJECT_CONTEXT.md not found" in result.stdout


def test_export_cmd_success(temp_repo, monkeypatch):
    runner.invoke(app, ["init"])
    runner.invoke(app, ["analyze"])
    runner.invoke(app, ["pack", "src", "--name", "frontend"])

    import pyperclip
    monkeypatch.setattr(pyperclip, "copy", lambda x: None)

    result = runner.invoke(app, ["export", "frontend"])
    assert result.exit_code == 0
    assert "Successfully copied to clipboard" in result.stdout
    assert "You can now paste the contents directly into Claude or ChatGPT." in result.stdout

    exports_dir = temp_repo / ".contextly" / "exports"
    exports = list(exports_dir.glob("*.md"))
    assert len(exports) == 1

    fused_content = exports[0].read_text(encoding="utf-8")
    assert "Architecture Map" in fused_content
    assert '<context_pack name="frontend">' in fused_content


def test_export_cmd_success_escaping(temp_repo, monkeypatch):
    """Verifies that special characters in pack names are HTML escaped."""
    runner.invoke(app, ["init"])
    runner.invoke(app, ["analyze"])
    runner.invoke(app, ["pack", "src", "--name", "front & back"])

    import pyperclip
    monkeypatch.setattr(pyperclip, "copy", lambda x: None)

    result = runner.invoke(app, ["export", "front & back"])
    assert result.exit_code == 0

    exports_dir = temp_repo / ".contextly" / "exports"
    exports = list(exports_dir.glob("*.md"))
    
    fused_content = exports[0].read_text(encoding="utf-8")
    assert '<context_pack name="front &amp; back">' in fused_content


def test_export_cmd_normalizes_pack_name_for_filesystem(temp_repo, monkeypatch):
    """Export should mirror pack's safe filename behavior for path-like names."""
    runner.invoke(app, ["init"])
    runner.invoke(app, ["analyze"])
    runner.invoke(app, ["pack", "src", "--name", "frontend"])

    import pyperclip
    monkeypatch.setattr(pyperclip, "copy", lambda x: None)

    result = runner.invoke(app, ["export", "../frontend"])
    assert result.exit_code == 0

    exports_dir = temp_repo / ".contextly" / "exports"
    exports = list(exports_dir.glob("*.md"))
    assert len(exports) == 1
    assert exports[0].name.startswith("export_frontend_")

    fused_content = exports[0].read_text(encoding="utf-8")
    assert '<context_pack name="frontend">' in fused_content


def test_export_cmd_missing_pack(temp_repo):
    runner.invoke(app, ["init"])
    runner.invoke(app, ["analyze"])
    result = runner.invoke(app, ["export", "non_existent"])
    assert result.exit_code == 1
    assert "not found at" in result.stdout


def test_export_cmd_read_error(temp_repo, monkeypatch):
    runner.invoke(app, ["init"])
    runner.invoke(app, ["analyze"])
    runner.invoke(app, ["pack", "src", "--name", "frontend"])

    import builtins
    original_open = builtins.open
    def mock_open(*args, **kwargs):
        if "frontend.contextpack.md" in str(args[0]):
            raise PermissionError("Access denied")
        return original_open(*args, **kwargs)

    monkeypatch.setattr(builtins, "open", mock_open)
    result = runner.invoke(app, ["export", "frontend"])
    assert result.exit_code == 1
    assert "Error reading files" in result.stdout


def test_export_cmd_write_error(temp_repo, monkeypatch):
    runner.invoke(app, ["init"])
    runner.invoke(app, ["analyze"])
    runner.invoke(app, ["pack", "src", "--name", "frontend"])

    import builtins
    original_open = builtins.open
    def mock_open(*args, **kwargs):
        if "export_frontend" in str(args[0]):
            raise PermissionError("Access denied")
        return original_open(*args, **kwargs)

    monkeypatch.setattr(builtins, "open", mock_open)
    result = runner.invoke(app, ["export", "frontend"])
    assert result.exit_code == 1
    assert "Error writing export file" in result.stdout


def test_export_cmd_clipboard_error(temp_repo, monkeypatch):
    runner.invoke(app, ["init"])
    runner.invoke(app, ["analyze"])
    runner.invoke(app, ["pack", "src"])

    import pyperclip
    def mock_copy(*args, **kwargs):
        raise Exception("Clipboard not available")
    monkeypatch.setattr(pyperclip, "copy", mock_copy)

    result = runner.invoke(app, ["export", "src"])
    assert result.exit_code == 0
    assert "Could not copy to clipboard" in result.stdout
    assert "Open the local export file to copy the contents manually." in result.stdout
    assert "You can now paste the contents directly" not in result.stdout


def test_export_cmd_context_read_error(temp_repo, monkeypatch):
    runner.invoke(app, ["init"])
    runner.invoke(app, ["analyze"])
    runner.invoke(app, ["pack", "src"])
    import builtins
    original_open = builtins.open
    def mock_open(*args, **kwargs):
        if "PROJECT_CONTEXT.md" in str(args[0]):
            raise PermissionError("Access denied")
        return original_open(*args, **kwargs)
    monkeypatch.setattr(builtins, "open", mock_open)
    result = runner.invoke(app, ["export", "src"])
    assert result.exit_code == 1
    assert "Error reading files" in result.stdout

def test_export_cmd_env(temp_repo, monkeypatch):
    runner.invoke(app, ["init"])
    runner.invoke(app, ["analyze"])
    runner.invoke(app, ["pack", "src", "--name", "frontend"])

    result = runner.invoke(app, ["export", "frontend", "--env"])
    assert result.exit_code == 0
    assert "export CONTEXTLY_PACK=" in result.stdout

def test_export_cmd_env_read_error(temp_repo, monkeypatch):
    runner.invoke(app, ["init"])
    runner.invoke(app, ["analyze"])
    runner.invoke(app, ["pack", "src", "--name", "frontend"])

    def mock_read_text(*args, **kwargs):
        raise OSError("Failed read")
        
    from pathlib import Path
    monkeypatch.setattr(Path, "read_text", mock_read_text)

    result = runner.invoke(app, ["export", "frontend", "--env"])
    assert result.exit_code == 1
    assert "Error generating env payload" in result.stderr

def test_export_cmd_save_command_result_error(temp_repo, monkeypatch):
    runner.invoke(app, ["init"])
    runner.invoke(app, ["analyze"])
    runner.invoke(app, ["pack", "src", "--name", "frontend"])

    import contextly.commands.export as exp_mod
    def mock_save(*args, **kwargs):
        raise OSError("Save failed")
    
    monkeypatch.setattr(exp_mod, "save_command_result", mock_save)
    import pyperclip
    monkeypatch.setattr(pyperclip, "copy", lambda x: None)

    result = runner.invoke(app, ["export", "frontend"])
    assert result.exit_code == 0
    assert "Warning: Could not save unified result file" in result.stdout
