---
phase: 16-buff-system-output-improvements
plan: "03"
subsystem: ui
tags: [qlineedit, encounter, sidebar, persistence, pyside6]

requires:
  - phase: 10-encounter-sidebar-and-saves-integration
    provides: EncounterSidebarDock, PersistenceService, LoadEncounterDialog

provides:
  - Sidebar QLineEdit name field with auto-generated timestamped names
  - Auto-name updates live as creatures are added/removed, preserves custom text
  - get_save_name() formats "{custom} — {auto}" or pure auto on save
  - LoadEncounterDialog inline double-click name editing with persistence
  - PersistenceService.rename_saved_encounter() for name update in encounters.json
  - Sidebar resizeEvent tracks expanded width; _expand() restores user-chosen width

affects:
  - encounter-sidebar
  - load-encounter-dialog
  - persistence-service

tech-stack:
  added: []
  patterns:
    - "Auto-name guard: compare field text to _current_auto_name before overwriting"
    - "QListWidget inline edit: blockSignals during population, ItemIsEditable flag, itemChanged signal"
    - "resizeEvent width tracking: only record when not collapsed and width >= 200"

key-files:
  created: []
  modified:
    - src/ui/encounter_sidebar.py
    - src/ui/app.py
    - src/ui/load_encounter_dialog.py
    - src/persistence/service.py

key-decisions:
  - "Auto-name format: '{YYYY-MM-DD HH:MM} — {N} creature(s)' generated fresh on each encounter change"
  - "Custom name guard: only overwrite _name_edit if current text == _current_auto_name or empty"
  - "Save name format: '{custom} — {auto_base}' appends fresh auto timestamp+count when DM typed custom"
  - "Load dialog inline edit: extract name part before first em-dash in display string to strip creature count and date"
  - "Renames processed before deletions in _on_sidebar_load so original indices remain valid"
  - "set_expanded_width applies immediately via resize() when expanded (not via setMaximumWidth constraint)"

requirements-completed:
  - ENC-01
  - ENC-02
  - ENC-03

duration: 3min
completed: 2026-02-28
---

# Phase 16 Plan 03: Encounter Naming, Load Dialog Edit, Sidebar Resize Summary

**QLineEdit encounter name field with auto-generated timestamps, load dialog inline rename via double-click, and sidebar width persistence across sessions**

## Performance

- **Duration:** 3 min
- **Started:** 2026-02-28T17:42:02Z
- **Completed:** 2026-02-28T17:45:00Z
- **Tasks:** 2
- **Files modified:** 4

## Accomplishments
- Replaced static QLabel with editable QLineEdit in sidebar header, auto-populating with "{date} {time} — N creatures" that updates live as the encounter changes
- Custom names typed by the DM are preserved when creature counts change; Save formats them as "{custom} — {auto}"
- Load dialog now supports double-click inline name editing with em-dash-aware name extraction and rename persistence via new PersistenceService method
- Sidebar resizeEvent tracks user-chosen expanded width; _expand() restores it on collapse-then-expand cycles

## Task Commits

Each task was committed atomically:

1. **Task 1: Sidebar encounter name field with auto-name and custom name support** - `c95a000` (feat)
2. **Task 2: Load dialog inline name edit and sidebar resize persistence** - `96ced51` (feat)

**Plan metadata:** (docs commit follows)

## Files Created/Modified
- `src/ui/encounter_sidebar.py` - Added QLineEdit _name_edit, _generate_auto_name(), _update_auto_name(), get_save_name(), resizeEvent, updated _expand() and set_expanded_width()
- `src/ui/app.py` - Updated _on_sidebar_save() to use get_save_name(), added pending_renames() processing in _on_sidebar_load()
- `src/ui/load_encounter_dialog.py` - Added inline editing (DoubleClicked trigger, ItemIsEditable flag, blockSignals during population), _on_item_renamed(), pending_renames() accessor
- `src/persistence/service.py` - Added rename_saved_encounter(index, new_name) method

## Decisions Made
- Auto-name guard uses string comparison (`current_text == _current_auto_name or current_text == ""`) — simple and reliable without needing a separate "is_custom" flag
- Load dialog stores name portion before em-dash separator (the creature count and date are display-only metadata, not part of the user-facing name)
- Renames processed before deletions in `_on_sidebar_load` to keep original indices valid when both operations occur in same dialog session
- `set_expanded_width()` now uses `resize()` instead of `setMaximumWidth()` — maximum is always QWIDGETSIZE_MAX when expanded, preserving full resize freedom

## Deviations from Plan

None - plan executed exactly as written.

## Issues Encountered
None

## User Setup Required
None - no external service configuration required.

## Next Phase Readiness
- ENC-01, ENC-02, ENC-03 all complete
- All encounter naming features are wired end-to-end through persistence
- Phase 16 plans may continue with COMBAT-UX items if any remain
