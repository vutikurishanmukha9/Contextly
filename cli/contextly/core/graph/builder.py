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

_WORKER_PARSE_TIMEOUT_SECONDS = 120

def _parse_file(file_path: str, root_dir: str, max_file_size_mb: float = 2.0) -> Optional[ParsedFileDTO]:
    """
    Module-level function required for ProcessPoolExecutor serialization.
    Instantiates the correct parser based on file extension and processes the file.
    Uses thread-local storage to guarantee thread safety inside thread pools.
    """
    try:
        root_path = Path(root_dir)
        file_path_obj = Path(file_path)
        abs_path = root_path / file_path_obj

        # Guard: enforce a hard ceiling to prevent OOM on generated bundles
        _AST_PARSE_MAX_BYTES = int(max_file_size_mb * 1024 * 1024)

        try:
            with open(abs_path, "rb") as f:
                file_size = os.fstat(f.fileno()).st_size
                if file_size > _AST_PARSE_MAX_BYTES:
                    return ParsedFileDTO(file_path=file_path, exports=[], imports=[], error=f"Skipped: file size {file_size} exceeds {_AST_PARSE_MAX_BYTES} byte AST parse limit")
                raw_bytes = f.read()
        except OSError:
            return None

        if b'\x00' in raw_bytes[:1024]:
            return None # Silently skip binaries

        try:
            content = raw_bytes.decode("utf-8")
        except UnicodeDecodeError:
            try:
                from charset_normalizer import from_bytes
                detection = from_bytes(raw_bytes).best()
                if detection is None or detection.encoding is None:
                    return ParsedFileDTO(file_path=file_path, exports=[], imports=[], error="Skipped: undetectable encoding (likely binary)")
                # charset-normalizer provides a coherence score (0.0-1.0); reject low-confidence detections
                _MIN_ENCODING_COHERENCE = 0.5
                if detection.coherence < _MIN_ENCODING_COHERENCE:
                    return ParsedFileDTO(file_path=file_path, exports=[], imports=[], error=f"Skipped: low encoding confidence ({detection.encoding}, coherence={detection.coherence:.2f})")
                content = str(detection)
            except ImportError:
                # charset-normalizer is required for non-UTF-8 files; skip to prevent data corruption from lossy decoding
                return ParsedFileDTO(file_path=file_path, exports=[], imports=[],
                    error="Skipped: non-UTF-8 encoding and charset-normalizer not installed")
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
    
    def __init__(self, root_dir: Path, max_file_size_mb: float = 2.0):
        self.root_dir = root_dir
        self.failed_files = {} # file_path -> error_message
        self.max_file_size_mb = max_file_size_mb
        

        # Dynamically load supported extensions from the registry
        self._SUPPORTED_EXTENSIONS = ParserRegistry.supported_extensions()

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
        
        # We process target_files in chunks to avoid OOM in large repos
        from itertools import islice
        def chunk_iterable(iterable, size):
            it = iter(iterable)
            while True:
                c = list(islice(it, size))
                if not c:
                    break
                yield c

        use_pool = True
        root_str = str(self.root_dir)
        
        # Initialize assembler once for the whole build
        
        def _process_chunk(chunk_files, is_process_pool, pool_name, on_init=None):
            """
            Processes a chunk of files through pebble.ProcessPool or concurrent.futures.ThreadPoolExecutor.
            """
            dtos = []
            optimal_workers = min(max(1, (os.cpu_count() or 4) - 1), 8)
            batch_size = optimal_workers * 32
            
            kwargs = {"max_workers": optimal_workers}
            
            if is_process_pool:
                try:
                    import sys
                    if sys.modules.get("pytest") is not None:
                        # Avoid multiprocessing/pebble inside pytest on Windows to prevent deadlocks
                        pool_class = concurrent.futures.ThreadPoolExecutor
                    else:
                        from pebble import ProcessPool
                        from concurrent.futures import TimeoutError as FuturesTimeoutError
                        pool_class = ProcessPool
                        kwargs["max_tasks"] = 10
                        import multiprocessing
                        kwargs["context"] = multiprocessing.get_context("spawn")
                except ImportError:
                    pool_class = concurrent.futures.ProcessPoolExecutor
            else:
                pool_class = concurrent.futures.ThreadPoolExecutor
                from concurrent.futures import TimeoutError as FuturesTimeoutError
                    
            with pool_class(**kwargs) as executor:
                if on_init:
                    on_init()
                in_flight = set()
                target_iter = iter(chunk_files)
                future_to_file = {}
                
                def submit_next():
                    try:
                        fp = next(target_iter)
                        if is_process_pool and pool_class.__name__ == "ProcessPool":
                            future = executor.schedule(_parse_file, args=(fp, root_str, self.max_file_size_mb), timeout=_WORKER_PARSE_TIMEOUT_SECONDS)
                        else:
                            future = executor.submit(_parse_file, fp, root_str, self.max_file_size_mb)
                        in_flight.add(future)
                        future_to_file[future] = fp
                        return True
                    except StopIteration:
                        return False
                        
                for _ in range(batch_size):
                    submit_next()
                    
                while in_flight:
                    done, _ = concurrent.futures.wait(
                        in_flight,
                        timeout=5,
                        return_when=concurrent.futures.FIRST_COMPLETED
                    )
                    
                    if not done:
                        continue

                    for future in done:
                        in_flight.discard(future)
                        file_path = future_to_file.pop(future, "unknown")
                        try:
                            dto = future.result()
                            if dto:
                                if dto.error:
                                    diagnostics.add_warning("ImportGraphBuilder", f"Failed to parse {dto.file_path}: {dto.error}")
                                    self.failed_files[dto.file_path] = dto.error
                                else:
                                    dtos.append(dto)
                        except Exception as e:
                            # Catch TimeoutError (either pebble.ProcessExpired, concurrent.futures.TimeoutError, etc.)
                            if type(e).__name__ in ('TimeoutError', 'ProcessExpired'):
                                self.failed_files[file_path] = f"TimeoutError: AST parsing exceeded deadline"
                                diagnostics.add_warning("ImportGraphBuilder", f"Timeout parsing {file_path}")
                            else:
                                self.failed_files[file_path] = f"ConcurrencyError: {str(e)}"
                            
                        submit_next()
            return dtos

        from ..diagnostics import DiagnosticsContext
        diagnostics = DiagnosticsContext()
        
        all_dtos_for_relationships = []
        
        # Process in chunks of 500 files at a time
        for chunk in chunk_iterable(target_files, 500):
            chunk_dtos = []
            if use_pool:
                pool_initialized = False
                def set_initialized():
                    nonlocal pool_initialized
                    pool_initialized = True
                    
                try:
                    chunk_dtos = _process_chunk(chunk, True, "ProcessPool", set_initialized)
                except Exception as e:
                    if pool_initialized:
                        diagnostics.add_error("ImportGraphBuilder", f"ProcessPool execution error (no retry): {str(e)}")
                        use_pool = False
                    else:
                        try:
                            chunk_dtos = _process_chunk(chunk, False, "ThreadPool", set_initialized)
                        except Exception as thread_err:
                            diagnostics.add_error("ImportGraphBuilder", f"ThreadPool fallback error: {str(thread_err)}")
                            use_pool = False
            
            # Sequential fallback for this chunk if pool failed
            if not use_pool:
                for file_path in chunk:
                    try:
                        dto = _parse_file(file_path, root_str, self.max_file_size_mb)
                        if dto:
                            if dto.error:
                                console.print(f"[yellow]Warning:[/yellow] Failed to parse {dto.file_path}: {dto.error}")
                                self.failed_files[dto.file_path] = dto.error
                            else:
                                chunk_dtos.append(dto)
                        else:
                            self.failed_files[file_path] = "Empty parser output"
                    except Exception as e:
                        self.failed_files[file_path] = f"SequentialError: {str(e)}"
                        
            # Immediately add nodes to assembler to free up memory from the full DTO tree
            for dto in chunk_dtos:
                self.assembler.add_node(dto)
                # Keep lightweight DTO structure for building relationships later
                all_dtos_for_relationships.append(dto)

        if self.failed_files:
            console.print(
                f"[yellow]Warning:[/yellow] AST parsing was partial. "
                f"Failed to parse {len(self.failed_files)} files out of {len(target_files)}. "
                f"The resulting graph will be incomplete."
            )

        # 3. Assemble the Graph deterministically
        # Sort DTOs by path to ensure stable IDs and predictable relationships.
        all_dtos_for_relationships.sort(key=lambda x: x.file_path)
        
        self.assembler.build_relationships(all_dtos_for_relationships)
        
        # Pass 3: Validate the Graph
        from .validator import GraphValidator
        validator = GraphValidator()
        self.assembler.graph = validator.validate(self.assembler.graph)
        
        return self.assembler.graph
