from pathlib import Path
import pathspec

class IgnoreEngine:
    """Centralized ignore logic for Context-Ly"""
    
    def __init__(self, root_dir: Path):
        self.root_dir = root_dir
        
        # Hardcoded defaults that should never be scanned
        self.default_ignores = [
            ".git/",
            "node_modules/",
            "venv/",
            ".venv/",
            "__pycache__/",
            ".contextly/",
            "dist/",
            "build/",
            ".next/"
        ]
        
        self.spec = self._build_spec()
        
    def _build_spec(self) -> pathspec.PathSpec:
        """Reads .gitignore and .contextlyignore and merges with defaults"""
        patterns = list(self.default_ignores)
        
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
                
        # Filter empty lines
        patterns = [p.strip() for p in patterns if p.strip()]
        
        # Use the modern 'gitignore' identifier to fix deprecation warnings
        return pathspec.PathSpec.from_lines('gitignore', patterns)
        
    def is_ignored(self, path: Path) -> bool:
        """
        Checks if a file or directory path is ignored.
        """
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
