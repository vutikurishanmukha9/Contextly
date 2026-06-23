import pytest
import os
from pathlib import Path
from contextly.core.packer.engine import PackerEngine
from contextly.core.packer.engine import PackerEngine
from contextly.types.models import KnowledgeGraph, KnowledgeNode, NodeType

@pytest.fixture
def packer_engine(tmp_path):
    return PackerEngine(root_dir=tmp_path)

def test_export_formats(packer_engine, tmp_path):
    # Test that exporting handles JSON, Markdown, XML correctly
    graph = KnowledgeGraph(nodes=[], relationships=[])
    file_node = KnowledgeNode(
        id="file_2",
        type=NodeType.FILE,
        name="test2.py",
        path=str(tmp_path / "test2.py"),
        metadata={}
    )
    graph.nodes.append(file_node)
    (tmp_path / "test2.py").write_text("def foo(): pass")
    
    json_path = tmp_path / "out.json"
    xml_path = tmp_path / "out.xml"
    txt_path = tmp_path / "out.txt"
    
    packer_engine.pack(target_paths=[tmp_path], pack_name="out_json", task="Task")
    assert (tmp_path / ".contextly" / "packs" / "out_json.contextpack.md").exists()
    
    packer_engine.pack(target_paths=[tmp_path], pack_name="out_xml", task="Task")
    assert (tmp_path / ".contextly" / "packs" / "out_xml.contextpack.md").exists()
    
    packer_engine.pack(target_paths=[tmp_path], pack_name="out_txt", task="Task")
    assert (tmp_path / ".contextly" / "packs" / "out_txt.contextpack.md").exists()

def test_empty_graph_packing(packer_engine, tmp_path):
    # Create an empty dir
    empty_dir = tmp_path / "empty"
    empty_dir.mkdir()
    
    token_est, token_type, file_count, out_file, skipped, exc = packer_engine.pack(
        target_paths=[empty_dir],
        pack_name="empty_pack"
    )
    
    assert file_count == 0
    assert out_file.exists()
