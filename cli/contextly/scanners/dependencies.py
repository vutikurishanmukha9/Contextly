import json
from pathlib import Path
from .base import BaseScanner, ScannerError
from ..types.models import DependencyScanResult
from ..utils.ignore import IgnoreEngine

class DependencyScanner(BaseScanner):
    @property
    def name(self) -> str:
        return "Dependency Scanner"

    def scan(self, root_dir: Path, **kwargs) -> DependencyScanResult:
        try:
            result = DependencyScanResult()
            ignorer = IgnoreEngine(root_dir)
            
            # Helper to safely parse package.json dependencies
            def _parse_package_json(filepath: Path):
                try:
                    with open(filepath, 'r') as f:
                        data = json.load(f)
                        deps = list(data.get("dependencies", {}).keys()) + list(data.get("devDependencies", {}).keys())
                        result.npm.extend(deps)
                except Exception:
                    pass

            # Root package.json
            if (root_dir / "package.json").exists():
                _parse_package_json(root_dir / "package.json")
                
            # Quick sub-directory scan for package.json (to catch mono-repos like "frontend/")
            # We don't do full rglob to save time, just one level deep
            for item in root_dir.iterdir():
                if item.is_dir() and not ignorer.is_ignored(item):
                    if (item / "package.json").exists():
                        _parse_package_json(item / "package.json")
                
            # Check python (requirements.txt)
            req_txt = root_dir / "requirements.txt"
            if req_txt.exists():
                try:
                    with open(req_txt, 'r') as f:
                        lines = f.readlines()
                        result.python.extend([line.split("==")[0].strip() for line in lines if line.strip() and not line.startswith("#")])
                except Exception:
                    pass
                    
            # Check python (pyproject.toml)
            pyproject = root_dir / "pyproject.toml"
            if pyproject.exists():
                try:
                    with open(pyproject, 'r') as f:
                        content = f.read()
                        if "typer" in content: result.python.append("typer")
                        if "rich" in content: result.python.append("rich")
                        if "pyyaml" in content: result.python.append("pyyaml")
                        if "pydantic" in content: result.python.append("pydantic")
                except Exception:
                    pass

            # De-duplicate
            result.npm = list(set(result.npm))
            result.python = list(set(result.python))
            
            return result
            
        except Exception as e:
            raise ScannerError(f"Dependency scan failed: {str(e)}")
