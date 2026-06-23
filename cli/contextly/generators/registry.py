from typing import Dict, Type
from pathlib import Path
from .base import BaseGenerator
from .claude import ClaudeGenerator
from .chatgpt import ChatGPTGenerator
from ..types.models import RepositoryIntelligence

class GeneratorRegistry:
    """
    Registry for Context Generators.
    Decouples LLM-specific formatting logic from the core analyzer engine.
    """
    _registry: Dict[str, Type[BaseGenerator]] = {}

    @classmethod
    def register(cls, model_name: str, generator_class: Type[BaseGenerator]) -> None:
        cls._registry[model_name.lower()] = generator_class

    @classmethod
    def register_defaults(cls) -> None:
        cls.register('claude', ClaudeGenerator)
        cls.register('chatgpt', ChatGPTGenerator)

    @classmethod
    def get_generator(cls, model_name: str, root_dir: Path, intelligence: RepositoryIntelligence) -> BaseGenerator:
        model = model_name.lower()
        if model not in cls._registry:
            from ..core.diagnostics import DiagnosticsContext
            DiagnosticsContext().add_warning(f"Unknown model '{model_name}', defaulting to chatgpt format")
            
        # Fallback to chatgpt if model is not registered
        generator_class = cls._registry.get(model, cls._registry.get('chatgpt'))
        if not generator_class:
            raise ValueError(f"No generator found for {model_name} and no fallback available.")
            
        return generator_class(root_dir, intelligence)

# Auto-register defaults
GeneratorRegistry.register_defaults()
