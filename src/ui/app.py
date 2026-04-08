"""MainWindow — root application window with tab bar."""
from __future__ import annotations

import datetime
import random
from pathlib import Path

from PySide6.QtCore import Qt, QTimer
from PySide6.QtWidgets import QMainWindow, QTabWidget, QMessageBox, QSplitter

from src.combat.models import CombatState, PlayerCharacter
from src.domain.models import MonsterModification
from src.engine.roller import Roller
from src.library.service import MonsterLibrary
from src.persistence.service import PersistenceService
from src.settings.service import SettingsService
from src.settings.models import AppSettings
from src.ui.library_tab import MonsterLibraryTab
from src.ui.attack_roller_tab import AttackRollerTab
from src.ui.combat_tracker_tab import CombatTrackerTab
from src.ui.encounters_tab import SavesTab
from src.ui.encounter_sidebar import EncounterSidebarDock
from src.ui.load_encounter_dialog import LoadEncounterDialog
from src.ui.macro_sandbox_tab import MacroSandboxTab
from src.ui.settings_tab import SettingsTab
from src.ui.storyteller_tab import StorytellerTab
from src.ui.theme_service import ThemeService
from src.workspace.setup import WorkspaceManager, resolve_workspace_root


class MainWindow(QMainWindow):
    """Main application window containing all tabs."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("RollinRollin")
        self.resize(1100, 750)

        # Shared state — one instance each for the entire session
        self._theme_service = ThemeService()
        self._library = MonsterLibrary()
        self._roller = Roller(random.Random())  # unseeded; seeding handled via settings
        self._workspace_manager = WorkspaceManager(resolve_workspace_root())
        self._workspace_manager.initialize()

        # Settings service: load persisted settings before constructing tabs
        self._settings_service = SettingsService(self._workspace_manager.root)
        self._current_settings = self._settings_service.load()

        # Persistence service: load session data on startup
        self._persistence = PersistenceService(self._workspace_manager.root)

        # Track previous encounter monster name set for LR counter reset logic (BUG-15)
        self._prev_encounter_names: set[str] = set()

        # Tabs
        self._tab_widget = QTabWidget()
        self._library_tab = MonsterLibraryTab(library=self._library, persistence=self._persistence)
        self._attack_roller_tab = AttackRollerTab(roller=self._roller)
        self._combat_tracker_tab = CombatTrackerTab(
            roller=self._roller,
            library=self._library,
        )
        self._storyteller_tab = StorytellerTab(persistence=self._persistence)
        self._saves_tab = SavesTab(
            library=self._library,
            roller=self._roller,
            persistence_service=self._persistence,
        )
        self._macro_tab = MacroSandboxTab(
            roller=self._roller,
            workspace_manager=self._workspace_manager,
        )
        self._settings_tab = SettingsTab()

        # Tab order: Library, Attack Roller, Combat Tracker, Storyteller, Saves, Macro Sandbox, Settings
        self._tab_widget.addTab(self._library_tab, "Library")
        self._tab_widget.addTab(self._attack_roller_tab, "Attack Roller")
        self._tab_widget.addTab(self._combat_tracker_tab, "Combat Tracker")
        self._tab_widget.addTab(self._storyteller_tab, "Storyteller")
        self._tab_widget.addTab(self._saves_tab, "Saves")
        self._tab_widget.addTab(self._macro_tab, "Macro Sandbox")
        self._tab_widget.addTab(self._settings_tab, "Settings")

        # Create sidebar and combine with tab widget in a splitter for drag-resize
        self._sidebar = EncounterSidebarDock(library=self._library, parent=self)
        self._main_splitter = QSplitter(Qt.Orientation.Horizontal)
        self._main_splitter.setObjectName("main_splitter")
        self._main_splitter.addWidget(self._tab_widget)
        self._main_splitter.addWidget(self._sidebar)
        self._main_splitter.setStretchFactor(0, 1)   # tabs take remaining space
        self._main_splitter.setStretchFactor(1, 0)    # sidebar keeps its size
        self._main_splitter.setChildrenCollapsible(False)
        self.setCentralWidget(self._main_splitter)

        # Respond to sidebar collapse/expand to adjust splitter sizes
        self._sidebar.collapse_toggled.connect(self._on_sidebar_collapse_toggled)

        # Load persisted data AFTER sidebar is constructed
        self._load_persisted_data()

        # Cross-tab signal: Library drop zone → sidebar
        self._library_tab.monster_added_to_encounter.connect(
            self._sidebar.add_monster
        )

        # Persist imported monster file paths when they change
        self._library_tab.source_files_changed.connect(self._on_source_files_changed)

        # Cross-tab signal: sidebar encounter changes → Attack Roller creature list
        self._sidebar.encounter_changed.connect(
            self._attack_roller_tab.set_creatures
        )

        # Sidebar: auto-reload SavesTab participants when encounter changes
        self._sidebar.encounter_changed.connect(self._on_sidebar_encounter_changed)

        # Cross-tab signal: sidebar single-click → preload Attack Roller
        self._sidebar.monster_selected.connect(
            self._attack_roller_tab.set_active_creature
        )

        # Cross-tab signal: sidebar double-click → switch to Attack Roller tab
        self._sidebar.switch_to_attack_roller.connect(
            lambda: self._tab_widget.setCurrentWidget(self._attack_roller_tab)
        )

        # Cross-tab signal: sidebar "View Stat Block" → switch to Library and select
        self._sidebar.view_stat_block_requested.connect(self._on_view_stat_block)

        # Sidebar save/load button signals
        self._sidebar.save_btn_clicked.connect(self._on_sidebar_save)
        self._sidebar.load_btn_clicked.connect(self._on_sidebar_load)

        # Combat Tracker: Start Combat button → read sidebar → call start_combat()
        self._combat_tracker_tab.start_combat_requested.connect(self._on_start_combat)

        # Combat Tracker: Send to Saves → load participants + switch to Saves tab
        self._combat_tracker_tab.send_to_saves.connect(self._on_send_to_saves)

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
    # Window lifecycle
    # ------------------------------------------------------------------

    def showEvent(self, event) -> None:
        """Apply deferred splitter sizing on first show.

        setSizes() must run AFTER Qt's layout pass has measured all widgets.
        Calling it during __init__ or _load_persisted_data() fires before the
        splitter has a real geometry, so at 1100x750 the minimum-size
        constraints consume all available slack and the handle is immovable.
        The guard flag prevents re-applying on subsequent show events
        (minimize/restore cycles).
        """
        super().showEvent(event)
        if not hasattr(self, '_splitter_initialized'):
            self._splitter_initialized = True
            if not self._sidebar.is_collapsed():
                sidebar_w = self._sidebar.get_expanded_width()
                total_w = self.width()
                self._main_splitter.setSizes([total_w - sidebar_w, sidebar_w])

    # ------------------------------------------------------------------
    # Settings wiring
    # ------------------------------------------------------------------

    def _on_settings_saved(self, settings: AppSettings) -> None:
        """Called when user clicks Save in Settings tab."""
        self._settings_service.save(settings)
        self._current_settings = settings
        self._apply_settings(settings)

    def get_theme_service(self) -> ThemeService:
        """Return the shared ThemeService instance.

        Allows child widgets to access the active accent color via the main window.
        """
        return self._theme_service

    def _apply_settings(self, settings: AppSettings) -> None:
        """Apply loaded/saved settings to all tabs and the shared roller."""
        # Apply theme first so all subsequent widget creation uses correct colors
        self._theme_service.apply(settings)

        # Re-seed or un-seed the shared RNG (never recreate the Roller instance)
        if settings.seeded_rng_enabled and settings.seed_value is not None:
            self._roller._rng.seed(settings.seed_value)
        else:
            self._roller._rng.seed(None)

        # Apply defaults to tabs
        self._attack_roller_tab.apply_defaults(settings)
        self._saves_tab.apply_defaults(settings)

        # Update seeded badge on output panels
        seeded = settings.seeded_rng_enabled and settings.seed_value is not None
        self._attack_roller_tab.set_seeded_mode(seeded)
        self._macro_tab._result_panel.set_seeded_mode(seeded)

        # Update template card accent color in macro sandbox
        accent = self._theme_service.get_accent_color(settings)
        if hasattr(self, '_macro_tab'):
            self._macro_tab.set_accent_color(accent)

        # Apply sandbox font to MacroEditor
        if hasattr(self, '_macro_tab'):
            self._macro_tab.set_sandbox_font(settings.sandbox_font)

        # Apply UI scaling — adjust base font and control sizes
        ui_scale = getattr(settings, "ui_scale", 100)
        from PySide6.QtWidgets import QApplication
        app = QApplication.instance()
        if app:
            font = app.font()
            base_pt = 9
            font.setPointSizeF(base_pt * ui_scale / 100.0)
            app.setFont(font)
            if ui_scale != 100:
                min_h = int(22 * ui_scale / 100)
                app.setStyleSheet(
                    app.styleSheet() +
                    f"\nQPushButton, QComboBox, QSpinBox, QLineEdit {{ min-height: {min_h}px; }}"
                )

        # Restore storyteller system and last-used config
        if hasattr(self, '_storyteller_tab'):
            self._storyteller_tab.restore_config(
                settings.storyteller_system,
                settings.storyteller_last_config,
            )

    # ------------------------------------------------------------------
    # Tab change guard (unsaved settings changes) and sidebar visibility
    # ------------------------------------------------------------------

    def _on_tab_changed(self, new_index: int) -> None:
        """Guard: prompt to save/discard when leaving Settings tab with unsaved changes.
        Also hide/show sidebar when Combat Tracker tab is active (combat log replaces it).
        """
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

        # Always capture current splitter sizes before switching
        if self._sidebar.isVisible():
            self._sidebar_sizes_backup = self._main_splitter.sizes()

        # Hide sidebar when Combat Tracker is active; restore otherwise
        current_widget = self._tab_widget.widget(new_index)
        if current_widget is self._combat_tracker_tab:
            self._sidebar.setVisible(False)
        else:
            self._sidebar.setVisible(True)
            if hasattr(self, '_sidebar_sizes_backup') and self._sidebar_sizes_backup:
                self._main_splitter.setSizes(self._sidebar_sizes_backup)

        # Auto-load checked sidebar members when switching to Saves tab
        if current_widget is self._saves_tab:
            checked = self._sidebar.get_checked_members()
            if checked:
                self._saves_tab.load_participants_from_sidebar(checked)

    def _on_sidebar_collapse_toggled(self, collapsed: bool) -> None:
        """Adjust splitter sizes when sidebar collapses or expands.

        Also hides the splitter handle when collapsed (no phantom grab zone next
        to the 24px strip) and restores it on expand to match the CSS width.
        """
        if collapsed:
            total = sum(self._main_splitter.sizes())
            self._main_splitter.setSizes([total - 24, 24])
            self._main_splitter.setHandleWidth(0)
        else:
            total = sum(self._main_splitter.sizes())
            sidebar_w = self._sidebar.get_expanded_width()
            self._main_splitter.setSizes([total - sidebar_w, sidebar_w])
            self._main_splitter.setHandleWidth(9)

    # ------------------------------------------------------------------
    # Persistence lifecycle
    # ------------------------------------------------------------------

    def _on_source_files_changed(self, paths: list) -> None:
        """Save updated import file paths to persistence when library imports change."""
        self._persisted_monsters = paths
        self._persistence.save_loaded_monsters(paths)

    def _reload_persisted_monster_files(self) -> None:
        """Re-parse persisted monster source file paths into the library on startup.

        Skips paths that no longer exist on disk (e.g. files on removable drives)
        without removing them from the persisted list — they may return later.
        Populates _library_tab._imported_paths so subsequent imports accumulate
        correctly.
        """
        from pathlib import Path as _Path
        from src.parser.statblock_parser import parse_file as _parse_file

        paths = self._persisted_monsters
        if not paths:
            return

        for path_str in paths:
            path = _Path(path_str)
            if not path.exists():
                # File missing (removable drive, renamed, etc.) — skip silently
                continue
            try:
                result = _parse_file(path)
            except Exception:
                continue

            for monster in result.monsters:
                if not self._library.has_name(monster.name):
                    self._library.add(monster)
                # If monster already exists (e.g. loaded via modifications), skip
                # rather than creating a duplicate.

        # Populate _imported_paths so future imports don't lose these paths
        self._library_tab._imported_paths = set(paths)

        # Refresh the library tab model to show restored monsters
        self._library_tab._refresh_model()
        self._library_tab._refresh_type_combo()

    def _load_persisted_data(self) -> None:
        """Load all persistence categories from disk into instance variables."""
        self._persisted_monsters = self._persistence.load_loaded_monsters()
        self._persisted_modifications = self._persistence.load_modified_monsters()
        self._persisted_macros = self._persistence.load_macros()

        # Re-parse persisted monster source files into the library
        self._reload_persisted_monster_files()

        # Restore active encounter into sidebar
        active_enc = self._persistence.load_active_encounter()
        if active_enc and active_enc.get("members"):
            resolved_members = []
            unresolved_count = 0
            for entry in active_enc["members"]:
                name = entry.get("name", "")
                count = entry.get("count", 1)
                if self._library.has_name(name):
                    resolved_members.append((self._library.get_by_name(name), count))
                else:
                    unresolved_count += 1

            enc_name = active_enc.get("name", "Active Encounter")
            self._sidebar.set_encounter(enc_name, resolved_members)

            if unresolved_count > 0:
                self.statusBar().showMessage(
                    f"Encounter restored — {unresolved_count} monster(s) not found in library",
                    5000,
                )

        # Restore sidebar width from settings — actual splitter sizing deferred to showEvent
        # so it runs after Qt's layout pass (fixes resize deadlock at 1100x750)
        self._sidebar.set_expanded_width(self._current_settings.sidebar_width)

        # Load player characters into Combat Tracker PC subtab
        pc_data = self._persistence.load_player_characters()
        pcs = [PlayerCharacter.from_dict(p) for p in pc_data]
        self._combat_tracker_tab.set_pcs(pcs)

        # Load combat state into Combat Tracker
        combat_data = self._persistence.load_combat_state()
        if combat_data and combat_data.get("combatants"):
            self._combat_tracker_tab.load_combat_state(combat_data)

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
            if getattr(mod, "proficiency_bonus", None) is not None:
                modified.proficiency_bonus = mod.proficiency_bonus

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
                            condition=dp.get("condition"),
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
                        after_text=a_dict.get("after_text", ""),
                    ))
                modified.actions = reconstructed_actions

            # Apply trait overrides
            if mod.traits:
                from src.domain.models import Trait, DetectedDie
                reconstructed_traits = []
                for t_dict in mod.traits:
                    rollable_dice = [
                        DetectedDie(
                            full_match=d.get("full_match", ""),
                            dice_expr=d.get("dice_expr", "1d6"),
                            damage_type=d.get("damage_type", "unknown"),
                            average=d.get("average", 0),
                        )
                        for d in t_dict.get("rollable_dice", [])
                    ]
                    rr = t_dict.get("recharge_range")
                    recharge_range = tuple(rr) if rr else None
                    reconstructed_traits.append(Trait(
                        name=t_dict.get("name", ""),
                        description=t_dict.get("description", ""),
                        rollable_dice=rollable_dice,
                        recharge_range=recharge_range,
                    ))
                modified.traits = reconstructed_traits

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
        self._persistence.save_modified_monsters(self._persisted_modifications)
        self._persistence.save_macros(self._persisted_macros)

        # Save sidebar active encounter state
        members = self._sidebar.get_members()
        if members:
            active_data = {
                "name": self._sidebar.get_encounter_name(),
                "members": [{"name": m.name, "count": c} for m, c in members],
            }
            self._persistence.save_active_encounter(active_data)

        # Save player characters from PC subtab
        pcs = self._combat_tracker_tab.get_pcs()
        self._persistence.save_player_characters([pc.to_dict() for pc in pcs])

        # Save combat state
        combat_state = self._combat_tracker_tab.get_combat_state()
        if combat_state and combat_state.get("combatants"):
            self._persistence.save_combat_state(combat_state)

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

        # Capture storyteller state into settings before saving
        self._current_settings.storyteller_system = self._storyteller_tab.current_system()
        self._current_settings.storyteller_last_config = self._storyteller_tab.current_config()

        # Save sidebar width to settings (from splitter allocation)
        sizes = self._main_splitter.sizes()
        self._current_settings.sidebar_width = sizes[1] if len(sizes) > 1 else 350
        self._settings_service.save(self._current_settings)

        self._save_persisted_data()
        event.accept()

    # ------------------------------------------------------------------
    # Combat Tracker handlers
    # ------------------------------------------------------------------

    def _on_sidebar_encounter_changed(self, members: list) -> None:
        """When sidebar encounter changes, reload SavesTab participants from checked members.

        LR counters are only reset when the set of monster TYPES changes — not on count
        adjustments — so counters persist across multiple save rolls in the same fight.
        """
        checked = self._sidebar.get_checked_members()
        self._saves_tab.load_participants_from_sidebar(checked)
        # Reset LR counters only when the set of monster types actually changes (BUG-15)
        current_names = {monster.name for monster, _count in members}
        if current_names != self._prev_encounter_names:
            self._saves_tab.reset_lr_counters()
            self._prev_encounter_names = current_names

    def _on_start_combat(self) -> None:
        """Read sidebar encounter members and start combat in the Combat Tracker tab."""
        members = self._sidebar.get_members()
        if not members:
            QMessageBox.information(
                self,
                "No Encounter",
                "Load an encounter into the sidebar first.",
            )
            return
        self._combat_tracker_tab.start_combat(members)
        # Switch to Combat Tracker tab
        self._tab_widget.setCurrentWidget(self._combat_tracker_tab)

    def _on_send_to_saves(self, participants: list) -> None:
        """Receive selected combatants from Combat Tracker and load into Saves tab."""
        settings = self._settings_service.load()
        if settings.ct_send_overrides_sidebar:
            # CT selection overrides sidebar — load CT participants directly
            self._saves_tab.load_participants(participants)
        else:
            # Sidebar checkboxes are authoritative — ignore CT list, load from sidebar
            checked = self._sidebar.get_checked_members()
            self._saves_tab.load_participants_from_sidebar(checked)
        self._tab_widget.setCurrentWidget(self._saves_tab)

    # ------------------------------------------------------------------
    # Sidebar cross-tab handlers
    # ------------------------------------------------------------------

    def _on_view_stat_block(self, monster) -> None:
        """Switch to Library tab and select the requested monster."""
        self._tab_widget.setCurrentWidget(self._library_tab)
        self._library_tab.select_monster_by_name(monster.name)

    # ------------------------------------------------------------------
    # Sidebar Save / Load handlers
    # ------------------------------------------------------------------

    def _on_sidebar_save(self) -> None:
        """Save current sidebar encounter to the saved encounters list.

        Skips saving if an identical encounter (same name and members) already exists.
        Uses get_save_name() which formats "{custom} — {auto}" when the DM typed
        a custom name, or returns the pure auto-name otherwise.
        """
        name = self._sidebar.get_save_name() or "Untitled Encounter"
        members = self._sidebar.get_members()
        if not members:
            return

        member_data = [{"name": m.name, "count": c} for m, c in members]

        # Check for duplicate: same name and same members
        existing = self._persistence.load_saved_encounters()
        for enc in existing:
            if enc.get("name") == name and enc.get("members") == member_data:
                self.statusBar().showMessage("Encounter already saved", 3000)
                return

        saved_data = {
            "name": name,
            "members": member_data,
            "saved_at": datetime.datetime.now().isoformat(timespec="seconds"),
        }
        self._persistence.save_saved_encounter(saved_data)
        self.statusBar().showMessage("Encounter saved", 3000)

    def _on_sidebar_load(self) -> None:
        """Load a saved encounter via modal dialog, auto-saving current first."""
        # Auto-save current encounter before loading
        members = self._sidebar.get_members()
        if members:
            self._on_sidebar_save()

        saved = self._persistence.load_saved_encounters()
        if not saved:
            self.statusBar().showMessage("No saved encounters", 3000)
            return

        dialog = LoadEncounterDialog(saved, parent=self)
        accepted = dialog.exec() == LoadEncounterDialog.DialogCode.Accepted

        # Process renames before deletions so original indices remain valid
        for original_idx, new_name in dialog.pending_renames().items():
            if original_idx not in dialog.deleted_indices():
                self._persistence.rename_saved_encounter(original_idx, new_name)

        # Process deletions in reverse order to avoid index shifting
        deleted = sorted(dialog.deleted_indices(), reverse=True)
        for idx in deleted:
            self._persistence.delete_saved_encounter(idx)

        if accepted and dialog.selected_index() is not None:
            enc = saved[dialog.selected_index()]
            resolved_members = []
            for entry in enc.get("members", []):
                name = entry.get("name", "")
                count = entry.get("count", 1)
                if self._library.has_name(name):
                    resolved_members.append((self._library.get_by_name(name), count))

            self._sidebar.set_encounter(enc.get("name", ""), resolved_members)

    # ------------------------------------------------------------------
    # Flush wiring
    # ------------------------------------------------------------------

    def _on_flush_category(self, category: str) -> None:
        """Flush a single persistence category and reset the in-memory cache."""
        self._persistence.flush(category)
        # Reset the corresponding in-memory variable to empty
        if category == "loaded_monsters":
            self._persisted_monsters = []
            self._library.clear()
            self._library_tab._refresh_model()
            self._library_tab._refresh_type_combo()
        elif category == "encounters":
            # Clear the sidebar encounter state
            self._sidebar.set_encounter("", [])
        elif category == "modified_monsters":
            self._persisted_modifications = {}
        elif category == "macros":
            self._persisted_macros = []
        elif category == "combat_state":
            self._combat_tracker_tab.reset_combat_ui()
        elif category == "player_characters":
            self._combat_tracker_tab.clear_pcs()
        self._refresh_flush_counts()

    def _on_clear_all(self) -> None:
        """Flush all persistence categories and reset all in-memory caches."""
        self._persistence.flush_all()
        self._persisted_monsters = []
        self._persisted_modifications = {}
        self._persisted_macros = []
        self._library.clear()
        self._library_tab._refresh_model()
        self._library_tab._refresh_type_combo()
        self._sidebar.set_encounter("", [])
        self._combat_tracker_tab.reset_combat_ui()
        self._combat_tracker_tab.clear_pcs()
        self._refresh_flush_counts()

    def _refresh_flush_counts(self) -> None:
        """Update flush count labels in the Settings tab from current persistence state."""
        counts = {cat: self._persistence.count(cat) for cat in self._persistence.categories()}
        self._settings_tab.refresh_counts(counts)
