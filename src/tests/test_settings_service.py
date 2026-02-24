"""TDD test suite for AppSettings and SettingsService."""
from __future__ import annotations

import json
from pathlib import Path

import pytest

from src.settings.models import AppSettings
from src.settings.service import SettingsService


# ---------------------------------------------------------------------------
# AppSettings model tests
# ---------------------------------------------------------------------------


def test_default_values():
    """AppSettings() with no args should have all expected defaults."""
    s = AppSettings()
    assert s.seeded_rng_enabled is False
    assert s.seed_value is None
    assert s.default_crit_enabled is True
    assert s.default_crit_range == 20
    assert s.default_nat1_always_miss is True
    assert s.default_nat20_always_hit is True
    assert s.default_advantage_mode == "normal"
    assert s.default_gwm_sharpshooter is False
    assert s.default_mode == "raw"
    assert s.default_target_ac == 15
    assert s.default_save_dc == 13


def test_custom_values():
    """Explicit constructor args override defaults; unspecified fields retain defaults."""
    s = AppSettings(
        seeded_rng_enabled=True,
        seed_value=42,
        default_crit_range=19,
        default_mode="compare",
        default_target_ac=18,
        default_save_dc=10,
    )
    assert s.seeded_rng_enabled is True
    assert s.seed_value == 42
    assert s.default_crit_range == 19
    assert s.default_mode == "compare"
    assert s.default_target_ac == 18
    assert s.default_save_dc == 10
    # Unspecified fields retain defaults
    assert s.default_crit_enabled is True
    assert s.default_nat1_always_miss is True
    assert s.default_nat20_always_hit is True
    assert s.default_advantage_mode == "normal"
    assert s.default_gwm_sharpshooter is False


# ---------------------------------------------------------------------------
# SettingsService tests
# ---------------------------------------------------------------------------


def test_load_no_file(tmp_path: Path):
    """Loading from empty workspace returns AppSettings() with all defaults."""
    service = SettingsService(tmp_path)
    result = service.load()
    assert result == AppSettings()


def test_save_and_load_round_trip(tmp_path: Path):
    """Save then load returns an identical AppSettings."""
    service = SettingsService(tmp_path)
    original = AppSettings(seeded_rng_enabled=True, seed_value=42, default_crit_range=19)
    service.save(original)
    loaded = service.load()
    assert loaded == original


def test_load_corrupt_json(tmp_path: Path):
    """Corrupt settings.json returns default AppSettings without crashing."""
    settings_path = tmp_path / "settings.json"
    settings_path.write_text("THIS IS NOT JSON }{{{", encoding="utf-8")
    service = SettingsService(tmp_path)
    result = service.load()
    assert result == AppSettings()


def test_load_unknown_keys_ignored(tmp_path: Path):
    """Unknown keys in settings.json are silently ignored (forward compatibility)."""
    settings_path = tmp_path / "settings.json"
    settings_path.write_text(
        json.dumps({"future_field": True, "seeded_rng_enabled": True}),
        encoding="utf-8",
    )
    service = SettingsService(tmp_path)
    result = service.load()
    assert result.seeded_rng_enabled is True
    # No error raised for the unknown key


def test_load_missing_keys_use_defaults(tmp_path: Path):
    """Partial settings.json — provided key overrides default; missing keys stay at defaults."""
    settings_path = tmp_path / "settings.json"
    settings_path.write_text(
        json.dumps({"default_mode": "compare"}),
        encoding="utf-8",
    )
    service = SettingsService(tmp_path)
    result = service.load()
    assert result.default_mode == "compare"
    # All other fields use defaults
    assert result.seeded_rng_enabled is False
    assert result.seed_value is None
    assert result.default_crit_enabled is True
    assert result.default_crit_range == 20
    assert result.default_target_ac == 15
    assert result.default_save_dc == 13


def test_save_creates_file(tmp_path: Path):
    """Saving to a workspace where settings.json does not exist creates the file."""
    service = SettingsService(tmp_path)
    settings_path = tmp_path / "settings.json"
    assert not settings_path.exists()
    service.save(AppSettings())
    assert settings_path.exists()
    # Content must be valid JSON
    data = json.loads(settings_path.read_text(encoding="utf-8"))
    assert isinstance(data, dict)


def test_load_os_error(tmp_path: Path, monkeypatch):
    """OSError during read returns default AppSettings without crashing."""
    settings_path = tmp_path / "settings.json"
    settings_path.write_text(json.dumps({}), encoding="utf-8")

    def raise_os_error(*args, **kwargs):
        raise OSError("Permission denied")

    monkeypatch.setattr(Path, "read_text", raise_os_error)
    service = SettingsService(tmp_path)
    result = service.load()
    assert result == AppSettings()
