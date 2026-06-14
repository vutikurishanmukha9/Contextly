import os
from pathlib import Path
from typing import Tuple, List, Optional

from ...utils.ignore import IgnoreEngine
from ...utils.exceptions import ContextlyError
from .compression import CompressionEngine
from .ranking import RankingEngine

class PackerEngine:
    def __init__(self, root_dir: Path):
        self.root_dir = root_dir
        self.ignorer = IgnoreEngine(root_dir)
        self.compressor = CompressionEngine()
        self.ranker = RankingEngine(root_dir)
        try:
            import tiktoken
            self.tokenizer = tiktoken.get_encoding("cl100k_base")
        except ImportError:  # pragma: no cover
            self.tokenizer = None

    def pack(self, target_paths: List[Path], pack_name: str, max_tokens: Optional[int] = None, compress: bool = False) -> Tuple[int, str, int, Path, List[Path], int]:
        """
        Creates a context pack for the target directories.
        Returns:
            tuple: (token_estimate, token_type, file_count, output_file, skipped_files, excluded_count)
        """
        packs_dir = self.root_dir / ".contextly" / "packs"
        packs_dir.mkdir(parents=True, exist_ok=True)
        
        safe_pack_name = os.path.basename(pack_name.replace("\\", "/"))
        output_file = packs_dir / f"{safe_pack_name}.contextpack.md"
        
        # Pre-validate access
        for target_path in target_paths:
            try:
                if target_path.is_dir():
                    next(target_path.iterdir(), None)
            except (PermissionError, OSError) as e:
                raise ContextlyError(f"Cannot access target directory {target_path}: {e}")
                
        # Phase 1: Collect all files
        all_files = []
        skipped_files = []
        for target_path in target_paths:
            try:
                if target_path.is_file():
                    if not self.ignorer.is_ignored(target_path):
                        all_files.append(target_path)
                    continue
                    
                for root, dirs, files in os.walk(target_path):
                    root_path = Path(root)
                    
                    # Prune ignored directories in-place to avoid deep traversal
                    dirs[:] = [d for d in dirs if not self.ignorer.is_ignored(root_path / d)]
                    
                    for f in files:
                        file_path = root_path / f
                        if not self.ignorer.is_ignored(file_path):
                            all_files.append(file_path)
            except (PermissionError, OSError):
                pass
                
        # Phase 2: Rank files
        ranked_files = self.ranker.rank(all_files)
        
        # Phase 3: Compress, Measure, and Select
        selected_files = []
        excluded_files = []
        compressed_cache = {}
        current_tokens = 0
        current_chars = 0
        
        for path in ranked_files:
            try:
                try:
                    with open(path, "r", encoding="utf-8") as in_f:
                        raw_code = in_f.read()
                except UnicodeDecodeError:
                    with open(path, "r", encoding="latin-1", errors="ignore") as in_f:
                        raw_code = in_f.read()
                    
                compressed_code = self.compressor.compress(path, raw_code) if compress else raw_code
                
                try:
                    rel_path = path.relative_to(self.root_dir).as_posix()
                except ValueError:
                    rel_path = path.name
                ext = path.suffix.replace('.', '')
                
                # Pre-calculate wrapper to accurately measure overhead
                wrapper_str = f"## File: `{rel_path}`\n```{ext}\n"
                if not compressed_code.endswith('\n'):
                    wrapper_str += '\n'
                wrapper_str += "```\n\n"
                
                if self.tokenizer:
                    try:
                        file_cost = len(self.tokenizer.encode(wrapper_str + compressed_code, disallowed_special=()))
                    except Exception:
                        skipped_files.append(path)
                        continue
                else:
                    file_cost = (len(wrapper_str) + len(compressed_code)) / 4.0

                if max_tokens and current_tokens + file_cost > max_tokens:
                    excluded_files.append(path)
                    continue
                    
                current_tokens += file_cost
                    
                selected_files.append(path)
                compressed_cache[path] = compressed_code
                
            except UnicodeDecodeError:
                skipped_files.append(path)
            except (FileNotFoundError, PermissionError, OSError):
                skipped_files.append(path)
                
                
        # Phase 4: Write Output Streamingly
        with open(output_file, "w", encoding="utf-8") as out_f:
            out_f.write(f"# Context Pack: {pack_name}\n\n")
            
            for path in selected_files:
                try:
                    rel_path = path.relative_to(self.root_dir).as_posix()
                except ValueError:
                    rel_path = path.name
                    
                out_f.write(f"## File: `{rel_path}`\n")
                ext = path.suffix.replace('.', '')
                try:
                    compressed_code = compressed_cache[path]
                    out_f.write(f"```{ext}\n")
                    out_f.write(compressed_code)
                    if not compressed_code.endswith('\n'):
                        out_f.write('\n')
                    out_f.write(f"```\n\n")
                except (OSError, IOError, UnicodeDecodeError):
                    out_f.write(f"> [!WARNING]\n> File became unreadable during packing.\n\n")
                
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
            token_type = "Estimated Tokens (chars / 4)"
            
        return token_estimate, token_type, len(selected_files), output_file, skipped_files, len(excluded_files)
