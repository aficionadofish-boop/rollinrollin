from __future__ import annotations

import dataclasses
import json
from pathlib import Path

from src.settings.models import AppSettings

_FILENAME = "settings.json"


class SettingsService:
    def __init__(self, workspace_root: Path) -> None:
        self._path = workspace_root / _FILENAME

    def load(self) -> AppSettings:
        """Load settings from JSON. Missing keys use dataclass defaults."""
        if not self._path.exists():
            return AppSettings()
        try:
            data = json.loads(self._path.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            return AppSettings()
        known = {f.name for f in dataclasses.fields(AppSettings)}
        filtered = {k: v for k, v in data.items() if k in known}
        return AppSettings(**filtered)

    def save(self, settings: AppSettings) -> None:
        """Write settings to JSON."""
        data = dataclasses.asdict(settings)
        self._path.write_text(json.dumps(data, indent=2), encoding="utf-8")
