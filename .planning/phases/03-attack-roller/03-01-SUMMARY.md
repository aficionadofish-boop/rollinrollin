---
phase: 03-attack-roller
plan: 01
subsystem: roll
tags: [python, dataclasses, dice-engine, tdd, pytest, d&d-5e]

# Dependency graph
requires:
  - phase: 01-dice-engine-and-domain-foundation
    provides: roll_expression(), Roller, DiceResult, DieFace — dice engine and domain models
  - phase: 02-monster-import-and-library
    provides: DamagePart, Action dataclasses from src.domain.models
provides:
  - RollService.execute_attack_roll(request, roller) -> RollResult
  - _double_dice(expr) utility for crit damage doubling
  - src/roll/ package with models and service fully importable
  - Seeded golden test suite (39 tests) covering all toggle combinations
affects:
  - 03-02 (AttackRollerTab UI — calls RollService)
  - 03-03 (main window integration — wires RollService to AttackRollerTab)

# Tech tracking
tech-stack:
  added: []
  patterns:
    - RollService DTO pattern: UI assembles RollRequest, service returns RollResult, no D&D logic in UI
    - Advantage translation: "2d20kh1" / "2d20kl1" / "1d20" passed to roll_expression(); engine stores both faces
    - Crit doubling via _double_dice regex: only NdM prefix doubled, constant bonus unchanged
    - Bonus dice formula handling: strip leading '+', detect '-' for sign, pass clean formula to roll_expression()
    - Nat-1/nat-20 check on kept DieFace.value (not d20_result.total) — Pitfall 1 avoidance
    - to_hit_bonus added as integer arithmetic (not concatenated into expression) — Pitfall 7 avoidance

key-files:
  created:
    - src/roll/__init__.py
    - src/roll/models.py
    - src/roll/service.py
    - src/tests/test_roll_service.py
  modified: []

key-decisions:
  - "RollRequest uses to_hit_bonus: int (not a formula string) — d20 rolled separately, bonus added as integer to avoid ParseError on negative bonuses"
  - "_double_dice() uses regex to double only leading NdM count; constant bonuses (+3) are left unchanged per 5e crit rules"
  - "Nat-1/nat-20 extracted from DieFace.kept=True in DiceResult.faces (not from d20_result.total) for correctness with advantage/disadvantage"
  - "Bonus dice formula: strip leading '+' before roll_expression(); sign detected from formula.startswith('-')"
  - "COMPARE mode damage gating: is_hit must be True (not just truthy) before rolling damage"

patterns-established:
  - "RollService DTO: UI only assembles RollRequest and renders RollResult — zero D&D rule logic in UI layer"
  - "TDD RED-GREEN-REFACTOR: test file committed first (ImportError), then implementation makes all 39 pass"
  - "Seeded roller pattern: Roller(random.Random(seed)) injected into service for deterministic test coverage"

requirements-completed: [ATTACK-02, ATTACK-03, ATTACK-04, ATTACK-05, ATTACK-06, ATTACK-07, ATTACK-08, ATTACK-09, ATTACK-10, ATTACK-12]

# Metrics
duration: 10min
completed: 2026-02-24
---

# Phase 3 Plan 01: Roll Models and RollService (TDD) Summary

**Pure-Python 5e attack roll service (RollService) with advantage/disadvantage, nat-1/nat-20 overrides, crit doubling, flat modifier, and bonus dice — all covered by 39 seeded golden tests**

## Performance

- **Duration:** ~10 min
- **Started:** 2026-02-24T00:00:00Z
- **Completed:** 2026-02-24T00:10:00Z
- **Tasks:** 1 (TDD feature: RED + GREEN phases)
- **Files modified:** 4

## Accomplishments

- Built `src/roll/` package: `__init__.py`, `models.py`, `service.py` — all importable, no Qt dependencies
- `RollService.execute_attack_roll(request, roller)` correctly handles all 12 toggle combinations (advantage, disadvantage, nat-1, nat-20, crit, flat modifier, bonus dice, COMPARE/RAW mode)
- `_double_dice()` utility doubles only dice count, leaving constant bonus unchanged (e.g. "2d6+3" -> "4d6+3")
- 39 new tests pass; 237 existing tests unaffected — total 276 passing

## Task Commits

Each task was committed atomically:

1. **RED phase: Failing test suite** - `6304f0e` (test)
2. **GREEN phase: RollService implementation** - `2269a3c` (feat)

_Note: TDD tasks have two commits (test -> feat). No refactor commit was needed — code was clean on first pass._

## Files Created/Modified

- `src/roll/__init__.py` - Package marker for src.roll module
- `src/roll/models.py` - RollRequest, AttackRollResult, DamagePartResult, RollSummary, RollResult, BonusDiceEntry dataclasses
- `src/roll/service.py` - RollService.execute_attack_roll() with full 5e logic + _double_dice() utility
- `src/tests/test_roll_service.py` - 39 seeded golden tests covering all toggle combinations

## Decisions Made

- **to_hit_bonus as int, not formula string:** `RollRequest.to_hit_bonus: int` — d20 rolled separately, bonus added as Python integer. Avoids ParseError when bonus is negative (e.g., -2 would produce "1d20+-2" which the lexer rejects).
- **_double_dice regex approach:** `^(\d+)(d\d+)` matches only the leading NdM prefix. `re.sub(..., count=1)` ensures only the first dice group is affected. Constant bonuses are untouched per 5e rules.
- **Nat-1/nat-20 from DieFace, not total:** `kept_face = next(f for f in d20_result.faces if f.kept)` — extracts the natural value from the physically kept die. Avoids the pitfall of checking d20_result.total which includes bonuses.
- **Damage gating uses `is_hit is True`:** In COMPARE mode, `if request.mode == "raw" or is_hit is True:` — not `is_hit` (truthy check would fail on None in RAW mode, but `is True` is explicit and correct).
- **Bonus dice sign from formula prefix:** Strip leading `+` with `lstrip('+')` before passing to roll_expression; detect negative sign from `formula.startswith('-')` on the original formula.

## Deviations from Plan

None - plan executed exactly as written.

## Issues Encountered

None. Implementation matched the RESEARCH.md Pattern 2 skeleton closely. All 39 tests passed on first run after implementation.

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness

- `src/roll/` package is complete and independently tested
- `RollService.execute_attack_roll(request, roller) -> RollResult` is the clean API for Phase 3 Plan 02 (AttackRollerTab UI)
- All dataclasses (`RollRequest`, `AttackRollResult`, `DamagePartResult`, `RollSummary`, `RollResult`, `BonusDiceEntry`) are importable from `src.roll.models`
- No blockers for Phase 3 Plan 02

---
*Phase: 03-attack-roller*
*Completed: 2026-02-24*
