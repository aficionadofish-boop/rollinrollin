"""HpBar — custom HP bar QWidget with color-coded segments and click-to-reveal."""
from __future__ import annotations

from PySide6.QtWidgets import QWidget
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QPainter, QColor, QFont


class HpBar(QWidget):
    """Color-coded HP bar with optional temp HP overlay.

    Visual layout (left to right):
    - Dark gray background (#333) filling full width
    - 5-band HP segment color based on percentage:
        100%       — bright green  (#4CAF50) "Uninjured"
        75–99%     — green-yellow  (#8BC34A) "Barely Injured"
        51–75%     — yellow        (#FFC107) "Injured"
        26–50%     — orange        (#FF6B35) "Badly Injured"
        1–25%      — red           (#F44336) "Near Death"
        0% (dead)  — grey          (#666666) no label
    - Blue temp HP segment immediately to the right of the HP segment
    - Centered descriptive text overlay (always visible, not hover-only)

    Click anywhere on the bar to emit the ``clicked`` signal (for click-to-reveal
    damage input in CombatantCard).
    """

    clicked = Signal()

    def __init__(self, max_hp: int, current_hp: int, temp_hp: int = 0, parent=None) -> None:
        super().__init__(parent)
        self._max_hp = max(max_hp, 1)   # guard against 0 max
        self._current_hp = max(0, current_hp)
        self._temp_hp = max(0, temp_hp)

        self.setFixedHeight(28)
        self.setCursor(Qt.CursorShape.PointingHandCursor)

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def update_hp(self, current_hp: int, max_hp: int, temp_hp: int = 0) -> None:
        """Update stored values and trigger a repaint."""
        self._max_hp = max(max_hp, 1)
        self._current_hp = max(0, current_hp)
        self._temp_hp = max(0, temp_hp)
        self.update()

    # ------------------------------------------------------------------
    # Qt overrides
    # ------------------------------------------------------------------

    def paintEvent(self, event) -> None:
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        w = self.width()
        h = self.height()

        # Background
        painter.fillRect(0, 0, w, h, QColor("#333333"))

        # HP segment color — 5-band system + defeated state
        hp_pct = self._current_hp / self._max_hp
        if hp_pct == 0:
            hp_color = QColor("#666666")   # grey (Defeated)
            label = ""                      # no text when defeated
        elif hp_pct <= 0.25:
            hp_color = QColor("#F44336")   # red (Near Death)
            label = "Near Death"
        elif hp_pct <= 0.50:
            hp_color = QColor("#FF6B35")   # orange (Badly Injured)
            label = "Badly Injured"
        elif hp_pct <= 0.75:
            hp_color = QColor("#FFC107")   # yellow (Injured)
            label = "Injured"
        elif hp_pct < 1.0:
            hp_color = QColor("#8BC34A")   # green-yellow (Barely Injured)
            label = "Barely Injured"
        else:
            hp_color = QColor("#4CAF50")   # bright green (Uninjured)
            label = "Uninjured"

        hp_width = int(w * hp_pct)
        if hp_width > 0:
            painter.fillRect(0, 0, hp_width, h, hp_color)
        elif hp_pct == 0:
            # Defeated: fill full bar with grey
            painter.fillRect(0, 0, w, h, hp_color)

        # Temp HP segment (blue, immediately right of HP segment)
        if self._temp_hp > 0:
            temp_pct = min(self._temp_hp / self._max_hp, 1.0)
            temp_width = int(w * temp_pct)
            # Clamp so blue doesn't overflow
            available = w - hp_width
            temp_width = min(temp_width, available)
            if temp_width > 0:
                painter.fillRect(hp_width, 0, temp_width, h, QColor("#2196F3"))

        # Text overlay — HP numbers centered + descriptive label left-aligned
        hp_text = f"{self._current_hp}/{self._max_hp}"

        # HP numbers: 9pt bold, centered
        hp_font = QFont()
        hp_font.setBold(True)
        hp_font.setPointSize(9)
        painter.setFont(hp_font)

        # Shadow
        painter.setPen(QColor("#000000"))
        painter.drawText(1, 1, w, h, Qt.AlignmentFlag.AlignCenter, hp_text)
        # Foreground
        painter.setPen(QColor("#FFFFFF"))
        painter.drawText(0, 0, w, h, Qt.AlignmentFlag.AlignCenter, hp_text)

        # Descriptive label: 8pt bold, white, left-aligned with padding
        if label:
            desc_font = QFont()
            desc_font.setBold(True)
            desc_font.setPointSize(8)
            painter.setFont(desc_font)

            pad = 4
            # Shadow
            painter.setPen(QColor("#000000"))
            painter.drawText(pad + 1, 1, w - pad, h, Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter, label)
            # Foreground
            painter.setPen(QColor("#FFFFFF"))
            painter.drawText(pad, 0, w - pad, h, Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter, label)

        painter.end()

    def mousePressEvent(self, event) -> None:
        self.clicked.emit()
        super().mousePressEvent(event)
