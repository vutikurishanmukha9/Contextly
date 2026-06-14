from pathlib import Path

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
        lang_scanner = LanguageScanner()
        dep_scanner = DependencyScanner()
        fw_scanner = FrameworkScanner()
        pat_scanner = PatternScanner()
        
        lang_data = lang_scanner.scan(self.root_dir)
        dep_data = dep_scanner.scan(self.root_dir)
        fw_data = fw_scanner.scan(self.root_dir, deps=dep_data)
        pat_data = pat_scanner.scan(self.root_dir, dependencies=dep_data)
        
        arch_scanner = ArchitectureScanner()
        cap_scanner = CapabilityDetector()
        
        arch_data = arch_scanner.scan(self.root_dir)
        cap_data = cap_scanner.scan(self.root_dir)
        
        memory_engine = MemoryEngine(self.root_dir)
        memory_data = memory_engine.load_memory()
        
        # Build the AST graph
        graph_builder = ImportGraphBuilder(self.root_dir)
        ast_graph = graph_builder.build()
        
        intelligence = RepositoryIntelligence(
            language=lang_data,
            dependencies=dep_data,
            frameworks=fw_data,
            patterns=pat_data,
            memory=memory_data
        )
        
        repo_knowledge = RepositoryKnowledge(
            repository_hash="pending", # To be implemented
            generated_at=datetime.now(timezone.utc).isoformat(),
            contextly_version="0.1.0",
            technologies=TechnologyKnowledge(
                frameworks=fw_data.frontend + fw_data.backend,
                languages=[lang_data.primary] + list(lang_data.breakdown.keys()),
                libraries=dep_data.npm + dep_data.python
            ),
            architecture=arch_data,
            capabilities=cap_data,
            domains=[], # To be implemented later based on graph boundaries
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
