import os
import codecs
from pathlib import Path
from typing import Tuple, List, Optional

from ...utils.ignore import IgnoreEngine
from ...utils.exceptions import ContextlyError
from .compression import CompressionEngine
from .ranking import RankingEngine

class PackerEngine:
    def __init__(self, root_dir: Path, no_default_excludes: bool = False):
        self.root_dir = root_dir
        self.ignorer = IgnoreEngine(root_dir, no_default_excludes=no_default_excludes)
        self.compressor = CompressionEngine()
        self.ranker = RankingEngine(root_dir)
        try:
            import tiktoken
            self.tokenizer = tiktoken.get_encoding("cl100k_base")
        except ImportError:
            self.tokenizer = None
            from ...core.diagnostics import DiagnosticsContext
            DiagnosticsContext().add_warning("PackerEngine", "tiktoken not installed. Using character-count heuristic for token estimates, which may be inaccurate.")

        from ...utils.config import load_config_model
        self.config = load_config_model(root_dir)
        self.max_file_size = self.config.packer.max_file_size_mb * 1024 * 1024

    def pack(self, target_paths: List[Path], pack_name: str, max_tokens: Optional[int] = None, compress: bool = False) -> Tuple[int, str, int, Path, List[Path], int]:
        """
        Creates a context pack for the target directories.
        Returns:
            tuple: (token_estimate, token_type, file_count, output_file, skipped_files, excluded_count)
        """
        packs_dir = self.root_dir / ".contextly" / "packs"
        packs_dir.mkdir(parents=True, exist_ok=True)
        
        safe_pack_name = Path(pack_name).name
        base_name = safe_pack_name
        output_file = packs_dir / f"{safe_pack_name}.contextpack.md"
        counter = 1
        fd = None
        while True:
            try:
                fd = os.open(output_file, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o666)
                break
            except FileExistsError:
                safe_pack_name = f"{base_name}_{counter}"
                output_file = packs_dir / f"{safe_pack_name}.contextpack.md"
                counter += 1
        
        # Pre-validate access
        for target_path in target_paths:
            try:
                if target_path.is_dir():
                    next(target_path.iterdir(), None)
            except (PermissionError, OSError) as e:
                raise ContextlyError(f"Cannot access target directory {target_path}: {e}")
                
        # Phase 1: Collect all files
        all_files_set = set()
        skipped_files = []
        for target_path in target_paths:
            try:
                target_path = target_path.resolve()
                if target_path.is_file():
                    if not self.ignorer.is_ignored(target_path):
                        all_files_set.add(target_path)
                    continue
                    
                for root, dirs, files in os.walk(target_path):
                    root_path = Path(root).resolve()
                    
                    # Prune ignored directories in-place to avoid deep traversal
                    dirs[:] = [d for d in dirs if not self.ignorer.is_ignored(root_path / d)]
                    
                    for f in files:
                        file_path = root_path / f
                        if not self.ignorer.is_ignored(file_path):
                            all_files_set.add(file_path)
            except (PermissionError, OSError):
                pass
                
        # Phase 2: Rank files
        all_files = list(all_files_set)
        ranked_files = self.ranker.rank(all_files)
        
        # Phase 3 & 4: Stream Compress, Measure, Select, and Write
        selected_files = []
        excluded_files = []
        
        header_text = f"# Context Pack: {pack_name}\n\n"
        if self.tokenizer:
            try:
                current_tokens = len(self.tokenizer.encode(header_text, disallowed_special=()))
            except ValueError:
                current_tokens = len(header_text) / 3.5
        else:
            current_tokens = len(header_text) / 3.5
            
        with os.fdopen(fd, "w", encoding="utf-8") as out_f:
            out_f.write(header_text)
            
            for path in ranked_files:
                try:
                    file_size = path.stat().st_size
                    if file_size > self.max_file_size:
                        skipped_files.append(path)
                        continue

                    try:
                        rel_path = path.relative_to(self.root_dir).as_posix()
                    except ValueError:
                        rel_path = path.name
                    ext = path.suffix.replace('.', '')
                    
                    is_py_compress = (compress and path.suffix.lower() == '.py')
                    
                    with open(path, "rb") as in_f:
                        first_kb = in_f.read(1024)
                        if b'\x00' in first_kb:
                            skipped_files.append(path)
                            continue
                        in_f.seek(0)
                        
                        out_f.flush()
                        start_pos = out_f.tell()
                        header_str = f"## File: `{rel_path}`\n```{ext}\n"
                        out_f.write(header_str)
                        
                        file_tokens = 0
                        is_excluded = False
                        
                        if self.tokenizer:
                            try:
                                file_tokens += len(self.tokenizer.encode(header_str, disallowed_special=()))
                            except ValueError:
                                file_tokens += len(header_str) / 3.5
                        else:
                            file_tokens += len(header_str) / 3.5
                        
                        if is_py_compress:
                            try:
                                raw_code = in_f.read().decode("utf-8")
                            except UnicodeDecodeError:
                                skipped_files.append(path)
                                out_f.seek(start_pos)
                                out_f.truncate()
                                continue
                                
                            compressed = self.compressor.compress(path, raw_code)
                            body = compressed if compressed.endswith('\n') else compressed + '\n'
                            
                            if self.tokenizer:
                                try:
                                    file_tokens += len(self.tokenizer.encode(body, disallowed_special=()))
                                except ValueError:
                                    file_tokens += len(body) / 3.5
                            else:
                                file_tokens += len(body) / 3.5
                                
                            if max_tokens and current_tokens + file_tokens > max_tokens:
                                excluded_files.append(path)
                                out_f.seek(start_pos)
                                out_f.truncate()
                                continue
                                
                            out_f.write(body)
                            out_f.write(f"```\n\n")
                            current_tokens += file_tokens
                            selected_files.append(path)
                            
                        else:
                            decoder = codecs.getincrementaldecoder('utf-8')(errors='strict')
                            try:
                                while True:
                                    chunk = in_f.read(4096)
                                    text_chunk = decoder.decode(chunk, final=not bool(chunk))
                                    if text_chunk:
                                        if self.tokenizer:
                                            try:
                                                chunk_cost = len(self.tokenizer.encode(text_chunk, disallowed_special=()))
                                            except ValueError:
                                                chunk_cost = len(text_chunk) / 3.5
                                        else:
                                            chunk_cost = len(text_chunk) / 3.5
                                            
                                        file_tokens += chunk_cost
                                        if max_tokens and current_tokens + file_tokens > max_tokens:
                                            is_excluded = True
                                            break
                                        
                                        out_f.write(text_chunk)
                                        
                                    if not chunk:
                                        break
                            except UnicodeDecodeError:
                                skipped_files.append(path)
                                out_f.seek(start_pos)
                                out_f.truncate()
                                continue
                                
                            if is_excluded:
                                excluded_files.append(path)
                                out_f.flush()
                                out_f.truncate(start_pos)
                                out_f.seek(start_pos)
                                continue
                                
                            out_f.write(f"\n```\n\n")
                            current_tokens += file_tokens
                            selected_files.append(path)
                            
                except Exception:
                    skipped_files.append(path)

            if excluded_files:
                out_f.write(f"## Excluded Files (Token Limit)\n")
                out_f.write(f"The following {len(excluded_files)} files were excluded to fit within the {max_tokens} token limit:\n")
                for path in excluded_files:
                    try:
                        rel_path = path.relative_to(self.root_dir).as_posix()
                    except ValueError:
                        rel_path = path.name
                    out_f.write(f"- `{rel_path}`\n")

        if self.tokenizer:
            token_estimate = int(current_tokens)
            token_type = "Exact Tokens (cl100k_base)"
        else:
            token_estimate = int(current_tokens)
            token_type = "Estimated Tokens (chars / 3.5)"
            
        return token_estimate, token_type, len(selected_files), output_file, skipped_files, len(excluded_files)
