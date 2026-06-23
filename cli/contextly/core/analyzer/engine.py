from pathlib import Path
import hashlib
import os
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
from ...core.diagnostics import DiagnosticsContext

class AnalyzerEngine:
    def __init__(self, root_dir: Path, no_default_excludes: bool = False):
        self.root_dir = root_dir
        self.no_default_excludes = no_default_excludes
        
        from ...utils.config import load_config_model
        self.config = load_config_model(root_dir)

    def _collect_files(self) -> list:
        """
        Walks the repository and returns a sorted list of relative file paths.
        Applies ignore rules, security filters, and depth limits.
        """
        from ...utils.walker import RepoWalker
        from ...utils.ignore import IgnoreEngine
        from ...utils.constants import ALWAYS_SKIP_DIRS, is_security_critical_dir, is_security_critical_file

        analyzer_depth = self.config.depth_limits.analyzer
        ignorer = IgnoreEngine(self.root_dir, no_default_excludes=self.no_default_excludes)

        def dir_skip_predicate(path: Path) -> bool:
            name = path.name.lower()
            if is_security_critical_dir(name):
                return True
            if not self.no_default_excludes and name in ALWAYS_SKIP_DIRS:
                return True
            return ignorer.is_ignored(path)

        def file_skip_predicate(path: Path) -> bool:
            name = path.name.lower()
            if is_security_critical_file(name):
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

        all_files = [
            (Path(dirpath).relative_to(self.root_dir) / filename).as_posix()
            for dirpath, _, filenames in walker.walk()
            for filename in filenames
        ]

        # Sort for deterministic hashing across OS/filesystem variations
        all_files.sort()
        return all_files

    def _compute_hash(self, all_files: list) -> str:
        """
        Computes a SHA-256 hash using file metadata (path, size, mtime) to 
        minimize TOCTOU race conditions and drastically improve performance.
        """
        import concurrent.futures
        
        def _get_metadata(f: str) -> str:
            try:
                abs_path = self.root_dir / f
                stat = abs_path.stat()
                return f"{f}|{stat.st_size}|{stat.st_mtime}"
            except OSError as e:
                DiagnosticsContext().add_warning(
                    "AnalyzerEngine",
                    f"Cannot hash metadata for {f}: {type(e).__name__} - {e}"
                )
                return ""
                
        metadata_list = []
        optimal_workers = min(32, (os.cpu_count() or 1) * 4)
        with concurrent.futures.ThreadPoolExecutor(max_workers=optimal_workers) as executor:
            # Map retains the original order of all_files for deterministic hashing
            for metadata in executor.map(_get_metadata, all_files):
                if metadata:
                    metadata_list.append(metadata)
                    
        hash_obj = hashlib.sha256()
        for metadata in metadata_list:
            hash_obj.update(metadata.encode("utf-8"))
            
        return hash_obj.hexdigest()

    def _write_outputs(self, repo_knowledge: RepositoryKnowledge, intelligence: RepositoryIntelligence, model: str) -> None:
        """
        Writes repository.json and PROJECT_CONTEXT.md to disk.
        Uses atomic_write to prevent partial file corruption.
        """
        from ...utils.io import atomic_write
        from ...generators.registry import GeneratorRegistry

        contextly_dir = self.root_dir / ".contextly"
        if not contextly_dir.exists():
            InitEngine(self.root_dir).initialize()

        atomic_write(contextly_dir / "repository.json", repo_knowledge.model_dump_json(indent=2))

        from contextly.generators.registry import GeneratorRegistry
        generator = GeneratorRegistry.get_generator(model, self.root_dir, intelligence)
            
        ctx_content = generator.generate()
        
        output_file = self.root_dir / "PROJECT_CONTEXT.md"
        try:
            atomic_write(output_file, ctx_content)
        except Exception as e:
            raise ContextlyError(f"Failed to write PROJECT_CONTEXT.md: {e}") from e
        
    def analyze(self, model: str = "chatgpt") -> RepositoryIntelligence:
        """
        Orchestrates all scanners and generates PROJECT_CONTEXT.md.
        Returns the generated RepositoryIntelligence object.
        """
        DiagnosticsContext().clear()

        # 1. Collect all files
        all_files = self._collect_files()

        # 2. Compute deterministic repository hash
        repository_hash = self._compute_hash(all_files)
        
        # 2.5 Build AST graph and cluster into domains
        from ...utils.console import console
        console.print("[dim]Building architecture graph for deep analysis...[/dim]")
        graph_builder = ImportGraphBuilder(self.root_dir, max_file_size_mb=self.config.packer.max_file_size_mb)
        ast_graph = graph_builder.build(file_paths=all_files)
        
        from contextly.core.graph.cluster import DomainClusterer
        clusterer = DomainClusterer()
        domains = clusterer.cluster(ast_graph)

        # 3. Run scanner pipeline
        scan_results = ScannerRegistry.execute_pipeline(self.root_dir, all_files, ast_graph=ast_graph, domains=domains)
        
        lang_data = scan_results.get('language') or LanguageScanResult(primary="Unknown")
        dep_data = scan_results.get('dependencies') or DependencyScanResult()
        fw_data = scan_results.get('frameworks') or FrameworkScanResult()
        pat_data = scan_results.get('patterns') or PatternScanResult()
        arch_data = scan_results.get('architecture') or ArchitectureKnowledge(
            primary_pattern=Discovery(name="Unknown", confidence=0.0, evidence=[])
        )
        cap_data = scan_results.get('capabilities') or []
        
        # 4. Load team memory
        memory_engine = MemoryEngine(self.root_dir)
        memory_data = memory_engine.load_memory()
        
        # 6. Assemble intelligence object
        intelligence = RepositoryIntelligence(
            language=lang_data,
            dependencies=dep_data,
            frameworks=fw_data,
            patterns=pat_data,
            memory=memory_data
        )
        
        # 7. Build repository knowledge metadata
        try:
            contextly_version = version("contextly")
        except PackageNotFoundError:
            contextly_version = "unknown"

        epoch = os.environ.get("SOURCE_DATE_EPOCH")
        if epoch:
            try:
                generated_timestamp = datetime.fromtimestamp(int(epoch), timezone.utc).isoformat()
            except ValueError:
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
        
        # 8. Write output files
        self._write_outputs(repo_knowledge, intelligence, model)
        
        DiagnosticsContext().report()
            
        return intelligence
