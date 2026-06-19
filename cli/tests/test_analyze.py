from conftest import runner, app


def test_analyze_cmd_claude(temp_repo):
    runner.invoke(app, ["init"])
    result = runner.invoke(app, ["analyze", "--model", "claude"])
    assert result.exit_code == 0
    assert "Repository scan complete" in result.stdout

    ctx_path = temp_repo / "PROJECT_CONTEXT.md"
    assert ctx_path.exists()

    content = ctx_path.read_text(encoding="utf-8")
    assert "<project_context>" in content

    # Verify XML is well-formed
    import xml.etree.ElementTree as ET
    # Extract just the XML part
    start_idx = content.find("<project_context>")
    end_idx = content.find("</project_context>") + len("</project_context>")
    xml_content = content[start_idx:end_idx]
    # This will raise ParseError if not well-formed
    ET.fromstring(xml_content)


def test_analyze_cmd_chatgpt(temp_repo):
    runner.invoke(app, ["init"])
    result = runner.invoke(app, ["analyze", "--model", "chatgpt"])
    assert result.exit_code == 0

    ctx_path = temp_repo / "PROJECT_CONTEXT.md"
    assert ctx_path.exists()

    content = ctx_path.read_text(encoding="utf-8")
    assert "## Stack Identity" in content

    # Verify JSON is valid
    import json
    import re
    # Extract the JSON block
    match = re.search(r"```json\n(.*?)\n```", content, re.DOTALL)
    assert match is not None
    json_str = match.group(1)
    # This will raise JSONDecodeError if not valid
    parsed = json.loads(json_str)
    assert "primary_language" in parsed


def test_analyze_cmd_python_deps(temp_python_repo):
    """Covers analyze.py line 80: table.add_row('Python Dependencies', ...) when py_count > 0."""
    runner.invoke(app, ["init"])
    result = runner.invoke(app, ["analyze"])
    assert result.exit_code == 0
    assert "Python Dependencies" in result.stdout


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
    import contextly.core.memory as mem_mod
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


def test_analyze_cmd_permission_error(temp_repo, monkeypatch):
    runner.invoke(app, ["init"])

    import os
    original_access = os.access
    def mock_access(path, mode):
        if mode == os.W_OK:
            # Pre-flight check simulates a failure
            return False
        return original_access(path, mode)

    monkeypatch.setattr(os, "access", mock_access)
    result = runner.invoke(app, ["analyze"])
    assert result.exit_code == 1
    assert "Failed to write PROJECT_CONTEXT.md" in result.stdout

def test_analyze_cmd_memory_error(temp_repo, monkeypatch):
    runner.invoke(app, ["init"])
    import contextly.core.analyzer.engine as engine_mod
    from contextly.utils.exceptions import ContextlyError

    def mock_init(self, *args, **kwargs):
        raise ContextlyError("Memory vault failed to initialize")

    monkeypatch.setattr(engine_mod.MemoryEngine, "__init__", mock_init)
    result = runner.invoke(app, ["analyze"])
    assert result.exit_code == 1
    assert "Context-Ly Error:" in result.stdout
