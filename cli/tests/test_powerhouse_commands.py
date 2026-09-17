import pytest
from conftest import runner, app
from pathlib import Path


def test_init_powerhouse_stack_detection(temp_repo):
    # Setup dummy project files
    (temp_repo / "package.json").write_text('{"name": "test-pkg", "dependencies": {"react": "^19.0.0"}}', encoding="utf-8")
    (temp_repo / "frontend").mkdir()
    (temp_repo / "frontend" / "App.tsx").write_text("export const App = () => null;", encoding="utf-8")

    result = runner.invoke(app, ["init", "--quick"])
    assert result.exit_code == 0
    assert "Contextly initialized successfully!" in result.stdout
    assert "TypeScript/JavaScript" in result.stdout
    assert "React" in result.stdout

    # Test --force
    result_force = runner.invoke(app, ["init", "--force"])
    assert result_force.exit_code == 0
    assert "Contextly initialized successfully!" in result_force.stdout


def test_analyze_powerhouse_modes(temp_repo):
    runner.invoke(app, ["init", "--quick"])

    # Test analyze --summary
    result_summary = runner.invoke(app, ["analyze", "--summary"])
    assert result_summary.exit_code == 0
    assert "Entry Points" in result_summary.stdout or "Architecture" in result_summary.stdout

    # Test analyze --stats
    result_stats = runner.invoke(app, ["analyze", "--stats"])
    assert result_stats.exit_code == 0
    assert "Health" in result_stats.stdout or "Score" in result_stats.stdout

    # Test analyze --inspect
    result_inspect = runner.invoke(app, ["analyze", "--inspect"])
    assert result_inspect.exit_code == 0
    assert "Inspection complete" in result_inspect.stdout


def test_pack_powerhouse_one_step_fusion(temp_repo, monkeypatch):
    runner.invoke(app, ["init", "--quick"])
    runner.invoke(app, ["analyze"])
    
    import pyperclip
    clipboard = []
    monkeypatch.setattr(pyperclip, "copy", lambda x: clipboard.append(x))

    # Test 1-step packaging with automatic fusion and clipboard copy
    result = runner.invoke(app, ["pack", "src", "--name", "frontend"])
    assert result.exit_code == 0
    assert "Context Pack 'frontend' created!" in result.stdout
    assert "Intelligence Fused" in result.stdout
    assert len(clipboard) == 1
    assert "context_pack name=\"frontend\"" in clipboard[0]

    # Test --standalone (skips fusion)
    clipboard.clear()
    result_standalone = runner.invoke(app, ["pack", "src", "--name", "standalone_pack", "--standalone"])
    assert result_standalone.exit_code == 0
    assert "Context Pack copied to clipboard!" in result_standalone.stdout
    assert "Architecture Map" not in clipboard[0]

    # Test --env flag
    result_env = runner.invoke(app, ["pack", "src", "--name", "env_pack", "--env"])
    assert result_env.exit_code == 0
    assert "export CONTEXTLY_PACK=" in result_env.stdout


def test_impact_powerhouse_visual_and_explain(temp_repo, monkeypatch):
    runner.invoke(app, ["init", "--quick"])
    runner.invoke(app, ["analyze"])

    # Test impact --visual
    result_visual = runner.invoke(app, ["impact", "src/index.js", "--visual"])
    assert result_visual.exit_code == 0
    assert "Blast Radius" in result_visual.stdout
    assert "Blast Radius Dependency Cascade" in result_visual.stdout

    # Test impact --explain <domain>
    class MockExplainer:
        def __init__(self, root_dir):
            pass
        def explain(self, domain):
            return f"Domain architecture for {domain}"

    monkeypatch.setattr("contextly.commands.impact.ExplainerEngine", MockExplainer)
    result_explain = runner.invoke(app, ["impact", "auth", "--explain", "--no-clipboard"])
    assert result_explain.exit_code == 0
    assert "Context payload saved to:" in result_explain.stdout


def test_memory_powerhouse_crud(temp_repo):
    runner.invoke(app, ["init", "--quick"])

    # 1. Learn custom rule
    res_learn = runner.invoke(app, ["memory", "--learn", "Always use strict TypeScript types", "--category", "Typing"])
    assert res_learn.exit_code == 0
    assert "Convention saved to memory vault" in res_learn.stdout

    # 1b. Duplicate rule
    res_dup = runner.invoke(app, ["memory", "--learn", "Always use strict TypeScript types", "--category", "Typing"])
    assert res_dup.exit_code == 0
    assert "already present" in res_dup.stdout

    # 2. Inspect memory
    res_view = runner.invoke(app, ["memory"])
    assert res_view.exit_code == 0
    assert "Stored Memory" in res_view.stdout
    assert "Always use strict TypeScript types" in res_view.stdout

    # 2b. Delete non-existent
    res_del_none = runner.invoke(app, ["memory", "--delete", "non_existent_id"])
    assert res_del_none.exit_code == 0
    assert "not found" in res_del_none.stdout

    # 2c. Delete existing rule
    from contextly.core.memory import MemoryEngine
    engine = MemoryEngine(temp_repo)
    rules = engine.load_memory().rules
    assert len(rules) > 0
    rule_id = rules[0].id
    res_del = runner.invoke(app, ["memory", "--delete", rule_id])
    assert res_del.exit_code == 0
    assert "deleted from memory vault" in res_del.stdout

    # 3. Clear memory
    res_clear = runner.invoke(app, ["memory", "--clear"])
    assert res_clear.exit_code == 0
    assert "Memory vault cleared" in res_clear.stdout

    res_empty = runner.invoke(app, ["memory"])
    assert "memory is currently empty" in res_empty.stdout

    # 4. Auto discover
    res_auto = runner.invoke(app, ["memory", "--auto", "--apply-all"])
    assert res_auto.exit_code == 0


def test_impact_visual_tree_full_cascade(temp_repo):
    from contextly.core.impact.engine import ImpactEngine
    from contextly.types.models import KnowledgeGraph, KnowledgeNode, NodeType
    
    graph = KnowledgeGraph()
    engine = ImpactEngine(graph)

    # Build 10 high files, 8 med files, 5 low files
    high_files = [KnowledgeNode(id=f"h{i}", type=NodeType.FILE, name=f"HighFile{i}", path=f"src/h{i}.ts") for i in range(10)]
    med_files = [KnowledgeNode(id=f"m{j}", type=NodeType.FILE, name=f"MedFile{j}", path=f"src/m{j}.ts") for j in range(8)]
    low_files = [KnowledgeNode(id=f"l{k}", type=NodeType.FILE, name=f"LowFile{k}", path=f"src/l{k}.ts") for k in range(5)]

    impact = {
        "HIGH": {"files": high_files, "entities": []},
        "MEDIUM": {"files": med_files, "entities": []},
        "LOW": {"files": low_files, "entities": []}
    }

    tree_output = engine.generate_visual_tree("src/core.ts", impact)
    assert "HIGH" in tree_output
    assert "MEDIUM" in tree_output
    assert "LOW" in tree_output
    assert "more HIGH risk files" in tree_output
    assert "more MEDIUM risk files" in tree_output
    assert "more LOW risk files" in tree_output


def test_impact_explain_error_handling(temp_repo, monkeypatch):
    runner.invoke(app, ["init", "--quick"])
    from contextly.utils.exceptions import ContextlyError

    class FaultyExplainer:
        def __init__(self, root_dir):
            pass
        def explain(self, domain):
            raise ContextlyError("Failed to explain domain")

    monkeypatch.setattr("contextly.commands.impact.ExplainerEngine", FaultyExplainer)
    result = runner.invoke(app, ["impact", "unknown_domain", "--explain"])
    assert result.exit_code == 1
    assert "Failed to explain domain" in result.stdout

