"""Unit tests for MonsterLibrary service (src/library/service.py).

No Qt dependencies — pure Python + domain models only.
"""
import pytest

from src.library.service import MonsterLibrary
from src.domain.models import Monster


def _make_monster(name: str, cr: str = "1", creature_type: str = "Humanoid", ac: int = 10, hp: int = 10) -> Monster:
    """Helper to build a minimal Monster for testing."""
    return Monster(name=name, ac=ac, hp=hp, cr=cr, creature_type=creature_type)


class TestAddAndAll:
    def test_add_and_all(self):
        lib = MonsterLibrary()
        goblin = _make_monster("Goblin")
        medusa = _make_monster("Medusa", cr="6", creature_type="Monstrosity")
        lib.add(goblin)
        lib.add(medusa)
        result = lib.all()
        assert len(result) == 2

    def test_all_returns_defensive_copy(self):
        lib = MonsterLibrary()
        lib.add(_make_monster("Goblin"))
        copy = lib.all()
        copy.clear()
        assert len(lib.all()) == 1


class TestHasName:
    def test_has_name_false_before_add(self):
        lib = MonsterLibrary()
        assert lib.has_name("Goblin") is False

    def test_has_name_true_after_add(self):
        lib = MonsterLibrary()
        lib.add(_make_monster("Goblin"))
        assert lib.has_name("Goblin") is True

    def test_has_name_false_for_unknown(self):
        lib = MonsterLibrary()
        lib.add(_make_monster("Goblin"))
        assert lib.has_name("Dragon") is False


class TestReplace:
    def test_replace_updates_in_place(self):
        lib = MonsterLibrary()
        lib.add(_make_monster("Goblin", ac=10))
        updated = _make_monster("Goblin", ac=20)
        lib.replace(updated)
        assert lib.all()[0].ac == 20

    def test_replace_preserves_list_length(self):
        lib = MonsterLibrary()
        lib.add(_make_monster("Goblin"))
        lib.replace(_make_monster("Goblin", ac=15))
        assert len(lib.all()) == 1

    def test_replace_nonexistent_appends(self):
        lib = MonsterLibrary()
        lib.replace(_make_monster("Goblin"))
        assert len(lib.all()) == 1
        assert lib.has_name("Goblin")


class TestAddDuplicate:
    def test_add_duplicate_keeps_both(self):
        lib = MonsterLibrary()
        lib.add(_make_monster("Goblin"))
        lib.add(_make_monster("Goblin", ac=99))
        assert len(lib.all()) == 2

    def test_has_name_true_for_duplicated(self):
        lib = MonsterLibrary()
        lib.add(_make_monster("Goblin"))
        lib.add(_make_monster("Goblin"))
        assert lib.has_name("Goblin") is True


class TestRemove:
    def test_remove_existing(self):
        lib = MonsterLibrary()
        lib.add(_make_monster("Goblin"))
        lib.add(_make_monster("Medusa"))
        result = lib.remove("Goblin")
        assert result is True
        assert len(lib.all()) == 1

    def test_remove_nonexistent_returns_false(self):
        lib = MonsterLibrary()
        result = lib.remove("Dragon")
        assert result is False

    def test_remove_leaves_correct_monster(self):
        lib = MonsterLibrary()
        lib.add(_make_monster("Goblin"))
        lib.add(_make_monster("Medusa"))
        lib.remove("Goblin")
        assert lib.all()[0].name == "Medusa"


class TestClear:
    def test_clear_empties_library(self):
        lib = MonsterLibrary()
        lib.add(_make_monster("Goblin"))
        lib.add(_make_monster("Medusa"))
        lib.add(_make_monster("Dragon"))
        lib.clear()
        assert lib.all() == []

    def test_clear_resets_has_name(self):
        lib = MonsterLibrary()
        lib.add(_make_monster("Goblin"))
        lib.clear()
        assert lib.has_name("Goblin") is False


class TestSearch:
    def test_search_by_name(self):
        lib = MonsterLibrary()
        goblin = _make_monster("Goblin")
        medusa = _make_monster("Medusa", creature_type="Monstrosity")
        lib.add(goblin)
        lib.add(medusa)
        result = lib.search("gob")
        assert len(result) == 1
        assert result[0].name == "Goblin"

    def test_search_by_type(self):
        lib = MonsterLibrary()
        dragon = _make_monster("Dragon", creature_type="Dragon")
        goblin = _make_monster("Goblin", creature_type="Humanoid")
        lib.add(dragon)
        lib.add(goblin)
        result = lib.search("drag")
        assert len(result) == 1
        assert result[0].name == "Dragon"

    def test_search_case_insensitive(self):
        lib = MonsterLibrary()
        lib.add(_make_monster("Goblin"))
        result = lib.search("GOBLIN")
        assert len(result) == 1

    def test_search_no_results(self):
        lib = MonsterLibrary()
        lib.add(_make_monster("Goblin"))
        result = lib.search("zzz")
        assert result == []

    def test_search_by_cr(self):
        lib = MonsterLibrary()
        lib.add(_make_monster("Goblin", cr="1/4"))
        lib.add(_make_monster("Ancient Dragon", cr="21"))
        result = lib.search("1/4")
        assert len(result) == 1
        assert result[0].name == "Goblin"

    def test_search_preserves_insertion_order(self):
        lib = MonsterLibrary()
        lib.add(_make_monster("Alpha"))
        lib.add(_make_monster("Beta"))
        lib.add(_make_monster("AlphaBeta"))
        result = lib.search("alpha")
        assert [m.name for m in result] == ["Alpha", "AlphaBeta"]


class TestCreatureTypes:
    def test_creature_types_sorted_unique(self):
        lib = MonsterLibrary()
        lib.add(_make_monster("Dragon", creature_type="Dragon"))
        lib.add(_make_monster("Goblin", creature_type="Humanoid"))
        lib.add(_make_monster("Dragon2", creature_type="Dragon"))
        types = lib.creature_types()
        assert types == ["Dragon", "Humanoid"]

    def test_creature_types_excludes_empty(self):
        lib = MonsterLibrary()
        lib.add(_make_monster("Unknown", creature_type=""))
        lib.add(_make_monster("Goblin", creature_type="Humanoid"))
        types = lib.creature_types()
        assert "" not in types
        assert "Humanoid" in types

    def test_creature_types_empty_library(self):
        lib = MonsterLibrary()
        assert lib.creature_types() == []
