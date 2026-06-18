from typing import List, Dict
from dataclasses import dataclass, field
import threading
from ...utils.console import console

@dataclass
class DiagnosticMessage:
    component: str
    message: str
    severity: str = "WARNING"

class DiagnosticsContext:
    """
    Aggregates non-fatal errors, warnings, and parser failures across the repository.
    Ensures the CLI does not silently drop data or crash abruptly.
    """
    _instance = None
    _lock = threading.Lock()

    def __new__(cls):
        with cls._lock:
            if cls._instance is None:
                cls._instance = super(DiagnosticsContext, cls).__new__(cls)
                cls._instance._messages = []
                cls._instance._msg_lock = threading.Lock()
        return cls._instance

    def add_warning(self, component: str, message: str) -> None:
        with self._msg_lock:
            self._messages.append(DiagnosticMessage(component, message, "WARNING"))

    def add_error(self, component: str, message: str) -> None:
        with self._msg_lock:
            self._messages.append(DiagnosticMessage(component, message, "ERROR"))

    def has_errors(self) -> bool:
        with self._msg_lock:
            return any(m.severity == "ERROR" for m in self._messages)

    def report(self) -> None:
        """Prints all collected diagnostics to the console."""
        with self._msg_lock:
            if not self._messages:
                return

            console.print("\n[bold]Diagnostic Report:[/bold]")
            for msg in self._messages:
                if msg.severity == "ERROR":
                    console.print(f"[red][{msg.component}] ERROR:[/red] {msg.message}")
                else:
                    console.print(f"[yellow][{msg.component}] WARNING:[/yellow] {msg.message}")

    def clear(self) -> None:
        with self._msg_lock:
            self._messages.clear()
