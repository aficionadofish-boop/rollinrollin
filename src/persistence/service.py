from __future__ import annotations

import json
from pathlib import Path

_FILENAMES = {
    "loaded_monsters": "loaded_monsters.json",
    "encounters": "encounters.json",
    "modified_monsters": "modified_monsters.json",
    "macros": "macros.json",
    "combat_state": "combat_state.json",
    "player_characters": "player_characters.json",
    "save_rules": "save_rules.json",
    "storyteller_presets": "storyteller_presets.json",
}

# Categories that use a dict as their empty default; all others use a list.
_DICT_CATEGORIES = {"modified_monsters", "encounters", "combat_state", "storyteller_presets"}


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
    # Encounters — active encounter and saved encounters
    # ------------------------------------------------------------------

    def load_active_encounter(self) -> dict | None:
        """Return the active encounter dict {name, members} or None if missing."""
        data = self._load("encounters")
        if not isinstance(data, dict):
            return None
        active = data.get("active")
        if not active:
            return None
        return active

    def save_active_encounter(self, encounter_data: dict) -> None:
        """Persist active encounter, preserving saved encounters in the same file."""
        data = self._load("encounters")
        if not isinstance(data, dict):
            data = {}
        data["active"] = encounter_data
        self._save("encounters", data)

    def load_saved_encounters(self) -> list:
        """Return the list of saved encounter dicts [{name, members, saved_at}]."""
        data = self._load("encounters")
        if not isinstance(data, dict):
            return []
        return data.get("saved", [])

    def save_saved_encounter(self, encounter: dict) -> None:
        """Append a named encounter to the saved list."""
        data = self._load("encounters")
        if not isinstance(data, dict):
            data = {}
        saved = data.get("saved", [])
        saved.append(encounter)
        data["saved"] = saved
        self._save("encounters", data)

    def delete_saved_encounter(self, index: int) -> None:
        """Remove a saved encounter by index."""
        data = self._load("encounters")
        if not isinstance(data, dict):
            return
        saved = data.get("saved", [])
        if 0 <= index < len(saved):
            saved.pop(index)
            data["saved"] = saved
            self._save("encounters", data)

    def rename_saved_encounter(self, index: int, new_name: str) -> None:
        """Update the name of a saved encounter at the given index."""
        data = self._load("encounters")
        if not isinstance(data, dict):
            return
        saved = data.get("saved", [])
        if 0 <= index < len(saved):
            saved[index]["name"] = new_name
            data["saved"] = saved
            self._save("encounters", data)

    def save_encounters(self, data: dict) -> None:
        """Write the entire encounters dict at once (flush/autosave lifecycle)."""
        self._save("encounters", data)

    def load_encounters(self) -> dict:
        """Return the full encounters dict. Kept for backward compatibility."""
        data = self._load("encounters")
        if not isinstance(data, dict):
            return {}
        return data

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
    # Combat state
    # ------------------------------------------------------------------

    def load_combat_state(self) -> dict:
        """Return the combat state dict or empty dict."""
        data = self._load("combat_state")
        if not isinstance(data, dict):
            return {}
        return data

    def save_combat_state(self, data: dict) -> None:
        self._save("combat_state", data)

    # ------------------------------------------------------------------
    # Player characters
    # ------------------------------------------------------------------

    def load_player_characters(self) -> list:
        """Return list of player character dicts."""
        return self._load("player_characters")

    def save_player_characters(self, data: list) -> None:
        self._save("player_characters", data)

    # ------------------------------------------------------------------
    # Save detection rules
    # ------------------------------------------------------------------

    def load_save_rules(self) -> list:
        """Return list of custom detection rule dicts."""
        return self._load("save_rules")

    def save_save_rules(self, data: list) -> None:
        self._save("save_rules", data)

    # ------------------------------------------------------------------
    # Storyteller presets
    # ------------------------------------------------------------------

    def load_storyteller_presets(self) -> dict:
        """Return dict of preset name -> preset dict. Empty dict if no file."""
        return self._load("storyteller_presets")

    def save_storyteller_presets(self, data: dict) -> None:
        """Persist presets dict to disk."""
        self._save("storyteller_presets", data)

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
        """Return number of entries in the given category.

        For encounters: counts active (1 if present) + number of saved encounters.
        For combat_state: returns len(combatants) from the loaded dict.
        For all other categories: returns len() of the loaded data.
        """
        if category == "encounters":
            data = self._load("encounters")
            if not isinstance(data, dict):
                return 0
            active = data.get("active")
            saved = data.get("saved", [])
            return len(saved) + (1 if active else 0)
        if category == "combat_state":
            data = self._load("combat_state")
            if not isinstance(data, dict):
                return 0
            return len(data.get("combatants", []))
        return len(self._load(category))
