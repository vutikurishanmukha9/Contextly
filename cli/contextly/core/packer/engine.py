import os
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

        from ...utils.config import load_config
        self.config = load_config(root_dir) or {}
        packer_config = self.config.get("packer", {}) if isinstance(self.config, dict) else {}
        self.max_file_size = packer_config.get("max_file_size_mb", 5) * 1024 * 1024

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
        while output_file.exists():
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
        
        # Phase 3: Compress, Measure, and Select
        selected_files = []
        excluded_files = []
        compressed_cache = {}
        
        header_text = f"# Context Pack: {pack_name}\n\n"
        if self.tokenizer:
            try:
                current_tokens = len(self.tokenizer.encode(header_text, disallowed_special=()))
            except ValueError:
                current_tokens = len(header_text) / 3.5
        else:
            current_tokens = len(header_text) / 3.5
        
        for path in ranked_files:
            try:
                # 1. Size constraint check before reading the file into memory
                try:
                    file_size = path.stat().st_size
                except OSError:
                    skipped_files.append(path)
                    continue

                if file_size > self.max_file_size:
                    skipped_files.append(path)
                    continue

                # 2. Binary detection check via first 1024 bytes in binary mode
                try:
                    with open(path, "rb") as check_f:
                        chunk = check_f.read(1024)
                        if b'\x00' in chunk:
                            skipped_files.append(path)
                            continue
                except OSError:
                    skipped_files.append(path)
                    continue

                # 3. Read and decode logic
                try:
                    with open(path, "r", encoding="utf-8") as in_f:
                        raw_code = in_f.read()
                except UnicodeDecodeError:
                    try:
                        with open(path, "r", encoding="latin-1", errors="ignore") as in_f:
                            raw_code = in_f.read()
                        if '\x00' in raw_code:
                            skipped_files.append(path)
                            continue
                    except OSError:
                        skipped_files.append(path)
                        continue
                except OSError:
                    skipped_files.append(path)
                    continue
                    
                compressed_code = self.compressor.compress(path, raw_code) if compress else raw_code
                
                try:
                    rel_path = path.relative_to(self.root_dir).as_posix()
                except ValueError:
                    rel_path = path.name
                ext = path.suffix.replace('.', '')
                
                body = compressed_code if compressed_code.endswith('\n') else compressed_code + '\n'
                full_text = f"## File: `{rel_path}`\n```{ext}\n{body}```\n\n"
                
                if self.tokenizer:
                    try:
                        file_cost = len(self.tokenizer.encode(full_text, disallowed_special=()))
                    except ValueError:
                        skipped_files.append(path)
                        continue
                else:
                    file_cost = len(full_text) / 3.5

                if max_tokens and current_tokens + file_cost > max_tokens:
                    excluded_files.append(path)
                    continue
                    
                current_tokens += file_cost
                    
                selected_files.append(path)
                compressed_cache[path] = body
                
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
            token_type = "Estimated Tokens (chars / 3.5)"
            
        return token_estimate, token_type, len(selected_files), output_file, skipped_files, len(excluded_files)
