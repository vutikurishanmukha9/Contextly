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
                from ..utils.config import load_config
                config = load_config(root_dir) or {}
                if not isinstance(config, dict):
                    config = {}
                depth_config = config.get("depth_limits") or {}
                if not isinstance(depth_config, dict):
                    depth_config = {}
                scanners_depth = depth_config.get("scanners", 4)
                
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
        except Exception as e:
            raise ScannerError(f"Dependency scan failed: {str(e)}")

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
                raise ScannerError(f"Could not access {rel}: {str(e)}")
        except Exception as e:
            try:
                rel = filepath.relative_to(root_dir)
            except ValueError:
                rel = filepath
            if strict:
                raise ScannerError(f"Failed to parse package.json {rel}: {str(e)}")
            else:
                console.print(f"[yellow]Warning:[/yellow] Failed to parse package.json {rel}: {str(e)}")

    def _parse_requirements_txt(self, filepath: Path, root_dir: Path, python_set: set[str], strict: bool = False):
        try:
            with open(filepath, 'r', encoding="utf-8") as f:
                for line in f:
                    stripped = line.strip()
                    if stripped and not stripped.startswith("#") and not stripped.startswith("-"):
                        clean_dep = stripped.split(';')[0].split('[')[0].strip()
                        dep = re.split(r'[=<>~!]', clean_dep)[0].strip()
                        if dep:
                            python_set.add(dep)
        except (FileNotFoundError, PermissionError, UnicodeDecodeError) as e:
            console.print(f"[yellow]Warning:[/yellow] Could not access requirements.txt: {str(e)}")
            if strict:
                raise ScannerError(f"Could not access requirements.txt: {str(e)}")
        except Exception as e:
            if strict:
                raise ScannerError(f"Failed to parse requirements.txt: {str(e)}")
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
                            for dep in deps:
                                if isinstance(dep, str):
                                    clean_dep = dep.split(';')[0].split('[')[0].strip()
                                    clean_dep = re.split(r'[=<>~!]', clean_dep)[0].strip()
                                    if clean_dep:
                                        python_set.add(clean_dep)
                                        
                        # Also extract [project.optional-dependencies]
                        opt_deps = project.get("optional-dependencies", {})
                        if isinstance(opt_deps, dict):
                            for group_deps in opt_deps.values():
                                if isinstance(group_deps, list):
                                    for dep in group_deps:
                                        if isinstance(dep, str):
                                            clean_dep = dep.split(';')[0].split('[')[0].strip()
                                            clean_dep = re.split(r'[=<>~!]', clean_dep)[0].strip()
                                            if clean_dep:
                                                python_set.add(clean_dep)
                                                
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
                raise ScannerError(f"Could not access pyproject.toml: {str(e)}")
        except Exception as e:
            if strict:
                raise ScannerError(f"Failed to parse pyproject.toml: {str(e)}")
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
                raise ScannerError(f"Could not access Pipfile: {str(e)}")
        except Exception as e:
            if strict:
                raise ScannerError(f"Failed to parse Pipfile: {str(e)}")
            else:
                console.print(f"[yellow]Warning:[/yellow] Failed to parse Pipfile: {str(e)}")
