import pytest
import tempfile
import json
from pathlib import Path
from typer.testing import CliRunner

from contextly.main import app

runner = CliRunner()



def test_init_cmd(temp_repo):
    result = runner.invoke(app, ["init"], catch_exceptions=False)
    assert result.exit_code == 0
    assert "Contextly initialized successfully!" in result.stdout
    assert (temp_repo / ".contextly" / "config.yaml").exists()

def test_init_cmd_already_exists(temp_repo):
    runner.invoke(app, ["init"])
    # Run again
    result = runner.invoke(app, ["init"])
    assert result.exit_code == 0
    assert "already initialized" in result.stdout.lower() or "already exists" in result.stdout.lower()

def test_init_cmd_os_error(temp_repo, monkeypatch):
    # init.py: target_dir.exists() check on line 10, then mkdir on line 16,
    # caught by except (OSError, PermissionError) on line 47.
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
    assert result.exit_code != 0 or "Error initializing" in result.stdout

def test_analyze_cmd_claude(temp_repo):
    print("running init")
    runner.invoke(app, ["init"])
    print("running analyze")
    result = runner.invoke(app, ["analyze", "--model", "claude"])
    print("analyze done", result.stdout, result.exception)
    assert result.exit_code == 0
    assert "Repository scan complete" in result.stdout
    
    ctx_path = temp_repo / "PROJECT_CONTEXT.md"
    assert ctx_path.exists()
    
    content = ctx_path.read_text(encoding="utf-8")
    assert "<project_context>" in content

def test_analyze_cmd_chatgpt(temp_repo):
    runner.invoke(app, ["init"])
    result = runner.invoke(app, ["analyze", "--model", "chatgpt"])
    assert result.exit_code == 0
    
    ctx_path = temp_repo / "PROJECT_CONTEXT.md"
    assert ctx_path.exists()
    
    content = ctx_path.read_text(encoding="utf-8")
    assert "## Stack Identity" in content

def test_analyze_cmd_python_deps(temp_python_repo):
    """Covers analyze.py line 80: table.add_row('Python Dependencies', ...) when py_count > 0."""
    runner.invoke(app, ["init"])
    result = runner.invoke(app, ["analyze"])
    assert result.exit_code == 0
    assert "Python Dependencies" in result.stdout

def test_pack_cmd(temp_repo):
    runner.invoke(app, ["init"])
    result = runner.invoke(app, ["pack", "src", "--name", "frontend"])
    assert result.exit_code == 0
    assert "Context Pack 'frontend' created!" in result.stdout
    
    pack_path = temp_repo / ".contextly" / "packs" / "frontend.contextpack.md"
    assert pack_path.exists()
    content = pack_path.read_text(encoding="utf-8")
    assert "## File: `src/index.js`" in content

def test_export_cmd_validation(temp_repo):
    # Try exporting without PROJECT_CONTEXT.md
    result = runner.invoke(app, ["export", "frontend"])
    assert result.exit_code == 1
    assert "Context-Ly is not initialized" in result.stdout

def test_export_cmd_success(temp_repo, monkeypatch):
    runner.invoke(app, ["init"])
    runner.invoke(app, ["analyze"])
    runner.invoke(app, ["pack", "src", "--name", "frontend"])
    
    # Mock pyperclip.copy to succeed (headless CI has no clipboard)
    import pyperclip
    monkeypatch.setattr(pyperclip, "copy", lambda x: None)
    
    result = runner.invoke(app, ["export", "frontend"])
    assert result.exit_code == 0
    assert "Successfully copied to clipboard" in result.stdout
    
    exports_dir = temp_repo / ".contextly" / "exports"
    exports = list(exports_dir.glob("*.md"))
    assert len(exports) == 1
    
    fused_content = exports[0].read_text(encoding="utf-8")
    assert "Architecture Map" in fused_content
    assert "<context_pack name=\"frontend\">" in fused_content

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

def test_learn_cmd_auto(temp_repo):
    runner.invoke(app, ["init"])
    runner.invoke(app, ["analyze"])
    # learn --auto discovers TailwindCSS pattern and prompts Confirm.ask() for each.
    # We provide 'y\n' to confirm saving.
    result = runner.invoke(app, ["learn", "--auto"], input="y\n")
    assert result.exit_code == 0
    assert "Discovered Conventions" in result.stdout
    assert "Successfully saved" in result.stdout

def test_learn_cmd_auto_duplicate(temp_repo):
    """Covers learn.py line 64: 'Skipped (Already in memory)' when add_rule returns False."""
    runner.invoke(app, ["init"])
    runner.invoke(app, ["analyze"])
    # First run: save the TailwindCSS rule
    runner.invoke(app, ["learn", "--auto"], input="y\n")
    # Second run: same rule already in memory, add_rule returns False
    result = runner.invoke(app, ["learn", "--auto"], input="y\n")
    assert result.exit_code == 0
    assert "Already in memory" in result.stdout

def test_learn_cmd_save_error(temp_repo, monkeypatch):
    runner.invoke(app, ["init"])
    runner.invoke(app, ["analyze"])
    # MemoryEngine writes to rules.yaml (not rules.json) via _save_memory.
    # We mock builtins.open to raise when writing rules.yaml.
    import builtins
    original_open = builtins.open
    def mock_open(*args, **kwargs):
        path_str = str(args[0]) if args else ""
        if "rules.yaml" in path_str:
            mode = kwargs.get("mode", "")
            if not mode and len(args) > 1:
                mode = str(args[1])
            if "w" in mode:
                raise PermissionError("Access denied")
        return original_open(*args, **kwargs)
    monkeypatch.setattr(builtins, "open", mock_open)
    # Provide 'y\n' to confirm saving the discovered TailwindCSS pattern
    result = runner.invoke(app, ["learn", "--auto"], input="y\n")
    # The PermissionError should propagate and cause an error
    assert result.exit_code == 1 or "Error" in result.stdout or result.exception is not None

def test_discover_cmd_success(temp_repo):
    runner.invoke(app, ["init"])
    runner.invoke(app, ["analyze"])
    result = runner.invoke(app, ["discover"])
    assert result.exit_code == 0
    assert "Pattern Discovery Complete" in result.stdout
    assert "TailwindCSS" in result.stdout

def test_discover_cmd_no_patterns(temp_repo):
    runner.invoke(app, ["init"])
    runner.invoke(app, ["analyze"])
    # Remove package.json to avoid finding patterns
    (temp_repo / "package.json").unlink()
    result = runner.invoke(app, ["discover"])
    assert result.exit_code == 0
    assert "No recognizable architectural patterns" in result.stdout

def test_discover_cmd_scanner_error(temp_repo, monkeypatch):
    runner.invoke(app, ["init"])
    runner.invoke(app, ["analyze"])
    import contextly.scanners.patterns as pat_mod
    from contextly.scanners.base import ScannerError
    
    def mock_scan(*args, **kwargs):
        raise ScannerError("Pattern scan failed")
        
    monkeypatch.setattr(pat_mod.PatternScanner, "scan", mock_scan)
    result = runner.invoke(app, ["discover"])
    assert result.exit_code == 1
    assert "Scanner Error" in result.stdout

def test_discover_cmd_contextly_error(temp_repo, monkeypatch):
    runner.invoke(app, ["init"])
    runner.invoke(app, ["analyze"])
    import contextly.scanners.patterns as pat_mod
    from contextly.utils.exceptions import ContextlyError
    
    def mock_scan(*args, **kwargs):
        raise ContextlyError("Contextly failed")
        
    monkeypatch.setattr(pat_mod.PatternScanner, "scan", mock_scan)
    result = runner.invoke(app, ["discover"])
    assert result.exit_code == 1
    assert "Context-Ly Error" in result.stdout

def test_inspect_cmd(temp_repo):
    runner.invoke(app, ["init"])
    result = runner.invoke(app, ["inspect"])
    assert result.exit_code == 0
    assert "Inspection complete" in result.stdout
    assert "package.json" in result.stdout

def test_inspect_cmd_validation_error(temp_repo, monkeypatch):
    import contextly.commands.inspect as insp_mod
    from contextly.utils.exceptions import ValidationError
    def mock_req(*args, **kwargs):
        raise ValidationError("Not a directory")
    monkeypatch.setattr(insp_mod, "require_directory_exists", mock_req)
    result = runner.invoke(app, ["inspect"])
    assert result.exit_code == 1
    assert "Error:" in result.stdout

def test_inspect_cmd_stat_permission_error(temp_repo, monkeypatch):
    runner.invoke(app, ["init"])
    target = temp_repo / "unreadable.txt"
    target.write_text("test")
    
    import pathlib
    original_is_file = pathlib.Path.is_file
    def mock_is_file(self):
        if self.name == "unreadable.txt":
            if self.exists():
                self.unlink()
            return True
        return original_is_file(self)
        
    monkeypatch.setattr(pathlib.Path, "is_file", mock_is_file, raising=False)
    if hasattr(pathlib, "PosixPath"):
        monkeypatch.setattr(pathlib.PosixPath, "is_file", mock_is_file, raising=False)
    if hasattr(pathlib, "WindowsPath"):
        monkeypatch.setattr(pathlib.WindowsPath, "is_file", mock_is_file, raising=False)
        
    result = runner.invoke(app, ["inspect"])
    assert result.exit_code == 0

def test_discover_cmd_validation_error(temp_repo, monkeypatch):
    import contextly.commands.discover as disc_mod
    from contextly.utils.exceptions import ValidationError
    def mock_req(*args, **kwargs):
        raise ValidationError("Not initialized")
    monkeypatch.setattr(disc_mod, "require_contextly_initialized", mock_req)
    result = runner.invoke(app, ["discover"])
    assert result.exit_code == 1
    assert "Error:" in result.stdout

def test_memory_cmd(temp_repo):
    runner.invoke(app, ["init"])
    runner.invoke(app, ["analyze"])
    # Empty memory initially
    res1 = runner.invoke(app, ["memory"])
    assert res1.exit_code == 0
    assert "memory is currently empty" in res1.stdout
    
    # Learn a convention
    runner.invoke(app, ["learn", "--auto"], input="y\n")
    
    # Now it should have 1 rule
    res2 = runner.invoke(app, ["memory"])
    assert res2.exit_code == 0
    assert "Stored Memory" in res2.stdout
    assert "Found 1 rules" in res2.stdout
    assert "TailwindCSS" in res2.stdout

def test_pack_cmd_validation(temp_repo):
    runner.invoke(app, ["init"])
    # Target directory doesn't exist
    result = runner.invoke(app, ["pack", "non_existent_dir"])
    assert result.exit_code == 1
    assert "Target directory does not exist" in result.stdout

def test_learn_cmd_manual(temp_repo):
    runner.invoke(app, ["init"])
    runner.invoke(app, ["analyze"])
    # Run without --auto
    result = runner.invoke(app, ["learn"])
    assert result.exit_code == 0
    assert "Manual learning is currently disabled" in result.stdout

def test_learn_cmd_auto_skip(temp_repo):
    runner.invoke(app, ["init"])
    runner.invoke(app, ["analyze"])
    # We provide 'n\n' to simulate skipping the discovered pattern
    result = runner.invoke(app, ["learn", "--auto"], input="n\n")
    assert result.exit_code == 0
    assert "Skipped." in result.stdout
    assert "No new rules were saved" in result.stdout

def test_learn_cmd_scanner_error(temp_repo, monkeypatch):
    runner.invoke(app, ["init"])
    runner.invoke(app, ["analyze"])
    import contextly.scanners.patterns as pat_mod
    from contextly.scanners.base import ScannerError
    
    def mock_scan(*args, **kwargs):
        raise ScannerError("Scan failed")
        
    monkeypatch.setattr(pat_mod.PatternScanner, "scan", mock_scan)
    result = runner.invoke(app, ["learn", "--auto"])
    assert result.exit_code == 1
    assert "Scanner Error" in result.stdout

def test_learn_cmd_contextly_error(temp_repo, monkeypatch):
    runner.invoke(app, ["init"])
    runner.invoke(app, ["analyze"])
    import contextly.scanners.patterns as pat_mod
    from contextly.utils.exceptions import ContextlyError
    
    def mock_scan(*args, **kwargs):
        raise ContextlyError("Contextly failed")
        
    monkeypatch.setattr(pat_mod.PatternScanner, "scan", mock_scan)
    result = runner.invoke(app, ["learn", "--auto"])
    assert result.exit_code == 1
    assert "Context-Ly Error" in result.stdout

def test_learn_cmd_no_patterns(temp_repo):
    runner.invoke(app, ["init"])
    runner.invoke(app, ["analyze"])
    (temp_repo / "package.json").unlink()
    result = runner.invoke(app, ["learn", "--auto"])
    assert result.exit_code == 0
    assert "No new recognizable conventions discovered" in result.stdout

def test_learn_cmd_validation_error(temp_repo, monkeypatch):
    import contextly.commands.learn as learn_mod
    from contextly.utils.exceptions import ValidationError
    def mock_req(*args, **kwargs):
        raise ValidationError("Not initialized")
    monkeypatch.setattr(learn_mod, "require_contextly_initialized", mock_req)
    result = runner.invoke(app, ["learn"])
    assert result.exit_code == 1
    assert "Error:" in result.stdout

def test_memory_cmd_validation_error(temp_repo, monkeypatch):
    import contextly.commands.memory as mem_mod
    from contextly.utils.exceptions import ValidationError
    def mock_req(*args, **kwargs):
        raise ValidationError("Not initialized")
    monkeypatch.setattr(mem_mod, "require_contextly_initialized", mock_req)
    result = runner.invoke(app, ["memory"])
    assert result.exit_code == 1
    assert "Error:" in result.stdout

def test_pack_cmd_empty_name(temp_repo):
    runner.invoke(app, ["init"])
    # Target is '.' — resolved .name is the temp dir name, not '.'
    result = runner.invoke(app, ["pack", "."])
    assert result.exit_code == 0
    pack_name = temp_repo.name
    assert f"Context Pack '{pack_name}' created!" in result.stdout

def test_pack_cmd_explicit_dot_name(temp_repo):
    """Covers pack.py line 32: the pack_name == '.' branch."""
    runner.invoke(app, ["init"])
    # Pass --name '.' explicitly to trigger pack_name == '.'
    result = runner.invoke(app, ["pack", "src", "--name", "."])
    assert result.exit_code == 0
    pack_name = temp_repo.name
    assert f"Context Pack '{pack_name}' created!" in result.stdout

def test_pack_cmd_explicit_empty_name(temp_repo):
    """Covers pack.py line 31: --name '' is falsy, so pack_name = target_path.name."""
    runner.invoke(app, ["init"])
    result = runner.invoke(app, ["pack", "src", "--name", ""])
    assert result.exit_code == 0
    # Empty string is falsy, so pack_name = target_path.name = 'src'
    assert "Context Pack 'src' created!" in result.stdout

def test_pack_cmd_no_tiktoken(temp_repo, monkeypatch):
    runner.invoke(app, ["init"])
    import contextly.commands.pack as pack_mod
    monkeypatch.setattr(pack_mod, "tokenizer", None)
    result = runner.invoke(app, ["pack", "src"])
    assert result.exit_code == 0
    assert "Estimated Tokens" in result.stdout

def test_pack_cmd_binary_file(temp_repo):
    runner.invoke(app, ["init"])
    # Create a binary file
    (temp_repo / "src" / "test.bin").write_bytes(b'\x80\x81\x82')
    result = runner.invoke(app, ["pack", "src"])
    assert result.exit_code == 0

def test_pack_cmd_massive(temp_repo):
    runner.invoke(app, ["init"])
    # Create a massive file > 100k tokens
    # 'a' is 1 token. 100k tokens is 100k 'a's. We'll write 200k
    (temp_repo / "src" / "massive.txt").write_text("a " * 150000)
    result = runner.invoke(app, ["pack", "src"])
    assert result.exit_code == 0
    assert "This pack is massive" in result.stdout

def test_pack_cmd_read_permission_error(temp_repo, monkeypatch):
    runner.invoke(app, ["init"])
    import builtins
    original_open = builtins.open
    def mock_open(*args, **kwargs):
        if "index.js" in str(args[0]):
            raise PermissionError("Access denied")
        return original_open(*args, **kwargs)
        
    monkeypatch.setattr(builtins, "open", mock_open)
    result = runner.invoke(app, ["pack", "src"])
    assert result.exit_code == 0
    assert "Warning: Could not read" in result.stdout

def test_pack_cmd_is_file_permission_error(temp_repo, monkeypatch):
    """Covers pack.py lines 78-79: except PermissionError: continue inside the rglob loop.
    The file must be inside the pack target dir ('src') to be encountered during rglob."""
    runner.invoke(app, ["init"])
    # Create the file INSIDE src/ so rglob('*') over src/ finds it
    (temp_repo / "src" / "forbidden.txt").write_text("test")
    
    import pathlib
    original_is_file = pathlib.Path.is_file
    def mock_is_file(self):
        if self.name == "forbidden.txt":
            raise PermissionError("Access denied")
        return original_is_file(self)
    monkeypatch.setattr(pathlib.Path, "is_file", mock_is_file)
    
    result = runner.invoke(app, ["pack", "src"])
    assert result.exit_code == 0

def test_pack_cmd_rglob_permission_error(temp_repo, monkeypatch):
    runner.invoke(app, ["init"])
    # pack.py line 50: for path in target_path.rglob('*')
    # pack.py line 80: except PermissionError: prints warning
    # We mock Path.rglob to raise PermissionError immediately.
    import pathlib
    def mock_rglob(self, pattern):
        raise PermissionError("Access denied")
    monkeypatch.setattr(pathlib.Path, "rglob", mock_rglob)
    
    forbidden = temp_repo / "forbidden_dir"
    forbidden.mkdir()
    (forbidden / "test.txt").write_text("test")
    
    result = runner.invoke(app, ["pack", "forbidden_dir"])
    assert result.exit_code == 0
    assert "Permission error while traversing directories" in result.stdout

def test_analyze_cmd_scanner_error(temp_repo, monkeypatch):
    runner.invoke(app, ["init"])
    import contextly.scanners.language as lang_mod
    from contextly.scanners.base import ScannerError
    
    def mock_scan(*args, **kwargs):
        raise ScannerError("Language scan failed")
        
    monkeypatch.setattr(lang_mod.LanguageScanner, "scan", mock_scan)
    result = runner.invoke(app, ["analyze"])
    assert result.exit_code == 1
    assert "Scanner Error" in result.stdout

def test_analyze_cmd_contextly_error(temp_repo, monkeypatch):
    runner.invoke(app, ["init"])
    import contextly.utils.memory as mem_mod
    from contextly.utils.exceptions import ContextlyError
    
    def mock_load(*args, **kwargs):
        raise ContextlyError("Memory load failed")
        
    monkeypatch.setattr(mem_mod.MemoryEngine, "load_memory", mock_load)
    result = runner.invoke(app, ["analyze"])
    assert result.exit_code == 1
    assert "Context-Ly Error" in result.stdout

def test_analyze_cmd_unexpected_error(temp_repo, monkeypatch):
    runner.invoke(app, ["init"])
    import contextly.scanners.language as lang_mod
    
    def mock_scan(*args, **kwargs):
        raise ValueError("Something went completely wrong")
        
    monkeypatch.setattr(lang_mod.LanguageScanner, "scan", mock_scan)
    result = runner.invoke(app, ["analyze"])
    assert result.exit_code == 1
    assert "Unexpected Error:" in result.stdout

def test_analyze_cmd_claude(temp_repo):
    runner.invoke(app, ["init"])
    result = runner.invoke(app, ["analyze", "--model", "claude"])
    assert result.exit_code == 0
    assert "claude" in result.stdout.lower()

def test_analyze_cmd_permission_error(temp_repo, monkeypatch):
    runner.invoke(app, ["init"])
    
    import builtins
    original_open = builtins.open
    def mock_open(*args, **kwargs):
        if "PROJECT_CONTEXT.md" in str(args[0]) and "w" in args[1]:
            raise PermissionError("Access denied")
        return original_open(*args, **kwargs)
        
    monkeypatch.setattr(builtins, "open", mock_open)
    result = runner.invoke(app, ["analyze"])
    assert result.exit_code == 1
    assert "Failed to write PROJECT_CONTEXT.md" in result.stdout
