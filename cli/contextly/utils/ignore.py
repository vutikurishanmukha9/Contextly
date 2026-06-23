from pathlib import Path
import pathspec
import functools

class IgnoreEngine:
    """Centralized ignore logic for Context-Ly"""
    
    def __init__(self, root_dir: Path, no_default_excludes: bool = False):
        self.root_dir = root_dir.absolute()
        self.root_dir_resolved = root_dir.resolve()
        self.no_default_excludes = no_default_excludes
        
        from .constants import ALWAYS_SKIP_DIRS
        # Hardcoded defaults that should never be scanned
        self.default_ignores = list(ALWAYS_SKIP_DIRS)
        
        self.spec = self._build_spec()
        
    def _build_spec(self) -> pathspec.PathSpec:
        """Reads .gitignore and .contextlyignore and merges with defaults"""
        patterns = []
        # Security critical ignores are now handled directly in is_ignored for stronger enforcement
        
        if not self.no_default_excludes:
            patterns.extend(self.default_ignores)
        
        def _read_patterns_with_fallback(filepath: Path) -> list:
            if not filepath.exists():
                return []
            
            from ..core.diagnostics import DiagnosticsContext
            for enc in ("utf-8", "utf-16", "latin-1"):
                try:
                    with open(filepath, "r", encoding=enc) as f:
                        return f.readlines()
                except UnicodeDecodeError:
                    continue
                except OSError as e:
                    DiagnosticsContext().add_warning("IgnoreEngine", f"Failed to read {filepath.name}: {str(e)}")
                    return []
                    
            DiagnosticsContext().add_warning("IgnoreEngine", f"Failed to decode {filepath.name} using any supported encoding.")
            return []

        # Read .gitignore
        patterns.extend(_read_patterns_with_fallback(self.root_dir / ".gitignore"))
        
        # Read .contextlyignore
        patterns.extend(_read_patterns_with_fallback(self.root_dir / ".contextlyignore"))
                
        # Filter empty lines and comments
        patterns = [p.strip() for p in patterns if p.strip() and not p.strip().startswith("#")]
        
        # Use the modern 'gitignore' identifier to fix deprecation warnings
        return pathspec.PathSpec.from_lines('gitignore', patterns)
        
    @functools.lru_cache(maxsize=10240)
    def is_ignored(self, path: Path) -> bool:
        """
        Checks if a file or directory path is ignored.
        """
        # Security Check: Never allow secrets, credentials or .git state to be scanned.
        # This operates on exact names, prefixes and extensions rather than ambiguous substrings.
        name_lower = path.name.lower()
        parts_lower = {p.lower() for p in path.parts}
        
        from .constants import is_security_critical_dir, is_security_critical_file
        
        if is_security_critical_dir(name_lower) or any(is_security_critical_dir(p) for p in parts_lower):
            return True

        if is_security_critical_file(name_lower):
            return True

        # Convert path to a relative POSIX string for matching (pathspec requires POSIX style)
        try:
            if path.is_absolute():
                try:
                    rel_path = path.relative_to(self.root_dir)
                except ValueError:
                    # Fallback for paths that differ in symlinks/casing
                    rel_path = path.resolve().relative_to(self.root_dir_resolved)
            else:
                rel_path = path
        except ValueError:
            # If path is not relative to root_dir, don't scan it
            return True
            
        str_path = rel_path.as_posix()

        try:
            is_directory = path.is_dir()
        except OSError:
            is_directory = True # Default to treating it as a directory to ensure directory-specific ignore rules can trigger

        if is_directory and not str_path.endswith('/'):
            str_path += '/'

        return self.spec.match_file(str_path)
