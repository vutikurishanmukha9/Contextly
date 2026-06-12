from pathlib import Path

from ...scanners.dependencies import DependencyScanner
from ...scanners.language import LanguageScanner
from ...scanners.framework import FrameworkScanner
from ...scanners.patterns import PatternScanner
from ...types.models import RepositoryIntelligence
from ...core.memory.engine import MemoryEngine
from ...generators.claude import ClaudeGenerator
from ...generators.chatgpt import ChatGPTGenerator

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
        
        memory_engine = MemoryEngine(self.root_dir)
        memory_data = memory_engine.load_memory()
        
        intelligence = RepositoryIntelligence(
            language=lang_data,
            dependencies=dep_data,
            frameworks=fw_data,
            patterns=pat_data,
            memory=memory_data
        )
        
        if model.lower() == "claude":
            generator = ClaudeGenerator(self.root_dir, intelligence)
        else:
            generator = ChatGPTGenerator(self.root_dir, intelligence)
            
        ctx_content = generator.generate()
        
        output_file = self.root_dir / "PROJECT_CONTEXT.md"
        with open(output_file, "w", encoding="utf-8") as f:
            f.write(ctx_content)
            
        return intelligence
