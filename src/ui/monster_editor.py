"""MonsterEditorDialog — near-fullscreen modal editor for Monster objects.

Provides:
  - CollapsibleSection: reusable collapsible QWidget for grouping editor fields
  - MonsterEditorDialog: two-column modal dialog (edit fields left, live preview right)

Layout:
  - Toolbar: editable name, Save dropdown (stub), Discard, Undo
  - Left (scroll area): collapsible sections for Ability Scores, Saving Throws,
    Skills, Hit Points, Challenge Rating
  - Right: MonsterDetailPanel preview, updated live on every change

The editor never mutates the original Monster object.  All changes are applied
to a deep copy (_working_copy) and reflected immediately in the right-hand
preview via MonsterMathEngine.recalculate().

Unsaved-changes guard: closing/escaping with a dirty working copy prompts the
user to confirm discard (Save option is a stub; wired in Plan 05).

Undo stack: every user action pushes a deep copy of _working_copy onto
_undo_stack.  Undo pops the most recent snapshot, repopulates all form
widgets, and refreshes the preview.
"""
from __future__ import annotations

import copy
from typing import Optional

from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QFont
from PySide6.QtWidgets import (
    QComboBox,
    QDialog,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
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

from src.domain.models import Monster, SKILL_TO_ABILITY
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

    Signals
    -------
    monster_saved : Signal(object)
        Emitted when the user saves (Plan 05 connects this).
    """

    monster_saved = Signal(object)  # Monster

    def __init__(self, monster: Monster, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)

        # Core state
        self._base_monster: Monster = monster
        self._working_copy: Monster = copy.deepcopy(monster)
        self._undo_stack: list[Monster] = []
        self._recalculating: bool = False
        self._dirty: bool = False

        # Math helpers
        self._engine = MonsterMathEngine()
        self._validator = MathValidator()

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

        # Save button with drop-down menu (stubs — Plan 05 wires)
        save_btn = QPushButton("Save")
        save_menu = QMenu(save_btn)
        save_menu.addAction("Save (override base)", self._save_override_stub)
        save_menu.addAction("Save as Copy...", self._save_copy_stub)
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
        """Collect all spinbox values, update working copy, rebuild preview."""
        if self._recalculating:
            return
        self._push_undo()
        for ability, spinbox in self._ability_spinboxes.items():
            self._working_copy.ability_scores[ability] = spinbox.value()
        self._sync_save_toggles()
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
        """Recalculate derived stats and refresh the preview panel."""
        self._engine.recalculate(self._working_copy)
        self._preview_panel.show_monster(self._working_copy)
        self.setWindowTitle(f"Editing: {self._working_copy.name}")

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
            # Save is a stub in this plan — Plan 05 wires real save logic.
            # For now, treat as discard and close so the dialog does not hang.
            self._dirty = False
            event.accept()
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

        finally:
            self._recalculating = False

    def _sync_save_toggles(self) -> None:
        """Sync the saving throw toggle buttons from working_copy saves.

        Determines the SaveState for each ability by comparing the monster's
        actual save value against the expected non-prof / prof / expertise
        values from the math engine.
        """
        derived = self._engine.recalculate(self._working_copy)

        for ability in _ABILITY_LABELS:
            group = self._save_toggle_groups.get(ability, [])
            custom_spin = self._save_custom_spinboxes.get(ability)
            if not group:
                continue

            actual = self._working_copy.saves.get(ability)
            if actual is None:
                # No save entry — default to Non-Prof visually
                state_label = "Non-Prof"
            else:
                non_prof = derived.expected_saves.get(ability, 0)
                prof = derived.expected_proficient_saves.get(ability, 0)
                expertise = derived.expected_expertise_saves.get(ability, 0)

                # Map SaveState to toggle label
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
                if is_custom and actual is not None:
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
    # Stub save handlers (Plan 05 wires real logic)
    # ------------------------------------------------------------------

    def _save_override_stub(self) -> None:
        """Stub: Save (override base) — Plan 05 wires this."""
        pass

    def _save_copy_stub(self) -> None:
        """Stub: Save as Copy — Plan 05 wires this."""
        pass
