import os
from pathlib import Path
from typing import List, Optional
import concurrent.futures
import multiprocessing

from ...types.models import KnowledgeGraph
from ...utils.walker import RepoWalker
from .assembler import GraphAssembler
from .parsers.base import ParsedFileDTO

def _parse_file(file_path: str, root_dir: str) -> Optional[ParsedFileDTO]:
    """
    Module-level function required for ProcessPoolExecutor serialization.
    Instantiates the correct parser based on file extension and processes the file.
    """
    try:
        abs_path = os.path.join(root_dir, file_path)
        with open(abs_path, "r", encoding="utf-8") as f:
            content = f.read()
            
        ext = file_path.lower().split('.')[-1]
        
        if ext in ('py', 'pyw'):
            from .parsers.python import PythonASTParser
            parser = PythonASTParser()
            return parser.parse(file_path, content, root_dir)
            
        elif ext in ('js', 'jsx', 'ts', 'tsx'):
            from .parsers.typescript import TypeScriptASTParser
            parser = TypeScriptASTParser()
            return parser.parse(file_path, content, root_dir)
            
        return None
    except Exception:
        # Silently skip unreadable/broken files to maintain process pool resilience
        return None

class ImportGraphBuilder:
    """
    Enterprise-grade Graph Builder orchestrator.
    Handles file discovery, thread/process pool management, and graph assembly delegation.
    """
    
    def __init__(self, root_dir: Path):
        self.root_dir = root_dir
        self.assembler = GraphAssembler()
        
        self._ALWAYS_SKIP = {
            ".git", "node_modules", "venv", ".venv", "__pycache__",
            ".contextly", "dist", "build", ".next", ".tox", ".eggs"
        }
        
        self._SUPPORTED_EXTENSIONS = {
            "py", "ts", "tsx", "js", "jsx"
        }

    def build(self) -> KnowledgeGraph:
        """
        Builds the entire repository AST graph concurrently.
        """
        def skip_predicate(path: Path) -> bool:
            name = path.name.lower()
            return name in self._ALWAYS_SKIP or name.endswith(".egg-info")

        walker = RepoWalker(self.root_dir, max_depth=6, skip_predicate=skip_predicate)
        target_files = []

        # 1. Discover all parseable files
        for dirpath, _, filenames in walker.walk():
            rel_path = str(Path(dirpath).relative_to(self.root_dir))
            for filename in filenames:
                ext = filename.lower().split('.')[-1]
                if ext in self._SUPPORTED_EXTENSIONS:
                    full_rel = os.path.join(rel_path, filename).replace("\\", "/")
                    if full_rel.startswith("./"):
                        full_rel = full_rel[2:]
                    target_files.append(full_rel)

        # 2. Concurrently parse files into DTOs
        # Using ProcessPoolExecutor to bypass GIL for CPU-bound AST parsing
        # Limit to 4 workers to prevent starving user systems
        dtos: List[ParsedFileDTO] = []
        ctx = multiprocessing.get_context("spawn")
        with concurrent.futures.ProcessPoolExecutor(max_workers=4, mp_context=ctx) as executor:
            # Pass root_dir as string to bypass path pickling issues on some systems
            root_str = str(self.root_dir)
            futures = [
                executor.submit(_parse_file, file_path, root_str) 
                for file_path in target_files
            ]
            
            for future in concurrent.futures.as_completed(futures):
                try:
                    dto = future.result(timeout=10) # 10s per file max
                    if dto and not dto.error:
                        dtos.append(dto)
                except Exception:
                    continue

        # 3. Assemble the Graph deterministically
        # Sort DTOs by path to ensure deterministic node UUIDs (if we were seeding UUIDs)
        # and predictable relationships
        dtos.sort(key=lambda x: x.file_path)
        
        for dto in dtos:
            self.assembler.add_node(dto)
            
        self.assembler.build_relationships(dtos)
        
        return self.assembler.graph
