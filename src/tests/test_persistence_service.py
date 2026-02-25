"""Tests for PersistenceService: round-trip, flush, count, corrupt recovery."""
from __future__ import annotations

import dataclasses
import json

import pytest

from src.domain.models import MonsterModification, EquipmentItem, BuffItem
from src.persistence.service import PersistenceService


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

LIST_CATEGORIES = ["loaded_monsters", "encounters", "macros"]
DICT_CATEGORIES = ["modified_monsters"]
ALL_CATEGORIES = LIST_CATEGORIES + DICT_CATEGORIES


def make_service(tmp_path) -> PersistenceService:
    return PersistenceService(workspace_root=tmp_path)


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------


def test_load_missing_file_returns_empty(tmp_path):
    """Each category returns the correct empty default when no file exists."""
    svc = make_service(tmp_path)
    for cat in LIST_CATEGORIES:
        assert svc._load(cat) == [], f"{cat} should default to []"
    for cat in DICT_CATEGORIES:
        assert svc._load(cat) == {}, f"{cat} should default to {{}}"


def test_save_then_load_round_trip(tmp_path):
    """Saving then loading data for each category yields identical data."""
    svc = make_service(tmp_path)

    svc.save_loaded_monsters(["path/a.txt", "path/b.txt"])
    assert svc.load_loaded_monsters() == ["path/a.txt", "path/b.txt"]

    encounters = [{"name": "Ambush", "members": [{"name": "Goblin", "count": 3}]}]
    svc.save_encounters(encounters)
    assert svc.load_encounters() == encounters

    modified = {"Goblin+": {"hp": 8, "ac": 13, "ability_scores": {}, "saves": {}}}
    svc.save_modified_monsters(modified)
    assert svc.load_modified_monsters() == modified

    macros = ["!roll 1d20+5", "!roll 2d6"]
    svc.save_macros(macros)
    assert svc.load_macros() == macros


def test_flush_writes_empty_structure(tmp_path):
    """Flushing one category empties it without affecting the others."""
    svc = make_service(tmp_path)

    svc.save_loaded_monsters(["a.txt"])
    svc.save_encounters([{"name": "Fight"}])
    svc.save_modified_monsters({"Goblin+": {}})
    svc.save_macros(["!roll 1d6"])

    svc.flush("encounters")

    assert svc.load_loaded_monsters() == ["a.txt"]
    assert svc.load_encounters() == []
    assert svc.load_modified_monsters() == {"Goblin+": {}}
    assert svc.load_macros() == ["!roll 1d6"]


def test_flush_all(tmp_path):
    """flush_all empties every category."""
    svc = make_service(tmp_path)

    svc.save_loaded_monsters(["a.txt"])
    svc.save_encounters([{"name": "Fight"}])
    svc.save_modified_monsters({"Goblin+": {}})
    svc.save_macros(["!roll 1d6"])

    svc.flush_all()

    assert svc.load_loaded_monsters() == []
    assert svc.load_encounters() == []
    assert svc.load_modified_monsters() == {}
    assert svc.load_macros() == []


def test_count_returns_entry_count(tmp_path):
    """count() returns the number of top-level entries in a category."""
    svc = make_service(tmp_path)

    svc.save_loaded_monsters(["a.txt", "b.txt", "c.txt"])
    assert svc.count("loaded_monsters") == 3

    svc.flush("loaded_monsters")
    assert svc.count("loaded_monsters") == 0

    svc.save_modified_monsters({"A": {}, "B": {}, "C": {}})
    assert svc.count("modified_monsters") == 3

    svc.flush("modified_monsters")
    assert svc.count("modified_monsters") == 0


def test_corrupt_json_returns_empty(tmp_path):
    """A corrupt JSON file triggers graceful fallback to empty default."""
    svc = make_service(tmp_path)

    for cat in LIST_CATEGORIES:
        path = tmp_path / f"{cat}.json"
        path.write_text("NOT VALID JSON {{{", encoding="utf-8")
        result = svc._load(cat)
        assert result == [], f"{cat}: corrupt file should return []"

    for cat in DICT_CATEGORIES:
        path = tmp_path / f"{cat}.json"
        path.write_text("NOT VALID JSON {{{", encoding="utf-8")
        result = svc._load(cat)
        assert result == {}, f"{cat}: corrupt file should return {{}}"


def test_modified_monsters_round_trip_with_dataclass(tmp_path):
    """MonsterModification round-trips through PersistenceService via dataclasses.asdict()."""
    svc = make_service(tmp_path)

    mod = MonsterModification(
        base_name="Goblin",
        custom_name="Boss Goblin",
        ability_scores={"STR": 8, "DEX": 14},
        saves={"DEX": 2},
        hp=12,
        ac=13,
        cr="1/4",
    )
    as_dict = dataclasses.asdict(mod)

    svc.save_modified_monsters({"Boss Goblin": as_dict})
    loaded = svc.load_modified_monsters()

    assert loaded["Boss Goblin"] == as_dict


def test_modified_monsters_round_trip_with_equipment_and_buffs(tmp_path):
    """MonsterModification with equipment and buffs round-trips through PersistenceService."""
    svc = make_service(tmp_path)

    mod = MonsterModification(
        base_name="Goblin",
        custom_name="Armored Goblin",
        skills={"Stealth": 6},
        hp_formula="2d6",
        size="Small",
        equipment=[
            EquipmentItem(item_type="weapon", item_name="Shortsword", magic_bonus=1),
            EquipmentItem(item_type="armor", item_name="Leather", magic_bonus=0),
        ],
        buffs=[
            BuffItem(name="Bless", bonus_value="+1d4", targets="attack_rolls"),
        ],
    )
    as_dict = dataclasses.asdict(mod)

    svc.save_modified_monsters({"Armored Goblin": as_dict})
    loaded = svc.load_modified_monsters()

    loaded_dict = loaded["Armored Goblin"]
    assert loaded_dict == as_dict

    # Verify from_dict reconstructs nested dataclasses
    restored = MonsterModification.from_dict(loaded_dict)
    assert restored.base_name == "Goblin"
    assert len(restored.equipment) == 2
    assert isinstance(restored.equipment[0], EquipmentItem)
    assert restored.equipment[0].item_name == "Shortsword"
    assert restored.equipment[0].magic_bonus == 1
    assert len(restored.buffs) == 1
    assert isinstance(restored.buffs[0], BuffItem)
    assert restored.buffs[0].name == "Bless"
    assert restored.skills == {"Stealth": 6}
    assert restored.hp_formula == "2d6"
    assert restored.size == "Small"


def test_modified_monsters_from_dict_old_format_loads_without_error(tmp_path):
    """Old-format MonsterModification dict (without new fields) loads via from_dict without error."""
    svc = make_service(tmp_path)

    # Simulate an old JSON dict that only has original fields (no equipment/buffs/skills/etc.)
    old_format = {
        "base_name": "Goblin",
        "custom_name": None,
        "ability_scores": {"STR": 8},
        "saves": {},
        "hp": None,
        "ac": None,
        "cr": None,
        "spellcasting_infos": [],
    }
    svc.save_modified_monsters({"Goblin": old_format})
    loaded = svc.load_modified_monsters()

    # from_dict must not raise even with missing new fields
    mod = MonsterModification.from_dict(loaded["Goblin"])
    assert mod.base_name == "Goblin"
    assert mod.equipment == []
    assert mod.buffs == []
    assert mod.skills == {}
    assert mod.hp_formula is None
    assert mod.size is None
