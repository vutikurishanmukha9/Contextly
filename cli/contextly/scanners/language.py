from pathlib import Path
from collections import Counter
from .base import BaseScanner, ScannerError
from ..types.models import LanguageScanResult
from ..utils.ignore import IgnoreEngine

class LanguageScanner(BaseScanner):
    @property
    def name(self) -> str:
        return "Language Scanner"

    def scan(self, root_dir: Path, **kwargs) -> LanguageScanResult:
        try:
            exts = Counter()
            ignorer = IgnoreEngine(root_dir)
            
            import os
            for root, dirs, files in os.walk(root_dir):
                root_path = Path(root)
                
                # Prune ignored directories in-place
                dirs[:] = [d for d in dirs if not ignorer.is_ignored(root_path / d)]
                
                for f in files:
                    try:
                        file_path = root_path / f
                        if ignorer.is_ignored(file_path):
                            continue
                        if file_path.suffix:
                            exts[file_path.suffix.lower()] += 1
                    except PermissionError:
                        continue
                        
            total = sum(exts.values())
            if total == 0:
                return LanguageScanResult(primary="Unknown", breakdown={})
                
            primary_ext = exts.most_common(1)[0][0]
            ext_map = {
                '.ts': 'TypeScript',
                '.tsx': 'TypeScript (React)',
                '.js': 'JavaScript',
                '.jsx': 'JavaScript (React)',
                '.py': 'Python',
                '.go': 'Go',
                '.rs': 'Rust',
                '.java': 'Java',
                '.md': 'Markdown'
            }
            
            primary_lang = ext_map.get(primary_ext, primary_ext)
            
            return LanguageScanResult(
                primary=primary_lang,
                breakdown=dict(exts.most_common(5))
            )
        except Exception as e:
            raise ScannerError(f"Language scan failed: {str(e)}")
