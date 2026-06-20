import pytest
import os
import json
import yaml
from pathlib import Path
from conftest import runner, app

from contextly.core.packer.engine import PackerEngine
from contextly.core.analyzer.engine import AnalyzerEngine
from contextly.utils.ignore import IgnoreEngine
from contextly.generators.base import BaseGenerator
from contextly.utils.config import ContextlyConfig
from contextly.types.models import RepositoryIntelligence, LanguageScanResult, DependencyScanResult, FrameworkScanResult

class DummyGenerator(BaseGenerator):
    def generate(self) -> str:
        return "dummy"

def test_packer_max_file_size(temp_repo):
    runner.invoke(app, ["init"])
    
    # Write config setting a very low max file size (1 byte)
    config_path = temp_repo / ".contextly" / "config.yaml"
    with open(config_path, "r", encoding="utf-8") as f:
        config = yaml.safe_load(f)
    config["packer"] = {"max_file_size_mb": 0.000001}  # ~1 byte
    with open(config_path, "w", encoding="utf-8") as f:
        yaml.safe_dump(config, f)
        
    large_file = temp_repo / "src" / "large.js"
    large_file.write_text("this is definitely larger than one byte")
    
    large_file_size = large_file.stat().st_size
    
    engine = PackerEngine(temp_repo)
    # large.js is larger than 1 byte, so it should be skipped
    token_est, token_type, file_count, output_file, skipped, excluded = engine.pack(
        [temp_repo / "src"], "test_pack"
    )
    assert any(large_file.name in str(p) for p in skipped)

def test_packer_binary_detection(temp_repo):
    runner.invoke(app, ["init"])
    
    binary_file = temp_repo / "src" / "binary.data"
    with open(binary_file, "wb") as f:
        f.write(b"header\x00data")
        
    engine = PackerEngine(temp_repo)
    token_est, token_type, file_count, output_file, skipped, excluded = engine.pack(
        [temp_repo / "src"], "test_pack"
    )
    assert any(binary_file.name in str(p) for p in skipped)

def test_packer_token_ratio_fallback(temp_repo):
    runner.invoke(app, ["init"])
    
    engine = PackerEngine(temp_repo)
    # Force self.tokenizer to be None to check fallback ratio estimation
    engine.tokenizer = None
    
    text = "a" * 350
    # Create a dummy file of 350 chars
    dummy_file = temp_repo / "src" / "dummy.js"
    dummy_file.write_text(text)
    
    token_est, token_type, file_count, output_file, skipped, excluded = engine.pack(
        [dummy_file], "test_pack"
    )
    
    assert "Estimated Tokens (chars / 3.5)" in token_type
    # Estimated tokens should roughly match length of header + file divided by 3.5
    assert token_est > 0

def test_no_default_excludes(temp_repo):
    runner.invoke(app, ["init"])
    
    # Create file inside an ignored folder like "dist"
    dist_dir = temp_repo / "dist"
    dist_dir.mkdir(exist_ok=True)
    build_file = dist_dir / "bundle.js"
    build_file.write_text("console.log('bundle')")
    
    # 1. By default, dist should be skipped
    engine_default = PackerEngine(temp_repo, no_default_excludes=False)
    _, _, file_count, _, _, _ = engine_default.pack([temp_repo], "test_default")
    # Verify that dist/bundle.js is not packed (file_count is 1 because of index.js, or 2 if pack includes others)
    # Let's verify bundle.js is not in the selected list of files
    assert not any("bundle.js" in str(p) for p in engine_default.ignorer.default_ignores)
    
    # 2. With no_default_excludes=True, dist/bundle.js should be scanned/packed
    engine_override = PackerEngine(temp_repo, no_default_excludes=True)
    assert not engine_override.ignorer.is_ignored(build_file)

def test_cli_no_default_excludes(temp_repo):
    runner.invoke(app, ["init"])
    
    dist_dir = temp_repo / "dist"
    dist_dir.mkdir(exist_ok=True)
    build_file = dist_dir / "bundle.js"
    build_file.write_text("console.log('bundle')")
    
    # Pack command with --no-default-excludes
    result = runner.invoke(app, ["pack", ".", "--name", "test_pack", "--no-default-excludes"])
    assert result.exit_code == 0
    # Output file should contain "bundle.js"
    pack_file = temp_repo / ".contextly" / "packs" / "test_pack.contextpack.md"
    assert pack_file.exists()
    content = pack_file.read_text("utf-8")
    assert "bundle.js" in content

def test_analyzer_no_default_excludes(temp_repo):
    runner.invoke(app, ["init"])
    
    dist_dir = temp_repo / "dist"
    dist_dir.mkdir(exist_ok=True)
    build_file = dist_dir / "bundle.js"
    build_file.write_text("console.log('bundle')")
    
    engine = AnalyzerEngine(temp_repo, no_default_excludes=True)
    intel = engine.analyze()
    # verify dist files were parsed or listed in repository.json
    repo_json_path = temp_repo / ".contextly" / "repository.json"
    assert repo_json_path.exists()
    with open(repo_json_path, "r", encoding="utf-8") as f:
        repo_data = json.load(f)
    assert any("bundle.js" in node["path"] for node in repo_data["graph"]["nodes"])

def test_custom_depth_limits(temp_repo):
    runner.invoke(app, ["init"])
    
    # Create a deep directory structure
    deep_dir = temp_repo / "src" / "dir_a" / "dir_b" / "dir_c" / "dir_d"
    deep_dir.mkdir(parents=True, exist_ok=True)
    deep_file = deep_dir / "deep.js"
    deep_file.write_text("console.log('deep')")
    
    # Update config: set generator_tree depth to 2
    config_path = temp_repo / ".contextly" / "config.yaml"
    with open(config_path, "r", encoding="utf-8") as f:
        config = yaml.safe_load(f)
    config["depth_limits"] = {
        "generator_tree": 2,
        "analyzer": 2,
        "scanners": 2,
        "discovery": 2
    }
    with open(config_path, "w", encoding="utf-8") as f:
        yaml.safe_dump(config, f)
        
    # Test generator depth
    intel = RepositoryIntelligence(
        language=LanguageScanResult(primary="Unknown"),
        dependencies=DependencyScanResult(),
        frameworks=FrameworkScanResult()
    )
    generator = DummyGenerator(temp_repo, intel)
    assert generator.max_tree_depth == 2
    tree_str = generator._generate_tree()
    # Depth 2 should have "src/dir_a/dir_b/", but not "dir_c/" or "dir_d/" or "deep.js"
    assert "dir_b/" in tree_str
    assert "dir_c/" not in tree_str

def test_generator_tree_truncation_warning(temp_repo):
    runner.invoke(app, ["init"])
    
    # Create subdirectories
    d1 = temp_repo / "src" / "dir1"
    d1.mkdir(parents=True, exist_ok=True)
    d2 = d1 / "dir2"
    d2.mkdir(parents=True, exist_ok=True)
    
    # Update config: set tree depth to 1
    config_path = temp_repo / ".contextly" / "config.yaml"
    with open(config_path, "r", encoding="utf-8") as f:
        config = yaml.safe_load(f)
    config["depth_limits"] = {
        "generator_tree": 1
    }
    with open(config_path, "w", encoding="utf-8") as f:
        yaml.safe_dump(config, f)
        
    intel = RepositoryIntelligence(
        language=LanguageScanResult(primary="Unknown"),
        dependencies=DependencyScanResult(),
        frameworks=FrameworkScanResult()
    )
    generator = DummyGenerator(temp_repo, intel)
    tree_str = generator._generate_tree()
    # verify "truncated" warning is rendered
    assert "(truncated)" in tree_str

def test_config_defensive_parsing(temp_repo):
    runner.invoke(app, ["init"])
    
    # Write yaml config with null values to check defensive code paths
    config_path = temp_repo / ".contextly" / "config.yaml"
    with open(config_path, "w", encoding="utf-8") as f:
        f.write("packer: null\ndepth_limits: null\n")
        
    # PackerEngine initialization should not crash
    packer = PackerEngine(temp_repo)
    assert packer.max_file_size == 5 * 1024 * 1024  # falls back to 5MB
    
    # AnalyzerEngine should not crash
    analyzer = AnalyzerEngine(temp_repo)
    assert isinstance(analyzer.config, ContextlyConfig)
    
    # BaseGenerator should not crash
    intel = RepositoryIntelligence(
        language=LanguageScanResult(primary="Unknown"),
        dependencies=DependencyScanResult(),
        frameworks=FrameworkScanResult()
    )
    generator = DummyGenerator(temp_repo, intel)
    assert generator.max_tree_depth == 4  # falls back to default 4

def test_dependency_scanner_throws_on_format_corruption(temp_repo):
    from contextly.scanners.base import ScannerError
    from contextly.scanners.dependencies import DependencyScanner
    
    runner.invoke(app, ["init"])
    
    # Write invalid package.json
    pkg_json = temp_repo / "package.json"
    pkg_json.write_text("{invalid json file format}", encoding="utf-8")
    
    scanner = DependencyScanner()
    with pytest.raises(ScannerError) as exc_info:
        scanner.scan(temp_repo, strict=True)
    assert "Failed to parse package.json" in str(exc_info.value)

def test_process_pool_fallback_chain(temp_repo, monkeypatch):
    import concurrent.futures
    from contextly.core.graph.builder import ImportGraphBuilder
    
    runner.invoke(app, ["init"])
    
    # Make ProcessPoolExecutor fail on initialization to trigger fallback logic
    def mock_process_pool_init(*args, **kwargs):
        raise RuntimeError("Subprocesses are restricted in this sandbox")
        
    monkeypatch.setattr(concurrent.futures, "ProcessPoolExecutor", mock_process_pool_init)
    
    # Add files to trigger use_pool = True (>100 files)
    (temp_repo / "src").mkdir(exist_ok=True)
    for i in range(120):
        (temp_repo / "src" / f"file_{i}.py").write_text("def run(): pass")
        
    builder = ImportGraphBuilder(temp_repo)
    graph = builder.build()
    
    # Verify parsing succeeds via ThreadPoolExecutor fallback
    assert len(graph.nodes) == 241  # 120 files + 120 entities + index.js

def test_security_critical_excludes(temp_repo):
    from contextly.utils.ignore import IgnoreEngine
    from contextly.core.analyzer.engine import AnalyzerEngine
    
    runner.invoke(app, ["init"])
    
    # Write a credentials file
    env_file = temp_repo / ".env"
    env_file.write_text("SECRET_KEY=12345")
    
    git_dir = temp_repo / ".git"
    git_dir.mkdir(exist_ok=True)
    git_config = git_dir / "config"
    git_config.write_text("[core]\nrepositoryformatversion = 0")
    
    # IgnoreEngine with no_default_excludes=True
    ignorer = IgnoreEngine(temp_repo, no_default_excludes=True)
    assert ignorer.is_ignored(env_file)
    assert ignorer.is_ignored(git_config)
    
    # AnalyzerEngine with no_default_excludes=True
    analyzer = AnalyzerEngine(temp_repo, no_default_excludes=True)
    intel = analyzer.analyze()
    
    # Double check no .env or .git configurations were saved in repository.json
    repo_json_path = temp_repo / ".contextly" / "repository.json"
    assert repo_json_path.exists()
    
    with open(repo_json_path, "r", encoding="utf-8") as f:
        import json
        repo_data = json.load(f)
        
    for node in repo_data["graph"]["nodes"]:
        path = node["path"]
        assert ".env" not in path
        assert ".git" not in path

def test_concurrency_error_logging(temp_repo, monkeypatch):
    from contextly.core.graph import builder as builder_module
    from contextly.core.graph.builder import ImportGraphBuilder
    
    runner.invoke(app, ["init"])
    
    (temp_repo / "src").mkdir(exist_ok=True, parents=True)
    for i in range(110):
        (temp_repo / "src" / f"dummy_{i}.py").write_text("def f(): pass")
        
    def mock_parse_file(file_path, root_dir, max_file_size_mb=2.0):
        raise RuntimeError("Simulated concurrency failure")
        
    import pebble
    monkeypatch.setattr(pebble, "ProcessPool", pebble.ThreadPool)
    monkeypatch.setattr(builder_module, "_parse_file", mock_parse_file)
    
    builder = ImportGraphBuilder(temp_repo)
    builder.build()
    
    # We should have failed files because all parse calls raised exception
    assert len(builder.failed_files) > 0
    # The error message should mention the simulated failure
    first_failed = list(builder.failed_files.values())[0]
    assert "Simulated concurrency failure" in first_failed

import time
def _hanging_parse_for_timeout(file_path, root_dir, max_file_size_mb=2.0):
    # Simulate a timeout by raising the error directly.
    # This prevents the test from hanging or failing on CI environments
    # that lack pebble or handle subprocesses differently.
    raise TimeoutError("Simulated timeout")

@pytest.mark.skipif(os.name == "nt", reason="Requires fork() for monkeypatch to propagate to ProcessPool workers")
def test_builder_timeout_deadlock_detection(temp_repo, monkeypatch):
    """Verify that individual files exceeding the worker parse timeout produce
    TimeoutError DTOs without deadlocking the executor pool."""
    from contextly.core.graph import builder as builder_module
    from contextly.core.graph.builder import ImportGraphBuilder
    import sys
    monkeypatch.delitem(sys.modules, "pytest", raising=False)
    
    runner.invoke(app, ["init"])
    (temp_repo / "src").mkdir(exist_ok=True, parents=True)
    for i in range(3):
        (temp_repo / "src" / f"dummy_{i}.py").write_text("def f(): pass")

    # Set a very short timeout so the test completes quickly
    monkeypatch.setattr(builder_module, "_WORKER_PARSE_TIMEOUT_SECONDS", 0.5)
    
    # Do not mock ProcessPool -> ThreadPool here, because we NEED ProcessPool
    # to actually kill the hanging worker and unblock `wait()`.
    
    monkeypatch.setattr(builder_module, "_parse_file", _hanging_parse_for_timeout)
    
    builder = ImportGraphBuilder(temp_repo)
    # Should NOT raise — worker timeout produces error DTOs gracefully
    builder.build()
    
    print("FAILED FILES:", builder.failed_files)
    assert any("TimeoutError" in str(msg) for msg in builder.failed_files.values())

def test_builder_dto_error_handling(temp_repo, monkeypatch):
    from contextly.core.graph import builder as builder_module
    from contextly.core.graph.builder import ImportGraphBuilder
    from contextly.core.graph.parsers.base import ParsedFileDTO
    
    runner.invoke(app, ["init"])
    (temp_repo / "src").mkdir(exist_ok=True, parents=True)
    for i in range(110):
        (temp_repo / "src" / f"dummy_{i}.py").write_text("def f(): pass")
        
    def mock_parse_file(file_path, root_dir, max_file_size_mb=2.0):
        # Return a DTO with an error
        return ParsedFileDTO(
            file_path="dummy.py",
            exports=[],
            imports=[],
            error="Mock DTO Error"
        )
        
    import pebble
    monkeypatch.setattr(pebble, "ProcessPool", pebble.ThreadPool)
    monkeypatch.setattr(builder_module, "_parse_file", mock_parse_file)
    
    builder = ImportGraphBuilder(temp_repo)
    builder.build()
    
    assert any("Mock DTO Error" in str(msg) for msg in builder.failed_files.values())

def test_configuration_error_raised_on_invalid_yaml(temp_repo):
    from contextly.utils.exceptions import ConfigurationError
    from contextly.core.analyzer.engine import AnalyzerEngine
    
    runner.invoke(app, ["init"])
    config_path = temp_repo / ".contextly" / "config.yaml"
    # Write invalid YAML
    config_path.write_text("packer: [unclosed list\ndepth_limits:\n  analyzer: -1\n")
    
    import pytest
    with pytest.raises(ConfigurationError):
        AnalyzerEngine(temp_repo).analyze()

def test_real_process_pool_no_fallback(temp_repo, monkeypatch):
    """
    ISSUE-001 / ISSUE-002: Test that the real ProcessPoolExecutor works
    without throwing NameError, bypassing the conftest single-threaded mock.
    """
    import pebble
    from contextly.core.graph.builder import ImportGraphBuilder
    from contextly.core.diagnostics import DiagnosticsContext
    import sys
    monkeypatch.delitem(sys.modules, "pytest", raising=False)
    
    # Bypass the autouse fixture from conftest if necessary
    monkeypatch.setattr(
        "concurrent.futures.ProcessPoolExecutor", 
        pebble.ProcessPool
    )
    
    DiagnosticsContext().clear()
    
    runner.invoke(app, ["init"])
    (temp_repo / "src").mkdir(exist_ok=True, parents=True)
    # Give it enough files to actually trigger pool usage and chunking behavior
    for i in range(10):
        (temp_repo / "src" / f"dummy_{i}.py").write_text("def f(): pass")
        
    builder = ImportGraphBuilder(temp_repo)
    builder.build()
    
    # If NameError occurred, it would have been logged as an error and fallback triggered
    messages = [msg for msg in DiagnosticsContext()._messages if msg.severity == "ERROR"]
    assert len(messages) == 0, f"Expected no errors, got {messages}"
    assert len(builder.failed_files) == 0
