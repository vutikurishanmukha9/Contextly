import pathlib
from conftest import runner, app


def test_pack_cmd(temp_repo):
    runner.invoke(app, ["init"])
    result = runner.invoke(app, ["pack", "src", "--name", "frontend"])
    assert result.exit_code == 0
    assert "Context Pack 'frontend' created!" in result.stdout

    pack_path = temp_repo / ".contextly" / "packs" / "frontend.contextpack.md"
    assert pack_path.exists()
    content = pack_path.read_text(encoding="utf-8")
    assert "## File: `src/index.js`" in content


def test_pack_cmd_uninitialized(temp_repo):
    result = runner.invoke(app, ["pack", "src"])
    assert result.exit_code == 1
    assert "Context-Ly is not initialized" in result.stdout


def test_pack_cmd_validation(temp_repo):
    runner.invoke(app, ["init"])
    result = runner.invoke(app, ["pack", "non_existent_dir"])
    assert result.exit_code == 1
    assert "Target directory does not exist" in result.stdout


def test_pack_cmd_empty_name(temp_repo):
    runner.invoke(app, ["init"])
    result = runner.invoke(app, ["pack", "."])
    assert result.exit_code == 0
    pack_name = temp_repo.name
    assert f"Context Pack '{pack_name}' created!" in result.stdout


def test_pack_cmd_explicit_dot_name(temp_repo):
    """Covers pack.py line 32: the pack_name == '.' branch."""
    runner.invoke(app, ["init"])
    result = runner.invoke(app, ["pack", "src", "--name", "."])
    assert result.exit_code == 0
    pack_name = temp_repo.name
    assert f"Context Pack '{pack_name}' created!" in result.stdout


def test_pack_cmd_explicit_empty_name(temp_repo):
    """Covers pack.py line 31: --name '' is falsy, so pack_name = target_path.name."""
    runner.invoke(app, ["init"])
    result = runner.invoke(app, ["pack", "src", "--name", ""])
    assert result.exit_code == 0
    assert "Context Pack 'src' created!" in result.stdout


def test_pack_cmd_no_tiktoken(temp_repo, monkeypatch):
    runner.invoke(app, ["init"])
    
    import contextly.core.packer.engine as pack_engine_mod
    
    # We patch the engine after it's initialized by the command
    original_init = pack_engine_mod.PackerEngine.__init__
    
    def mock_init(self, root_dir):
        original_init(self, root_dir)
        self.tokenizer = None
        
    monkeypatch.setattr(pack_engine_mod.PackerEngine, "__init__", mock_init)
    
    result = runner.invoke(app, ["pack", "src"])
    assert result.exit_code == 0
    assert "Estimated Tokens" in result.stdout


def test_pack_cmd_binary_file(temp_repo):
    runner.invoke(app, ["init"])
    (temp_repo / "src" / "test.bin").write_bytes(b'\x80\x81\x82')
    result = runner.invoke(app, ["pack", "src"])
    assert result.exit_code == 0


def test_pack_cmd_massive(temp_repo):
    runner.invoke(app, ["init"])
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
    """Covers pack.py lines 78-79: except PermissionError: continue inside the rglob loop."""
    runner.invoke(app, ["init"])
    (temp_repo / "src" / "forbidden.txt").write_text("test")

    original_is_file = pathlib.Path.is_file
    def mock_is_file(self):
        if self.name == "forbidden.txt":
            raise PermissionError("Access denied")
        return original_is_file(self)
    monkeypatch.setattr(pathlib.Path, "is_file", mock_is_file)

    result = runner.invoke(app, ["pack", "src"])
    assert result.exit_code == 0


def test_pack_cmd_rglob_permission_error(temp_repo, monkeypatch):
    """Covers pack.py line 80: except PermissionError on directory traversal."""
    runner.invoke(app, ["init"])

    def mock_rglob(self, pattern):
        raise PermissionError("Access denied")
    monkeypatch.setattr(pathlib.Path, "rglob", mock_rglob)

    forbidden = temp_repo / "forbidden_dir"
    forbidden.mkdir()
    (forbidden / "test.txt").write_text("test")

    result = runner.invoke(app, ["pack", "forbidden_dir"])
    assert result.exit_code == 0
    assert "[OK] Context Pack 'forbidden_dir' created!" in result.stdout


def test_pack_cmd_root_permission_error(temp_repo, monkeypatch):
    """Covers the pre-validation iterdir PermissionError guard in pack.py."""
    runner.invoke(app, ["init"])

    import pathlib
    original_iterdir = pathlib.Path.iterdir
    def mock_iterdir(self):
        if self.name == "forbidden_dir":
            raise PermissionError("Access denied")
        return original_iterdir(self)
    monkeypatch.setattr(pathlib.Path, "iterdir", mock_iterdir)

    forbidden = temp_repo / "forbidden_dir"
    forbidden.mkdir()

    result = runner.invoke(app, ["pack", "forbidden_dir"])
    assert result.exit_code == 1
    assert "Cannot access target directory" in result.stdout


def test_pack_cmd_outside_root(temp_repo):
    runner.invoke(app, ["init"])
    outside_dir = temp_repo.parent
    result = runner.invoke(app, ["pack", str(outside_dir)])
    assert result.exit_code == 1
    assert "Target directory must be inside the project root directory" in result.stdout

def test_pack_cmd_max_tokens(temp_repo):
    runner.invoke(app, ["init"])
    
    # Create some files
    (temp_repo / "src" / "main.py").write_text("print('hello')\n" * 50)
    (temp_repo / "src" / "utils.py").write_text("print('utils')\n" * 50)
    
    result = runner.invoke(app, ["pack", "src", "--max-tokens", "100"]) # Very low limit
    assert result.exit_code == 0
    assert "Files Excluded (Token Limit)" in result.stdout
    assert "files were automatically excluded" in result.stdout

def test_pack_cmd_profile(temp_repo):
    # Test valid profile
    runner.invoke(app, ["init"])
    
    # Write a custom profile into config
    import yaml
    config_file = temp_repo / ".contextly" / "config.yaml"
    data = yaml.safe_load(config_file.read_text())
    data["profiles"] = {"custom": ["src", "tests"]}
    config_file.write_text(yaml.dump(data))
    
    (temp_repo / "tests").mkdir()
    (temp_repo / "tests" / "test_main.py").write_text("test")
    
    result = runner.invoke(app, ["pack", "--profile", "custom"])
    assert result.exit_code == 0
    assert "profile 'custom'" in result.stdout
    
    # Test missing profile
    result = runner.invoke(app, ["pack", "--profile", "missing"])
    assert result.exit_code == 1
    assert "Profile 'missing' not found" in result.stdout

