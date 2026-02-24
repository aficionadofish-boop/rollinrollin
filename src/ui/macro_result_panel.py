"""macro_result_panel.py — Scrollable numbered result cards for macro roll output.

Contains:
  ResultCard   — Collapsible QFrame card showing one MacroLineResult
  ResultPanel  — Scroll area collecting roll sets with auto-trim and copy-all
"""
from __future__ import annotations

from datetime import datetime

from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QColor, QFont
from PySide6.QtWidgets import (
    QApplication,
    QFrame,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QScrollArea,
    QSizePolicy,
    QVBoxLayout,
    QWidget,
)

from src.macro.models import MacroLineResult, MacroRollResult


# ---------------------------------------------------------------------------
# Face formatting helpers
# ---------------------------------------------------------------------------

def _face_plain(f) -> str:
    """Plain text representation of a DieFace (for tooltips and clipboard)."""
    text = f"d{f.sides}: {f.value}"
    annotations = []
    if not f.kept:
        annotations.append("dropped")
    if f.exploded:
        annotations.append("exploded")
    if f.critical:
        annotations.append("CRIT")
    if annotations:
        text += f" ({', '.join(annotations)})"
    return text


def _face_rich(f) -> str:
    """HTML-formatted DieFace for rich text QLabel display."""
    text = f"d{f.sides}: {f.value}"
    if not f.kept:
        text += " (dropped)"
    if f.exploded:
        text += " (exploded)"
    if f.critical:
        return f'<span style="color: #00CC00;">{text} &#9733;</span>'
    if not f.kept:
        return f'<span style="color: #888888;">{text}</span>'
    return text


# ---------------------------------------------------------------------------
# ResultCard
# ---------------------------------------------------------------------------

class ResultCard(QFrame):
    """One collapsible result card showing a single MacroLineResult.

    Layout
    ------
    Header row:  #N badge | Total (bold) or error label | warnings | [+/-] [Copy]
    Warning row: one label per MacroWarning (orange) — hidden if no warnings
    Detail section (collapsed by default):
      - Expression
      - Per-die breakdown
      - Constant bonus (if nonzero)
      - Inline roll breakdown (if any)
    """

    def __init__(self, line_result: MacroLineResult, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._line_result = line_result
        self.setFrameShape(QFrame.Shape.StyledPanel)
        self.setFrameShadow(QFrame.Shadow.Raised)

        root = QVBoxLayout(self)
        root.setContentsMargins(6, 4, 6, 4)
        root.setSpacing(2)

        # ---- Header row ------------------------------------------------
        header = QHBoxLayout()
        header.setSpacing(6)

        # Line number badge
        badge = QLabel(f"#{line_result.line_number}")
        badge_font = QFont(badge.font())
        badge_font.setBold(True)
        badge.setFont(badge_font)
        badge.setStyleSheet("color: #AAAAAA;")
        header.addWidget(badge)

        # Template name (shown before total/error if present)
        if line_result.template_name:
            name_label = QLabel(line_result.template_name)
            name_font = QFont(name_label.font())
            name_font.setBold(True)
            name_label.setFont(name_font)
            name_label.setStyleSheet("color: #4DA6FF;")
            name_label.setWordWrap(True)
            header.addWidget(name_label)

        if line_result.has_result:
            total_label = QLabel(f"Total: {line_result.dice_result.total}")
            total_font = QFont(total_label.font())
            total_font.setBold(True)
            total_font.setPointSize(total_font.pointSize() + 2)
            total_label.setFont(total_font)
            total_label.setStyleSheet("color: #FFFFFF;")
            header.addWidget(total_label)
        elif line_result.error:
            err_label = QLabel(f"Error: {line_result.error}")
            err_label.setStyleSheet("color: #FF4444;")
            err_label.setWordWrap(True)
            header.addWidget(err_label)

        header.addStretch()

        # Expand/collapse toggle
        self._toggle_btn = QPushButton("+")
        self._toggle_btn.setFixedSize(24, 24)
        self._toggle_btn.setToolTip("Expand / collapse details")
        self._toggle_btn.clicked.connect(self._toggle_detail)
        header.addWidget(self._toggle_btn)

        # Per-card copy button
        copy_btn = QPushButton("Copy")
        copy_btn.setFixedHeight(24)
        copy_btn.setToolTip("Copy this result to clipboard")
        copy_btn.clicked.connect(self._copy_card)
        header.addWidget(copy_btn)

        root.addLayout(header)

        # ---- Warning row -----------------------------------------------
        if line_result.has_warnings:
            for w in line_result.warnings:
                warn_label = QLabel(f"Warning: {w.token} — {w.reason}")
                warn_label.setStyleSheet("color: #FF9900;")
                warn_label.setWordWrap(True)
                root.addWidget(warn_label)

        # For template-only results, show inline rolls directly in the card
        # (not hidden in the detail section) since they ARE the main results.
        is_template_only = line_result.has_inline_only

        if is_template_only and line_result.inline_results:
            for original_expr, dice_result in line_result.inline_results:
                tooltip_parts = [_face_plain(f) for f in dice_result.faces]
                if dice_result.constant_bonus != 0:
                    tooltip_parts.append(f"constant: {dice_result.constant_bonus:+d}")
                tooltip = "\n".join(tooltip_parts) if tooltip_parts else "No dice faces"

                inline_label = QLabel(f"  {original_expr} = {dice_result.total}")
                inline_label.setStyleSheet("color: #4DA6FF;")
                inline_label.setToolTip(tooltip)
                root.addWidget(inline_label)

        # ---- Detail section (collapsed by default) ---------------------
        self._detail = QWidget()
        self._detail.setVisible(False)
        detail_layout = QVBoxLayout(self._detail)
        detail_layout.setContentsMargins(8, 2, 0, 2)
        detail_layout.setSpacing(2)

        if line_result.has_result:
            dr = line_result.dice_result

            expr_label = QLabel(f"Expression: {dr.expression}")
            expr_label.setStyleSheet("color: #CCCCCC;")
            detail_layout.addWidget(expr_label)

            if dr.faces:
                face_parts = [_face_rich(f) for f in dr.faces]
                faces_html = "&nbsp;&nbsp;".join(face_parts)
                faces_label = QLabel(f"Dice: {faces_html}")
                faces_label.setTextFormat(Qt.TextFormat.RichText)
                faces_label.setStyleSheet("color: #CCCCCC;")
                faces_label.setWordWrap(True)
                detail_layout.addWidget(faces_label)

            if dr.constant_bonus != 0:
                const_label = QLabel(f"Constant: {dr.constant_bonus:+d}")
                const_label.setStyleSheet("color: #CCCCCC;")
                detail_layout.addWidget(const_label)

        # Show inline rolls in detail section for non-template results
        if not is_template_only and line_result.inline_results:
            inline_header = QLabel("Inline rolls:")
            inline_header.setStyleSheet("color: #BBBBBB;")
            detail_layout.addWidget(inline_header)
            for original_expr, dice_result in line_result.inline_results:
                tooltip_parts = [_face_plain(f) for f in dice_result.faces]
                if dice_result.constant_bonus != 0:
                    tooltip_parts.append(f"constant: {dice_result.constant_bonus:+d}")
                tooltip = "\n".join(tooltip_parts) if tooltip_parts else "No dice faces"

                inline_label = QLabel(f"  {original_expr} = {dice_result.total}")
                inline_label.setStyleSheet("color: #4DA6FF;")
                inline_label.setToolTip(tooltip)
                detail_layout.addWidget(inline_label)

        root.addWidget(self._detail)

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    def _toggle_detail(self) -> None:
        visible = not self._detail.isVisible()
        self._detail.setVisible(visible)
        self._toggle_btn.setText("-" if visible else "+")

    def _copy_card(self) -> None:
        QApplication.clipboard().setText(self.to_text())

    def to_text(self) -> str:
        """Plain text representation of this result card for clipboard copy."""
        lr = self._line_result
        header = f"#{lr.line_number}"
        if lr.template_name:
            header += f" {lr.template_name}"
        lines: list[str] = [header]

        if lr.has_result:
            dr = lr.dice_result
            lines.append(f"  Total: {dr.total}")
            lines.append(f"  Expression: {dr.expression}")
            if dr.faces:
                face_parts = [_face_plain(f) for f in dr.faces]
                lines.append(f"  Dice: {', '.join(face_parts)}")
            if dr.constant_bonus != 0:
                lines.append(f"  Constant: {dr.constant_bonus:+d}")
        elif lr.error:
            lines.append(f"  Error: {lr.error}")

        for w in lr.warnings:
            lines.append(f"  Warning: {w.token} — {w.reason}")

        if lr.inline_results:
            for original_expr, dice_result in lr.inline_results:
                lines.append(f"  Inline: {original_expr} = {dice_result.total}")

        return "\n".join(lines)


# ---------------------------------------------------------------------------
# ResultPanel
# ---------------------------------------------------------------------------

class ResultPanel(QWidget):
    """Scrollable panel that accumulates result cards from multiple roll sets.

    Each call to add_roll_result() inserts a timestamp divider and one or more
    ResultCard widgets.  Auto-trims to a maximum of 20 roll sets.

    Public API
    ----------
    add_roll_result(roll_result)  — append a new roll set
    clear()                       — remove all content and reset counter
    """

    _MAX_ROLL_SETS = 20

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)

        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        # ---- Toolbar row -----------------------------------------------
        toolbar = QHBoxLayout()
        toolbar.setContentsMargins(4, 4, 4, 4)
        toolbar.setSpacing(6)

        copy_all_btn = QPushButton("Copy All")
        copy_all_btn.setToolTip("Copy all visible results to clipboard")
        copy_all_btn.clicked.connect(self._copy_all)
        toolbar.addWidget(copy_all_btn)

        clear_btn = QPushButton("Clear Results")
        clear_btn.setToolTip("Remove all result cards")
        clear_btn.clicked.connect(self.clear)
        toolbar.addWidget(clear_btn)

        toolbar.addStretch()
        root.addLayout(toolbar)

        # ---- Scroll area -----------------------------------------------
        self._scroll = QScrollArea()
        self._scroll.setWidgetResizable(True)
        self._scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)

        self._container = QWidget()
        self._layout = QVBoxLayout(self._container)
        self._layout.setContentsMargins(4, 4, 4, 4)
        self._layout.setSpacing(4)
        self._layout.addStretch()  # keeps cards pushed to top

        self._scroll.setWidget(self._container)
        root.addWidget(self._scroll)

        self._roll_set_count = 0
        # Track (divider_widget, [card_widget, ...]) for auto-trim
        self._roll_sets: list[tuple[QWidget, list[QWidget]]] = []
        self._seeded_mode: bool = False

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def set_seeded_mode(self, enabled: bool) -> None:
        """Show or hide the seeded indicator on future roll results."""
        self._seeded_mode = enabled

    def add_roll_result(self, roll_result: MacroRollResult) -> None:
        """Append a new roll set with timestamp divider."""
        self._roll_set_count += 1

        # Insert before the trailing stretch (last item)
        insert_at = self._layout.count() - 1  # position before stretch

        # Timestamp divider
        now = datetime.now().strftime("%H:%M:%S")
        seeded_suffix = " [seeded]" if self._seeded_mode else ""
        divider = QLabel(f"── Roll at {now}{seeded_suffix} ──")
        divider.setAlignment(Qt.AlignmentFlag.AlignHCenter)
        divider.setStyleSheet("color: #888888; font-size: 11px; padding: 2px 0;")
        self._layout.insertWidget(insert_at, divider)
        insert_at += 1

        # Result cards
        cards: list[QWidget] = []
        for line_result in roll_result.line_results:
            card = ResultCard(line_result)
            self._layout.insertWidget(insert_at, card)
            insert_at += 1
            cards.append(card)

        self._roll_sets.append((divider, cards))

        # Auto-trim
        if len(self._roll_sets) > self._MAX_ROLL_SETS:
            oldest_divider, oldest_cards = self._roll_sets.pop(0)
            oldest_divider.deleteLater()
            for card in oldest_cards:
                card.deleteLater()
            self._roll_set_count -= 1

        # Scroll to bottom after layout settles
        QTimer.singleShot(50, self._scroll_to_bottom)

    def clear(self) -> None:
        """Remove all widgets from the container and reset counter."""
        for divider, cards in self._roll_sets:
            divider.deleteLater()
            for card in cards:
                card.deleteLater()
        self._roll_sets.clear()
        self._roll_set_count = 0

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    def _scroll_to_bottom(self) -> None:
        sb = self._scroll.verticalScrollBar()
        sb.setValue(sb.maximum())

    def _copy_all(self) -> None:
        """Collect text from all visible ResultCard widgets and copy to clipboard."""
        texts: list[str] = []
        for _divider, cards in self._roll_sets:
            for card in cards:
                if isinstance(card, ResultCard):
                    texts.append(card.to_text())
        QApplication.clipboard().setText("\n\n".join(texts))
