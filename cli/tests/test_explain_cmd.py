import pytest
from typer.testing import CliRunner
from contextly.main import app

runner = CliRunner()

def test_explain_command_success(monkeypatch, tmp_path):
    # Mock ExplainerEngine
    class MockEngine:
        def __init__(self, root_dir):
            self.root_dir = root_dir
        def explain(self, domain):
            if domain == "missing":
                raise ValueError("Domain 'missing' not found.")
            return f"Payload for {domain}"
            
    monkeypatch.setattr("contextly.commands.explain.ExplainerEngine", MockEngine)
    
    # Mock pyperclip
    mock_clipboard = []
    def mock_copy(text):
        mock_clipboard.append(text)
    monkeypatch.setattr("contextly.commands.explain.pyperclip.copy", mock_copy)
    
    result = runner.invoke(app, ["explain", "auth", "--path", str(tmp_path)])
    assert result.exit_code == 0
    assert "Context payload saved to:" in result.stdout
    assert "Notice: Proprietary source architecture has also been copied" in result.stdout
    assert "Payload for auth" in mock_clipboard[0]
    
    # Test missing domain
    result = runner.invoke(app, ["explain", "missing", "--path", str(tmp_path)])
    assert result.exit_code == 1
    assert "Domain 'missing' not found" in result.stdout
    
    # Test FileNotFoundError
    class MockEngineMissing:
        def __init__(self, root_dir):
            pass
        def explain(self, domain):
            raise FileNotFoundError("repo.json missing")
            
    monkeypatch.setattr("contextly.commands.explain.ExplainerEngine", MockEngineMissing)
    result = runner.invoke(app, ["explain", "auth", "--path", str(tmp_path)])
    assert result.exit_code == 1
    assert "repo.json missing" in result.stdout
    
    # Test generic exception
    class MockEngineError:
        def __init__(self, root_dir):
            pass
        def explain(self, domain):
            raise Exception("generic error")
            
    monkeypatch.setattr("contextly.commands.explain.ExplainerEngine", MockEngineError)
    result = runner.invoke(app, ["explain", "auth", "--path", str(tmp_path)])
    assert result.exit_code == 1
    assert "generic error" in result.stdout
