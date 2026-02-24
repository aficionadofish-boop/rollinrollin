from PySide6.QtWidgets import QWidget, QHBoxLayout, QPushButton
from PySide6.QtCore import Signal


class ToggleBar(QWidget):
    """Exclusive multi-button toggle bar (like a radio group).

    Emits value_changed(str) with the label of the newly selected button.
    Mutual exclusivity is enforced: clicking one button unchecks all others.
    """
    value_changed = Signal(str)

    def __init__(self, options: list[str], default: str = None, parent=None):
        super().__init__(parent)
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        self._buttons: dict[str, QPushButton] = {}
        for label in options:
            btn = QPushButton(label)
            btn.setCheckable(True)
            btn.clicked.connect(lambda checked, l=label: self._on_click(l))
            layout.addWidget(btn)
            self._buttons[label] = btn
        first = default if default in self._buttons else options[0]
        self._buttons[first].setChecked(True)
        self._current = first

    def _on_click(self, label: str) -> None:
        for lbl, btn in self._buttons.items():
            btn.setChecked(lbl == label)
        self._current = label
        self.value_changed.emit(label)

    def value(self) -> str:
        """Return the currently selected label string."""
        return self._current

    def set_value(self, label: str) -> None:
        """Set selection to label and emit value_changed signal."""
        if label in self._buttons:
            self._on_click(label)
