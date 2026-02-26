"""HpBar — custom HP bar QWidget with color-coded segments and click-to-reveal."""
from __future__ import annotations

from PySide6.QtWidgets import QWidget
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QPainter, QColor, QFont


class HpBar(QWidget):
    """Color-coded HP bar with optional temp HP overlay.

    Visual layout (left to right):
    - Dark gray background (#333) filling full width
    - Green/yellow/red HP segment based on percentage
    - Blue temp HP segment immediately to the right of the HP segment
    - Centered text overlay: "{current_hp} / {max_hp}" or "{current_hp} + {temp_hp}t / {max_hp}"

    Click anywhere on the bar to emit the ``clicked`` signal (for click-to-reveal
    damage input in CombatantCard).
    """

    clicked = Signal()

    def __init__(self, max_hp: int, current_hp: int, temp_hp: int = 0, parent=None) -> None:
        super().__init__(parent)
        self._max_hp = max(max_hp, 1)   # guard against 0 max
        self._current_hp = max(0, current_hp)
        self._temp_hp = max(0, temp_hp)

        self.setFixedHeight(24)
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

        # HP segment color
        hp_pct = self._current_hp / self._max_hp
        if hp_pct > 0.5:
            hp_color = QColor("#4CAF50")   # green
        elif hp_pct > 0.25:
            hp_color = QColor("#FFC107")   # yellow
        else:
            hp_color = QColor("#F44336")   # red

        hp_width = int(w * hp_pct)
        if hp_width > 0:
            painter.fillRect(0, 0, hp_width, h, hp_color)

        # Temp HP segment (blue, immediately right of HP segment)
        if self._temp_hp > 0:
            temp_pct = min(self._temp_hp / self._max_hp, 1.0)
            temp_width = int(w * temp_pct)
            # Clamp so blue doesn't overflow
            available = w - hp_width
            temp_width = min(temp_width, available)
            if temp_width > 0:
                painter.fillRect(hp_width, 0, temp_width, h, QColor("#2196F3"))

        # Text overlay — white bold with shadow for readability
        font = QFont()
        font.setBold(True)
        font.setPointSize(8)
        painter.setFont(font)

        if self._temp_hp > 0:
            text = f"{self._current_hp} + {self._temp_hp}t / {self._max_hp}"
        else:
            text = f"{self._current_hp} / {self._max_hp}"

        # Draw shadow (dark, offset 1px)
        painter.setPen(QColor("#000000"))
        painter.drawText(1, 1, w, h, Qt.AlignmentFlag.AlignCenter, text)

        # Draw foreground (white)
        painter.setPen(QColor("#FFFFFF"))
        painter.drawText(0, 0, w, h, Qt.AlignmentFlag.AlignCenter, text)

        painter.end()

    def mousePressEvent(self, event) -> None:
        self.clicked.emit()
        super().mousePressEvent(event)
