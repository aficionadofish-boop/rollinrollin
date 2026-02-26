---
phase: 14-bug-fixes-critical-polish
plan: 01
subsystem: ui
tags: [pyside6, persistence, library, sidebar, qpainter]

# Dependency graph
requires:
  - phase: 08-domain-expansion-and-persistence-foundation
    provides: PersistenceService with loaded_monsters category
  - phase: 10-encounter-sidebar-and-persistence
    provides: EncounterSidebarDock collapse/expand infrastructure
provides:
  - Imported monsters survive app restart via source file path persistence
  - Library single-result clicks correctly load the statblock
  - Collapsed sidebar is 24px wide with vertically rotated Show text
affects: [15-editor-parser-overhaul, 16-buff-system-output-improvements]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - source_files_changed signal connects library import events to app-level persistence handler
    - QPainter coordinate rotation for narrow vertical button labels

key-files:
  created: []
  modified:
    - src/ui/library_tab.py
    - src/ui/app.py
    - src/ui/encounter_sidebar.py

key-decisions:
  - "BUG-01 persistence: emit source_files_changed only when at least one monster was actually imported (not on skip-all batch); avoids false saves"
  - "BUG-01 restart reload: skip missing files silently but keep them in persisted list — file may be on removable drive"
  - "BUG-01 startup: populate _library_tab._imported_paths from persisted data so subsequent imports don't lose previously saved paths"
  - "BUG-02 fix: use selectedRows() instead of selected.indexes() — indexes() returns per-cell deltas which are empty for single-result selections triggered by programmatic selection changes"
  - "UX-01: _COLLAPSED_WIDTH changed from 60 to 24; _RotatedButton overrides paintEvent with QPainter translate+rotate(90) pattern"

patterns-established:
  - "Rotated button pattern: _RotatedButton subclasses QPushButton, overrides paintEvent with QPainter.translate(width,0) + rotate(90) to render vertical text in narrow strips"
  - "Import persistence pattern: emit signal from library tab on file path change, handler in MainWindow saves to PersistenceService immediately"

requirements-completed: [BUG-01, BUG-02, UX-01]

# Metrics
duration: 18min
completed: 2026-02-26
---

# Phase 14 Plan 01: Bug Fixes (BUG-01, BUG-02, UX-01) Summary

**Imported monster persistence via source file path re-parse on startup, single-result library selection fix using selectedRows(), and 24px collapsed sidebar with QPainter-rotated Show label**

## Performance

- **Duration:** 18 min
- **Started:** 2026-02-26T22:37:12Z
- **Completed:** 2026-02-26T22:55:00Z
- **Tasks:** 2
- **Files modified:** 3

## Accomplishments
- Imported monsters now survive app close+reopen: file paths are emitted via `source_files_changed` signal, saved to `loaded_monsters.json`, and re-parsed from disk on startup
- Single-result library clicks now load the statblock: fixed `_on_selection_changed` to use `selectedRows()` which returns the full row regardless of which cell was clicked
- Collapsed sidebar strip is now 24px wide with "Show" text rendered vertically via `_RotatedButton` QPushButton subclass using QPainter coordinate rotation

## Task Commits

Each task was committed atomically:

1. **Task 1: Fix imported monster persistence and library selection** - `4291d27` (fix)
2. **Task 2: Narrow collapsed sidebar with rotated Show text** - `fe24e77` (feat)

**Plan metadata:** (docs commit to follow)

## Files Created/Modified
- `src/ui/library_tab.py` - Added `source_files_changed` signal, `_imported_paths` set, emit on successful import; fixed `_on_selection_changed` to use `selectedRows()`
- `src/ui/app.py` - Added `_on_source_files_changed` handler to persist paths; added `_reload_persisted_monster_files` called from `_load_persisted_data` on startup
- `src/ui/encounter_sidebar.py` - Added `_RotatedButton` class with QPainter paint override; changed `_COLLAPSED_WIDTH` to 24; replaced `QPushButton("Show")` with `_RotatedButton("Show")`

## Decisions Made
- `source_files_changed` is emitted only when at least one monster was actually imported (not on skip-all batches) to avoid spurious persistence writes
- Missing files on restart are skipped silently but kept in the persisted list — they may be on a removable drive and return later
- `_imported_paths` is populated from the persisted list on startup so subsequent imports in the same session accumulate correctly rather than starting from zero
- `selectedRows()` is the correct Qt method for row-level selection regardless of per-cell click events; `selected.indexes()` only returns cells included in the selection delta which is empty for unchanged rows
- `_COLLAPSED_WIDTH` set to 24 (matching `_RotatedButton._BTN_WIDTH`) for a minimal, clean collapsed strip

## Deviations from Plan

None - plan executed exactly as written.

## Issues Encountered
None — all 510 existing tests pass after both changes.

## User Setup Required
None - no external service configuration required.

## Next Phase Readiness
- BUG-01, BUG-02, and UX-01 are resolved; plans 14-02 through 14-06 can proceed independently
- No regressions detected in the test suite

---
*Phase: 14-bug-fixes-critical-polish*
*Completed: 2026-02-26*
