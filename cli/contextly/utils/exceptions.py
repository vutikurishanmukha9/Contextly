class ContextlyError(Exception):
    """Base exception for all Context-Ly errors."""
    pass

class ValidationError(ContextlyError):
    """Raised when user input or directory state is invalid."""
    pass

class ScannerError(ContextlyError):
    """Raised when an intelligence scanner fails to process the repository."""
    pass

class MemoryVaultError(ContextlyError):
    """Raised when the team memory vault cannot be accessed or parsed."""
    pass

class ConfigurationError(ContextlyError):
    """Raised when the Context-Ly configuration is invalid or missing."""
    pass
