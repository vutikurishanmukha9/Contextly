import os
from pathlib import Path
from typing import List, Dict, Set

from .base import BaseScanner, ScannerError
from ..types.models import RepositoryCapability
from ..utils.walker import RepoWalker

class CapabilityDetector(BaseScanner):
    @property
    def name(self) -> str:
        return "Capability Detector"

    def scan(self, root_dir: Path, **kwargs) -> List[RepositoryCapability]:
        try:
            # Map of Capability Name -> set of keywords
            # Very simplistic for Step 2
            CAPABILITIES = {
                "Authentication": {"auth", "login", "register", "signup", "session", "jwt", "oauth", "password"},
                "Payments": {"payment", "stripe", "billing", "checkout", "invoice", "subscription"},
                "Users": {"user", "profile", "account", "avatar"},
                "Notifications": {"notification", "email", "sms", "alert", "push"}
            }

            scores: Dict[str, float] = {cap: 0.0 for cap in CAPABILITIES}
            evidence: Dict[str, Set[str]] = {cap: set() for cap in CAPABILITIES}

            _ALWAYS_SKIP = {
                ".git", "node_modules", "venv", ".venv", "__pycache__",
                ".contextly", "dist", "build", ".next", ".tox", ".eggs"
            }

            def skip_predicate(path: Path) -> bool:
                name = path.name.lower()
                return name in _ALWAYS_SKIP or name.endswith(".egg-info")

            walker = RepoWalker(root_dir, max_depth=4, skip_predicate=skip_predicate)

            for dirpath, dirnames, filenames in walker.walk():
                rel_path = str(Path(dirpath).relative_to(root_dir))
                
                # Check directory names
                for dirname in dirnames:
                    lower_dir = dirname.lower()
                    for cap, keywords in CAPABILITIES.items():
                        if any(kw in lower_dir for kw in keywords):
                            scores[cap] += 0.3
                            full_rel = os.path.join(rel_path, dirname).replace("\\", "/")
                            if full_rel.startswith("./"):
                                full_rel = full_rel[2:]
                            evidence[cap].add(full_rel)

                # Check filenames
                for filename in filenames:
                    lower_file = filename.lower()
                    for cap, keywords in CAPABILITIES.items():
                        if any(kw in lower_file for kw in keywords):
                            scores[cap] += 0.1
                            full_rel = os.path.join(rel_path, filename).replace("\\", "/")
                            if full_rel.startswith("./"):
                                full_rel = full_rel[2:]
                            evidence[cap].add(full_rel)

            results = []
            for cap, score in scores.items():
                if score > 0:
                    results.append(RepositoryCapability(
                        capability=cap,
                        confidence=min(1.0, score),
                        evidence=list(evidence[cap])[:5], # Limit evidence to top 5
                        node_ids=[] # Filled later when AST graph is built
                    ))

            results.sort(key=lambda x: x.confidence, reverse=True)
            return results

        except Exception as e:
            raise ScannerError(f"Capability scan failed: {str(e)}")
