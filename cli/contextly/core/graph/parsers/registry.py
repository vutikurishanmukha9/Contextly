import threading
from typing import Dict, Type, Optional, Callable
from .base import BaseParser
from .python import PythonASTParser
from .typescript import TypeScriptASTParser

class ParserRegistry:
    """
    Registry for AST Parsers. 
    Thread-safe implementation for dynamically resolving language parsers
    without hardcoding them into the ImportGraphBuilder.
    """
    _registry: Dict[str, Type[BaseParser]] = {}
    _lock = threading.Lock()
    
    # Thread-local storage for instantiated parsers to avoid thread contention during parsing
    _local = threading.local()

    @classmethod
    def register(cls, extension: str, parser_class: Type[BaseParser]) -> None:
        """Registers a parser class for a given file extension."""
        with cls._lock:
            cls._registry[extension.lower()] = parser_class

    @classmethod
    def register_defaults(cls) -> None:
        """Registers default out-of-the-box parsers."""
        cls.register('py', PythonASTParser)
        cls.register('pyw', PythonASTParser)
        cls.register('ts', TypeScriptASTParser)
        cls.register('tsx', TypeScriptASTParser)
        cls.register('js', TypeScriptASTParser)
        cls.register('jsx', TypeScriptASTParser)

    @classmethod
    def get_parser(cls, extension: str) -> Optional[BaseParser]:
        """
        Retrieves a thread-local instance of a parser for the given extension.
        Returns None if no parser is registered.
        """
        ext = extension.lower()
        if not hasattr(cls._local, 'instances'):
            cls._local.instances = {}
            
        if ext in cls._local.instances:
            return cls._local.instances[ext]
            
        with cls._lock:
            parser_class = cls._registry.get(ext)
            
        if parser_class:
            if issubclass(parser_class, TypeScriptASTParser):
                instance = parser_class(extension=ext)
            else:
                instance = parser_class()
            cls._local.instances[ext] = instance
            return instance
            
        return None

    @classmethod
    def supported_extensions(cls) -> set[str]:
        """Returns a set of all currently registered file extensions."""
        with cls._lock:
            return set(cls._registry.keys())

# Auto-register defaults on module load
ParserRegistry.register_defaults()
