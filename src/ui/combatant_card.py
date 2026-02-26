"""CombatantCard — wide horizontal card widget for a single combat participant.

Displays name, AC badge, initiative spinbox, HP bar, and condition chips.
All user actions route outward via signals; this widget holds NO HP state.
"""
from __future__ import annotations

from PySide6.QtWidgets import (
    QFrame,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QSpinBox,
    QLineEdit,
    QPushButton,
    QWidget,
    QSizePolicy,
)
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QFont, QIntValidator

from src.combat.models import CombatantState
from src.ui.hp_bar import HpBar


# ---------------------------------------------------------------------------
# Condition color map (plan spec)
# ---------------------------------------------------------------------------

CONDITION_COLORS: dict[str, str] = {
    "Blinded":            "#795548",
    "Charmed":            "#E91E63",
    "Deafened":           "#9E9E9E",
    "Frightened":         "#9C27B0",
    "Grappled":           "#FF5722",
    "Incapacitated":      "#607D8B",
    "Invisible":          "#B0BEC5",
    "Paralyzed":          "#FF9800",
    "Petrified":          "#8D6E63",
    "Poisoned":           "#4CAF50",
    "Prone":              "#FFEB3B",
    "Restrained":         "#3F51B5",
    "Stunned":            "#FFC107",
    "Unconscious":        "#F44336",
    # Buffs / effects
    "Bless":              "#8BC34A",
    "Shield":             "#03A9F4",
    "Bane":               "#880E4F",
    "Hypnotic Pattern":   "#CE93D8",
    "Fear":               "#4A148C",
    "Web":                "#BDBDBD",
    "Entangle":           "#1B5E20",
    "Maze":               "#311B92",
    "Haste":              "#00BCD4",
    "Slow":               "#827717",
    "Faerie Fire":        "#F48FB1",
    "Hold Person":        "#6A1B9A",
    "Hex":                "#37474F",
    "Hunter's Mark":      "#2E7D32",
    "Spirit Guardians":   "#FFD54F",
}

_DEFAULT_CONDITION_COLOR = "#757575"


# ---------------------------------------------------------------------------
# _ConditionChip
# ---------------------------------------------------------------------------

class _ConditionChip(QLabel):
    """Clickable colored pill label for a condition or buff."""

    clicked = Signal(str)   # condition_name

    def __init__(self, condition_name: str, duration, expired: bool, parent=None) -> None:
        super().__init__(parent)
        self._condition_name = condition_name
        self._expired = expired

        # Build display text
        if duration is not None:
            text = f"{condition_name} ({duration})"
        else:
            text = condition_name
        self.setText(text)

        # Style
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        color = CONDITION_COLORS.get(condition_name, _DEFAULT_CONDITION_COLOR)
        self._apply_style(color, expired, duration)

    def _apply_style(self, color: str, expired: bool, duration) -> None:
        if expired:
            style = (
                "border-radius: 8px; padding: 2px 8px; "
                "background-color: #555; color: #888; "
                "text-decoration: line-through;"
            )
        elif duration == 1:
            style = (
                f"border-radius: 8px; padding: 2px 8px; "
                f"background-color: {color}; color: white; "
                f"border: 1px dashed red;"
            )
        else:
            style = (
                f"border-radius: 8px; padding: 2px 8px; "
                f"background-color: {color}; color: white;"
            )
        self.setStyleSheet(style)

    def mousePressEvent(self, event) -> None:
        self.clicked.emit(self._condition_name)
        super().mousePressEvent(event)


# ---------------------------------------------------------------------------
# CombatantCard
# ---------------------------------------------------------------------------

class CombatantCard(QFrame):
    """Wide horizontal card for one combatant.

    Signals:
        damage_entered(combatant_id, signed_value): User submitted a +/- number in the input.
        condition_add_requested(combatant_id): User clicked the "+" chip button.
        condition_clicked(combatant_id, condition_name): User clicked an existing chip.
        initiative_changed(combatant_id, new_value): Initiative spinbox changed.
    """

    damage_entered = Signal(str, int)
    condition_add_requested = Signal(str)
    condition_clicked = Signal(str, str)
    initiative_changed = Signal(str, int)

    def __init__(self, state: CombatantState, parent=None) -> None:
        super().__init__(parent)
        self._combatant_id = state.id
        self._recalculating = False
        self._damage_input_visible = False
        self._active_turn = False
        self._selected = False

        self.setFrameShape(QFrame.Shape.StyledPanel)
        self.setStyleSheet(
            "CombatantCard { border: 1px solid #555; border-radius: 4px; }"
        )
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)

        self._build_layout(state)

    # ------------------------------------------------------------------
    # Layout construction
    # ------------------------------------------------------------------

    def _build_layout(self, state: CombatantState) -> None:
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(8, 4, 8, 4)
        main_layout.setSpacing(4)

        # ---- Top row ----
        top_row = QHBoxLayout()
        top_row.setSpacing(6)

        # Active-turn indicator (left chevron)
        self._active_indicator = QLabel("")
        self._active_indicator.setFixedWidth(16)
        self._active_indicator.setAlignment(Qt.AlignmentFlag.AlignCenter)
        top_row.addWidget(self._active_indicator)

        # Name label
        name_font = QFont()
        name_font.setBold(True)
        name_font.setPointSize(11)
        self._name_label = QLabel(state.name)
        self._name_label.setFont(name_font)
        self._name_label.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
        if state.is_defeated:
            self._apply_strikethrough(self._name_label)
        top_row.addWidget(self._name_label)

        # AC badge
        self._ac_badge = QLabel(f"AC {state.ac}")
        self._ac_badge.setFixedWidth(48)
        self._ac_badge.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._ac_badge.setStyleSheet(
            "QLabel { background-color: #1976D2; color: white; border-radius: 4px; "
            "padding: 2px 4px; font-weight: bold; font-size: 9pt; }"
        )
        top_row.addWidget(self._ac_badge)

        # Initiative spinbox
        self._initiative_spin = QSpinBox()
        self._initiative_spin.setRange(-10, 40)
        self._initiative_spin.setValue(state.initiative)
        self._initiative_spin.setFixedWidth(55)
        self._initiative_spin.setToolTip("Initiative")
        self._initiative_spin.setPrefix("Init ")
        self._initiative_spin.valueChanged.connect(self._on_initiative_changed)
        top_row.addWidget(self._initiative_spin)

        # Toggleable stat labels area (hidden by default — Plan 03 controls toggle)
        self._stats_widget = QWidget()
        stats_layout = QHBoxLayout(self._stats_widget)
        stats_layout.setContentsMargins(0, 0, 0, 0)
        stats_layout.setSpacing(4)

        self._speed_label = QLabel(f"Spd: {state.speed}" if state.speed else "")
        self._speed_label.setStyleSheet("font-size: 8pt; color: #aaa;")
        stats_layout.addWidget(self._speed_label)

        self._pp_label = QLabel(f"PP: {state.passive_perception}" if state.passive_perception else "")
        self._pp_label.setStyleSheet("font-size: 8pt; color: #aaa;")
        stats_layout.addWidget(self._pp_label)

        if state.legendary_resistances_max > 0:
            self._leg_res_label = QLabel(
                f"LR: {state.legendary_resistances}/{state.legendary_resistances_max}"
            )
            self._leg_res_label.setStyleSheet("font-size: 8pt; color: #FFB300;")
            stats_layout.addWidget(self._leg_res_label)
        else:
            self._leg_res_label = QLabel("")
            stats_layout.addWidget(self._leg_res_label)

        if state.legendary_actions_max > 0:
            self._leg_act_label = QLabel(
                f"LA: {state.legendary_actions}/{state.legendary_actions_max}"
            )
            self._leg_act_label.setStyleSheet("font-size: 8pt; color: #FF8F00;")
            stats_layout.addWidget(self._leg_act_label)
        else:
            self._leg_act_label = QLabel("")
            stats_layout.addWidget(self._leg_act_label)

        self._stats_widget.setVisible(False)
        top_row.addWidget(self._stats_widget)

        main_layout.addLayout(top_row)

        # ---- Middle row — HP bar + damage input ----
        mid_row = QHBoxLayout()
        mid_row.setSpacing(6)

        self._hp_bar = HpBar(state.max_hp, state.current_hp, state.temp_hp)
        self._hp_bar.clicked.connect(self._toggle_damage_input)
        mid_row.addWidget(self._hp_bar, 7)

        self._damage_input = QLineEdit()
        self._damage_input.setPlaceholderText("e.g. -12 or +5")
        self._damage_input.setFixedWidth(100)
        self._damage_input.setValidator(QIntValidator(-9999, 9999))
        self._damage_input.setVisible(False)
        self._damage_input.returnPressed.connect(self._on_damage_submitted)
        mid_row.addWidget(self._damage_input)

        main_layout.addLayout(mid_row)

        # ---- Bottom row — condition chips ----
        self._chip_container = QWidget()
        self._chip_layout = QHBoxLayout(self._chip_container)
        self._chip_layout.setContentsMargins(0, 0, 0, 0)
        self._chip_layout.setSpacing(4)
        self._chip_layout.setAlignment(Qt.AlignmentFlag.AlignLeft)

        self._plus_btn = QPushButton("+")
        self._plus_btn.setFixedSize(22, 22)
        self._plus_btn.setToolTip("Add condition")
        self._plus_btn.setStyleSheet(
            "QPushButton { border-radius: 11px; background-color: #444; color: white; "
            "font-weight: bold; font-size: 12pt; } "
            "QPushButton:hover { background-color: #555; }"
        )
        self._plus_btn.clicked.connect(
            lambda: self.condition_add_requested.emit(self._combatant_id)
        )

        self._rebuild_condition_chips(state)

        main_layout.addWidget(self._chip_container)

    def _rebuild_condition_chips(self, state: CombatantState) -> None:
        """Clear and recreate all condition chips from state."""
        # Remove all widgets from chip layout
        while self._chip_layout.count():
            item = self._chip_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        for cond in state.conditions:
            chip = _ConditionChip(cond.name, cond.duration, cond.expired)
            chip.clicked.connect(
                lambda name, cid=self._combatant_id: self.condition_clicked.emit(cid, name)
            )
            self._chip_layout.addWidget(chip)

        self._chip_layout.addWidget(self._plus_btn)

    # ------------------------------------------------------------------
    # Slots
    # ------------------------------------------------------------------

    def _toggle_damage_input(self) -> None:
        """Show or hide the damage input next to the HP bar."""
        self._damage_input_visible = not self._damage_input_visible
        self._damage_input.setVisible(self._damage_input_visible)
        if self._damage_input_visible:
            self._damage_input.clear()
            self._damage_input.setFocus()

    def _on_damage_submitted(self) -> None:
        """Parse the damage input and emit damage_entered signal."""
        text = self._damage_input.text().strip()
        if not text:
            return
        try:
            # QIntValidator allows the sign in input so parse directly
            value = int(text)
        except ValueError:
            return
        self._damage_input.clear()
        self._damage_input.setVisible(False)
        self._damage_input_visible = False
        self.damage_entered.emit(self._combatant_id, value)

    def _on_initiative_changed(self, value: int) -> None:
        if not self._recalculating:
            self.initiative_changed.emit(self._combatant_id, value)

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def refresh(self, state: CombatantState) -> None:
        """Update ALL display fields from the given state."""
        # Name + strikethrough
        self._name_label.setText(state.name)
        if state.is_defeated:
            self._apply_strikethrough(self._name_label)
        else:
            self._remove_strikethrough(self._name_label)

        # AC badge
        self._ac_badge.setText(f"AC {state.ac}")

        # HP bar
        self._hp_bar.update_hp(state.current_hp, state.max_hp, state.temp_hp)

        # Initiative spinbox (blockSignals to avoid re-triggering initiative_changed)
        self._recalculating = True
        self._initiative_spin.blockSignals(True)
        self._initiative_spin.setValue(state.initiative)
        self._initiative_spin.blockSignals(False)
        self._recalculating = False

        # Toggleable stats
        self._speed_label.setText(f"Spd: {state.speed}" if state.speed else "")
        self._pp_label.setText(f"PP: {state.passive_perception}" if state.passive_perception else "")
        if state.legendary_resistances_max > 0:
            self._leg_res_label.setText(
                f"LR: {state.legendary_resistances}/{state.legendary_resistances_max}"
            )
        if state.legendary_actions_max > 0:
            self._leg_act_label.setText(
                f"LA: {state.legendary_actions}/{state.legendary_actions_max}"
            )

        # Condition chips
        self._rebuild_condition_chips(state)

        self.updateGeometry()
        self.adjustSize()

    def set_active_turn(self, active: bool) -> None:
        """Highlight with golden border and chevron when it's this combatant's turn."""
        self._active_turn = active
        self._apply_border_style()
        self._active_indicator.setText("> " if active else "")

    def set_selected(self, selected: bool) -> None:
        """Highlight with blue border when selected for AOE/multi-actions."""
        self._selected = selected
        self._apply_border_style()

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _apply_border_style(self) -> None:
        if self._active_turn:
            self.setStyleSheet(
                "CombatantCard { border: 2px solid #FF9800; border-radius: 4px; }"
            )
        elif self._selected:
            self.setStyleSheet(
                "CombatantCard { border: 2px solid #2196F3; border-radius: 4px; }"
            )
        else:
            self.setStyleSheet(
                "CombatantCard { border: 1px solid #555; border-radius: 4px; }"
            )

    @staticmethod
    def _apply_strikethrough(label: QLabel) -> None:
        font = label.font()
        font.setStrikeOut(True)
        label.setFont(font)
        label.setStyleSheet("color: #888;")

    @staticmethod
    def _remove_strikethrough(label: QLabel) -> None:
        font = label.font()
        font.setStrikeOut(False)
        label.setFont(font)
        label.setStyleSheet("")
