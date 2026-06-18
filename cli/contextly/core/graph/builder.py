import os
from pathlib import Path
from typing import List, Optional
import concurrent.futures

from ...types.models import KnowledgeGraph
from ...utils.walker import RepoWalker
from .assembler import GraphAssembler
from .parsers.base import ParsedFileDTO
from .parsers.python import PythonASTParser
from .parsers.typescript import TypeScriptASTParser
from ...utils.constants import is_skippable

import threading

_thread_local = threading.local()

def _get_parsers():
    if not hasattr(_thread_local, 'parsers'):
        _thread_local.parsers = {}
    return _thread_local.parsers

def _parse_file(file_path: str, root_dir: str) -> Optional[ParsedFileDTO]:
    """
    Module-level function required for ProcessPoolExecutor serialization.
    Instantiates the correct parser based on file extension and processes the file.
    Uses thread-local storage to guarantee thread safety inside thread pools.
    """
    try:
        abs_path = os.path.join(root_dir, file_path)
        try:
            with open(abs_path, "r", encoding="utf-8") as f:
                content = f.read()
        except UnicodeDecodeError:
            with open(abs_path, "r", encoding="latin-1", errors="ignore") as f:
                content = f.read()
            if '\x00' in content:
                return None # Silently skip binaries
            
        ext = file_path.lower().split('.')[-1]
        parsers = _get_parsers()
        
        if ext in ('py', 'pyw'):
            if 'py' not in parsers:
                parsers['py'] = PythonASTParser()
            return parsers['py'].parse(file_path, content, root_dir)
            
        elif ext in ('js', 'jsx', 'ts', 'tsx'):
            if 'ts' not in parsers:
                parsers['ts'] = TypeScriptASTParser()
            return parsers['ts'].parse(file_path, content, root_dir)
            
        return None
    except Exception:
        # Silently skip unreadable/broken files to maintain process pool resilience
        return None

class ImportGraphBuilder:
    """
    Graph Builder orchestrator.
    Handles file discovery, thread/process pool management, and graph assembly delegation.
    """
    
    def __init__(self, root_dir: Path):
        self.root_dir = root_dir
        
        self._ALWAYS_SKIP = {
            ".git", "node_modules", "venv", ".venv", "__pycache__",
            ".contextly", "dist", "build", ".next", ".tox", ".eggs"
        }
        
        self._SUPPORTED_EXTENSIONS = {
            "py", "ts", "tsx", "js", "jsx"
        }

    def build(self, file_paths: Optional[List[str]] = None) -> KnowledgeGraph:
        """
        Builds the entire repository AST graph concurrently.
        """
        self.assembler = GraphAssembler()
        target_files = []

        if file_paths is not None:
            for p in file_paths:
                ext = p.lower().split('.')[-1]
                if ext in self._SUPPORTED_EXTENSIONS:
                    target_files.append(p)
        else:
            walker = RepoWalker(self.root_dir, max_depth=None, skip_predicate=is_skippable)

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
        # Using ThreadPoolExecutor since tree-sitter C bindings release the GIL
        # Limit to 8 workers to prevent overwhelming the disk/system
        dtos: List[ParsedFileDTO] = []
        
        # Heuristic: For small repositories, sequential is faster.
        # Also provides fallback if multithreading fails.
        use_pool = len(target_files) > 100
        root_str = str(self.root_dir)
        
        if use_pool:
            try:
                # Leave 1 core free for OS, cap at 8 to prevent OOM on massive repos
                optimal_workers = min(max(1, (os.cpu_count() or 4) - 1), 8)
                with concurrent.futures.ThreadPoolExecutor(max_workers=optimal_workers) as executor:
                    # Process in chunks to prevent unbounded memory allocation for futures (C-3)
                    chunk_size = optimal_workers * 4
                    for i in range(0, len(target_files), chunk_size):
                        chunk = target_files[i:i + chunk_size]
                        futures = [
                            executor.submit(_parse_file, file_path, root_str) 
                            for file_path in chunk
                        ]
                        
                        for future in concurrent.futures.as_completed(futures):
                            try:
                                dto = future.result(timeout=10) # 10s per file max
                                if dto and not dto.error:
                                    dtos.append(dto)
                            except Exception:
                                continue
            except Exception:
                # If pool creation fails (e.g. strict sandboxing, no /dev/shm, etc.), fallback to sequential
                use_pool = False
                
        # Pool failure is already handled in the except block which sets use_pool = False
        if not use_pool:
            parsed_paths = {d.file_path for d in dtos}
            for file_path in target_files:
                if file_path in parsed_paths:
                    continue
                try:
                    dto = _parse_file(file_path, root_str)
                    if dto and not dto.error:
                        dtos.append(dto)
                except Exception:
                    continue

        # 3. Assemble the Graph deterministically
        # Sort DTOs by path to ensure stable IDs and predictable relationships.
        dtos.sort(key=lambda x: x.file_path)
        
        for dto in dtos:
            self.assembler.add_node(dto)
            
        self.assembler.build_relationships(dtos)
        
        return self.assembler.graph
