---
phase: 03-attack-roller
plan: 04
subsystem: ui
tags: [pyside6, qmainwindow, qtabwidget, signal, cross-tab, entry-point]

# Dependency graph
requires:
  - phase: 03-attack-roller-03
    provides: AttackRollerTab, RollOutputPanel widgets

provides:
  - MainWindow (QMainWindow with QTabWidget: Library + Attack Roller tabs)
  - monster_selected Signal on MonsterLibraryTab for cross-tab wiring
  - src/main.py application entry point (python src/main.py)
  - End-to-end DM workflow: select monster in Library, roll attacks in Attack Roller

affects:
  - 04-saving-throws
  - 05-macro-system
  - 06-settings
  - 07-packaging

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "MainWindow owns shared Roller + MonsterLibrary; passes them to tabs at construction"
    - "Cross-tab signal wired AFTER both tabs constructed (avoids signal-before-init pitfall)"
    - "monster_selected = Signal(object) class-level on MonsterLibraryTab; emit after detail panel update"

key-files:
  created:
    - src/ui/app.py
    - src/main.py
  modified:
    - src/ui/library_tab.py

key-decisions:
  - "MainWindow connects monster_selected AFTER both tabs are constructed — avoids accessing tab refs before __init__ completes"
  - "Roller(random.Random()) constructed once in MainWindow; unseeded for now; Phase 6 wires seed"
  - "MonsterLibrary constructed in MainWindow, passed to MonsterLibraryTab — consistent with existing tab API"

patterns-established:
  - "Application entry point: QApplication in main(), MainWindow.show(), sys.exit(app.exec())"
  - "Shared session state (Roller, MonsterLibrary) owned by MainWindow, injected into tabs as constructor args"

requirements-completed: [ATTACK-01, ATTACK-11]

# Metrics
duration: 2min
completed: 2026-02-24
---

# Phase 3 Plan 04: Wire-up and End-to-End Verification Summary

**QTabWidget MainWindow wires Library + Attack Roller tabs via monster_selected Signal; `python src/main.py` launches full DM workflow**

## Performance

- **Duration:** ~2 min
- **Started:** 2026-02-24T01:03:25Z
- **Completed:** 2026-02-24T01:05:00Z
- **Tasks:** 2 of 2 complete
- **Files modified:** 3

## Accomplishments
- Added `monster_selected = Signal(object)` to `MonsterLibraryTab` and emit in `_on_selection_changed`
- Created `src/ui/app.py` with `MainWindow(QMainWindow)` — QTabWidget with Library and Attack Roller tabs, shared Roller and MonsterLibrary, cross-tab signal wiring
- Created `src/main.py` entry point (`QApplication` + `MainWindow.show()` + `sys.exit(app.exec())`)
- All 276 existing tests continue to pass (no regressions)

## Task Commits

Each task was committed atomically:

1. **Task 1: Add monster_selected signal, create MainWindow + main.py** - `9f0fb0c` (feat)
2. **Task 2: End-to-end verification checkpoint** - APPROVED by human verifier

## Files Created/Modified
- `src/ui/library_tab.py` — Added `Signal` import, `monster_selected = Signal(object)` class attr, emit in `_on_selection_changed`
- `src/ui/app.py` — New file: MainWindow with QTabWidget, shared Roller + Library, cross-tab signal wiring
- `src/main.py` — New file: application entry point

## Decisions Made
- MainWindow connects `monster_selected` after both tabs are constructed to avoid signal-before-init
- `Roller(random.Random())` — unseeded; Phase 6 will wire the global seed
- `MonsterLibrary` constructed in MainWindow and passed down — consistent with existing tab API pattern

## Deviations from Plan

None - plan executed exactly as written.

## Issues Encountered

None.

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness
- App launches with `python src/main.py` — all Phase 3 components wired together
- Human verification (Task 2) must pass before Phase 3 is considered complete
- Phase 4 (Saving Throws) can begin once Task 2 is approved

---
*Phase: 03-attack-roller*
*Completed: 2026-02-24*

## Self-Check: APPROVED — Phase 3 complete
