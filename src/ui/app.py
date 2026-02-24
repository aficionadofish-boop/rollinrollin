"""MainWindow — root application window with tab bar."""
from __future__ import annotations

import random
from PySide6.QtWidgets import QMainWindow, QTabWidget

from src.engine.roller import Roller
from src.library.service import MonsterLibrary
from src.ui.library_tab import MonsterLibraryTab
from src.ui.attack_roller_tab import AttackRollerTab


class MainWindow(QMainWindow):
    """Main application window containing all tabs."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("RollinRollin")
        self.resize(1100, 750)

        # Shared state — one instance each for the entire session
        self._library = MonsterLibrary()
        self._roller = Roller(random.Random())  # unseeded; Phase 6 will wire seed

        # Tabs
        self._tab_widget = QTabWidget()
        self._library_tab = MonsterLibraryTab(library=self._library)
        self._attack_roller_tab = AttackRollerTab(roller=self._roller)

        self._tab_widget.addTab(self._library_tab, "Library")
        self._tab_widget.addTab(self._attack_roller_tab, "Attack Roller")
        self.setCentralWidget(self._tab_widget)

        # Cross-tab signal: Library monster selection → Attack Roller
        # Connect AFTER both tabs are constructed (Pitfall 6 in RESEARCH.md)
        self._library_tab.monster_selected.connect(
            self._attack_roller_tab.set_monster
        )
