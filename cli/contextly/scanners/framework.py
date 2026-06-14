from pathlib import Path
from .base import BaseScanner, ScannerError
from ..types.models import DependencyScanResult, FrameworkScanResult

class FrameworkScanner(BaseScanner):
    @property
    def name(self) -> str:
        return "Framework Scanner"

    def scan(self, root_dir: Path, **kwargs) -> FrameworkScanResult:
        try:
            deps: DependencyScanResult = kwargs.get("deps", DependencyScanResult())
            
            frontends = []
            backends = []
            
            # Frontend
            if "next" in deps.npm:
                frontends.append("Next.js")
            if "react" in deps.npm:
                frontends.append("React (SPA)")
            if "vue" in deps.npm:
                frontends.append("Vue.js")
            if "nuxt" in deps.npm:
                frontends.append("Nuxt.js")
            if "svelte" in deps.npm:
                frontends.append("SvelteKit")
                
            # Backend (Node)
            if "express" in deps.npm:
                backends.append("Express.js")
            if "nestjs" in deps.npm or "@nestjs/core" in deps.npm:
                backends.append("NestJS")
                
            # Backend (Python)
            if "fastapi" in deps.python:
                backends.append("FastAPI")
            if "django" in deps.python:
                backends.append("Django")
            if "flask" in deps.python:
                backends.append("Flask")
                
            # Python CLI
            if "typer" in deps.python or "click" in deps.python:
                backends.append("Python CLI")
                
            return FrameworkScanResult(
                frontend=frontends,
                backend=backends
            )
        except Exception as e:
            raise ScannerError(f"Framework scan failed: {str(e)}")
