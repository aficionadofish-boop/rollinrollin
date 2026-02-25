"""MainWindow — root application window with tab bar."""
from __future__ import annotations

import random
from pathlib import Path

from PySide6.QtCore import QTimer
from PySide6.QtWidgets import QMainWindow, QTabWidget, QMessageBox

from src.domain.models import MonsterModification
from src.engine.roller import Roller
from src.library.service import MonsterLibrary
from src.persistence.service import PersistenceService
from src.settings.service import SettingsService
from src.settings.models import AppSettings
from src.ui.library_tab import MonsterLibraryTab
from src.ui.attack_roller_tab import AttackRollerTab
from src.ui.encounters_tab import EncountersTab
from src.ui.macro_sandbox_tab import MacroSandboxTab
from src.ui.settings_tab import SettingsTab
from src.workspace.setup import WorkspaceManager, resolve_workspace_root


class MainWindow(QMainWindow):
    """Main application window containing all tabs."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("RollinRollin")
        self.resize(1100, 750)

        # Shared state — one instance each for the entire session
        self._library = MonsterLibrary()
        self._roller = Roller(random.Random())  # unseeded; seeding handled via settings
        self._workspace_manager = WorkspaceManager(resolve_workspace_root())
        self._workspace_manager.initialize()

        # Settings service: load persisted settings before constructing tabs
        self._settings_service = SettingsService(self._workspace_manager.root)
        self._current_settings = self._settings_service.load()

        # Persistence service: load session data on startup
        self._persistence = PersistenceService(self._workspace_manager.root)
        self._load_persisted_data()

        # Tabs
        self._tab_widget = QTabWidget()
        self._library_tab = MonsterLibraryTab(library=self._library, persistence=self._persistence)
        self._attack_roller_tab = AttackRollerTab(roller=self._roller)
        self._encounters_tab = EncountersTab(
            library=self._library,
            roller=self._roller,
        )
        self._macro_tab = MacroSandboxTab(
            roller=self._roller,
            workspace_manager=self._workspace_manager,
        )
        self._settings_tab = SettingsTab()

        self._tab_widget.addTab(self._library_tab, "Library")
        self._tab_widget.addTab(self._attack_roller_tab, "Attack Roller")
        self._tab_widget.addTab(self._encounters_tab, "Encounters && Saves")
        self._tab_widget.addTab(self._macro_tab, "Macro Sandbox")
        self._tab_widget.addTab(self._settings_tab, "Settings")
        self.setCentralWidget(self._tab_widget)

        # Cross-tab signal: Library drop zone → Encounters tab member list
        self._library_tab.monster_added_to_encounter.connect(
            self._encounters_tab.add_monster_to_encounter
        )

        # Cross-tab signal: Encounter member list changes → Attack Roller
        self._encounters_tab.encounter_members_changed.connect(
            self._attack_roller_tab.set_creatures
        )

        # Settings tab signals
        self._settings_tab.settings_saved.connect(self._on_settings_saved)

        # Flush signals from Settings tab → PersistenceService
        self._settings_tab.flush_requested.connect(self._on_flush_category)
        self._settings_tab.clear_all_requested.connect(self._on_clear_all)

        # Initialize settings tab with loaded settings
        self._settings_tab.apply_settings(self._current_settings)

        # Apply loaded settings to all tabs and shared roller
        # Called AFTER all tabs are fully constructed
        self._apply_settings(self._current_settings)

        # Apply persisted monster modifications to library and populate badge set
        self._apply_persisted_modifications()

        # Unsaved-changes guard — track Settings tab index and previous tab
        self._settings_tab_index = self._tab_widget.indexOf(self._settings_tab)
        self._prev_tab_index = self._tab_widget.currentIndex()
        self._tab_widget.currentChanged.connect(self._on_tab_changed)

        # Auto-save timer: fires every 30 seconds
        self._autosave_timer = QTimer(self)
        self._autosave_timer.setInterval(30_000)  # 30 seconds
        self._autosave_timer.timeout.connect(self._autosave)
        self._autosave_timer.start()

        # Status bar initial message
        self.statusBar().showMessage("Ready")

    # ------------------------------------------------------------------
    # Settings wiring
    # ------------------------------------------------------------------

    def _on_settings_saved(self, settings: AppSettings) -> None:
        """Called when user clicks Save in Settings tab."""
        self._settings_service.save(settings)
        self._current_settings = settings
        self._apply_settings(settings)

    def _apply_settings(self, settings: AppSettings) -> None:
        """Apply loaded/saved settings to all tabs and the shared roller."""
        # Re-seed or un-seed the shared RNG (never recreate the Roller instance)
        if settings.seeded_rng_enabled and settings.seed_value is not None:
            self._roller._rng.seed(settings.seed_value)
        else:
            self._roller._rng.seed(None)

        # Apply defaults to tabs
        self._attack_roller_tab.apply_defaults(settings)
        self._encounters_tab.apply_defaults(settings)

        # Update seeded badge on output panels
        seeded = settings.seeded_rng_enabled and settings.seed_value is not None
        self._attack_roller_tab.set_seeded_mode(seeded)
        self._macro_tab._result_panel.set_seeded_mode(seeded)

    # ------------------------------------------------------------------
    # Tab change guard (unsaved settings changes)
    # ------------------------------------------------------------------

    def _on_tab_changed(self, new_index: int) -> None:
        """Guard: prompt to save/discard when leaving Settings tab with unsaved changes."""
        if (self._prev_tab_index == self._settings_tab_index
                and self._settings_tab.is_dirty()):
            reply = QMessageBox.question(
                self,
                "Unsaved Settings",
                "You have unsaved settings changes.\nSave or discard?",
                QMessageBox.StandardButton.Save | QMessageBox.StandardButton.Discard,
            )
            if reply == QMessageBox.StandardButton.Save:
                self._settings_tab.save()
                # settings_saved signal will trigger _on_settings_saved
            else:
                self._settings_tab.discard()
        self._prev_tab_index = new_index

        # Refresh flush counts when switching TO the settings tab
        if new_index == self._settings_tab_index:
            self._refresh_flush_counts()

    # ------------------------------------------------------------------
    # Persistence lifecycle
    # ------------------------------------------------------------------

    def _load_persisted_data(self) -> None:
        """Load all persistence categories from disk into instance variables."""
        self._persisted_monsters = self._persistence.load_loaded_monsters()
        self._persisted_encounters = self._persistence.load_encounters()
        self._persisted_modifications = self._persistence.load_modified_monsters()
        self._persisted_macros = self._persistence.load_macros()

    def _apply_persisted_modifications(self) -> None:
        """Apply persisted MonsterModifications to the library on startup.

        For each key in _persisted_modifications:
          - Reconstruct MonsterModification via from_dict()
          - If the base monster exists in the library, apply overrides to
            produce a modified Monster and replace it (or add it as new for
            save-as-copy entries with a custom_name different from base_name).
          - Populate the library tab's modified names badge set.
        """
        import copy as _copy
        import dataclasses as _dc

        for key, mod_dict in self._persisted_modifications.items():
            try:
                mod = MonsterModification.from_dict(mod_dict)
            except Exception:
                continue

            base_name = mod.base_name
            if not self._library.has_name(base_name):
                continue  # Base monster not loaded — skip

            base_monster = self._library.get_by_name(base_name)
            modified = _copy.deepcopy(base_monster)

            # Apply field overrides
            if mod.ability_scores:
                for ability, score in mod.ability_scores.items():
                    modified.ability_scores[ability] = score
            if mod.saves:
                modified.saves = dict(mod.saves)
            if mod.skills:
                modified.skills = dict(mod.skills)
            if mod.hp is not None:
                modified.hp = mod.hp
            if mod.ac is not None:
                modified.ac = mod.ac
            if mod.cr is not None:
                modified.cr = mod.cr
            if mod.size is not None:
                modified.size = mod.size
            if mod.buffs:
                modified.buffs = list(mod.buffs)

            # Apply action overrides
            if mod.actions:
                from src.domain.models import Action, DamagePart
                reconstructed_actions = []
                for a_dict in mod.actions:
                    damage_parts = [
                        DamagePart(
                            dice_expr=dp.get("dice_expr", "1d6"),
                            damage_type=dp.get("damage_type", "bludgeoning"),
                            raw_text=dp.get("raw_text", ""),
                        )
                        for dp in a_dict.get("damage_parts", [])
                    ]
                    reconstructed_actions.append(Action(
                        name=a_dict.get("name", ""),
                        to_hit_bonus=a_dict.get("to_hit_bonus"),
                        damage_parts=damage_parts,
                        raw_text=a_dict.get("raw_text", ""),
                        is_parsed=a_dict.get("is_parsed", True),
                        damage_bonus=a_dict.get("damage_bonus"),
                        is_equipment_generated=a_dict.get("is_equipment_generated", False),
                    ))
                modified.actions = reconstructed_actions

            # For save-as-copy: custom_name differs from base_name → add as new
            if mod.custom_name and mod.custom_name != base_name:
                modified.name = mod.custom_name
                if not self._library.has_name(mod.custom_name):
                    self._library.add(modified)
                else:
                    self._library.replace(modified)
            else:
                # Override: replace the base monster
                self._library.replace(modified)

        # Populate modified badge set in library tab's table model
        modified_names = set(self._persisted_modifications.keys())
        self._library_tab._model.set_modified_names(modified_names)

    def _save_persisted_data(self) -> None:
        """Save all persistence categories to disk."""
        self._persistence.save_loaded_monsters(self._persisted_monsters)
        self._persistence.save_encounters(self._persisted_encounters)
        self._persistence.save_modified_monsters(self._persisted_modifications)
        self._persistence.save_macros(self._persisted_macros)

    def _autosave(self) -> None:
        """Timer callback: save all persistence data and briefly show status."""
        self._save_persisted_data()
        self.statusBar().showMessage("Saved", 2000)

    def closeEvent(self, event) -> None:
        """Save data and handle unsaved settings before closing."""
        # Guard: if Settings tab is dirty, prompt save/discard
        if self._settings_tab.is_dirty():
            reply = QMessageBox.question(
                self,
                "Unsaved Settings",
                "You have unsaved settings changes.\nSave or discard?",
                QMessageBox.StandardButton.Save | QMessageBox.StandardButton.Discard,
            )
            if reply == QMessageBox.StandardButton.Save:
                self._settings_tab.save()
            else:
                self._settings_tab.discard()

        self._save_persisted_data()
        event.accept()

    # ------------------------------------------------------------------
    # Flush wiring
    # ------------------------------------------------------------------

    def _on_flush_category(self, category: str) -> None:
        """Flush a single persistence category and reset the in-memory cache."""
        self._persistence.flush(category)
        # Reset the corresponding in-memory variable to empty
        if category == "loaded_monsters":
            self._persisted_monsters = []
        elif category == "encounters":
            self._persisted_encounters = []
        elif category == "modified_monsters":
            self._persisted_modifications = {}
        elif category == "macros":
            self._persisted_macros = []
        self._refresh_flush_counts()

    def _on_clear_all(self) -> None:
        """Flush all persistence categories and reset all in-memory caches."""
        self._persistence.flush_all()
        self._persisted_monsters = []
        self._persisted_encounters = []
        self._persisted_modifications = {}
        self._persisted_macros = []
        self._refresh_flush_counts()

    def _refresh_flush_counts(self) -> None:
        """Update flush count labels in the Settings tab from current persistence state."""
        counts = {cat: self._persistence.count(cat) for cat in self._persistence.categories()}
        self._settings_tab.refresh_counts(counts)
