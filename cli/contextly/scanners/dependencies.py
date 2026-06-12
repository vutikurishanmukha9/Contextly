import json
import re
from pathlib import Path
from .base import BaseScanner, ScannerError
from ..types.models import DependencyScanResult
from ..utils.ignore import IgnoreEngine
from ..utils.console import console

try:
    import tomllib
except ImportError:
    try:
        import tomli as tomllib
    except ImportError:
        tomllib = None

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
                    with open(filepath, 'r', encoding="utf-8") as f:
                        data = json.load(f)
                        if isinstance(data, dict):
                            deps = list(data.get("dependencies", {}).keys()) + list(data.get("devDependencies", {}).keys())
                            for d in deps:
                                if d not in result.npm:
                                    result.npm.append(d)
                except (FileNotFoundError, json.JSONDecodeError, PermissionError) as e:
                    console.print(f"[yellow]Warning:[/yellow] Could not parse {filepath.relative_to(root_dir)}: {str(e)}")
                except Exception as e:
                    console.print(f"[yellow]Warning:[/yellow] Unexpected error reading {filepath.relative_to(root_dir)}: {str(e)}")

            # Root package.json
            if (root_dir / "package.json").exists():
                _parse_package_json(root_dir / "package.json")
                
            # Quick sub-directory scan for package.json (to catch mono-repos like "frontend/")
            try:
                for item in root_dir.iterdir():
                    if item.is_dir() and not ignorer.is_ignored(item):
                        if (item / "package.json").exists():
                            _parse_package_json(item / "package.json")
            except PermissionError:
                pass
                
            # Check python (requirements.txt)
            req_txt = root_dir / "requirements.txt"
            if req_txt.exists():
                try:
                    with open(req_txt, 'r', encoding="utf-8") as f:
                        for line in f:
                            if line.strip() and not line.startswith("#"):
                                dep = line.split("==")[0].strip()
                                if dep not in result.python:
                                    result.python.append(dep)
                except (FileNotFoundError, PermissionError, UnicodeDecodeError) as e:
                    console.print(f"[yellow]Warning:[/yellow] Could not parse requirements.txt: {str(e)}")
                except Exception as e:
                    console.print(f"[yellow]Warning:[/yellow] Unexpected error reading requirements.txt: {str(e)}")
                    
            # Check python (pyproject.toml)
            pyproject = root_dir / "pyproject.toml"
            if pyproject.exists():
                try:
                    with open(pyproject, 'rb') as f:
                        if tomllib is not None:
                            data = tomllib.load(f)
                            # Extract standard dependencies
                            deps = data.get("project", {}).get("dependencies", [])
                            # Strip out version constraints and add safely
                            for dep in deps:
                                clean_dep = re.split(r'[=<>~]', dep)[0].strip()
                                if clean_dep not in result.python:
                                    result.python.append(clean_dep)
                        else:
                            console.print("[yellow]Warning:[/yellow] `tomllib` (or `tomli`) is not installed. Skipping pyproject.toml parsing.")
                except (FileNotFoundError, PermissionError) as e:
                    console.print(f"[yellow]Warning:[/yellow] Could not access pyproject.toml: {str(e)}")
                except Exception as e:
                    # Catching Exception here is acceptable if we print/log the specific parsing error
                    console.print(f"[yellow]Warning:[/yellow] Could not parse pyproject.toml: {str(e)}")

            return result
            
        except Exception as e:
            raise ScannerError(f"Dependency scan failed: {str(e)}")
