"""AttackRollerTab — full Attack Roller tab widget.

Assembles all Phase 3 UI:
- Monster name header + N (count) spinner
- Scrollable action list with per-row Roll buttons
- Controls: mode toggle, advantage toggle, nat-1/nat-20 checkboxes,
  crit controls, flat modifier, bonus dice list
- RollOutputPanel for results

Wires RollService to the UI; implements RAW/COMPARE mode switching with
result re-render (no re-roll on mode switch).
"""
from __future__ import annotations

from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QGroupBox,
    QLabel,
    QPushButton,
    QSpinBox,
    QCheckBox,
    QScrollArea,
    QSizePolicy,
)

from src.roll.service import RollService
from src.roll.models import RollRequest, RollResult
from src.ui.toggle_bar import ToggleBar
from src.ui.bonus_dice_list import BonusDiceList
from src.ui.roll_output import RollOutputPanel


class AttackRollerTab(QWidget):
    """Full Attack Roller tab.

    Construction
    ------------
    roller : Roller
        The shared session Roller instance (passed from main window).

    Public API
    ----------
    set_monster(monster)
        Called from main window when Library tab selection changes.
        Rebuilds the action list to show the selected monster's actions.
    """

    def __init__(self, roller, parent=None) -> None:
        super().__init__(parent)
        self._roller = roller
        self._roll_service = RollService()
        self._last_result: RollResult | None = None
        self._current_monster = None
        self._action_rows: list[QWidget] = []
        self._mode = "raw"

        self._setup_ui()

    # ------------------------------------------------------------------
    # UI Construction
    # ------------------------------------------------------------------

    def _setup_ui(self) -> None:
        root_layout = QVBoxLayout(self)
        root_layout.setContentsMargins(6, 6, 6, 6)
        root_layout.setSpacing(6)

        # -- Header row: monster label + N spinner -----------------------
        header_row = QHBoxLayout()
        self._monster_label = QLabel("Monster: None selected")
        self._monster_label.setSizePolicy(
            QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred
        )
        header_row.addWidget(self._monster_label)

        n_label = QLabel("N:")
        self._n_spin = QSpinBox()
        self._n_spin.setRange(1, 99)
        self._n_spin.setValue(1)
        self._n_spin.setToolTip("Number of attacks to roll")
        header_row.addWidget(n_label)
        header_row.addWidget(self._n_spin)
        root_layout.addLayout(header_row)

        # -- Action list (scrollable) ------------------------------------
        self._action_list_layout = QVBoxLayout()
        self._action_list_layout.setContentsMargins(0, 0, 0, 0)
        self._action_list_layout.setSpacing(2)
        self._action_list_layout.addStretch()

        action_list_widget = QWidget()
        action_list_widget.setLayout(self._action_list_layout)

        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setWidget(action_list_widget)
        scroll_area.setMinimumHeight(120)
        root_layout.addWidget(scroll_area)

        # -- Controls area -----------------------------------------------
        controls_row = QHBoxLayout()
        controls_row.addWidget(self._build_attack_roll_group())
        controls_row.addWidget(self._build_crit_group())
        controls_row.addWidget(self._build_modifiers_group())
        root_layout.addLayout(controls_row)

        # -- Show margin checkbox (COMPARE mode only) --------------------
        self._show_margin_check = QCheckBox("Show margin")
        self._show_margin_check.setVisible(False)
        root_layout.addWidget(self._show_margin_check)

        # -- Roll output panel -------------------------------------------
        self._output_panel = RollOutputPanel()
        root_layout.addWidget(self._output_panel)

    def _build_attack_roll_group(self) -> QGroupBox:
        group = QGroupBox("Attack Roll")
        layout = QVBoxLayout(group)

        # RAW | COMPARE mode toggle
        mode_row = QHBoxLayout()
        mode_label = QLabel("Mode:")
        self._mode_bar = ToggleBar(["RAW", "COMPARE"], default="RAW")
        self._mode_bar.value_changed.connect(self._on_mode_changed)
        mode_row.addWidget(mode_label)
        mode_row.addWidget(self._mode_bar)
        layout.addLayout(mode_row)

        # Target AC container (visible only in COMPARE mode)
        self._target_ac_widget = QWidget()
        target_ac_layout = QHBoxLayout(self._target_ac_widget)
        target_ac_layout.setContentsMargins(0, 0, 0, 0)
        target_ac_label = QLabel("Target AC:")
        self._target_ac_spin = QSpinBox()
        self._target_ac_spin.setRange(1, 30)
        self._target_ac_spin.setValue(15)
        target_ac_layout.addWidget(target_ac_label)
        target_ac_layout.addWidget(self._target_ac_spin)
        self._target_ac_widget.setVisible(False)  # hidden in RAW mode
        layout.addWidget(self._target_ac_widget)

        # Normal | Advantage | Disadvantage toggle
        adv_row = QHBoxLayout()
        adv_label = QLabel("Advantage:")
        self._adv_bar = ToggleBar(
            ["Normal", "Advantage", "Disadvantage"], default="Normal"
        )
        adv_row.addWidget(adv_label)
        adv_row.addWidget(self._adv_bar)
        layout.addLayout(adv_row)

        # Nat-1 / Nat-20 checkboxes
        self._nat1_check = QCheckBox("Nat-1 always miss")
        self._nat1_check.setChecked(True)
        self._nat20_check = QCheckBox("Nat-20 always hit")
        self._nat20_check.setChecked(True)
        layout.addWidget(self._nat1_check)
        layout.addWidget(self._nat20_check)

        return group

    def _build_crit_group(self) -> QGroupBox:
        group = QGroupBox("Crit")
        layout = QVBoxLayout(group)

        self._crit_check = QCheckBox("Enable crits")
        self._crit_check.setChecked(True)
        layout.addWidget(self._crit_check)

        crit_range_row = QHBoxLayout()
        crit_range_label = QLabel("Crit range:")
        self._crit_range_spin = QSpinBox()
        self._crit_range_spin.setRange(18, 20)
        self._crit_range_spin.setValue(20)
        self._crit_range_spin.setEnabled(True)  # enabled because crit starts checked
        crit_range_row.addWidget(crit_range_label)
        crit_range_row.addWidget(self._crit_range_spin)
        layout.addLayout(crit_range_row)

        # Crit range spinner active only when crit checkbox is checked
        self._crit_check.toggled.connect(self._crit_range_spin.setEnabled)

        return group

    def _build_modifiers_group(self) -> QGroupBox:
        group = QGroupBox("Modifiers")
        layout = QVBoxLayout(group)

        flat_row = QHBoxLayout()
        flat_label = QLabel("Flat modifier:")
        self._flat_mod_spin = QSpinBox()
        self._flat_mod_spin.setRange(-99, 99)
        self._flat_mod_spin.setValue(0)
        flat_row.addWidget(flat_label)
        flat_row.addWidget(self._flat_mod_spin)
        layout.addLayout(flat_row)

        bonus_label = QLabel("Bonus dice:")
        self._bonus_dice_list = BonusDiceList()
        layout.addWidget(bonus_label)
        layout.addWidget(self._bonus_dice_list)

        return group

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def set_monster(self, monster) -> None:
        """Called from main window when Library tab selection changes."""
        self._current_monster = monster
        name = monster.name if monster else "None selected"
        self._monster_label.setText(f"Monster: {name}")
        self._rebuild_action_list()

    # ------------------------------------------------------------------
    # Action list
    # ------------------------------------------------------------------

    def _rebuild_action_list(self) -> None:
        """Clear and rebuild action rows for self._current_monster."""
        # Remove existing rows (deleteLater is required for Qt ownership)
        for row_widget in self._action_rows:
            self._action_list_layout.removeWidget(row_widget)
            row_widget.deleteLater()
        self._action_rows = []

        if self._current_monster is None:
            return

        for action in self._current_monster.actions:
            row = self._make_action_row(action)
            # Insert before the stretch at the end
            insert_idx = self._action_list_layout.count() - 1
            self._action_list_layout.insertWidget(insert_idx, row)
            self._action_rows.append(row)

    def _make_action_row(self, action) -> QWidget:
        """Build one action row widget with label + Roll button."""
        row = QWidget()
        layout = QHBoxLayout(row)
        layout.setContentsMargins(2, 1, 2, 1)

        name_label = QLabel(action.name)
        name_label.setSizePolicy(
            QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred
        )
        roll_btn = QPushButton("Roll")

        if action.is_parsed and action.to_hit_bonus is not None:
            roll_btn.setEnabled(True)
            roll_btn.clicked.connect(
                lambda checked, a=action: self._on_roll(a)
            )
        else:
            roll_btn.setEnabled(False)
            roll_btn.setToolTip("Action could not be parsed — no roll available")
            name_label.setStyleSheet("color: gray;")

        layout.addWidget(name_label)
        layout.addWidget(roll_btn)
        return row

    # ------------------------------------------------------------------
    # Roll trigger
    # ------------------------------------------------------------------

    def _on_roll(self, action) -> None:
        """Roll N attacks for the given action using current toggle state."""
        request = self._build_roll_request(action)
        result = self._roll_service.execute_attack_roll(request, self._roller)
        self._last_result = result
        self._render_results(result)

    def _build_roll_request(self, action) -> RollRequest:
        """Assemble a RollRequest from current UI toggle state."""
        return RollRequest(
            action_name=action.name,
            to_hit_bonus=action.to_hit_bonus,
            damage_parts=action.damage_parts,
            count=self._n_spin.value(),
            mode=self._mode_bar.value().lower(),  # "raw" or "compare"
            target_ac=(
                self._target_ac_spin.value() if self._mode == "compare" else None
            ),
            advantage=self._adv_bar.value().lower(),
            crit_enabled=self._crit_check.isChecked(),
            crit_range=self._crit_range_spin.value(),
            nat1_always_miss=self._nat1_check.isChecked(),
            nat20_always_hit=self._nat20_check.isChecked(),
            flat_modifier=self._flat_mod_spin.value(),
            bonus_dice=self._bonus_dice_list.get_entries(),
            show_margin=self._show_margin_check.isChecked(),
            seed=None,  # Phase 6 (Settings) wires the global seed
        )

    # ------------------------------------------------------------------
    # Mode switching
    # ------------------------------------------------------------------

    def _on_mode_changed(self, mode: str) -> None:
        """Handle RAW/COMPARE mode toggle."""
        self._mode = mode.lower()
        self._target_ac_widget.setVisible(self._mode == "compare")
        self._show_margin_check.setVisible(self._mode == "compare")
        if self._last_result is not None:
            self._render_results(self._last_result)

    # ------------------------------------------------------------------
    # Result rendering
    # ------------------------------------------------------------------

    def _render_results(self, result: RollResult) -> None:
        """Re-render stored results in the current mode (no re-roll)."""
        self._output_panel.clear()
        mode = result.request.mode
        for attack in result.attack_rolls:
            line = self._format_attack_line(attack, result.request)
            self._output_panel.append(line)
        if mode == "compare":
            self._output_panel.append(self._format_summary(result.summary))

    def _format_attack_line(self, attack, request) -> str:
        """Format one attack result as a compact single-line string."""
        mode = request.mode
        n = attack.attack_number

        if mode == "raw":
            return self._format_raw_line(attack)
        else:
            return self._format_compare_line(attack, request)

    def _format_raw_line(self, attack) -> str:
        """Format RAW mode: #N: d20=14 (+5 hit)(+2 flat)(+3 bless) -> 24  |  8 slashing"""
        n = attack.attack_number

        # d20 display
        faces = attack.d20_faces
        if len(faces) == 2:
            vals = [f.value for f in faces]
            kept_val = attack.d20_natural
            adv_label = "adv" if faces[0].kept == (faces[0].value >= faces[1].value) else "disadv"
            # Determine advantage or disadvantage from which was kept
            kept_face = next(f for f in faces if f.kept)
            other_face = next(f for f in faces if not f.kept)
            if kept_face.value >= other_face.value:
                adv_label = "adv"
            else:
                adv_label = "disadv"
            d20_str = f"d20=[{kept_face.value}, {other_face.value}]({adv_label})"
        else:
            d20_str = f"d20={attack.d20_natural}"

        if attack.is_crit:
            d20_str += " [CRIT]"

        # Bonus components
        parts = [d20_str]
        if attack.to_hit_bonus != 0:
            sign = "+" if attack.to_hit_bonus >= 0 else ""
            parts.append(f"({sign}{attack.to_hit_bonus} hit)")
        if attack.flat_modifier != 0:
            sign = "+" if attack.flat_modifier >= 0 else ""
            parts.append(f"({sign}{attack.flat_modifier} flat)")
        for (formula, signed_total, label) in attack.bonus_dice_results:
            lbl = label if label else formula
            sign = "+" if signed_total >= 0 else ""
            parts.append(f"({sign}{signed_total} {lbl})")

        roll_str = " ".join(parts)

        # Damage
        if attack.damage_parts:
            dmg_str = " + ".join(
                f"{dp.total} {dp.damage_type}" for dp in attack.damage_parts
            )
            return f"#{n}: {roll_str} \u2192 {attack.attack_total}  |  {dmg_str}"
        else:
            return f"#{n}: {roll_str} \u2192 {attack.attack_total}"

    def _format_compare_line(self, attack, request) -> str:
        """Format COMPARE mode: #N: 24 vs AC15 -> HIT [CRIT]  |  16 slashing"""
        n = attack.attack_number
        ac = request.target_ac

        if attack.is_hit:
            hit_label = "HIT"
            if attack.is_crit:
                hit_label += " [CRIT]"
            if attack.damage_parts:
                dmg_str = " + ".join(
                    f"{dp.total} {dp.damage_type}" for dp in attack.damage_parts
                )
                return f"#{n}: {attack.attack_total} vs AC{ac} \u2192 {hit_label}  |  {dmg_str}"
            else:
                return f"#{n}: {attack.attack_total} vs AC{ac} \u2192 {hit_label}"
        else:
            if request.show_margin and attack.margin is not None:
                margin_abs = abs(attack.margin)
                return f"#{n}: {attack.attack_total} vs AC{ac} \u2192 Miss by {margin_abs}"
            else:
                return f"#{n}: {attack.attack_total} vs AC{ac} \u2192 Miss"

    def _format_summary(self, summary) -> str:
        """Format COMPARE mode summary line."""
        crit_str = f" ({summary.crits} crit)" if summary.crits else ""
        return (
            f"\u2500\u2500\u2500 Summary: {summary.hits} hits / "
            f"{summary.misses} misses{crit_str} | "
            f"Total damage: {summary.total_damage} \u2500\u2500\u2500"
        )
