import pytest
from pathlib import Path
from contextly.scanners.framework import FrameworkScanner
from contextly.types.models import DependencyScanResult

def test_framework_scanner_edge_cases(tmp_path):
    """Covers framework.py multiple lines."""
    s = FrameworkScanner()
    assert s.name == "Framework Scanner"
    
    deps = DependencyScanResult()
    deps.npm.extend(["next", "vue", "nuxt", "react", "angular", "svelte", "gatsby", "express", "@nestjs/core", "koa", "fastify"])
    deps.python.extend(["fastapi", "spring-boot-starter-web", "gin", "echo", "fiber", "rails", "sinatra", "laravel", "actix-web"])
    
    res = s.scan(tmp_path, deps=deps)
    assert "Next.js" in res.frontend
    assert "FastAPI" in res.backend
    
    deps_dj = DependencyScanResult()
    deps_dj.python.append("django")
    res_dj = s.scan(tmp_path, deps=deps_dj)
    assert "Django" in res_dj.backend
    
    # Test fallback
    deps2 = DependencyScanResult()
    deps2.npm.extend(["express", "spring-boot-starter-web"])
    res2 = s.scan(tmp_path, deps=deps2)
    assert "Express.js" in res2.backend

def test_framework_scanner_missing_branches(tmp_path):
    """Covers framework.py 23, 25, 27, 33, 45-46, 52-53."""
    s = FrameworkScanner()
    deps = DependencyScanResult()
    # 23, 25, 27, 33: react/vue with no explicit web framework
    deps.npm.extend(["react", "vue", "svelte", "angular"])
    # 45-46, 52-53: various python frameworks
    deps.python.extend(["flask", "fastapi"])
    res = s.scan(tmp_path, deps=deps)
    assert "React (SPA)" in res.frontend or "Vue.js" in res.frontend
    assert "FastAPI" in res.backend or "Flask" in res.backend
