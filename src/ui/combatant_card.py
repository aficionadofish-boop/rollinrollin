"""CombatantCard — wide horizontal card widget for a single combat participant.

Displays name, AC badge, initiative spinbox, HP bar, and condition chips.
All user actions route outward via signals; this widget holds NO HP state.

Also contains GroupCard (three-level grouped display) and CompactSubRow.
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
from PySide6.QtCore import Qt, Signal, QMimeData, QPoint
from PySide6.QtGui import QFont, QIntValidator, QDrag

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
        card_clicked(combatant_id, modifiers): Mouse press on card (for multi-select).
    """

    damage_entered = Signal(str, int)
    condition_add_requested = Signal(str)
    condition_clicked = Signal(str, str)
    initiative_changed = Signal(str, int)
    card_clicked = Signal(str, object)  # combatant_id, Qt.KeyboardModifiers

    def __init__(self, state: CombatantState, parent=None) -> None:
        super().__init__(parent)
        self._combatant_id = state.id
        self._recalculating = False
        self._damage_input_visible = False
        self._active_turn = False
        self._selected = False
        self._drag_start_pos: QPoint | None = None

        self.setFrameShape(QFrame.Shape.StyledPanel)
        self.setStyleSheet(
            "CombatantCard { border: 1px solid #555; border-radius: 4px; }"
        )
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)

        # Set property for drag identification
        self.setProperty("combatant_id", self._combatant_id)

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

        self._regen_label = QLabel(
            f"Regen: {state.regeneration_hp}" if state.regeneration_hp > 0 else ""
        )
        self._regen_label.setStyleSheet("font-size: 8pt; color: #4CAF50;")
        stats_layout.addWidget(self._regen_label)

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
        # Remove all widgets from chip layout except the persistent + button
        while self._chip_layout.count():
            item = self._chip_layout.takeAt(0)
            w = item.widget()
            if w and w is not self._plus_btn:
                w.deleteLater()

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
    # Drag-to-reorder support
    # ------------------------------------------------------------------

    def mousePressEvent(self, event) -> None:
        if event.button() == Qt.MouseButton.LeftButton:
            self._drag_start_pos = event.pos()
            self.card_clicked.emit(self._combatant_id, event.modifiers())
        super().mousePressEvent(event)

    def mouseMoveEvent(self, event) -> None:
        if (
            event.buttons() & Qt.MouseButton.LeftButton
            and self._drag_start_pos is not None
            and (event.pos() - self._drag_start_pos).manhattanLength() > 10
        ):
            drag = QDrag(self)
            mime = QMimeData()
            mime.setData(
                "application/x-combatant-id",
                self._combatant_id.encode("utf-8"),
            )
            drag.setMimeData(mime)
            drag.exec(Qt.DropAction.MoveAction)
        super().mouseMoveEvent(event)

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
        self._regen_label.setText(
            f"Regen: {state.regeneration_hp}" if state.regeneration_hp > 0 else ""
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

    def set_stat_visible(self, stat_key: str, visible: bool) -> None:
        """Show or hide a specific stat label by key. Also makes the stats widget visible if any stat is shown."""
        label_map = {
            "speed": self._speed_label,
            "passive_perception": self._pp_label,
            "legendary_resistance": self._leg_res_label,
            "legendary_actions": self._leg_act_label,
            "regeneration": self._regen_label,
        }
        if stat_key in label_map:
            label_map[stat_key].setVisible(visible)
        # Show stats widget if any child label is visible
        any_visible = any(
            lbl.isVisible() for lbl in label_map.values()
        )
        self._stats_widget.setVisible(any_visible)

    def set_drag_enabled(self, enabled: bool) -> None:
        """Enable or disable drag-to-reorder. When disabled, mouse events pass normally."""
        self._drag_enabled = enabled

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _apply_border_style(self) -> None:
        if self._active_turn:
            self.setStyleSheet(
                "CombatantCard { border: 2px solid #FF9800; border-radius: 4px; "
                "background-color: rgba(255, 152, 0, 0.08); }"
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


# ---------------------------------------------------------------------------
# CompactSubRow
# ---------------------------------------------------------------------------

class CompactSubRow(QFrame):
    """Small inline row for one member inside an expanded GroupCard.

    Shows: name, compact HpBar (height 16px), condition chip summary, and
    an expand-to-full button.

    Signals:
        clicked(combatant_id): Emitted when the user clicks to expand this member.
    """

    clicked = Signal(str)  # combatant_id

    def __init__(self, state: CombatantState, parent=None) -> None:
        super().__init__(parent)
        self._combatant_id = state.id
        self._state = state

        self.setFrameShape(QFrame.Shape.NoFrame)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)
        self.setCursor(Qt.CursorShape.PointingHandCursor)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(20, 2, 4, 2)  # 20px left indent for group membership
        layout.setSpacing(6)

        # Individual name
        self._name_label = QLabel(state.name)
        self._name_label.setStyleSheet("font-size: 9pt;")
        self._name_label.setMinimumWidth(80)
        layout.addWidget(self._name_label)

        # Compact HP bar (16px height)
        self._hp_bar = HpBar(state.max_hp, state.current_hp, state.temp_hp)
        self._hp_bar.setFixedHeight(16)
        layout.addWidget(self._hp_bar, 1)

        # Condition summary (small count badge if any conditions)
        self._cond_label = QLabel()
        self._cond_label.setStyleSheet("font-size: 8pt; color: #aaa;")
        layout.addWidget(self._cond_label)

        # Expand button
        expand_btn = QPushButton("^")
        expand_btn.setFixedSize(20, 20)
        expand_btn.setToolTip("Expand to full card")
        expand_btn.setStyleSheet(
            "QPushButton { background-color: #444; color: white; border: none; "
            "border-radius: 3px; font-size: 9pt; } "
            "QPushButton:hover { background-color: #555; }"
        )
        expand_btn.clicked.connect(lambda: self.clicked.emit(self._combatant_id))
        layout.addWidget(expand_btn)

        self._refresh_display(state)

    def _refresh_display(self, state: CombatantState) -> None:
        if state.is_defeated:
            self._name_label.setStyleSheet("font-size: 9pt; color: #888; text-decoration: line-through;")
        else:
            self._name_label.setStyleSheet("font-size: 9pt;")
        n_conds = len([c for c in state.conditions if not c.expired])
        self._cond_label.setText(f"{n_conds} cond." if n_conds else "")

    def refresh(self, state: CombatantState) -> None:
        """Update display from new state."""
        self._state = state
        self._hp_bar.update_hp(state.current_hp, state.max_hp, state.temp_hp)
        self._name_label.setText(state.name)
        self._refresh_display(state)

    def set_active(self, active: bool) -> None:
        """Highlight this sub-row as the active turn member."""
        if active:
            self.setStyleSheet(
                "CompactSubRow { background-color: rgba(255,152,0,30); border-radius: 3px; }"
            )
        else:
            self.setStyleSheet("")

    def mousePressEvent(self, event) -> None:
        if event.button() == Qt.MouseButton.LeftButton:
            self.clicked.emit(self._combatant_id)
        super().mousePressEvent(event)


# ---------------------------------------------------------------------------
# GroupCard
# ---------------------------------------------------------------------------

class GroupCard(QFrame):
    """Three-level progressive disclosure card for a group of same-type monsters.

    Level 1 (collapsed): "Nx [Monster]" with average HP bar.
    Level 2 (expanded compact): indented CompactSubRow for each member.
    Level 3 (individual full card): clicking a sub-row reveals a full CombatantCard.

    Signals pass through from individual CombatantCards outward to CombatTrackerTab.
    """

    damage_entered = Signal(str, int)
    condition_add_requested = Signal(str)
    condition_clicked = Signal(str, str)
    initiative_changed = Signal(str, int)  # applies to all members (shared initiative)

    def __init__(self, group_id: str, members: list[CombatantState], parent=None) -> None:
        super().__init__(parent)
        self._group_id = group_id
        self._members = list(members)
        self._expanded = False
        self._expanded_individual: str | None = None  # ID of full-card-expanded member
        self._active_turn = False
        self._active_member_id: str | None = None

        # Track sub-row and full-card widgets for refresh
        self._sub_rows: dict[str, CompactSubRow] = {}
        self._individual_cards: dict[str, CombatantCard] = {}

        self.setFrameShape(QFrame.Shape.StyledPanel)
        self.setStyleSheet(
            "GroupCard { border: 1px solid #445; border-radius: 4px; background-color: #1a1a2e; }"
        )
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)

        self._main_layout = QVBoxLayout(self)
        self._main_layout.setContentsMargins(8, 4, 8, 4)
        self._main_layout.setSpacing(4)

        self._build_collapsed_header()

    # ------------------------------------------------------------------
    # Layout construction
    # ------------------------------------------------------------------

    def _build_collapsed_header(self) -> None:
        """Build the header row (collapsed or expanded indicator)."""
        header_widget = QWidget()
        header_layout = QHBoxLayout(header_widget)
        header_layout.setContentsMargins(0, 0, 0, 0)
        header_layout.setSpacing(6)

        # Active turn indicator
        self._active_indicator = QLabel("")
        self._active_indicator.setFixedWidth(16)
        self._active_indicator.setAlignment(Qt.AlignmentFlag.AlignCenter)
        header_layout.addWidget(self._active_indicator)

        # Count label
        count_font = QFont()
        count_font.setBold(True)
        count_font.setPointSize(11)
        n = len(self._members)
        self._count_label = QLabel(f"{n}x")
        self._count_label.setFont(count_font)
        self._count_label.setStyleSheet("color: #90CAF9;")
        header_layout.addWidget(self._count_label)

        # Monster name
        name_font = QFont()
        name_font.setBold(True)
        name_font.setPointSize(11)
        self._name_label = QLabel(self._group_id)
        self._name_label.setFont(name_font)
        self._name_label.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
        header_layout.addWidget(self._name_label)

        # AC badge (shared — all members have same AC)
        ac = self._members[0].ac if self._members else 0
        self._ac_badge = QLabel(f"AC {ac}")
        self._ac_badge.setFixedWidth(48)
        self._ac_badge.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._ac_badge.setStyleSheet(
            "QLabel { background-color: #1976D2; color: white; border-radius: 4px; "
            "padding: 2px 4px; font-weight: bold; font-size: 9pt; }"
        )
        header_layout.addWidget(self._ac_badge)

        # Initiative spinbox (shared roll for group)
        self._initiative_spin = QSpinBox()
        self._initiative_spin.setRange(-10, 40)
        init_val = self._members[0].initiative if self._members else 0
        self._initiative_spin.setValue(init_val)
        self._initiative_spin.setFixedWidth(55)
        self._initiative_spin.setToolTip("Initiative (shared for group)")
        self._initiative_spin.setPrefix("Init ")
        self._initiative_spin.valueChanged.connect(self._on_group_initiative_changed)
        header_layout.addWidget(self._initiative_spin)

        # Condition summary indicator
        self._cond_summary_label = QLabel()
        self._cond_summary_label.setStyleSheet("font-size: 8pt; color: #FFC107;")
        header_layout.addWidget(self._cond_summary_label)

        # Average HP bar
        avg_cur, avg_max, avg_temp = self._compute_avg_hp()
        self._avg_hp_bar = HpBar(avg_max, avg_cur, avg_temp)
        header_layout.addWidget(self._avg_hp_bar, 2)

        # Expand/collapse button
        self._expand_btn = QPushButton("v")
        self._expand_btn.setFixedSize(24, 24)
        self._expand_btn.setToolTip("Expand group")
        self._expand_btn.setStyleSheet(
            "QPushButton { background-color: #333; color: white; border: none; "
            "border-radius: 3px; } "
            "QPushButton:hover { background-color: #444; }"
        )
        self._expand_btn.clicked.connect(self._toggle_expand)
        header_layout.addWidget(self._expand_btn)

        self._header_widget = header_widget
        self._main_layout.addWidget(header_widget)

        # Container for sub-rows / individual cards (hidden initially)
        self._members_container = QWidget()
        self._members_layout = QVBoxLayout(self._members_container)
        self._members_layout.setContentsMargins(0, 0, 0, 0)
        self._members_layout.setSpacing(2)
        self._members_container.setVisible(False)
        self._main_layout.addWidget(self._members_container)

        self._update_cond_summary()

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    def _compute_avg_hp(self) -> tuple[int, int, int]:
        """Return (avg_current_hp, avg_max_hp, avg_temp_hp) across all members."""
        if not self._members:
            return 0, 1, 0
        avg_cur = sum(m.current_hp for m in self._members) // len(self._members)
        avg_max = sum(m.max_hp for m in self._members) // len(self._members)
        avg_temp = sum(m.temp_hp for m in self._members) // len(self._members)
        return avg_cur, max(avg_max, 1), avg_temp

    def _update_cond_summary(self) -> None:
        """Update the condition summary label from all members."""
        total = sum(
            len([c for c in m.conditions if not c.expired])
            for m in self._members
        )
        self._cond_summary_label.setText(f"{total} cond." if total else "")

    def _build_members_view(self) -> None:
        """Populate _members_container with CompactSubRows (clearing first)."""
        # Clear existing
        while self._members_layout.count():
            item = self._members_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        self._sub_rows.clear()
        self._individual_cards.clear()

        for state in self._members:
            if self._expanded_individual == state.id:
                # Full card for this member
                card = CombatantCard(state)
                card.setContentsMargins(20, 0, 0, 0)
                card.damage_entered.connect(self.damage_entered)
                card.condition_add_requested.connect(self.condition_add_requested)
                card.condition_clicked.connect(self.condition_clicked)
                card.initiative_changed.connect(self.initiative_changed)
                if self._active_member_id == state.id:
                    card.set_active_turn(True)
                self._individual_cards[state.id] = card
                self._members_layout.addWidget(card)
            else:
                # Compact sub-row
                row = CompactSubRow(state)
                row.clicked.connect(self._on_sub_row_clicked)
                if self._active_member_id == state.id:
                    row.set_active(True)
                self._sub_rows[state.id] = row
                self._members_layout.addWidget(row)

    def _on_sub_row_clicked(self, combatant_id: str) -> None:
        """Toggle individual expansion when a sub-row is clicked."""
        if self._expanded_individual == combatant_id:
            # Collapse back to sub-row
            self._expanded_individual = None
        else:
            self._expanded_individual = combatant_id
        self._build_members_view()

    def _on_group_initiative_changed(self, value: int) -> None:
        """Emit initiative_changed for the first member (representative for the group)."""
        if self._members:
            self.initiative_changed.emit(self._members[0].id, value)

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def refresh(self, members: list[CombatantState]) -> None:
        """Update stored members and rebuild display."""
        self._members = list(members)
        n = len(self._members)
        self._count_label.setText(f"{n}x")

        # Update average HP bar
        avg_cur, avg_max, avg_temp = self._compute_avg_hp()
        self._avg_hp_bar.update_hp(avg_cur, avg_max, avg_temp)

        # Update initiative spinbox (use first member as reference)
        if self._members:
            self._initiative_spin.blockSignals(True)
            self._initiative_spin.setValue(self._members[0].initiative)
            self._initiative_spin.blockSignals(False)

        self._update_cond_summary()

        # Refresh sub-rows and individual cards if expanded
        if self._expanded:
            for state in self._members:
                if state.id in self._sub_rows:
                    self._sub_rows[state.id].refresh(state)
                elif state.id in self._individual_cards:
                    self._individual_cards[state.id].refresh(state)

    def set_active_turn(self, active: bool) -> None:
        """Apply active styling to the group header."""
        self._active_turn = active
        if active:
            self.setStyleSheet(
                "GroupCard { border: 2px solid #FF9800; border-radius: 4px; "
                "background-color: #1a1a2e; }"
            )
        else:
            self.setStyleSheet(
                "GroupCard { border: 1px solid #445; border-radius: 4px; "
                "background-color: #1a1a2e; }"
            )
        self._active_indicator.setText("> " if active else "")

    def set_member_active(self, combatant_id: str) -> None:
        """Highlight a specific member's sub-row within the expanded group."""
        self._active_member_id = combatant_id
        for mid, row in self._sub_rows.items():
            row.set_active(mid == combatant_id)
        for mid, card in self._individual_cards.items():
            card.set_active_turn(mid == combatant_id)

    def set_stat_visible(self, stat_key: str, visible: bool) -> None:
        """Forward stat visibility toggle to all individual cards."""
        for card in self._individual_cards.values():
            card.set_stat_visible(stat_key, visible)

    def _toggle_expand(self) -> None:
        """Switch between collapsed and expanded views."""
        self._expanded = not self._expanded
        if self._expanded:
            self._expand_btn.setText("^")
            self._expand_btn.setToolTip("Collapse group")
            self._build_members_view()
            self._members_container.setVisible(True)
        else:
            self._expanded_individual = None
            self._members_container.setVisible(False)
            self._expand_btn.setText("v")
            self._expand_btn.setToolTip("Expand group")
