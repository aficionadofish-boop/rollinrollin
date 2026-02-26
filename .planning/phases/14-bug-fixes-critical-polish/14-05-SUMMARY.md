---
phase: 14-bug-fixes-critical-polish
plan: 05
subsystem: ui
tags: [pyside6, combat-tracker, saves-tab, legendary-resistance, hp-bar, stats-toggle]

requires:
  - phase: 12-save-roller-legendary-resistance
    provides: LR counter architecture (_lr_counters dict, _on_lr_used signal, reset_lr_counters)
  - phase: 11-combat-tracker-card-ui
    provides: CombatantCard.set_stat_visible, _visible_stats dict, stats menu in CombatTrackerTab
provides:
  - Working stats toggle menu in Combat Tracker (triggered signal replaces exec() return check)
  - LR counters that persist across multiple save rolls in the same encounter
  - LR counter seeded at max on first detection (was never tracked before)
  - Encounter type-change detection for LR reset (prev names set comparison)
  - Verified 0 HP behavior: grey bar, healing works, floor at 0 confirmed correct
affects: [phase-15, phase-16, saves-tab, combat-tracker]

tech-stack:
  added: []
  patterns:
    - "QMenu checkable actions: use action.triggered.connect(lambda checked, key=k: ...) not menu.exec() return value"
    - "LR counter pattern: seed _lr_counters[name] at first detection, decrement on use, reset on type-set change"

key-files:
  created: []
  modified:
    - src/ui/combat_tracker_tab.py
    - src/ui/combatant_card.py
    - src/ui/encounters_tab.py
    - src/ui/app.py

key-decisions:
  - "BUG-11: QMenu.exec() in PySide6 returns None for checkable action toggles — fix uses triggered(bool) signal per action"
  - "_toggle_stat() is a new helper method on CombatTrackerTab for signal-based stat visibility updates"
  - "BUG-15 root cause was dual: (1) reset on every encounter_changed (not just type changes), (2) _lr_counters never seeded so _on_lr_used could not decrement from max"
  - "LR counter seeding: if base_name not in _lr_counters on roll execution, set _lr_counters[base_name] = lr_uses (from feature detection)"
  - "Encounter type-change detection uses set comprehension {monster.name for monster, _ in members} compared to _prev_encounter_names"
  - "BUG-16 (0 HP): service.py apply_damage already correct (max(0,...)); HpBar already shows grey at 0 HP; is_defeated is a property — no code changes needed"

requirements-completed: [BUG-11, BUG-15, BUG-16]

duration: 25min
completed: 2026-02-26
---

# Phase 14 Plan 05: Stats Toggle, LR Counter Persistence, 0 HP Behavior Summary

**Stats toggle wired via triggered signals (was broken by exec() return value); LR counters now persist and seed correctly across save rolls; 0 HP behavior verified correct**

## Performance

- **Duration:** ~25 min
- **Started:** 2026-02-26T22:25:00Z
- **Completed:** 2026-02-26T22:50:00Z
- **Tasks:** 2
- **Files modified:** 4

## Accomplishments

- Fixed BUG-11: Stats toggle menu now uses `action.triggered.connect()` per checkable action instead of relying on `menu.exec()` return value (which returns None in PySide6 for checkable action toggles)
- Fixed BUG-15 (dual root cause): encounter type-change tracking in `_on_sidebar_encounter_changed` prevents spurious LR resets on count adjustments; LR counter now seeded at max on first detection so `_on_lr_used` can actually decrement
- Added `_toggle_stat()` helper method on `CombatTrackerTab` for clean signal-based stat visibility
- Verified BUG-16 correct: `apply_damage()` floors at 0, `HpBar` shows grey background at 0 HP, `is_defeated` is a property not a mutable flag — no changes needed

## Task Commits

1. **Task 1: Fix stats toggle visibility in Combat Tracker** - `3e925b6` (fix)
2. **Task 2: Fix LR counter persistence and 0 HP behavior** - `0efed7a` (fix)

**Plan metadata:** (this commit)

## Files Created/Modified

- `src/ui/combat_tracker_tab.py` - Rewired stats menu to use triggered signals; added _toggle_stat() helper
- `src/ui/combatant_card.py` - Pre-existing fix for condition chip rebuild + active border style
- `src/ui/encounters_tab.py` - Seed _lr_counters on first detection; always use persisted value
- `src/ui/app.py` - Track _prev_encounter_names; reset LR only on monster type-set change

## Decisions Made

- **QMenu triggered signal pattern**: PySide6 `menu.exec()` returns `None` for checkable action clicks (the click toggles the checked state but does not "select" the item in the traditional sense). Fix is to connect `action.triggered.connect(lambda checked, key=k: ...)` with key captured by value.
- **LR counter seeding**: `_lr_counters` was never initialized — `_on_lr_used` used `get(name, 0)` default so `0 > 0` was always False and nothing was stored. Fix seeds the dict on first execution.
- **BUG-16 no-op**: All three 0 HP behaviors were already correct in code. Service floors at 0, HpBar background is #333 (grey) when `hp_width == 0`, healing adds to `current_hp` correctly.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] LR counter _on_lr_used decrement was broken: counter never seeded**
- **Found during:** Task 2 (Fix LR counter persistence)
- **Issue:** `_lr_counters` only decremented in `_on_lr_used` but was never initialized; `get(name, 0)` returned 0 every time so `0 > 0` guard prevented any write
- **Fix:** Added counter seeding in `_execute_roll`: `if base_name not in _lr_counters: _lr_counters[base_name] = lr_uses`
- **Files modified:** `src/ui/encounters_tab.py`
- **Verification:** Import check passes; logic trace confirms counter correctly tracks across multiple rolls
- **Committed in:** `0efed7a` (Task 2 commit)

---

**Total deviations:** 1 auto-fixed (Rule 1 - Bug)
**Impact on plan:** Essential correctness fix. Without seeding, LR counters appeared to work visually (spinbox decrements in the row) but the session-level counter in `_lr_counters` was never updated, so subsequent rolls always showed max LR.

## Issues Encountered

None - both bugs had clear root causes and targeted fixes.

## Next Phase Readiness

- Stats toggle working: DM can now show/hide Speed, Passive Perception, LR, LA, Regen on combatant cards
- LR tracking working: DM can track LR usage across multiple save rolls in a boss fight
- Ready for Plan 06 (final polish / remaining bugs in phase 14)

---
*Phase: 14-bug-fixes-critical-polish*
*Completed: 2026-02-26*
