---
phase: 16-buff-system-output-improvements
plan: "04"
subsystem: ui
tags: [hp-bar, pyside6, qpainter, combat-tracker]

# Dependency graph
requires:
  - phase: 11-combat-tracker-ui
    provides: HpBar widget with QPainter paintEvent in src/ui/hp_bar.py
provides:
  - HpBar with 5-band color system (bright green, green-yellow, yellow, orange, red, grey)
  - Always-visible descriptive text overlay on HP bar (Uninjured, Barely Injured, Injured, Badly Injured, Near Death)
  - Defeated state: full grey bar with no label text
affects:
  - Any phase that renders CombatantCard or GroupCard (HP bar display changes are global)

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "HP band thresholds: 0=defeated, <=0.25=near death, <=0.50=badly injured, <=0.75=injured, <1.0=barely injured, 1.0=uninjured"
    - "Descriptive text drawn with shadow+white QPainter approach for readability on all color bands"

key-files:
  created: []
  modified:
    - src/ui/hp_bar.py

key-decisions:
  - "Font size set to 7pt (down from 8pt) to accommodate longest label 'Badly Injured' (13 chars) in 24px bar height"
  - "Defeated state fills full bar with grey (#666666) rather than leaving it as background (#333333) — visible distinction from zero-fill"
  - "No HP numbers shown — description-only text locked per plan specification"
  - "label='' for defeated state; if-label guard skips all QPainter text calls cleanly"

patterns-established:
  - "HP band label logic: if/elif chain on hp_pct, assign both color and label string together"

requirements-completed:
  - COMBAT-UX-01
  - COMBAT-UX-02

# Metrics
duration: 2min
completed: 2026-02-28
---

# Phase 16 Plan 04: HP Bar Descriptive Labels Summary

**HpBar upgraded to 5-band color system with always-visible descriptive health labels (Uninjured through Near Death) replacing raw HP numbers**

## Performance

- **Duration:** ~2 min
- **Started:** 2026-02-28T17:41:57Z
- **Completed:** 2026-02-28T17:43:00Z
- **Tasks:** 1
- **Files modified:** 1

## Accomplishments
- Replaced 3-band (green/yellow/red) HP bar color logic with 5-band + defeated system covering all D&D health thresholds
- Replaced raw HP number text (`"12 / 40"`) with always-visible descriptive labels matching each color band
- Defeated state (0 HP) renders as full grey bar with no text — clean DM-screen distinction
- Temp HP blue segment and click-to-damage-input behavior unchanged

## Task Commits

Each task was committed atomically:

1. **Task 1: HP bar 5-band color system with descriptive text overlay** - `0bd6140` (feat)

**Plan metadata:** _(created with docs commit below)_

## Files Created/Modified
- `src/ui/hp_bar.py` - paintEvent updated: 5-band color bands + descriptive label text overlay, defeated grey state

## Decisions Made
- Font size reduced from 8pt to 7pt to fit "Badly Injured" (13 chars) within the 24px bar without clipping on narrow cards
- Defeated state explicitly fills full bar with grey (#666666) over the #333333 background for a clear defeated visual
- `label = ""` combined with `if label:` guard cleanly skips all text-drawing code for defeated combatants

## Deviations from Plan

None - plan executed exactly as written.

## Issues Encountered

None. Two pre-existing test failures (`test_buff_item_round_trip`, `test_modified_monsters_round_trip_with_equipment_and_buffs`) are unrelated to this plan — they fail because `BuffItem.targets` field does not yet exist (that's work for Plans 16-01 to 16-03). All 508 other tests pass.

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness
- HP bar descriptive labels are live for all combatants in the Combat Tracker
- Requires visual verification in app (start combat, check all 5 bands render correctly with correct labels)
- Phase 16 Plan 05 (if any) can proceed; no blockers introduced

---
*Phase: 16-buff-system-output-improvements*
*Completed: 2026-02-28*
