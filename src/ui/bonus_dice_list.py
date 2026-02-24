from PySide6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLineEdit, QPushButton


class BonusDiceList(QWidget):
    """Dynamic bonus dice row list.

    Users click '+' to add a row with formula and label QLineEdits.
    Each row has a '-' button to remove it.
    get_entries() returns a BonusDiceEntry for each non-empty formula row.
    """

    def __init__(self, parent=None):
        super().__init__(parent)
        self._layout = QVBoxLayout(self)
        self._rows: list[tuple] = []  # (formula_edit, label_edit, row_widget)
        add_btn = QPushButton("+")
        add_btn.setMaximumWidth(30)
        add_btn.clicked.connect(self._add_row)
        self._layout.addWidget(add_btn)
        self._add_btn = add_btn

    def _add_row(self):
        row_widget = QWidget()
        row_layout = QHBoxLayout(row_widget)
        row_layout.setContentsMargins(0, 0, 0, 0)
        formula_edit = QLineEdit()
        formula_edit.setPlaceholderText("+1d4")
        formula_edit.setMaximumWidth(80)
        label_edit = QLineEdit()
        label_edit.setPlaceholderText("Bless")
        remove_btn = QPushButton("\u2212")
        remove_btn.setMaximumWidth(24)
        row_layout.addWidget(formula_edit)
        row_layout.addWidget(label_edit)
        row_layout.addWidget(remove_btn)
        self._layout.insertWidget(self._layout.count() - 1, row_widget)
        entry = (formula_edit, label_edit, row_widget)
        self._rows.append(entry)
        remove_btn.clicked.connect(lambda: self._remove_row(entry))

    def _remove_row(self, entry):
        if entry in self._rows:
            self._rows.remove(entry)
            entry[2].deleteLater()

    def get_entries(self) -> list:
        """Return list[BonusDiceEntry] for each non-empty formula row."""
        from src.roll.models import BonusDiceEntry
        entries = []
        for (formula_edit, label_edit, _) in self._rows:
            formula = formula_edit.text().strip()
            if formula:
                label = label_edit.text().strip()
                entries.append(BonusDiceEntry(formula=formula, label=label))
        return entries
