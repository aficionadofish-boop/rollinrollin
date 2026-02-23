"""MonsterFilterProxyModel — QSortFilterProxyModel with AND-logic filtering.

Filters combine three independent criteria in AND fashion:
    1. Text search  — case-insensitive substring across name, cr, creature_type
    2. Type filter  — exact creature_type match (set via set_type_filter)
    3. Incomplete   — only show incomplete monsters (set via set_incomplete_only)

CR numeric sort:
    setSortRole(Qt.UserRole) delegates to MonsterTableModel.data(index, UserRole)
    which returns _cr_to_float(monster.cr) for column 1.  This makes '10' sort
    after '2' (float comparison) rather than before it (string comparison).
"""
from __future__ import annotations

from PySide6.QtCore import QSortFilterProxyModel, Qt, QModelIndex


class MonsterFilterProxyModel(QSortFilterProxyModel):
    """AND-logic proxy filter for the monster library table."""

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self._type_filter: str = ""
        self._incomplete_only: bool = False
        self.setFilterCaseSensitivity(Qt.CaseInsensitive)
        self.setSortRole(Qt.UserRole)  # numeric CR sort via _cr_to_float

    # ------------------------------------------------------------------
    # Filter setters
    # ------------------------------------------------------------------

    def set_type_filter(self, creature_type: str) -> None:
        """Set the creature_type equality filter.

        Pass an empty string to disable type filtering.
        Calls invalidate() to trigger a full sort+filter re-evaluation.
        """
        self._type_filter = creature_type
        self.invalidate()

    def set_incomplete_only(self, incomplete_only: bool) -> None:
        """When True, only monsters with incomplete=True are shown.

        Calls invalidate() to trigger a full sort+filter re-evaluation.
        """
        self._incomplete_only = incomplete_only
        self.invalidate()

    # ------------------------------------------------------------------
    # QSortFilterProxyModel override
    # ------------------------------------------------------------------

    def filterAcceptsRow(self, source_row: int, source_parent: QModelIndex) -> bool:  # noqa: N802
        """Return True if the row at *source_row* passes all active filters."""
        model = self.sourceModel()
        monster = model._monsters[source_row]

        # --- Text search (AND across name, cr, creature_type) ---
        text = self.filterRegularExpression().pattern()
        if text:
            searchable = f"{monster.name} {monster.cr} {monster.creature_type}"
            if text.lower() not in searchable.lower():
                return False

        # --- Type dropdown filter ---
        if self._type_filter:
            if monster.creature_type.lower() != self._type_filter.lower():
                return False

        # --- Incomplete-only toggle ---
        if self._incomplete_only and not monster.incomplete:
            return False

        return True
