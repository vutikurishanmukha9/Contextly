from pathlib import Path
from typing import Tuple

from ...utils.ignore import IgnoreEngine
from ...utils.exceptions import ContextlyError

class PackerEngine:
    def __init__(self, root_dir: Path):
        self.root_dir = root_dir
        self.ignorer = IgnoreEngine(root_dir)
        try:
            import tiktoken
            self.tokenizer = tiktoken.get_encoding("cl100k_base")
        except ImportError:  # pragma: no cover
            self.tokenizer = None

    def pack(self, target_path: Path, pack_name: str) -> Tuple[int, str, int, Path]:
        """
        Creates a context pack for the target directory.
        Returns:
            tuple: (token_estimate, token_type, file_count, output_file)
        """
        packs_dir = self.root_dir / ".contextly" / "packs"
        packs_dir.mkdir(parents=True, exist_ok=True)
        
        output_file = packs_dir / f"{pack_name}.contextpack.md"
        
        file_count = 0
        total_chars = 0
        total_tokens = 0
        
        # Pre-validate access
        try:
            if target_path.is_dir():
                next(target_path.iterdir(), None)
        except (PermissionError, OSError) as e:
            raise ContextlyError(f"Cannot access target directory {target_path}: {e}")
            
        with open(output_file, "w", encoding="utf-8") as out_f:
            out_f.write(f"# Context Pack: {pack_name}\n\n")
            
            try:
                for path in target_path.rglob('*'):
                    try:
                        if path.is_file():
                            if self.ignorer.is_ignored(path):
                                continue
                            
                            try:
                                rel_path = path.relative_to(self.root_dir).as_posix()
                                out_f.write(f"## File: `{rel_path}`\n")
                                ext = path.suffix.replace('.', '')
                                out_f.write(f"```{ext}\n")
                                
                                with open(path, "r", encoding="utf-8") as in_f:
                                    for line in in_f:
                                        out_f.write(line)
                                        if self.tokenizer:
                                            total_tokens += len(self.tokenizer.encode(line, disallowed_special=()))
                                        else:
                                            total_chars += len(line)
                                            
                                out_f.write(f"\n```\n\n")
                                file_count += 1
                                
                            except UnicodeDecodeError:
                                # Skip binary files silently
                                pass
                            except (FileNotFoundError, PermissionError, OSError):
                                # Ignore unreadable individual files
                                pass
                    except PermissionError:
                        continue
            except PermissionError:
                pass
                
        if self.tokenizer:
            token_estimate = total_tokens
            token_type = "Exact Tokens (cl100k_base)"
        else:
            token_estimate = total_chars // 4
            token_type = "Estimated Tokens (chars / 4)"
            
        return token_estimate, token_type, file_count, output_file
