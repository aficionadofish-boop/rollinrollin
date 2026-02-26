"""AttackRollerTab — full Attack Roller tab widget.

Assembles all Phase 3 UI:
- Scrollable grouped attack list (populated from shared encounter creature list)
- Controls: mode toggle, advantage toggle, nat-1/nat-20 checkboxes,
  crit controls, flat modifier, bonus dice list, N attacks spinner
- RollOutputPanel for results

Wires RollService to the UI; implements RAW/COMPARE mode switching with
result re-render (no re-roll on mode switch).
"""
from __future__ import annotations

from PySide6.QtCore import Qt
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

# ---------------------------------------------------------------------------
# Damage type color palette
# ---------------------------------------------------------------------------

DAMAGE_COLORS: dict[str, str] = {
    # Physical — neutral/understated (user decision: "feel understated, let magical pop")
    "slashing":    "#A0A8B0",   # slate gray
    "piercing":    "#8A9BA8",   # steel gray
    "bludgeoning": "#909090",   # neutral gray
    # Magical — distinct intuitive colors
    "fire":        "#FF6B35",   # orange-red
    "cold":        "#7EC8E3",   # ice blue
    "lightning":   "#FFD700",   # gold-yellow
    "acid":        "#7FFF00",   # chartreuse green
    "poison":      "#6B8E23",   # olive green
    "necrotic":    "#9B59B6",   # purple
    "radiant":     "#FFF44F",   # bright yellow
    "force":       "#E040FB",   # magenta
    "psychic":     "#FF69B4",   # hot pink
    "thunder":     "#4169E1",   # royal blue
}
_DEFAULT_DAMAGE_COLOR = "#CCCCCC"  # fallback for unknown types


class AttackRollerTab(QWidget):
    """Full Attack Roller tab.

    Construction
    ------------
    roller : Roller
        The shared session Roller instance (passed from main window).

    Public API
    ----------
    set_creatures(creatures)
        Called from main window when encounter member list changes.
        Rebuilds the grouped attack list.
    """

    def __init__(self, roller, parent=None) -> None:
        super().__init__(parent)
        self._roller = roller
        self._roll_service = RollService()
        self._last_result: RollResult | None = None
        self._creatures: list[tuple] = []  # [(Monster, count), ...]
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

        # -- Placeholder (shown when no creatures loaded) -----------------
        self._placeholder_label = QLabel(
            "Add creatures from the Library to see their attacks"
        )
        self._placeholder_label.setStyleSheet("color: gray; padding: 12px;")
        self._placeholder_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        root_layout.addWidget(self._placeholder_label)

        # -- Grouped attack list (scrollable) -----------------------------
        self._action_list_layout = QVBoxLayout()
        self._action_list_layout.setContentsMargins(0, 0, 0, 0)
        self._action_list_layout.setSpacing(2)
        self._action_list_layout.addStretch()

        action_list_widget = QWidget()
        action_list_widget.setLayout(self._action_list_layout)

        self._action_scroll = QScrollArea()
        self._action_scroll.setWidgetResizable(True)
        self._action_scroll.setWidget(action_list_widget)
        self._action_scroll.setMinimumHeight(140)
        self._action_scroll.setVisible(False)  # hidden until creatures added
        root_layout.addWidget(self._action_scroll)

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

        # N (number of attacks) spinner
        n_row = QHBoxLayout()
        n_label = QLabel("N:")
        self._n_spin = QSpinBox()
        self._n_spin.setRange(1, 99)
        self._n_spin.setValue(1)
        self._n_spin.setToolTip("Number of attacks to roll")
        n_row.addWidget(n_label)
        n_row.addWidget(self._n_spin)
        layout.addLayout(n_row)

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
        self._crit_range_spin.setRange(2, 20)
        self._crit_range_spin.setValue(20)
        self._crit_range_spin.setEnabled(True)  # enabled because crit starts checked
        crit_range_row.addWidget(crit_range_label)
        crit_range_row.addWidget(self._crit_range_spin)
        layout.addLayout(crit_range_row)

        # Crit range spinner active only when crit checkbox is checked
        self._crit_check.toggled.connect(self._crit_range_spin.setEnabled)

        self._crunchy_crits_check = QCheckBox("Crunchy Crits")
        self._crunchy_crits_check.setToolTip(
            "Maximize base damage dice; only the extra crit dice are rolled.\n"
            "E.g. 1d8+4 crit → 8 (max) + 4 + Xd8 (rolled)"
        )
        self._crunchy_crits_check.setChecked(False)
        layout.addWidget(self._crunchy_crits_check)

        self._brutal_crits_check = QCheckBox("Brutal Crits")
        self._brutal_crits_check.setToolTip(
            "Maximize all damage dice on a crit — no rolling, everything is maximum.\n"
            "E.g. 1d8+4 crit → 8 (max) + 4 + 8 (max)"
        )
        self._brutal_crits_check.setChecked(False)
        layout.addWidget(self._brutal_crits_check)

        # Mutually exclusive — checking one unchecks the other
        self._crunchy_crits_check.toggled.connect(
            lambda checked: self._brutal_crits_check.setChecked(False) if checked else None
        )
        self._brutal_crits_check.toggled.connect(
            lambda checked: self._crunchy_crits_check.setChecked(False) if checked else None
        )

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

    def set_creatures(self, creatures: list) -> None:
        """Called from MainWindow when encounter member list changes.

        Args:
            creatures: list of (Monster, int) tuples from EncounterMemberList.
        """
        self._creatures = creatures
        self._rebuild_action_list()

    def set_active_creature(self, monster) -> None:
        """Preload a specific monster into the Attack Roller (single-click from sidebar).

        Ensures the monster is in self._creatures (adds it if missing), then
        rebuilds the action list and scrolls to the creature's header.

        Args:
            monster: Monster dataclass instance to focus on.
        """
        if monster is None:
            return

        # Add if missing
        names = [m.name for m, _ in self._creatures]
        if monster.name not in names:
            self._creatures = list(self._creatures) + [(monster, 1)]
            self._rebuild_action_list()

        # Scroll to the creature's header in the action list
        for widget in self._action_rows:
            if isinstance(widget, QLabel) and monster.name in widget.text():
                self._action_scroll.ensureWidgetVisible(widget)
                break

    # ------------------------------------------------------------------
    # Action list
    # ------------------------------------------------------------------

    def _rebuild_action_list(self) -> None:
        """Clear and rebuild action rows, grouped by creature."""
        # Remove existing dynamic widgets
        for row_widget in self._action_rows:
            self._action_list_layout.removeWidget(row_widget)
            row_widget.deleteLater()
        self._action_rows = []

        if not self._creatures:
            self._placeholder_label.setVisible(True)
            self._action_scroll.setVisible(False)
            return

        self._placeholder_label.setVisible(False)
        self._action_scroll.setVisible(True)

        for monster, count in self._creatures:
            # Filter to rollable attacks only
            rollable = [
                a for a in monster.actions
                if a.is_parsed and a.to_hit_bonus is not None
            ]
            if not rollable:
                continue

            # Creature header
            if count > 1:
                header_text = f"\u2500\u2500 {monster.name} (x{count}) \u2500\u2500"
            else:
                header_text = f"\u2500\u2500 {monster.name} \u2500\u2500"

            header_label = QLabel(header_text)
            header_label.setStyleSheet("font-weight: bold; padding: 4px 0 2px 0;")
            insert_idx = self._action_list_layout.count() - 1
            self._action_list_layout.insertWidget(insert_idx, header_label)
            self._action_rows.append(header_label)

            # Buff label — show active buffs if any (EDIT-10 cross-tab visibility)
            buffs = getattr(monster, "buffs", [])
            if buffs:
                buff_parts = [
                    f"{b.name} ({b.bonus_value} {b.targets.replace('_', ' ')})"
                    for b in buffs
                ]
                buff_label = QLabel(f"Buffs: {', '.join(buff_parts)}")
                buff_label.setStyleSheet(
                    "color: #8ecae6; font-size: 8pt; padding: 0 0 2px 16px;"
                )
                buff_label.setWordWrap(True)
                insert_idx = self._action_list_layout.count() - 1
                self._action_list_layout.insertWidget(insert_idx, buff_label)
                self._action_rows.append(buff_label)

            # Action rows for this creature
            for action in rollable:
                row = self._make_action_row(action)
                insert_idx = self._action_list_layout.count() - 1
                self._action_list_layout.insertWidget(insert_idx, row)
                self._action_rows.append(row)

    def _make_action_row(self, action) -> QWidget:
        """Build one action row: 'Scimitar (+4)  [Roll]'."""
        row = QWidget()
        layout = QHBoxLayout(row)
        layout.setContentsMargins(16, 1, 2, 1)  # 16px left indent for grouping

        bonus_sign = "+" if action.to_hit_bonus >= 0 else ""
        label_text = f"{action.name} ({bonus_sign}{action.to_hit_bonus})"
        name_label = QLabel(label_text)
        name_label.setSizePolicy(
            QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred
        )

        roll_btn = QPushButton("Roll")
        roll_btn.clicked.connect(
            lambda checked, a=action: self._on_roll(a)
        )

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
            crunchy_crits=self._crunchy_crits_check.isChecked(),
            brutal_crits=self._brutal_crits_check.isChecked(),
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
            line = self._format_attack_line_html(attack, result.request)
            self._output_panel.append_html(line)
        if mode == "compare":
            self._output_panel.append_html(self._format_summary_html(result.summary))

    def _format_attack_line(self, attack, request) -> str:
        """Format one attack result as a compact single-line string."""
        if request.mode == "raw":
            return self._format_raw_line(attack, request)
        else:
            return self._format_compare_line(attack, request)

    def _d20_str(self, attack) -> str:
        """Format the d20 roll portion, including secondary die for adv/disadv."""
        faces = attack.d20_faces
        if len(faces) == 2:
            kept_face = next(f for f in faces if f.kept)
            other_face = next(f for f in faces if not f.kept)
            adv_label = "adv" if kept_face.value >= other_face.value else "disadv"
            return f"d20=[{kept_face.value}, {other_face.value}]({adv_label})"
        return f"d20={attack.d20_natural}"

    def _damage_str(self, attack, request) -> str:
        """Format damage parts, showing crit extra dice breakdown when present."""
        if not attack.damage_parts:
            return ""
        parts = []
        extra_list = attack.crit_extra_parts
        for i, dp in enumerate(attack.damage_parts):
            if attack.is_crit and i < len(extra_list):
                extra = extra_list[i]
                combined = dp.total + extra.total
                if request.brutal_crits:
                    note = f"{dp.total}+{extra.total} [all max]"
                elif request.crunchy_crits:
                    note = f"{dp.total}[max]+{extra.total} crit"
                else:
                    note = f"{dp.total}+{extra.total} crit"
                parts.append(f"{combined} {dp.damage_type} ({note})")
            else:
                parts.append(f"{dp.total} {dp.damage_type}")
        return " + ".join(parts)

    def _format_raw_line(self, attack, request) -> str:
        """Format RAW mode: #N: d20=14 (+5 hit)(+2 flat)(+3 bless) -> 24  |  8 slashing"""
        n = attack.attack_number

        d20_str = self._d20_str(attack)
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

        dmg_str = self._damage_str(attack, request)
        if dmg_str:
            return f"#{n}: {roll_str} \u2192 {attack.attack_total}  |  {dmg_str}"
        return f"#{n}: {roll_str} \u2192 {attack.attack_total}"

    def _format_compare_line(self, attack, request) -> str:
        """Format COMPARE mode: #N: [d20 adv] 24 vs AC15 -> HIT [CRIT]  |  16 slashing"""
        n = attack.attack_number
        ac = request.target_ac

        # Critical miss — show no further math
        if attack.is_nat1 and request.nat1_always_miss and attack.is_hit is False:
            return f"#{n}: CRITICAL MISS"

        # Secondary d20 prefix for advantage/disadvantage
        d20_prefix = ""
        if len(attack.d20_faces) == 2:
            kept_face = next(f for f in attack.d20_faces if f.kept)
            other_face = next(f for f in attack.d20_faces if not f.kept)
            adv_label = "adv" if kept_face.value >= other_face.value else "disadv"
            d20_prefix = f"[d20={kept_face.value}/{other_face.value} {adv_label}] "

        if attack.is_hit:
            hit_label = "HIT"
            if attack.is_crit:
                hit_label += " [CRIT]"
            dmg_str = self._damage_str(attack, request)
            if dmg_str:
                return f"#{n}: {d20_prefix}{attack.attack_total} vs AC{ac} \u2192 {hit_label}  |  {dmg_str}"
            return f"#{n}: {d20_prefix}{attack.attack_total} vs AC{ac} \u2192 {hit_label}"
        else:
            if request.show_margin and attack.margin is not None:
                margin_abs = abs(attack.margin)
                return f"#{n}: {d20_prefix}{attack.attack_total} vs AC{ac} \u2192 Miss by {margin_abs}"
            return f"#{n}: {d20_prefix}{attack.attack_total} vs AC{ac} \u2192 Miss"

    def _format_summary(self, summary) -> str:
        """Format COMPARE mode summary line."""
        crit_str = f" ({summary.crits} crit)" if summary.crits else ""
        return (
            f"\u2500\u2500\u2500 Summary: {summary.hits} hits / "
            f"{summary.misses} misses{crit_str} | "
            f"Total damage: {summary.total_damage} \u2500\u2500\u2500"
        )

    # ------------------------------------------------------------------
    # HTML formatting helpers
    # ------------------------------------------------------------------

    def _html_escape(self, text: str) -> str:
        """Escape HTML special characters in roll output text."""
        return text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")

    def _color_damage_segment(self, total: int, dtype: str, note: str = "") -> str:
        """Wrap a damage segment in a colored <span>. Colors the entire segment per user decision."""
        color = DAMAGE_COLORS.get(dtype.lower(), _DEFAULT_DAMAGE_COLOR)
        text = f"{total} {dtype}"
        if note:
            text += f" ({note})"
        return f'<span style="color:{color};">{text}</span>'

    def _wrap_crit_line(self, html_content: str) -> str:
        """Wrap content in a crit highlight background (gold tint). Per user decision: color + full row background."""
        return (
            f'<div style="background-color:rgba(212,175,55,0.25); padding:1px 4px; border-radius:2px;">'
            f'{html_content}</div>'
        )

    def _wrap_miss_line(self, html_content: str) -> str:
        """Wrap content in a miss highlight background (red tint). Per user decision: row highlight treatment."""
        return (
            f'<div style="background-color:rgba(180,0,0,0.18); padding:1px 4px; border-radius:2px;">'
            f'{html_content}</div>'
        )

    # ------------------------------------------------------------------
    # HTML format methods (parallel to plain-text methods)
    # ------------------------------------------------------------------

    def _damage_str_html(self, attack, request) -> str:
        """Format damage parts as HTML with per-type color spans."""
        if not attack.damage_parts:
            return ""
        parts = []
        extra_list = attack.crit_extra_parts
        for i, dp in enumerate(attack.damage_parts):
            if attack.is_crit and i < len(extra_list):
                extra = extra_list[i]
                combined = dp.total + extra.total
                if request.brutal_crits:
                    note = f"{dp.total}+{extra.total} [all max]"
                elif request.crunchy_crits:
                    note = f"{dp.total}[max]+{extra.total} crit"
                else:
                    note = f"{dp.total}+{extra.total} crit"
                parts.append(self._color_damage_segment(combined, dp.damage_type, note))
            else:
                parts.append(self._color_damage_segment(dp.total, dp.damage_type))
        return " + ".join(parts)

    def _format_raw_line_html(self, attack, request) -> str:
        """Format RAW mode attack line as HTML with colored damage and crit highlight."""
        n = attack.attack_number

        d20_str = self._html_escape(self._d20_str(attack))
        if attack.is_crit:
            d20_str += " [CRIT]"

        # Bonus components (plain text, HTML-escaped)
        parts = [d20_str]
        if attack.to_hit_bonus != 0:
            sign = "+" if attack.to_hit_bonus >= 0 else ""
            parts.append(self._html_escape(f"({sign}{attack.to_hit_bonus} hit)"))
        if attack.flat_modifier != 0:
            sign = "+" if attack.flat_modifier >= 0 else ""
            parts.append(self._html_escape(f"({sign}{attack.flat_modifier} flat)"))
        for (formula, signed_total, label) in attack.bonus_dice_results:
            lbl = label if label else formula
            sign = "+" if signed_total >= 0 else ""
            parts.append(self._html_escape(f"({sign}{signed_total} {lbl})"))

        roll_str = " ".join(parts)

        dmg_str = self._damage_str_html(attack, request)
        if dmg_str:
            line = f"#{n}: {roll_str} \u2192 {attack.attack_total}&nbsp;&nbsp;|&nbsp;&nbsp;{dmg_str}"
        else:
            line = f"#{n}: {roll_str} \u2192 {attack.attack_total}"

        if attack.is_crit:
            return self._wrap_crit_line(line)
        return line

    def _format_compare_line_html(self, attack, request) -> str:
        """Format COMPARE mode attack line as HTML with colored damage and crit/miss highlights."""
        n = attack.attack_number
        ac = request.target_ac

        # Critical miss — red tint background
        if attack.is_nat1 and request.nat1_always_miss and attack.is_hit is False:
            return self._wrap_miss_line(f"#{n}: CRITICAL MISS")

        # Secondary d20 prefix for advantage/disadvantage
        d20_prefix = ""
        if len(attack.d20_faces) == 2:
            kept_face = next(f for f in attack.d20_faces if f.kept)
            other_face = next(f for f in attack.d20_faces if not f.kept)
            adv_label = "adv" if kept_face.value >= other_face.value else "disadv"
            d20_prefix = self._html_escape(
                f"[d20={kept_face.value}/{other_face.value} {adv_label}] "
            )

        if attack.is_hit:
            hit_label = "HIT"
            if attack.is_crit:
                hit_label += " [CRIT]"
            dmg_str = self._damage_str_html(attack, request)
            if dmg_str:
                line = (
                    f"#{n}: {d20_prefix}{attack.attack_total} vs AC{ac} "
                    f"\u2192 {hit_label}&nbsp;&nbsp;|&nbsp;&nbsp;{dmg_str}"
                )
            else:
                line = f"#{n}: {d20_prefix}{attack.attack_total} vs AC{ac} \u2192 {hit_label}"
            if attack.is_crit:
                return self._wrap_crit_line(line)
            return line
        else:
            if request.show_margin and attack.margin is not None:
                margin_abs = abs(attack.margin)
                line = f"#{n}: {d20_prefix}{attack.attack_total} vs AC{ac} \u2192 Miss by {margin_abs}"
            else:
                line = f"#{n}: {d20_prefix}{attack.attack_total} vs AC{ac} \u2192 Miss"
            return self._wrap_miss_line(line)

    def _format_attack_line_html(self, attack, request) -> str:
        """Dispatch to the appropriate HTML format method based on mode."""
        if request.mode == "raw":
            return self._format_raw_line_html(attack, request)
        else:
            return self._format_compare_line_html(attack, request)

    def _format_summary_html(self, summary) -> str:
        """Format COMPARE mode summary line as HTML-escaped text."""
        crit_str = self._html_escape(
            f" ({summary.crits} crit)" if summary.crits else ""
        )
        return (
            f"\u2500\u2500\u2500 Summary: {summary.hits} hits / "
            f"{summary.misses} misses{crit_str} | "
            f"Total damage: {summary.total_damage} \u2500\u2500\u2500"
        )

    # ------------------------------------------------------------------
    # Settings integration
    # ------------------------------------------------------------------

    def apply_defaults(self, settings) -> None:
        """Apply saved default settings to UI controls. Called by MainWindow."""
        self._mode_bar.set_value("RAW" if settings.default_mode == "raw" else "COMPARE")
        self._adv_bar.set_value(settings.default_advantage_mode.capitalize())
        self._nat1_check.setChecked(settings.default_nat1_always_miss)
        self._nat20_check.setChecked(settings.default_nat20_always_hit)
        self._crit_check.setChecked(settings.default_crit_enabled)
        self._crit_range_spin.setValue(settings.default_crit_range)
        self._target_ac_spin.setValue(settings.default_target_ac)

    def set_seeded_mode(self, enabled: bool) -> None:
        """Show or hide the seeded badge on the output panel."""
        self._output_panel.set_seeded_mode(enabled)
