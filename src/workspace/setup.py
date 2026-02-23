from pathlib import Path
from typing import Optional

WORKSPACE_SUBFOLDERS: tuple[str, ...] = ("monsters", "lists", "encounters", "exports")


class WorkspaceError(Exception):
    """Raised when workspace root is missing or inaccessible."""
    pass


class WorkspaceManager:
    def __init__(self, root: Path):
        self.root = root

    def initialize(self) -> list[str]:
        """Create missing subfolders. Returns names of folders that were created (not pre-existing)."""
        created: list[str] = []
        for name in WORKSPACE_SUBFOLDERS:
            folder = self.root / name
            if not folder.exists():
                folder.mkdir(parents=True, exist_ok=True)
                created.append(name)
        return created
        # Caller is responsible for logging/notifying about created folders.
        # Phase 1 has no UI — caller should log to stdout or pass to logger.

    def validate(self) -> bool:
        """Return True if root path exists and is a directory. False if USB unplugged or path deleted."""
        return self.root.exists() and self.root.is_dir()

    def get_subfolder(self, name: str) -> Path:
        """Return Path for a known subfolder. Raises ValueError if name not in WORKSPACE_SUBFOLDERS."""
        if name not in WORKSPACE_SUBFOLDERS:
            raise ValueError(f"Unknown workspace subfolder: {name!r}. Valid: {WORKSPACE_SUBFOLDERS}")
        return self.root / name
