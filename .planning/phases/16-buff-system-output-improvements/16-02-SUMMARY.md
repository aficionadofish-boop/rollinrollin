---
phase: 16-buff-system-output-improvements
plan: 02
subsystem: ui
tags: [PySide6, buffs, BonusDiceEntry, RollRequest, SaveParticipant, attack-roller, saves-tab]

# Dependency graph
requires:
  - phase: 16-01
    provides: BuffItem.affects_attacks and affects_saves boolean fields used to gate injection

provides:
  - BonusDiceEntry objects injected into RollRequest.bonus_dice from monster buffs with affects_attacks=True
  - BonusDiceEntry objects injected into SaveParticipant.bonus_dice from monster buffs with affects_saves=True
  - SaveParticipant.bonus_dice field for per-participant buff dice in save rolls
  - SaveRollService merges participant.bonus_dice with request.bonus_dice during roll
  - _format_bonus_dice_part() helper: full label on first attack, abbreviated on subsequent
  - Bold creature/attack header prepended to attack output in _render_results()
  - Per-damage-type colored subtotals in COMPARE mode summary when multiple types present
  - Save result rows show buff breakdown with full label on first row, abbreviated on subsequent

affects: [16-03-save-injection, future-buff-plans]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Buff dice injection: filter monster.buffs by affects_X boolean, map to BonusDiceEntry(formula, label)"
    - "First/subsequent label pattern: is_first=True shows '+ Bless 1d4(3)', subsequent shows '+ 1d4(2)'"
    - "Per-participant bonus dice: SaveParticipant.bonus_dice merged with global request.bonus_dice in service"

key-files:
  created: []
  modified:
    - src/ui/attack_roller_tab.py
    - src/encounter/models.py
    - src/encounter/service.py
    - src/ui/encounters_tab.py

key-decisions:
  - "_format_bonus_dice_part() uses 'd' presence in dice_notation to distinguish dice vs flat bonuses; flat bonuses show '+ Bless(+2)' on first, '+2' on subsequent"
  - "SaveParticipant.bonus_dice field added (not SaveRequest) so each participant gets their own monster's buffs independently"
  - "_execute_roll() injects save buffs during feature detection loop to cover CT 'Send to Saves' path; sidebar path already covered by _expand_participants()"
  - "_render_results() passes result.attack_rolls to _format_summary_html() for per-type aggregation; buff totals intentionally excluded from summary"
  - "Damage type summary only shown when len(type_totals) > 1 — single type breakdown is redundant with total"
  - "is_first determined by row_idx == 0 in _execute_roll() loop (first participant result row gets full labels)"

patterns-established:
  - "Monster buff injection pattern: getattr(monster, 'buffs', []) + filter by affects_X + BonusDiceEntry(formula=buff.bonus_value, label=buff.name)"
  - "is_first label abbreviation: check attack_number or row_idx to show full label only once per roll group"

requirements-completed: [BUFF-02, BUFF-03, OUT-01, OUT-02]

# Metrics
duration: 5min
completed: 2026-02-28
---

# Phase 16 Plan 02: Buff Injection & Output Improvements Summary

**Buff dice auto-injected into attack and save rolls from monster.buffs boolean fields, with labeled output (full on first, abbreviated on subsequent), bold attack header, and per-damage-type colored summary**

## Performance

- **Duration:** 5 min
- **Started:** 2026-02-28T17:48:53Z
- **Completed:** 2026-02-28T17:53:48Z
- **Tasks:** 2
- **Files modified:** 4

## Accomplishments

- Monster buffs with affects_attacks=True are now injected as BonusDiceEntry objects into RollRequest.bonus_dice, making the d4 (or other bonus) actually roll and add to each attack's to-hit total
- First attack line shows `+ Bless 1d4(3)` (full label + formula + result), subsequent attacks show `+ 1d4(2)` (abbreviated); flat bonuses handled separately
- Bold header `Young Red Dragon — Bite (5x)` prepended to attack output; stored on self._last_header so mode switches re-render correctly
- COMPARE mode summary shows per-damage-type colored subtotals `(e.g. 18 slashing, 12 fire)` when multiple damage types present; buff totals excluded per spec
- SaveParticipant gains bonus_dice field; SaveRollService merges per-participant and global bonus dice; save result rows mirror attack format for buff labels

## Task Commits

Each task was committed atomically:

1. **Task 1: Attack buff injection, output header, and damage type summary** - `4c9b3fb` (feat)
2. **Task 2: Save roll buff injection with matching format** - `7ba1cb9` (feat)

**Plan metadata:** (docs commit below)

## Files Created/Modified

- `src/ui/attack_roller_tab.py` - BonusDiceEntry import; _last_header/_last_monster instance vars; _make_action_row() captures monster; _on_roll() accepts monster=None and builds header; _build_roll_request() injects buff dice; _format_raw_line_html() uses _format_bonus_dice_part(); _format_bonus_dice_part() helper; _render_results() prepends header; _format_summary_html() accepts attack_rolls and builds per-type summary
- `src/encounter/models.py` - SaveParticipant.bonus_dice field added (default empty list)
- `src/encounter/service.py` - _roll_one_participant() merges participant.bonus_dice with request.bonus_dice
- `src/ui/encounters_tab.py` - BonusDiceEntry import; _expand_participants() injects save buff dice per monster; _execute_roll() injects save buffs for CT path; _SaveResultRow gains is_first param; _format_line() shows full/abbreviated buff labels

## Decisions Made

- `_format_bonus_dice_part()` checks for 'd' in dice_notation to distinguish dice formulae from flat integers; flat bonuses use `(+ Bless(+2))` on first and `(+2)` on subsequent
- `SaveParticipant.bonus_dice` (not `SaveRequest`) carries per-participant buffs so each monster's buffs apply independently; global `SaveRequest.bonus_dice` (UI manual entries) still apply to all
- `_execute_roll()` re-injects save buffs during feature detection (where monster is already looked up) to handle CT "Send to Saves" path without duplicating injection logic
- `_render_results()` passes `result.attack_rolls` to `_format_summary_html()`; summary excludes buff dice from type_totals aggregation (buff results are in bonus_dice_results, not damage_parts)
- Damage type breakdown only rendered when `len(type_totals) > 1` — single-type breakdown would duplicate the total
- `is_first=(row_idx == 0)` determines first participant row in `_execute_roll()` loop for save label abbreviation

## Deviations from Plan

None - plan executed exactly as written. The save pipeline already had `bonus_dice` on `SaveRequest` and `bonus_dice_results` on `SaveParticipantResult`, so the only model change needed was adding `bonus_dice` to `SaveParticipant`.

## Issues Encountered

None — the existing BonusDiceEntry infrastructure and parallel service patterns (RollService vs SaveRollService) made implementation straightforward. All 514 tests pass after both tasks.

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness

- Attack rolls now inject buff dice from monster.buffs via BonusDiceEntry — Plans 03+ can extend this pattern
- Save rolls mirror attack rolls exactly for buff injection and formatting
- The affects_attacks/affects_saves boolean fields from Plan 01 are fully wired into roll calculations
- Damage type summary and attack header infrastructure is in place for future output improvements

## Self-Check: PASSED

- [x] `src/ui/attack_roller_tab.py` — FOUND
- [x] `src/encounter/models.py` — FOUND
- [x] `src/encounter/service.py` — FOUND
- [x] `src/ui/encounters_tab.py` — FOUND
- [x] `.planning/phases/16-buff-system-output-improvements/16-02-SUMMARY.md` — FOUND
- [x] Commit `4c9b3fb` — FOUND (feat(16-02): attack buff injection, output header, and damage type summary)
- [x] Commit `7ba1cb9` — FOUND (feat(16-02): save roll buff injection with matching format)
- [x] 514 tests pass — VERIFIED

---
*Phase: 16-buff-system-output-improvements*
*Completed: 2026-02-28*
