"""SavesTab — Save Roller tab (encounter builder removed; sidebar handles it)."""
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
)
from PySide6.QtCore import Signal

from src.encounter.models import SaveParticipant, SaveRequest
from src.encounter.service import SaveRollService, _resolve_save_bonus
from src.ui.toggle_bar import ToggleBar
from src.ui.bonus_dice_list import BonusDiceList
from src.ui.roll_output import RollOutputPanel


# ---------------------------------------------------------------------------
# Module-level helpers
# ---------------------------------------------------------------------------


def _expand_participants(members: list, ability: str) -> list:
    """Expand encounter members to individual SaveParticipant list."""
    participants = []
    for monster, count in members:
        for i in range(1, count + 1):
            name = f"{monster.name} {i}" if count > 1 else monster.name
            bonus = _resolve_save_bonus(monster, ability.upper())
            participants.append(SaveParticipant(name=name, save_bonus=bonus))
    return participants


# ---------------------------------------------------------------------------
# SavesTab
# ---------------------------------------------------------------------------


class SavesTab(QWidget):
    """Save Roller tab.

    The encounter builder (left panel) has been moved to EncounterSidebarDock.
    This tab now contains only the Save Roller controls.

    Construction
    ------------
    library : MonsterLibrary — shared library (kept for forward-compat API)
    roller  : Roller — shared roller for dice rolling
    """

    def __init__(self, library, roller, parent=None) -> None:
        super().__init__(parent)
        self._library = library
        self._roller = roller
        self._participants: list[SaveParticipant] = []
        self._save_roll_service = SaveRollService()

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

        # Roll Saves button (disabled until participants loaded)
        self._roll_saves_btn = QPushButton("Roll Saves")
        self._roll_saves_btn.setEnabled(False)
        self._roll_saves_btn.clicked.connect(self._execute_roll)
        root_layout.addWidget(self._roll_saves_btn)

        # Output panel
        self._output_panel = RollOutputPanel()
        root_layout.addWidget(self._output_panel, 1)

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def load_participants(self, participants: list) -> None:
        """Set participants and enable Roll Saves.

        Called by MainWindow when sidebar triggers "Load into Save Roller".

        Args:
            participants: list of SaveParticipant objects
        """
        self._participants = participants
        self._roll_saves_btn.setEnabled(bool(participants))
        if participants:
            self._output_panel.append(f"Loaded {len(participants)} participants")

    # ------------------------------------------------------------------
    # Save Roller
    # ------------------------------------------------------------------

    def _execute_roll(self) -> None:
        """Build SaveRequest from current UI state and execute saves."""
        if not self._participants:
            return

        ability = self._save_type_bar.value()
        advantage_map = {
            "Normal": "normal",
            "Advantage": "advantage",
            "Disadvantage": "disadvantage",
        }
        advantage = advantage_map.get(self._adv_bar.value(), "normal")

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

        for pr in result.participant_results:
            self._output_panel.append(self._format_participant_line(pr))
        self._output_panel.append(self._format_summary_line(result.summary))

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
