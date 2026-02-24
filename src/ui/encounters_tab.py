"""EncountersTab — combined Encounter builder and Save Roller tab."""
from __future__ import annotations

from pathlib import Path

from PySide6.QtWidgets import (
    QWidget,
    QHBoxLayout,
    QVBoxLayout,
    QSplitter,
    QLabel,
    QSpinBox,
    QPushButton,
    QLineEdit,
    QScrollArea,
    QSizePolicy,
    QFileDialog,
    QTextEdit,
)
from PySide6.QtCore import Qt, Signal

from src.domain.models import Encounter, Monster
from src.encounter.models import SaveParticipant, SaveRequest
from src.encounter.service import EncounterService, SaveRollService, _resolve_save_bonus
from src.ui.toggle_bar import ToggleBar
from src.ui.bonus_dice_list import BonusDiceList
from src.ui.roll_output import RollOutputPanel


# ---------------------------------------------------------------------------
# Module-level helpers
# ---------------------------------------------------------------------------


def _expand_participants(encounter: Encounter, ability: str) -> list:
    """Expand encounter members to individual SaveParticipant list."""
    participants = []
    for monster, count in encounter.members:
        for i in range(1, count + 1):
            name = f"{monster.name} {i}" if count > 1 else monster.name
            bonus = _resolve_save_bonus(monster, ability.upper())
            participants.append(SaveParticipant(name=name, save_bonus=bonus))
    return participants


# ---------------------------------------------------------------------------
# EncounterMemberList widget
# ---------------------------------------------------------------------------


class EncounterMemberList(QWidget):
    """Dynamic list of (Monster, count) rows for the encounter builder.

    Mirrors BonusDiceList pattern: rows added to a scroll area, each row
    has a name label, count spinbox, and remove button.
    """

    members_changed = Signal(list)

    def __init__(self, library, parent=None):
        super().__init__(parent)
        self._library = library
        self._rows: list[tuple] = []  # (monster, QSpinBox, QWidget)
        self.setAcceptDrops(True)

        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QScrollArea.Shape.NoFrame)

        container = QWidget()
        self._layout = QVBoxLayout(container)
        self._layout.setSpacing(2)
        self._layout.addStretch()  # keeps rows pushed to the top
        scroll.setWidget(container)
        outer.addWidget(scroll)

    def add_monster(self, monster: Monster, count: int = 1) -> None:
        """Add monster or increment count if already present."""
        for (m, spin, _) in self._rows:
            if m.name == monster.name:
                spin.setValue(spin.value() + count)
                self.members_changed.emit(self.get_members())
                return
        # New row — insert before the stretch at position (len - 1)
        row_widget = QWidget()
        row_layout = QHBoxLayout(row_widget)
        row_layout.setContentsMargins(4, 2, 4, 2)

        name_label = QLabel(monster.name)
        name_label.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)

        count_spin = QSpinBox()
        count_spin.setRange(1, 99)
        count_spin.setValue(count)
        count_spin.setFixedWidth(56)
        count_spin.valueChanged.connect(lambda _: self.members_changed.emit(self.get_members()))

        remove_btn = QPushButton("\u2212")  # minus sign
        remove_btn.setFixedWidth(28)

        row_layout.addWidget(name_label)
        row_layout.addWidget(count_spin)
        row_layout.addWidget(remove_btn)

        entry = (monster, count_spin, row_widget)
        self._rows.append(entry)
        # Insert before stretch (last item in layout)
        insert_pos = self._layout.count() - 1
        self._layout.insertWidget(insert_pos, row_widget)

        remove_btn.clicked.connect(lambda checked=False, e=entry: self._remove_row(e))
        self.members_changed.emit(self.get_members())

    def get_members(self) -> list[tuple]:
        """Return list of (Monster, count) for current encounter state."""
        return [(m, spin.value()) for (m, spin, _) in self._rows]

    def _remove_row(self, entry: tuple) -> None:
        if entry in self._rows:
            self._rows.remove(entry)
            entry[2].deleteLater()
            self.members_changed.emit(self.get_members())

    def clear_all(self) -> None:
        """Remove all rows."""
        for (_, _, row_widget) in self._rows:
            row_widget.deleteLater()
        self._rows = []
        self.members_changed.emit(self.get_members())

    # --- Drag-and-drop target ---

    def dragEnterEvent(self, event) -> None:
        if event.mimeData().hasFormat("application/x-monster-name"):
            event.acceptProposedAction()
        else:
            event.ignore()

    def dragMoveEvent(self, event) -> None:
        if event.mimeData().hasFormat("application/x-monster-name"):
            event.acceptProposedAction()

    def dropEvent(self, event) -> None:
        raw_bytes = event.mimeData().data("application/x-monster-name")
        name = bytes(raw_bytes).decode("utf-8")  # explicit UTF-8 decode
        if self._library is not None and self._library.has_name(name):
            monster = self._library.get_by_name(name)
            self.add_monster(monster)
        event.acceptProposedAction()


# ---------------------------------------------------------------------------
# EncountersTab
# ---------------------------------------------------------------------------


class EncountersTab(QWidget):
    """Combined Encounter Builder + Save Roller tab.

    Construction
    ------------
    library          : MonsterLibrary — shared library for drag-drop resolution
    roller           : Roller — shared roller for dice rolling
    workspace_manager: WorkspaceManager or None — provides encounters/ folder path
    """

    encounter_members_changed = Signal(list)

    def __init__(self, library, roller, workspace_manager=None, parent=None) -> None:
        super().__init__(parent)
        self._library = library
        self._roller = roller
        self._workspace_manager = workspace_manager
        self._participants: list[SaveParticipant] = []
        self._encounter_service = EncounterService()
        self._save_roll_service = SaveRollService()

        self._setup_ui()

    # ------------------------------------------------------------------
    # UI Construction
    # ------------------------------------------------------------------

    def _setup_ui(self) -> None:
        root_layout = QVBoxLayout(self)
        root_layout.setContentsMargins(6, 6, 6, 6)

        splitter = QSplitter(Qt.Orientation.Horizontal)

        splitter.addWidget(self._build_left_panel())
        splitter.addWidget(self._build_right_panel())
        splitter.setStretchFactor(0, 1)
        splitter.setStretchFactor(1, 1)

        root_layout.addWidget(splitter)

    def _build_left_panel(self) -> QWidget:
        """Build encounter builder panel (left side)."""
        panel = QWidget()
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(4, 4, 4, 4)
        layout.setSpacing(6)

        # Section header
        header = QLabel("Encounter")
        header.setStyleSheet("font-weight: bold;")
        layout.addWidget(header)

        # Encounter name field
        self._name_edit = QLineEdit()
        self._name_edit.setPlaceholderText("New Encounter")
        layout.addWidget(self._name_edit)

        # Member list (drag target)
        self._member_list = EncounterMemberList(library=self._library)
        self._member_list.members_changed.connect(self.encounter_members_changed)
        layout.addWidget(self._member_list, 1)

        # Hint label
        hint = QLabel("Drag monsters from the Library tab")
        hint.setStyleSheet("color: gray; font-size: 10px;")
        layout.addWidget(hint)

        # Button row: New / Save / Load
        btn_row = QHBoxLayout()
        new_btn = QPushButton("New")
        save_btn = QPushButton("Save...")
        load_btn = QPushButton("Load...")
        new_btn.clicked.connect(self._on_new)
        save_btn.clicked.connect(self._on_save)
        load_btn.clicked.connect(self._on_load)
        btn_row.addWidget(new_btn)
        btn_row.addWidget(save_btn)
        btn_row.addWidget(load_btn)
        layout.addLayout(btn_row)

        # Load into Save Roller button
        self._load_roller_btn = QPushButton("Load into Save Roller")
        self._load_roller_btn.clicked.connect(self._load_encounter_into_save_roller)
        layout.addWidget(self._load_roller_btn)

        # Unresolved entries panel (hidden by default)
        self._unresolved_label = QLabel("Unresolved Entries")
        self._unresolved_label.setStyleSheet("font-weight: bold; color: orange;")
        self._unresolved_text = QTextEdit()
        self._unresolved_text.setReadOnly(True)
        self._unresolved_text.setMaximumHeight(100)
        self._unresolved_label.setVisible(False)
        self._unresolved_text.setVisible(False)
        layout.addWidget(self._unresolved_label)
        layout.addWidget(self._unresolved_text)

        return panel

    def _build_right_panel(self) -> QWidget:
        """Build Save Roller panel (right side)."""
        panel = QWidget()
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(4, 4, 4, 4)
        layout.setSpacing(6)

        # Save Type
        save_type_row = QHBoxLayout()
        save_type_row.addWidget(QLabel("Save Type"))
        self._save_type_bar = ToggleBar(
            ["STR", "DEX", "CON", "INT", "WIS", "CHA"], default="CON"
        )
        save_type_row.addWidget(self._save_type_bar)
        layout.addLayout(save_type_row)

        # DC
        dc_row = QHBoxLayout()
        dc_row.addWidget(QLabel("DC"))
        self._dc_spin = QSpinBox()
        self._dc_spin.setRange(1, 30)
        self._dc_spin.setValue(15)
        self._dc_spin.setFixedWidth(60)
        dc_row.addWidget(self._dc_spin)
        dc_row.addStretch()
        layout.addLayout(dc_row)

        # Advantage
        adv_row = QHBoxLayout()
        adv_row.addWidget(QLabel("Advantage"))
        self._adv_bar = ToggleBar(
            ["Normal", "Advantage", "Disadvantage"], default="Normal"
        )
        adv_row.addWidget(self._adv_bar)
        layout.addLayout(adv_row)

        # Flat Modifier
        flat_row = QHBoxLayout()
        flat_row.addWidget(QLabel("Flat Modifier"))
        self._flat_mod_spin = QSpinBox()
        self._flat_mod_spin.setRange(-20, 20)
        self._flat_mod_spin.setValue(0)
        self._flat_mod_spin.setFixedWidth(60)
        flat_row.addWidget(self._flat_mod_spin)
        flat_row.addStretch()
        layout.addLayout(flat_row)

        # Bonus Dice
        layout.addWidget(QLabel("Bonus Dice"))
        self._bonus_dice_list = BonusDiceList()
        layout.addWidget(self._bonus_dice_list)

        # Roll Saves button (disabled until participants loaded)
        self._roll_saves_btn = QPushButton("Roll Saves")
        self._roll_saves_btn.setEnabled(False)
        self._roll_saves_btn.clicked.connect(self._execute_roll)
        layout.addWidget(self._roll_saves_btn)

        # Output panel
        self._output_panel = RollOutputPanel()
        layout.addWidget(self._output_panel, 1)

        return panel

    # ------------------------------------------------------------------
    # Public API for cross-tab monster addition
    # ------------------------------------------------------------------

    def add_monster_to_encounter(self, monster) -> None:
        """Add *monster* to the encounter builder (called by Library tab drop zone)."""
        self._member_list.add_monster(monster)

    # ------------------------------------------------------------------
    # Left panel button handlers
    # ------------------------------------------------------------------

    def _on_new(self) -> None:
        """Clear encounter builder for a fresh encounter."""
        self._name_edit.setText("")
        self._name_edit.setPlaceholderText("New Encounter")
        self._member_list.clear_all()
        self._unresolved_label.setVisible(False)
        self._unresolved_text.setVisible(False)
        self._output_panel.clear()

    def _on_save(self) -> None:
        """Save current encounter to a Markdown file."""
        name = self._name_edit.text().strip()
        if not name:
            self._name_edit.setStyleSheet("border: 1px solid red;")
            return
        self._name_edit.setStyleSheet("")

        members = self._member_list.get_members()
        encounter = Encounter(name=name, members=members)

        start_dir = self._get_encounters_folder()
        path_str, _ = QFileDialog.getSaveFileName(
            self,
            "Save Encounter",
            str(start_dir / f"{name}.md"),
            "Markdown Files (*.md)",
        )
        if not path_str:
            return

        self._encounter_service.save_encounter(encounter, Path(path_str))

    def _on_load(self) -> None:
        """Load encounter from a Markdown file."""
        start_dir = self._get_encounters_folder()
        path_str, _ = QFileDialog.getOpenFileName(
            self,
            "Load Encounter",
            str(start_dir),
            "Markdown Files (*.md)",
        )
        if not path_str:
            return

        encounter, unresolved = self._encounter_service.load_encounter(
            Path(path_str), self._library
        )

        self._member_list.clear_all()
        for monster, count in encounter.members:
            self._member_list.add_monster(monster, count)

        self._name_edit.setText(encounter.name)

        if unresolved:
            lines = "\n".join(f"- {u.count}x {u.name}" for u in unresolved)
            self._unresolved_text.setPlainText(lines)
            self._unresolved_label.setVisible(True)
            self._unresolved_text.setVisible(True)
        else:
            self._unresolved_label.setVisible(False)
            self._unresolved_text.setVisible(False)

    def _load_encounter_into_save_roller(self) -> None:
        """Expand current encounter members into SaveParticipants and enable Roll Saves."""
        ability = self._save_type_bar.value()
        members = self._member_list.get_members()
        encounter = Encounter(
            name=self._name_edit.text().strip() or "Untitled",
            members=members,
        )
        self._participants = _expand_participants(encounter, ability)
        self._roll_saves_btn.setEnabled(True)
        self._output_panel.append(f"Loaded {len(self._participants)} participants")

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
    # Helpers
    # ------------------------------------------------------------------

    def _get_encounters_folder(self) -> Path:
        """Return path to encounters/ folder, falling back to home if not configured."""
        if self._workspace_manager is not None:
            try:
                return self._workspace_manager.get_subfolder("encounters")
            except (ValueError, AttributeError):
                pass
        return Path.home()

    # ------------------------------------------------------------------
    # Settings integration
    # ------------------------------------------------------------------

    def apply_defaults(self, settings) -> None:
        """Apply saved default settings to UI controls. Called by MainWindow."""
        self._dc_spin.setValue(settings.default_save_dc)
