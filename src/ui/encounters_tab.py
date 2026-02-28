"""SavesTab — Save Roller tab with feature detection, per-row results, and LR tracking."""
from __future__ import annotations

from PySide6.QtWidgets import (
    QWidget,
    QHBoxLayout,
    QVBoxLayout,
    QLabel,
    QSpinBox,
    QPushButton,
    QScrollArea,
    QSizePolicy,
    QCheckBox,
    QGroupBox,
    QComboBox,
    QFrame,
    QLineEdit,
)
from PySide6.QtCore import Signal, Qt

from src.encounter.models import SaveParticipant, SaveRequest
from src.encounter.service import (
    SaveRollService,
    _resolve_save_bonus,
    FeatureDetectionService,
    FeatureRule,
    BUILTIN_RULES,
)
from src.roll.models import BonusDiceEntry
from src.ui.toggle_bar import ToggleBar
from src.ui.bonus_dice_list import BonusDiceList
from src.ui.roll_output import RollOutputPanel


# ---------------------------------------------------------------------------
# Module-level helpers
# ---------------------------------------------------------------------------


def _expand_participants(members: list, ability: str) -> list:
    """Expand encounter members to individual SaveParticipant list.

    Buff dice for buffs with affects_saves=True are injected as per-participant
    BonusDiceEntry objects so each monster's buffs apply to its own rolls only.
    """
    participants = []
    for monster, count in members:
        # Collect save buff dice for this monster type
        save_buff_dice = [
            BonusDiceEntry(formula=buff.bonus_value, label=buff.name)
            for buff in getattr(monster, "buffs", [])
            if getattr(buff, "affects_saves", False)
        ]
        for i in range(1, count + 1):
            name = f"{monster.name} {i}" if count > 1 else monster.name
            bonus = _resolve_save_bonus(monster, ability.upper())
            participants.append(
                SaveParticipant(
                    name=name,
                    save_bonus=bonus,
                    bonus_dice=list(save_buff_dice),  # copy per participant
                )
            )
    return participants


# ---------------------------------------------------------------------------
# _SaveResultRow — per-participant result widget with inline LR interaction
# ---------------------------------------------------------------------------


class _SaveResultRow(QFrame):
    """Single participant result row with inline LR 'Use?' button."""

    lr_used = Signal(str)       # monster_name — to update LR counter in SavesTab

    def __init__(self, result, adv_label: str, is_first: bool = False, parent=None) -> None:
        super().__init__(parent)
        self._result = result
        self._passed = result.passed
        layout = QHBoxLayout(self)
        layout.setContentsMargins(4, 2, 4, 2)
        layout.setSpacing(6)

        # Name + roll info
        self._text_label = QLabel(self._format_line(result, adv_label, is_first=is_first))
        self._text_label.setWordWrap(True)
        self._text_label.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
        layout.addWidget(self._text_label, 1)

        # Features column (always present; empty if no features)
        features_text = ", ".join(result.detected_features) if result.detected_features else ""
        self._feature_label = QLabel(features_text)
        self._feature_label.setMinimumWidth(80)
        layout.addWidget(self._feature_label)

        # LR "Use?" button — only shown when creature has LR and FAILED
        self._lr_btn = None
        self._lr_spin = None
        if result.lr_max > 0:
            # LR counter spinbox for manual adjustment
            self._lr_spin = QSpinBox()
            self._lr_spin.setRange(0, result.lr_max)
            self._lr_spin.setValue(result.lr_uses)
            self._lr_spin.setFixedWidth(50)
            self._lr_spin.setToolTip(f"Legendary Resistance uses remaining (max {result.lr_max})")
            layout.addWidget(self._lr_spin)

            if not result.passed and result.lr_uses > 0:
                self._lr_btn = QPushButton("Use LR?")
                self._lr_btn.setFixedHeight(22)
                self._lr_btn.setToolTip("Spend one Legendary Resistance to pass this save")
                self._lr_btn.clicked.connect(self._on_use_lr)
                layout.addWidget(self._lr_btn)

        self._apply_row_color()

    def _format_line(self, result, adv_label: str, is_first: bool = False) -> str:
        faces = result.d20_faces
        if len(faces) == 2:
            kept_face = next(f for f in faces if f.kept)
            other_face = next(f for f in faces if not f.kept)
            d20_str = f"[{kept_face.value}, {other_face.value}]({adv_label})"
        else:
            d20_str = f"[{result.d20_natural}]"
        bonus_str = f"+{result.save_bonus}" if result.save_bonus >= 0 else str(result.save_bonus)
        flat_str = ""
        if result.flat_modifier != 0:
            flat_str = f" {'+' if result.flat_modifier > 0 else ''}{result.flat_modifier}"

        # Format bonus dice results with full label on first row, abbreviated on subsequent
        buff_str = ""
        for formula, signed_total, label in result.bonus_dice_results:
            dice_notation = formula.lstrip("+-")
            has_dice = "d" in dice_notation.lower()
            sign = "+" if signed_total >= 0 else ""
            if is_first and label:
                if has_dice:
                    buff_str += f" + {label} {dice_notation}({signed_total})"
                else:
                    buff_str += f" + {label}({sign}{signed_total})"
            else:
                if has_dice:
                    buff_str += f" + {dice_notation}({signed_total})"
                else:
                    buff_str += f" {sign}{signed_total}"

        status = "PASS" if result.passed else "FAIL"
        return f"{result.name}: {d20_str} {bonus_str}{flat_str}{buff_str} = {result.total} \u2014 {status}"

    def _apply_row_color(self) -> None:
        if not self._passed and self._result.lr_max > 0 and self._result.lr_uses > 0:
            # Red tint for LR creature that failed — DM needs to notice
            self.setStyleSheet("_SaveResultRow { background-color: rgba(220, 50, 50, 40); }")
        elif self._passed:
            self.setStyleSheet("")  # no tint on natural pass
        else:
            self.setStyleSheet("")  # normal fail, no LR

    def _on_use_lr(self) -> None:
        """Flip row from FAIL to PASS (LR), recolor green, hide button, decrement counter."""
        self._passed = True
        # Update text: replace FAIL with PASS (LR)
        text = self._text_label.text().replace("FAIL", "PASS (LR)")
        self._text_label.setText(text)
        # Green tint — satisfying visual feedback
        self.setStyleSheet("_SaveResultRow { background-color: rgba(50, 200, 50, 40); }")
        # Hide the Use LR button
        if self._lr_btn:
            self._lr_btn.hide()
        # Decrement spinbox
        if self._lr_spin and self._lr_spin.value() > 0:
            self._lr_spin.setValue(self._lr_spin.value() - 1)
        # Emit signal so SavesTab can track the LR counter
        monster_name = getattr(self._result, 'monster_name', '') or self._result.name
        self.lr_used.emit(monster_name)

    def get_lr_remaining(self) -> int:
        """Return current LR spinbox value (for counter tracking)."""
        if self._lr_spin:
            return self._lr_spin.value()
        return 0


# ---------------------------------------------------------------------------
# _DetectionRulesPanel — collapsible rules manager
# ---------------------------------------------------------------------------


class _DetectionRulesPanel(QGroupBox):
    """Collapsible panel for managing feature detection rules."""

    rules_changed = Signal()  # emitted when rules are added, edited, or deleted

    def __init__(self, persistence_service=None, parent=None) -> None:
        super().__init__("Detection Rules", parent)
        self._persistence = persistence_service
        self.setCheckable(True)
        self.setChecked(False)   # collapsed by default
        self._rules: list[FeatureRule] = []
        self._setup_ui()
        self._load_rules()

    def _setup_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(4, 4, 4, 4)
        layout.setSpacing(4)

        # Existing rules list
        self._rules_scroll = QScrollArea()
        self._rules_scroll.setWidgetResizable(True)
        self._rules_scroll.setMaximumHeight(200)
        self._rules_container = QWidget()
        self._rules_layout = QVBoxLayout(self._rules_container)
        self._rules_layout.setContentsMargins(0, 0, 0, 0)
        self._rules_layout.setSpacing(2)
        self._rules_layout.addStretch()
        self._rules_scroll.setWidget(self._rules_container)
        layout.addWidget(self._rules_scroll)

        # Add rule inline row: [trigger text] [behavior dropdown] [Add button]
        add_row = QHBoxLayout()
        self._trigger_edit = QLineEdit()
        self._trigger_edit.setPlaceholderText("Trigger text (e.g. Evasion)")
        add_row.addWidget(self._trigger_edit, 1)

        self._behavior_combo = QComboBox()
        self._behavior_combo.addItems([
            "auto-advantage", "auto-disadvantage",
            "auto-fail", "auto-pass", "reminder"
        ])
        add_row.addWidget(self._behavior_combo)

        self._add_btn = QPushButton("Add")
        self._add_btn.setFixedHeight(24)
        self._add_btn.clicked.connect(self._on_add_rule)
        add_row.addWidget(self._add_btn)

        layout.addLayout(add_row)

    def _load_rules(self) -> None:
        """Load built-in rules + custom rules from persistence."""
        self._rules = list(BUILTIN_RULES)  # shallow copy of built-ins
        if self._persistence:
            custom_dicts = self._persistence.load_save_rules()
            for d in custom_dicts:
                self._rules.append(FeatureRule.from_dict(d))
        self._rebuild_rule_rows()

    def _rebuild_rule_rows(self) -> None:
        """Clear and rebuild the rule row widgets."""
        # Remove all existing rows (keep the stretch at the end)
        while self._rules_layout.count() > 1:
            item = self._rules_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        for i, rule in enumerate(self._rules):
            row = QFrame()
            row_layout = QHBoxLayout(row)
            row_layout.setContentsMargins(2, 1, 2, 1)
            row_layout.setSpacing(4)

            # Enabled checkbox
            enabled_cb = QCheckBox()
            enabled_cb.setChecked(rule.enabled)
            enabled_cb.stateChanged.connect(lambda state, idx=i: self._on_toggle_enabled(idx, state))
            row_layout.addWidget(enabled_cb)

            # Trigger label
            trigger_label = QLabel(rule.trigger)
            trigger_label.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
            row_layout.addWidget(trigger_label, 1)

            # Behavior label
            behavior_label = QLabel(rule.behavior)
            behavior_label.setMinimumWidth(100)
            row_layout.addWidget(behavior_label)

            # Delete button (only for custom rules)
            if not rule.is_builtin:
                del_btn = QPushButton("Del")
                del_btn.setFixedSize(36, 22)
                del_btn.clicked.connect(lambda checked, idx=i: self._on_delete_rule(idx))
                row_layout.addWidget(del_btn)
            else:
                # Placeholder for alignment
                spacer = QWidget()
                spacer.setFixedWidth(36)
                row_layout.addWidget(spacer)

            self._rules_layout.insertWidget(self._rules_layout.count() - 1, row)

    def _on_add_rule(self) -> None:
        trigger = self._trigger_edit.text().strip()
        if not trigger:
            return
        behavior = self._behavior_combo.currentText()
        label = trigger[:20]  # truncate label for display
        rule = FeatureRule(trigger=trigger, label=label, behavior=behavior)
        self._rules.append(rule)
        self._trigger_edit.clear()
        self._save_custom_rules()
        self._rebuild_rule_rows()
        self.rules_changed.emit()

    def _on_toggle_enabled(self, idx: int, state: int) -> None:
        if 0 <= idx < len(self._rules):
            self._rules[idx].enabled = bool(state)
            self._save_custom_rules()
            self.rules_changed.emit()

    def _on_delete_rule(self, idx: int) -> None:
        if 0 <= idx < len(self._rules) and not self._rules[idx].is_builtin:
            self._rules.pop(idx)
            self._save_custom_rules()
            self._rebuild_rule_rows()
            self.rules_changed.emit()

    def _save_custom_rules(self) -> None:
        """Persist only custom (non-builtin) rules."""
        if self._persistence:
            custom = [r.to_dict() for r in self._rules if not r.is_builtin]
            self._persistence.save_save_rules(custom)

    def get_rules(self) -> list[FeatureRule]:
        """Return all rules (built-in + custom)."""
        return list(self._rules)


# ---------------------------------------------------------------------------
# SavesTab
# ---------------------------------------------------------------------------


class SavesTab(QWidget):
    """Save Roller tab.

    The encounter builder (left panel) has been moved to EncounterSidebarDock.
    This tab now contains only the Save Roller controls with feature detection.

    Construction
    ------------
    library           : MonsterLibrary — shared library for monster lookup
    roller            : Roller — shared roller for dice rolling
    persistence_service : PersistenceService — optional, for custom rule persistence
    """

    def __init__(self, library, roller, persistence_service=None, parent=None) -> None:
        super().__init__(parent)
        self._library = library
        self._roller = roller
        self._persistence = persistence_service
        self._participants: list[SaveParticipant] = []
        self._save_roll_service = SaveRollService()
        self._feature_service = FeatureDetectionService()
        self._lr_counters: dict[str, int] = {}    # monster_name -> remaining LR uses
        self._result_rows: list[_SaveResultRow] = []  # current roll result row widgets

        self._setup_ui()

    # ------------------------------------------------------------------
    # UI Construction
    # ------------------------------------------------------------------

    def _setup_ui(self) -> None:
        root_layout = QVBoxLayout(self)
        root_layout.setContentsMargins(6, 6, 6, 6)
        root_layout.setSpacing(6)

        # Save Type
        save_type_row = QHBoxLayout()
        save_type_row.addWidget(QLabel("Save Type"))
        self._save_type_bar = ToggleBar(
            ["STR", "DEX", "CON", "INT", "WIS", "CHA"], default="CON"
        )
        save_type_row.addWidget(self._save_type_bar)
        root_layout.addLayout(save_type_row)

        # DC
        dc_row = QHBoxLayout()
        dc_row.addWidget(QLabel("DC"))
        self._dc_spin = QSpinBox()
        self._dc_spin.setRange(1, 30)
        self._dc_spin.setValue(15)
        self._dc_spin.setFixedWidth(60)
        dc_row.addWidget(self._dc_spin)
        dc_row.addStretch()
        root_layout.addLayout(dc_row)

        # Advantage
        adv_row = QHBoxLayout()
        adv_row.addWidget(QLabel("Advantage"))
        self._adv_bar = ToggleBar(
            ["Normal", "Advantage", "Disadvantage"], default="Normal"
        )
        adv_row.addWidget(self._adv_bar)
        root_layout.addLayout(adv_row)

        # Feature detection toggles (SAVE-11)
        toggle_row = QHBoxLayout()
        self._magical_toggle = QCheckBox("Is save magical?")
        self._magical_toggle.setToolTip("When checked, Magic Resistance creatures auto-roll with advantage")
        toggle_row.addWidget(self._magical_toggle)

        self._mr_toggle = QCheckBox("MR detection")
        self._mr_toggle.setChecked(True)
        self._mr_toggle.setToolTip("Enable/disable Magic Resistance auto-detection")
        toggle_row.addWidget(self._mr_toggle)

        self._lr_toggle = QCheckBox("LR detection")
        self._lr_toggle.setChecked(True)
        self._lr_toggle.setToolTip("Enable/disable Legendary Resistance reminder detection")
        toggle_row.addWidget(self._lr_toggle)

        root_layout.addLayout(toggle_row)

        # Flat Modifier
        flat_row = QHBoxLayout()
        flat_row.addWidget(QLabel("Flat Modifier"))
        self._flat_mod_spin = QSpinBox()
        self._flat_mod_spin.setRange(-20, 20)
        self._flat_mod_spin.setValue(0)
        self._flat_mod_spin.setFixedWidth(60)
        flat_row.addWidget(self._flat_mod_spin)
        flat_row.addStretch()
        root_layout.addLayout(flat_row)

        # Bonus Dice
        root_layout.addWidget(QLabel("Bonus Dice"))
        self._bonus_dice_list = BonusDiceList()
        root_layout.addWidget(self._bonus_dice_list)

        # Detection Rules panel (SAVE-14)
        self._rules_panel = _DetectionRulesPanel(persistence_service=self._persistence)
        root_layout.addWidget(self._rules_panel)

        # Roll Saves button (disabled until participants loaded)
        self._roll_saves_btn = QPushButton("Roll Saves")
        self._roll_saves_btn.setEnabled(False)
        self._roll_saves_btn.clicked.connect(self._execute_roll)
        root_layout.addWidget(self._roll_saves_btn)

        # Per-row results area (replaces plain text for participant results)
        self._results_scroll = QScrollArea()
        self._results_scroll.setWidgetResizable(True)
        self._results_container = QWidget()
        self._results_layout = QVBoxLayout(self._results_container)
        self._results_layout.setContentsMargins(0, 0, 0, 0)
        self._results_layout.setSpacing(2)
        self._results_layout.addStretch()
        self._results_scroll.setWidget(self._results_container)
        root_layout.addWidget(self._results_scroll, 1)

        # Summary output panel (single-line summary after each roll)
        self._output_panel = RollOutputPanel()
        self._output_panel.setMaximumHeight(80)
        root_layout.addWidget(self._output_panel)

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def load_participants(self, participants: list) -> None:
        """Set participants and enable Roll Saves.

        Called by MainWindow when CT sends to saves or sidebar triggers load.
        """
        self._participants = participants
        # Ensure monster_name is set for LR tracking
        for p in self._participants:
            if not getattr(p, 'monster_name', None):
                base = p.name.rsplit(" ", 1)[0] if p.name and p.name.split()[-1].isdigit() else p.name
                p.monster_name = base
        self._roll_saves_btn.setEnabled(bool(participants))
        if participants:
            self._output_panel.append(f"Loaded {len(participants)} participants")

    def load_participants_from_sidebar(self, members: list, ability: str = None) -> None:
        """Build participants from sidebar checked members.

        Args:
            members: list of (Monster, count) tuples from sidebar get_checked_members()
            ability: optional save ability override; uses current toggle if None
        """
        ab = ability or self._save_type_bar.value()
        self._participants = _expand_participants(members, ab)
        # Set monster_name on each participant for LR counter keying
        for p in self._participants:
            # Strip numeric suffix to get base monster name
            base = p.name.rsplit(" ", 1)[0] if p.name and p.name.split()[-1].isdigit() else p.name
            p.monster_name = base
        self._roll_saves_btn.setEnabled(bool(self._participants))
        if self._participants:
            self._output_panel.append(f"Loaded {len(self._participants)} participants from sidebar")

    def reset_lr_counters(self) -> None:
        """Clear LR session counters. Called when encounter changes."""
        self._lr_counters.clear()

    # ------------------------------------------------------------------
    # Save Roller
    # ------------------------------------------------------------------

    def _execute_roll(self) -> None:
        """Build SaveRequest with per-creature feature detection and execute saves."""
        if not self._participants:
            return

        ability = self._save_type_bar.value()
        advantage_map = {
            "Normal": "normal",
            "Advantage": "advantage",
            "Disadvantage": "disadvantage",
        }
        advantage = advantage_map.get(self._adv_bar.value(), "normal")
        is_magical = self._magical_toggle.isChecked()

        # Get active detection rules, filtered by MR/LR toggle state
        rules = self._get_active_rules()

        # Apply feature detection per participant
        for p in self._participants:
            # Resolve the Monster object from library for detection
            monster = None
            lookup_name = p.monster_name or p.name
            # Strip numeric suffix for library lookup (e.g., "Goblin 1" -> "Goblin")
            base_name = lookup_name.rsplit(" ", 1)[0] if lookup_name and lookup_name.split()[-1].isdigit() else lookup_name
            if self._library.has_name(base_name):
                monster = self._library.get_by_name(base_name)
            elif self._library.has_name(lookup_name):
                monster = self._library.get_by_name(lookup_name)

            adv_override, labels, lr_uses, lr_max = self._feature_service.detect_for_participant(
                monster, rules, is_magical
            )

            # Initialize or apply LR counter from session state (persists across rolls)
            if lr_max > 0:
                if base_name not in self._lr_counters:
                    # First time seeing this monster — seed the counter at max
                    self._lr_counters[base_name] = lr_uses
                # Always use the persisted counter value
                lr_uses = self._lr_counters[base_name]

            p.advantage = adv_override if adv_override else p.advantage
            p.detected_features = labels
            p.lr_uses = lr_uses
            p.lr_max = lr_max
            if p.monster_name is None:
                p.monster_name = base_name

            # Inject save buff dice from monster — only if not already set
            # (sidebar path sets them in _expand_participants; CT path needs them here)
            if not getattr(p, "bonus_dice", None) and monster is not None:
                p.bonus_dice = [
                    BonusDiceEntry(formula=buff.bonus_value, label=buff.name)
                    for buff in getattr(monster, "buffs", [])
                    if getattr(buff, "affects_saves", False)
                ]

        request = SaveRequest(
            participants=self._participants,
            ability=ability,
            dc=self._dc_spin.value(),
            advantage=advantage,
            flat_modifier=self._flat_mod_spin.value(),
            bonus_dice=self._bonus_dice_list.get_entries(),
            seed=None,
        )

        result = self._save_roll_service.execute_save_roll(request, self._roller)

        # Clear previous result rows
        self._clear_result_rows()

        # Build per-row widgets
        adv_text = self._adv_bar.value().lower()
        if adv_text == "normal":
            adv_text = ""
        for row_idx, pr in enumerate(result.participant_results):
            # Propagate monster_name from participant to result for LR tracking
            pr_monster_name = None
            for p in self._participants:
                if p.name == pr.name:
                    pr_monster_name = p.monster_name
                    break
            # Monkey-patch monster_name onto result for _SaveResultRow access
            pr.monster_name = pr_monster_name

            row = _SaveResultRow(pr, adv_text, is_first=(row_idx == 0))
            row.lr_used.connect(self._on_lr_used)
            self._results_layout.insertWidget(self._results_layout.count() - 1, row)
            self._result_rows.append(row)

        # Summary line
        self._output_panel.append(self._format_summary_line(result.summary))

    def _get_active_rules(self) -> list:
        """Return detection rules filtered by MR/LR toggle state."""
        rules = self._rules_panel.get_rules()
        active = []
        for r in rules:
            if r.trigger.lower() == "magic resistance" and not self._mr_toggle.isChecked():
                continue
            if r.trigger.lower() == "legendary resistance" and not self._lr_toggle.isChecked():
                continue
            active.append(r)
        return active

    def _on_lr_used(self, monster_name: str) -> None:
        """Decrement LR counter for a monster type when DM uses LR."""
        current = self._lr_counters.get(monster_name, 0)
        if current > 0:
            self._lr_counters[monster_name] = current - 1

    def _clear_result_rows(self) -> None:
        """Remove all _SaveResultRow widgets from the results area."""
        for row in self._result_rows:
            row.deleteLater()
        self._result_rows.clear()
        # Clear layout items (keep the stretch)
        while self._results_layout.count() > 1:
            item = self._results_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

    def _format_participant_line(self, result) -> str:
        faces = result.d20_faces
        if len(faces) == 2:
            kept_face = next(f for f in faces if f.kept)
            other_face = next(f for f in faces if not f.kept)
            adv_label = "adv" if self._adv_bar.value() == "Advantage" else "disadv"
            d20_str = f"[{kept_face.value}, {other_face.value}]({adv_label})"
        else:
            d20_str = f"[{result.d20_natural}]"
        bonus_str = f"+{result.save_bonus}" if result.save_bonus >= 0 else str(result.save_bonus)
        flat_str = ""
        if result.flat_modifier != 0:
            flat_str = f" {'+' if result.flat_modifier > 0 else ''}{result.flat_modifier}"
        status = "PASS" if result.passed else "FAIL"
        return f"{result.name}: {d20_str} {bonus_str}{flat_str} = {result.total} \u2014 {status}"

    def _format_summary_line(self, summary) -> str:
        failed_str = ", ".join(summary.failed_names) if summary.failed_names else "none"
        return (
            f"\u2500\u2500\u2500 Passed: {summary.passed}  |  "
            f"Failed ({summary.failed}): {failed_str} \u2500\u2500\u2500"
        )

    # ------------------------------------------------------------------
    # Settings integration
    # ------------------------------------------------------------------

    def apply_defaults(self, settings) -> None:
        """Apply saved default settings to UI controls. Called by MainWindow."""
        self._dc_spin.setValue(settings.default_save_dc)
