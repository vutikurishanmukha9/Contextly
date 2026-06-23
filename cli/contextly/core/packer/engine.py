import os
import codecs
import tempfile
import shutil
from pathlib import Path
from typing import Tuple, List, Optional

from ...utils.ignore import IgnoreEngine
from ...utils.exceptions import ContextlyError, ValidationError
from ...utils.paths import safe_resolve
from .ranking import RankingEngine
from ..graph.parsers.registry import ParserRegistry
from .formatter import KnowledgeFormatter
from ..graph.builder import ImportGraphBuilder
from ..graph.validator import GraphValidator

class PackerEngine:
    def __init__(self, root_dir: Path, no_default_excludes: bool = False):
        self.root_dir = root_dir
        self.ignorer = IgnoreEngine(root_dir, no_default_excludes=no_default_excludes)
        self.ranker = RankingEngine(root_dir)
        try:
            import tiktoken
            self.tokenizer = tiktoken.get_encoding("cl100k_base")
        except ImportError:
            self.tokenizer = None
            from ...core.diagnostics import DiagnosticsContext
            self.token_multiplier = float(os.environ.get("CONTEXTLY_TOKEN_MULTIPLIER", "3.5"))
            DiagnosticsContext().add_warning("PackerEngine", f"tiktoken not installed. Using character-count heuristic (/{self.token_multiplier}) for token estimates, which may be inaccurate.")
        else:
            self.token_multiplier = 3.5

        from ...utils.config import load_config_model
        self.config = load_config_model(root_dir)
        self.max_file_size = int(self.config.packer.max_file_size_mb * 1024 * 1024)

    def _estimate_tokens(self, text: str) -> float:
        """Fast character-count heuristic for in-loop token budget enforcement."""
        return len(text) / self.token_multiplier

    def _exact_token_count(self, text: str) -> int:
        """Exact token count using tiktoken. Falls back to heuristic if unavailable."""
        if self.tokenizer:
            try:
                return len(self.tokenizer.encode(text, disallowed_special=()))
            except ValueError:
                return int(len(text) / self.token_multiplier)
        return int(len(text) / self.token_multiplier)

    def _is_binary_file(self, first_kb: bytes) -> bool:
        """
        Detects binary files by checking for null bytes, with an exemption
        for UTF-16 encoded text files which legitimately contain null bytes.
        """
        if b'\x00' not in first_kb:
            return False

        # Check if this might be UTF-16 before classifying as binary
        import codecs
        has_bom = first_kb.startswith(codecs.BOM_UTF16_LE) or first_kb.startswith(codecs.BOM_UTF16_BE)
        even_kb = first_kb if len(first_kb) % 2 == 0 else first_kb[:-1]
        for encoding in ('utf-16', 'utf-16-le', 'utf-16-be'):
            try:
                text = even_kb.decode(encoding, errors='strict')
                if text:
                    if has_bom:
                        return False
                    ascii_chars = sum(1 for c in text if ord(c) < 128 and (c.isprintable() or c.isspace()))
                    if (ascii_chars / len(text)) > 0.3:
                        return False  # Valid UTF-16 text, not binary
            except Exception:
                continue

        return True  # Contains null bytes and is not valid UTF-16

    def pack(self, target_paths: List[Path], pack_name: str, max_tokens: Optional[int] = None, raw: bool = False, task: Optional[str] = None, force: bool = False) -> Tuple[int, str, int, Path, List[Path], int]:
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
        
        # Determine final file name with UUID fallback to prevent overwriting
        try:
            target_fd = os.open(output_file, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o600)
            os.close(target_fd)
        except FileExistsError:
            import uuid
            safe_pack_name = f"{base_name}_{uuid.uuid4().hex[:8]}"
            output_file = packs_dir / f"{safe_pack_name}.contextpack.md"
            
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
                try:
                    target_path = safe_resolve(target_path, self.root_dir)
                except ValidationError:
                    from ...core.diagnostics import DiagnosticsContext
                    DiagnosticsContext().add_warning("PackerEngine", f"Path traversal attempt blocked: {target_path}")
                    continue

                if target_path.is_file():
                    if not self.ignorer.is_ignored(target_path):
                        all_files_set.add(target_path)
                    continue
                    
                for root, dirs, files in os.walk(target_path):
                    root_path = Path(root)
                    try:
                        root_path = safe_resolve(root_path, self.root_dir)
                    except ValidationError:
                        from ...core.diagnostics import DiagnosticsContext
                        DiagnosticsContext().add_warning("PackerEngine", f"Path traversal attempt blocked: {root_path}")
                        continue
                    
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
        
        if not force and not max_tokens:
            total_size = sum(f.stat().st_size for f in all_files)
            estimated_tokens = int(total_size / self.token_multiplier)
            if estimated_tokens > 100000:
                raise ContextlyError(f"Estimated context size (~{estimated_tokens:,} tokens) is very large and may exceed LLM context windows.\nUse --force to generate anyway, or use --max-tokens to limit the size.")
        
        
        if task:
            from ...utils.console import console
            console.print("[dim]Building graph for task relevance...[/dim]")
            builder = ImportGraphBuilder(self.root_dir)
            graph = builder.build()
            validator = GraphValidator()
            graph = validator.validate(graph)
            self.ranker = RankingEngine(self.root_dir, task=task, graph=graph)
            
        ranked_files = self.ranker.rank(all_files)
        
        # Phase 3 & 4: Stream Compress, Measure, Select, and Write
        # Uses fast character-count heuristic for in-loop budget enforcement.
        # Final exact token count is computed after all files are written.
        selected_files = []
        excluded_files = []
        
        header_text = f"# Context Pack: {pack_name}\n\n"
        
        if task:
            header_text += f"## Navigation Guidance (Task: {task})\n\n"
            # Top 20% read first, bottom 40% ignore
            if len(ranked_files) > 0:
                top_count = max(1, int(len(ranked_files) * 0.2))
                bottom_count = max(1, int(len(ranked_files) * 0.4))
                read_first = ranked_files[:top_count]
                ignore = ranked_files[-bottom_count:] if len(ranked_files) > 3 else []
                
                header_text += "**Read First:**\n"
                for f in read_first[:10]:
                    try:
                        rel = f.relative_to(self.root_dir)
                    except ValueError:
                        rel = f.name
                    header_text += f"- `{rel}`\n"
                    
                if ignore:
                    header_text += "\n**Ignore:**\n"
                    for f in ignore[-10:]:
                        try:
                            rel = f.relative_to(self.root_dir)
                        except ValueError:
                            rel = f.name
                        header_text += f"- `{rel}`\n"
            header_text += "\n---\n\n"
            
        current_tokens = self._estimate_tokens(header_text)
        
        # Pre-filter by budget using heuristic to maintain cross-domain representation
        if max_tokens:
            budget_chars = max_tokens * self.token_multiplier
            current_chars = len(header_text)
            selected_paths = []
            for p in ranked_files:
                try:
                    size = p.stat().st_size
                except Exception:
                    size = 1000
                if current_chars + size > budget_chars:
                    excluded_files.append(p)
                else:
                    selected_paths.append(p)
                    current_chars += size
            ranked_files = selected_paths
            
        import collections
        domain_groups = collections.defaultdict(list)
        for path in ranked_files:
            try:
                rel = path.relative_to(self.root_dir)
                parts = rel.parts
                domain = "root"
                if len(parts) > 1:
                    if parts[0] in ("src", "app", "lib", "cli", "frontend", "backend"):
                        if len(parts) > 2:
                            domain = f"{parts[0]}/{parts[1]}"
                    else:
                        domain = parts[0]
                domain_groups[domain].append(path)
            except ValueError:
                domain_groups["root"].append(path)
            
        # Write to a temporary file and atomically rename on Windows
        fd, temp_path_str = tempfile.mkstemp(dir=packs_dir, suffix=".tmp")
        temp_path = Path(temp_path_str)
        
        with os.fdopen(fd, "wb") as out_f:
            out_f.write(header_text.encode("utf-8"))
            
            for domain, paths in domain_groups.items():
                domain_header = f"## Domain: `{domain}`\n\n"
                out_f.write(domain_header.encode("utf-8"))
                current_tokens += self._estimate_tokens(domain_header)
                
                for path in paths:
                    start_pos = None
                    try:
                        # Flush before recording position for reliable rollback
                        out_f.flush()
                        start_pos = out_f.tell()
                    
                        file_size = path.stat().st_size
                        if file_size > self.max_file_size:
                            skipped_files.append(path)
                            continue

                        try:
                            rel_path = path.relative_to(self.root_dir).as_posix()
                        except ValueError:
                            rel_path = path.name
                        ext = path.suffix.replace('.', '')
                    
                        with open(path, "rb") as in_f:
                            first_kb = in_f.read(1024)
                            if self._is_binary_file(first_kb):
                                skipped_files.append(path)
                                continue
                            in_f.seek(0)
                        
                            parser = None if raw else ParserRegistry.get_parser(ext)
                            is_excluded = False
                        
                            if parser:
                                try:
                                    raw_bytes = in_f.read(self.max_file_size + 1)
                                    if len(raw_bytes) > self.max_file_size:
                                        skipped_files.append(path)
                                        from ...core.diagnostics import DiagnosticsContext
                                        DiagnosticsContext().add_warning("PackerEngine", f"File grew beyond max size during read (TOCTOU prevention): {path.name}")
                                        out_f.flush()
                                        out_f.seek(start_pos)
                                        out_f.truncate(start_pos)
                                        continue
                                    raw_code = raw_bytes.decode("utf-8")
                                except UnicodeDecodeError:
                                    skipped_files.append(path)
                                    # Defensive flush before rollback
                                    out_f.flush()
                                    out_f.seek(start_pos)
                                    out_f.truncate(start_pos)
                                    continue
                                
                                parsed_dto = parser.parse(str(path), raw_code, str(self.root_dir))
                                body = KnowledgeFormatter.format_file_knowledge(parsed_dto)
                            
                                header_str = f"### File: `{rel_path}`\n```{ext}\n"
                                footer_str = "\n```\n\n"
                            
                                file_tokens = self._estimate_tokens(header_str) + self._estimate_tokens(body) + self._estimate_tokens(footer_str)
                                
                                if max_tokens and current_tokens + file_tokens > max_tokens:
                                    excluded_files.append(path)
                                    out_f.flush()
                                    out_f.seek(start_pos)
                                    out_f.truncate(start_pos)
                                    continue
                                
                                out_f.write(header_str.encode("utf-8"))
                                out_f.write(body.encode("utf-8"))
                                out_f.write(footer_str.encode("utf-8"))
                                current_tokens += file_tokens
                                selected_files.append(path)
                            
                            elif not raw:
                                try:
                                    raw_bytes = in_f.read(self.max_file_size + 1)
                                    if len(raw_bytes) > self.max_file_size:
                                        skipped_files.append(path)
                                        out_f.flush()
                                        out_f.seek(start_pos)
                                        out_f.truncate(start_pos)
                                        continue
                                    raw_code = raw_bytes.decode("utf-8")
                                except UnicodeDecodeError:
                                    skipped_files.append(path)
                                    out_f.flush()
                                    out_f.seek(start_pos)
                                    out_f.truncate(start_pos)
                                    continue
                                
                                body = KnowledgeFormatter.format_metadata_fallback(str(path), raw_code)
                            
                                header_str = f"### File: `{rel_path}`\n"
                                footer_str = "\n\n"
                            
                                file_tokens = self._estimate_tokens(header_str) + self._estimate_tokens(body) + self._estimate_tokens(footer_str)
                            
                                if max_tokens and current_tokens + file_tokens > max_tokens:
                                    excluded_files.append(path)
                                    out_f.flush()
                                    out_f.seek(start_pos)
                                    out_f.truncate(start_pos)
                                    continue
                                
                                out_f.write(header_str.encode("utf-8"))
                                out_f.write(body.encode("utf-8"))
                                out_f.write(footer_str.encode("utf-8"))
                                current_tokens += file_tokens
                                selected_files.append(path)
                            
                            else:
                                header_str = f"## File: `{rel_path}`\n```{ext}\n"
                                out_f.write(header_str.encode("utf-8"))
                            
                                file_tokens = self._estimate_tokens(header_str)
                                decoder = codecs.getincrementaldecoder('utf-8')(errors='replace')
                                while True:
                                    chunk = in_f.read(4096)
                                    text_chunk = decoder.decode(chunk, final=not bool(chunk))
                                    if text_chunk:
                                        chunk_cost = self._estimate_tokens(text_chunk)
                                        file_tokens += chunk_cost
                                        if max_tokens and current_tokens + file_tokens > max_tokens:
                                            is_excluded = True
                                            break
                                    
                                        out_f.write(text_chunk.encode("utf-8"))
                                    
                                    if not chunk:
                                        break
                                
                                if is_excluded:
                                    excluded_files.append(path)
                                    out_f.flush()
                                    out_f.truncate(start_pos)
                                    out_f.seek(start_pos)
                                    continue
                                
                                out_f.write(b"\n```\n\n")
                                current_tokens += file_tokens
                                selected_files.append(path)
                            
                    except Exception as e:
                        # Roll back any partially written content to prevent stream corruption
                        # Defensive flush before rollback
                        if start_pos is not None:
                            out_f.flush()
                            out_f.seek(start_pos)
                            out_f.truncate(start_pos)
                        skipped_files.append(path)
                        from ...core.diagnostics import DiagnosticsContext
                        DiagnosticsContext().add_warning("PackerEngine", f"Failed to pack {path.name}: {type(e).__name__} - {str(e)}")

            if excluded_files:
                out_f.write(b"## Excluded Files (Token Limit)\n")
                out_f.write(f"The following {len(excluded_files)} files were excluded to fit within the {max_tokens} token limit:\n".encode("utf-8"))
                for path in excluded_files:
                    try:
                        rel_path = path.relative_to(self.root_dir).as_posix()
                    except ValueError:
                        rel_path = path.name
                    out_f.write(f"- `{rel_path}`\n".encode("utf-8"))

        # Safely atomic rename
        try:
            if output_file.exists():
                output_file.unlink()
        except OSError:
            pass
            
        try:
            shutil.move(str(temp_path), str(output_file))
        except OSError as e:
            if temp_path.exists():
                temp_path.unlink()
            raise ContextlyError(f"Failed to write context pack to {output_file}: {e}")

        # Compute final exact token count from the completed output file
        if self.tokenizer:
            try:
                with open(output_file, "r", encoding="utf-8") as f:
                    final_content = f.read()
                token_estimate = len(self.tokenizer.encode(final_content, disallowed_special=()))
                token_type = "Exact Tokens (cl100k_base)"
            except (ValueError, OSError):
                token_estimate = int(current_tokens)
                token_type = f"Estimated Tokens (chars / {self.token_multiplier})"
        else:
            token_estimate = int(current_tokens)
            token_type = f"Estimated Tokens (chars / {self.token_multiplier})"
            
        return token_estimate, token_type, len(selected_files), output_file, skipped_files, len(excluded_files)

