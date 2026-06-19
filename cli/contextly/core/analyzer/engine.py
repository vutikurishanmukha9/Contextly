from pathlib import Path
import hashlib
from importlib.metadata import PackageNotFoundError, version

from ...scanners.registry import ScannerRegistry
from ...types.models import (
    LanguageScanResult, DependencyScanResult, FrameworkScanResult, 
    PatternScanResult, ArchitectureKnowledge, Discovery
)
from ...core.graph.builder import ImportGraphBuilder
from ...types.models import RepositoryIntelligence, RepositoryKnowledge, TechnologyKnowledge, KnowledgeGraph
from datetime import datetime, timezone
from ...core.memory.engine import MemoryEngine
from ...core.initializer.engine import InitEngine
from ...utils.exceptions import ContextlyError

class AnalyzerEngine:
    def __init__(self, root_dir: Path, no_default_excludes: bool = False):
        self.root_dir = root_dir
        self.no_default_excludes = no_default_excludes
        
        from ...utils.config import load_config_model
        self.config = load_config_model(root_dir)
        
    def analyze(self, model: str = "chatgpt") -> RepositoryIntelligence:
        """
        Orchestrates all scanners and generates PROJECT_CONTEXT.md.
        Returns the generated RepositoryIntelligence object.
        """
        from ...core.diagnostics import DiagnosticsContext
        DiagnosticsContext().clear()
        
        from ...utils.walker import RepoWalker
        from ...utils.ignore import IgnoreEngine
        import os

        analyzer_depth = self.config.depth_limits.analyzer
        
        # 1. Single unified walk of the repository to discover all valid files
        # We use a depth of 6 and the standard exclusion list for maximum coverage
        from ...utils.constants import ALWAYS_SKIP_DIRS, SECURITY_CRITICAL_NAMES, SENSITIVE_DIRS
        
        ignorer = IgnoreEngine(self.root_dir, no_default_excludes=self.no_default_excludes)
        
        def dir_skip_predicate(path: Path) -> bool:
            name = path.name.lower()
            if name in SENSITIVE_DIRS or name == ".git" or name == ".contextly":
                return True
            if not self.no_default_excludes and name in ALWAYS_SKIP_DIRS:
                return True
            return ignorer.is_ignored(path)

        def file_skip_predicate(path: Path) -> bool:
            name = path.name.lower()
            # Basename heuristics: substring, suffix, and exact-match
            if ".env" in name or name in SECURITY_CRITICAL_NAMES or name.endswith(".key") or name.endswith(".pem"):
                return True
            if not self.no_default_excludes and name.endswith(".egg-info"):
                return True
            return ignorer.is_ignored(path)
            
        walker = RepoWalker(
            self.root_dir, 
            max_depth=analyzer_depth,
            skip_predicate=file_skip_predicate,
            dir_skip_predicate=dir_skip_predicate
        )
        def file_generator():
            for dirpath, _, filenames in walker.walk():
                rel_path = Path(dirpath).relative_to(self.root_dir)
                for filename in filenames:
                    yield (rel_path / filename).as_posix()

        from itertools import islice
        def get_chunks(iterable, size):
            it = iter(iterable)
            while True:
                chunk = list(islice(it, size))
                if not chunk:
                    break
                yield chunk
                
        all_files = []
        
        # Gather all files from generator
        for chunk in get_chunks(file_generator(), 1000):
            all_files.extend(chunk)
        
        # Sort for deterministic hashing across OS/filesystem variations
        all_files.sort()
        
        hash_obj = hashlib.sha256()
        for f in all_files:
            try:
                with open(self.root_dir / f, "rb") as file_obj:
                    for b in iter(lambda: file_obj.read(4096), b""):
                        hash_obj.update(b)
            except Exception:
                pass
                    
        scan_results = ScannerRegistry.execute_pipeline(self.root_dir, all_files)
        
        lang_data = scan_results.get('language') or LanguageScanResult(primary="Unknown")
        dep_data = scan_results.get('dependencies') or DependencyScanResult()
        fw_data = scan_results.get('frameworks') or FrameworkScanResult()
        pat_data = scan_results.get('patterns') or PatternScanResult()
        arch_data = scan_results.get('architecture') or ArchitectureKnowledge(
            primary_pattern=Discovery(name="Unknown", confidence=0.0, evidence=[])
        )
        cap_data = scan_results.get('capabilities') or []
        
        memory_engine = MemoryEngine(self.root_dir)
        memory_data = memory_engine.load_memory()
        
        # Build the AST graph
        graph_builder = ImportGraphBuilder(self.root_dir, max_file_size_mb=self.config.packer.max_file_size_mb)
        ast_graph = graph_builder.build(file_paths=all_files)
        
        # Cluster the graph into Domains
        from contextly.core.graph.cluster import DomainClusterer
        clusterer = DomainClusterer()
        domains = clusterer.cluster(ast_graph)
        
        intelligence = RepositoryIntelligence(
            language=lang_data,
            dependencies=dep_data,
            frameworks=fw_data,
            patterns=pat_data,
            memory=memory_data
        )
        
        repository_hash = hash_obj.hexdigest()
        try:
            contextly_version = version("contextly")
        except PackageNotFoundError:
            contextly_version = "unknown"

        import os
        epoch = os.environ.get("SOURCE_DATE_EPOCH")
        if epoch:
            try:
                generated_timestamp = datetime.fromtimestamp(int(epoch), timezone.utc).isoformat()
            except ValueError:
                from ...core.diagnostics import DiagnosticsContext
                DiagnosticsContext().add_warning("AnalyzerEngine", f"Invalid SOURCE_DATE_EPOCH: {epoch}. Falling back to current time.")
                generated_timestamp = datetime.now(timezone.utc).isoformat()
        else:
            generated_timestamp = datetime.now(timezone.utc).isoformat()

        repo_knowledge = RepositoryKnowledge(
            repository_hash=repository_hash,
            generated_at=generated_timestamp,
            contextly_version=contextly_version,
            technologies=TechnologyKnowledge(
                frameworks=fw_data.frontend + fw_data.backend,
                languages=[lang_data.primary] + list(lang_data.breakdown.keys()),
                libraries=dep_data.npm + dep_data.python
            ),
            architecture=arch_data,
            capabilities=cap_data,
            domains=domains,
            graph=ast_graph
        )
        
        contextly_dir = self.root_dir / ".contextly"
        if not contextly_dir.exists():
            InitEngine(self.root_dir).initialize()
            
        from ...utils.io import atomic_write
        atomic_write(contextly_dir / "repository.json", repo_knowledge.model_dump_json(indent=2))
        
        from ...generators.registry import GeneratorRegistry
        generator = GeneratorRegistry.get_generator(model, self.root_dir, intelligence)
            
        ctx_content = generator.generate()
        
        output_file = self.root_dir / "PROJECT_CONTEXT.md"
        try:
            # Safe pre-flight write permission check
            if output_file.exists() and not os.access(output_file, os.W_OK):
                raise PermissionError(f"Cannot write to {output_file}")
            if not output_file.exists():
                # Walk up to find the nearest existing ancestor directory
                check_dir = output_file.parent
                while check_dir and not check_dir.exists():
                    check_dir = check_dir.parent
                if check_dir and not os.access(check_dir, os.W_OK):
                    raise PermissionError(f"Cannot write to directory {check_dir}")
            from ...utils.io import atomic_write
            atomic_write(output_file, ctx_content)
        except Exception as e:
            raise ContextlyError(f"Failed to write PROJECT_CONTEXT.md: {e}") from e
            
        from ...core.diagnostics import DiagnosticsContext
        DiagnosticsContext().report()
            
        return intelligence
