"""Tests for MonsterTableModel and MonsterFilterProxyModel.

All tests require a QApplication instance — provided by the qapp session
fixture defined in conftest.py.  Qt model tests are kept in this separate
file so the qapp fixture is only loaded when running Qt tests.
"""
import pytest

from PySide6.QtCore import Qt, QModelIndex

from src.domain.models import Monster
from src.ui.monster_table import MonsterTableModel, _cr_to_float
from src.ui.monster_filter import MonsterFilterProxyModel


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _monster(name: str, cr: str = "1", creature_type: str = "Humanoid", incomplete: bool = False) -> Monster:
    return Monster(name=name, ac=10, hp=10, cr=cr, creature_type=creature_type, incomplete=incomplete)


def _model(*monsters, qapp) -> MonsterTableModel:  # noqa: ANN001  (qapp fixture injected)
    """Build a MonsterTableModel from *monsters* (qapp fixture ensures QApp exists)."""
    return MonsterTableModel(list(monsters))


# ---------------------------------------------------------------------------
# _cr_to_float unit tests (no QApp needed but kept here for cohesion)
# ---------------------------------------------------------------------------

class TestCrToFloat:
    def test_fraction_half(self):
        assert _cr_to_float("1/2") == pytest.approx(0.5)

    def test_fraction_quarter(self):
        assert _cr_to_float("1/4") == pytest.approx(0.25)

    def test_fraction_eighth(self):
        assert _cr_to_float("1/8") == pytest.approx(0.125)

    def test_integer_zero(self):
        assert _cr_to_float("0") == pytest.approx(0.0)

    def test_integer_large(self):
        assert _cr_to_float("17") == pytest.approx(17.0)

    def test_question_mark(self):
        assert _cr_to_float("?") == pytest.approx(-1.0)

    def test_empty_string(self):
        assert _cr_to_float("") == pytest.approx(-1.0)

    def test_em_dash(self):
        assert _cr_to_float("—") == pytest.approx(-1.0)

    def test_hyphen(self):
        assert _cr_to_float("-") == pytest.approx(-1.0)

    def test_whitespace_stripped(self):
        assert _cr_to_float("  2  ") == pytest.approx(2.0)


# ---------------------------------------------------------------------------
# MonsterTableModel tests
# ---------------------------------------------------------------------------

class TestMonsterTableModelRowCount:
    def test_row_count(self, qapp):
        m = MonsterTableModel([_monster("A"), _monster("B"), _monster("C")])
        assert m.rowCount() == 3

    def test_row_count_empty(self, qapp):
        m = MonsterTableModel([])
        assert m.rowCount() == 0

    def test_row_count_default_none(self, qapp):
        m = MonsterTableModel()
        assert m.rowCount() == 0


class TestMonsterTableModelColumnCount:
    def test_column_count(self, qapp):
        m = MonsterTableModel([_monster("A")])
        assert m.columnCount() == 4


class TestMonsterTableModelData:
    def test_data_name(self, qapp):
        goblin = _monster("Goblin")
        m = MonsterTableModel([goblin])
        assert m.data(m.index(0, 0), Qt.DisplayRole) == "Goblin"

    def test_data_cr(self, qapp):
        goblin = _monster("Goblin", cr="1/4")
        m = MonsterTableModel([goblin])
        assert m.data(m.index(0, 1), Qt.DisplayRole) == "1/4"

    def test_data_type(self, qapp):
        goblin = _monster("Goblin", creature_type="Humanoid")
        m = MonsterTableModel([goblin])
        assert m.data(m.index(0, 2), Qt.DisplayRole) == "Humanoid"

    def test_data_incomplete_badge_true(self, qapp):
        goblin = _monster("Goblin", incomplete=True)
        m = MonsterTableModel([goblin])
        assert m.data(m.index(0, 3), Qt.DisplayRole) == "!"

    def test_data_incomplete_badge_false(self, qapp):
        goblin = _monster("Goblin", incomplete=False)
        m = MonsterTableModel([goblin])
        assert m.data(m.index(0, 3), Qt.DisplayRole) == ""

    def test_data_cr_user_role_returns_float(self, qapp):
        goblin = _monster("Goblin", cr="1/4")
        m = MonsterTableModel([goblin])
        val = m.data(m.index(0, 1), Qt.UserRole)
        assert isinstance(val, float)
        assert val == pytest.approx(0.25)

    def test_data_invalid_index_returns_none(self, qapp):
        m = MonsterTableModel([_monster("A")])
        assert m.data(m.index(99, 0), Qt.DisplayRole) is None

    def test_data_unknown_role_returns_none(self, qapp):
        m = MonsterTableModel([_monster("A")])
        assert m.data(m.index(0, 0), Qt.DecorationRole) is None

    def test_data_user_role_col0_returns_lowercase_name(self, qapp):
        # UserRole for col 0 returns lowercase name for case-insensitive sort
        m = MonsterTableModel([_monster("Goblin")])
        assert m.data(m.index(0, 0), Qt.UserRole) == "goblin"


class TestMonsterTableModelHeaderData:
    def test_header_name(self, qapp):
        m = MonsterTableModel([_monster("A")])
        assert m.headerData(0, Qt.Horizontal, Qt.DisplayRole) == "Name"

    def test_header_cr(self, qapp):
        m = MonsterTableModel([_monster("A")])
        assert m.headerData(1, Qt.Horizontal, Qt.DisplayRole) == "CR"

    def test_header_type(self, qapp):
        m = MonsterTableModel([_monster("A")])
        assert m.headerData(2, Qt.Horizontal, Qt.DisplayRole) == "Type"

    def test_header_badge_empty(self, qapp):
        m = MonsterTableModel([_monster("A")])
        assert m.headerData(3, Qt.Horizontal, Qt.DisplayRole) == ""

    def test_header_vertical_returns_none(self, qapp):
        m = MonsterTableModel([_monster("A")])
        assert m.headerData(0, Qt.Vertical, Qt.DisplayRole) is None


class TestMonsterTableModelResetMonsters:
    def test_reset_monsters_changes_row_count(self, qapp):
        m = MonsterTableModel([_monster("A"), _monster("B")])
        assert m.rowCount() == 2
        m.reset_monsters([_monster("X")])
        assert m.rowCount() == 1

    def test_reset_monsters_updates_data(self, qapp):
        m = MonsterTableModel([_monster("OldName")])
        m.reset_monsters([_monster("NewName")])
        assert m.data(m.index(0, 0), Qt.DisplayRole) == "NewName"

    def test_reset_monsters_empty(self, qapp):
        m = MonsterTableModel([_monster("A")])
        m.reset_monsters([])
        assert m.rowCount() == 0


class TestMonsterAt:
    def test_monster_at_returns_correct_monster(self, qapp):
        goblin = _monster("Goblin")
        m = MonsterTableModel([goblin, _monster("Medusa")])
        assert m.monster_at(0) is goblin

    def test_monster_at_raises_on_invalid(self, qapp):
        m = MonsterTableModel([_monster("A")])
        with pytest.raises(IndexError):
            m.monster_at(99)


# ---------------------------------------------------------------------------
# MonsterFilterProxyModel tests
# ---------------------------------------------------------------------------

class TestMonsterFilterProxyText:
    def test_filter_text_shows_match(self, qapp):
        source = MonsterTableModel([_monster("Goblin"), _monster("Medusa")])
        proxy = MonsterFilterProxyModel()
        proxy.setSourceModel(source)
        proxy.setFilterFixedString("gob")
        assert proxy.rowCount() == 1
        # Verify the matching monster is Goblin
        src_idx = proxy.mapToSource(proxy.index(0, 0))
        assert source.monster_at(src_idx.row()).name == "Goblin"

    def test_filter_text_hides_nonmatch(self, qapp):
        source = MonsterTableModel([_monster("Goblin"), _monster("Medusa")])
        proxy = MonsterFilterProxyModel()
        proxy.setSourceModel(source)
        proxy.setFilterFixedString("medusa")
        assert proxy.rowCount() == 1

    def test_filter_text_empty_shows_all(self, qapp):
        source = MonsterTableModel([_monster("Goblin"), _monster("Medusa")])
        proxy = MonsterFilterProxyModel()
        proxy.setSourceModel(source)
        proxy.setFilterFixedString("")
        assert proxy.rowCount() == 2


class TestMonsterFilterProxyType:
    def test_filter_type_shows_match(self, qapp):
        source = MonsterTableModel([
            _monster("Dragon", creature_type="Dragon"),
            _monster("Goblin", creature_type="Humanoid"),
        ])
        proxy = MonsterFilterProxyModel()
        proxy.setSourceModel(source)
        proxy.set_type_filter("Dragon")
        assert proxy.rowCount() == 1

    def test_filter_type_hides_others(self, qapp):
        source = MonsterTableModel([
            _monster("Dragon", creature_type="Dragon"),
            _monster("Goblin", creature_type="Humanoid"),
            _monster("Lich", creature_type="Undead"),
        ])
        proxy = MonsterFilterProxyModel()
        proxy.setSourceModel(source)
        proxy.set_type_filter("Undead")
        assert proxy.rowCount() == 1

    def test_filter_type_empty_shows_all(self, qapp):
        source = MonsterTableModel([
            _monster("Dragon", creature_type="Dragon"),
            _monster("Goblin", creature_type="Humanoid"),
        ])
        proxy = MonsterFilterProxyModel()
        proxy.setSourceModel(source)
        proxy.set_type_filter("")
        assert proxy.rowCount() == 2


class TestMonsterFilterProxyIncomplete:
    def test_filter_incomplete_shows_only_incomplete(self, qapp):
        source = MonsterTableModel([
            _monster("Broken", incomplete=True),
            _monster("Complete", incomplete=False),
        ])
        proxy = MonsterFilterProxyModel()
        proxy.setSourceModel(source)
        proxy.set_incomplete_only(True)
        assert proxy.rowCount() == 1

    def test_filter_incomplete_false_shows_all(self, qapp):
        source = MonsterTableModel([
            _monster("Broken", incomplete=True),
            _monster("Complete", incomplete=False),
        ])
        proxy = MonsterFilterProxyModel()
        proxy.setSourceModel(source)
        proxy.set_incomplete_only(False)
        assert proxy.rowCount() == 2


class TestMonsterFilterProxyAndLogic:
    def test_and_logic_text_and_type(self, qapp):
        source = MonsterTableModel([
            _monster("Dragon", creature_type="Dragon"),
            _monster("DarkElf", creature_type="Humanoid"),
            _monster("Goblin", creature_type="Humanoid"),
        ])
        proxy = MonsterFilterProxyModel()
        proxy.setSourceModel(source)
        proxy.setFilterFixedString("dragon")
        proxy.set_type_filter("Dragon")
        # Only "Dragon" with creature_type="Dragon" passes both filters
        assert proxy.rowCount() == 1

    def test_and_logic_all_three(self, qapp):
        source = MonsterTableModel([
            _monster("Broken Dragon", cr="5", creature_type="Dragon", incomplete=True),
            _monster("Complete Dragon", cr="10", creature_type="Dragon", incomplete=False),
            _monster("Broken Goblin", cr="1", creature_type="Humanoid", incomplete=True),
        ])
        proxy = MonsterFilterProxyModel()
        proxy.setSourceModel(source)
        proxy.setFilterFixedString("dragon")
        proxy.set_type_filter("Dragon")
        proxy.set_incomplete_only(True)
        assert proxy.rowCount() == 1


class TestCrSortOrder:
    def test_cr_sort_numeric(self, qapp):
        """CR '10' must sort after CR '2' using float comparison."""
        source = MonsterTableModel([
            _monster("TenCR", cr="10"),
            _monster("TwoCR", cr="2"),
        ])
        proxy = MonsterFilterProxyModel()
        proxy.setSourceModel(source)
        proxy.sort(1, Qt.AscendingOrder)
        # After sort: row 0 = CR 2, row 1 = CR 10
        idx0 = proxy.mapToSource(proxy.index(0, 0))
        idx1 = proxy.mapToSource(proxy.index(1, 0))
        assert source.monster_at(idx0.row()).cr == "2"
        assert source.monster_at(idx1.row()).cr == "10"

    def test_cr_sort_fraction(self, qapp):
        """CR '1/2' (0.5) must sort before CR '1' (1.0)."""
        source = MonsterTableModel([
            _monster("OneCR", cr="1"),
            _monster("HalfCR", cr="1/2"),
        ])
        proxy = MonsterFilterProxyModel()
        proxy.setSourceModel(source)
        proxy.sort(1, Qt.AscendingOrder)
        idx0 = proxy.mapToSource(proxy.index(0, 0))
        assert source.monster_at(idx0.row()).cr == "1/2"

    def test_name_sort_ascending(self, qapp):
        """Name column sorts A→Z when sorted ascending."""
        source = MonsterTableModel([
            _monster("Zombie"),
            _monster("Goblin"),
            _monster("Aboleth"),
        ])
        proxy = MonsterFilterProxyModel()
        proxy.setSourceModel(source)
        proxy.sort(0, Qt.AscendingOrder)
        idx0 = proxy.mapToSource(proxy.index(0, 0))
        idx2 = proxy.mapToSource(proxy.index(2, 0))
        assert source.monster_at(idx0.row()).name == "Aboleth"
        assert source.monster_at(idx2.row()).name == "Zombie"

    def test_name_sort_case_insensitive(self, qapp):
        """Name sort is case-insensitive: 'aboleth' sorts before 'Goblin'."""
        source = MonsterTableModel([
            _monster("goblin"),
            _monster("aboleth"),
        ])
        proxy = MonsterFilterProxyModel()
        proxy.setSourceModel(source)
        proxy.sort(0, Qt.AscendingOrder)
        idx0 = proxy.mapToSource(proxy.index(0, 0))
        assert source.monster_at(idx0.row()).name == "aboleth"
