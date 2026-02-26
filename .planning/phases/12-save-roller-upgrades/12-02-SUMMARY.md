---
phase: 12-save-roller-upgrades
plan: 02
subsystem: ui
tags: [pyside6, qcheckbox, encounter-sidebar, creature-selection]

# Dependency graph
requires:
  - phase: 10-encounter-sidebar-and-persistence
    provides: "_MonsterRowWidget and EncounterSidebarDock with get_members() API"
provides:
  - "QCheckBox per _MonsterRowWidget for per-creature selection"
  - "Select All / Select None / Invert buttons in sidebar header"
  - "EncounterSidebarDock.get_checked_members() returning only checked (Monster, count) pairs"
  - "Checkbox state preserved across _sort_by_cr() rebuilds"
affects:
  - "12-03 through 12-07 — any plan that calls get_checked_members() for save participants"

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Capture-before/restore-after pattern for state preservation across widget rebuilds"
    - "checked_state = {m.name: rw.is_checked() for m, rw, _ in self._rows} before sort; restore after"

key-files:
  created: []
  modified:
    - src/ui/encounter_sidebar.py

key-decisions:
  - "Checkbox state is NOT persisted to disk — all rows start checked on set_encounter() and app launch (avoids confusion when DM returns to a saved encounter days later)"
  - "Grouped creatures (e.g., 4x Goblin) toggle as a group via the single checkbox per monster type row — individual-creature expansion is deferred"
  - "QCheckBox prepended before name label (leftmost position) for intuitive check-then-read scanning"
  - "select_all/select_none/invert_selection buttons placed as Row 4 in sidebar header, after Save/Load row"

patterns-established:
  - "Capture-before/restore-after for _sort_by_cr(): save {name: is_checked()} dict before clearing rows, call set_checked() after rebuilding"

requirements-completed: [SAVE-08]

# Metrics
duration: 2min
completed: 2026-02-26
---

# Phase 12 Plan 02: Save Roller Upgrades — Sidebar Checkboxes Summary

**Per-creature QCheckBox selection on EncounterSidebarDock with Select All / None / Invert shortcuts and get_checked_members() API for save participant filtering**

## Performance

- **Duration:** ~2 min
- **Started:** 2026-02-26T06:08:07Z
- **Completed:** 2026-02-26T06:09:30Z
- **Tasks:** 1 of 1
- **Files modified:** 1

## Accomplishments

- Added QCheckBox (checked by default) as the leftmost widget in each `_MonsterRowWidget` row
- Added `is_checked()` and `set_checked()` accessor methods to `_MonsterRowWidget`
- Added Select All / Select None / Invert shortcut buttons (Row 4) to `EncounterSidebarDock` header
- Added `select_all()`, `select_none()`, `invert_selection()` public methods to `EncounterSidebarDock`
- Added `get_checked_members()` returning only checked `(Monster, count)` pairs in display order
- Added `set_all_checked()` utility method for bulk state control
- Fixed `_sort_by_cr()` to preserve checkbox state across row rebuilds via capture-before/restore-after pattern

## Task Commits

Each task was committed atomically:

1. **Task 1: Add QCheckBox to _MonsterRowWidget and selection shortcuts to sidebar** - `76fd8f6` (feat)

**Plan metadata:** _(pending final commit)_

## Files Created/Modified

- `src/ui/encounter_sidebar.py` - Added QCheckBox to _MonsterRowWidget, selection shortcut buttons, get_checked_members(), checkbox state preservation in _sort_by_cr()

## Decisions Made

- Checkbox state not persisted to disk — all rows start checked on `set_encounter()` and app launch; avoids confusion when DM returns to a saved encounter days later (follows RESEARCH.md recommendation)
- One checkbox per monster type row (not per individual creature) — the sidebar's `(Monster, count)` data model naturally groups creatures; individual toggling is deferred
- Buttons labeled "All", "None", "Invert" for compactness; placed as the fourth row in the sidebar header below Save/Load

## Deviations from Plan

None - plan executed exactly as written.

## Issues Encountered

None.

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness

- `get_checked_members()` is now ready for Plans 03+ to call when building save participants
- The sidebar public API is stable: `get_members()` still returns all members; `get_checked_members()` returns the filtered subset
- No blockers for subsequent plans

---
*Phase: 12-save-roller-upgrades*
*Completed: 2026-02-26*
