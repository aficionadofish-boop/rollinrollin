"""LoadEncounterDialog — modal dialog for selecting and deleting saved encounters."""
from __future__ import annotations

from PySide6.QtWidgets import (
    QDialog,
    QVBoxLayout,
    QHBoxLayout,
    QListWidget,
    QPushButton,
    QLabel,
)
from PySide6.QtCore import Qt


class LoadEncounterDialog(QDialog):
    """Modal dialog for loading or deleting a saved encounter.

    Args:
        saved_encounters: list of encounter dicts, each with keys:
            - name (str)
            - members (list[dict] with 'name' and 'count')
            - saved_at (str, ISO timestamp)
        parent: optional parent widget
    """

    def __init__(self, saved_encounters: list[dict], parent=None) -> None:
        super().__init__(parent)
        self.setWindowTitle("Load Encounter")
        self.setModal(True)
        self.resize(400, 300)

        self._saved = saved_encounters
        self._selected_index: int | None = None
        self._deleted_indices: list[int] = []
        # Map from current list widget row to original saved_encounters index
        self._row_to_original: list[int] = list(range(len(saved_encounters)))

        self._setup_ui()
        self._update_buttons()

    # ------------------------------------------------------------------
    # UI Construction
    # ------------------------------------------------------------------

    def _setup_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setSpacing(8)

        # Title label
        title = QLabel("Select an encounter to load:")
        layout.addWidget(title)

        # List widget
        self._list = QListWidget()
        self._list.setSelectionMode(QListWidget.SelectionMode.SingleSelection)
        for enc in self._saved:
            name = enc.get("name", "Untitled")
            members = enc.get("members", [])
            n_creatures = sum(m.get("count", 1) for m in members)
            saved_at = enc.get("saved_at", "")
            date_str = saved_at[:10] if saved_at else "unknown"
            self._list.addItem(f"{name} \u2014 {n_creatures} creature{'s' if n_creatures != 1 else ''} \u2014 {date_str}")

        self._list.currentRowChanged.connect(self._on_selection_changed)
        self._list.itemDoubleClicked.connect(self._on_double_click)
        layout.addWidget(self._list)

        # Button row
        btn_row = QHBoxLayout()
        self._load_btn = QPushButton("Load")
        self._load_btn.setDefault(True)
        self._load_btn.clicked.connect(self._on_load)

        self._delete_btn = QPushButton("Delete")
        self._delete_btn.clicked.connect(self._on_delete)

        cancel_btn = QPushButton("Cancel")
        cancel_btn.clicked.connect(self.reject)

        btn_row.addWidget(self._load_btn)
        btn_row.addWidget(self._delete_btn)
        btn_row.addStretch()
        btn_row.addWidget(cancel_btn)
        layout.addLayout(btn_row)

    # ------------------------------------------------------------------
    # Slots
    # ------------------------------------------------------------------

    def _on_selection_changed(self, row: int) -> None:
        self._update_buttons()

    def _on_double_click(self, item) -> None:
        self._on_load()

    def _on_load(self) -> None:
        row = self._list.currentRow()
        if row < 0 or row >= len(self._row_to_original):
            return
        self._selected_index = self._row_to_original[row]
        self.accept()

    def _on_delete(self) -> None:
        row = self._list.currentRow()
        if row < 0 or row >= len(self._row_to_original):
            return
        original_idx = self._row_to_original[row]
        self._deleted_indices.append(original_idx)
        self._list.takeItem(row)
        self._row_to_original.pop(row)
        # Select nearby item
        new_count = self._list.count()
        if new_count > 0:
            self._list.setCurrentRow(min(row, new_count - 1))
        self._update_buttons()

    def _update_buttons(self) -> None:
        has_selection = self._list.currentRow() >= 0
        self._load_btn.setEnabled(has_selection)
        self._delete_btn.setEnabled(has_selection)

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def selected_index(self) -> int | None:
        """Return original saved_encounters index of the encounter to load, or None."""
        return self._selected_index

    def deleted_indices(self) -> list[int]:
        """Return list of original saved_encounters indices that were deleted."""
        return list(self._deleted_indices)
