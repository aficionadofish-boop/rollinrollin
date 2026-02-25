from __future__ import annotations

import json
from pathlib import Path

_FILENAMES = {
    "loaded_monsters": "loaded_monsters.json",
    "encounters": "encounters.json",
    "modified_monsters": "modified_monsters.json",
    "macros": "macros.json",
}

# Categories that use a dict as their empty default; all others use a list.
_DICT_CATEGORIES = {"modified_monsters"}


class PersistenceService:
    """JSON persistence for four app data categories: loaded_monsters, encounters,
    modified_monsters, and macros.

    Modeled on SettingsService. Takes a workspace_root Path so callers can inject
    a tmp_path for testing.
    """

    def __init__(self, workspace_root: Path) -> None:
        self._root = workspace_root

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    def _empty_default(self, category: str) -> dict | list:
        """Return the appropriate empty default for a category."""
        return {} if category in _DICT_CATEGORIES else []

    def _load(self, category: str) -> dict | list:
        """Read JSON from disk. Returns empty default on missing/corrupt file."""
        path = self._root / _FILENAMES[category]
        if not path.exists():
            return self._empty_default(category)
        try:
            return json.loads(path.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            return self._empty_default(category)

    def _save(self, category: str, data: dict | list) -> None:
        """Write data as JSON to disk, creating parent dirs if needed."""
        path = self._root / _FILENAMES[category]
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(data, indent=2), encoding="utf-8")

    # ------------------------------------------------------------------
    # Loaded monsters
    # ------------------------------------------------------------------

    def load_loaded_monsters(self) -> list:
        """Return list of source file paths (strings)."""
        return self._load("loaded_monsters")

    def save_loaded_monsters(self, data: list) -> None:
        self._save("loaded_monsters", data)

    # ------------------------------------------------------------------
    # Encounters
    # ------------------------------------------------------------------

    def load_encounters(self) -> list:
        """Return list of {name: str, members: [{name: str, count: int}]}."""
        return self._load("encounters")

    def save_encounters(self, data: list) -> None:
        self._save("encounters", data)

    # ------------------------------------------------------------------
    # Modified monsters
    # ------------------------------------------------------------------

    def load_modified_monsters(self) -> dict:
        """Return {name: {ability_scores, saves, ...}} dict."""
        return self._load("modified_monsters")

    def save_modified_monsters(self, data: dict) -> None:
        self._save("modified_monsters", data)

    # ------------------------------------------------------------------
    # Macros
    # ------------------------------------------------------------------

    def load_macros(self) -> list:
        """Return list (or single-element list with last-active buffer)."""
        return self._load("macros")

    def save_macros(self, data: list) -> None:
        self._save("macros", data)

    # ------------------------------------------------------------------
    # Utility
    # ------------------------------------------------------------------

    def categories(self) -> list[str]:
        """Return list of all category keys."""
        return list(_FILENAMES.keys())

    def flush(self, category: str) -> None:
        """Write empty structure for the given category without deleting the file."""
        self._save(category, self._empty_default(category))

    def flush_all(self) -> None:
        """Flush all categories to their empty defaults."""
        for category in _FILENAMES:
            self.flush(category)

    def count(self, category: str) -> int:
        """Return number of entries in the given category."""
        return len(self._load(category))
