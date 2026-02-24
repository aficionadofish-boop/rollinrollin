"""MacroEditor — code-editor-like QPlainTextEdit with line number gutter and syntax highlighting.

Contains:
  MacroHighlighter  — QSyntaxHighlighter subclass; colors Roll20 macro tokens
  LineNumberArea    — QWidget that paints the line-number gutter
  MacroEditor       — QPlainTextEdit subclass with line numbers, highlighter, and debounce timer
"""
from __future__ import annotations

import re

from PySide6.QtCore import QRect, QSize, Qt, QTimer
from PySide6.QtGui import (
    QColor,
    QFont,
    QFontMetrics,
    QPainter,
    QSyntaxHighlighter,
    QTextCharFormat,
)
from PySide6.QtWidgets import QPlainTextEdit, QTextEdit, QWidget


# ---------------------------------------------------------------------------
# MacroHighlighter
# ---------------------------------------------------------------------------

class MacroHighlighter(QSyntaxHighlighter):
    """Token-based syntax highlighter for Roll20 macro text.

    Colors:
      [[...]]                 — blue bold  (#4DA6FF)
      ?{...}                  — orange     (#FF9900)
      @{...} / &{template:..} — red underline (#FF4444)
    """

    def __init__(self, document) -> None:
        super().__init__(document)

        # Inline roll: [[...]] — blue bold
        self._inline_fmt = QTextCharFormat()
        self._inline_fmt.setForeground(QColor("#4DA6FF"))
        self._inline_fmt.setFontWeight(QFont.Weight.Bold)

        # Query: ?{...} — orange
        self._query_fmt = QTextCharFormat()
        self._query_fmt.setForeground(QColor("#FF9900"))

        # Unsupported: @{...} and &{template:...} — red underline
        self._warn_fmt = QTextCharFormat()
        self._warn_fmt.setForeground(QColor("#FF4444"))
        self._warn_fmt.setFontUnderline(True)

        self._rules: list[tuple[re.Pattern, QTextCharFormat]] = [
            (re.compile(r"\[\[[^\]]*\]\]"), self._inline_fmt),
            (re.compile(r"\?\{[^}]*\}"), self._query_fmt),
            (re.compile(r"@\{[^}]*\}|&\{template:[^}]*\}"), self._warn_fmt),
        ]

    def highlightBlock(self, text: str) -> None:  # noqa: N802 — Qt naming convention
        for pattern, fmt in self._rules:
            for m in pattern.finditer(text):
                self.setFormat(m.start(), m.end() - m.start(), fmt)


# ---------------------------------------------------------------------------
# LineNumberArea
# ---------------------------------------------------------------------------

class LineNumberArea(QWidget):
    """Narrow gutter widget painted on the left side of MacroEditor.

    Delegates all painting to MacroEditor.line_number_area_paint_event().
    """

    def __init__(self, editor: "MacroEditor") -> None:
        super().__init__(editor)
        self._editor = editor

    def sizeHint(self) -> QSize:  # noqa: N802
        return QSize(self._editor._line_number_area_width(), 0)

    def paintEvent(self, event) -> None:  # noqa: N802
        self._editor.line_number_area_paint_event(event)


# ---------------------------------------------------------------------------
# MacroEditor
# ---------------------------------------------------------------------------

class MacroEditor(QPlainTextEdit):
    """Code-editor-like plain text input for Roll20 macros.

    Features:
    - Monospace font (Courier New 10pt)
    - 4-space tab stops
    - Placeholder text
    - Line number gutter (LineNumberArea)
    - Syntax highlighting via MacroHighlighter
    - Debounced full-document rehighlight (1.5 s after last keystroke)
    - Current-line highlight
    """

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)

        # --- Font ---
        font = QFont("Courier New", 10)
        self.setFont(font)
        self.setTabStopDistance(4 * QFontMetrics(self.font()).horizontalAdvance(" "))
        self.setPlaceholderText("Type or paste a Roll20 macro...")

        # --- Syntax highlighter ---
        self._highlighter = MacroHighlighter(self.document())

        # --- Line number area ---
        self._line_number_area = LineNumberArea(self)

        # --- Signals for line number area ---
        self.blockCountChanged.connect(self._update_line_number_area_width)
        self.updateRequest.connect(self._update_line_number_area)
        self.cursorPositionChanged.connect(self._highlight_current_line)

        # Set initial margins
        self._update_line_number_area_width(0)
        self._highlight_current_line()

        # --- Debounce timer for full-document rehighlight ---
        # QSyntaxHighlighter.highlightBlock() fires automatically per block
        # on each document change, so per-keystroke highlighting is instant.
        # The timer triggers an explicit rehighlight() for warning-sweep passes
        # only after the user stops typing for 1.5 seconds.
        self._debounce_timer = QTimer(self)
        self._debounce_timer.setSingleShot(True)
        self._debounce_timer.setInterval(1500)
        self._debounce_timer.timeout.connect(self._highlighter.rehighlight)
        self.textChanged.connect(self._debounce_timer.start)

    # ------------------------------------------------------------------
    # Line number gutter helpers
    # ------------------------------------------------------------------

    def _line_number_area_width(self) -> int:
        """Return the pixel width required for the line number gutter."""
        digits = len(str(max(1, self.blockCount())))
        char_width = self.fontMetrics().horizontalAdvance("9")
        return 6 + digits * char_width

    def _update_line_number_area_width(self, _: int = 0) -> None:
        """Adjust viewport left margin to make room for the line number gutter."""
        self.setViewportMargins(self._line_number_area_width(), 0, 0, 0)

    def _update_line_number_area(self, rect: QRect, dy: int) -> None:
        """Scroll or repaint the line number area in response to viewport updates."""
        if dy:
            self._line_number_area.scroll(0, dy)
        else:
            self._line_number_area.update(
                0, rect.y(), self._line_number_area.width(), rect.height()
            )
        if rect.contains(self.viewport().rect()):
            self._update_line_number_area_width()

    def resizeEvent(self, event) -> None:  # noqa: N802
        super().resizeEvent(event)
        cr = self.contentsRect()
        self._line_number_area.setGeometry(
            cr.left(), cr.top(), self._line_number_area_width(), cr.height()
        )

    def _highlight_current_line(self) -> None:
        """Draw a subtle background highlight on the line containing the cursor."""
        selections: list[QTextEdit.ExtraSelection] = []
        if not self.isReadOnly():
            selection = QTextEdit.ExtraSelection()
            line_color = QColor("#2A2A2A")
            selection.format.setBackground(line_color)
            selection.format.setProperty(
                QTextEdit.ExtraSelection.FullWidthSelection
                if hasattr(QTextEdit.ExtraSelection, "FullWidthSelection")
                else 0x100000,  # Qt::TextFormat::FullWidthSelection
                True,
            )
            selection.cursor = self.textCursor()
            selection.cursor.clearSelection()
            selections.append(selection)
        self.setExtraSelections(selections)

    def line_number_area_paint_event(self, event) -> None:
        """Paint line numbers in the gutter. Called by LineNumberArea.paintEvent()."""
        painter = QPainter(self._line_number_area)
        painter.fillRect(event.rect(), QColor("#1E1E1E"))

        block = self.firstVisibleBlock()
        block_number = block.blockNumber()
        top = int(
            self.blockBoundingGeometry(block).translated(self.contentOffset()).top()
        )
        bottom = top + int(self.blockBoundingRect(block).height())

        gutter_width = self._line_number_area.width()

        while block.isValid() and top <= event.rect().bottom():
            if block.isVisible() and bottom >= event.rect().top():
                number = str(block_number + 1)
                painter.setPen(QColor("#858585"))
                painter.drawText(
                    0,
                    top,
                    gutter_width - 3,
                    self.fontMetrics().height(),
                    Qt.AlignmentFlag.AlignRight,
                    number,
                )
            block = block.next()
            block_number += 1
            top = bottom
            bottom = top + int(self.blockBoundingRect(block).height())
