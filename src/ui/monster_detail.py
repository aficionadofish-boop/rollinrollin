"""MonsterDetailPanel — full statblock display with collapsible lore and tag editor.

Displays all fields of a Monster object in a readable layout:
  - Name (large, bold)
  - Stats grid: AC, HP, CR, Type
  - Ability scores row: STR DEX CON INT WIS CHA with modifiers
  - Saving throws (comma-separated, or "None")
  - Actions: Roll button for parsed attacks, raw text for unparsed
  - Tags: editable QLineEdit synced to monster.tags
  - Lore: hidden by default; shown via a toggle button, markdown stripped

Lore section uses a QPushButton toggle that shows/hides a QTextEdit.
This avoids the QGroupBox checkable pattern which greys out content but
keeps it visible — the requirement is fully hidden until the user clicks.
"""
from __future__ import annotations
import re

from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QGridLayout,
    QLabel,
    QPushButton,
    QLineEdit,
    QScrollArea,
    QSizePolicy,
    QTextEdit,
)
from PySide6.QtCore import Qt

from src.domain.models import Monster, Action


ABILITY_LABELS = ["STR", "DEX", "CON", "INT", "WIS", "CHA"]

# Markdown patterns to strip before displaying lore text
_MD_HEADING_RE = re.compile(r'^#{1,6}\s*', re.MULTILINE)
_MD_BOLD_RE = re.compile(r'\*{2,3}([^*]+)\*{2,3}')
_MD_ITALIC_RE = re.compile(r'\*([^*]+)\*')


def _strip_markdown(text: str) -> str:
    """Remove basic Markdown syntax from lore text before display.

    Strips:
      - Heading markers (## Monster Name -> Monster Name)
      - Bold (***text*** or **text** -> text)
      - Italic (*text* -> text)

    Leaves plain text paragraphs intact.
    """
    text = _MD_HEADING_RE.sub('', text)
    text = _MD_BOLD_RE.sub(r'\1', text)
    text = _MD_ITALIC_RE.sub(r'\1', text)
    return text.strip()


class MonsterDetailPanel(QWidget):
    """Full statblock display panel with toggle-expandable lore and editable tags.

    Scroll area wraps all content.  The lore section is HIDDEN by default;
    a QPushButton toggle shows/hides a QTextEdit containing the lore text
    with Markdown syntax stripped.
    """

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self._current_monster: Monster | None = None
        self._lore_expanded: bool = False
        self._setup_ui()

    # ------------------------------------------------------------------
    # Setup
    # ------------------------------------------------------------------

    def _setup_ui(self) -> None:
        outer_layout = QVBoxLayout(self)
        outer_layout.setContentsMargins(0, 0, 0, 0)

        # Scroll area wrapping the content widget
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)

        content_widget = QWidget()
        self._content_layout = QVBoxLayout(content_widget)
        self._content_layout.setAlignment(Qt.AlignmentFlag.AlignTop)

        # 1. Name label (large, bold)
        self._name_label = QLabel("")
        font = self._name_label.font()
        font.setPointSize(14)
        font.setBold(True)
        self._name_label.setFont(font)
        self._name_label.setWordWrap(True)
        self._content_layout.addWidget(self._name_label)

        # 2. Stats grid: AC | HP | CR | Type
        stats_grid = QGridLayout()
        self._ac_label = QLabel("")
        self._hp_label = QLabel("")
        self._cr_label = QLabel("")
        self._type_label = QLabel("")
        stats_grid.addWidget(QLabel("AC:"), 0, 0)
        stats_grid.addWidget(self._ac_label, 0, 1)
        stats_grid.addWidget(QLabel("HP:"), 0, 2)
        stats_grid.addWidget(self._hp_label, 0, 3)
        stats_grid.addWidget(QLabel("CR:"), 1, 0)
        stats_grid.addWidget(self._cr_label, 1, 1)
        stats_grid.addWidget(QLabel("Type:"), 1, 2)
        stats_grid.addWidget(self._type_label, 1, 3)
        self._content_layout.addLayout(stats_grid)

        # 3. Ability scores row: STR DEX CON INT WIS CHA
        ability_layout = QHBoxLayout()
        self._ability_labels: dict[str, QLabel] = {}
        for ability in ABILITY_LABELS:
            col_widget = QWidget()
            col_layout = QVBoxLayout(col_widget)
            col_layout.setContentsMargins(2, 2, 2, 2)
            col_layout.setSpacing(0)
            header = QLabel(ability)
            header.setAlignment(Qt.AlignmentFlag.AlignCenter)
            header_font = header.font()
            header_font.setBold(True)
            header.setFont(header_font)
            value_label = QLabel("10 (+0)")
            value_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            col_layout.addWidget(header)
            col_layout.addWidget(value_label)
            self._ability_labels[ability] = value_label
            ability_layout.addWidget(col_widget)
        self._content_layout.addLayout(ability_layout)

        # 4. Saving throws
        saves_row = QHBoxLayout()
        saves_row.addWidget(QLabel("Saving Throws:"))
        self._saves_label = QLabel("None")
        self._saves_label.setWordWrap(True)
        saves_row.addWidget(self._saves_label, 1)
        self._content_layout.addLayout(saves_row)

        # 5. Actions section label + dynamic action rows
        self._actions_label = QLabel("Actions")
        actions_header_font = self._actions_label.font()
        actions_header_font.setBold(True)
        actions_header_font.setPointSize(11)
        self._actions_label.setFont(actions_header_font)
        self._content_layout.addWidget(self._actions_label)

        # Container widget for dynamic action rows
        self._actions_container = QWidget()
        self._actions_layout = QVBoxLayout(self._actions_container)
        self._actions_layout.setContentsMargins(0, 0, 0, 0)
        self._actions_layout.setSpacing(2)
        self._content_layout.addWidget(self._actions_container)

        # 6. Tags QLineEdit
        tags_row = QHBoxLayout()
        tags_row.addWidget(QLabel("Tags:"))
        self._tags_edit = QLineEdit()
        self._tags_edit.setPlaceholderText("comma-separated tags...")
        self._tags_edit.textChanged.connect(self._on_tags_changed)
        tags_row.addWidget(self._tags_edit, 1)
        self._content_layout.addLayout(tags_row)

        # 7. Lore section — toggle button + hidden QTextEdit
        #    Button label changes to indicate collapsed/expanded state.
        self._lore_toggle_btn = QPushButton("+ Lore && Description")
        self._lore_toggle_btn.setCheckable(False)
        self._lore_toggle_btn.clicked.connect(self._toggle_lore)
        self._content_layout.addWidget(self._lore_toggle_btn)

        self._lore_edit = QTextEdit()
        self._lore_edit.setReadOnly(True)
        self._lore_edit.setPlaceholderText("No lore recorded.")
        self._lore_edit.setMinimumHeight(80)
        self._lore_edit.setVisible(False)  # hidden by default
        self._content_layout.addWidget(self._lore_edit)

        # Spacer at bottom
        self._content_layout.addStretch(1)

        scroll.setWidget(content_widget)
        outer_layout.addWidget(scroll)

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def show_monster(self, monster: Monster) -> None:
        """Populate all widgets with the given monster's data."""
        self._current_monster = monster

        # Name
        self._name_label.setText(monster.name)

        # Stats
        self._ac_label.setText(str(monster.ac))
        self._hp_label.setText(str(monster.hp))
        self._cr_label.setText(monster.cr or "\u2014")
        self._type_label.setText(monster.creature_type or "\u2014")

        # Ability scores
        for ability in ABILITY_LABELS:
            score = monster.ability_scores.get(ability, 10)
            modifier = _modifier_str(score)
            self._ability_labels[ability].setText(f"{score} {modifier}")

        # Saving throws
        if monster.saves:
            saves_parts = [
                f"{attr} {'+' if val >= 0 else ''}{val}"
                for attr, val in monster.saves.items()
            ]
            self._saves_label.setText(", ".join(saves_parts))
        else:
            self._saves_label.setText("None")

        # Actions — clear and rebuild
        self._clear_actions_layout()
        for action in monster.actions:
            self._add_action_row(action)

        # Tags — block signal to avoid spurious mutation
        self._tags_edit.blockSignals(True)
        self._tags_edit.setText(", ".join(monster.tags))
        self._tags_edit.blockSignals(False)

        # Lore — always reset to collapsed when switching monsters
        lore_raw = monster.lore if monster.lore else ""
        lore_clean = _strip_markdown(lore_raw) if lore_raw else ""
        self._lore_edit.setPlainText(lore_clean if lore_clean else "No lore recorded.")
        self._lore_edit.setVisible(False)
        self._lore_expanded = False
        self._lore_toggle_btn.setText("+ Lore && Description")

    def clear(self) -> None:
        """Clear all widgets; called when no monster is selected."""
        self._current_monster = None
        self._name_label.setText("")
        self._ac_label.setText("")
        self._hp_label.setText("")
        self._cr_label.setText("")
        self._type_label.setText("")
        for ability in ABILITY_LABELS:
            self._ability_labels[ability].setText("")
        self._saves_label.setText("")
        self._clear_actions_layout()
        self._tags_edit.blockSignals(True)
        self._tags_edit.clear()
        self._tags_edit.blockSignals(False)
        self._lore_edit.clear()
        self._lore_edit.setVisible(False)
        self._lore_expanded = False
        self._lore_toggle_btn.setText("+ Lore && Description")

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    def _toggle_lore(self) -> None:
        """Show or hide the lore QTextEdit when the toggle button is clicked."""
        self._lore_expanded = not self._lore_expanded
        self._lore_edit.setVisible(self._lore_expanded)
        if self._lore_expanded:
            self._lore_toggle_btn.setText("- Lore & Description")
        else:
            self._lore_toggle_btn.setText("+ Lore && Description")

    def _clear_actions_layout(self) -> None:
        """Remove all widgets from the actions layout."""
        layout = self._actions_layout
        while layout.count():
            item = layout.takeAt(0)
            widget = item.widget()
            if widget:
                widget.deleteLater()

    def _add_action_row(self, action: Action) -> None:
        """Add a single action row widget to the actions layout."""
        if action.is_parsed and action.to_hit_bonus is not None:
            # Parsed attack action — show name + disabled Roll button
            row_widget = QWidget()
            row_layout = QHBoxLayout(row_widget)
            row_layout.setContentsMargins(0, 0, 0, 0)
            name_label = QLabel(action.name)
            name_label.setSizePolicy(
                QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred
            )
            roll_btn = QPushButton("Roll")
            roll_btn.setEnabled(False)  # Phase 3 will wire this
            row_layout.addWidget(name_label)
            row_layout.addWidget(roll_btn)
            self._actions_layout.addWidget(row_widget)
        else:
            # Unparsed action — raw text only, no button
            raw_label = QLabel(action.raw_text or action.name)
            raw_label.setWordWrap(True)
            self._actions_layout.addWidget(raw_label)

    def _on_tags_changed(self, text: str) -> None:
        """Sync tag edits back to the live Monster object."""
        if self._current_monster is not None:
            tags = [t.strip() for t in text.split(",") if t.strip()]
            self._current_monster.tags = tags


def _modifier_str(score: int) -> str:
    """Return D&D 5e ability modifier string for a given score.

    Uses Python integer division (rounds toward negative infinity), which
    matches 5e convention: -7 // 2 = -4 -> modifier -4, not -3.

    Examples:
        10 -> "(+0)"
        14 -> "(+2)"
        8  -> "(-1)"
        1  -> "(-5)"
    """
    modifier = (score - 10) // 2
    if modifier >= 0:
        return f"(+{modifier})"
    return f"({modifier})"
