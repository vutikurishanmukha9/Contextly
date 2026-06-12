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
            
            framework = "None detected"
            backend = "None detected"
            
            # Frontend
            if "next" in deps.npm:
                framework = "Next.js"
            elif "react" in deps.npm:
                framework = "React (SPA)"
            elif "vue" in deps.npm:
                framework = "Vue.js"
            elif "nuxt" in deps.npm:
                framework = "Nuxt.js"
            elif "svelte" in deps.npm:
                framework = "SvelteKit"
                
            # Backend (Node)
            if "express" in deps.npm:
                backend = "Express.js"
            elif "nestjs" in deps.npm or "@nestjs/core" in deps.npm:
                backend = "NestJS"
                
            # Backend (Python)
            if "fastapi" in deps.python:
                backend = "FastAPI"
            elif "django" in deps.python:
                backend = "Django"
            elif "flask" in deps.python:
                backend = "Flask"
                
            # Python CLI
            if "typer" in deps.python or "click" in deps.python:
                if backend == "None detected":
                    backend = "Python CLI"
                
            return FrameworkScanResult(
                frontend=framework,
                backend=backend
            )
        except Exception as e:
            raise ScannerError(f"Framework scan failed: {str(e)}")
