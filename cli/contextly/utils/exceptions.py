class ContextlyError(Exception):
    """Base exception for all Context-Ly errors."""
    pass

class ValidationError(ContextlyError):
    """Raised when user input or directory state is invalid."""
    pass

class ScannerError(ContextlyError):
    """Raised when an intelligence scanner fails to process the repository."""
    pass

class ContextGenerationError(ContextlyError):
    """Raised when the LLM context cannot be generated or formatted."""
    pass

class MemoryError(ContextlyError):
    """Raised when the team memory vault cannot be accessed or parsed."""
    pass
