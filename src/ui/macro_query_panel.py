"""QueryPanel — inline widget for sequential ?{query} resolution.

Presents Roll20 ?{prompt|opt,val|...} queries one at a time without using
QDialog.exec() or any nested event loop.  The panel is a hidden QWidget that
becomes visible when start() is called and hides itself after the last query
is answered, emitting answered(dict) with the collected values.

Critical design requirement: NO QDialog.exec() usage anywhere in this file.
The panel drives its sequential flow entirely through signal/slot connections.
"""
from __future__ import annotations

from PySide6.QtCore import Signal
from PySide6.QtGui import QFont
from PySide6.QtWidgets import (
    QComboBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QSizePolicy,
    QStackedWidget,
    QVBoxLayout,
    QWidget,
)


class QueryPanel(QWidget):
    """Inline query-resolution widget for Roll20 ?{...} tokens.

    Usage
    -----
    panel = QueryPanel(parent=some_widget)
    panel.answered.connect(my_slot)          # dict[raw_token -> chosen_value]
    panel.start(queries)                     # list of QuerySpec (duck-typed)

    The panel shows itself, presents queries one at a time, then hides itself
    and emits answered(dict) when the last query is resolved.

    Previous answers are remembered per prompt text for the lifetime of the
    panel instance (in-memory, not persisted across sessions).
    """

    # Emitted when all queries are answered.
    # dict maps raw token string (e.g. '?{Save|STR,+2|DEX,+4}') -> chosen value string
    answered = Signal(dict)

    # Index into QStackedWidget pages
    _PAGE_COMBO = 0
    _PAGE_LINE = 1

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setVisible(False)

        # --- State ---
        self._queries: list = []               # list of QuerySpec (duck-typed)
        self._answers: dict[str, str] = {}     # raw_token -> chosen_value (current run)
        self._idx: int = 0
        self._previous_answers: dict[str, str] = {}  # prompt text -> last chosen value/label

        # --- Layout ---
        root = QVBoxLayout(self)
        root.setContentsMargins(8, 6, 8, 6)
        root.setSpacing(6)

        # Prompt label (bold, slightly larger)
        self._prompt_label = QLabel()
        prompt_font = QFont(self._prompt_label.font())
        prompt_font.setBold(True)
        prompt_font.setPointSize(prompt_font.pointSize() + 1)
        self._prompt_label.setFont(prompt_font)
        self._prompt_label.setWordWrap(True)
        root.addWidget(self._prompt_label)

        # Stacked widget: page 0 = QComboBox, page 1 = QLineEdit
        self._stack = QStackedWidget()
        self._combo = QComboBox()
        self._line_edit = QLineEdit()
        self._line_edit.setPlaceholderText("Enter value...")
        self._stack.addWidget(self._combo)    # index 0
        self._stack.addWidget(self._line_edit)  # index 1
        root.addWidget(self._stack)

        # Button row
        btn_row = QHBoxLayout()
        btn_row.setContentsMargins(0, 0, 0, 0)
        btn_row.addStretch()
        self._next_btn = QPushButton("Next")
        self._next_btn.setSizePolicy(
            QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed
        )
        self._next_btn.clicked.connect(self._on_next)
        btn_row.addWidget(self._next_btn)
        root.addLayout(btn_row)

        # Frame / border so the panel is visually distinct
        self.setStyleSheet(
            "QueryPanel { border: 1px solid #555; border-radius: 4px; "
            "background-color: #252525; }"
        )

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def start(self, queries: list) -> None:
        """Begin presenting queries sequentially.

        Parameters
        ----------
        queries:
            A list of objects with .prompt (str), .options (list of
            (label, value) tuples — empty for free-text), and .raw (str).
            Typically list[QuerySpec] from src.macro.preprocessor.
        """
        self._queries = list(queries)
        self._answers = {}
        self._idx = 0
        if not self._queries:
            # Nothing to ask — emit immediately without showing
            self.answered.emit({})
            return
        self._show_current()
        self.setVisible(True)

    def reset(self) -> None:
        """Hide the panel and clear run-state (previous answers are preserved)."""
        self.setVisible(False)
        self._queries = []
        self._answers = {}
        self._idx = 0
        # _previous_answers intentionally NOT cleared — persists for session

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _show_current(self) -> None:
        """Render the current query (self._idx) into the UI."""
        q = self._queries[self._idx]
        self._prompt_label.setText(q.prompt)

        is_last = self._idx == len(self._queries) - 1
        self._next_btn.setText("Roll" if is_last else "Next")

        if q.options:
            # Dropdown mode
            self._stack.setCurrentIndex(self._PAGE_COMBO)
            self._combo.blockSignals(True)
            self._combo.clear()
            prev_label = self._previous_answers.get(q.prompt)
            restore_idx = 0
            for i, (label, value) in enumerate(q.options):
                self._combo.addItem(label, value)
                if prev_label is not None and label == prev_label:
                    restore_idx = i
            if prev_label is not None:
                self._combo.setCurrentIndex(restore_idx)
            self._combo.blockSignals(False)
        else:
            # Free-text mode
            self._stack.setCurrentIndex(self._PAGE_LINE)
            prev_text = self._previous_answers.get(q.prompt, "")
            self._line_edit.setText(prev_text)

    def _on_next(self) -> None:
        """Collect current answer and advance to the next query (or finish)."""
        q = self._queries[self._idx]

        if q.options:
            # Dropdown: userData holds the substitution value; text is the label
            value = self._combo.currentData()
            label = self._combo.currentText()
            # Remember the label for pre-selection on re-roll
            self._previous_answers[q.prompt] = label
        else:
            # Free-text
            value = self._line_edit.text()
            self._previous_answers[q.prompt] = value

        self._answers[q.raw] = value
        self._idx += 1

        if self._idx >= len(self._queries):
            # All queries answered
            self.setVisible(False)
            self.answered.emit(dict(self._answers))
        else:
            self._show_current()
