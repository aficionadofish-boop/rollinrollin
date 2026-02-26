"""CombatTrackerTab — main Combat Tracker tab widget.

Orchestrates CombatantCards, CombatLogPanel, and CombatTrackerService.
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
)
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QFont

from src.combat.models import (
    CombatState,
    ConditionEntry,
    STANDARD_CONDITIONS,
    COMMON_BUFFS,
)
from src.combat.service import CombatTrackerService
from src.ui.combatant_card import CombatantCard
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
# CombatTrackerTab
# ---------------------------------------------------------------------------

class CombatTrackerTab(QWidget):
    """Main Combat Tracker tab.

    Constructor args:
        roller: Roller instance (shared from MainWindow)
        library: MonsterLibrary instance (shared from MainWindow)
    """

    send_to_saves = Signal(list)   # list of selected combatant data (COMBAT-14, Plan 04)

    def __init__(self, roller, library, parent=None) -> None:
        super().__init__(parent)
        self._roller = roller
        self._library = library
        self._service = CombatTrackerService()
        self._cards: dict[str, CombatantCard] = {}
        self._selected_ids: set[str] = set()
        self._combat_active = False

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

        self._reset_btn = QPushButton("Reset Combat")
        self._reset_btn.setEnabled(False)
        self._reset_btn.clicked.connect(self._on_reset_combat)
        toolbar.addWidget(self._reset_btn)

        # Round counter
        round_font = QFont()
        round_font.setBold(True)
        round_font.setPointSize(11)
        self._round_label = QLabel("Round 1")
        self._round_label.setFont(round_font)
        toolbar.addWidget(self._round_label)

        # Next/Previous Turn — hidden; shown by Plan 03 when initiative mode wired
        self._next_turn_btn = QPushButton("Next Turn")
        self._next_turn_btn.setVisible(False)
        toolbar.addWidget(self._next_turn_btn)

        self._prev_turn_btn = QPushButton("Prev Turn")
        self._prev_turn_btn.setVisible(False)
        toolbar.addWidget(self._prev_turn_btn)

        # Pass 1 Round — hidden; shown by Plan 03
        self._pass_round_btn = QPushButton("Pass 1 Round")
        self._pass_round_btn.setVisible(False)
        toolbar.addWidget(self._pass_round_btn)

        toolbar.addStretch()

        # AOE Damage — disabled until Plan 04 multi-select
        self._aoe_btn = QPushButton("AOE Damage")
        self._aoe_btn.setEnabled(False)
        toolbar.addWidget(self._aoe_btn)

        # Send to Saves — disabled until Plan 04 wiring
        self._send_saves_btn = QPushButton("Send to Saves")
        self._send_saves_btn.setEnabled(False)
        toolbar.addWidget(self._send_saves_btn)

        # Gear icon — placeholder for stats toggle (Plan 03)
        self._gear_btn = QPushButton("Stats")
        self._gear_btn.setToolTip("Toggle stat columns (Plan 03)")
        self._gear_btn.setEnabled(False)
        toolbar.addWidget(self._gear_btn)

        main_layout.addLayout(toolbar)

        # ---- Body splitter ----
        splitter = QSplitter(Qt.Orientation.Horizontal)

        # Left: scrollable card area
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)

        card_container = QWidget()
        self._card_layout = QVBoxLayout(card_container)
        self._card_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        self._card_layout.setSpacing(6)
        self._card_layout.setContentsMargins(4, 4, 4, 4)

        scroll_area.setWidget(card_container)

        # Right: combat log
        self._log_panel = CombatLogPanel()

        splitter.addWidget(scroll_area)
        splitter.addWidget(self._log_panel)
        splitter.setStretchFactor(0, 7)
        splitter.setStretchFactor(1, 3)

        main_layout.addWidget(splitter, 1)

    # ------------------------------------------------------------------
    # Public API (called by MainWindow)
    # ------------------------------------------------------------------

    def start_combat(self, members: list[tuple]) -> None:
        """Load an encounter and initialize combat state.

        Called by MainWindow when the encounter sidebar provides a member list.
        """
        self._service.load_encounter(members, self._roller)
        self._rebuild_cards()
        self._combat_active = True
        self._roll_init_btn.setEnabled(True)
        self._reset_btn.setEnabled(True)
        self._start_btn.setText("Reload Encounter")
        n = len(self._service.state.combatants)
        self._log_panel.set_round(self._service.state.round_number)
        self._log_panel.add_entry(f"Combat started with {n} combatant(s).")

    def load_combat_state(self, state_dict: dict) -> None:
        """Restore from persisted state dict."""
        state = CombatState.from_dict(state_dict)
        self._service.load_state(state)
        self._rebuild_cards()
        self._combat_active = True
        self._roll_init_btn.setEnabled(True)
        self._reset_btn.setEnabled(True)
        self._start_btn.setText("Reload Encounter")
        # Restore log entries
        log_entries = state_dict.get("log_entries", [])
        if log_entries:
            self._log_panel.load_entries(log_entries)
        self._update_round_label()

    def get_combat_state(self) -> dict:
        """Return serializable state dict for persistence."""
        state_dict = self._service.state.to_dict()
        state_dict["log_entries"] = self._log_panel.get_entries()
        return state_dict

    # ------------------------------------------------------------------
    # Private: card management
    # ------------------------------------------------------------------

    def _rebuild_cards(self) -> None:
        """Clear layout, destroy old cards, create new CombatantCards."""
        # Remove all widgets from card layout
        while self._card_layout.count():
            item = self._card_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        self._cards = {}

        for state in self._service.state.combatants:
            card = CombatantCard(state)
            card.damage_entered.connect(self._on_damage)
            card.condition_add_requested.connect(self._on_condition_add_requested)
            card.initiative_changed.connect(self._on_initiative_changed)
            card.condition_clicked.connect(self._on_condition_clicked)
            self._card_layout.addWidget(card)
            self._cards[state.id] = card

        self._update_round_label()

    def _refresh_cards(self) -> None:
        """Update all existing card displays without rebuilding. Updates round counter."""
        for state in self._service.state.combatants:
            if state.id in self._cards:
                self._cards[state.id].refresh(state)
        self._update_round_label()

    def _update_round_label(self) -> None:
        round_num = self._service.state.round_number
        self._round_label.setText(f"Round {round_num}")
        self._log_panel.set_round(round_num)

    # ------------------------------------------------------------------
    # Toolbar slots
    # ------------------------------------------------------------------

    def _on_start_combat(self) -> None:
        """Triggered by 'Start Combat' / 'Reload Encounter' button.

        The actual encounter members come from MainWindow via start_combat().
        This button requests the MainWindow to provide members; the tab
        itself is wired so that MainWindow calls start_combat(members) directly.
        Without encounter data this is a no-op with an informative message.
        """
        if not self._combat_active:
            # No encounter members yet — inform the user
            QMessageBox.information(
                self,
                "No Encounter",
                "Build an encounter in the sidebar first, then click 'Start Combat'.",
            )
        # If already active, the button text is "Reload Encounter".
        # Reloading is done via MainWindow calling start_combat() again;
        # this button is just a trigger routed through MainWindow.
        # (This is wired in app.py during Phase 11 Plan 04.)

    def _on_roll_initiative(self) -> None:
        self._service.roll_all_initiative(self._roller)
        self._rebuild_cards()
        log_entries = [
            e for e in self._service.state.log_entries
            if "initiative" in e.lower() or "Initiative" in e
        ]
        if log_entries:
            self._log_panel.add_entry(log_entries[-1])

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

    # ------------------------------------------------------------------
    # Card action slots
    # ------------------------------------------------------------------

    def _on_damage(self, combatant_id: str, value: int) -> None:
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
            log_entry = self._service.add_condition(combatant_id, entry)
            self._log_panel.add_entry(log_entry)
            self._refresh_cards()

        elif kind == "custom":
            dialog = _CustomConditionDialog(self)
            if dialog.exec() == QDialog.DialogCode.Accepted:
                name = dialog.get_condition_name()
                if name:
                    duration = dialog.get_duration()
                    entry = ConditionEntry(name=name, duration=duration)
                    log_entry = self._service.add_condition(combatant_id, entry)
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
