"""MacroSandboxTab — complete Macro Sandbox tab assembling all sub-widgets.

Orchestrates the full roll flow:
  1. User types macro text in MacroEditor
  2. Roll button pressed -> preprocess_all_lines() + collect_all_queries()
  3. If queries found -> QueryPanel presented inline
  4. After queries answered (or skipped) -> execute() -> ResultPanel updated

Sidebar (MacroSidebar) allows save/load/delete of macro files from workspace.

Exports: MacroSandboxTab
"""
from __future__ import annotations

from pathlib import Path

from PySide6.QtWidgets import (
    QHBoxLayout,
    QPushButton,
    QSplitter,
    QVBoxLayout,
    QWidget,
)
from PySide6.QtCore import Qt

from src.macro.service import MacroSandboxService
from src.macro.preprocessor import CleanedMacro
from src.ui.macro_editor import MacroEditor
from src.ui.macro_query_panel import QueryPanel
from src.ui.macro_result_panel import ResultPanel
from src.ui.macro_sidebar import MacroSidebar


class MacroSandboxTab(QWidget):
    """Main Macro Sandbox tab — assembles editor, query panel, results, sidebar.

    Parameters
    ----------
    roller:
        Roller instance from MainWindow (shared for the session).
    workspace_manager:
        WorkspaceManager instance for accessing macros/ folder.
        May be None; sidebar save/load will be disabled until set.
    """

    def __init__(self, roller, workspace_manager=None, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._roller = roller
        self._workspace_manager = workspace_manager
        self._service = MacroSandboxService()
        self._cleaned: list[CleanedMacro] = []

        # Compute macros folder path from workspace manager
        self._macros_path: Path | None = (
            workspace_manager.get_subfolder("macros") if workspace_manager else None
        )

        # ------------------------------------------------------------------
        # Build layout: horizontal splitter (main content | sidebar)
        # ------------------------------------------------------------------
        outer_layout = QHBoxLayout(self)
        outer_layout.setContentsMargins(0, 0, 0, 0)

        h_splitter = QSplitter(Qt.Orientation.Horizontal)

        # ---- Main content: vertical splitter (editor top | results bottom) ----
        v_splitter = QSplitter(Qt.Orientation.Vertical)

        # Editor section
        editor_section = QWidget()
        editor_layout = QVBoxLayout(editor_section)
        editor_layout.setContentsMargins(4, 4, 4, 0)
        editor_layout.setSpacing(4)

        # Toolbar row
        toolbar_row = QHBoxLayout()
        self._roll_btn = QPushButton("Roll")
        self._roll_btn.setToolTip("Evaluate the macro expression(s)")
        self._roll_btn.clicked.connect(self._on_roll)
        toolbar_row.addWidget(self._roll_btn)

        self._clear_btn = QPushButton("Clear")
        self._clear_btn.setToolTip("Clear editor and results")
        self._clear_btn.clicked.connect(self._on_clear)
        toolbar_row.addWidget(self._clear_btn)

        toolbar_row.addStretch()
        editor_layout.addLayout(toolbar_row)

        # MacroEditor
        self._editor = MacroEditor()
        editor_layout.addWidget(self._editor)

        # QueryPanel (hidden by default)
        self._query_panel = QueryPanel()
        self._query_panel.answered.connect(self._on_queries_answered)
        editor_layout.addWidget(self._query_panel)

        v_splitter.addWidget(editor_section)

        # Results section
        self._result_panel = ResultPanel()
        v_splitter.addWidget(self._result_panel)

        v_splitter.setSizes([300, 400])

        # ---- Sidebar ----
        self._sidebar = MacroSidebar(workspace_path=self._macros_path)
        self._sidebar.macro_loaded.connect(self._on_macro_loaded)

        # Wire sidebar Save button through the tab (tab owns the editor text)
        self._sidebar._save_btn.clicked.connect(self._on_save_macro)

        # Add to horizontal splitter
        h_splitter.addWidget(v_splitter)
        h_splitter.addWidget(self._sidebar)
        h_splitter.setSizes([700, 250])
        h_splitter.setCollapsible(0, False)
        h_splitter.setCollapsible(1, True)

        outer_layout.addWidget(h_splitter)

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def set_workspace_manager(self, workspace_manager) -> None:
        """Update the workspace manager and refresh sidebar path."""
        self._workspace_manager = workspace_manager
        if workspace_manager is not None:
            self._macros_path = workspace_manager.get_subfolder("macros")
            self._sidebar.set_workspace_path(self._macros_path)

    # ------------------------------------------------------------------
    # Slots
    # ------------------------------------------------------------------

    def _on_roll(self) -> None:
        """Handle Roll button: preprocess input, then query or execute directly."""
        raw_text = self._editor.toPlainText()
        if not raw_text.strip():
            return

        self._cleaned = self._service.preprocess_all_lines(raw_text)
        queries = self._service.collect_all_queries(self._cleaned)

        if queries:
            # Show query panel; flow continues in _on_queries_answered
            self._query_panel.start(queries)
        else:
            self._execute_with_answers({})

    def _on_queries_answered(self, answers: dict) -> None:
        """Called by QueryPanel.answered signal after all queries resolved."""
        self._execute_with_answers(answers)

    def _execute_with_answers(self, answers: dict) -> None:
        """Run the service and display results."""
        result = self._service.execute(self._cleaned, answers, self._roller)
        self._result_panel.add_roll_result(result)

    def _on_clear(self) -> None:
        """Clear editor, results, and query panel."""
        self._editor.clear()
        self._result_panel.clear()
        self._query_panel.reset()

    def _on_macro_loaded(self, text: str) -> None:
        """Load macro text from sidebar into the editor."""
        self._editor.setPlainText(text)

    def _on_save_macro(self) -> None:
        """Save current editor text via sidebar (sidebar shows name prompt)."""
        self._sidebar.save_macro(self._editor.toPlainText())
