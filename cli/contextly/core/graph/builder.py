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
            is_valid_utf16 = False
            first_kb = raw_bytes[:1024]
            import codecs
            has_bom = first_kb.startswith(codecs.BOM_UTF16_LE) or first_kb.startswith(codecs.BOM_UTF16_BE)
            even_kb = first_kb if len(first_kb) % 2 == 0 else first_kb[:-1]
            for encoding in ('utf-16', 'utf-16-le', 'utf-16-be'):
                try:
                    text = even_kb.decode(encoding, errors='strict')
                    if text:
                        if has_bom:
                            is_valid_utf16 = True
                            break
                        ascii_chars = sum(1 for c in text if ord(c) < 128 and (c.isprintable() or c.isspace()))
                        if (ascii_chars / len(text)) > 0.3:
                            is_valid_utf16 = True
                            break
                except Exception:
                    continue
                    
            if not is_valid_utf16:
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
        
        # We process target_files dynamically to avoid OOM in large repos and prevent worker stalls
        use_pool = True
        root_str = str(self.root_dir)
        
        import tempfile
        import json
        import os
        from ..diagnostics import DiagnosticsContext
        diagnostics = DiagnosticsContext()
        
        optimal_workers = min(max(1, (os.cpu_count() or 4) - 1), 8)
        if os.environ.get("CI"):
            optimal_workers = min(optimal_workers, 2)
            
        fd, temp_path = tempfile.mkstemp(suffix=".contextly.ast")
        os.close(fd)
        
        try:
            with open(temp_path, "w", encoding="utf-8") as dto_store:
                try:
                    import pebble
                    pool_class = pebble.ProcessPool
                except ImportError:
                    pool_class = concurrent.futures.ProcessPoolExecutor
                
                try:
                    with pool_class(max_workers=optimal_workers) as executor:
                        future_to_fp = {}
                        file_iterator = iter(target_files)
                        
                        # Pre-fill the queue to keep workers busy
                        for _ in range(optimal_workers * 2):
                            try:
                                fp = next(file_iterator)
                                future_to_fp[executor.submit(_parse_file, fp, root_str, self.max_file_size_mb)] = fp
                            except StopIteration:
                                break
                                
                        while future_to_fp:
                            done, _ = concurrent.futures.wait(
                                future_to_fp.keys(), return_when=concurrent.futures.FIRST_COMPLETED, timeout=120
                            )
                            
                            if not done:
                                diagnostics.add_error("ImportGraphBuilder", "File parsing exceeded global 120s timeout")
                                break
                                
                            for future in done:
                                fp = future_to_fp.pop(future)
                                try:
                                    dto = future.result()
                                    if dto:
                                        if dto.error:
                                            self.failed_files[dto.file_path] = dto.error
                                        else:
                                            self.assembler.add_node(dto)
                                            dto_store.write(dto.model_dump_json() + "\n")
                                except Exception as e:
                                    self.failed_files[fp] = f"ConcurrencyError: {str(e)}"
                                    
                                # Feed the next file instantly
                                try:
                                    next_fp = next(file_iterator)
                                    future_to_fp[executor.submit(_parse_file, next_fp, root_str, self.max_file_size_mb)] = next_fp
                                except StopIteration:
                                    pass
                except Exception as e:
                    diagnostics.add_warning("ImportGraphBuilder", f"ProcessPool fallback to sequential due to: {str(e)}")
                    for file_path in target_files:
                        try:
                            dto = _parse_file(file_path, root_str, self.max_file_size_mb)
                            if dto and not dto.error:
                                self.assembler.add_node(dto)
                                dto_store.write(dto.model_dump_json() + "\n")
                            elif dto and dto.error:
                                self.failed_files[dto.file_path] = dto.error
                        except Exception as seq_err:
                            self.failed_files[file_path] = f"SequentialError: {str(seq_err)}"

            if self.failed_files:
                console.print(
                    f"[yellow]Warning:[/yellow] AST parsing was partial. "
                    f"Failed to parse {len(self.failed_files)} files out of {len(target_files)}. "
                    f"The resulting graph will be incomplete."
                )

            # Pass 2: Re-read DTOs incrementally to build relationships
            def dto_generator():
                with open(temp_path, "r", encoding="utf-8") as f:
                    for line in f:
                        if line.strip():
                            yield ParsedFileDTO.model_validate_json(line)
                            
            self.assembler.build_relationships(dto_generator())
            
        finally:
            try:
                os.remove(temp_path)
            except OSError:
                pass
        
        # Pass 3: Validate the Graph
        from .validator import GraphValidator
        validator = GraphValidator()
        self.assembler.graph = validator.validate(self.assembler.graph)
        
        return self.assembler.graph
