"""MainWindow — root application window with tab bar."""
from __future__ import annotations

import random
from pathlib import Path

from PySide6.QtWidgets import QMainWindow, QTabWidget

from src.engine.roller import Roller
from src.library.service import MonsterLibrary
from src.ui.library_tab import MonsterLibraryTab
from src.ui.attack_roller_tab import AttackRollerTab
from src.ui.encounters_tab import EncountersTab
from src.ui.macro_sandbox_tab import MacroSandboxTab
from src.workspace.setup import WorkspaceManager


class MainWindow(QMainWindow):
    """Main application window containing all tabs."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("RollinRollin")
        self.resize(1100, 750)

        # Shared state — one instance each for the entire session
        self._library = MonsterLibrary()
        self._roller = Roller(random.Random())  # unseeded; Phase 6 will wire seed
        self._workspace_manager = WorkspaceManager(Path.home() / "RollinRollin")
        self._workspace_manager.initialize()

        # Tabs
        self._tab_widget = QTabWidget()
        self._library_tab = MonsterLibraryTab(library=self._library)
        self._attack_roller_tab = AttackRollerTab(roller=self._roller)
        self._encounters_tab = EncountersTab(
            library=self._library,
            roller=self._roller,
        )
        self._macro_tab = MacroSandboxTab(
            roller=self._roller,
            workspace_manager=self._workspace_manager,
        )

        self._tab_widget.addTab(self._library_tab, "Library")
        self._tab_widget.addTab(self._attack_roller_tab, "Attack Roller")
        self._tab_widget.addTab(self._encounters_tab, "Encounters && Saves")
        self._tab_widget.addTab(self._macro_tab, "Macro Sandbox")
        self.setCentralWidget(self._tab_widget)

        # Cross-tab signal: Library monster selection → Attack Roller
        # Connect AFTER both tabs are constructed (Pitfall 6 in RESEARCH.md)
        self._library_tab.monster_selected.connect(
            self._attack_roller_tab.set_monster
        )

        # Cross-tab signal: Library drop zone → Encounters tab member list
        self._library_tab.monster_added_to_encounter.connect(
            self._encounters_tab.add_monster_to_encounter
        )
