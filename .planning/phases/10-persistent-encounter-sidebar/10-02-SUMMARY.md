---
phase: 10-persistent-encounter-sidebar
plan: 02
subsystem: ui, persistence
tags: [sidebar, QDockWidget, encounter, persistence, signal-chain, dialog]
dependency_graph:
  requires:
    - src/ui/encounter_sidebar.py (EncounterSidebarDock — built in Plan 01)
    - src/persistence/service.py (load/save_active_encounter, load/save_saved_encounter, delete_saved_encounter)
    - src/settings/models.py (sidebar_width field)
    - src/ui/library_tab.py (monster_added_to_encounter signal)
    - src/ui/attack_roller_tab.py (set_creatures, set_active_creature)
  provides:
    - src/ui/app.py (MainWindow with sidebar docked, all signals wired, persistence lifecycle)
    - src/ui/load_encounter_dialog.py (LoadEncounterDialog)
    - src/ui/encounters_tab.py (SavesTab — encounter builder removed)
  affects:
    - src/ui/attack_roller_tab.py (set_active_creature method added)
tech_stack:
  added: []
  patterns:
    - QMainWindow.addDockWidget(Qt.DockWidgetArea.RightDockWidgetArea) for sidebar placement
    - Load+merge pattern for encounters.json active encounter on startup/close
    - Modal QDialog with original-index tracking for safe deletion during list mutation
    - datetime.datetime.now().isoformat(timespec="seconds") for save timestamps
key_files:
  created:
    - src/ui/load_encounter_dialog.py
  modified:
    - src/ui/app.py
    - src/ui/encounters_tab.py
    - src/ui/attack_roller_tab.py
decisions:
  - "SavesTab keeps file name encounters_tab.py to avoid breaking any future imports — only class name changed"
  - "LoadEncounterDialog tracks row_to_original mapping so deletions during the session do not shift index used for load"
  - "set_active_creature adds monster to creature list if not already present — allows sidebar single-click to work without full encounter load"
  - "_load_persisted_data called AFTER sidebar is constructed so set_encounter() can be called during startup"
  - "_persisted_encounters removed from MainWindow — sidebar is now the authoritative in-memory encounter state"
metrics:
  duration: "~3 minutes"
  completed: "2026-02-26"
  tasks_completed: 2
  files_modified: 3
  files_created: 1
---

# Phase 10 Plan 02: MainWindow Integration Summary

**One-liner:** EncounterSidebarDock docked into MainWindow at RightDockWidgetArea with full Library→Sidebar→AttackRoller signal chain, active encounter cross-session persistence, and LoadEncounterDialog with safe index-tracked deletion.

## Tasks Completed

| Task | Name | Commit | Key Files |
|------|------|--------|-----------|
| 1 | Refactor EncountersTab to SavesTab + Build LoadEncounterDialog | e24563c | src/ui/encounters_tab.py, src/ui/load_encounter_dialog.py |
| 2 | Wire EncounterSidebarDock into MainWindow with full signal chain and persistence | cee5620 | src/ui/app.py, src/ui/attack_roller_tab.py |

## What Was Built

### Task 1: SavesTab + LoadEncounterDialog

**`src/ui/encounters_tab.py`** — refactored from EncountersTab to SavesTab:
- Renamed class `EncountersTab` → `SavesTab`
- Removed entire encounter builder left panel: `EncounterMemberList` class, `_build_left_panel()`, `_name_edit`, `_member_list`, `_on_new()`, `_on_save()`, `_on_load()`, `_load_encounter_into_save_roller()`, `_get_encounters_folder()`, `encounter_members_changed` signal, `add_monster_to_encounter()` method
- Removed all associated imports: QFileDialog, QTextEdit, QSplitter, QLineEdit, Path, Encounter, EncounterService
- Simplified `_setup_ui()` to a flat QVBoxLayout containing Save Roller controls directly
- Added `load_participants(participants: list)` public method for sidebar integration
- Kept all save roller logic intact: `_execute_roll()`, `_format_participant_line()`, `_format_summary_line()`, `apply_defaults()`

**`src/ui/load_encounter_dialog.py`** — new LoadEncounterDialog (116 lines):
- `QDialog` subclass, modal, 400x300
- `QListWidget` with rows formatted as `"{name} — {N} creatures — {date}"`
- Load / Delete / Cancel buttons; Load and Delete enabled only when row is selected
- Double-click on row triggers load (same as clicking Load button)
- `_row_to_original: list[int]` maps current list positions to original `saved_encounters` indices — handles safe deletion during the dialog session without index shifting
- `selected_index() -> int | None` returns original index of encounter to load
- `deleted_indices() -> list[int]` returns original indices of all encounters deleted

### Task 2: MainWindow Integration

**`src/ui/app.py`** — complete wiring:

**Imports added:**
- `datetime`, `Qt` from PySide6.QtCore
- `EncounterSidebarDock`, `LoadEncounterDialog`
- `SavesTab` (replacing `EncountersTab`)

**Sidebar construction:**
```python
self._sidebar = EncounterSidebarDock(library=self._library, parent=self)
self.addDockWidget(Qt.DockWidgetArea.RightDockWidgetArea, self._sidebar)
```

**Tab change:** `"Encounters && Saves"` → `"Saves"`, `EncountersTab` → `SavesTab`

**Signal chain wired:**
- `library_tab.monster_added_to_encounter` → `sidebar.add_monster`
- `sidebar.encounter_changed` → `attack_roller_tab.set_creatures`
- `sidebar.monster_selected` → `attack_roller_tab.set_active_creature`
- `sidebar.switch_to_attack_roller` → `lambda: tab_widget.setCurrentWidget(attack_roller_tab)`
- `sidebar.save_btn_clicked` → `_on_sidebar_save`
- `sidebar.load_btn_clicked` → `_on_sidebar_load`

**Persistence lifecycle:**
- Startup: `load_active_encounter()` → resolve names from library → `sidebar.set_encounter()`; unresolved count shown in status bar; sidebar width restored from settings
- Close/autosave: `sidebar.get_members()` → serialize → `save_active_encounter()`; sidebar width saved to settings
- `_persisted_encounters` instance variable removed — sidebar is the authoritative in-memory state

**Save/Load handlers:**
- `_on_sidebar_save`: gets name+members from sidebar, serializes with ISO timestamp, calls `save_saved_encounter()`
- `_on_sidebar_load`: auto-saves current, loads saved list, shows LoadEncounterDialog, processes deletions in reverse order, resolves and loads selected encounter

**Flush integration:**
- `_on_flush_category("encounters")` → `sidebar.set_encounter("", [])`
- `_on_clear_all()` → `sidebar.set_encounter("", [])`

**`src/ui/attack_roller_tab.py`** — added `set_active_creature(monster)`:
- Adds monster to creature list if not already present
- Calls `_rebuild_action_list()` to show the monster's attacks
- Allows sidebar single-click to preload Attack Roller without requiring full encounter load

## Verification Results

1. `from src.ui.encounters_tab import SavesTab` — passes
2. `from src.ui.load_encounter_dialog import LoadEncounterDialog` — passes
3. `from src.ui.app import MainWindow` — passes
4. `python -m pytest src/tests/ -v` — 488 passed, 0 failed (both tasks)
5. All key signal wiring patterns verified in app.py source
6. `SavesTab` has no `encounter_members_changed` signal or `add_monster_to_encounter` method

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 2 - Missing functionality] Added set_active_creature to AttackRollerTab**
- **Found during:** Task 2 — plan specified wiring `sidebar.monster_selected → attack_roller_tab.set_active_creature` but method didn't exist
- **Issue:** `set_active_creature` was not yet implemented on AttackRollerTab; plan noted "may not exist yet" and described what to add
- **Fix:** Added `set_active_creature(monster)` method that adds the monster to the creature list if not already present and calls `_rebuild_action_list()`
- **Files modified:** src/ui/attack_roller_tab.py
- **Commit:** cee5620

### Notes

- `_persisted_encounters` instance variable removed from MainWindow entirely (was `dict`, used for old autosave loop). The sidebar is now the single authoritative in-memory encounter state. `_save_persisted_data()` now calls `save_active_encounter()` directly from sidebar state.
- The plan mentioned `set_expanded_width` should be called on startup — this is done in `_load_persisted_data()` after sidebar creation.
- `_load_persisted_data()` is now called AFTER sidebar is created (moved from before tabs). This was necessary because sidebar must exist before we can call `set_encounter()` on it.

## Self-Check: PASSED

All created/modified files exist on disk. Both task commits (e24563c, cee5620) exist in git log. SUMMARY.md created successfully.
