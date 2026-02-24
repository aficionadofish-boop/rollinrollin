---
phase: 03-attack-roller
plan: 02
subsystem: ui
tags: [pyside6, qwidget, toggle, bonus-dice, signal]

# Dependency graph
requires:
  - phase: 03-attack-roller/03-01
    provides: src/roll/models.py with BonusDiceEntry dataclass used by BonusDiceList.get_entries()
provides:
  - ToggleBar(QWidget) — exclusive multi-button toggle group with value_changed Signal
  - BonusDiceList(QWidget) — dynamic add/remove bonus dice formula rows
affects:
  - 03-attack-roller/03-03  # AttackRollerTab assembles both widgets

# Tech tracking
tech-stack:
  added: []
  patterns:
    - ToggleBar pattern: QHBoxLayout of checkable QPushButtons with mutual exclusivity enforced via _on_click()
    - BonusDiceList pattern: QVBoxLayout with rows inserted before anchor '+' button via insertWidget(count-1)
    - Lazy import in get_entries() avoids circular Qt/model dependency

key-files:
  created:
    - src/ui/toggle_bar.py
    - src/ui/bonus_dice_list.py
  modified: []

key-decisions:
  - "ToggleBar default falls back to options[0] if provided default not in options dict — safe guard against caller typo"
  - "BonusDiceList.get_entries() lazy-imports BonusDiceEntry from src.roll.models to avoid Qt circular dependency"
  - "remove_btn uses unicode minus sign (U+2212) matching the plan spec"

patterns-established:
  - "Pattern 5 (ToggleBar): reusable for RAW/COMPARE and Normal/Advantage/Disadvantage in AttackRollerTab"
  - "Pattern 6 (BonusDiceList): dynamic row list with insertWidget(count-1) to insert before anchor button"

requirements-completed: [ATTACK-05, ATTACK-07, ATTACK-09, ATTACK-10]

# Metrics
duration: 1min
completed: 2026-02-24
---

# Phase 3 Plan 02: ToggleBar and BonusDiceList Widget Summary

**Two reusable PySide6 widgets: ToggleBar (exclusive toggle group with Signal) and BonusDiceList (dynamic bonus dice row list with get_entries())**

## Performance

- **Duration:** 1 min
- **Started:** 2026-02-24T00:54:47Z
- **Completed:** 2026-02-24T00:55:52Z
- **Tasks:** 2
- **Files modified:** 2

## Accomplishments
- ToggleBar(QWidget) with value_changed Signal(str), mutual exclusivity via _on_click(), value() and set_value() API
- BonusDiceList(QWidget) with dynamic row add/remove, get_entries() returning BonusDiceEntry list for non-empty rows
- All 276 existing tests still pass — no regressions

## Task Commits

Each task was committed atomically:

1. **Task 1: ToggleBar widget** - `1bb8fed` (feat)
2. **Task 2: BonusDiceList widget** - `873561b` (feat)

**Plan metadata:** (docs commit — see below)

## Files Created/Modified
- `src/ui/toggle_bar.py` - Exclusive multi-button toggle group; emits value_changed(str); value() and set_value() API
- `src/ui/bonus_dice_list.py` - Dynamic bonus dice row list; _add_row()/_remove_row(); get_entries() returns BonusDiceEntry list

## Decisions Made
- ToggleBar default guard: `default if default in self._buttons else options[0]` protects against caller typo without raising
- BonusDiceList.get_entries() uses lazy import of BonusDiceEntry to avoid circular dependency (Qt widget importing pure model)
- Unicode minus sign (U+2212) used for remove button to match plan spec exactly

## Deviations from Plan

None - plan executed exactly as written.

## Issues Encountered
None.

## User Setup Required
None - no external service configuration required.

## Next Phase Readiness
- Both widgets are importable and ready for use by AttackRollerTab (Plan 03-03)
- ToggleBar will be instantiated for RAW|COMPARE mode and Normal|Advantage|Disadvantage toggles
- BonusDiceList will be wired to RollRequest.bonus_dice via get_entries() at roll time

## Self-Check: PASSED

- FOUND: src/ui/toggle_bar.py
- FOUND: src/ui/bonus_dice_list.py
- FOUND: .planning/phases/03-attack-roller/03-02-SUMMARY.md
- FOUND commit 1bb8fed (Task 1: ToggleBar widget)
- FOUND commit 873561b (Task 2: BonusDiceList widget)

---
*Phase: 03-attack-roller*
*Completed: 2026-02-24*
