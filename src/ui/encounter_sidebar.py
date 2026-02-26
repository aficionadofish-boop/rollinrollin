"""EncounterSidebarDock — persistent QDockWidget encounter sidebar.

Displays the active encounter (monster list with inline-editable count and X
remove buttons) as a collapsible panel docked to the right side of MainWindow.
Wired into MainWindow in Plan 02.
"""
from __future__ import annotations

from PySide6.QtWidgets import (
    QDockWidget,
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QSpinBox,
    QPushButton,
    QScrollArea,
    QSizePolicy,
    QMenu,
    QListWidget,
    QListWidgetItem,
    QAbstractItemView,
)
from PySide6.QtCore import Qt, Signal

# ---------------------------------------------------------------------------
# XP lookup table and helpers (D&D 5e SRD, static values)
# ---------------------------------------------------------------------------

_XP_BY_CR: dict[str, int] = {
    "0": 10, "1/8": 25, "1/4": 50, "1/2": 100,
    "1": 200, "2": 450, "3": 700, "4": 1100,
    "5": 1800, "6": 2300, "7": 2900, "8": 3900,
    "9": 5000, "10": 5900, "11": 7200, "12": 8400,
    "13": 10000, "14": 11500, "15": 13000, "16": 15000,
    "17": 18000, "18": 20000, "19": 22000, "20": 25000,
    "21": 33000, "22": 41000, "23": 50000, "24": 62000,
}


def cr_to_float(cr: str) -> float:
    """Convert CR string to float for sorting (CR descending)."""
    if "/" in cr:
        n, d = cr.split("/")
        return int(n) / int(d)
    try:
        return float(cr)
    except ValueError:
        return 0.0


def compute_encounter_xp(members: list[tuple]) -> int:
    """Return total base XP for a list of (Monster, count) pairs."""
    total = 0
    for monster, count in members:
        xp = _XP_BY_CR.get(str(getattr(monster, "cr", "0")), 0)
        total += xp * count
    return total


# ---------------------------------------------------------------------------
# Monster row widget
# ---------------------------------------------------------------------------


class _MonsterRowWidget(QWidget):
    """Single encounter row: name label | count spinbox | remove button."""

    count_changed = Signal(str, int)      # (monster_name, new_count)
    remove_requested = Signal(str)        # monster_name
    context_menu_requested = Signal(str, object, "QPoint")  # (monster_name, monster, pos)

    def __init__(self, monster, count: int = 1, parent=None) -> None:
        super().__init__(parent)
        self._monster = monster
        self._monster_name: str = monster.name

        layout = QHBoxLayout(self)
        layout.setContentsMargins(4, 2, 4, 2)
        layout.setSpacing(4)

        self._name_label = QLabel(monster.name)
        self._name_label.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
        self._name_label.setToolTip(f"CR {getattr(monster, 'cr', '?')}")

        self._count_spin = QSpinBox()
        self._count_spin.setRange(1, 99)
        self._count_spin.setFixedWidth(56)
        self._count_spin.blockSignals(True)
        self._count_spin.setValue(count)
        self._count_spin.blockSignals(False)
        self._count_spin.valueChanged.connect(self._on_count_changed)

        self._remove_btn = QPushButton("Del")
        self._remove_btn.setFixedHeight(24)
        self._remove_btn.setToolTip(f"Remove {monster.name}")
        self._remove_btn.clicked.connect(lambda: self.remove_requested.emit(self._monster_name))

        layout.addWidget(self._name_label)
        layout.addWidget(self._count_spin)
        layout.addWidget(self._remove_btn)

        # Right-click context menu
        self.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.customContextMenuRequested.connect(self._on_context_menu_requested)

    def _on_count_changed(self, value: int) -> None:
        self.count_changed.emit(self._monster_name, value)

    def _on_context_menu_requested(self, pos) -> None:
        self.context_menu_requested.emit(self._monster_name, self._monster, self.mapToGlobal(pos))

    def get_count(self) -> int:
        return self._count_spin.value()

    def set_count(self, count: int) -> None:
        self._count_spin.blockSignals(True)
        self._count_spin.setValue(count)
        self._count_spin.blockSignals(False)

    def get_monster(self):
        return self._monster

    def set_selected(self, selected: bool) -> None:
        """Highlight/unhighlight this row with a theme-safe translucent overlay."""
        if selected:
            self.setStyleSheet(
                "_MonsterRowWidget { background-color: rgba(255, 255, 255, 30); }"
            )
        else:
            self.setStyleSheet("")


# ---------------------------------------------------------------------------
# EncounterSidebarDock
# ---------------------------------------------------------------------------


class EncounterSidebarDock(QDockWidget):
    """Persistent QDockWidget encounter sidebar.

    Emits signals for MainWindow to wire to other tabs. All monster state
    is held here; MainWindow reads/writes via the public API.
    """

    # --- Signals (wired by MainWindow in Plan 02) ---
    monster_selected = Signal(object)           # Monster — single-click preload
    switch_to_attack_roller = Signal()          # double-click → switch tab
    encounter_changed = Signal(list)            # [(Monster, count)] on any mutation
    view_stat_block_requested = Signal(object)  # Monster — context menu "View Stat Block"
    save_btn_clicked = Signal()                 # Save button pressed
    load_btn_clicked = Signal()                 # Load button pressed

    _COLLAPSED_WIDTH = 60
    _DEFAULT_EXPANDED_WIDTH = 300

    def __init__(self, library, parent=None) -> None:
        super().__init__("Encounter", parent)
        self._library = library
        self._rows: list[tuple] = []   # (monster, _MonsterRowWidget, QListWidgetItem)
        self._collapsed = False
        self._expanded_width = self._DEFAULT_EXPANDED_WIDTH
        self._encounter_name = "Active Encounter"
        self._selected_monster_name: str | None = None

        self.setObjectName("encounter_sidebar")
        self.setFeatures(QDockWidget.DockWidgetFeature.DockWidgetMovable)
        # Remove default title bar — we build our own header inside _content_widget
        self.setTitleBarWidget(QWidget())

        # Build the two internal widgets
        self._content_widget = QWidget()
        self._content_widget.setObjectName("sidebar_content")
        self._handle_widget = QWidget()
        self._handle_widget.setObjectName("sidebar_handle")

        self._build_content()
        self._build_handle()

        # Wrap both in a container so QDockWidget only holds one widget
        container = QWidget()
        container_layout = QHBoxLayout(container)
        container_layout.setContentsMargins(0, 0, 0, 0)
        container_layout.setSpacing(0)
        container_layout.addWidget(self._content_widget)
        container_layout.addWidget(self._handle_widget)
        self.setWidget(container)

        # Initial state: expanded, handle hidden
        self._handle_widget.setVisible(False)
        self.setMinimumWidth(200)
        self.setMaximumWidth(self._expanded_width)

        # No forced background — inherit from system/app theme

        self._update_empty_state()

    # ------------------------------------------------------------------
    # Build UI
    # ------------------------------------------------------------------

    def _build_content(self) -> None:
        """Build the full expanded panel (header + monster list)."""
        layout = QVBoxLayout(self._content_widget)
        layout.setContentsMargins(4, 4, 4, 4)
        layout.setSpacing(4)

        # --- Header area ---
        header_container = QWidget()
        header_container.setObjectName("sidebar_header")
        header_layout = QVBoxLayout(header_container)
        header_layout.setContentsMargins(0, 0, 0, 0)
        header_layout.setSpacing(2)

        # Row 1: Encounter name + collapse button
        name_row = QHBoxLayout()
        self._name_label = QLabel(self._encounter_name)
        self._name_label.setStyleSheet("font-weight: bold; font-size: 11px;")
        self._name_label.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
        self._collapse_btn = QPushButton("Hide")
        self._collapse_btn.setFixedHeight(24)
        self._collapse_btn.setToolTip("Collapse sidebar")
        self._collapse_btn.clicked.connect(self.toggle_collapse)
        name_row.addWidget(self._name_label)
        name_row.addWidget(self._collapse_btn)
        header_layout.addLayout(name_row)

        # Row 2: Summary (creature count + XP)
        self._summary_label = QLabel("No encounter active")
        self._summary_label.setStyleSheet("color: #555; font-size: 10px;")
        header_layout.addWidget(self._summary_label)

        # Row 3: Save / Load buttons
        btn_row = QHBoxLayout()
        self._save_btn = QPushButton("Save")
        self._save_btn.setFixedHeight(24)
        self._save_btn.setToolTip("Save current encounter")
        self._save_btn.clicked.connect(self.save_btn_clicked)
        self._load_btn = QPushButton("Load")
        self._load_btn.setFixedHeight(24)
        self._load_btn.setToolTip("Load a saved encounter")
        self._load_btn.clicked.connect(self.load_btn_clicked)
        btn_row.addWidget(self._save_btn)
        btn_row.addWidget(self._load_btn)
        header_layout.addLayout(btn_row)

        layout.addWidget(header_container)

        # Separator line
        sep = QWidget()
        sep.setFixedHeight(1)
        sep.setStyleSheet("background-color: #ccc;")
        layout.addWidget(sep)

        # --- Empty state label ---
        self._empty_label = QLabel("No encounter active")
        self._empty_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._empty_label.setStyleSheet("color: #999; font-style: italic;")
        layout.addWidget(self._empty_label)

        # --- Monster list ---
        self._list_widget = QListWidget()
        self._list_widget.setDragDropMode(QAbstractItemView.DragDropMode.InternalMove)
        self._list_widget.setDefaultDropAction(Qt.DropAction.MoveAction)
        self._list_widget.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        self._list_widget.setFrameShape(QListWidget.Shape.NoFrame)
        # Disable native selection highlight and focus border — we handle row styling ourselves
        self._list_widget.setStyleSheet(
            "QListWidget::item:selected { background: transparent; }"
            " QListWidget::item:focus { outline: none; border: none; }"
        )
        self._list_widget.itemClicked.connect(self._on_single_click)
        self._list_widget.itemDoubleClicked.connect(self._on_double_click)
        self._list_widget.model().rowsMoved.connect(self._on_rows_moved)
        layout.addWidget(self._list_widget, 1)

    def _build_handle(self) -> None:
        """Build the thin 20px collapsed strip with expand button."""
        layout = QVBoxLayout(self._handle_widget)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        self._handle_btn = QPushButton("Show")
        self._handle_btn.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Expanding)
        self._handle_btn.setToolTip("Expand encounter sidebar")
        self._handle_btn.clicked.connect(self.toggle_collapse)

        layout.addWidget(self._handle_btn)
        self._handle_widget.setFixedWidth(60)

    # ------------------------------------------------------------------
    # Collapse / expand (instant toggle)
    # ------------------------------------------------------------------

    def toggle_collapse(self) -> None:
        """Instantly toggle collapse/expand of the sidebar."""
        if self._collapsed:
            self._expand()
        else:
            self._collapse()

    def _collapse(self) -> None:
        self._collapsed = True
        self.setMinimumWidth(0)
        self.setMaximumWidth(self._COLLAPSED_WIDTH)
        self._content_widget.setVisible(False)
        self._handle_widget.setVisible(True)

    def _expand(self) -> None:
        self._collapsed = False
        self._content_widget.setVisible(True)
        self._handle_widget.setVisible(False)
        self.setMinimumWidth(200)
        self.setMaximumWidth(16777215)  # QWIDGETSIZE_MAX — allows resize

    # ------------------------------------------------------------------
    # Monster list management
    # ------------------------------------------------------------------

    def _add_row(self, monster, count: int) -> None:
        """Add a new row widget to the list. Assumes monster is not already present."""
        item = QListWidgetItem()
        item.setData(Qt.ItemDataRole.UserRole, monster)

        row_widget = _MonsterRowWidget(monster, count)
        row_widget.count_changed.connect(self._on_count_changed)
        row_widget.remove_requested.connect(lambda name: self.remove_monster(name, all_of_type=True))
        row_widget.context_menu_requested.connect(self._show_context_menu)

        item.setSizeHint(row_widget.sizeHint())
        self._list_widget.addItem(item)
        self._list_widget.setItemWidget(item, row_widget)
        self._rows.append((monster, row_widget, item))

    def _remove_row(self, monster_name: str) -> None:
        """Remove the row for the given monster name entirely."""
        for i, (m, row_widget, item) in enumerate(self._rows):
            if m.name == monster_name:
                row_idx = self._list_widget.row(item)
                self._list_widget.takeItem(row_idx)
                self._rows.pop(i)
                if self._selected_monster_name == monster_name:
                    self._selected_monster_name = None
                return

    def _find_row(self, monster_name: str):
        """Return (monster, row_widget, item) for the given name, or None."""
        for entry in self._rows:
            if entry[0].name == monster_name:
                return entry
        return None

    # ------------------------------------------------------------------
    # Slots
    # ------------------------------------------------------------------

    def _on_count_changed(self, monster_name: str, new_count: int) -> None:
        """Update summary and emit encounter_changed when a count spinbox changes."""
        self._update_summary()
        self.encounter_changed.emit(self.get_members())

    def _on_single_click(self, item: QListWidgetItem) -> None:
        monster = item.data(Qt.ItemDataRole.UserRole)
        if monster is None:
            return
        # Update selection highlight
        self._set_selected_row(monster.name)
        self.monster_selected.emit(monster)

    def _on_double_click(self, item: QListWidgetItem) -> None:
        monster = item.data(Qt.ItemDataRole.UserRole)
        if monster is None:
            return
        self._set_selected_row(monster.name)
        self.monster_selected.emit(monster)
        self.switch_to_attack_roller.emit()

    def _set_selected_row(self, monster_name: str) -> None:
        self._selected_monster_name = monster_name
        for m, row_widget, item in self._rows:
            row_widget.set_selected(m.name == monster_name)

    def _on_rows_moved(self, parent, start, end, dest, row) -> None:
        """Re-sync self._rows order after drag-to-reorder, then emit encounter_changed."""
        new_rows = []
        for i in range(self._list_widget.count()):
            item = self._list_widget.item(i)
            monster = item.data(Qt.ItemDataRole.UserRole)
            if monster is None:
                continue
            entry = self._find_row_by_monster(monster)
            if entry is not None:
                new_rows.append(entry)
        self._rows = new_rows
        self.encounter_changed.emit(self.get_members())

    def _find_row_by_monster(self, monster):
        for entry in self._rows:
            if entry[0] is monster:
                return entry
        return None

    def _show_context_menu(self, monster_name: str, monster, pos) -> None:
        """Show right-click context menu at global position."""
        menu = QMenu(self)
        remove_action = menu.addAction("Remove")
        remove_all_action = menu.addAction(f"Remove all {monster_name}")
        menu.addSeparator()
        roll_action = menu.addAction("Roll Attacks")
        view_action = menu.addAction("View Stat Block")

        action = menu.exec(pos)
        if action == remove_action:
            self.remove_monster(monster_name, all_of_type=False)
        elif action == remove_all_action:
            self.remove_monster(monster_name, all_of_type=True)
        elif action == roll_action:
            self._set_selected_row(monster_name)
            self.monster_selected.emit(monster)
            self.switch_to_attack_roller.emit()
        elif action == view_action:
            self.view_stat_block_requested.emit(monster)

    # ------------------------------------------------------------------
    # Empty state management
    # ------------------------------------------------------------------

    def _update_empty_state(self) -> None:
        """Show/hide empty label and list widget based on member count."""
        has_members = len(self._rows) > 0
        self._empty_label.setVisible(not has_members)
        self._list_widget.setVisible(has_members)
        self._save_btn.setEnabled(has_members)
        # Collapse button and handle: disabled when no encounter
        self._collapse_btn.setEnabled(has_members)
        self._handle_btn.setEnabled(has_members)
        if not has_members and self._collapsed:
            # Auto-expand when encounter is cleared and sidebar is collapsed
            self._collapsed = False
            self._content_widget.setVisible(True)
            self._handle_widget.setVisible(False)
            self.setMinimumWidth(200)
            self.setMaximumWidth(16777215)

    def _update_summary(self) -> None:
        """Recompute and display total creature count + total XP in header."""
        members = self.get_members()
        if not members:
            self._summary_label.setText("No encounter active")
            return
        total_creatures = sum(count for _, count in members)
        total_xp = compute_encounter_xp(members)
        self._summary_label.setText(
            f"{total_creatures} creature{'s' if total_creatures != 1 else ''} | {total_xp:,} XP"
        )

    # ------------------------------------------------------------------
    # Public API (called by MainWindow in Plan 02)
    # ------------------------------------------------------------------

    def add_monster(self, monster, count: int = 1) -> None:
        """Add a monster or increment count if already present. Emits encounter_changed."""
        entry = self._find_row(monster.name)
        if entry is not None:
            # Increment existing
            _, row_widget, _ = entry
            new_count = row_widget.get_count() + count
            row_widget.set_count(new_count)
        else:
            self._add_row(monster, count)
            # Sort by CR descending after adding
            self._sort_by_cr()

        # Auto-expand when first monster added
        if len(self._rows) == 1 and self._collapsed:
            self._expand()

        self._update_empty_state()
        self._update_summary()
        self.encounter_changed.emit(self.get_members())

    def remove_monster(self, name: str, all_of_type: bool = False) -> None:
        """Remove one count or all of a monster type. Emits encounter_changed."""
        entry = self._find_row(name)
        if entry is None:
            return

        _, row_widget, _ = entry
        current_count = row_widget.get_count()

        if all_of_type or current_count <= 1:
            self._remove_row(name)
        else:
            row_widget.set_count(current_count - 1)

        self._update_empty_state()
        self._update_summary()
        self.encounter_changed.emit(self.get_members())

    def set_encounter(self, name: str, members: list[tuple]) -> None:
        """Bulk load an encounter (for persistence restore).

        Members are (Monster, count) tuples.
        """
        # Clear existing
        for _, row_widget, _ in list(self._rows):
            pass
        self._list_widget.clear()
        self._rows = []
        self._selected_monster_name = None

        self._encounter_name = name
        self._name_label.setText(name)

        for monster, count in members:
            self._add_row(monster, count)

        self._sort_by_cr()

        # Auto-expand if we have members
        if self._rows and self._collapsed:
            self._expand()

        self._update_empty_state()
        self._update_summary()
        self.encounter_changed.emit(self.get_members())

    def get_members(self) -> list[tuple]:
        """Return [(Monster, count)] from current list rows in display order."""
        result = []
        for i in range(self._list_widget.count()):
            item = self._list_widget.item(i)
            if item is None:
                continue
            monster = item.data(Qt.ItemDataRole.UserRole)
            if monster is None:
                continue
            entry = self._find_row_by_monster(monster)
            if entry is not None:
                _, row_widget, _ = entry
                result.append((monster, row_widget.get_count()))
        return result

    def get_encounter_name(self) -> str:
        """Return the current encounter name."""
        return self._encounter_name

    def set_encounter_name(self, name: str) -> None:
        """Set the header name label."""
        self._encounter_name = name
        self._name_label.setText(name)

    def set_expanded_width(self, width: int) -> None:
        """Restore persisted sidebar width (called on startup)."""
        if width >= 200:
            self._expanded_width = width
            if not self._collapsed:
                self.setMaximumWidth(width)

    # ------------------------------------------------------------------
    # CR sorting
    # ------------------------------------------------------------------

    def _sort_by_cr(self) -> None:
        """Sort rows by CR descending (highest CR first)."""
        if len(self._rows) < 2:
            return

        # Collect all (monster, count) in CR-descending order
        current_members = [(m, rw.get_count()) for m, rw, _ in self._rows]
        current_members.sort(key=lambda x: cr_to_float(getattr(x[0], "cr", "0")), reverse=True)

        # Rebuild the list widget with the sorted order
        self._list_widget.clear()
        self._rows = []

        for monster, count in current_members:
            item = QListWidgetItem()
            item.setData(Qt.ItemDataRole.UserRole, monster)
            row_widget = _MonsterRowWidget(monster, count)
            row_widget.count_changed.connect(self._on_count_changed)
            row_widget.remove_requested.connect(
                lambda name: self.remove_monster(name, all_of_type=True)
            )
            row_widget.context_menu_requested.connect(self._show_context_menu)
            item.setSizeHint(row_widget.sizeHint())
            self._list_widget.addItem(item)
            self._list_widget.setItemWidget(item, row_widget)
            self._rows.append((monster, row_widget, item))

        # Restore selection highlight if any
        if self._selected_monster_name:
            self._set_selected_row(self._selected_monster_name)
