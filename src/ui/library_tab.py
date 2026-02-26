"""MonsterLibraryTab — main library tab widget integrating import, search, filter, and detail.

Assembles:
  - Import toolbar (File/Folder menu)
  - Search bar + Type combo + Incomplete/Complete filter combo
  - Sortable monster table (MonsterTableModel + MonsterFilterProxyModel)
  - Monster detail panel (MonsterDetailPanel)
  - Import log panel (ImportLogPanel)

The tab holds a shared MonsterLibrary instance passed from the application window.
"""
from __future__ import annotations

from pathlib import Path

from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QSplitter,
    QTableView,
    QLineEdit,
    QComboBox,
    QPushButton,
    QMenu,
    QLabel,
    QFileDialog,
    QMessageBox,
    QHeaderView,
    QAbstractItemView,
    QDialog,
)
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QDragEnterEvent, QDragLeaveEvent, QDropEvent

from src.library.service import MonsterLibrary
from src.parser.statblock_parser import parse_file
from src.parser.models import ImportResult
from src.ui.monster_table import MonsterTableModel
from src.ui.monster_filter import MonsterFilterProxyModel
from src.ui.monster_detail import MonsterDetailPanel
from src.ui.import_log import ImportLogPanel
from src.ui.monster_editor import MonsterEditorDialog


class EncounterDropZone(QLabel):
    """Drop target on the Library tab that adds a monster to the current encounter.

    Accepts ``application/x-monster-name`` drags. Emits ``monster_dropped``
    with the resolved Monster when a valid drag is released.
    """

    monster_dropped = Signal(object)  # Monster

    _STYLE_IDLE = (
        "border: 2px dashed #888; border-radius: 4px; "
        "color: #888; padding: 4px; font-size: 10px;"
    )
    _STYLE_HOVER = (
        "border: 2px dashed #4a9; border-radius: 4px; "
        "color: #4a9; padding: 4px; font-size: 10px;"
    )

    def __init__(self, library, parent=None) -> None:
        super().__init__(parent)
        self._library = library
        self.setAcceptDrops(True)
        self.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.setText("Drop monster here\nto add to encounter")
        self.setWordWrap(True)
        self.setStyleSheet(self._STYLE_IDLE)

    def dragEnterEvent(self, event: QDragEnterEvent) -> None:
        if event.mimeData().hasFormat("application/x-monster-name"):
            self.setStyleSheet(self._STYLE_HOVER)
            event.acceptProposedAction()
        else:
            event.ignore()

    def dragLeaveEvent(self, event: QDragLeaveEvent) -> None:
        self.setStyleSheet(self._STYLE_IDLE)

    def dropEvent(self, event: QDropEvent) -> None:
        self.setStyleSheet(self._STYLE_IDLE)
        raw = event.mimeData().data("application/x-monster-name")
        name = bytes(raw).decode("utf-8")
        if self._library is not None and self._library.has_name(name):
            self.monster_dropped.emit(self._library.get_by_name(name))
        event.acceptProposedAction()


class MonsterLibraryTab(QWidget):
    """Complete Monster Library tab widget.

    Args:
        library:     Shared MonsterLibrary instance (owned by the caller / main window).
        persistence: Optional PersistenceService for modified monster tracking.
        parent:      Optional parent QWidget.
    """

    monster_selected = Signal(object)         # emitted when user selects a row
    monster_added_to_encounter = Signal(object)  # emitted when monster dropped onto drop zone

    def __init__(self, library: MonsterLibrary, persistence=None, parent=None) -> None:
        super().__init__(parent)
        self._library = library
        self._persistence = persistence
        self._setup_ui()
        self._connect_signals()

    # ------------------------------------------------------------------
    # UI construction
    # ------------------------------------------------------------------

    def _setup_ui(self) -> None:
        main_layout = QVBoxLayout(self)

        # ---- Toolbar row ----
        toolbar = QHBoxLayout()

        # Import button with drop-down menu
        import_btn = QPushButton("Import…")
        import_menu = QMenu(import_btn)
        import_menu.addAction("File(s)…", self._import_files)
        import_menu.addAction("Folder…", self._import_folder)
        import_btn.setMenu(import_menu)
        toolbar.addWidget(import_btn)

        toolbar.addWidget(QLabel("Search:"))
        self._search_edit = QLineEdit()
        self._search_edit.setPlaceholderText("Search name, type, CR…")
        toolbar.addWidget(self._search_edit)

        toolbar.addWidget(QLabel("Type:"))
        self._type_combo = QComboBox()
        self._type_combo.addItem("All Types")
        self._type_combo.setSizeAdjustPolicy(QComboBox.SizeAdjustPolicy.AdjustToContents)
        self._type_combo.setMinimumWidth(120)
        toolbar.addWidget(self._type_combo)

        self._incomplete_check = QComboBox()
        self._incomplete_check.addItems(["All", "Incomplete only", "Complete only"])
        toolbar.addWidget(self._incomplete_check)

        toolbar.addStretch()
        main_layout.addLayout(toolbar)

        # ---- Left panel: monster table ----
        self._model = MonsterTableModel(parent=self)
        self._proxy = MonsterFilterProxyModel(parent=self)
        self._proxy.setSourceModel(self._model)
        self._proxy.setSortRole(Qt.UserRole)

        self._table = QTableView()
        self._table.setModel(self._proxy)
        self._table.setSortingEnabled(True)
        self._table.setSelectionBehavior(
            QAbstractItemView.SelectionBehavior.SelectRows
        )
        self._table.setSelectionMode(
            QAbstractItemView.SelectionMode.SingleSelection
        )
        header = self._table.horizontalHeader()
        header.setSortIndicatorShown(True)
        header.setStretchLastSection(False)
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)  # Name
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)  # CR
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.Stretch)            # Type stretches
        header.setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents)  # badge
        self._table.setEditTriggers(
            QAbstractItemView.EditTrigger.NoEditTriggers
        )
        self._table.verticalHeader().setVisible(False)
        self._table.setDragEnabled(True)
        self._table.setDefaultDropAction(Qt.DropAction.CopyAction)

        left_widget = QWidget()
        left_layout = QVBoxLayout(left_widget)
        left_layout.setContentsMargins(0, 0, 0, 0)
        left_layout.addWidget(self._table)

        # ---- Right panel: detail + (drop zone | log) ----
        self._detail_panel = MonsterDetailPanel(parent=self)

        self._drop_zone = EncounterDropZone(library=self._library, parent=self)
        self._drop_zone.monster_dropped.connect(self.monster_added_to_encounter)

        self._log_panel = ImportLogPanel(parent=self)

        # Bottom strip: drop zone on the left, import log on the right
        bottom_splitter = QSplitter(Qt.Orientation.Horizontal)
        bottom_splitter.addWidget(self._drop_zone)
        bottom_splitter.addWidget(self._log_panel)
        bottom_splitter.setStretchFactor(0, 1)
        bottom_splitter.setStretchFactor(1, 1)
        bottom_splitter.setMaximumHeight(180)

        right_widget = QWidget()
        right_layout = QVBoxLayout(right_widget)
        right_layout.setContentsMargins(0, 0, 0, 0)
        right_layout.addWidget(self._detail_panel, 1)
        right_layout.addWidget(bottom_splitter)

        # ---- Splitter ----
        splitter = QSplitter(Qt.Orientation.Horizontal)
        splitter.addWidget(left_widget)
        splitter.addWidget(right_widget)
        splitter.setStretchFactor(0, 2)
        splitter.setStretchFactor(1, 3)

        main_layout.addWidget(splitter, 1)

    # ------------------------------------------------------------------
    # Signal connections
    # ------------------------------------------------------------------

    def _connect_signals(self) -> None:
        self._search_edit.textChanged.connect(self._proxy.setFilterFixedString)
        self._type_combo.currentTextChanged.connect(self._on_type_filter_changed)
        self._incomplete_check.currentIndexChanged.connect(
            self._on_incomplete_filter_changed
        )
        self._table.selectionModel().selectionChanged.connect(
            self._on_selection_changed
        )
        self._detail_panel.edit_requested.connect(self._on_edit_monster)

    # ------------------------------------------------------------------
    # Slot handlers
    # ------------------------------------------------------------------

    def _on_type_filter_changed(self, text: str) -> None:
        if text == "All Types":
            self._proxy.set_type_filter("")
        else:
            self._proxy.set_type_filter(text)

    def _on_incomplete_filter_changed(self, index: int) -> None:
        if index == 0:  # All
            self._proxy.set_incomplete_only(False)
            self._proxy.set_complete_only(False)
        elif index == 1:  # Incomplete only
            self._proxy.set_incomplete_only(True)
        elif index == 2:  # Complete only
            self._proxy.set_complete_only(True)

    def _on_selection_changed(self, selected, deselected) -> None:
        indexes = selected.indexes()
        if not indexes:
            self._detail_panel.clear()
            return
        proxy_index = indexes[0]
        source_index = self._proxy.mapToSource(proxy_index)
        monster = self._model.monster_at(source_index.row())
        self._detail_panel.show_monster(monster)
        self.monster_selected.emit(monster)   # NEW — cross-tab signal

    def select_monster_by_name(self, name: str) -> None:
        """Programmatically select a monster row in the table by name."""
        for source_row in range(self._model.rowCount()):
            m = self._model.monster_at(source_row)
            if m.name == name:
                source_index = self._model.index(source_row, 0)
                proxy_index = self._proxy.mapFromSource(source_index)
                if proxy_index.isValid():
                    self._table.selectRow(proxy_index.row())
                    self._table.scrollTo(proxy_index)
                return

    def _on_edit_monster(self, monster) -> None:
        """Open MonsterEditorDialog for the given monster (modal).

        Passes library and persistence so the editor can save directly.
        Connects the monster_saved signal before exec() so it fires before
        dialog teardown.
        """
        dialog = MonsterEditorDialog(
            monster,
            parent=self.window(),
            library=self._library,
            persistence=self._persistence,
        )
        dialog.monster_saved.connect(self._on_monster_saved)
        dialog.exec()

    def _on_monster_saved(self, monster) -> None:
        """Refresh the table after a monster is saved in the editor."""
        self._model.reset_monsters(self._library.all())
        self._model.set_modified_names(self._get_modified_names())
        self._refresh_type_combo()

    def _get_modified_names(self) -> set[str]:
        """Return the set of monster names that have persisted modifications."""
        if self._persistence is None:
            return set()
        return set(self._persistence.load_modified_monsters().keys())

    # ------------------------------------------------------------------
    # Import actions
    # ------------------------------------------------------------------

    def _import_files(self) -> None:
        files, _ = QFileDialog.getOpenFileNames(
            self, "Import Monster Files", "", "Markdown Files (*.md);;All Files (*)"
        )
        if not files:
            return
        # apply_to_all is a single-element list so _process_import_file can mutate it.
        # Reset to None at the start of each import batch.
        apply_to_all: list[str | None] = [None]
        for file_path in files:
            self._process_import_file(Path(file_path), apply_to_all)
        self._refresh_model()
        self._refresh_type_combo()

    def _import_folder(self) -> None:
        folder = QFileDialog.getExistingDirectory(
            self,
            "Import Monsters from Folder",
            "",
            QFileDialog.Option.ShowDirsOnly,
        )
        if not folder:
            return
        md_files = list(Path(folder).glob("*.md"))
        if not md_files:
            self._log_panel.log(f"No .md files found in {Path(folder).name}/")
            return
        # Fresh apply_to_all state for each folder import batch.
        apply_to_all: list[str | None] = [None]
        for file_path in md_files:
            self._process_import_file(file_path, apply_to_all)
        self._refresh_model()
        self._refresh_type_combo()

    def _process_import_file(self, path: Path, apply_to_all: list[str | None] | None = None) -> None:
        """Parse one Markdown file, handle duplicates, add to library, log result.

        Args:
            path:          Path to the Markdown file to parse.
            apply_to_all:  Single-element mutable list used to propagate an
                           "Apply to All" duplicate decision across multiple files
                           in the same import batch.  Pass None when importing a
                           single file outside of a batch.
        """
        if apply_to_all is None:
            apply_to_all = [None]

        result = parse_file(path)
        for monster in result.monsters:
            if self._library.has_name(monster.name):
                # Use the batch-wide decision if already set, otherwise ask.
                if apply_to_all[0] is not None:
                    action = apply_to_all[0]
                else:
                    action = self._ask_duplicate_action(monster.name)
                    # Propagate "All" decisions to the rest of this batch.
                    if action in ("keep_all", "replace_all", "skip_all"):
                        apply_to_all[0] = action

                # Normalise "all" variants to their base action for execution.
                base_action = action.replace("_all", "")
                if base_action == "skip":
                    continue
                elif base_action == "replace":
                    self._library.replace(monster)
                else:  # 'keep' / 'keep_all'
                    self._library.add(monster)
            else:
                self._library.add(monster)

        import_result = ImportResult.from_parse_result(str(path.name), result)
        self._log_panel.log_result(
            import_result.filename,
            import_result.success_count,
            import_result.incomplete_count,
            import_result.failures,
        )
        for warning in result.warnings:
            self._log_panel.log(f"  WARN: {warning}")

    def _ask_duplicate_action(self, monster_name: str) -> str:
        """Show duplicate-resolution dialog for a monster that already exists.

        Provides per-item buttons (Keep Both, Replace, Skip) and batch buttons
        (Keep All, Replace All, Skip All) that apply the choice to all remaining
        duplicates in the current import batch without further prompting.

        Returns one of:
            'keep_both'   — keep both entries for this monster only
            'replace'     — replace the existing entry for this monster only
            'skip'        — skip this monster only
            'keep_all'    — keep both for this and all subsequent duplicates
            'replace_all' — replace for this and all subsequent duplicates
            'skip_all'    — skip this and all subsequent duplicates
        """
        box = QMessageBox(self)
        box.setWindowTitle("Duplicate Monster")
        box.setText(f'"{monster_name}" already exists in the library.')
        box.setInformativeText(
            "Choose an action for this monster, or use an 'All' option to apply "
            "the same choice to all remaining duplicates in this import."
        )

        keep_btn = box.addButton("Keep Both", QMessageBox.ButtonRole.AcceptRole)
        replace_btn = box.addButton("Replace", QMessageBox.ButtonRole.DestructiveRole)
        skip_btn = box.addButton("Skip", QMessageBox.ButtonRole.RejectRole)
        keep_all_btn = box.addButton("Keep All", QMessageBox.ButtonRole.AcceptRole)
        replace_all_btn = box.addButton("Replace All", QMessageBox.ButtonRole.DestructiveRole)
        skip_all_btn = box.addButton("Skip All", QMessageBox.ButtonRole.RejectRole)

        box.exec()
        clicked = box.clickedButton()

        if clicked == keep_btn:
            return "keep_both"
        if clicked == replace_btn:
            return "replace"
        if clicked == skip_btn:
            return "skip"
        if clicked == keep_all_btn:
            return "keep_all"
        if clicked == replace_all_btn:
            return "replace_all"
        # Default: skip_all (covers skip_all_btn and any unexpected close)
        return "skip_all"

    # ------------------------------------------------------------------
    # Model refresh helpers
    # ------------------------------------------------------------------

    def _refresh_model(self) -> None:
        """Push current library contents into the table model."""
        self._model.reset_monsters(self._library.all())

    def _refresh_type_combo(self) -> None:
        """Repopulate the Type dropdown from the current library's creature types."""
        current = self._type_combo.currentText()
        self._type_combo.blockSignals(True)
        self._type_combo.clear()
        self._type_combo.addItem("All Types")
        for t in self._library.creature_types():
            self._type_combo.addItem(t)
        # Restore previous selection if it still exists
        idx = self._type_combo.findText(current)
        if idx >= 0:
            self._type_combo.setCurrentIndex(idx)
        self._type_combo.blockSignals(False)
