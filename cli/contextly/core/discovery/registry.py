from typing import Dict, List
from .rules.base import BaseRule
from .rules.path import PathRegexRule

class Registry:
    """
    Decoupled configuration mapping capabilities and architectural paradigms
    to their composite Rule definitions. This allows the discovery logic to be 
    easily scaled, mocked, and maintained independently of the execution engine.
    """
    
    CAPABILITIES: Dict[str, List[BaseRule]] = {
        "Authentication": [
            PathRegexRule(r'\b(auth|login|register|signup|session|jwt|oauth|password)\b', 0.8),
            PathRegexRule(r'auth[-_]?(service|manager|usecase|controller)', 0.5)
        ],
        "Payments": [
            PathRegexRule(r'\b(payment|stripe|billing|checkout|invoice|subscription)\b', 0.8),
            PathRegexRule(r'payment[-_]?(service|gateway)', 0.5)
        ],
        "Users": [
            PathRegexRule(r'\b(user|profile|account|avatar)\b', 0.8)
        ],
        "Notifications": [
            PathRegexRule(r'\b(notification|email|sms|alert|push)\b', 0.8)
        ]
    }

    ARCHITECTURE_PATTERNS: Dict[str, List[BaseRule]] = {
        "Feature-Based": [
            PathRegexRule(r'\b(features|modules|domains)\b', 0.6)
        ],
        "MVC": [
            PathRegexRule(r'\b(controllers)\b', 0.3),
            PathRegexRule(r'\b(views)\b', 0.3),
            PathRegexRule(r'\b(models)\b', 0.2)
        ],
        "Layered": [
            PathRegexRule(r'\b(services)\b', 0.3),
            PathRegexRule(r'\b(repositories)\b', 0.3),
            PathRegexRule(r'\b(core|infrastructure)\b', 0.2)
        ]
    }
    
    ARCHITECTURE_LAYERS: Dict[str, List[BaseRule]] = {
        "Service Layer": [
            PathRegexRule(r'\b(services)\b', 0.9)
        ],
        "Repository Layer": [
            PathRegexRule(r'\b(repositories)\b', 0.9)
        ],
        "Controller Layer": [
            PathRegexRule(r'\b(controllers)\b', 0.9)
        ]
    }
