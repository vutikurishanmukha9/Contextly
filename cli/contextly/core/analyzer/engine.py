from pathlib import Path
import hashlib
from importlib.metadata import PackageNotFoundError, version

from ...scanners.dependencies import DependencyScanner
from ...scanners.language import LanguageScanner
from ...scanners.framework import FrameworkScanner
from ...scanners.patterns import PatternScanner
from ...scanners.architecture import ArchitectureScanner
from ...scanners.capabilities import CapabilityDetector
from ...core.graph.builder import ImportGraphBuilder
from ...types.models import RepositoryIntelligence, RepositoryKnowledge, TechnologyKnowledge, KnowledgeGraph
from datetime import datetime, timezone
from ...core.memory.engine import MemoryEngine
from ...core.initializer.engine import InitEngine
from ...generators.claude import ClaudeGenerator
from ...generators.chatgpt import ChatGPTGenerator
from ...utils.exceptions import ContextlyError

class AnalyzerEngine:
    def __init__(self, root_dir: Path):
        self.root_dir = root_dir
        
    def analyze(self, model: str = "chatgpt") -> RepositoryIntelligence:
        """
        Orchestrates all scanners and generates PROJECT_CONTEXT.md.
        Returns the generated RepositoryIntelligence object.
        """
        from ...utils.walker import RepoWalker
        import os

        InitEngine(self.root_dir).initialize()
        
        # 1. Single unified walk of the repository to discover all valid files
        # We use a depth of 6 and the standard exclusion list for maximum coverage
        ALWAYS_SKIP = {
            ".git", "node_modules", "venv", ".venv", "__pycache__",
            ".contextly", "dist", "build", ".next", ".tox", ".eggs"
        }
        
        def skip_predicate(path: Path) -> bool:
            name = path.name.lower()
            return name in ALWAYS_SKIP or name.endswith(".egg-info")

        walker = RepoWalker(self.root_dir, max_depth=6, skip_predicate=skip_predicate)
        all_files: list[str] = []
        
        for dirpath, _, filenames in walker.walk():
            rel_path = str(Path(dirpath).relative_to(self.root_dir))
            for filename in filenames:
                full_rel = os.path.join(rel_path, filename).replace("\\", "/")
                if full_rel.startswith("./"):
                    full_rel = full_rel[2:]
                all_files.append(full_rel)
        lang_scanner = LanguageScanner()
        dep_scanner = DependencyScanner()
        fw_scanner = FrameworkScanner()
        pat_scanner = PatternScanner()
        
        lang_data = lang_scanner.scan(self.root_dir, file_paths=all_files)
        dep_data = dep_scanner.scan(self.root_dir, file_paths=all_files)
        fw_data = fw_scanner.scan(self.root_dir, deps=dep_data, file_paths=all_files)
        pat_data = pat_scanner.scan(self.root_dir, dependencies=dep_data, file_paths=all_files)
        
        arch_scanner = ArchitectureScanner()
        cap_scanner = CapabilityDetector()
        
        arch_data = arch_scanner.scan(self.root_dir, file_paths=all_files)
        cap_data = cap_scanner.scan(self.root_dir, file_paths=all_files)
        
        memory_engine = MemoryEngine(self.root_dir)
        memory_data = memory_engine.load_memory()
        
        # Build the AST graph
        graph_builder = ImportGraphBuilder(self.root_dir)
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
        
        hash_input = "\n".join(sorted(all_files)).encode("utf-8")
        repository_hash = hashlib.sha256(hash_input).hexdigest()
        try:
            contextly_version = version("contextly")
        except PackageNotFoundError:
            contextly_version = "unknown"

        repo_knowledge = RepositoryKnowledge(
            repository_hash=repository_hash,
            generated_at=datetime.now(timezone.utc).isoformat(),
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
            contextly_dir.mkdir(parents=True, exist_ok=True)
            
        with open(contextly_dir / "repository.json", "w", encoding="utf-8") as f:
            f.write(repo_knowledge.model_dump_json(indent=2))
        
        if model.lower() == "claude":
            generator = ClaudeGenerator(self.root_dir, intelligence)
        else:
            generator = ChatGPTGenerator(self.root_dir, intelligence)
            
        ctx_content = generator.generate()
        
        output_file = self.root_dir / "PROJECT_CONTEXT.md"
        try:
            with open(output_file, "w", encoding="utf-8") as f:
                f.write(ctx_content)
        except (FileNotFoundError, PermissionError) as e:
            raise ContextlyError(f"Failed to write PROJECT_CONTEXT.md: {e}")
            
        return intelligence
