"""MonsterTableModel — QAbstractTableModel wrapping a list of Monster instances.

Columns (index 0-3):
    0  Name          — monster.name
    1  CR            — monster.cr (display) / _cr_to_float(monster.cr) at UserRole
    2  Type          — monster.creature_type
    3  (badge)       — "!" when monster.incomplete, "" otherwise

CR sort uses Qt.UserRole so that a sort-proxy model with setSortRole(Qt.UserRole)
performs numeric float comparison rather than lexicographic string comparison.
"""
from __future__ import annotations

from PySide6.QtCore import Qt, QAbstractTableModel, QModelIndex, QMimeData

from src.domain.models import Monster


COLUMNS = ["Name", "CR", "Type", ""]


def _cr_to_float(cr: str) -> float:
    """Convert a CR string to a float for numeric sort ordering.

    Supported formats:
        '1/4' -> 0.25    '1/2' -> 0.5    '1/8' -> 0.125
        '0'   -> 0.0     '17'  -> 17.0
        '?'   -> -1.0    ''    -> -1.0    '—'   -> -1.0    '-' -> -1.0

    Unknown / unparseable values return -1.0 so they sort to the top and are
    easy to spot as incomplete entries.
    """
    cr = cr.strip()
    if not cr or cr in ("?", "—", "-"):
        return -1.0
    if "/" in cr:
        try:
            num, denom = cr.split("/", 1)
            return float(num) / float(denom)
        except (ValueError, ZeroDivisionError):
            return -1.0
    try:
        return float(cr)
    except ValueError:
        return -1.0


class MonsterTableModel(QAbstractTableModel):
    """4-column read-only table model backed by a list of Monster objects."""

    def __init__(self, monsters: list | None = None, parent=None) -> None:
        super().__init__(parent)
        self._monsters: list[Monster] = list(monsters) if monsters is not None else []

    # ------------------------------------------------------------------
    # Required QAbstractTableModel overrides
    # ------------------------------------------------------------------

    def rowCount(self, parent: QModelIndex = QModelIndex()) -> int:  # noqa: B008
        if parent.isValid():
            return 0
        return len(self._monsters)

    def columnCount(self, parent: QModelIndex = QModelIndex()) -> int:  # noqa: B008
        if parent.isValid():
            return 0
        return 4

    def data(self, index: QModelIndex, role: int = Qt.DisplayRole):
        if not index.isValid():
            return None
        row, col = index.row(), index.column()
        if row < 0 or row >= len(self._monsters):
            return None
        monster = self._monsters[row]

        if role == Qt.DisplayRole:
            if col == 0:
                return monster.name
            if col == 1:
                return monster.cr
            if col == 2:
                return monster.creature_type
            if col == 3:
                return "!" if monster.incomplete else ""
            return None

        if role == Qt.UserRole:
            if col == 0:
                # Lowercase string for case-insensitive name sort
                return monster.name.lower()
            if col == 1:
                return _cr_to_float(monster.cr)
            if col == 2:
                return monster.creature_type.lower()
            if col == 3:
                return 1 if monster.incomplete else 0
            return None

        return None

    def headerData(self, section: int, orientation: Qt.Orientation, role: int = Qt.DisplayRole):
        if role != Qt.DisplayRole:
            return None
        if orientation == Qt.Horizontal:
            if 0 <= section < len(COLUMNS):
                return COLUMNS[section]
        return None

    # ------------------------------------------------------------------
    # Custom methods
    # ------------------------------------------------------------------

    def reset_monsters(self, monsters: list) -> None:
        """Replace the internal list and notify all attached views.

        Calls beginResetModel / endResetModel so that proxy models and views
        discard stale persistent indices and re-query row/column counts.
        """
        self.beginResetModel()
        self._monsters = list(monsters)
        self.endResetModel()

    def monster_at(self, row: int) -> Monster:
        """Return the Monster at *row*.

        Used by LibraryTab to retrieve the selected Monster for detail display
        or editing.  Raises IndexError on out-of-range row.
        """
        return self._monsters[row]

    # ------------------------------------------------------------------
    # Drag support
    # ------------------------------------------------------------------

    def flags(self, index: QModelIndex) -> Qt.ItemFlag:
        base = super().flags(index)
        return base | Qt.ItemFlag.ItemIsDragEnabled

    def mimeTypes(self) -> list[str]:
        return ["application/x-monster-name"]

    def mimeData(self, indexes) -> QMimeData:
        mime = QMimeData()
        if indexes:
            # indexes may be multiple cells in same row — use first unique row
            rows = sorted({idx.row() for idx in indexes})
            row = rows[0]
            monster = self._monsters[row]
            mime.setData(
                "application/x-monster-name",
                monster.name.encode("utf-8"),
            )
        return mime
