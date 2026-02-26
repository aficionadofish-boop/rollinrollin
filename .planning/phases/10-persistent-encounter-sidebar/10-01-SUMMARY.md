---
phase: 10-persistent-encounter-sidebar
plan: 01
subsystem: ui, persistence, settings
tags: [sidebar, QDockWidget, encounter, persistence, animation]
dependency_graph:
  requires:
    - src/persistence/service.py (PersistenceService)
    - src/settings/models.py (AppSettings)
    - src/domain/models.py (Monster dataclass)
  provides:
    - src/ui/encounter_sidebar.py (EncounterSidebarDock)
    - src/persistence/service.py (active/saved encounter CRUD)
    - src/settings/models.py (sidebar_width field)
  affects:
    - src/ui/app.py (Plan 02 will wire the sidebar into MainWindow)
    - src/tests/test_persistence_service.py (updated for new schema)
tech_stack:
  added: []
  patterns:
    - QPropertyAnimation on maximumWidth for collapse/expand slide
    - QListWidget.DragDropMode.InternalMove for drag-to-reorder
    - blockSignals() on QSpinBox to prevent infinite signal loops
    - Load+merge pattern for encounters.json (preserves active when saving saved, vice versa)
key_files:
  created:
    - src/ui/encounter_sidebar.py
  modified:
    - src/persistence/service.py
    - src/settings/models.py
    - src/tests/test_persistence_service.py
decisions:
  - "Encounters category changed from list to dict schema {active: {...}, saved: [{...}]} — list was never populated by UI"
  - "count('encounters') returns len(saved) + (1 if active else 0)"
  - "sidebar_width: int = 300 added to AppSettings for cross-session persistence"
  - "EncounterSidebarDock uses two internal widgets (content + handle strip) swapped on collapse, not QDockWidget.hide()"
  - "CR-descending sort applied after add; drag-to-reorder overrides sort order"
  - "Start always expanded — collapse state not persisted (DM expects to see encounter on launch)"
  - "_MonsterRowWidget uses blockSignals(True/False) on QSpinBox during programmatic set_count() calls"
metrics:
  duration: "~4 minutes"
  completed: "2026-02-26"
  tasks_completed: 2
  files_modified: 4
  files_created: 1
---

# Phase 10 Plan 01: EncounterSidebarDock Core Widget Summary

**One-liner:** QDockWidget encounter sidebar with 200ms InOutQuad collapse animation, CR-sorted monster list (name+QSpinBox+X), XP summary header, and dict-schema persistence for active+saved encounters.

## Tasks Completed

| Task | Name | Commit | Key Files |
|------|------|--------|-----------|
| 1 | Update PersistenceService encounters schema and AppSettings | ee663ee | src/persistence/service.py, src/settings/models.py, src/tests/test_persistence_service.py |
| 2 | Build EncounterSidebarDock QDockWidget with full UI | 2611036 | src/ui/encounter_sidebar.py |

## What Was Built

### Task 1: PersistenceService + AppSettings

`src/persistence/service.py`:
- Added `"encounters"` to `_DICT_CATEGORIES` — empty default is now `{}` instead of `[]`
- Added `load_active_encounter() -> dict | None` — returns `encounters["active"]` or `None`
- Added `save_active_encounter(data: dict)` — load+merge pattern; preserves `"saved"` list
- Added `load_saved_encounters() -> list` — returns `encounters["saved"]` or `[]`
- Added `save_saved_encounter(encounter: dict)` — appends to saved list, saves back
- Added `delete_saved_encounter(index: int)` — removes saved[index], saves back
- `save_encounters(data: dict)` kept for flush/autosave lifecycle (writes entire dict)
- `load_encounters() -> dict` kept for backward compat (returns full encounters dict)
- `count("encounters")` updated: `len(saved) + (1 if active else 0)`

`src/settings/models.py`:
- Added `sidebar_width: int = 300`

`src/tests/test_persistence_service.py`:
- Updated `LIST_CATEGORIES` — removed `"encounters"` (now a dict category)
- Updated `DICT_CATEGORIES` — added `"encounters"`
- Updated all tests that used `save_encounters([...])` / `load_encounters()` to use new CRUD methods
- Added `test_count_encounters_reflects_active_and_saved`
- Added `test_active_encounter_load_merge_does_not_clobber_saved`
- Added `test_delete_saved_encounter`

### Task 2: EncounterSidebarDock (630 lines)

`src/ui/encounter_sidebar.py` provides:

**Module-level:**
- `_XP_BY_CR: dict[str, int]` — D&D 5e XP by CR (CR 0 through 24)
- `cr_to_float(cr: str) -> float` — CR string to float for sorting
- `compute_encounter_xp(members: list[tuple]) -> int` — total base XP

**`_MonsterRowWidget(QWidget)`:**
- `QHBoxLayout`: name `QLabel` (expanding) | count `QSpinBox` (range 1-99, 56px) | remove `QPushButton` ("X", 28px)
- Signals: `count_changed(name, count)`, `remove_requested(name)`, `context_menu_requested(name, monster, pos)`
- `set_count()` uses `blockSignals(True/False)` to prevent infinite loops
- `set_selected(bool)` toggles `background-color: #d0e8ff` highlight

**`EncounterSidebarDock(QDockWidget)`:**
- Signals: `monster_selected`, `switch_to_attack_roller`, `encounter_changed`, `view_stat_block_requested`, `save_btn_clicked`, `load_btn_clicked`
- `objectName("encounter_sidebar")` — required for `saveState`/`restoreState`
- `setTitleBarWidget(QWidget())` — hides default title bar; custom header inside `_content_widget`
- `setFeatures(DockWidgetMovable)` — prevents user from closing or floating
- Two inner widgets: `_content_widget` (full panel), `_handle_widget` (20px strip with ">>" button)
- Animation: `QPropertyAnimation(self, b"maximumWidth")`, 200ms, `InOutQuad`
- Content panel: name label + collapse `<<` button | summary label | Save/Load buttons | separator | empty label | `QListWidget`
- `toggle_collapse()` / `_collapse()` / `_after_collapse()` / `_expand()` / `_after_expand()` — Pattern 2 from RESEARCH.md
- `_after_expand()` resets `setMaximumWidth(16777215)` so user can drag-resize
- Context menu: Remove | Remove all {name} | separator | Roll Attacks | View Stat Block
- CR-descending sort via `_sort_by_cr()` after `add_monster()`; drag-to-reorder via `rowsMoved` signal
- Public API: `add_monster()`, `remove_monster()`, `set_encounter()`, `get_members()`, `get_encounter_name()`, `set_encounter_name()`, `set_expanded_width()`
- Empty state: `_update_empty_state()` shows/hides list, disables collapse button and save button when empty
- Auto-expand on first monster added; auto-collapse when last monster removed

## Verification Results

1. `from src.ui.encounter_sidebar import EncounterSidebarDock` — passes
2. `from src.persistence.service import PersistenceService` — passes
3. `AppSettings().sidebar_width == 300` — passes
4. `python -m pytest src/tests/ -v` — 488 passed, 0 failed
5. All 6 required signals present on EncounterSidebarDock
6. `_XP_BY_CR.get('1', 0)` returns 200 (correct)

## Deviations from Plan

### Auto-fixed Issues

None — plan executed exactly as written.

### Notes

- The plan had a minor inconsistency in `save_active_encounter` spec: it said "sets `data["active"] = data`" (self-referential). Implemented as intended: `data_dict["active"] = encounter_data` where `data_dict` is the loaded encounters dict and `encounter_data` is the parameter. This matches the load+merge pattern described in Phase 09-05.
- `_sort_by_cr()` rebuilds the entire QListWidget with new row widgets (simpler than reordering existing items). This is correct since sort only runs after `add_monster()`, not on every change.

## Self-Check: PASSED

All created files exist on disk. Both task commits (ee663ee, 2611036) exist in git log. SUMMARY.md created successfully.
