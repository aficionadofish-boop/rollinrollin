"""CombatTrackerTab — main Combat Tracker tab widget.

Orchestrates CombatantCards, GroupCards, CombatLogPanel, and CombatTrackerService.
All state mutations go through CombatTrackerService; the UI is display-only.
"""
from __future__ import annotations

from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QScrollArea,
    QSplitter,
    QMessageBox,
    QMenu,
    QDialog,
    QSpinBox,
    QLineEdit,
    QFormLayout,
    QDialogButtonBox,
    QToolButton,
    QFrame,
    QTabWidget,
    QRubberBand,
    QSizePolicy,
)
from PySide6.QtCore import Qt, Signal, QByteArray, QTimer, QRect, QPoint, QSize
from PySide6.QtGui import QFont, QDragEnterEvent, QDropEvent, QDragMoveEvent

from src.combat.models import (
    CombatState,
    ConditionEntry,
    PlayerCharacter,
    STANDARD_CONDITIONS,
    COMMON_BUFFS,
)
from src.combat.service import CombatTrackerService
from src.ui.combatant_card import CombatantCard, GroupCard
from src.ui.combat_log_panel import CombatLogPanel


# ---------------------------------------------------------------------------
# _CustomConditionDialog
# ---------------------------------------------------------------------------

class _CustomConditionDialog(QDialog):
    """Small dialog for adding a custom condition with name and optional duration."""

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.setWindowTitle("Add Custom Condition")
        self.setModal(True)

        layout = QFormLayout(self)

        self._name_edit = QLineEdit()
        self._name_edit.setPlaceholderText("Condition name")
        layout.addRow("Name:", self._name_edit)

        self._duration_spin = QSpinBox()
        self._duration_spin.setRange(0, 100)
        self._duration_spin.setValue(0)
        self._duration_spin.setToolTip("0 = indefinite")
        layout.addRow("Duration (0=indefinite):", self._duration_spin)

        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addRow(buttons)

    def get_condition_name(self) -> str:
        return self._name_edit.text().strip()

    def get_duration(self):
        """Return None if duration=0 (indefinite), else the int value."""
        val = self._duration_spin.value()
        return None if val == 0 else val


# ---------------------------------------------------------------------------
# _EditDurationDialog
# ---------------------------------------------------------------------------

class _EditDurationDialog(QDialog):
    """Small inline dialog for editing a condition's remaining duration."""

    def __init__(self, condition_name: str, current_duration, parent=None) -> None:
        super().__init__(parent)
        self.setWindowTitle(f"Edit Duration: {condition_name}")
        self.setModal(True)

        layout = QFormLayout(self)

        self._duration_spin = QSpinBox()
        self._duration_spin.setRange(0, 100)
        current = current_duration if current_duration is not None else 0
        self._duration_spin.setValue(current)
        self._duration_spin.setToolTip("0 = indefinite")
        layout.addRow("Duration (0=indefinite):", self._duration_spin)

        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addRow(buttons)

    def get_duration(self):
        val = self._duration_spin.value()
        return None if val == 0 else val


# ---------------------------------------------------------------------------
# _AOEDamageDialog
# ---------------------------------------------------------------------------

class _AOEDamageDialog(QDialog):
    """Small dialog for entering AOE damage amount."""

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.setWindowTitle("AOE Damage")
        self.setModal(True)

        layout = QFormLayout(self)

        self._damage_spin = QSpinBox()
        self._damage_spin.setRange(1, 9999)
        self._damage_spin.setValue(10)
        self._damage_spin.setToolTip("Damage amount (positive integer; will be applied as damage)")
        layout.addRow("Damage:", self._damage_spin)

        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addRow(buttons)

    def get_damage(self) -> int:
        return self._damage_spin.value()


# ---------------------------------------------------------------------------
# PCSubtab
# ---------------------------------------------------------------------------

class _PCRow(QWidget):
    """A single row in the PCSubtab for one player character."""

    changed = Signal()

    def __init__(self, name: str = "", ac: int = 10, max_hp: int = 1, parent=None) -> None:
        super().__init__(parent)
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 2, 0, 2)
        layout.setSpacing(4)

        self._name_edit = QLineEdit(name)
        self._name_edit.setPlaceholderText("PC Name")
        self._name_edit.setMinimumWidth(100)
        self._name_edit.textChanged.connect(self.changed)
        layout.addWidget(self._name_edit, 2)

        layout.addWidget(QLabel("AC:"))
        self._ac_spin = QSpinBox()
        self._ac_spin.setRange(1, 30)
        self._ac_spin.setValue(ac)
        self._ac_spin.setFixedWidth(55)
        self._ac_spin.valueChanged.connect(self.changed)
        layout.addWidget(self._ac_spin)

        layout.addWidget(QLabel("HP:"))
        self._max_hp_spin = QSpinBox()
        self._max_hp_spin.setRange(1, 999)
        self._max_hp_spin.setValue(max_hp)
        self._max_hp_spin.setFixedWidth(65)
        self._max_hp_spin.setToolTip("Max HP")
        self._max_hp_spin.valueChanged.connect(self.changed)
        layout.addWidget(self._max_hp_spin)

        layout.addWidget(QLabel("Init:"))
        self._init_bonus_spin = QSpinBox()
        self._init_bonus_spin.setRange(-10, 20)
        self._init_bonus_spin.setValue(0)
        self._init_bonus_spin.setFixedWidth(50)
        self._init_bonus_spin.setToolTip("Initiative bonus")
        self._init_bonus_spin.valueChanged.connect(self.changed)
        layout.addWidget(self._init_bonus_spin)

        self._del_btn = QPushButton("Del")
        self._del_btn.setFixedWidth(48)
        self._del_btn.setStyleSheet(
            "QPushButton { color: #f44336; font-weight: bold; } "
            "QPushButton:hover { background-color: #3a1a1a; }"
        )
        layout.addWidget(self._del_btn)

    def get_pc(self) -> PlayerCharacter:
        return PlayerCharacter(
            name=self._name_edit.text().strip() or "PC",
            ac=self._ac_spin.value(),
            max_hp=self._max_hp_spin.value(),
            current_hp=self._max_hp_spin.value(),
            initiative_bonus=self._init_bonus_spin.value(),
        )

    def set_pc(self, pc: PlayerCharacter) -> None:
        self._name_edit.blockSignals(True)
        self._ac_spin.blockSignals(True)
        self._max_hp_spin.blockSignals(True)
        self._init_bonus_spin.blockSignals(True)
        self._name_edit.setText(pc.name)
        self._ac_spin.setValue(pc.ac)
        self._max_hp_spin.setValue(pc.max_hp)
        self._init_bonus_spin.setValue(getattr(pc, "initiative_bonus", 0))
        self._name_edit.blockSignals(False)
        self._ac_spin.blockSignals(False)
        self._max_hp_spin.blockSignals(False)
        self._init_bonus_spin.blockSignals(False)

    @property
    def del_btn(self) -> QPushButton:
        return self._del_btn


class PCSubtab(QWidget):
    """Tab for managing persistent player characters."""

    pc_changed = Signal()

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self._rows: list[_PCRow] = []
        self._debounce_timer = QTimer()
        self._debounce_timer.setSingleShot(True)
        self._debounce_timer.setInterval(500)
        self._debounce_timer.timeout.connect(self.pc_changed)

        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(4, 4, 4, 4)
        main_layout.setSpacing(4)

        # Header
        header = QLabel("Player Characters")
        header_font = QFont()
        header_font.setBold(True)
        header.setFont(header_font)
        main_layout.addWidget(header)

        # Scroll area
        self._scroll = QScrollArea()
        self._scroll.setWidgetResizable(True)
        self._scroll.setFrameShape(QFrame.Shape.NoFrame)
        self._rows_container = QWidget()
        self._rows_layout = QVBoxLayout(self._rows_container)
        self._rows_layout.setContentsMargins(0, 0, 0, 0)
        self._rows_layout.setSpacing(2)
        self._rows_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        self._scroll.setWidget(self._rows_container)
        main_layout.addWidget(self._scroll, 1)

        # Add PC button
        self._add_btn = QPushButton("Add PC")
        self._add_btn.clicked.connect(self._on_add_pc)
        main_layout.addWidget(self._add_btn)

    def _on_add_pc(self) -> None:
        n = len(self._rows) + 1
        self._add_row(PlayerCharacter(name=f"PC {n}", ac=10, max_hp=1, current_hp=1))

    def _add_row(self, pc: PlayerCharacter) -> None:
        row = _PCRow(pc.name, pc.ac, pc.max_hp)
        row.set_pc(pc)
        row.changed.connect(self._debounce_timer.start)
        row.del_btn.clicked.connect(lambda checked=False, r=row: self._remove_row(r))
        self._rows.append(row)
        self._rows_layout.addWidget(row)

    def _remove_row(self, row: _PCRow) -> None:
        if row in self._rows:
            self._rows.remove(row)
        row.setParent(None)
        row.deleteLater()
        self._debounce_timer.start()

    def get_pcs(self) -> list[PlayerCharacter]:
        return [r.get_pc() for r in self._rows]

    def set_pcs(self, pcs: list[PlayerCharacter]) -> None:
        # Clear existing
        for row in list(self._rows):
            row.setParent(None)
            row.deleteLater()
        self._rows.clear()
        for pc in pcs:
            self._add_row(pc)

    def clear_pcs(self) -> None:
        self.set_pcs([])


# ---------------------------------------------------------------------------
# CombatantListArea — QScrollArea subclass with rubber-band box selection
# ---------------------------------------------------------------------------

class CombatantListArea(QScrollArea):
    """QScrollArea subclass that supports rubber-band box drag selection.

    Emits box_selected(set[str]) when a drag selection completes,
    providing the set of combatant_ids whose card geometries intersect
    the rubber-band rectangle.
    """

    box_selected = Signal(object)  # set[str] of combatant_ids

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self._rubber_band: QRubberBand | None = None
        self._drag_origin: QPoint | None = None
        self._dragging = False

    def mousePressEvent(self, event) -> None:
        modifiers = event.modifiers()
        no_modifier = not (
            modifiers & Qt.KeyboardModifier.ControlModifier
            or modifiers & Qt.KeyboardModifier.ShiftModifier
        )
        if event.button() == Qt.MouseButton.LeftButton and no_modifier:
            self._drag_origin = event.pos()
            self._dragging = False
            if self._rubber_band is None:
                self._rubber_band = QRubberBand(QRubberBand.Shape.Rectangle, self.viewport())
        super().mousePressEvent(event)

    def mouseMoveEvent(self, event) -> None:
        if (
            event.buttons() & Qt.MouseButton.LeftButton
            and self._drag_origin is not None
            and self._rubber_band is not None
        ):
            self._dragging = True
            rect = QRect(self._drag_origin, event.pos()).normalized()
            self._rubber_band.setGeometry(rect)
            self._rubber_band.show()
        super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event) -> None:
        if (
            event.button() == Qt.MouseButton.LeftButton
            and self._drag_origin is not None
            and self._rubber_band is not None
            and self._dragging
        ):
            self._rubber_band.hide()
            # Compute intersection with card widgets
            selection_rect = QRect(self._drag_origin, event.pos()).normalized()
            selected_ids: set[str] = set()
            inner = self.widget()
            if inner is not None:
                layout = inner.layout()
                if layout is not None:
                    for i in range(layout.count()):
                        item = layout.itemAt(i)
                        if item is None:
                            continue
                        widget = item.widget()
                        if widget is None:
                            continue
                        cid = widget.property("combatant_id")
                        if cid is None:
                            continue
                        # Map widget rect to viewport coords
                        widget_rect_global = QRect(
                            widget.mapTo(self.viewport(), QPoint(0, 0)),
                            widget.size(),
                        )
                        if selection_rect.intersects(widget_rect_global):
                            selected_ids.add(cid)
            if selected_ids:
                self.box_selected.emit(selected_ids)

        self._drag_origin = None
        self._dragging = False
        if self._rubber_band is not None:
            self._rubber_band.hide()
        super().mouseReleaseEvent(event)


# ---------------------------------------------------------------------------
# _CardContainer — drag-and-drop aware container for combatant cards
# ---------------------------------------------------------------------------

class _CardContainer(QWidget):
    """QWidget that accepts drop events to reorder combatant cards."""

    reorder_requested = Signal(list)  # list[str] ordered combatant IDs

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self._drop_enabled = False

    def set_drop_enabled(self, enabled: bool) -> None:
        self._drop_enabled = enabled
        self.setAcceptDrops(enabled)

    def dragEnterEvent(self, event: QDragEnterEvent) -> None:
        if self._drop_enabled and event.mimeData().hasFormat("application/x-combatant-id"):
            event.acceptProposedAction()
        else:
            event.ignore()

    def dragMoveEvent(self, event: QDragMoveEvent) -> None:
        if self._drop_enabled and event.mimeData().hasFormat("application/x-combatant-id"):
            event.acceptProposedAction()
        else:
            event.ignore()

    def dropEvent(self, event: QDropEvent) -> None:
        if not self._drop_enabled:
            event.ignore()
            return
        mime = event.mimeData()
        if not mime.hasFormat("application/x-combatant-id"):
            event.ignore()
            return

        dragged_id = bytes(mime.data("application/x-combatant-id")).decode("utf-8")

        # Determine drop position: find which card slot the drop occurred in
        drop_y = event.position().y()
        layout = self.layout()
        ordered_ids: list[str] = []
        dragged_collected = False
        insert_before_idx: int | None = None

        # Collect all current card IDs and find insertion point
        for i in range(layout.count()):
            item = layout.itemAt(i)
            if item is None:
                continue
            widget = item.widget()
            if widget is None:
                continue
            cid = widget.property("combatant_id")
            if cid is None:
                continue
            if cid == dragged_id:
                dragged_collected = True
                continue
            # Check if drop happened above the midpoint of this widget
            widget_mid_y = widget.y() + widget.height() / 2
            if insert_before_idx is None and drop_y < widget_mid_y:
                insert_before_idx = len(ordered_ids)
            ordered_ids.append(cid)

        # Insert dragged card at computed position
        if insert_before_idx is None:
            ordered_ids.append(dragged_id)
        else:
            ordered_ids.insert(insert_before_idx, dragged_id)

        event.acceptProposedAction()
        self.reorder_requested.emit(ordered_ids)


# ---------------------------------------------------------------------------
# CombatTrackerTab
# ---------------------------------------------------------------------------

class CombatTrackerTab(QWidget):
    """Main Combat Tracker tab.

    Constructor args:
        roller: Roller instance (shared from MainWindow)
        library: MonsterLibrary instance (shared from MainWindow)
    """

    send_to_saves = Signal(list)        # list of SaveParticipant objects (COMBAT-14)
    start_combat_requested = Signal()   # MainWindow reads sidebar and calls start_combat()

    # Default visibility for toggleable stats (all hidden by default)
    _DEFAULT_STAT_VISIBILITY: dict[str, bool] = {
        "speed":                False,
        "passive_perception":   False,
        "legendary_resistance": False,
        "legendary_actions":    False,
        "regeneration":         False,
    }

    def __init__(self, roller, library, parent=None) -> None:
        super().__init__(parent)
        self._roller = roller
        self._library = library
        self._service = CombatTrackerService()
        self._cards: dict[str, CombatantCard] = {}
        self._group_cards: dict[str, GroupCard] = {}
        self._selected_ids: set[str] = set()
        self._last_selected_id: str | None = None
        self._combat_active = False
        self._visible_stats: dict[str, bool] = dict(self._DEFAULT_STAT_VISIBILITY)

        self._build_layout()

    # ------------------------------------------------------------------
    # Layout
    # ------------------------------------------------------------------

    def _build_layout(self) -> None:
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(4, 4, 4, 4)
        main_layout.setSpacing(4)

        # ---- Toolbar ----
        toolbar = QHBoxLayout()
        toolbar.setSpacing(6)

        self._start_btn = QPushButton("Start Combat")
        self._start_btn.setToolTip(
            "Load current encounter and start combat. "
            "Reloads encounter if combat is already active."
        )
        self._start_btn.clicked.connect(self._on_start_combat)
        toolbar.addWidget(self._start_btn)

        self._roll_init_btn = QPushButton("Roll Initiative")
        self._roll_init_btn.setEnabled(False)
        self._roll_init_btn.clicked.connect(self._on_roll_initiative)
        toolbar.addWidget(self._roll_init_btn)

        self._resort_init_btn = QPushButton("Re-sort")
        self._resort_init_btn.setEnabled(False)
        self._resort_init_btn.setToolTip("Re-sort combatants by current initiative values")
        self._resort_init_btn.clicked.connect(self._on_resort_initiative)
        toolbar.addWidget(self._resort_init_btn)

        self._reset_btn = QPushButton("Reset Combat")
        self._reset_btn.setEnabled(False)
        self._reset_btn.clicked.connect(self._on_reset_combat)
        toolbar.addWidget(self._reset_btn)

        self._clear_btn = QPushButton("Clear All")
        self._clear_btn.setEnabled(False)
        self._clear_btn.clicked.connect(self._on_clear_combat)
        toolbar.addWidget(self._clear_btn)

        # Round counter
        round_font = QFont()
        round_font.setBold(True)
        round_font.setPointSize(11)
        self._round_label = QLabel("Round 1")
        self._round_label.setFont(round_font)
        toolbar.addWidget(self._round_label)

        # Initiative Mode toggle button
        self._init_mode_btn = QToolButton()
        self._init_mode_btn.setText("Initiative Mode")
        self._init_mode_btn.setCheckable(True)
        self._init_mode_btn.setChecked(True)  # ON by default
        self._init_mode_btn.setToolTip(
            "Initiative Mode ON: sorted by initiative; Next/Prev Turn visible.\n"
            "Initiative Mode OFF: manual order; Pass 1 Round visible."
        )
        self._init_mode_btn.toggled.connect(self._on_initiative_mode_toggled)
        toolbar.addWidget(self._init_mode_btn)

        # Grouping toggle button
        self._group_btn = QToolButton()
        self._group_btn.setText("Group Monsters")
        self._group_btn.setCheckable(True)
        self._group_btn.setChecked(True)  # ON by default (per locked decision)
        self._group_btn.setToolTip(
            "Group Monsters ON: same-type monsters collapsed into group cards.\n"
            "Group Monsters OFF: individual cards for all combatants."
        )
        self._group_btn.toggled.connect(self._on_grouping_toggled)
        toolbar.addWidget(self._group_btn)

        # Next/Previous Turn — visible when initiative mode ON
        self._next_turn_btn = QPushButton("Next Turn")
        self._next_turn_btn.setVisible(True)  # initiative mode ON by default
        self._next_turn_btn.clicked.connect(self._on_next_turn)
        toolbar.addWidget(self._next_turn_btn)

        self._prev_turn_btn = QPushButton("Prev Turn")
        self._prev_turn_btn.setVisible(True)
        self._prev_turn_btn.clicked.connect(self._on_previous_turn)
        toolbar.addWidget(self._prev_turn_btn)

        # Pass 1 Round — visible when initiative mode OFF
        self._pass_round_btn = QPushButton("Pass 1 Round")
        self._pass_round_btn.setVisible(False)
        self._pass_round_btn.clicked.connect(self._on_pass_one_round)
        toolbar.addWidget(self._pass_round_btn)

        toolbar.addStretch()

        # AOE Damage — enabled when selection is non-empty
        self._aoe_btn = QPushButton("AOE Damage")
        self._aoe_btn.setEnabled(False)
        self._aoe_btn.setToolTip("Apply the same damage to all selected combatants")
        self._aoe_btn.clicked.connect(self._on_aoe_damage)
        toolbar.addWidget(self._aoe_btn)

        # Group Selected — merge selected combatants into one initiative group
        self._group_btn = QPushButton("Group Selected")
        self._group_btn.setEnabled(False)
        self._group_btn.setToolTip("Merge selected combatants into one initiative group")
        self._group_btn.clicked.connect(self._on_group_selected)
        toolbar.addWidget(self._group_btn)

        # Send to Saves — enabled when selection is non-empty
        self._send_saves_btn = QPushButton("Send to Saves")
        self._send_saves_btn.setEnabled(False)
        self._send_saves_btn.setToolTip("Jump to Saves tab with selected combatants loaded")
        self._send_saves_btn.clicked.connect(self._on_send_to_saves)
        toolbar.addWidget(self._send_saves_btn)

        # Stats toggle button (gear/filter icon)
        self._gear_btn = QPushButton("Stats")
        self._gear_btn.setToolTip("Toggle stat columns")
        self._gear_btn.clicked.connect(self._on_stats_menu)
        toolbar.addWidget(self._gear_btn)

        main_layout.addLayout(toolbar)

        # ---- Inner tab widget: Combat | PCs ----
        self._inner_tabs = QTabWidget()

        # -- Combat tab (scrollable card area + combat log) --
        combat_widget = QWidget()
        combat_layout = QVBoxLayout(combat_widget)
        combat_layout.setContentsMargins(0, 0, 0, 0)
        combat_layout.setSpacing(0)

        splitter = QSplitter(Qt.Orientation.Horizontal)

        # Left: CombatantListArea (rubber-band scroll area)
        self._scroll_area = CombatantListArea()
        self._scroll_area.setWidgetResizable(True)
        self._scroll_area.box_selected.connect(self._on_box_selected)

        self._card_container = _CardContainer()
        self._card_container.reorder_requested.connect(self._on_reorder_requested)
        self._card_container.setMinimumWidth(520)
        self._card_layout = QVBoxLayout(self._card_container)
        self._card_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        self._card_layout.setSpacing(6)
        self._card_layout.setContentsMargins(4, 4, 4, 4)

        self._scroll_area.setWidget(self._card_container)
        self._scroll_area.setMinimumWidth(540)

        # Right: combat log
        self._log_panel = CombatLogPanel()

        splitter.addWidget(self._scroll_area)
        splitter.addWidget(self._log_panel)
        splitter.setStretchFactor(0, 7)
        splitter.setStretchFactor(1, 3)

        combat_layout.addWidget(splitter)

        # -- PC subtab --
        self._pc_subtab = PCSubtab()
        self._pc_subtab.pc_changed.connect(self._on_pc_changed)

        self._inner_tabs.addTab(combat_widget, "Combat")
        self._inner_tabs.addTab(self._pc_subtab, "PCs")

        main_layout.addWidget(self._inner_tabs, 1)

    # ------------------------------------------------------------------
    # Public API (called by MainWindow)
    # ------------------------------------------------------------------

    def start_combat(self, members: list[tuple]) -> None:
        """Load an encounter and initialize combat state.

        Called by MainWindow when the encounter sidebar provides a member list.
        PCs from the PC subtab are added automatically after loading monsters.
        """
        self._service.load_encounter(members, self._roller)
        # Auto-add all saved PCs
        pcs = self._pc_subtab.get_pcs()
        if pcs:
            self._service.add_pcs(pcs)
        self._rebuild_cards()
        self._combat_active = True
        self._roll_init_btn.setEnabled(True)
        self._resort_init_btn.setEnabled(True)
        self._reset_btn.setEnabled(True)
        self._clear_btn.setEnabled(True)
        self._start_btn.setText("Reload Encounter")
        n = len(self._service.state.combatants)
        self._log_panel.set_round(self._service.state.round_number)
        self._log_panel.add_entry(f"Combat started with {n} combatant(s).")
        # Switch to Combat tab
        self._inner_tabs.setCurrentIndex(0)

    def load_combat_state(self, state_dict: dict) -> None:
        """Restore from persisted state dict."""
        state = CombatState.from_dict(state_dict)
        self._service.load_state(state)
        self._rebuild_cards()
        self._combat_active = True
        self._roll_init_btn.setEnabled(True)
        self._resort_init_btn.setEnabled(True)
        self._reset_btn.setEnabled(True)
        self._clear_btn.setEnabled(True)
        self._start_btn.setText("Reload Encounter")
        # Restore log entries
        log_entries = state_dict.get("log_entries", [])
        if log_entries:
            self._log_panel.load_entries(log_entries)
        self._update_round_label()
        # Restore initiative mode button state
        init_mode = self._service.state.initiative_mode
        self._init_mode_btn.blockSignals(True)
        self._init_mode_btn.setChecked(init_mode)
        self._init_mode_btn.blockSignals(False)
        self._update_turn_buttons_visibility(init_mode)

    def get_combat_state(self) -> dict:
        """Return serializable state dict for persistence."""
        state_dict = self._service.state.to_dict()
        state_dict["log_entries"] = self._log_panel.get_entries()
        return state_dict

    def get_pcs(self) -> list[PlayerCharacter]:
        """Return current PC list from the PC subtab."""
        return self._pc_subtab.get_pcs()

    def set_pcs(self, pcs: list[PlayerCharacter]) -> None:
        """Load PCs into the PC subtab (called on startup from persistence)."""
        self._pc_subtab.set_pcs(pcs)

    def reset_combat_ui(self) -> None:
        """Clear all combat cards and reset the service (flush integration)."""
        self._service = CombatTrackerService()
        self._cards = {}
        self._group_cards = {}
        self._selected_ids = set()
        self._last_selected_id = None
        self._combat_active = False
        while self._card_layout.count():
            item = self._card_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        self._roll_init_btn.setEnabled(False)
        self._resort_init_btn.setEnabled(False)
        self._reset_btn.setEnabled(False)
        self._clear_btn.setEnabled(False)
        self._start_btn.setText("Start Combat")
        self._round_label.setText("Round 1")
        self._update_selection_buttons()

    def clear_pcs(self) -> None:
        """Clear the PC subtab (flush integration)."""
        self._pc_subtab.clear_pcs()

    # ------------------------------------------------------------------
    # Private: card management
    # ------------------------------------------------------------------

    def _rebuild_cards(self) -> None:
        """Clear layout, destroy old cards, create new CombatantCards or GroupCards."""
        # Clear selection when rebuilding
        self._selected_ids = set()
        self._last_selected_id = None

        # Remove all widgets from card layout
        while self._card_layout.count():
            item = self._card_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        self._cards = {}
        self._group_cards = {}

        state = self._service.state
        if state.grouping_enabled:
            self._rebuild_cards_grouped()
        else:
            self._rebuild_cards_ungrouped()

        # Apply current stat visibility state to all new cards
        for stat_key, visible in self._visible_stats.items():
            self._apply_stat_visible_to_all(stat_key, visible)

        # Apply drag-to-reorder based on initiative mode
        drag_on = not state.initiative_mode
        self._card_container.set_drop_enabled(drag_on)
        for card in self._cards.values():
            card.setAcceptDrops(False)  # container handles drop, not cards

        self._update_round_label()
        self._update_active_turn_highlight()
        self._update_selection_buttons()

    def _rebuild_cards_ungrouped(self) -> None:
        """Create individual CombatantCards for all combatants (no grouping)."""
        for state in self._service.state.combatants:
            card = CombatantCard(state)
            self._wire_card_signals(card)
            self._card_layout.addWidget(card)
            self._cards[state.id] = card

    def _rebuild_cards_grouped(self) -> None:
        """Group combatants by group_id; create GroupCard for multi-member groups."""
        # Collect groups in display order (preserving first-occurrence order)
        groups: dict[str, list] = {}
        group_order: list[str] = []
        singles: list = []  # combatants with unique group_id or no group

        for state in self._service.state.combatants:
            gid = state.group_id
            if not gid:
                singles.append(state)
                continue
            if gid not in groups:
                groups[gid] = []
                group_order.append(gid)
            groups[gid].append(state)

        # Build cards in initiative order (combatants already sorted by service)
        for gid in group_order:
            members = groups[gid]
            if len(members) > 1:
                # Create GroupCard for this group
                group_card = GroupCard(gid, members)
                self._wire_group_card_signals(group_card)
                self._card_layout.addWidget(group_card)
                self._group_cards[gid] = group_card
                # Also register members so _update_active_turn_highlight can find them
                for m in members:
                    # Map individual IDs to their group card for highlight
                    pass  # GroupCard handles member highlights internally
            else:
                # Single member — use individual card
                card = CombatantCard(members[0])
                self._wire_card_signals(card)
                self._card_layout.addWidget(card)
                self._cards[members[0].id] = card

        # Add standalone singles (PCs with no group_id or unique group_ids)
        for state in singles:
            card = CombatantCard(state)
            self._wire_card_signals(card)
            self._card_layout.addWidget(card)
            self._cards[state.id] = card

    def _wire_card_signals(self, card: CombatantCard) -> None:
        card.damage_entered.connect(self._on_damage)
        card.condition_add_requested.connect(self._on_condition_add_requested)
        card.initiative_changed.connect(self._on_initiative_changed)
        card.condition_clicked.connect(self._on_condition_clicked)
        card.card_clicked.connect(self._on_card_clicked)
        card.remove_requested.connect(self._on_remove_combatant)

    def _wire_group_card_signals(self, group_card: GroupCard) -> None:
        group_card.damage_entered.connect(self._on_damage)
        group_card.condition_add_requested.connect(self._on_condition_add_requested)
        group_card.initiative_changed.connect(self._on_initiative_changed)
        group_card.condition_clicked.connect(self._on_condition_clicked)

    def _refresh_cards(self) -> None:
        """Update all existing card displays without rebuilding. Updates round counter."""
        for state in self._service.state.combatants:
            if state.id in self._cards:
                self._cards[state.id].refresh(state)
        for gid, group_card in self._group_cards.items():
            members = [
                c for c in self._service.state.combatants
                if c.group_id == gid
            ]
            if members:
                group_card.refresh(members)
        self._update_round_label()

    def _update_round_label(self) -> None:
        round_num = self._service.state.round_number
        self._round_label.setText(f"Round {round_num}")
        self._log_panel.set_round(round_num)

    def _update_active_turn_highlight(self) -> None:
        """Clear all active highlights, then set active on the current turn card."""
        combatants = self._service.state.combatants
        if not combatants:
            return

        idx = self._service.state.current_turn_index
        if not (0 <= idx < len(combatants)):
            return

        active_combatant = combatants[idx]
        active_id = active_combatant.id
        active_group = active_combatant.group_id

        # Clear all individual cards
        for cid, card in self._cards.items():
            card.set_active_turn(cid == active_id)

        # Clear all group cards
        for gid, group_card in self._group_cards.items():
            is_active_group = (gid == active_group and active_group != "")
            group_card.set_active_turn(is_active_group)
            if is_active_group:
                group_card.set_member_active(active_id)
            else:
                group_card.set_member_active("")

    def _update_turn_buttons_visibility(self, initiative_mode: bool) -> None:
        """Show/hide Next/Prev Turn and Pass 1 Round based on initiative_mode."""
        self._next_turn_btn.setVisible(initiative_mode)
        self._prev_turn_btn.setVisible(initiative_mode)
        self._pass_round_btn.setVisible(not initiative_mode)

    def _update_selection_buttons(self) -> None:
        """Enable/disable AOE Damage, Send to Saves, and Group Selected based on selection."""
        has_selection = len(self._selected_ids) > 0
        self._aoe_btn.setEnabled(has_selection)
        self._send_saves_btn.setEnabled(has_selection)
        self._group_btn.setEnabled(len(self._selected_ids) >= 2)

    def _apply_selection_visuals(self) -> None:
        """Update selected state on all CombatantCard widgets."""
        for cid, card in self._cards.items():
            card.set_selected(cid in self._selected_ids)
        # GroupCards don't participate in selection individually — only individual
        # cards exposed in ungrouped mode are selectable via Ctrl/Shift/box.

    # ------------------------------------------------------------------
    # Toolbar slots
    # ------------------------------------------------------------------

    def _on_start_combat(self) -> None:
        """Triggered by 'Start Combat' / 'Reload Encounter' button.

        Emits start_combat_requested so MainWindow reads the sidebar and calls
        start_combat(members) with the actual encounter data.
        """
        self.start_combat_requested.emit()

    def _on_roll_initiative(self) -> None:
        self._service.roll_all_initiative(self._roller)
        self._rebuild_cards()
        log_entries = self._service.state.log_entries
        if log_entries:
            self._log_panel.add_entry(log_entries[-1])

    def _on_resort_initiative(self) -> None:
        """Re-sort combatants by their current initiative values without re-rolling."""
        self._service._sort_by_initiative()
        self._rebuild_cards()
        self._log_panel.add_entry("Initiative re-sorted.")

    def _on_group_selected(self) -> None:
        """Group selected combatants under a shared group_id so they render as a GroupCard."""
        if len(self._selected_ids) < 2:
            return
        # Use the first selected combatant's name as the group_id
        first_id = next(iter(self._selected_ids))
        first = self._service.get_combatant(first_id)
        group_id = first.name if first else first_id
        # Set all selected combatants' initiative to match and share group_id
        init_val = first.initiative if first else 0
        count = len(self._selected_ids)
        for cid in self._selected_ids:
            c = self._service.get_combatant(cid)
            if c:
                c.group_id = group_id
                c.initiative = init_val
        self._selected_ids.clear()
        self._rebuild_cards()
        self._log_panel.add_entry(f"Grouped {count} combatants.")

    def _on_reset_combat(self) -> None:
        reply = QMessageBox.question(
            self,
            "Reset Combat",
            "Reset all HP, conditions, and initiative?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )
        if reply == QMessageBox.StandardButton.Yes:
            self._service.reset_combat()
            self._rebuild_cards()
            self._log_panel.add_entry("Combat reset.")

    def _on_clear_combat(self) -> None:
        """Clear all combatants from the combat tracker."""
        reply = QMessageBox.question(
            self,
            "Clear All",
            "Remove all combatants from combat?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )
        if reply == QMessageBox.StandardButton.Yes:
            self.reset_combat_ui()
            self._log_panel.add_entry("Combat cleared.")

    def _on_remove_combatant(self, combatant_id: str) -> None:
        """Remove a single combatant from combat via right-click menu."""
        self._service.remove_combatant(combatant_id)
        self._selected_ids.discard(combatant_id)
        if self._last_selected_id == combatant_id:
            self._last_selected_id = None
        self._rebuild_cards()
        self._update_selection_buttons()

    def _on_initiative_mode_toggled(self, checked: bool) -> None:
        """Switch between initiative mode (sorted, Next/Prev Turn) and manual mode (Pass 1 Round)."""
        self._service.state.initiative_mode = checked
        self._update_turn_buttons_visibility(checked)

        if checked:
            # Entering initiative mode: sort combatants by initiative
            self._service._sort_by_initiative()
            self._log_panel.add_entry("Initiative mode ON — sorted by initiative.")
        else:
            self._log_panel.add_entry("Initiative mode OFF — manual order / Pass 1 Round.")

        # Rebuild cards to reflect new order and drag-to-reorder state
        self._rebuild_cards()

    def _on_grouping_toggled(self, checked: bool) -> None:
        """Toggle auto-grouping of same-type monsters."""
        self._service.state.grouping_enabled = checked
        self._rebuild_cards()

    def _on_next_turn(self) -> None:
        """Advance to the next combatant's turn."""
        if not self._combat_active:
            return
        log_entries = self._service.advance_turn()
        for entry in log_entries:
            self._log_panel.add_entry(entry)
        self._update_round_label()
        self._refresh_cards()
        self._update_active_turn_highlight()
        # Auto-scroll to active combatant
        self._scroll_to_active()

    def _on_previous_turn(self) -> None:
        """Undo the last turn advance."""
        if not self._combat_active:
            return
        success = self._service.undo_advance()
        if success:
            self._log_panel.add_entry("Turn undone.")
            self._update_round_label()
            self._refresh_cards()
            self._update_active_turn_highlight()
            self._scroll_to_active()
        else:
            self._log_panel.add_entry("Nothing to undo.")

    def _on_pass_one_round(self) -> None:
        """Decrement all conditions by 1 round in non-initiative mode."""
        if not self._combat_active:
            return
        log_entries = self._service.pass_one_round()
        for entry in log_entries:
            self._log_panel.add_entry(entry)
        self._update_round_label()
        self._refresh_cards()

    def _scroll_to_active(self) -> None:
        """Scroll the card area to show the active turn card."""
        combatants = self._service.state.combatants
        if not combatants:
            return
        idx = self._service.state.current_turn_index
        if not (0 <= idx < len(combatants)):
            return
        active_id = combatants[idx].id
        active_group = combatants[idx].group_id

        # Find the widget to scroll to
        target_widget = None
        if active_id in self._cards:
            target_widget = self._cards[active_id]
        elif active_group and active_group in self._group_cards:
            target_widget = self._group_cards[active_group]

        if target_widget is not None:
            self._scroll_area.ensureWidgetVisible(target_widget)

    # ------------------------------------------------------------------
    # Multi-select slots
    # ------------------------------------------------------------------

    def _on_card_clicked(self, combatant_id: str, modifiers) -> None:
        """Handle Ctrl-click and Shift-click selection on CombatantCards."""
        if modifiers & Qt.KeyboardModifier.ControlModifier:
            # Ctrl-click: toggle selection
            if combatant_id in self._selected_ids:
                self._selected_ids.discard(combatant_id)
            else:
                self._selected_ids.add(combatant_id)
                self._last_selected_id = combatant_id
        elif modifiers & Qt.KeyboardModifier.ShiftModifier:
            # Shift-click: select range from last selected to this card
            combatant_ids = list(self._cards.keys())
            if self._last_selected_id and self._last_selected_id in combatant_ids:
                a = combatant_ids.index(self._last_selected_id)
                b = combatant_ids.index(combatant_id) if combatant_id in combatant_ids else -1
                if b >= 0:
                    lo, hi = min(a, b), max(a, b)
                    for cid in combatant_ids[lo:hi + 1]:
                        self._selected_ids.add(cid)
            else:
                self._selected_ids.add(combatant_id)
            self._last_selected_id = combatant_id
        else:
            # Plain click without modifier — clear and select only this card
            self._selected_ids = {combatant_id}
            self._last_selected_id = combatant_id

        self._apply_selection_visuals()
        self._update_selection_buttons()

    def _on_box_selected(self, ids: set) -> None:
        """Handle rubber-band box selection result."""
        self._selected_ids = ids
        self._last_selected_id = next(iter(ids)) if ids else None
        self._apply_selection_visuals()
        self._update_selection_buttons()

    # ------------------------------------------------------------------
    # AOE Damage
    # ------------------------------------------------------------------

    def _on_aoe_damage(self) -> None:
        """Apply same damage to all selected combatants."""
        if not self._selected_ids:
            return
        dialog = _AOEDamageDialog(self)
        if dialog.exec() != QDialog.DialogCode.Accepted:
            return
        damage = dialog.get_damage()
        log_entries = self._service.apply_aoe_damage(list(self._selected_ids), damage)
        for entry in log_entries:
            self._log_panel.add_entry(entry)
        self._refresh_cards()

    # ------------------------------------------------------------------
    # Send to Saves
    # ------------------------------------------------------------------

    def _on_send_to_saves(self) -> None:
        """Resolve selected combatants to SaveParticipant objects and emit send_to_saves."""
        if not self._selected_ids:
            return

        from src.encounter.models import SaveParticipant
        from src.encounter.service import _resolve_save_bonus

        participants: list[SaveParticipant] = []
        for cid in self._selected_ids:
            state = self._service.get_combatant(cid)
            if state is None:
                continue
            if state.monster_name and self._library.has_name(state.monster_name):
                monster = self._library.get_by_name(state.monster_name)
                save_bonus = _resolve_save_bonus(monster, "CON")  # default ability for initial load
                participants.append(SaveParticipant(name=state.name, save_bonus=save_bonus))
            else:
                # PC or unresolvable monster — use save bonus 0
                participants.append(SaveParticipant(name=state.name, save_bonus=0))

        if participants:
            self.send_to_saves.emit(participants)

    # ------------------------------------------------------------------
    # Stat toggle menu
    # ------------------------------------------------------------------

    def _on_stats_menu(self) -> None:
        """Show a menu with checkable actions to toggle stat visibility on cards."""
        menu = QMenu(self)

        stat_definitions = [
            ("speed",                "Walking Speed"),
            ("passive_perception",   "Passive Perception"),
            ("legendary_resistance", "Legendary Resistance"),
            ("legendary_actions",    "Legendary Actions"),
            ("regeneration",         "Regeneration"),
        ]

        for stat_key, label in stat_definitions:
            action = menu.addAction(label)
            action.setCheckable(True)
            action.setChecked(self._visible_stats.get(stat_key, False))
            # Connect triggered(bool) so toggling works regardless of exec() return value
            action.triggered.connect(
                lambda checked, key=stat_key: self._toggle_stat(key, checked)
            )

        menu.addSeparator()

        regen_auto_action = menu.addAction("Regen Auto-Apply")
        regen_auto_action.setCheckable(True)
        regen_auto_action.setChecked(self._service._auto_regen)
        regen_auto_action.triggered.connect(
            lambda checked: self._service.set_auto_regen(checked)
        )

        menu.exec(self._gear_btn.mapToGlobal(
            self._gear_btn.rect().bottomLeft()
        ))

    def _toggle_stat(self, stat_key: str, visible: bool) -> None:
        """Update visibility state for one stat and propagate to all cards."""
        self._visible_stats[stat_key] = visible
        self._apply_stat_visible_to_all(stat_key, visible)

    def _apply_stat_visible_to_all(self, stat_key: str, visible: bool) -> None:
        """Propagate stat visibility to all current card widgets."""
        for card in self._cards.values():
            card.set_stat_visible(stat_key, visible)
        for group_card in self._group_cards.values():
            group_card.set_stat_visible(stat_key, visible)

    # ------------------------------------------------------------------
    # Drag-to-reorder
    # ------------------------------------------------------------------

    def _on_reorder_requested(self, ordered_ids: list[str]) -> None:
        """Called when the card container detects a drop reorder."""
        if self._service.state.initiative_mode:
            return  # ignore in initiative mode
        self._service.reorder_combatants(ordered_ids)
        self._rebuild_cards()

    # ------------------------------------------------------------------
    # Card action slots
    # ------------------------------------------------------------------

    def _on_damage(self, combatant_id: str, value: int) -> None:
        """Apply damage. If multiple combatants are selected, apply to all selected."""
        if len(self._selected_ids) > 1 and combatant_id in self._selected_ids:
            for cid in list(self._selected_ids):
                log_entry = self._service.apply_damage(cid, value)
                self._log_panel.add_entry(log_entry)
        else:
            log_entry = self._service.apply_damage(combatant_id, value)
            self._log_panel.add_entry(log_entry)
        self._refresh_cards()

    def _on_condition_add_requested(self, combatant_id: str) -> None:
        """Show popup with preset conditions/buffs and a Custom option."""
        menu = QMenu(self)

        # Section: Conditions
        menu.addSection("Conditions")
        for cond_def in STANDARD_CONDITIONS:
            action = menu.addAction(cond_def["name"])
            action.setData(("preset", cond_def))

        menu.addSeparator()

        # Section: Buffs / Effects
        menu.addSection("Buffs / Effects")
        for buff_def in COMMON_BUFFS:
            action = menu.addAction(buff_def["name"])
            action.setData(("preset", buff_def))

        menu.addSeparator()

        # Custom
        custom_action = menu.addAction("Custom...")
        custom_action.setData(("custom", None))

        selected = menu.exec(self.cursor().pos())
        if selected is None:
            return

        data = selected.data()
        if data is None:
            return

        kind, payload = data

        if kind == "preset":
            name = payload["name"]
            duration = payload.get("default_duration")
            from src.ui.combatant_card import CONDITION_COLORS, _DEFAULT_CONDITION_COLOR
            color = CONDITION_COLORS.get(name, _DEFAULT_CONDITION_COLOR)
            entry = ConditionEntry(name=name, duration=duration, color=color)
            # Apply to all selected if multi-select
            target_ids = (
                list(self._selected_ids)
                if len(self._selected_ids) > 1 and combatant_id in self._selected_ids
                else [combatant_id]
            )
            for cid in target_ids:
                log_entry = self._service.add_condition(cid, ConditionEntry(
                    name=name, duration=duration, color=color
                ))
                self._log_panel.add_entry(log_entry)
            self._refresh_cards()

        elif kind == "custom":
            dialog = _CustomConditionDialog(self)
            if dialog.exec() == QDialog.DialogCode.Accepted:
                name = dialog.get_condition_name()
                if name:
                    duration = dialog.get_duration()
                    # Apply to all selected if multi-select
                    target_ids = (
                        list(self._selected_ids)
                        if len(self._selected_ids) > 1 and combatant_id in self._selected_ids
                        else [combatant_id]
                    )
                    for cid in target_ids:
                        entry = ConditionEntry(name=name, duration=duration)
                        log_entry = self._service.add_condition(cid, entry)
                        self._log_panel.add_entry(log_entry)
                    self._refresh_cards()

    def _on_condition_clicked(self, combatant_id: str, condition_name: str) -> None:
        """Show edit/remove popup when a condition chip is clicked."""
        menu = QMenu(self)
        edit_action = menu.addAction("Edit Duration")
        remove_action = menu.addAction("Remove")
        dismiss_action = menu.addAction("Dismiss")

        selected = menu.exec(self.cursor().pos())
        if selected is None:
            return

        if selected == edit_action:
            combatant = self._service.get_combatant(combatant_id)
            current_duration = None
            if combatant:
                for cond in combatant.conditions:
                    if cond.name == condition_name:
                        current_duration = cond.duration
                        break
            dialog = _EditDurationDialog(condition_name, current_duration, self)
            if dialog.exec() == QDialog.DialogCode.Accepted:
                new_duration = dialog.get_duration()
                # Update condition duration directly on the combatant
                combatant = self._service.get_combatant(combatant_id)
                if combatant:
                    for cond in combatant.conditions:
                        if cond.name == condition_name:
                            cond.duration = new_duration
                            cond.expired = False
                            break
                self._log_panel.add_entry(
                    f"{combatant.name if combatant else combatant_id}: "
                    f"{condition_name} duration set to {new_duration}"
                )
                self._refresh_cards()

        elif selected in (remove_action, dismiss_action):
            log_entry = self._service.remove_condition(combatant_id, condition_name)
            self._log_panel.add_entry(log_entry)
            self._refresh_cards()

    def _on_initiative_changed(self, combatant_id: str, value: int) -> None:
        self._service.set_initiative(combatant_id, value)
        # If initiative mode, rebuild to reflect new sort order
        if self._service.state.initiative_mode:
            self._rebuild_cards()

    # ------------------------------------------------------------------
    # PC subtab slot
    # ------------------------------------------------------------------

    def _on_pc_changed(self) -> None:
        """PC subtab emitted a change; no immediate action needed here.
        MainWindow auto-save timer will catch this, or direct wiring can be added."""
        pass
