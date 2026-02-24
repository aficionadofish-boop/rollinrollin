"""RollOutputPanel — read-only roll log panel with clipboard copy button.

A QWidget that contains a read-only QTextEdit for streaming roll results
and a "Copy to Clipboard" button below it.  Reusable across any rolling tab.
"""
from __future__ import annotations

from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QTextEdit,
    QPushButton,
    QLabel,
    QApplication,
)


class RollOutputPanel(QWidget):
    """Read-only roll result log with a Copy to Clipboard button.

    Public API
    ----------
    append(text)       -- Append one line to the log.
    clear()            -- Clear all log content.
    to_plain_text()    -- Return current log text as a plain string.
    """

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        self._text_edit = QTextEdit()
        self._text_edit.setReadOnly(True)
        self._text_edit.setPlaceholderText("Roll results will appear here...")
        self._text_edit.setMinimumHeight(150)
        layout.addWidget(self._text_edit)

        btn_row = QHBoxLayout()
        self._seeded_label = QLabel("Seeded")
        self._seeded_label.setStyleSheet(
            "background-color: #3A5F3A; color: #8FBC8F; "
            "padding: 2px 8px; border-radius: 3px; font-size: 11px;"
        )
        self._seeded_label.setVisible(False)
        btn_row.addWidget(self._seeded_label)
        btn_row.addStretch()
        self._copy_btn = QPushButton("Copy to Clipboard")
        self._copy_btn.clicked.connect(self._copy_to_clipboard)
        btn_row.addWidget(self._copy_btn)
        layout.addLayout(btn_row)

    def append(self, text: str) -> None:
        """Append a line of text to the log and scroll to it."""
        self._text_edit.append(text)
        self._text_edit.ensureCursorVisible()

    def clear(self) -> None:
        """Clear all log content."""
        self._text_edit.clear()

    def to_plain_text(self) -> str:
        """Return the current log content as a plain string."""
        return self._text_edit.toPlainText()

    def set_seeded_mode(self, enabled: bool) -> None:
        """Show or hide the 'Seeded' badge indicator."""
        self._seeded_label.setVisible(enabled)

    def _copy_to_clipboard(self) -> None:
        """Write current log text to the system clipboard."""
        text = self._text_edit.toPlainText()
        if text:
            QApplication.clipboard().setText(text)
