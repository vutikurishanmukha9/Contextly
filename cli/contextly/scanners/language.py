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
            
            for path in root_dir.rglob('*'):
                try:
                    if path.is_file():
                        if ignorer.is_ignored(path):
                            continue
                        if path.suffix:
                            exts[path.suffix.lower()] += 1
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
