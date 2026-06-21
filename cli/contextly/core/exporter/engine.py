from pathlib import Path
from datetime import datetime
import html
import uuid
import pyperclip

from ...utils.exceptions import ContextlyError

class ExporterEngine:
    def __init__(self, root_dir: Path):
        self.root_dir = root_dir

    def export(self, pack_name: str) -> tuple[Path, bool]:
        """
        Fuses intelligence and context packs.
        Returns a tuple of (export_path, clipboard_success).
        """
        safe_file_pack_name = Path(pack_name).name
        if not safe_file_pack_name or safe_file_pack_name in (".", ".."):
            raise ContextlyError("Invalid pack name provided.")
            
        project_context_path = self.root_dir / "PROJECT_CONTEXT.md"
        packs_dir = self.root_dir / ".contextly" / "packs"
        pack_path = packs_dir / f"{safe_file_pack_name}.contextpack.md"
        
        try:
            resolved_pack_path = pack_path.resolve(strict=False)
            resolved_pack_path.relative_to(packs_dir.resolve(strict=False))
        except (ValueError, RuntimeError):
            raise ContextlyError("Invalid pack name leading to path traversal.")
            
        export_dir = self.root_dir / ".contextly" / "exports"
        
        if not project_context_path.exists():
            raise ContextlyError(
                "PROJECT_CONTEXT.md not found in the current directory. "
                "Please run 'contextly analyze' first."
            )
            
        if not pack_path.exists():
            raise ContextlyError(
                f"Context Pack '{pack_name}' not found at {pack_path.relative_to(self.root_dir)}. "
                "Please run 'contextly pack <dir>' to generate it."
            )
            
        export_dir.mkdir(parents=True, exist_ok=True)
        
        try:
            with open(project_context_path, "r", encoding="utf-8") as f:
                intelligence_layer = f.read()
        except (FileNotFoundError, PermissionError) as e:
            raise ContextlyError(f"Error reading files: {e}")
            
        safe_pack_name = html.escape(safe_file_pack_name)

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        unique_id = uuid.uuid4().hex[:4]
        export_filename = f"export_{safe_file_pack_name}_{timestamp}_{unique_id}.md"
        export_path = export_dir / export_filename
        
        import re
        pattern = re.compile(r'</\s*context_pack\s*>', flags=re.IGNORECASE)
        
        try:
            with open(export_path, "w", encoding="utf-8") as out_f:
                out_f.write(intelligence_layer)
                out_f.write(f'\n\n<context_pack name="{safe_pack_name}">\n')
                
                try:
                    in_f = open(pack_path, "r", encoding="utf-8")
                except (FileNotFoundError, PermissionError) as e:
                    raise ContextlyError(f"Error reading files: {e}")
                
                with in_f:
                    overlap = ""
                    while True:
                        chunk = in_f.read(8 * 1024 * 1024)
                        if not chunk:
                            if overlap:
                                out_f.write(pattern.sub('&lt;/context_pack&gt;', overlap))
                            break
                        
                        buffer = overlap + chunk
                        if len(buffer) > 128:
                            safe_part = buffer[:-128]
                            overlap = buffer[-128:]
                        else:
                            safe_part = ""
                            overlap = buffer
                            
                        out_f.write(pattern.sub('&lt;/context_pack&gt;', safe_part))
                        
                out_f.write('\n</context_pack>\n')
        except ContextlyError:
            raise
        except Exception as e:
            raise ContextlyError(f"Error writing export file: {e}")
            
        clipboard_success = True
        try:
            if export_path.stat().st_size < 10 * 1024 * 1024:
                with open(export_path, "r", encoding="utf-8") as f:
                    pyperclip.copy(f.read())
            else:
                clipboard_success = False
        except Exception:
            clipboard_success = False
            
        return export_path, clipboard_success
