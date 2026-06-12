import pytest
from pathlib import Path
from contextly.generators.base import BaseGenerator
from contextly.generators.chatgpt import ChatGPTGenerator
from contextly.generators.claude import ClaudeGenerator
from contextly.types.models import RepositoryIntelligence, ProjectMemory, MemoryRule, LanguageScanResult, DependencyScanResult, FrameworkScanResult

def get_dummy_intel():
    return RepositoryIntelligence(
        language=LanguageScanResult(primary="Unknown"),
        dependencies=DependencyScanResult(),
        frameworks=FrameworkScanResult()
    )

class DummyGenerator(BaseGenerator):
    def generate(self):
        return "dummy"

def test_base_generator_readme(tmp_path):
    """Covers base.py 18-23: Readme parsing success and truncation."""
    intel = get_dummy_intel()
    gen = DummyGenerator(tmp_path, intel)
    
    # Missing readme
    assert "No README.md found" in gen._get_readme_content()
    
    # Readme with > 1000 chars
    readme = tmp_path / "README.md"
    readme.write_text("A" * 1500)
    res = gen._get_readme_content()
    assert "[truncated]" in res
    assert len(res) < 1100

def test_base_generator_tree_depth_and_permission(tmp_path, monkeypatch):
    """Covers base.py 32 (depth>2), 34 (not dir), 38-39 (PermissionError in iterdir)."""
    intel = get_dummy_intel()
    gen = DummyGenerator(tmp_path, intel)
    
    # Create deep structure
    d1 = tmp_path / "dir1"
    d1.mkdir()
    d2 = d1 / "dir2"
    d2.mkdir()
    d3 = d2 / "dir3"
    d3.mkdir()
    
    # File to cover not dir
    f1 = tmp_path / "file1.txt"
    f1.write_text("f")
    
    # Permission error mock
    import pathlib
    original_iterdir = pathlib.Path.iterdir
    def mock_iterdir(self):
        if self.name == "dir2":
            raise PermissionError("Access denied")
        return original_iterdir(self)
    monkeypatch.setattr(pathlib.Path, "iterdir", mock_iterdir)
    
    tree = gen._generate_tree()
    assert "dir1" in tree
    assert "dir3" not in tree  # Because dir2 raises PermissionError

def test_base_generator_edge_cases(tmp_path, monkeypatch):
    """Covers base.py 22-23 (truncate), 32 (depth>2), 34 (not dir)"""
    intel = get_dummy_intel()
    gen = DummyGenerator(tmp_path, intel)

    # 22-23: truncate readme
    readme = tmp_path / "README.md"
    readme.write_text("A" * 1500)
    res = gen._get_readme_content()
    assert "[truncated" in res

    # 32: depth > 2
    d1 = tmp_path / "dir1"
    d1.mkdir()
    d2 = d1 / "dir2"
    d2.mkdir()
    d3 = d2 / "dir3"
    d3.mkdir()
    d4 = d3 / "dir4"
    d4.mkdir()
    
    # 34: not dir
    f1 = tmp_path / "file1.txt"
    f1.write_text("a")

    tree = gen._generate_tree()
    assert "dir1" in tree
    assert "dir4" not in tree

def test_chatgpt_generator_memory_rules(tmp_path):
    """Covers chatgpt.py 20-23: memory formatting."""
    mem = ProjectMemory(rules=[MemoryRule(id="1", category="Cat", rule="Rule1", confidence="High", source="user", created_at="2023")])
    intel = get_dummy_intel()
    intel.memory = mem
    gen = ChatGPTGenerator(tmp_path, intel)
    res = gen.generate()
    assert "Explicit Rules (Memory)" in res
    assert "[Cat] Rule1 [High confidence]" in res

def test_claude_generator_memory_rules(tmp_path):
    """Covers claude.py 21-26: memory formatting."""
    mem = ProjectMemory(rules=[MemoryRule(id="1", category="Cat", rule="Rule1", confidence="High", source="user", created_at="2023")])
    intel = get_dummy_intel()
    intel.memory = mem
    gen = ClaudeGenerator(tmp_path, intel)
    res = gen.generate()
    assert "<explicit_rules source=\"memory\">" in res
    assert "<rule category=\"Cat\"><![CDATA[Rule1]]></rule>" in res

def test_base_generator_exceptions(tmp_path, monkeypatch):
    """Covers base.py 22-23 (README exceptions), 34 (not is_dir inside walk)."""
    intel = get_dummy_intel()
    gen = ClaudeGenerator(tmp_path, intel)
    
    import builtins
    original_open = builtins.open
    def mock_open(*args, **kwargs):
        if "README.md" in str(args[0]):
            raise PermissionError("Denied")
        return original_open(*args, **kwargs)
    monkeypatch.setattr(builtins, "open", mock_open)
    (tmp_path / "README.md").write_text("a")
    assert "No README.md found." in gen._get_readme_content()
    monkeypatch.undo()
    
    # max length
    (tmp_path / "README.md").write_text("a" * 1050)
    assert "[truncated]" in gen._get_readme_content()
    
    # not is_dir inside walk
    import pathlib
    original_is_dir = pathlib.Path.is_dir
    def mock_is_dir(self):
        if "subdir" in self.name:
            return False
        return original_is_dir(self)
    monkeypatch.setattr(pathlib.Path, "is_dir", mock_is_dir)
    (tmp_path / "subdir").mkdir()
    gen._generate_tree()
    monkeypatch.undo()
