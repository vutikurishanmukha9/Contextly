import json
import os
import re
from pathlib import Path
from typing import Optional, List
from .base import BaseScanner, ScannerError
from ..types.models import DependencyScanResult
from ..utils.console import console

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
            result = DependencyScanResult()

            if file_paths is not None:
                for rel in file_paths:
                    filename = Path(rel).name
                    if filename == "package.json":
                        self._parse_package_json(root_dir / rel, root_dir, result)
                    elif filename == "requirements.txt":
                        self._parse_requirements_txt(root_dir / rel, root_dir, result)
                    elif filename == "Pipfile":
                        self._parse_pipfile(root_dir / rel, root_dir, result)
                    elif filename == "pyproject.toml":
                        self._parse_pyproject_toml(root_dir / rel, root_dir, result)
            else:
                walker = RepoWalker(root_dir, max_depth=3, skip_predicate=is_skippable)

                for dirpath, dirnames, filenames in walker.walk():
                    current = Path(dirpath)

                    if "package.json" in filenames:
                        self._parse_package_json(current / "package.json", root_dir, result)

                    if "requirements.txt" in filenames:
                        self._parse_requirements_txt(current / "requirements.txt", root_dir, result)

                    if "Pipfile" in filenames:
                        self._parse_pipfile(current / "Pipfile", root_dir, result)

                    if "pyproject.toml" in filenames:
                        self._parse_pyproject_toml(current / "pyproject.toml", root_dir, result)

            return result

        except Exception as e:
            raise ScannerError(f"Dependency scan failed: {str(e)}")

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    def _parse_package_json(self, filepath: Path, root_dir: Path, result: DependencyScanResult):
        try:
            with open(filepath, 'r', encoding="utf-8") as f:
                data = json.load(f)
                if isinstance(data, dict):
                    deps_dict = data.get("dependencies") or {}
                    dev_deps_dict = data.get("devDependencies") or {}
                    deps = list(deps_dict.keys()) + list(dev_deps_dict.keys())
                    for d in deps:
                        if d not in result.npm:
                            result.npm.append(d)
        except (FileNotFoundError, json.JSONDecodeError, PermissionError) as e:
            try:
                rel = filepath.relative_to(root_dir)
            except ValueError:
                rel = filepath
            console.print(f"[yellow]Warning:[/yellow] Could not parse {rel}: {str(e)}")
        except Exception as e:
            try:
                rel = filepath.relative_to(root_dir)
            except ValueError:
                rel = filepath
            console.print(f"[yellow]Warning:[/yellow] Unexpected error reading {rel}: {str(e)}")

    def _parse_requirements_txt(self, filepath: Path, root_dir: Path, result: DependencyScanResult):
        try:
            with open(filepath, 'r', encoding="utf-8") as f:
                for line in f:
                    stripped = line.strip()
                    if stripped and not stripped.startswith("#") and not stripped.startswith("-"):
                        clean_dep = stripped.split(';')[0].split('[')[0].strip()
                        dep = re.split(r'[=<>~!]', clean_dep)[0].strip()
                        if dep and dep not in result.python:
                            result.python.append(dep)
        except (FileNotFoundError, PermissionError, UnicodeDecodeError) as e:
            console.print(f"[yellow]Warning:[/yellow] Could not parse requirements.txt: {str(e)}")
        except Exception as e:
            console.print(f"[yellow]Warning:[/yellow] Unexpected error reading requirements.txt: {str(e)}")

    def _parse_pyproject_toml(self, filepath: Path, root_dir: Path, result: DependencyScanResult):
        try:
            with open(filepath, 'rb') as f:
                if tomllib is not None:
                    data = tomllib.load(f)
                    project = data.get("project")
                    if isinstance(project, dict):
                        # Extract standard [project.dependencies]
                        deps = project.get("dependencies", [])
                        if isinstance(deps, list):
                            for dep in deps:
                                if isinstance(dep, str):
                                    clean_dep = dep.split(';')[0].split('[')[0].strip()
                                    clean_dep = re.split(r'[=<>~!]', clean_dep)[0].strip()
                                    if clean_dep and clean_dep not in result.python:
                                        result.python.append(clean_dep)
                                        
                        # Also extract [project.optional-dependencies]
                        opt_deps = project.get("optional-dependencies", {})
                        if isinstance(opt_deps, dict):
                            for group_deps in opt_deps.values():
                                if isinstance(group_deps, list):
                                    for dep in group_deps:
                                        if isinstance(dep, str):
                                            clean_dep = dep.split(';')[0].split('[')[0].strip()
                                            clean_dep = re.split(r'[=<>~!]', clean_dep)[0].strip()
                                            if clean_dep and clean_dep not in result.python:
                                                result.python.append(clean_dep)
                                                
                    # Also extract Poetry dependencies
                    tool = data.get("tool")
                    if isinstance(tool, dict):
                        poetry = tool.get("poetry")
                        if isinstance(poetry, dict):
                            poetry_deps = poetry.get("dependencies", {})
                            if isinstance(poetry_deps, dict):
                                for dep in poetry_deps.keys():
                                    if dep != "python" and dep not in result.python:
                                        result.python.append(dep)
                else:
                    raise ScannerError("`tomllib` (or `tomli`) is not installed. Required for pyproject.toml parsing.")
        except ScannerError:
            raise
        except (FileNotFoundError, PermissionError) as e:
            console.print(f"[yellow]Warning:[/yellow] Could not access pyproject.toml: {str(e)}")
        except Exception as e:
            console.print(f"[yellow]Warning:[/yellow] Could not parse pyproject.toml: {str(e)}")

    def _parse_pipfile(self, filepath: Path, root_dir: Path, result: DependencyScanResult):
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
                            if dep not in result.python:
                                result.python.append(dep)
        except (FileNotFoundError, PermissionError, UnicodeDecodeError) as e:
            console.print(f"[yellow]Warning:[/yellow] Could not parse Pipfile: {str(e)}")
        except Exception as e:
            console.print(f"[yellow]Warning:[/yellow] Unexpected error reading Pipfile: {str(e)}")
