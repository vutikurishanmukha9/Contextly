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
        project_context_path = self.root_dir / "PROJECT_CONTEXT.md"
        pack_path = self.root_dir / ".contextly" / "packs" / f"{safe_file_pack_name}.contextpack.md"
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
                
            with open(pack_path, "r", encoding="utf-8") as f:
                pack_layer = f.read()
        except (FileNotFoundError, PermissionError) as e:
            raise ContextlyError(f"Error reading files: {e}")
            
        safe_pack_name = html.escape(safe_file_pack_name)
        # Escape closing tags to protect downstream XML parsing boundaries
        safe_pack_layer = pack_layer.replace("</context_pack>", r"<\/context_pack>")
        fused_content = f"""{intelligence_layer}

<context_pack name="{safe_pack_name}">
{safe_pack_layer}
</context_pack>
"""

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        unique_id = uuid.uuid4().hex[:4]
        export_filename = f"export_{safe_file_pack_name}_{timestamp}_{unique_id}.md"
        export_path = export_dir / export_filename
        
        try:
            with open(export_path, "w", encoding="utf-8") as f:
                f.write(fused_content)
        except (FileNotFoundError, PermissionError) as e:
            raise ContextlyError(f"Error writing export file: {e}")
            
        clipboard_success = True
        try:
            pyperclip.copy(fused_content)
        except Exception:
            clipboard_success = False
            
        return export_path, clipboard_success
