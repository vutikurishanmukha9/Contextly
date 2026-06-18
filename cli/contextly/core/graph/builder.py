import os
from pathlib import Path
from typing import List, Optional
import concurrent.futures

from ...types.models import KnowledgeGraph
from ...utils.walker import RepoWalker
from .assembler import GraphAssembler
from .parsers.base import ParsedFileDTO
from .parsers.registry import ParserRegistry
from ...utils.constants import is_skippable
from ...utils.console import console

import threading


def _parse_file(file_path: str, root_dir: str) -> Optional[ParsedFileDTO]:
    """
    Module-level function required for ProcessPoolExecutor serialization.
    Instantiates the correct parser based on file extension and processes the file.
    Uses thread-local storage to guarantee thread safety inside thread pools.
    """
    try:
        root_path = Path(root_dir)
        file_path_obj = Path(file_path)
        abs_path = root_path / file_path_obj
        try:
            with open(abs_path, "rb") as f:
                raw_bytes = f.read()
        except OSError:
            return None

        if b'\x00' in raw_bytes[:1024]:
            return None # Silently skip binaries

        try:
            content = raw_bytes.decode("utf-8")
        except UnicodeDecodeError:
            try:
                content = raw_bytes.decode("latin-1")
            except Exception as e:
                return ParsedFileDTO(file_path=file_path, exports=[], imports=[], error=f"DecodeError: {str(e)}")
            
        ext = file_path_obj.suffix.lower().lstrip(".")
        
        parser = ParserRegistry.get_parser(ext)
        if parser:
            return parser.parse(file_path, content, root_dir)
            
        return None
    except Exception as e:
        return ParsedFileDTO(file_path=file_path, exports=[], imports=[], error=f"ParseError: {str(e)}")

class ImportGraphBuilder:
    """
    Graph Builder orchestrator.
    Handles file discovery, thread/process pool management, and graph assembly delegation.
    """
    
    def __init__(self, root_dir: Path):
        self.root_dir = root_dir
        self.failed_files = {} # file_path -> error_message
        
        self._ALWAYS_SKIP = {
            ".git", "node_modules", "venv", ".venv", "__pycache__",
            ".contextly", "dist", "build", ".next", ".tox", ".eggs"
        }
        
        # Dynamically load supported extensions from the registry
        self._SUPPORTED_EXTENSIONS = set(ParserRegistry._registry.keys())

    def build(self, file_paths: Optional[List[str]] = None) -> KnowledgeGraph:
        """
        Builds the entire repository AST graph concurrently.
        """
        self.assembler = GraphAssembler()
        target_files = []

        if file_paths is not None:
            for p in file_paths:
                path_obj = Path(p)
                ext = path_obj.suffix.lower().lstrip(".")
                if ext in self._SUPPORTED_EXTENSIONS:
                    target_files.append(path_obj.as_posix())
        else:
            walker = RepoWalker(self.root_dir, max_depth=None, skip_predicate=is_skippable)

            # 1. Discover all parseable files
            for dirpath, _, filenames in walker.walk():
                dir_path_obj = Path(dirpath)
                for filename in filenames:
                    file_path_obj = dir_path_obj / filename
                    ext = file_path_obj.suffix.lower().lstrip(".")
                    if ext in self._SUPPORTED_EXTENSIONS:
                        full_rel = file_path_obj.relative_to(self.root_dir).as_posix()
                        target_files.append(full_rel)

        # 2. Concurrently parse files into DTOs
        # Using ProcessPoolExecutor to bypass Python's GIL bottlenecks for CPU-heavy AST parsing.
        # Limit to optimal workers to prevent overwhelming the disk/system.
        dtos: List[ParsedFileDTO] = []
        
        # Heuristic: For small repositories, sequential is faster.
        # Also provides fallback if multithreading fails.
        use_pool = len(target_files) > 100
        root_str = str(self.root_dir)
        
        if use_pool:
            try:
                # Leave 1 core free for OS, cap at 8 to prevent resource limit exhaustion
                optimal_workers = min(max(1, (os.cpu_count() or 4) - 1), 8)
                with concurrent.futures.ProcessPoolExecutor(max_workers=optimal_workers) as executor:
                    future_to_file = {
                        executor.submit(_parse_file, file_path, root_str): file_path 
                        for file_path in target_files
                    }
                    
                    for future in concurrent.futures.as_completed(future_to_file):
                        file_path = future_to_file[future]
                        try:
                            dto = future.result(timeout=30)
                            if dto:
                                if dto.error:
                                    console.print(f"[yellow]Warning:[/yellow] Failed to parse {dto.file_path}: {dto.error}")
                                    self.failed_files[dto.file_path] = dto.error
                                else:
                                    dtos.append(dto)
                            else:
                                self.failed_files[file_path] = "Empty parser output"
                        except Exception as e:
                            console.print(f"[yellow]Warning:[/yellow] Concurrency error parsing {file_path}: {str(e)}")
                            self.failed_files[file_path] = f"ConcurrencyError: {str(e)}"
            except Exception:
                # ProcessPoolExecutor fallback: ThreadPoolExecutor fallback
                try:
                    optimal_workers = min(max(1, (os.cpu_count() or 4) - 1), 8)
                    with concurrent.futures.ThreadPoolExecutor(max_workers=optimal_workers) as executor:
                        future_to_file = {
                            executor.submit(_parse_file, file_path, root_str): file_path 
                            for file_path in target_files
                        }
                        
                        for future in concurrent.futures.as_completed(future_to_file):
                            file_path = future_to_file[future]
                            try:
                                dto = future.result(timeout=30)
                                if dto:
                                    if dto.error:
                                        console.print(f"[yellow]Warning:[/yellow] Failed to parse {dto.file_path}: {dto.error}")
                                        self.failed_files[dto.file_path] = dto.error
                                    else:
                                        dtos.append(dto)
                                else:
                                    self.failed_files[file_path] = "Empty parser output"
                            except Exception as err:
                                console.print(f"[yellow]Warning:[/yellow] Concurrency error parsing {file_path}: {str(err)}")
                                self.failed_files[file_path] = f"ConcurrencyError: {str(err)}"
                except Exception:
                    # Fallback to sequential parsing
                    use_pool = False
                
        # Sequential Parsing Fallback
        if not use_pool:
            parsed_paths = {d.file_path for d in dtos}
            for file_path in target_files:
                if file_path in parsed_paths:
                    continue
                try:
                    dto = _parse_file(file_path, root_str)
                    if dto:
                        if dto.error:
                            console.print(f"[yellow]Warning:[/yellow] Failed to parse {dto.file_path}: {dto.error}")
                            self.failed_files[dto.file_path] = dto.error
                        else:
                            dtos.append(dto)
                    else:
                        self.failed_files[file_path] = "Empty parser output"
                except Exception as e:
                    self.failed_files[file_path] = f"SequentialError: {str(e)}"

        if self.failed_files:
            console.print(
                f"[yellow]Warning:[/yellow] AST parsing was partial. "
                f"Failed to parse {len(self.failed_files)} files out of {len(target_files)}. "
                f"The resulting graph will be incomplete."
            )

        # 3. Assemble the Graph deterministically
        # Sort DTOs by path to ensure stable IDs and predictable relationships.
        dtos.sort(key=lambda x: x.file_path)
        
        for dto in dtos:
            self.assembler.add_node(dto)
            
        self.assembler.build_relationships(dtos)
        
        return self.assembler.graph
