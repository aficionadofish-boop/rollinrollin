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
)
from PySide6.QtCore import Qt

from src.library.service import MonsterLibrary
from src.parser.statblock_parser import parse_file
from src.parser.models import ImportResult
from src.ui.monster_table import MonsterTableModel
from src.ui.monster_filter import MonsterFilterProxyModel
from src.ui.monster_detail import MonsterDetailPanel
from src.ui.import_log import ImportLogPanel


class MonsterLibraryTab(QWidget):
    """Complete Monster Library tab widget.

    Args:
        library: Shared MonsterLibrary instance (owned by the caller / main window).
        parent:  Optional parent QWidget.
    """

    def __init__(self, library: MonsterLibrary, parent=None) -> None:
        super().__init__(parent)
        self._library = library
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
        self._table.horizontalHeader().setSortIndicatorShown(True)
        self._table.horizontalHeader().setStretchLastSection(False)
        self._table.horizontalHeader().setSectionResizeMode(
            0, QHeaderView.ResizeMode.Stretch
        )
        self._table.setEditTriggers(
            QAbstractItemView.EditTrigger.NoEditTriggers
        )
        self._table.verticalHeader().setVisible(False)

        left_widget = QWidget()
        left_layout = QVBoxLayout(left_widget)
        left_layout.setContentsMargins(0, 0, 0, 0)
        left_layout.addWidget(self._table)

        # ---- Right panel: detail + log ----
        self._detail_panel = MonsterDetailPanel(parent=self)
        self._log_panel = ImportLogPanel(parent=self)
        self._log_panel.setMaximumHeight(180)

        right_widget = QWidget()
        right_layout = QVBoxLayout(right_widget)
        right_layout.setContentsMargins(0, 0, 0, 0)
        right_layout.addWidget(self._detail_panel, 1)
        right_layout.addWidget(self._log_panel)

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

    # ------------------------------------------------------------------
    # Import actions
    # ------------------------------------------------------------------

    def _import_files(self) -> None:
        files, _ = QFileDialog.getOpenFileNames(
            self, "Import Monster Files", "", "Markdown Files (*.md);;All Files (*)"
        )
        if not files:
            return
        for file_path in files:
            self._process_import_file(Path(file_path))
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
        for file_path in md_files:
            self._process_import_file(file_path)
        self._refresh_model()
        self._refresh_type_combo()

    def _process_import_file(self, path: Path) -> None:
        """Parse one Markdown file, handle duplicates, add to library, log result."""
        result = parse_file(path)
        for monster in result.monsters:
            if self._library.has_name(monster.name):
                action = self._ask_duplicate_action(monster.name)
                if action == "skip":
                    continue
                elif action == "replace":
                    self._library.replace(monster)
                else:  # 'keep'
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
        """Show Keep Both / Replace / Skip dialog for a duplicate monster name.

        Returns one of: 'keep', 'replace', 'skip'
        """
        box = QMessageBox(self)
        box.setWindowTitle("Duplicate Monster")
        box.setText(f'"{monster_name}" already exists in the library.')
        box.setInformativeText("What would you like to do?")
        keep_btn = box.addButton("Keep Both", QMessageBox.ButtonRole.AcceptRole)
        replace_btn = box.addButton("Replace", QMessageBox.ButtonRole.DestructiveRole)
        box.addButton("Skip", QMessageBox.ButtonRole.RejectRole)
        box.exec()
        clicked = box.clickedButton()
        if clicked == keep_btn:
            return "keep"
        if clicked == replace_btn:
            return "replace"
        return "skip"

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
