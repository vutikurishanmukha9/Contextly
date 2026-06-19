import json
import os
import re
from pathlib import Path
from typing import Optional, List
from .base import BaseScanner, ScannerError
from ..types.models import DependencyScanResult
from ..utils.console import console

# PEP 508-compliant patterns to skip non-package lines
_URL_PREFIXES = ("git+", "http://", "https://", "svn+", "hg+")
_SKIP_LINE_PREFIXES = ("-e", "-r", "-c", "-f", "--")


def _extract_dep_name(raw: str) -> Optional[str]:
    """
    Extracts a normalized package name from a PEP 508 dependency string.
    Handles version constraints, extras, environment markers, and URL specifications.
    Returns None for lines that are not valid package references.
    """
    stripped = raw.strip()
    if not stripped or stripped.startswith("#"):
        return None

    # Skip pip flags and editable installs
    if any(stripped.lower().startswith(p) for p in _SKIP_LINE_PREFIXES):
        return None

    # Skip direct URL references (PEP 440 direct references, VCS URIs)
    if any(stripped.startswith(p) for p in _URL_PREFIXES):
        return None

    # Handle PEP 508 URL specs: "requests @ https://..."
    if " @ " in stripped:
        name_part = stripped.split(" @ ")[0].strip()
        # Strip extras from the name part
        name_part = name_part.split("[")[0].strip()
        return name_part if name_part else None

    # Try spec-compliant parsing first
    try:
        from packaging.requirements import Requirement
        req = Requirement(stripped)
        return req.name
    except Exception:
        pass

    # Fallback: strip environment markers, extras, and version constraints
    clean = stripped.split(";")[0].split("[")[0].strip()
    dep = re.split(r'[=<>~!]', clean)[0].strip()
    return dep if dep else None

try:
    import tomllib
except ImportError:
    try:
        import tomli as tomllib
    except ImportError:
        tomllib = None

from ..utils.walker import RepoWalker
from ..utils.constants import is_skippable

class DependencyScanner(BaseScanner):
    @property
    def name(self) -> str:
        return "Dependency Scanner"

    def scan(self, root_dir: Path, file_paths: Optional[List[str]] = None, **kwargs) -> DependencyScanResult:
        try:
            npm_set: set[str] = set()
            python_set: set[str] = set()
            strict = kwargs.get("strict", False)

            if file_paths is not None:
                for rel in file_paths:
                    filename = Path(rel).name
                    if filename == "package.json":
                        self._parse_package_json(root_dir / rel, root_dir, npm_set, strict=strict)
                    elif filename == "requirements.txt":
                        self._parse_requirements_txt(root_dir / rel, root_dir, python_set, strict=strict)
                    elif filename == "Pipfile":
                        self._parse_pipfile(root_dir / rel, root_dir, python_set, strict=strict)
                    elif filename == "pyproject.toml":
                        self._parse_pyproject_toml(root_dir / rel, root_dir, python_set, strict=strict)
            else:
                from ..utils.config import load_config_model
                config = load_config_model(root_dir)
                scanners_depth = config.depth_limits.scanners
                
                walker = RepoWalker(root_dir, max_depth=scanners_depth, skip_predicate=is_skippable)

                for dirpath, dirnames, filenames in walker.walk():
                    current = Path(dirpath)

                    if "package.json" in filenames:
                        self._parse_package_json(current / "package.json", root_dir, npm_set, strict=strict)

                    if "requirements.txt" in filenames:
                        self._parse_requirements_txt(current / "requirements.txt", root_dir, python_set, strict=strict)

                    if "Pipfile" in filenames:
                        self._parse_pipfile(current / "Pipfile", root_dir, python_set, strict=strict)

                    if "pyproject.toml" in filenames:
                        self._parse_pyproject_toml(current / "pyproject.toml", root_dir, python_set, strict=strict)

            result = DependencyScanResult()
            result.npm = sorted(list(npm_set))
            result.python = sorted(list(python_set))
            return result
        except ScannerError:
            raise
        except Exception as e:
            raise ScannerError(f"Dependency scan failed: {str(e)}") from e

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    def _parse_package_json(self, filepath: Path, root_dir: Path, npm_set: set[str], strict: bool = False):
        try:
            with open(filepath, 'r', encoding="utf-8") as f:
                data = json.load(f)
                if isinstance(data, dict):
                    deps_dict = data.get("dependencies") or {}
                    dev_deps_dict = data.get("devDependencies") or {}
                    deps = list(deps_dict.keys()) + list(dev_deps_dict.keys())
                    npm_set.update(deps)
        except (FileNotFoundError, PermissionError) as e:
            try:
                rel = filepath.relative_to(root_dir)
            except ValueError:
                rel = filepath
            console.print(f"[yellow]Warning:[/yellow] Could not access {rel}: {str(e)}")
            if strict:
                raise ScannerError(f"Could not access {rel}: {str(e)}") from e
        except Exception as e:
            try:
                rel = filepath.relative_to(root_dir)
            except ValueError:
                rel = filepath
            if strict:
                raise ScannerError(f"Failed to parse package.json {rel}: {str(e)}") from e
            else:
                console.print(f"[yellow]Warning:[/yellow] Failed to parse package.json {rel}: {str(e)}")

    def _parse_requirements_txt(self, filepath: Path, root_dir: Path, python_set: set[str], strict: bool = False):
        try:
            with open(filepath, 'r', encoding="utf-8") as f:
                for line in f:
                    dep = _extract_dep_name(line)
                    if dep:
                        python_set.add(dep)
        except (FileNotFoundError, PermissionError, UnicodeDecodeError) as e:
            console.print(f"[yellow]Warning:[/yellow] Could not access requirements.txt: {str(e)}")
            if strict:
                raise ScannerError(f"Could not access requirements.txt: {str(e)}") from e
        except Exception as e:
            if strict:
                raise ScannerError(f"Failed to parse requirements.txt: {str(e)}") from e
            else:
                console.print(f"[yellow]Warning:[/yellow] Failed to parse requirements.txt: {str(e)}")

    def _parse_pyproject_toml(self, filepath: Path, root_dir: Path, python_set: set[str], strict: bool = False):
        try:
            with open(filepath, 'rb') as f:
                if tomllib is not None:
                    data = tomllib.load(f)
                    project = data.get("project")
                    if isinstance(project, dict):
                        # Extract standard [project.dependencies]
                        deps = project.get("dependencies", [])
                        if isinstance(deps, list):
                            for dep_str in deps:
                                if isinstance(dep_str, str):
                                    name = _extract_dep_name(dep_str)
                                    if name:
                                        python_set.add(name)
                                        
                        # Also extract [project.optional-dependencies]
                        opt_deps = project.get("optional-dependencies", {})
                        if isinstance(opt_deps, dict):
                            for group_deps in opt_deps.values():
                                if isinstance(group_deps, list):
                                    for dep_str in group_deps:
                                        if isinstance(dep_str, str):
                                            name = _extract_dep_name(dep_str)
                                            if name:
                                                python_set.add(name)
                                                
                    # Also extract Poetry dependencies
                    tool = data.get("tool")
                    if isinstance(tool, dict):
                        poetry = tool.get("poetry")
                        if isinstance(poetry, dict):
                            poetry_deps = poetry.get("dependencies", {})
                            if isinstance(poetry_deps, dict):
                                for dep in poetry_deps.keys():
                                    if dep != "python":
                                        python_set.add(dep)
                else:
                    raise ScannerError("`tomllib` (or `tomli`) is not installed. Required for pyproject.toml parsing. Please run: pip install tomli")
        except ScannerError:
            raise
        except (FileNotFoundError, PermissionError) as e:
            console.print(f"[yellow]Warning:[/yellow] Could not access pyproject.toml: {str(e)}")
            if strict:
                raise ScannerError(f"Could not access pyproject.toml: {str(e)}") from e
        except Exception as e:
            if strict:
                raise ScannerError(f"Failed to parse pyproject.toml: {str(e)}") from e
            else:
                console.print(f"[yellow]Warning:[/yellow] Failed to parse pyproject.toml: {str(e)}")

    def _parse_pipfile(self, filepath: Path, root_dir: Path, python_set: set[str], strict: bool = False):
        try:
            with open(filepath, 'r', encoding="utf-8") as f:
                in_packages = False
                for line in f:
                    stripped = line.strip()
                    if stripped.startswith("[packages]") or stripped.startswith("[dev-packages]"):
                        in_packages = True
                        continue
                    elif stripped.startswith("["):
                        in_packages = False
                        continue
                        
                    if in_packages and "=" in stripped:
                        dep = stripped.split("=")[0].strip().strip('"').strip("'")
                        if dep and not dep.startswith("#"):
                            python_set.add(dep)
        except (FileNotFoundError, PermissionError, UnicodeDecodeError) as e:
            console.print(f"[yellow]Warning:[/yellow] Could not access Pipfile: {str(e)}")
            if strict:
                raise ScannerError(f"Could not access Pipfile: {str(e)}") from e
        except Exception as e:
            if strict:
                raise ScannerError(f"Failed to parse Pipfile: {str(e)}") from e
            else:
                console.print(f"[yellow]Warning:[/yellow] Failed to parse Pipfile: {str(e)}")
