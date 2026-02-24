"""macro_sidebar.py — Saved macro list sidebar with save/load/delete controls.

MacroSidebar lists .md files from the workspace macros/ folder.  Users can:
  - Double-click an item to load it (macro_loaded signal emitted)
  - Click Save to save the current editor text (name prompt via QInputDialog)
  - Click Delete to remove the selected macro (confirmation via QMessageBox)

File persistence uses Path.read_text / Path.write_text; no Qt file dialogs.
"""
from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import Signal
from PySide6.QtGui import QFont
from PySide6.QtWidgets import (
    QInputDialog,
    QLabel,
    QListWidget,
    QListWidgetItem,
    QMenu,
    QMessageBox,
    QPushButton,
    QVBoxLayout,
    QHBoxLayout,
    QWidget,
)


class MacroSidebar(QWidget):
    """Right-side panel listing saved macros from the workspace macros/ folder.

    Signals
    -------
    macro_loaded(str) — emits the macro text content when user loads a saved macro
    """

    macro_loaded = Signal(str)

    def __init__(
        self,
        workspace_path: Path | None = None,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self._workspace_path: Path | None = workspace_path

        root = QVBoxLayout(self)
        root.setContentsMargins(4, 4, 4, 4)
        root.setSpacing(6)

        # Header
        header = QLabel("Saved Macros")
        header_font = QFont(header.font())
        header_font.setBold(True)
        header.setFont(header_font)
        root.addWidget(header)

        # Macro list
        self._list_widget = QListWidget()
        self._list_widget.setToolTip("Double-click to load a macro")
        self._list_widget.itemDoubleClicked.connect(self._on_load)
        self._list_widget.setContextMenuPolicy(
            self._list_widget.contextMenuPolicy().CustomContextMenu
        )
        self._list_widget.customContextMenuRequested.connect(self._show_context_menu)
        root.addWidget(self._list_widget)

        # Button row
        btn_row = QHBoxLayout()
        btn_row.setSpacing(4)

        self._save_btn = QPushButton("Save")
        self._save_btn.setToolTip("Save current macro text to file")
        self._save_btn.clicked.connect(self._on_save_clicked)
        btn_row.addWidget(self._save_btn)

        self._delete_btn = QPushButton("Delete")
        self._delete_btn.setToolTip("Delete selected macro")
        self._delete_btn.clicked.connect(self._on_delete)
        btn_row.addWidget(self._delete_btn)

        root.addLayout(btn_row)

        if workspace_path is not None:
            self._refresh_list()

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def set_workspace_path(self, path: Path) -> None:
        """Update the workspace path and refresh the macro list."""
        self._workspace_path = path
        self._refresh_list()

    def save_macro(self, macro_text: str) -> None:
        """Prompt for a name and write macro_text to workspace macros/ folder.

        Called by MacroSandboxTab when the Save button is clicked.
        """
        if self._workspace_path is None:
            QMessageBox.warning(
                self,
                "No Workspace",
                "Select a workspace folder first.",
            )
            return

        name, ok = QInputDialog.getText(self, "Save Macro", "Macro name:")
        if not ok or not name.strip():
            return

        safe_name = name.strip().replace(" ", "_")
        target = self._workspace_path / f"{safe_name}.md"
        target.write_text(macro_text, encoding="utf-8")
        self._refresh_list()

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    def _refresh_list(self) -> None:
        """Reload the list from the workspace macros/ folder."""
        self._list_widget.clear()
        if self._workspace_path is None or not self._workspace_path.exists():
            return
        for file in sorted(self._workspace_path.glob("*.md")):
            self._list_widget.addItem(file.stem)

    def _on_load(self, item: QListWidgetItem | None = None) -> None:
        """Load the selected macro and emit macro_loaded."""
        if item is None:
            item = self._list_widget.currentItem()
        if item is None:
            return
        if self._workspace_path is None:
            return
        path = self._workspace_path / f"{item.text()}.md"
        if path.exists():
            self.macro_loaded.emit(path.read_text(encoding="utf-8"))

    def _on_delete(self) -> None:
        """Delete the selected macro after confirmation."""
        item = self._list_widget.currentItem()
        if item is None:
            return
        reply = QMessageBox.question(
            self,
            "Delete Macro",
            f"Delete macro '{item.text()}'?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )
        if reply == QMessageBox.StandardButton.Yes:
            if self._workspace_path is not None:
                target = self._workspace_path / f"{item.text()}.md"
                if target.exists():
                    target.unlink()
            self._refresh_list()

    def _on_save_clicked(self) -> None:
        """Internal: Save button clicked — signal is handled by the parent tab.

        The tab calls sidebar.save_macro(editor.toPlainText()) directly.
        This slot exists as a placeholder so the button is visually connected.
        Note: MacroSandboxTab connects the Save button's clicked signal to its
        own slot, NOT to this method — see MacroSandboxTab.__init__.
        """
        # MacroSandboxTab wires: sidebar._save_btn.clicked -> tab._on_save_macro
        # This method is intentionally empty; the tab owns the wiring.
        pass

    def _show_context_menu(self, pos) -> None:
        """Right-click context menu with Delete option."""
        item = self._list_widget.itemAt(pos)
        if item is None:
            return
        menu = QMenu(self)
        delete_action = menu.addAction("Delete")
        action = menu.exec(self._list_widget.viewport().mapToGlobal(pos))
        if action == delete_action:
            self._on_delete()
