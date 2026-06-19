from pathlib import Path
import pathspec

class IgnoreEngine:
    """Centralized ignore logic for Context-Ly"""
    
    def __init__(self, root_dir: Path, no_default_excludes: bool = False):
        self.root_dir = root_dir
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
        
        # Read .gitignore
        gitignore_path = self.root_dir / ".gitignore"
        if gitignore_path.exists():
            try:
                with open(gitignore_path, "r", encoding="utf-8") as f:
                    patterns.extend(f.readlines())
            except (OSError, UnicodeDecodeError):
                pass
                
        # Read .contextlyignore
        contextlyignore_path = self.root_dir / ".contextlyignore"
        if contextlyignore_path.exists():
            try:
                with open(contextlyignore_path, "r", encoding="utf-8") as f:
                    patterns.extend(f.readlines())
            except (OSError, UnicodeDecodeError):
                pass
                
        # Filter empty lines and comments
        patterns = [p.strip() for p in patterns if p.strip() and not p.strip().startswith("#")]
        
        # Use the modern 'gitignore' identifier to fix deprecation warnings
        return pathspec.PathSpec.from_lines('gitignore', patterns)
        
    def is_ignored(self, path: Path) -> bool:
        """
        Checks if a file or directory path is ignored.
        """
        # Security Check: Never allow secrets, credentials or .git state to be scanned.
        # This operates on exact names, prefixes and extensions rather than ambiguous substrings.
        name_lower = path.name.lower()
        parts_lower = {p.lower() for p in path.parts}
        
        # Sensitive directory hierarchies — skip entire trees
        _SENSITIVE_DIRS = {".git", ".contextly", ".ssh", ".aws", ".kube", ".gcp", ".docker", ".gnupg"}
        if parts_lower.intersection(_SENSITIVE_DIRS):
            return True

        # Exact filenames and precise patterns
        _SENSITIVE_FILES = {".npmrc", "id_rsa", "id_ed25519", "master.key", "credentials"}
        if (
            name_lower in _SENSITIVE_FILES
            or name_lower.startswith(".env")
            or name_lower.endswith(".pem")
            or name_lower.endswith(".key")
        ):
            return True

        # Convert path to a relative POSIX string for matching (pathspec requires POSIX style)
        try:
            rel_path = path.relative_to(self.root_dir)
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
