"""
Tests for EncounterService: round-trip save/load, unresolved entries, edge cases.

RED phase: these tests import from src.encounter.service which does not yet exist.
Running this file must fail with ImportError.
"""
from __future__ import annotations

import tempfile
from pathlib import Path

import pytest

from src.encounter.service import EncounterService  # noqa: F401 (will fail in RED)
from src.encounter.models import UnresolvedEntry
from src.domain.models import Monster, Encounter
from src.library.service import MonsterLibrary


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_goblin() -> Monster:
    return Monster(
        name="Goblin",
        ac=15,
        hp=7,
        cr="1/4",
        saves={"DEX": 4},
        ability_scores={"STR": 8, "DEX": 14, "CON": 10, "INT": 10, "WIS": 8, "CHA": 8},
    )


def _make_hobgoblin() -> Monster:
    return Monster(
        name="Hobgoblin",
        ac=18,
        hp=11,
        cr="1/2",
        saves={},
        ability_scores={"STR": 13, "DEX": 12, "CON": 12, "INT": 10, "WIS": 10, "CHA": 9},
    )


def _make_library(*monsters: Monster) -> MonsterLibrary:
    lib = MonsterLibrary()
    for m in monsters:
        lib.add(m)
    return lib


# ---------------------------------------------------------------------------
# Round-trip tests
# ---------------------------------------------------------------------------


def test_save_load_round_trip():
    """Saving an encounter and loading it back produces the same name, members, and counts."""
    goblin = _make_goblin()
    hobgoblin = _make_hobgoblin()
    encounter = Encounter(
        name="Bandit Ambush",
        members=[(goblin, 3), (hobgoblin, 1)],
    )
    lib = _make_library(goblin, hobgoblin)
    svc = EncounterService()

    with tempfile.TemporaryDirectory() as tmp:
        path = Path(tmp) / "encounter.md"
        svc.save_encounter(encounter, path)
        loaded, unresolved = svc.load_encounter(path, lib)

    assert loaded.name == "Bandit Ambush"
    assert len(loaded.members) == 2
    assert unresolved == []
    # Check members: order and counts
    member_map = {m.name: count for m, count in loaded.members}
    assert member_map["Goblin"] == 3
    assert member_map["Hobgoblin"] == 1


def test_save_load_single_monster():
    """Round-trip with a single monster entry preserves count."""
    goblin = _make_goblin()
    encounter = Encounter(name="Single Test", members=[(goblin, 2)])
    lib = _make_library(goblin)
    svc = EncounterService()

    with tempfile.TemporaryDirectory() as tmp:
        path = Path(tmp) / "single.md"
        svc.save_encounter(encounter, path)
        loaded, unresolved = svc.load_encounter(path, lib)

    assert loaded.name == "Single Test"
    assert len(loaded.members) == 1
    assert loaded.members[0][0].name == "Goblin"
    assert loaded.members[0][1] == 2
    assert unresolved == []


def test_save_creates_file():
    """save_encounter must create the file at the given path."""
    goblin = _make_goblin()
    encounter = Encounter(name="Test", members=[(goblin, 1)])
    svc = EncounterService()

    with tempfile.TemporaryDirectory() as tmp:
        path = Path(tmp) / "subdir" / "test.md"
        path.parent.mkdir(parents=True, exist_ok=True)
        svc.save_encounter(encounter, path)
        assert path.exists()


def test_save_format_utf8_header():
    """Saved file starts with '# Encounter: {name}' header and has bullet entries."""
    goblin = _make_goblin()
    encounter = Encounter(name="Forest Glade", members=[(goblin, 2)])
    svc = EncounterService()

    with tempfile.TemporaryDirectory() as tmp:
        path = Path(tmp) / "fmt.md"
        svc.save_encounter(encounter, path)
        content = path.read_text(encoding="utf-8")

    assert content.startswith("# Encounter: Forest Glade")
    assert "- 2x Goblin" in content


# ---------------------------------------------------------------------------
# Unresolved entries
# ---------------------------------------------------------------------------


def test_load_unknown_monster_returns_unresolved():
    """Loading a file with an unknown monster name returns it as UnresolvedEntry, members=[]."""
    svc = EncounterService()
    lib = _make_library()  # empty library

    content = "# Encounter: Ghost Town\n\n- 2x FantomMonster\n"
    with tempfile.TemporaryDirectory() as tmp:
        path = Path(tmp) / "ghost.md"
        path.write_text(content, encoding="utf-8")
        loaded, unresolved = svc.load_encounter(path, lib)

    assert loaded.name == "Ghost Town"
    assert loaded.members == []
    assert len(unresolved) == 1
    assert unresolved[0] == UnresolvedEntry(name="FantomMonster", count=2)


def test_load_mixed_known_and_unknown():
    """Loading with 1 known + 1 unknown produces 1 member and 1 unresolved entry."""
    goblin = _make_goblin()
    lib = _make_library(goblin)
    svc = EncounterService()

    content = "# Encounter: Mixed\n\n- 1x Goblin\n- 3x UnknownBeast\n"
    with tempfile.TemporaryDirectory() as tmp:
        path = Path(tmp) / "mixed.md"
        path.write_text(content, encoding="utf-8")
        loaded, unresolved = svc.load_encounter(path, lib)

    assert loaded.name == "Mixed"
    assert len(loaded.members) == 1
    assert loaded.members[0][0].name == "Goblin"
    assert loaded.members[0][1] == 1
    assert len(unresolved) == 1
    assert unresolved[0] == UnresolvedEntry(name="UnknownBeast", count=3)


def test_load_all_unresolved_no_crash():
    """If all entries are unresolved, returns empty members without crash."""
    lib = _make_library()
    svc = EncounterService()

    content = "# Encounter: Empty Lib\n\n- 5x BogMonster\n- 1x DragonKing\n"
    with tempfile.TemporaryDirectory() as tmp:
        path = Path(tmp) / "all_unresolved.md"
        path.write_text(content, encoding="utf-8")
        loaded, unresolved = svc.load_encounter(path, lib)

    assert loaded.members == []
    assert len(unresolved) == 2


# ---------------------------------------------------------------------------
# Empty encounter
# ---------------------------------------------------------------------------


def test_empty_encounter_round_trip():
    """An encounter with no members saves and loads back with empty members."""
    encounter = Encounter(name="Empty", members=[])
    lib = _make_library()
    svc = EncounterService()

    with tempfile.TemporaryDirectory() as tmp:
        path = Path(tmp) / "empty.md"
        svc.save_encounter(encounter, path)
        loaded, unresolved = svc.load_encounter(path, lib)

    assert loaded.name == "Empty"
    assert loaded.members == []
    assert unresolved == []


# ---------------------------------------------------------------------------
# Bad lines: non-crash guarantee
# ---------------------------------------------------------------------------


def test_bad_lines_do_not_crash():
    """Malformed or unparseable lines are silently skipped without crash."""
    goblin = _make_goblin()
    lib = _make_library(goblin)
    svc = EncounterService()

    content = (
        "# Encounter: With Noise\n"
        "\n"
        "Some random paragraph text\n"
        "- 2x Goblin\n"
        "- badline no count\n"
        "   \n"
    )
    with tempfile.TemporaryDirectory() as tmp:
        path = Path(tmp) / "noisy.md"
        path.write_text(content, encoding="utf-8")
        loaded, unresolved = svc.load_encounter(path, lib)

    assert loaded.name == "With Noise"
    assert len(loaded.members) == 1
    assert loaded.members[0][0].name == "Goblin"
