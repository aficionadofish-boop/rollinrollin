"""MonsterEditorDialog — near-fullscreen modal editor for Monster objects.

Provides:
  - CollapsibleSection: reusable collapsible QWidget for grouping editor fields
  - MonsterEditorDialog: two-column modal dialog (edit fields left, live preview right)

Layout:
  - Toolbar: editable name, Save dropdown (stub), Discard, Undo
  - Left (scroll area): collapsible sections for Ability Scores, Saving Throws,
    Skills, Hit Points, Challenge Rating, Equipment, Actions, Buffs
  - Right: MonsterDetailPanel preview, updated live on every change

The editor never mutates the original Monster object.  All changes are applied
to a deep copy (_working_copy) and reflected immediately in the right-hand
preview via MonsterMathEngine.recalculate().

Equipment tracking:
  The editor maintains its own equipment state separate from Monster (which has
  no equipment field).  Equipping items updates Monster.ac and Monster.actions
  as side effects.  Plan 05 will persist these via MonsterModification.

Unsaved-changes guard: closing/escaping with a dirty working copy prompts the
user to confirm discard (Save option is a stub; wired in Plan 05).

Undo stack: every user action pushes a deep copy of _working_copy onto
_undo_stack.  Undo pops the most recent snapshot, repopulates all form
widgets, and refreshes the preview.
"""
from __future__ import annotations

import copy
import dataclasses
from typing import Optional

from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QFont
from PySide6.QtWidgets import (
    QComboBox,
    QDialog,
    QGridLayout,
    QHBoxLayout,
    QInputDialog,
    QLabel,
    QLineEdit,
    QListWidget,
    QListWidgetItem,
    QMenu,
    QMessageBox,
    QPushButton,
    QScrollArea,
    QSizePolicy,
    QSpinBox,
    QSplitter,
    QVBoxLayout,
    QWidget,
)

from src.domain.models import (
    Action,
    BuffItem,
    DamagePart,
    EquipmentItem,
    Monster,
    MonsterModification,
    SKILL_TO_ABILITY,
)
from src.equipment.data import SRD_ARMORS, SRD_WEAPONS
from src.equipment.service import EquipmentService
from src.monster_math.engine import MonsterMathEngine
from src.monster_math.validator import MathValidator, SaveState
from src.ui.monster_detail import MonsterDetailPanel


# ---------------------------------------------------------------------------
# CR values in display order
# ---------------------------------------------------------------------------

_CR_VALUES: list[str] = [
    "0", "1/8", "1/4", "1/2",
    "1", "2", "3", "4", "5", "6", "7", "8", "9", "10",
    "11", "12", "13", "14", "15", "16", "17", "18", "19", "20",
    "21", "22", "23", "24", "25", "26", "27", "28", "29", "30",
]

# Ability labels in D&D 5e order
_ABILITY_LABELS: list[str] = ["STR", "DEX", "CON", "INT", "WIS", "CHA"]

# Toggle state labels for save/skill rows
_TOGGLE_LABELS: list[str] = ["Non-Prof", "Prof", "Expertise", "Custom"]

# Magic bonus options for equipment pickers
_MAGIC_BONUS_OPTIONS: list[str] = ["+0 (nonmagical)", "+1", "+2", "+3"]
_FOCUS_BONUS_OPTIONS: list[str] = ["+1", "+2", "+3"]

# Three-tier color highlighting hex values (used in rich text spans)
COLOR_EQUIPMENT   = "#4EA8DE"   # steel blue — equipment-modified values
COLOR_MANUAL      = "#F4A261"   # amber — manually edited values
COLOR_CUSTOM_FLAG = "#E63946"   # red — custom override (doesn't match prof math)
COLOR_BASE        = ""          # empty — unmodified base values (no color wrapping)

# Buff target options
_BUFF_TARGETS: list[str] = [
    "Attack Rolls",
    "Saving Throws",
    "Ability Checks",
    "Damage",
    "All",
]


# ---------------------------------------------------------------------------
# CollapsibleSection
# ---------------------------------------------------------------------------


class CollapsibleSection(QWidget):
    """A QWidget that wraps a content widget under a collapsible toggle header.

    The header is a QPushButton that shows "+/- {title}".  Clicking it
    toggles visibility of the content widget.

    An optional summary string can be set via set_summary(); it is appended
    to the header text in grey when the section is collapsed, giving the DM
    a quick-glance overview without expanding.

    Parameters
    ----------
    title : str
        Section title displayed in the header button.
    content : QWidget
        The widget to show/hide when the header is toggled.
    expanded : bool
        Whether the section is initially expanded (default: False).
    parent : QWidget or None
        Optional parent widget.
    """

    def __init__(
        self,
        title: str,
        content: QWidget,
        expanded: bool = False,
        parent: Optional[QWidget] = None,
    ) -> None:
        super().__init__(parent)
        self._title = title
        self._content = content
        self._expanded = expanded
        self._summary: str = ""

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 2, 0, 2)
        layout.setSpacing(0)

        self._toggle_btn = QPushButton()
        self._toggle_btn.clicked.connect(self._toggle)
        layout.addWidget(self._toggle_btn)
        layout.addWidget(content)

        # Apply initial state
        content.setVisible(expanded)
        self._update_button_text()

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def set_summary(self, text: str) -> None:
        """Set a grey summary string shown in the header when collapsed."""
        self._summary = text
        if not self._expanded:
            self._update_button_text()

    # ------------------------------------------------------------------
    # Private
    # ------------------------------------------------------------------

    def _toggle(self) -> None:
        self._expanded = not self._expanded
        self._content.setVisible(self._expanded)
        self._update_button_text()

    def _update_button_text(self) -> None:
        prefix = "-" if self._expanded else "+"
        text = f"{prefix} {self._title}"
        if not self._expanded and self._summary:
            # Append summary — plain text; colour via HTML not supported on
            # QPushButton easily, so we use a parenthetical suffix.
            text += f"  ({self._summary})"
        self._toggle_btn.setText(text)


# ---------------------------------------------------------------------------
# MonsterEditorDialog
# ---------------------------------------------------------------------------


class MonsterEditorDialog(QDialog):
    """Near-fullscreen modal editor for a Monster.

    Opens from Library tab's Edit button.  Shows a two-column layout:
    left = scrollable edit sections, right = live MonsterDetailPanel preview.

    The original monster is never mutated; all edits go into _working_copy.
    MonsterMathEngine.recalculate() is called on every change to keep the
    preview panel in sync.

    Equipment state is tracked separately from Monster (which has no equipment
    field).  Equipping items updates _working_copy.ac and _working_copy.actions
    as side effects.  Plan 05 persists these via MonsterModification.

    Signals
    -------
    monster_saved : Signal(object)
        Emitted when the user saves (Plan 05 connects this).
    """

    monster_saved = Signal(object)  # Monster

    def __init__(
        self,
        monster: Monster,
        parent: Optional[QWidget] = None,
        library=None,
        persistence=None,
    ) -> None:
        super().__init__(parent)

        # Library and persistence (passed from LibraryTab, optional for backward compat)
        self._library = library
        self._persistence = persistence

        # Core state
        self._base_monster: Monster = monster
        self._working_copy: Monster = copy.deepcopy(monster)
        self._undo_stack: list[Monster] = []
        self._recalculating: bool = False
        self._dirty: bool = False

        # Math helpers
        self._engine = MonsterMathEngine()
        self._validator = MathValidator()
        self._equip_service = EquipmentService()

        # Equipment editor state (separate from Monster dataclass)
        # These track what is currently equipped so effects can be computed
        self._equipped_weapons: list[tuple[EquipmentItem, dict]] = []  # (item, action_dict)
        self._equipped_armor: Optional[tuple[EquipmentItem, dict]] = None  # (item, armor_result)
        self._equipped_shield: Optional[EquipmentItem] = None
        self._equipped_focus: Optional[EquipmentItem] = None  # focus_bonus stored here
        self._focus_bonus: int = 0  # focus_magic_bonus

        # Modification source tracking for three-tier highlighting
        # Maps field key -> "equipment" | "manual" | "custom"
        self._mod_sources: dict[str, str] = {}

        # Load existing buffs from monster (e.g. from a previous save/persistence)
        self._initial_buffs: list[BuffItem] = list(getattr(monster, "buffs", []))

        # Window properties
        self.setModal(True)
        self.setWindowTitle(f"Editing: {monster.name}")
        if parent is not None:
            parent_size = parent.size()
            self.resize(
                int(parent_size.width() * 0.92),
                int(parent_size.height() * 0.92),
            )
        else:
            self.resize(1000, 700)

        self._setup_ui()
        self._populate_form()
        self._rebuild_preview()

    # ------------------------------------------------------------------
    # UI construction
    # ------------------------------------------------------------------

    def _setup_ui(self) -> None:
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(8, 8, 8, 8)
        main_layout.setSpacing(4)

        # ---- Toolbar ----
        toolbar = self._build_toolbar()
        main_layout.addLayout(toolbar)

        # ---- Splitter: edit area (left) + preview (right) ----
        splitter = QSplitter(Qt.Orientation.Horizontal)

        # Left: scroll area with editing sections
        left_scroll = QScrollArea()
        left_scroll.setWidgetResizable(True)
        left_scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)

        left_content = QWidget()
        self._edit_layout = QVBoxLayout(left_content)
        self._edit_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        self._edit_layout.setSpacing(4)

        self._build_ability_scores_section()
        self._build_saving_throws_section()
        self._build_skills_section()
        self._build_hp_section()
        self._build_cr_section()
        self._build_equipment_section()
        self._build_actions_section()
        self._build_buffs_section()

        self._edit_layout.addStretch(1)
        left_scroll.setWidget(left_content)

        # Right: preview panel
        self._preview_panel = MonsterDetailPanel()

        splitter.addWidget(left_scroll)
        splitter.addWidget(self._preview_panel)
        splitter.setStretchFactor(0, 1)
        splitter.setStretchFactor(1, 1)

        main_layout.addWidget(splitter, 1)

    def _build_toolbar(self) -> QHBoxLayout:
        toolbar = QHBoxLayout()
        toolbar.setSpacing(6)

        # Editable monster name
        self._name_edit = QLineEdit(self._working_copy.name)
        name_font = QFont()
        name_font.setBold(True)
        name_font.setPointSize(14)
        self._name_edit.setFont(name_font)
        self._name_edit.editingFinished.connect(self._on_name_changed)
        toolbar.addWidget(self._name_edit, 1)

        toolbar.addStretch()

        # Save button with drop-down menu
        save_btn = QPushButton("Save")
        save_menu = QMenu(save_btn)
        save_menu.addAction("Save (override base)", self._save_override)
        save_menu.addAction("Save as Copy...", self._save_as_copy)
        save_btn.setMenu(save_menu)
        toolbar.addWidget(save_btn)

        # Discard button
        discard_btn = QPushButton("Discard")
        discard_btn.clicked.connect(self._discard)
        toolbar.addWidget(discard_btn)

        # Undo button
        undo_btn = QPushButton("Undo")
        undo_btn.clicked.connect(self._undo)
        toolbar.addWidget(undo_btn)

        return toolbar

    # ------------------------------------------------------------------
    # Section builders
    # ------------------------------------------------------------------

    def _build_ability_scores_section(self) -> None:
        """Build the 6-across ability score grid (expanded by default)."""
        content = QWidget()
        grid = QGridLayout(content)
        grid.setSpacing(6)

        self._ability_spinboxes: dict[str, QSpinBox] = {}

        for col, ability in enumerate(_ABILITY_LABELS):
            header = QLabel(ability)
            header.setAlignment(Qt.AlignmentFlag.AlignCenter)
            header_font = header.font()
            header_font.setBold(True)
            header.setFont(header_font)
            grid.addWidget(header, 0, col)

            spinbox = QSpinBox()
            spinbox.setRange(1, 30)
            spinbox.setValue(self._working_copy.ability_scores.get(ability, 10))
            spinbox.editingFinished.connect(self._on_ability_changed)
            spinbox.setProperty("ability", ability)
            grid.addWidget(spinbox, 1, col)
            self._ability_spinboxes[ability] = spinbox

        section = CollapsibleSection("Ability Scores", content, expanded=True)
        self._edit_layout.addWidget(section)

    def _build_saving_throws_section(self) -> None:
        """Build the saving throws section with toggle + custom override rows."""
        content = QWidget()
        layout = QVBoxLayout(content)
        layout.setSpacing(4)

        self._save_toggle_groups: dict[str, list[QPushButton]] = {}
        self._save_custom_spinboxes: dict[str, QSpinBox] = {}

        derived = self._engine.recalculate(self._working_copy)
        save_validations = {
            sv.ability: sv
            for sv in self._validator.validate_saves(self._working_copy, derived)
        }

        for ability in _ABILITY_LABELS:
            row = QHBoxLayout()

            label = QLabel(ability)
            label.setFixedWidth(36)
            row.addWidget(label)

            # Toggle group: Non-Prof / Prof / Expertise / Custom
            btn_group: list[QPushButton] = []
            for state_label in _TOGGLE_LABELS:
                btn = QPushButton(state_label)
                btn.setCheckable(True)
                btn.setFixedWidth(72)
                btn.clicked.connect(self._on_save_toggle_changed)
                btn.setProperty("ability", ability)
                btn.setProperty("state_label", state_label)
                btn_group.append(btn)
                row.addWidget(btn)
            self._save_toggle_groups[ability] = btn_group

            # Custom override spinbox (hidden unless Custom selected)
            custom_spin = QSpinBox()
            custom_spin.setRange(-20, 30)
            custom_spin.setFixedWidth(60)
            custom_spin.setEnabled(False)
            custom_spin.setVisible(False)
            custom_spin.editingFinished.connect(self._on_save_custom_changed)
            custom_spin.setProperty("ability", ability)
            row.addWidget(custom_spin)
            self._save_custom_spinboxes[ability] = custom_spin

            row.addStretch()
            layout.addLayout(row)

        # Set initial toggle states from working_copy
        self._sync_save_toggles()

        section = CollapsibleSection("Saving Throws", content, expanded=False)
        self._edit_layout.addWidget(section)

    def _build_skills_section(self) -> None:
        """Build the skills section showing existing skills + add/remove."""
        content = QWidget()
        self._skills_layout = QVBoxLayout(content)
        self._skills_layout.setSpacing(4)

        self._skill_rows: dict[str, tuple[list[QPushButton], QSpinBox, QWidget]] = {}

        # Build rows for current skills
        for skill_name, skill_value in list(self._working_copy.skills.items()):
            self._add_skill_row(skill_name, skill_value)

        # "Add Skill" row at the bottom
        add_row = QHBoxLayout()
        self._add_skill_combo = QComboBox()
        self._add_skill_combo.addItem("-- Add Skill --")
        for skill_name in sorted(SKILL_TO_ABILITY.keys()):
            self._add_skill_combo.addItem(skill_name)
        self._add_skill_combo.currentIndexChanged.connect(self._on_add_skill)
        add_row.addWidget(self._add_skill_combo)
        add_row.addStretch()

        add_row_widget = QWidget()
        add_row_widget.setLayout(add_row)
        self._skills_layout.addWidget(add_row_widget)

        section = CollapsibleSection("Skills", content, expanded=False)
        self._edit_layout.addWidget(section)

    def _add_skill_row(self, skill_name: str, skill_value: int) -> None:
        """Add a single skill row to the skills section."""
        row_widget = QWidget()
        row_layout = QHBoxLayout(row_widget)
        row_layout.setContentsMargins(0, 0, 0, 0)
        row_layout.setSpacing(4)

        label = QLabel(skill_name)
        label.setFixedWidth(110)
        row_layout.addWidget(label)

        btn_group: list[QPushButton] = []
        for state_label in _TOGGLE_LABELS:
            btn = QPushButton(state_label)
            btn.setCheckable(True)
            btn.setFixedWidth(72)
            btn.clicked.connect(self._on_skill_toggle_changed)
            btn.setProperty("skill_name", skill_name)
            btn.setProperty("state_label", state_label)
            btn_group.append(btn)
            row_layout.addWidget(btn)

        custom_spin = QSpinBox()
        custom_spin.setRange(-20, 30)
        custom_spin.setFixedWidth(60)
        custom_spin.setValue(skill_value)
        custom_spin.setEnabled(False)
        custom_spin.setVisible(False)
        custom_spin.editingFinished.connect(self._on_skill_custom_changed)
        custom_spin.setProperty("skill_name", skill_name)
        row_layout.addWidget(custom_spin)

        # Remove (X) button
        remove_btn = QPushButton("X")
        remove_btn.setFixedWidth(24)
        remove_btn.clicked.connect(lambda _checked, sn=skill_name: self._remove_skill(sn))
        row_layout.addWidget(remove_btn)

        row_layout.addStretch()

        # Insert before the "Add Skill" row (last widget)
        insert_index = self._skills_layout.count() - 1
        self._skills_layout.insertWidget(insert_index, row_widget)
        self._skill_rows[skill_name] = (btn_group, custom_spin, row_widget)

        # Sync toggle state for this skill
        self._sync_skill_toggle(skill_name, skill_value)

    def _build_hp_section(self) -> None:
        """Build the Hit Points section with formula + flat HP fields."""
        content = QWidget()
        layout = QVBoxLayout(content)
        layout.setSpacing(4)

        # Hit dice formula
        formula_row = QHBoxLayout()
        formula_row.addWidget(QLabel("Hit Dice Formula:"))
        self._hp_formula_edit = QLineEdit()
        self._hp_formula_edit.setPlaceholderText("e.g. 7d8+14")
        self._hp_formula_edit.editingFinished.connect(self._on_hp_changed)
        formula_row.addWidget(self._hp_formula_edit, 1)
        layout.addLayout(formula_row)

        # Flat max HP
        flat_row = QHBoxLayout()
        flat_row.addWidget(QLabel("Max HP (flat):"))
        self._hp_flat_spinbox = QSpinBox()
        self._hp_flat_spinbox.setRange(1, 9999)
        self._hp_flat_spinbox.setValue(max(1, self._working_copy.hp))
        self._hp_flat_spinbox.editingFinished.connect(self._on_hp_changed)
        flat_row.addWidget(self._hp_flat_spinbox)
        flat_row.addStretch()
        layout.addLayout(flat_row)

        section = CollapsibleSection("Hit Points", content, expanded=False)
        self._edit_layout.addWidget(section)

    def _build_cr_section(self) -> None:
        """Build the Challenge Rating section with CR combo box."""
        content = QWidget()
        layout = QHBoxLayout(content)
        layout.setContentsMargins(4, 4, 4, 4)

        layout.addWidget(QLabel("Challenge Rating:"))
        self._cr_combo = QComboBox()
        for cr in _CR_VALUES:
            self._cr_combo.addItem(cr)
        # Set current CR
        current_cr = self._working_copy.cr or "1"
        if current_cr in _CR_VALUES:
            self._cr_combo.setCurrentText(current_cr)
        self._cr_combo.currentTextChanged.connect(self._on_cr_changed)
        layout.addWidget(self._cr_combo)
        layout.addStretch()

        section = CollapsibleSection("Challenge Rating", content, expanded=False)
        self._edit_layout.addWidget(section)

    def _build_equipment_section(self) -> None:
        """Build the Equipment section with weapon/armor/shield/focus pickers."""
        content = QWidget()
        layout = QVBoxLayout(content)
        layout.setSpacing(8)

        # ---- Weapons sub-area ----
        layout.addWidget(self._make_section_header("Weapons"))

        self._weapon_list = QListWidget()
        self._weapon_list.setMaximumHeight(100)
        layout.addWidget(self._weapon_list)

        weapon_picker_row = QHBoxLayout()
        weapon_picker_row.addWidget(QLabel("Weapon:"))
        self._weapon_combo = QComboBox()
        for w in SRD_WEAPONS:
            self._weapon_combo.addItem(w.name)
        weapon_picker_row.addWidget(self._weapon_combo, 1)

        weapon_picker_row.addWidget(QLabel("Bonus:"))
        self._weapon_bonus_combo = QComboBox()
        for opt in _MAGIC_BONUS_OPTIONS:
            self._weapon_bonus_combo.addItem(opt)
        weapon_picker_row.addWidget(self._weapon_bonus_combo)

        add_weapon_btn = QPushButton("Add Weapon")
        add_weapon_btn.clicked.connect(self._on_add_weapon)
        weapon_picker_row.addWidget(add_weapon_btn)
        layout.addLayout(weapon_picker_row)

        remove_weapon_btn = QPushButton("Remove Selected Weapon")
        remove_weapon_btn.clicked.connect(self._on_remove_weapon)
        layout.addWidget(remove_weapon_btn)

        # ---- Armor sub-area ----
        layout.addWidget(self._make_section_header("Armor"))

        self._armor_display = QLabel("None")
        layout.addWidget(self._armor_display)

        self._armor_stealth_warn = QLabel("")
        self._armor_stealth_warn.setStyleSheet("color: orange;")
        self._armor_stealth_warn.setVisible(False)
        layout.addWidget(self._armor_stealth_warn)

        self._armor_str_warn = QLabel("")
        self._armor_str_warn.setStyleSheet("color: red;")
        self._armor_str_warn.setVisible(False)
        layout.addWidget(self._armor_str_warn)

        armor_picker_row = QHBoxLayout()
        armor_picker_row.addWidget(QLabel("Armor:"))
        self._armor_combo = QComboBox()
        for a in SRD_ARMORS:
            self._armor_combo.addItem(a.name)
        armor_picker_row.addWidget(self._armor_combo, 1)

        armor_picker_row.addWidget(QLabel("Bonus:"))
        self._armor_bonus_combo = QComboBox()
        for opt in _MAGIC_BONUS_OPTIONS:
            self._armor_bonus_combo.addItem(opt)
        armor_picker_row.addWidget(self._armor_bonus_combo)

        set_armor_btn = QPushButton("Set Armor")
        set_armor_btn.clicked.connect(self._on_set_armor)
        armor_picker_row.addWidget(set_armor_btn)
        layout.addLayout(armor_picker_row)

        remove_armor_btn = QPushButton("Remove Armor")
        remove_armor_btn.clicked.connect(self._on_remove_armor)
        layout.addWidget(remove_armor_btn)

        # ---- Shield sub-area ----
        layout.addWidget(self._make_section_header("Shield"))

        self._shield_display = QLabel("None")
        layout.addWidget(self._shield_display)

        shield_picker_row = QHBoxLayout()
        shield_picker_row.addWidget(QLabel("Bonus:"))
        self._shield_bonus_combo = QComboBox()
        for opt in _MAGIC_BONUS_OPTIONS:
            self._shield_bonus_combo.addItem(opt)
        shield_picker_row.addWidget(self._shield_bonus_combo)

        set_shield_btn = QPushButton("Set Shield")
        set_shield_btn.clicked.connect(self._on_set_shield)
        shield_picker_row.addWidget(set_shield_btn)

        remove_shield_btn = QPushButton("Remove Shield")
        remove_shield_btn.clicked.connect(self._on_remove_shield)
        shield_picker_row.addWidget(remove_shield_btn)
        shield_picker_row.addStretch()
        layout.addLayout(shield_picker_row)

        # ---- Spellcasting Focus sub-area ----
        layout.addWidget(self._make_section_header("Spellcasting Focus"))

        self._focus_display = QLabel("None")
        layout.addWidget(self._focus_display)

        focus_picker_row = QHBoxLayout()
        focus_picker_row.addWidget(QLabel("Bonus:"))
        self._focus_bonus_combo = QComboBox()
        for opt in _FOCUS_BONUS_OPTIONS:
            self._focus_bonus_combo.addItem(opt)
        focus_picker_row.addWidget(self._focus_bonus_combo)

        set_focus_btn = QPushButton("Set Focus")
        set_focus_btn.clicked.connect(self._on_set_focus)
        focus_picker_row.addWidget(set_focus_btn)

        remove_focus_btn = QPushButton("Remove Focus")
        remove_focus_btn.clicked.connect(self._on_remove_focus)
        focus_picker_row.addWidget(remove_focus_btn)
        focus_picker_row.addStretch()
        layout.addLayout(focus_picker_row)

        self._equipment_section = CollapsibleSection("Equipment", content, expanded=False)
        self._edit_layout.addWidget(self._equipment_section)

    def _build_actions_section(self) -> None:
        """Build the Actions section with structured editable rows."""
        content = QWidget()
        self._actions_edit_layout = QVBoxLayout(content)
        self._actions_edit_layout.setSpacing(4)

        # Action rows container (rebuilt on every change)
        self._action_rows_widget = QWidget()
        self._action_rows_layout = QVBoxLayout(self._action_rows_widget)
        self._action_rows_layout.setContentsMargins(0, 0, 0, 0)
        self._action_rows_layout.setSpacing(4)
        self._actions_edit_layout.addWidget(self._action_rows_widget)

        # "Add Action" button
        add_action_btn = QPushButton("Add Action")
        add_action_btn.clicked.connect(self._on_add_action)
        self._actions_edit_layout.addWidget(add_action_btn)

        section = CollapsibleSection("Actions", content, expanded=False)
        self._edit_layout.addWidget(section)

        # Build initial action rows
        self._rebuild_action_rows()

    def _build_buffs_section(self) -> None:
        """Build the Buffs section with name + value + target rows."""
        content = QWidget()
        self._buffs_edit_layout = QVBoxLayout(content)
        self._buffs_edit_layout.setSpacing(4)

        # Buff rows container (rebuilt on every change)
        self._buff_rows_widget = QWidget()
        self._buff_rows_layout = QVBoxLayout(self._buff_rows_widget)
        self._buff_rows_layout.setContentsMargins(0, 0, 0, 0)
        self._buff_rows_layout.setSpacing(4)
        self._buffs_edit_layout.addWidget(self._buff_rows_widget)

        # "Add Buff" button
        add_buff_btn = QPushButton("Add Buff")
        add_buff_btn.clicked.connect(self._on_add_buff)
        self._buffs_edit_layout.addWidget(add_buff_btn)

        # Editor-level buff list — load from monster if previously saved
        self._buff_items: list[BuffItem] = list(self._initial_buffs)
        if self._buff_items:
            self._dirty = False  # Don't mark as dirty just from loading

        section = CollapsibleSection("Buffs", content, expanded=False)
        self._edit_layout.addWidget(section)

    # ------------------------------------------------------------------
    # Equipment signal handlers
    # ------------------------------------------------------------------

    def _on_add_weapon(self) -> None:
        """Add the selected weapon (with magic bonus) to the equipped weapons."""
        weapon_name = self._weapon_combo.currentText()
        magic_bonus = self._weapon_bonus_combo.currentIndex()  # 0=+0, 1=+1, 2=+2, 3=+3

        # Find the weapon data
        weapon_data = next((w for w in SRD_WEAPONS if w.name == weapon_name), None)
        if weapon_data is None:
            return

        # Compute action from weapon
        action_dict = self._equip_service.compute_weapon_action(
            weapon_data, magic_bonus, self._working_copy
        )
        action_name = action_dict["name"]
        if magic_bonus > 0:
            action_name = f"{weapon_data.name} +{magic_bonus}"
            action_dict["name"] = action_name

        # Check for conflict with existing actions
        existing_action = next(
            (a for a in self._working_copy.actions if a.name == weapon_data.name or a.name == action_name),
            None,
        )

        replace_index = None  # Track position for in-place replacement
        extra_damage_parts = []  # Extra damage riders from the original action
        replace_raw_text = ""   # Preserve raw_text (extra effect descriptions)

        if existing_action is not None:
            reply = QMessageBox.question(
                self,
                "Action Conflict",
                f"An action named '{existing_action.name}' already exists.\n"
                "Replace the existing action, or add as a new separate action?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No | QMessageBox.StandardButton.Cancel,
                QMessageBox.StandardButton.Yes,
            )
            # Yes = Replace, No = Add as New, Cancel = abort
            if reply == QMessageBox.StandardButton.Cancel:
                return
            if reply == QMessageBox.StandardButton.Yes:
                # Replace: remember position, extra damage riders, and raw_text
                replace_index = next(
                    (i for i, a in enumerate(self._working_copy.actions) if a is existing_action),
                    None,
                )
                extra_damage_parts = list(existing_action.damage_parts[1:])
                replace_raw_text = existing_action.raw_text or ""
                self._working_copy.actions = [
                    a for a in self._working_copy.actions if a is not existing_action
                ]

        self._push_undo()

        # Insert at original position when replacing, otherwise append
        new_action = self._dict_to_action(action_dict)
        # Carry over extra damage riders and raw_text from replaced action
        if extra_damage_parts:
            new_action.damage_parts.extend(extra_damage_parts)
        if replace_raw_text:
            new_action.raw_text = replace_raw_text
        if replace_index is not None:
            self._working_copy.actions.insert(replace_index, new_action)
        else:
            self._working_copy.actions.append(new_action)

        # Track equipped weapon
        equip_item = EquipmentItem(item_type="weapon", item_name=action_name, magic_bonus=magic_bonus)
        self._equipped_weapons.append((equip_item, action_dict))
        self._mod_sources["actions"] = "equipment"

        self._update_weapon_list_widget()
        self._update_equipment_summary()
        self._rebuild_action_rows()
        self._rebuild_preview()

    def _on_remove_weapon(self) -> None:
        """Remove the selected weapon from the equipped weapons list."""
        selected = self._weapon_list.currentRow()
        if selected < 0 or selected >= len(self._equipped_weapons):
            return

        self._push_undo()
        equip_item, action_dict = self._equipped_weapons.pop(selected)
        action_name = action_dict["name"]

        # Remove auto-generated action with matching name
        self._working_copy.actions = [
            a for a in self._working_copy.actions
            if not (a.name == action_name and a.is_equipment_generated)
        ]

        self._update_weapon_list_widget()
        self._update_equipment_summary()
        self._rebuild_action_rows()
        self._rebuild_preview()

    def _on_set_armor(self) -> None:
        """Set/replace the equipped armor."""
        armor_name = self._armor_combo.currentText()
        magic_bonus = self._armor_bonus_combo.currentIndex()

        armor_data = next((a for a in SRD_ARMORS if a.name == armor_name), None)
        if armor_data is None:
            return

        self._push_undo()

        # Remove old armor AC contribution if any
        if self._equipped_armor is not None:
            old_item, old_result = self._equipped_armor
            # Restore base AC (remove armor contribution)
            self._working_copy.ac = self._base_monster.ac
            # Also account for any currently equipped shield
            if self._equipped_shield is not None:
                shield_bonus = self._equip_service.compute_shield_bonus(
                    self._equipped_shield.magic_bonus
                )
                self._working_copy.ac = self._base_monster.ac + shield_bonus

        armor_result = self._equip_service.compute_armor_ac(
            armor_data, magic_bonus, self._working_copy
        )

        # Apply armor AC (start from armor result, add shield if present)
        new_ac = armor_result["ac"]
        if self._equipped_shield is not None:
            new_ac += self._equip_service.compute_shield_bonus(
                self._equipped_shield.magic_bonus
            )
        self._working_copy.ac = new_ac

        # Track armor
        display_name = armor_name if magic_bonus == 0 else f"{armor_name} +{magic_bonus}"
        equip_item = EquipmentItem(item_type="armor", item_name=display_name, magic_bonus=magic_bonus)
        self._equipped_armor = (equip_item, armor_result)
        self._mod_sources["ac"] = "equipment"

        # Update armor display
        self._armor_display.setText(display_name)

        # Warnings + flag on working_copy for statblock display
        if armor_result["stealth_disadvantage"]:
            self._armor_stealth_warn.setText("Stealth Disadvantage")
            self._armor_stealth_warn.setVisible(True)
            self._working_copy._stealth_disadvantage = True
        else:
            self._armor_stealth_warn.setVisible(False)
            self._working_copy._stealth_disadvantage = False

        if not armor_result["str_requirement_met"]:
            self._armor_str_warn.setText(
                f"STR requirement not met (needs STR {armor_data.str_requirement})"
            )
            self._armor_str_warn.setVisible(True)
        else:
            self._armor_str_warn.setVisible(False)

        self._update_equipment_summary()
        self._rebuild_preview()

    def _on_remove_armor(self) -> None:
        """Remove the equipped armor and restore base AC."""
        if self._equipped_armor is None:
            return
        self._push_undo()

        # Restore base AC (+ shield if present)
        base_ac = self._base_monster.ac
        if self._equipped_shield is not None:
            base_ac += self._equip_service.compute_shield_bonus(
                self._equipped_shield.magic_bonus
            )
        self._working_copy.ac = base_ac

        self._equipped_armor = None
        self._armor_display.setText("None")
        self._armor_stealth_warn.setVisible(False)
        self._armor_str_warn.setVisible(False)
        self._working_copy._stealth_disadvantage = False

        if "ac" in self._mod_sources:
            del self._mod_sources["ac"]

        self._update_equipment_summary()
        self._rebuild_preview()

    def _on_set_shield(self) -> None:
        """Set/replace the equipped shield, adding +2+bonus to AC."""
        magic_bonus = self._shield_bonus_combo.currentIndex()

        self._push_undo()

        # Remove old shield bonus if any
        if self._equipped_shield is not None:
            old_bonus = self._equip_service.compute_shield_bonus(
                self._equipped_shield.magic_bonus
            )
            self._working_copy.ac -= old_bonus

        shield_bonus = self._equip_service.compute_shield_bonus(magic_bonus)
        self._working_copy.ac += shield_bonus
        self._mod_sources["ac"] = "equipment"

        display_name = "Shield" if magic_bonus == 0 else f"Shield +{magic_bonus}"
        self._equipped_shield = EquipmentItem(
            item_type="shield", item_name=display_name, magic_bonus=magic_bonus
        )
        self._shield_display.setText(display_name)

        self._update_equipment_summary()
        self._rebuild_preview()

    def _on_remove_shield(self) -> None:
        """Remove the equipped shield and subtract its AC bonus."""
        if self._equipped_shield is None:
            return
        self._push_undo()

        shield_bonus = self._equip_service.compute_shield_bonus(
            self._equipped_shield.magic_bonus
        )
        self._working_copy.ac -= shield_bonus
        self._equipped_shield = None
        self._shield_display.setText("None")

        # Remove ac mod source if no armor either
        if self._equipped_armor is None and "ac" in self._mod_sources:
            del self._mod_sources["ac"]

        self._update_equipment_summary()
        self._rebuild_preview()

    def _on_set_focus(self) -> None:
        """Set the spellcasting focus bonus (+1/+2/+3)."""
        # Focus bonus options are +1/+2/+3, so index 0 = +1
        focus_bonus = self._focus_bonus_combo.currentIndex() + 1

        self._push_undo()
        self._focus_bonus = focus_bonus
        display_name = f"Focus +{focus_bonus}"
        self._equipped_focus = EquipmentItem(
            item_type="focus", item_name=display_name, magic_bonus=focus_bonus
        )
        self._focus_display.setText(display_name)
        self._mod_sources["focus"] = "equipment"

        self._update_equipment_summary()
        self._rebuild_preview()

    def _on_remove_focus(self) -> None:
        """Remove the spellcasting focus."""
        if self._equipped_focus is None:
            return
        self._push_undo()
        self._focus_bonus = 0
        self._equipped_focus = None
        self._focus_display.setText("None")
        if "focus" in self._mod_sources:
            del self._mod_sources["focus"]

        self._update_equipment_summary()
        self._rebuild_preview()

    # ------------------------------------------------------------------
    # Actions section signal handlers
    # ------------------------------------------------------------------

    def _on_add_action(self) -> None:
        """Add a new empty action to working_copy."""
        self._push_undo()
        new_action = Action(
            name="New Action",
            to_hit_bonus=0,
            damage_parts=[DamagePart(dice_expr="1d6", damage_type="bludgeoning", raw_text="1d6 bludgeoning")],
            raw_text="New Action",
            is_parsed=True,
            damage_bonus=0,
            is_equipment_generated=False,
        )
        self._working_copy.actions.append(new_action)
        self._rebuild_action_rows()
        self._rebuild_preview()

    def _on_remove_action(self, action_index: int) -> None:
        """Remove an action by index from working_copy."""
        if 0 <= action_index < len(self._working_copy.actions):
            self._push_undo()
            removed = self._working_copy.actions.pop(action_index)
            # Also remove from equipped weapons tracking if equipment-generated
            if removed.is_equipment_generated:
                self._equipped_weapons = [
                    (item, ad) for item, ad in self._equipped_weapons
                    if ad["name"] != removed.name
                ]
                self._update_weapon_list_widget()
                self._update_equipment_summary()
            self._rebuild_action_rows()
            self._rebuild_preview()

    def _on_action_field_changed(self, action_index: int) -> None:
        """Read action row widgets and update working_copy action."""
        if self._recalculating:
            return
        if action_index < 0 or action_index >= len(self._working_copy.actions):
            return
        action = self._working_copy.actions[action_index]
        row_widgets = self._action_row_widgets.get(action_index)
        if row_widgets is None:
            return

        name_edit, to_hit_spin, dmg_dice_edit, dmg_bonus_spin, dmg_type_edit = row_widgets

        self._push_undo()
        action.name = name_edit.text().strip() or action.name
        action.to_hit_bonus = to_hit_spin.value()
        action.damage_bonus = dmg_bonus_spin.value()
        # Equipment-generated flag: lose it when user edits the action
        action.is_equipment_generated = False

        # Update damage parts
        new_dice = dmg_dice_edit.text().strip() or "1d6"
        new_type = dmg_type_edit.text().strip() or "bludgeoning"
        if action.damage_parts:
            action.damage_parts[0].dice_expr = new_dice
            action.damage_parts[0].damage_type = new_type
            action.damage_parts[0].raw_text = f"{new_dice} {new_type}"
        else:
            action.damage_parts = [
                DamagePart(dice_expr=new_dice, damage_type=new_type, raw_text=f"{new_dice} {new_type}")
            ]

        self._rebuild_preview()

    # ------------------------------------------------------------------
    # Buffs section signal handlers
    # ------------------------------------------------------------------

    def _on_add_buff(self) -> None:
        """Add a new empty buff to the buff list."""
        self._push_undo()
        new_buff = BuffItem(name="New Buff", bonus_value="+0", targets="all")
        self._buff_items.append(new_buff)
        self._rebuild_buff_rows()
        self._rebuild_preview()

    def _on_remove_buff(self, buff_index: int) -> None:
        """Remove a buff by index."""
        if 0 <= buff_index < len(self._buff_items):
            self._push_undo()
            self._buff_items.pop(buff_index)
            self._rebuild_buff_rows()
            self._rebuild_preview()

    def _on_buff_field_changed(self, buff_index: int) -> None:
        """Read buff row widgets and update the buff list."""
        if self._recalculating:
            return
        if buff_index < 0 or buff_index >= len(self._buff_items):
            return
        row_widgets = self._buff_row_widgets.get(buff_index)
        if row_widgets is None:
            return
        name_edit, bonus_edit, target_combo = row_widgets

        self._push_undo()
        self._buff_items[buff_index].name = name_edit.text().strip() or "Buff"
        self._buff_items[buff_index].bonus_value = bonus_edit.text().strip() or "+0"
        target_text = target_combo.currentText()
        self._buff_items[buff_index].targets = target_text.lower().replace(" ", "_")
        self._rebuild_preview()

    def _recompute_equipped_weapon_actions(self) -> None:
        """Recompute all equipment-generated actions with current ability scores.

        Called when ability scores change so weapon to-hit and damage cascade
        correctly (e.g. STR 24 -> 30 should update longsword to-hit).
        """
        if not self._equipped_weapons:
            return

        for i, (equip_item, old_action_dict) in enumerate(self._equipped_weapons):
            old_name = old_action_dict["name"]
            # Find the SRD weapon data
            base_weapon_name = equip_item.item_name.split(" +")[0]
            weapon_data = next(
                (w for w in SRD_WEAPONS if w.name == base_weapon_name), None
            )
            if weapon_data is None:
                continue

            # Recompute with current ability scores
            new_action_dict = self._equip_service.compute_weapon_action(
                weapon_data, equip_item.magic_bonus, self._working_copy
            )
            new_action_dict["name"] = old_name  # Preserve the display name

            # Update stored action dict
            self._equipped_weapons[i] = (equip_item, new_action_dict)

            # Update the corresponding Action on working_copy
            for j, action in enumerate(self._working_copy.actions):
                if action.name == old_name and action.is_equipment_generated:
                    self._working_copy.actions[j] = self._dict_to_action(new_action_dict)
                    break

        # Refresh action editor rows to show updated values
        self._rebuild_action_rows()

    def _cascade_all_actions_on_ability_change(
        self, old_scores: dict[str, int]
    ) -> None:
        """Cascade ability score changes to ALL actions.

        Equipment-generated: recomputed via EquipmentService (exact).
        Non-equipment (imported): to-hit inferred from old ability mod + prof,
        recomputed with new ability mod delta.  Damage bonus in dice_expr is
        also updated when it matches the inferred ability modifier.
        """
        import re as _re

        # Equipment-generated actions: full recompute
        self._recompute_equipped_weapon_actions()

        # Non-equipment actions: delta-based inference
        derived = self._engine.recalculate(self._working_copy)
        prof = derived.proficiency_bonus

        # Build delta map for abilities that actually changed.
        # CON is excluded — it never drives attack rolls in D&D 5e and
        # would falsely match STR-based actions when both have the same mod.
        ability_deltas: dict[str, tuple[int, int]] = {}  # ability -> (old_mod, delta)
        for ability in _ABILITY_LABELS:
            if ability == "CON":
                continue
            old_mod = (old_scores.get(ability, 10) - 10) // 2
            new_mod = (self._working_copy.ability_scores.get(ability, 10) - 10) // 2
            if old_mod != new_mod:
                ability_deltas[ability] = (old_mod, new_mod - old_mod)

        if not ability_deltas:
            return

        for action in self._working_copy.actions:
            if action.is_equipment_generated or action.to_hit_bonus is None:
                continue

            # Try to infer which ability this action uses:
            # to_hit = ability_mod + prof + [0..3 magic bonus]
            for ability, (old_mod, delta) in ability_deltas.items():
                remainder = action.to_hit_bonus - prof - old_mod
                if 0 <= remainder <= 3:
                    action.to_hit_bonus += delta

                    # Also try to update damage bonus embedded in dice_expr
                    if action.damage_parts:
                        dp = action.damage_parts[0]
                        match = _re.match(r'^(.+d\d+)([+-]\d+)$', dp.dice_expr)
                        if match:
                            dice_part = match.group(1)
                            old_dmg_bonus = int(match.group(2))
                            dmg_remainder = old_dmg_bonus - old_mod
                            if 0 <= dmg_remainder <= 3:
                                new_dmg_bonus = old_dmg_bonus + delta
                                if new_dmg_bonus == 0:
                                    dp.dice_expr = dice_part
                                elif new_dmg_bonus > 0:
                                    dp.dice_expr = f"{dice_part}+{new_dmg_bonus}"
                                else:
                                    dp.dice_expr = f"{dice_part}{new_dmg_bonus}"
                                dp.raw_text = f"{dp.dice_expr} {dp.damage_type}"
                    break  # Only apply one ability's delta per action

        # Rebuild editor action rows with updated values
        self._rebuild_action_rows()

    def _cascade_hp_on_con_change(self, old_scores: dict[str, int]) -> None:
        """Recalculate HP when CON score changes.

        Requires the HP formula field to contain a valid NdX+Y expression
        so the hit dice count is known.  Delta = dice_count * (new_mod - old_mod).
        """
        import re as _re

        old_con = old_scores.get("CON", 10)
        new_con = self._working_copy.ability_scores.get("CON", 10)
        if old_con == new_con:
            return

        formula_text = self._hp_formula_edit.text().strip()
        if not formula_text:
            return

        match = _re.match(r'(\d+)d(\d+)', formula_text)
        if not match:
            return

        dice_count = int(match.group(1))
        die_size = int(match.group(2))
        old_con_mod = (old_con - 10) // 2
        new_con_mod = (new_con - 10) // 2
        hp_delta = dice_count * (new_con_mod - old_con_mod)

        self._working_copy.hp = max(1, self._working_copy.hp + hp_delta)

        # Update flat HP spinbox
        self._hp_flat_spinbox.blockSignals(True)
        self._hp_flat_spinbox.setValue(self._working_copy.hp)
        self._hp_flat_spinbox.blockSignals(False)

        # Update formula text with new CON bonus
        new_bonus = dice_count * new_con_mod
        if new_bonus > 0:
            self._hp_formula_edit.setText(f"{dice_count}d{die_size}+{new_bonus}")
        elif new_bonus < 0:
            self._hp_formula_edit.setText(f"{dice_count}d{die_size}{new_bonus}")
        else:
            self._hp_formula_edit.setText(f"{dice_count}d{die_size}")

        if self._working_copy.hp != self._base_monster.hp:
            self._mod_sources["hp"] = "manual"
        else:
            self._mod_sources.pop("hp", None)

    # ------------------------------------------------------------------
    # Action rows rebuild
    # ------------------------------------------------------------------

    def _rebuild_action_rows(self) -> None:
        """Clear and rebuild all action editor rows from working_copy.actions."""
        # Clear existing rows
        layout = self._action_rows_layout
        while layout.count():
            item = layout.takeAt(0)
            widget = item.widget()
            if widget:
                widget.deleteLater()

        self._action_row_widgets: dict[int, tuple] = {}

        for idx, action in enumerate(self._working_copy.actions):
            row_widget = QWidget()
            row_layout = QHBoxLayout(row_widget)
            row_layout.setContentsMargins(0, 0, 0, 0)
            row_layout.setSpacing(4)

            # Name
            name_edit = QLineEdit(action.name)
            name_edit.setFixedWidth(120)
            name_edit.editingFinished.connect(
                lambda _idx=idx: self._on_action_field_changed(_idx)
            )
            row_layout.addWidget(name_edit)

            # To-hit bonus
            to_hit_spin = QSpinBox()
            to_hit_spin.setRange(-10, 30)
            to_hit_spin.setValue(action.to_hit_bonus if action.to_hit_bonus is not None else 0)
            to_hit_spin.setFixedWidth(55)
            to_hit_spin.setToolTip("To-hit bonus")
            to_hit_spin.editingFinished.connect(
                lambda _idx=idx: self._on_action_field_changed(_idx)
            )
            row_layout.addWidget(to_hit_spin)

            # Damage dice
            first_dp = action.damage_parts[0] if action.damage_parts else None
            dmg_dice_edit = QLineEdit(first_dp.dice_expr if first_dp else "1d6")
            dmg_dice_edit.setFixedWidth(70)
            dmg_dice_edit.setPlaceholderText("e.g. 2d6+3")
            dmg_dice_edit.editingFinished.connect(
                lambda _idx=idx: self._on_action_field_changed(_idx)
            )
            row_layout.addWidget(dmg_dice_edit)

            # Damage bonus
            dmg_bonus_spin = QSpinBox()
            dmg_bonus_spin.setRange(-10, 30)
            dmg_bonus_spin.setValue(
                getattr(action, "damage_bonus", 0) or 0
            )
            dmg_bonus_spin.setFixedWidth(55)
            dmg_bonus_spin.setToolTip("Damage bonus")
            dmg_bonus_spin.editingFinished.connect(
                lambda _idx=idx: self._on_action_field_changed(_idx)
            )
            row_layout.addWidget(dmg_bonus_spin)

            # Damage type
            dmg_type_edit = QLineEdit(first_dp.damage_type if first_dp else "bludgeoning")
            dmg_type_edit.setFixedWidth(90)
            dmg_type_edit.editingFinished.connect(
                lambda _idx=idx: self._on_action_field_changed(_idx)
            )
            row_layout.addWidget(dmg_type_edit)

            # [auto] badge for equipment-generated actions
            if action.is_equipment_generated:
                auto_label = QLabel("[auto]")
                auto_label.setStyleSheet("color: #4EA8DE; font-size: 8pt;")
                row_layout.addWidget(auto_label)

            # Remove button
            remove_btn = QPushButton("X")
            remove_btn.setFixedWidth(24)
            remove_btn.clicked.connect(
                lambda _checked, _idx=idx: self._on_remove_action(_idx)
            )
            row_layout.addWidget(remove_btn)

            row_layout.addStretch()
            layout.addWidget(row_widget)
            self._action_row_widgets[idx] = (
                name_edit, to_hit_spin, dmg_dice_edit, dmg_bonus_spin, dmg_type_edit
            )

    # ------------------------------------------------------------------
    # Buff rows rebuild
    # ------------------------------------------------------------------

    def _rebuild_buff_rows(self) -> None:
        """Clear and rebuild all buff editor rows from _buff_items."""
        layout = self._buff_rows_layout
        while layout.count():
            item = layout.takeAt(0)
            widget = item.widget()
            if widget:
                widget.deleteLater()

        self._buff_row_widgets: dict[int, tuple] = {}

        for idx, buff in enumerate(self._buff_items):
            row_widget = QWidget()
            row_layout = QHBoxLayout(row_widget)
            row_layout.setContentsMargins(0, 0, 0, 0)
            row_layout.setSpacing(4)

            # Name
            name_edit = QLineEdit(buff.name)
            name_edit.setFixedWidth(100)
            name_edit.editingFinished.connect(
                lambda _idx=idx: self._on_buff_field_changed(_idx)
            )
            row_layout.addWidget(name_edit)

            # Bonus value
            bonus_edit = QLineEdit(buff.bonus_value)
            bonus_edit.setFixedWidth(60)
            bonus_edit.setPlaceholderText("+1d4")
            bonus_edit.editingFinished.connect(
                lambda _idx=idx: self._on_buff_field_changed(_idx)
            )
            row_layout.addWidget(bonus_edit)

            # Target
            target_combo = QComboBox()
            for tgt in _BUFF_TARGETS:
                target_combo.addItem(tgt)
            # Set current target
            stored = buff.targets.replace("_", " ").title()
            if stored in _BUFF_TARGETS:
                target_combo.setCurrentText(stored)
            target_combo.currentIndexChanged.connect(
                lambda _i, _idx=idx: self._on_buff_field_changed(_idx)
            )
            row_layout.addWidget(target_combo)

            # Remove button
            remove_btn = QPushButton("X")
            remove_btn.setFixedWidth(24)
            remove_btn.clicked.connect(
                lambda _checked, _idx=idx: self._on_remove_buff(_idx)
            )
            row_layout.addWidget(remove_btn)

            row_layout.addStretch()
            layout.addWidget(row_widget)
            self._buff_row_widgets[idx] = (name_edit, bonus_edit, target_combo)

    # ------------------------------------------------------------------
    # Equipment helpers
    # ------------------------------------------------------------------

    def _update_weapon_list_widget(self) -> None:
        """Refresh the weapon QListWidget from _equipped_weapons."""
        self._weapon_list.clear()
        for equip_item, _action_dict in self._equipped_weapons:
            self._weapon_list.addItem(equip_item.item_name)

    def _update_equipment_summary(self) -> None:
        """Update the collapsed Equipment section header with a summary."""
        self._equipment_section.set_summary(self._equipment_summary_text())

    def _equipment_summary_text(self) -> str:
        """Build a comma-separated equipment summary string."""
        parts = []
        for equip_item, _ in self._equipped_weapons:
            parts.append(equip_item.item_name)
        if self._equipped_armor is not None:
            parts.append(self._equipped_armor[0].item_name)
        if self._equipped_shield is not None:
            parts.append(self._equipped_shield.item_name)
        if self._equipped_focus is not None:
            parts.append(self._equipped_focus.item_name)
        return ", ".join(parts) if parts else ""

    def _dict_to_action(self, action_dict: dict) -> Action:
        """Convert a compute_weapon_action() result dict to an Action."""
        return Action(
            name=action_dict["name"],
            to_hit_bonus=action_dict["to_hit_bonus"],
            damage_parts=[
                DamagePart(
                    dice_expr=action_dict["damage_dice"],
                    damage_type=action_dict["damage_type"],
                    raw_text=f"{action_dict['damage_dice']} {action_dict['damage_type']}",
                )
            ],
            raw_text=action_dict["name"],
            is_parsed=True,
            damage_bonus=action_dict.get("damage_bonus", 0),
            is_equipment_generated=action_dict.get("is_equipment_generated", True),
        )

    @staticmethod
    def _make_section_header(text: str) -> QLabel:
        """Create a bold sub-section header label."""
        label = QLabel(text)
        font = label.font()
        font.setBold(True)
        label.setFont(font)
        return label

    # ------------------------------------------------------------------
    # Three-tier color highlighting
    # ------------------------------------------------------------------

    def _apply_highlights(self) -> None:
        """Apply three-tier color highlighting to preview panel labels.

        Compares working_copy against base_monster field by field.
        Colors:
          - equipment (steel blue): AC changed by armor/shield, actions from weapon
          - manual (amber): any field manually edited by user
          - custom (red): save/skill that doesn't match expected prof math
        """
        # AC highlighting
        if self._working_copy.ac != self._base_monster.ac:
            source = self._mod_sources.get("ac", "manual")
            color = COLOR_EQUIPMENT if source == "equipment" else COLOR_MANUAL
            tooltip = f"Base: {self._base_monster.ac}"
            self._set_label_highlight(self._preview_panel._ac_label, color, tooltip)
        else:
            self._set_label_highlight(self._preview_panel._ac_label, COLOR_BASE, "")

        # HP highlighting
        if self._working_copy.hp != self._base_monster.hp:
            self._set_label_highlight(
                self._preview_panel._hp_label,
                COLOR_MANUAL,
                f"Base: {self._base_monster.hp}",
            )
        else:
            self._set_label_highlight(self._preview_panel._hp_label, COLOR_BASE, "")

        # Ability score highlighting
        for ability, label in self._preview_panel._ability_labels.items():
            base_score = self._base_monster.ability_scores.get(ability, 10)
            curr_score = self._working_copy.ability_scores.get(ability, 10)
            if curr_score != base_score:
                self._set_label_highlight(label, COLOR_MANUAL, f"Base: {base_score}")
            else:
                self._set_label_highlight(label, COLOR_BASE, "")

        # Per-save highlighting — only color individual saves that differ from base
        derived = self._engine.recalculate(self._working_copy)
        save_validations = {
            sv.ability: sv
            for sv in self._validator.validate_saves(self._working_copy, derived)
        }
        if self._working_copy.saves:
            parts = []
            for attr, val in self._working_copy.saves.items():
                text = f"{attr} {'+' if val >= 0 else ''}{val}"
                base_val = self._base_monster.saves.get(attr)
                if base_val is not None and val == base_val:
                    parts.append(text)
                else:
                    sv = save_validations.get(attr)
                    is_custom = sv and hasattr(sv, "state") and sv.state.value == "custom"
                    color = COLOR_CUSTOM_FLAG if is_custom else COLOR_MANUAL
                    parts.append(f'<span style="color: {color};">{text}</span>')
            self._preview_panel._saves_label.setText(", ".join(parts))
            self._preview_panel._saves_label.setToolTip("")
        else:
            self._set_label_highlight(self._preview_panel._saves_label, COLOR_BASE, "")

    def _set_label_highlight(self, label, color: str, tooltip: str) -> None:
        """Apply color highlighting to a QLabel using rich text for reliability.

        Uses HTML <span> wrapping instead of setStyleSheet to avoid
        Qt stylesheet cascade issues on Windows.
        """
        try:
            current_text = label.text()
            # Strip any existing HTML wrapping
            if current_text.startswith("<span"):
                import re as _re
                current_text = _re.sub(r"<[^>]+>", "", current_text)
            if color:
                label.setText(f'<span style="color: {color};">{current_text}</span>')
            else:
                label.setText(current_text)
            label.setToolTip(tooltip)
        except (AttributeError, RuntimeError):
            pass

    # ------------------------------------------------------------------
    # Signal handlers — user edits
    # ------------------------------------------------------------------

    def _on_name_changed(self) -> None:
        """Update working copy name and window title when name field finished."""
        if self._recalculating:
            return
        new_name = self._name_edit.text().strip()
        if new_name and new_name != self._working_copy.name:
            self._push_undo()
            self._working_copy.name = new_name
            self.setWindowTitle(f"Editing: {new_name}")
            self._rebuild_preview()

    def _on_ability_changed(self) -> None:
        """Collect all spinbox values, update working copy, rebuild preview.

        Also cascades ability score changes to:
        - Saving throws (recomputed for Prof/Expertise state)
        - ALL actions: equipment-generated (exact recompute) and imported
          (delta-based inference from old ability mod + proficiency)
        """
        if self._recalculating:
            return
        self._push_undo()
        # Snapshot old scores BEFORE overwriting (for action cascade inference)
        old_scores = dict(self._working_copy.ability_scores)
        for ability, spinbox in self._ability_spinboxes.items():
            old_score = self._base_monster.ability_scores.get(ability, 10)
            new_score = spinbox.value()
            self._working_copy.ability_scores[ability] = new_score
            if new_score != old_score:
                self._mod_sources[f"ability_{ability}"] = "manual"
            else:
                self._mod_sources.pop(f"ability_{ability}", None)
        # Cascade: recompute saves based on new ability modifiers
        self._sync_save_toggles(recompute_values=True)
        # Cascade: recompute ALL actions (equipment + imported)
        self._cascade_all_actions_on_ability_change(old_scores)
        # Cascade: recalculate HP when CON changes (requires hit dice formula)
        self._cascade_hp_on_con_change(old_scores)
        self._rebuild_preview()

    def _on_save_toggle_changed(self) -> None:
        """Handle save proficiency toggle button click."""
        if self._recalculating:
            return
        btn = self.sender()
        if btn is None:
            return
        ability: str = btn.property("ability")
        state_label: str = btn.property("state_label")

        # Uncheck all buttons in the group first, check only this one
        group = self._save_toggle_groups.get(ability, [])
        for b in group:
            b.setChecked(b is btn)

        custom_spin = self._save_custom_spinboxes.get(ability)
        is_custom = (state_label == "Custom")
        if custom_spin is not None:
            custom_spin.setEnabled(is_custom)
            custom_spin.setVisible(is_custom)

        self._push_undo()
        self._apply_save_value(ability, state_label)
        # Mark source
        if state_label == "Custom":
            self._mod_sources[f"save_{ability}"] = "custom"
        elif state_label != "Non-Prof":
            self._mod_sources[f"save_{ability}"] = "manual"
        else:
            self._mod_sources.pop(f"save_{ability}", None)
        self._rebuild_preview()

    def _on_save_custom_changed(self) -> None:
        """Handle custom save spinbox value change."""
        if self._recalculating:
            return
        spinbox = self.sender()
        if spinbox is None:
            return
        ability: str = spinbox.property("ability")
        self._push_undo()
        self._working_copy.saves[ability] = spinbox.value()
        self._mod_sources[f"save_{ability}"] = "custom"
        self._rebuild_preview()

    def _on_skill_toggle_changed(self) -> None:
        """Handle skill proficiency toggle button click."""
        if self._recalculating:
            return
        btn = self.sender()
        if btn is None:
            return
        skill_name: str = btn.property("skill_name")
        state_label: str = btn.property("state_label")

        row_data = self._skill_rows.get(skill_name)
        if row_data is None:
            return
        btn_group, custom_spin, _ = row_data

        for b in btn_group:
            b.setChecked(b is btn)

        is_custom = (state_label == "Custom")
        custom_spin.setEnabled(is_custom)
        custom_spin.setVisible(is_custom)

        self._push_undo()
        self._apply_skill_value(skill_name, state_label, custom_spin.value())
        self._rebuild_preview()

    def _on_skill_custom_changed(self) -> None:
        """Handle custom skill spinbox value change."""
        if self._recalculating:
            return
        spinbox = self.sender()
        if spinbox is None:
            return
        skill_name: str = spinbox.property("skill_name")
        self._push_undo()
        self._working_copy.skills[skill_name] = spinbox.value()
        self._rebuild_preview()

    def _on_add_skill(self, index: int) -> None:
        """Add a new skill row when user selects from the Add Skill combo."""
        if index == 0:
            return
        skill_name = self._add_skill_combo.currentText()
        self._add_skill_combo.blockSignals(True)
        self._add_skill_combo.setCurrentIndex(0)
        self._add_skill_combo.blockSignals(False)

        if skill_name in self._skill_rows:
            return  # Already present

        # Compute a default non-proficient value (ability modifier)
        ability = SKILL_TO_ABILITY.get(skill_name, "STR")
        score = self._working_copy.ability_scores.get(ability, 10)
        default_value = (score - 10) // 2

        self._push_undo()
        self._working_copy.skills[skill_name] = default_value
        self._add_skill_row(skill_name, default_value)
        self._rebuild_preview()

    def _remove_skill(self, skill_name: str) -> None:
        """Remove a skill row and delete from working copy."""
        row_data = self._skill_rows.pop(skill_name, None)
        if row_data is None:
            return
        _, _, row_widget = row_data
        self._push_undo()
        self._working_copy.skills.pop(skill_name, None)
        row_widget.setParent(None)
        row_widget.deleteLater()
        self._rebuild_preview()

    def _on_hp_changed(self) -> None:
        """Update working copy HP from formula and/or flat spinbox."""
        if self._recalculating:
            return
        self._push_undo()
        # Store formula in working copy as lore comment (no hp_formula field on Monster)
        # Update flat HP from spinbox
        self._working_copy.hp = self._hp_flat_spinbox.value()
        if self._working_copy.hp != self._base_monster.hp:
            self._mod_sources["hp"] = "manual"
        else:
            self._mod_sources.pop("hp", None)
        self._rebuild_preview()

    def _on_cr_changed(self, cr_text: str) -> None:
        """Update CR and trigger full recalculation (cascades prof bonus)."""
        if self._recalculating:
            return
        self._push_undo()
        self._working_copy.cr = cr_text
        self._sync_save_toggles()
        self._rebuild_preview()

    # ------------------------------------------------------------------
    # Core operations
    # ------------------------------------------------------------------

    def _rebuild_preview(self) -> None:
        """Recalculate derived stats, refresh the preview panel, apply highlights."""
        self._engine.recalculate(self._working_copy)
        self._preview_panel.show_monster(self._working_copy)
        self.setWindowTitle(f"Editing: {self._working_copy.name}")
        self._apply_highlights()

    def _push_undo(self) -> None:
        """Push a deep copy of the working monster onto the undo stack."""
        self._undo_stack.append(copy.deepcopy(self._working_copy))
        self._dirty = True

    def _undo(self) -> None:
        """Restore the most recent undo snapshot and repopulate the form."""
        if not self._undo_stack:
            return
        self._working_copy = self._undo_stack.pop()
        self._populate_form()
        self._rebuild_preview()
        # Dirty remains True (unless undo_stack fully empty and matches base)
        if not self._undo_stack:
            self._dirty = False

    def _discard(self) -> None:
        """Prompt to discard changes if dirty, then close."""
        if self._dirty:
            reply = QMessageBox.question(
                self,
                "Discard changes?",
                "Discard all changes to this monster?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                QMessageBox.StandardButton.No,
            )
            if reply != QMessageBox.StandardButton.Yes:
                return
        self._dirty = False  # Suppress closeEvent guard
        self.reject()

    # ------------------------------------------------------------------
    # Close / reject guards
    # ------------------------------------------------------------------

    def closeEvent(self, event) -> None:
        """Guard against closing with unsaved changes."""
        if not self._dirty:
            event.accept()
            return

        box = QMessageBox(self)
        box.setWindowTitle("Unsaved changes")
        box.setText("You have unsaved changes.")
        box.setInformativeText("What do you want to do?")
        save_btn = box.addButton("Save", QMessageBox.ButtonRole.AcceptRole)
        discard_btn = box.addButton("Discard", QMessageBox.ButtonRole.DestructiveRole)
        cancel_btn = box.addButton("Cancel", QMessageBox.ButtonRole.RejectRole)
        box.setDefaultButton(cancel_btn)
        box.exec()

        clicked = box.clickedButton()
        if clicked == save_btn:
            # Real save logic: suppress event and let _save_override handle close.
            event.ignore()
            self._save_override()
        elif clicked == discard_btn:
            self._dirty = False
            event.accept()
        else:
            event.ignore()

    def reject(self) -> None:
        """Route Escape/reject through close() so the closeEvent guard fires."""
        self.close()

    # ------------------------------------------------------------------
    # Form population / sync helpers
    # ------------------------------------------------------------------

    def _populate_form(self) -> None:
        """Repopulate all form widgets from self._working_copy.

        Uses blockSignals() to prevent signal re-entry during programmatic
        updates.
        """
        self._recalculating = True
        try:
            # Name
            self._name_edit.blockSignals(True)
            self._name_edit.setText(self._working_copy.name)
            self._name_edit.blockSignals(False)

            # Ability scores
            for ability, spinbox in self._ability_spinboxes.items():
                spinbox.blockSignals(True)
                spinbox.setValue(self._working_copy.ability_scores.get(ability, 10))
                spinbox.blockSignals(False)

            # Saving throws — sync toggles
            self._sync_save_toggles()

            # HP
            self._hp_flat_spinbox.blockSignals(True)
            self._hp_flat_spinbox.setValue(max(1, self._working_copy.hp))
            self._hp_flat_spinbox.blockSignals(False)

            # CR
            self._cr_combo.blockSignals(True)
            cr = self._working_copy.cr or "1"
            if cr in _CR_VALUES:
                self._cr_combo.setCurrentText(cr)
            self._cr_combo.blockSignals(False)

            # Rebuild action rows (restores from working_copy)
            self._rebuild_action_rows()
            # Rebuild buff rows (restores from _buff_items)
            self._rebuild_buff_rows()

        finally:
            self._recalculating = False

    def _sync_save_toggles(self, recompute_values: bool = False) -> None:
        """Sync the saving throw toggle buttons from working_copy saves.

        Determines the SaveState for each ability by comparing the monster's
        actual save value against the expected non-prof / prof / expertise
        values from the math engine.

        When recompute_values is True (e.g. after ability score changes),
        the toggle state is read from the UI buttons (which reflect the
        user's intent) rather than inferred from the stale numerical value,
        and save values are recomputed to match new ability modifiers.
        """
        derived = self._engine.recalculate(self._working_copy)

        for ability in _ABILITY_LABELS:
            group = self._save_toggle_groups.get(ability, [])
            custom_spin = self._save_custom_spinboxes.get(ability)
            if not group:
                continue

            if recompute_values:
                # Read state from the currently-checked UI button.
                # After an ability score change the old numerical value no
                # longer matches any expected tier, so inferring from the
                # value would misclassify Prof/Expertise as "Custom".
                state_label = "Non-Prof"
                for btn in group:
                    if btn.isChecked():
                        state_label = btn.property("state_label")
                        break
                self._apply_save_value(ability, state_label)
            else:
                actual = self._working_copy.saves.get(ability)
                if actual is None:
                    state_label = "Non-Prof"
                else:
                    non_prof = derived.expected_saves.get(ability, 0)
                    prof = derived.expected_proficient_saves.get(ability, 0)
                    expertise = derived.expected_expertise_saves.get(ability, 0)

                    if actual == expertise:
                        state_label = "Expertise"
                    elif actual == prof:
                        state_label = "Prof"
                    elif actual == non_prof:
                        state_label = "Non-Prof"
                    else:
                        state_label = "Custom"

            for btn in group:
                btn.blockSignals(True)
                btn.setChecked(btn.property("state_label") == state_label)
                btn.blockSignals(False)

            is_custom = (state_label == "Custom")
            if custom_spin is not None:
                custom_spin.blockSignals(True)
                if is_custom:
                    actual = self._working_copy.saves.get(ability)
                    if actual is not None:
                        custom_spin.setValue(actual)
                custom_spin.setEnabled(is_custom)
                custom_spin.setVisible(is_custom)
                custom_spin.blockSignals(False)

    def _sync_skill_toggle(self, skill_name: str, skill_value: int) -> None:
        """Sync a single skill row's toggle state from the given value."""
        row_data = self._skill_rows.get(skill_name)
        if row_data is None:
            return
        btn_group, custom_spin, _ = row_data

        derived = self._engine.recalculate(self._working_copy)
        ability = SKILL_TO_ABILITY.get(skill_name, "STR")
        mod = derived.ability_modifiers.get(ability, 0)
        prof = derived.proficiency_bonus

        non_prof_val = mod
        prof_val = mod + prof
        expertise_val = mod + 2 * prof

        if skill_value == expertise_val:
            state_label = "Expertise"
        elif skill_value == prof_val:
            state_label = "Prof"
        elif skill_value == non_prof_val:
            state_label = "Non-Prof"
        else:
            state_label = "Custom"

        for btn in btn_group:
            btn.blockSignals(True)
            btn.setChecked(btn.property("state_label") == state_label)
            btn.blockSignals(False)

        is_custom = (state_label == "Custom")
        custom_spin.blockSignals(True)
        custom_spin.setValue(skill_value)
        custom_spin.setEnabled(is_custom)
        custom_spin.setVisible(is_custom)
        custom_spin.blockSignals(False)

    def _apply_save_value(self, ability: str, state_label: str) -> None:
        """Write the computed save value into working_copy.saves."""
        derived = self._engine.recalculate(self._working_copy)
        mod = derived.ability_modifiers.get(ability, 0)
        prof = derived.proficiency_bonus

        if state_label == "Non-Prof":
            # Non-proficient: remove from saves dict
            self._working_copy.saves.pop(ability, None)
        elif state_label == "Prof":
            self._working_copy.saves[ability] = mod + prof
        elif state_label == "Expertise":
            self._working_copy.saves[ability] = mod + 2 * prof
        elif state_label == "Custom":
            # Keep whatever the custom spinbox currently holds
            custom_spin = self._save_custom_spinboxes.get(ability)
            if custom_spin is not None:
                self._working_copy.saves[ability] = custom_spin.value()

    def _apply_skill_value(self, skill_name: str, state_label: str, custom_value: int) -> None:
        """Write the computed skill value into working_copy.skills."""
        derived = self._engine.recalculate(self._working_copy)
        ability = SKILL_TO_ABILITY.get(skill_name, "STR")
        mod = derived.ability_modifiers.get(ability, 0)
        prof = derived.proficiency_bonus

        if state_label == "Non-Prof":
            self._working_copy.skills[skill_name] = mod
        elif state_label == "Prof":
            self._working_copy.skills[skill_name] = mod + prof
        elif state_label == "Expertise":
            self._working_copy.skills[skill_name] = mod + 2 * prof
        elif state_label == "Custom":
            self._working_copy.skills[skill_name] = custom_value

    # ------------------------------------------------------------------
    # Public accessors for Plan 05 persistence
    # ------------------------------------------------------------------

    def get_equipment_items(self) -> list[EquipmentItem]:
        """Return all currently equipped items as EquipmentItem list for persistence."""
        items = []
        for equip_item, _ in self._equipped_weapons:
            items.append(equip_item)
        if self._equipped_armor is not None:
            items.append(self._equipped_armor[0])
        if self._equipped_shield is not None:
            items.append(self._equipped_shield)
        if self._equipped_focus is not None:
            items.append(self._equipped_focus)
        return items

    def get_buff_items(self) -> list[BuffItem]:
        """Return current buff list for persistence."""
        return list(self._buff_items)

    def get_focus_bonus(self) -> int:
        """Return current focus bonus for spellcasting persistence."""
        return self._focus_bonus

    # ------------------------------------------------------------------
    # Save handlers
    # ------------------------------------------------------------------

    def _build_modification(self, base_name: str, custom_name: Optional[str] = None) -> MonsterModification:
        """Build a MonsterModification from the diff between _base_monster and _working_copy.

        Only stores fields that actually changed from the base monster so the
        persisted dict stays minimal.
        """
        base = self._base_monster
        wc = self._working_copy

        # Changed ability scores only
        changed_ability_scores = {
            ability: score
            for ability, score in wc.ability_scores.items()
            if score != base.ability_scores.get(ability, 10)
        }

        # Changed saves only
        changed_saves = dict(wc.saves) if wc.saves != base.saves else {}

        # Changed skills only
        changed_skills = dict(wc.skills) if wc.skills != base.skills else {}

        # HP and AC — store if changed
        hp = wc.hp if wc.hp != base.hp else None
        ac = wc.ac if wc.ac != base.ac else None
        cr = wc.cr if wc.cr != base.cr else None
        size = wc.size if wc.size != base.size else None

        # HP formula from UI widget (if filled in)
        hp_formula_text = self._hp_formula_edit.text().strip() or None

        # Serialize actions
        serialized_actions = []
        for action in wc.actions:
            serialized_actions.append({
                "name": action.name,
                "to_hit_bonus": action.to_hit_bonus,
                "damage_bonus": action.damage_bonus,
                "is_equipment_generated": action.is_equipment_generated,
                "damage_parts": [
                    {
                        "dice_expr": dp.dice_expr,
                        "damage_type": dp.damage_type,
                        "raw_text": dp.raw_text,
                    }
                    for dp in action.damage_parts
                ],
                "raw_text": action.raw_text,
                "is_parsed": action.is_parsed,
            })

        return MonsterModification(
            base_name=base_name,
            custom_name=custom_name,
            ability_scores=changed_ability_scores,
            saves=changed_saves,
            skills=changed_skills,
            hp=hp,
            hp_formula=hp_formula_text,
            ac=ac,
            cr=cr,
            size=size,
            equipment=self.get_equipment_items(),
            buffs=self.get_buff_items(),
            actions=serialized_actions,
        )

    def _modification_to_dict(self, mod: MonsterModification) -> dict:
        """Serialize a MonsterModification to a JSON-compatible dict."""
        return {
            "base_name": mod.base_name,
            "custom_name": mod.custom_name,
            "ability_scores": mod.ability_scores,
            "saves": mod.saves,
            "skills": mod.skills,
            "hp": mod.hp,
            "hp_formula": mod.hp_formula,
            "ac": mod.ac,
            "cr": mod.cr,
            "size": mod.size,
            "equipment": [dataclasses.asdict(e) for e in mod.equipment],
            "buffs": [dataclasses.asdict(b) for b in mod.buffs],
            "actions": mod.actions,
            "spellcasting_infos": [],
        }

    def _save_override(self) -> None:
        """Save the working copy as an override of the base monster.

        - Replaces the base monster in the library.
        - Persists the MonsterModification.
        - Emits monster_saved and closes.
        """
        # Carry buffs onto the Monster object so AttackRollerTab sees them
        self._working_copy.buffs = list(self._buff_items)

        if self._library is not None:
            self._library.replace(self._working_copy)

        if self._persistence is not None:
            mod = self._build_modification(base_name=self._base_monster.name)
            persisted = self._persistence.load_modified_monsters()
            key = self._working_copy.name
            persisted[key] = self._modification_to_dict(mod)
            self._persistence.save_modified_monsters(persisted)

        self._dirty = False
        self.monster_saved.emit(self._working_copy)
        self.accept()

    def _save_as_copy(self) -> None:
        """Save the working copy as a new named monster in the library.

        Prompts for a name, validates uniqueness, then adds the copy to the
        library and persists it with custom_name set.
        """
        while True:
            proposed_name, ok = QInputDialog.getText(
                self,
                "Save as Copy",
                "Enter a name for the copy:",
            )
            if not ok:
                return  # User cancelled

            proposed_name = proposed_name.strip()
            if not proposed_name:
                QMessageBox.warning(self, "Invalid Name", "Name cannot be empty.")
                continue

            if self._library is not None and self._library.has_name(proposed_name):
                QMessageBox.warning(
                    self,
                    "Name Already Exists",
                    f'"{proposed_name}" already exists in the library.\nPlease choose a different name.',
                )
                continue

            break  # Valid unique name obtained

        # Apply the proposed name to the working copy
        self._working_copy.name = proposed_name
        # Carry buffs onto the Monster object
        self._working_copy.buffs = list(self._buff_items)

        if self._library is not None:
            self._library.add(self._working_copy)

        if self._persistence is not None:
            mod = self._build_modification(
                base_name=self._base_monster.name,
                custom_name=proposed_name,
            )
            persisted = self._persistence.load_modified_monsters()
            persisted[proposed_name] = self._modification_to_dict(mod)
            self._persistence.save_modified_monsters(persisted)

        self._dirty = False
        self.monster_saved.emit(self._working_copy)
        self.accept()
