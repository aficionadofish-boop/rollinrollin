---
phase: 17-sidebar-handle-fix
plan: 01
subsystem: ui
tags: [qsplitter, pyside6, stylesheet, sidebar, resize]

# Dependency graph
requires:
  - phase: 16-buff-system-output-improvements
    provides: encounter sidebar with QSplitter already integrated
provides:
  - Sidebar QSplitter handle draggable at 1100x750 standard launch size
  - Scoped gradient CSS handle styling for all three themes with hover brightening
  - Handle disappears on sidebar collapse, reappears on expand
  - Deferred setSizes() via showEvent() to fix constraint deadlock
  - is_collapsed() accessor on EncounterSidebarDock
affects: [encounter sidebar, theme system, app window lifecycle]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "showEvent() deferred layout: setSizes() must run after Qt's layout pass — use showEvent() with a guard flag rather than __init__"
    - "Scoped QSplitter CSS: QSplitter#object_name::handle:horizontal overrides global handle rules for a specific splitter only"
    - "Handle width toggle: setHandleWidth(0) on collapse removes phantom grab zone; setHandleWidth(9) on expand restores grab zone matching CSS width"
    - "minimumWidth reduction: lowering sidebar minimumWidth from 200 to 150 gives splitter 50px more slack at smaller window sizes"

key-files:
  created: []
  modified:
    - src/ui/app.py
    - src/ui/encounter_sidebar.py
    - src/ui/theme_service.py

key-decisions:
  - "showEvent() deferred setSizes(): removed early call from _load_persisted_data() which fired before Qt's layout pass; showEvent() guard flag _splitter_initialized prevents re-applying on minimize/restore"
  - "setObjectName('main_splitter') on QSplitter enables CSS selector QSplitter#main_splitter scoping so handle style is isolated from Library/Macro/Combat internal splitters"
  - "minimumWidth reduced from 200 to 150 in _expand() and __init__: gives splitter 50px more drag range at 1100px window width; resizeEvent threshold updated to match"
  - "setHandleWidth(0/9) toggled in _on_sidebar_collapse_toggled: hides the grab zone entirely when collapsed so no phantom clickable area exists next to the 24px strip"
  - "Gradient CSS with qlineargradient: renders a 1-2px visible center line within a 9px grab zone; hover state widens visible portion and brightens color"

patterns-established:
  - "showEvent() lifecycle guard: check hasattr(self, '_flag') before first-run setup, set flag immediately to prevent duplicate execution"
  - "Splitter handle width CSS + programmatic width: stylesheet controls rendering, setHandleWidth() controls logical grab area — set both to same value (9px) to avoid conflicts"

requirements-completed: []

# Metrics
duration: 2min
completed: 2026-03-01
---

# Phase 17 Plan 01: Sidebar Handle Fix Summary

**QSplitter handle fixed at 1100x750 via deferred showEvent() sizing, reduced minimumWidth, and scoped gradient CSS with collapse-aware handle hiding across all three themes**

## Performance

- **Duration:** 2 min
- **Started:** 2026-03-01T18:39:06Z
- **Completed:** 2026-03-01T18:41:19Z
- **Tasks:** 2
- **Files modified:** 3

## Accomplishments

- Fixed root cause of sidebar resize deadlock at 1100x750: `setSizes()` now deferred to `showEvent()` with a guard flag so it runs after Qt's layout pass
- Reduced sidebar `minimumWidth` from 200 to 150 to give the splitter 50px more drag range at standard window size
- Added scoped gradient-line CSS to all three themes (dark, light, high-contrast) with hover state brightening, isolated to `QSplitter#main_splitter` only
- Handle disappears (`setHandleWidth(0)`) when sidebar is collapsed and reappears (`setHandleWidth(9)`) on expand — no phantom grab zone in collapsed state
- Added `is_collapsed()` accessor to `EncounterSidebarDock` and `setObjectName("main_splitter")` to enable scoped CSS targeting

## Task Commits

Each task was committed atomically:

1. **Task 1: Fix constraint deadlock and deferred splitter initialization** - `49545d7` (feat)
2. **Task 2: Style handle with themed gradient line, hover state, and collapsed-state hiding** - `b7631a1` (feat)

**Plan metadata:** *(created in final commit)*

## Files Created/Modified

- `src/ui/app.py` - showEvent() lifecycle method, setObjectName on splitter, removed early setSizes(), collapse toggle with handle width management
- `src/ui/encounter_sidebar.py` - minimumWidth reduced to 150, resizeEvent threshold updated, is_collapsed() accessor added
- `src/ui/theme_service.py` - QSplitter#main_splitter scoped CSS added to all three preset stylesheets

## Decisions Made

- **showEvent() deferred sizing:** Removed `setSizes()` from `_load_persisted_data()` which ran before Qt had measured real widget geometry. `showEvent()` guard flag `_splitter_initialized` runs once on first show.
- **setObjectName("main_splitter"):** Required for `QSplitter#main_splitter::handle:horizontal` CSS scoping. Without it, the CSS would affect all QSplitters in the app.
- **minimumWidth 150 not 200:** Reduces the floor constraint, giving the splitter more drag range at 1100px. Threshold updated in `resizeEvent()` and `set_expanded_width()` to match.
- **setHandleWidth(0/9) toggling:** Programmatic width overrides CSS when collapsed to zero — simpler than toggling inline stylesheets and avoids CSS specificity issues.
- **Gradient center line CSS:** `qlineargradient` with transparent stops around center renders a 1-2px visible line within a 9px invisible grab zone — discoverable but not intrusive.

## Deviations from Plan

None - plan executed exactly as written.

## Issues Encountered

None. The plan accurately described the root causes and fixes. All changes worked as expected.

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness

- Sidebar handle fix complete — the resize interaction works at all window sizes
- Three-theme styling is consistent and isolated via object name scoping
- No known blockers for subsequent phases

## Self-Check: PASSED

- `src/ui/app.py` — FOUND
- `src/ui/encounter_sidebar.py` — FOUND
- `src/ui/theme_service.py` — FOUND
- Commit `49545d7` — FOUND
- Commit `b7631a1` — FOUND
- Key patterns verified: `showEvent`, `is_collapsed`, `setObjectName("main_splitter")`, `setHandleWidth(0)`, `setHandleWidth(9)`, `setMinimumWidth(150)`, `QSplitter#main_splitter` in all 3 themes

---
*Phase: 17-sidebar-handle-fix*
*Completed: 2026-03-01*
