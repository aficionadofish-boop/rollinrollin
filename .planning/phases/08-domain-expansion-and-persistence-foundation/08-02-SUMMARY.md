---
phase: 08-domain-expansion-and-persistence-foundation
plan: 02
subsystem: testing
tags: [python, tdd, monster-math, validation, spellcasting, d&d-5e, dataclass, enum]

# Dependency graph
requires:
  - phase: 08-domain-expansion-and-persistence-foundation (plan 01)
    provides: domain models (Monster, Action, DamagePart) used as engine input

provides:
  - MonsterMathEngine.recalculate(): DerivedStats with proficiency bonus and all save tiers
  - MathValidator.validate_saves(): NON_PROFICIENT/PROFICIENT/EXPERTISE/CUSTOM classification
  - MathValidator.validate_action(): independent to-hit and damage bonus validation with STR/DEX heuristic
  - MathValidator.validate_spellcasting(): attack and DC validation with focus bonus support
  - SpellcastingDetector.detect(): casting ability extraction from trait text + highest mental stat fallback
  - SaveState str enum for JSON-serializable save classification
  - 37 new tests covering all MATH requirements

affects:
  - Phase 9 Monster Editor (will use engine for live recalculation and validator for mismatch flagging)
  - Any future UI that displays derived stats or flags bonuses

# Tech tracking
tech-stack:
  added: []
  patterns:
    - TDD RED/GREEN cycle with separate commits per phase
    - Pure function engine design (recalculate never mutates input)
    - str,Enum for JSON-serializable enums
    - getattr with None default for forward-compat attribute access on domain models
    - Property-based is_flagged on dataclasses (computed from fields, not stored)
    - Fallback priority chain (explicit parsing -> highest mental stat)

key-files:
  created:
    - src/monster_math/__init__.py
    - src/monster_math/engine.py
    - src/monster_math/validator.py
    - src/monster_math/spellcasting.py
    - src/tests/test_monster_math.py
  modified: []

key-decisions:
  - "damage_bonus accessed via getattr(action, 'damage_bonus', None) — forward-compat for when Action domain model adds the field formally"
  - "SpellcastingInfo defined in spellcasting.py (runtime detection result) separately from any domain model version (persistence) — import from spellcasting for math operations"
  - "SaveState uses (str, Enum) — enables JSON serialization without extra conversion step"
  - "Fallback mental stat priority: WIS > INT > CHA by score comparison, WIS as default if none present"
  - "damage expected = ability_mod only (no proficiency) — per D&D 5e rules, prof applies to attack roll not damage"

patterns-established:
  - "Property is_flagged: computed on dataclass via @property, not stored — zero-cost flag computation"
  - "Pure engine pattern: recalculate() takes Monster, returns DerivedStats, never stores state or mutates"
  - "Ability heuristic: Ranged in raw_text → DEX; finesse in raw_text + DEX>STR → DEX; else STR"

requirements-completed: [MATH-01, MATH-02, MATH-03, MATH-04, MATH-05]

# Metrics
duration: 18min
completed: 2026-02-25
---

# Phase 8 Plan 02: Monster Math Engine Summary

**Pure-Python math engine with TDD: MonsterMathEngine recalculates derived stats from CR and ability scores, MathValidator flags save/attack/spell mismatches, SpellcastingDetector extracts casting ability from trait text**

## Performance

- **Duration:** ~18 min
- **Started:** 2026-02-25T20:45:00Z
- **Completed:** 2026-02-25T21:03:00Z
- **Tasks:** 2 (RED + GREEN TDD phases)
- **Files modified:** 5 (3 implementation + 1 test + 1 package init)

## Accomplishments
- MonsterMathEngine with complete _PROF_BY_CR table (all CRs 0 through 30 including fractions) and _ability_mod using floor division matching D&D 5e rules
- MathValidator classifies saves as NON_PROFICIENT/PROFICIENT/EXPERTISE/CUSTOM, validates attack to-hit (mod+prof) and damage (mod only) independently, and validates spell attack bonus and DC with focus_bonus support
- SpellcastingDetector scans actions by name (case-insensitive), extracts casting ability via regex, falls back to highest mental stat (WIS/INT/CHA by score) with is_assumed flag
- 37 new tests pass; full suite 419 tests, zero regressions

## Task Commits

Each task was committed atomically:

1. **Task 1: RED phase - failing tests** - `4a9cdef` (test)
2. **Task 2: GREEN phase - implementation** - `403066c` (feat)

_Note: TDD plan — two commits per the RED/GREEN cycle._

## Files Created/Modified
- `src/monster_math/__init__.py` - Package marker
- `src/monster_math/engine.py` - _PROF_BY_CR, _ability_mod, DerivedStats, MonsterMathEngine.recalculate()
- `src/monster_math/validator.py` - SaveState, SaveValidation, ActionValidation, SpellValidation, MathValidator
- `src/monster_math/spellcasting.py` - SpellcastingInfo, SpellcastingDetector.detect()
- `src/tests/test_monster_math.py` - 37 tests covering all MATH requirements

## Decisions Made
- `damage_bonus` accessed via `getattr(action, 'damage_bonus', None)` — the Action domain model does not have this field yet; forward-compatible access avoids breaking existing code while tests can set it directly on action instances
- `SpellcastingInfo` lives in `spellcasting.py` as the runtime detection result, separate from any persistence-oriented version in domain models
- `SaveState(str, Enum)` chosen for JSON serialization compatibility with no extra conversion overhead
- Fallback mental stat priority: WIS > INT > CHA ordered by score comparison; WIS is the default when no mental stats are in ability_scores
- Damage expected = ability_mod only (no prof) — core D&D 5e rule: proficiency bonus applies to attack rolls, not damage rolls

## Deviations from Plan

None - plan executed exactly as written.

## Issues Encountered

None.

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness
- All three math modules fully tested and ready for Phase 9 Monster Editor integration
- MonsterMathEngine.recalculate() is the live recalculation hook for QSpinBox value changes in the editor
- MathValidator is the mismatch detection service for the editor's flag display
- SpellcastingDetector enables the editor to auto-detect and pre-populate spell section fields
- Action.damage_bonus field will need to be formally added to the domain model (models.py) before full editor integration

---
*Phase: 08-domain-expansion-and-persistence-foundation*
*Completed: 2026-02-25*
