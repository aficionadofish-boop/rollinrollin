"""CombatLogPanel — timestamped log panel with copy-to-clipboard and clear."""
from __future__ import annotations

from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QTextEdit,
    QApplication,
)
from PySide6.QtGui import QFont


class CombatLogPanel(QWidget):
    """Scrolling combat log panel shown on the right side of the CombatTrackerTab.

    All events — HP changes, condition changes, turn transitions — are appended
    as plain-text lines prefixed with the current round number.

    Public API:
        add_entry(text)            -- append one line
        add_entries(entries)       -- append multiple lines
        set_round(round_number)    -- update round prefix
        load_entries(entries)      -- bulk-load pre-formatted lines (persistence restore)
        get_entries() -> list[str] -- return all log lines for persistence
    """

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self._current_round: int = 1
        self._entries: list[str] = []
        self._build_layout()

    # ------------------------------------------------------------------
    # Layout
    # ------------------------------------------------------------------

    def _build_layout(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(4, 4, 4, 4)
        layout.setSpacing(4)

        # Header row
        header_row = QHBoxLayout()

        header_label = QLabel("Combat Log")
        header_font = QFont()
        header_font.setBold(True)
        header_label.setFont(header_font)

        copy_btn = QPushButton("Copy")
        copy_btn.setFixedHeight(24)
        copy_btn.setToolTip("Copy log to clipboard")
        copy_btn.clicked.connect(self._copy_to_clipboard)

        clear_btn = QPushButton("Clear")
        clear_btn.setFixedHeight(24)
        clear_btn.setToolTip("Clear log")
        clear_btn.clicked.connect(self._clear_log)

        header_row.addWidget(header_label)
        header_row.addStretch()
        header_row.addWidget(copy_btn)
        header_row.addWidget(clear_btn)

        layout.addLayout(header_row)

        # Log display
        self._log_text = QTextEdit()
        self._log_text.setReadOnly(True)
        mono_font = QFont("Consolas")
        if not mono_font.exactMatch():
            mono_font = QFont("Courier New")
        mono_font.setPointSize(9)
        self._log_text.setFont(mono_font)

        layout.addWidget(self._log_text, 1)

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def set_round(self, round_number: int) -> None:
        """Store current round number for use as log line prefix."""
        self._current_round = round_number

    def add_entry(self, text: str) -> None:
        """Append a timestamped line to the log."""
        line = f"[Round {self._current_round}] {text}"
        self._entries.append(line)
        self._log_text.append(line)
        # Scroll to bottom
        scrollbar = self._log_text.verticalScrollBar()
        scrollbar.setValue(scrollbar.maximum())

    def add_entries(self, entries: list[str]) -> None:
        """Append multiple lines."""
        for entry in entries:
            self.add_entry(entry)

    def load_entries(self, entries: list[str]) -> None:
        """Bulk-load pre-formatted log lines from persistence (no round prefix added)."""
        self._entries = list(entries)
        self._log_text.clear()
        for line in self._entries:
            self._log_text.append(line)
        # Scroll to bottom
        scrollbar = self._log_text.verticalScrollBar()
        scrollbar.setValue(scrollbar.maximum())

    def get_entries(self) -> list[str]:
        """Return all log entries as a list for persistence."""
        return list(self._entries)

    # ------------------------------------------------------------------
    # Private slots
    # ------------------------------------------------------------------

    def _copy_to_clipboard(self) -> None:
        QApplication.clipboard().setText(self._log_text.toPlainText())

    def _clear_log(self) -> None:
        self._entries = []
        self._log_text.clear()
