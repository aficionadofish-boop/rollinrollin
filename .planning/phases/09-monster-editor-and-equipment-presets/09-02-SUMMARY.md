---
phase: 09-monster-editor-and-equipment-presets
plan: 02
subsystem: testing
tags: [dnd5e, equipment, math, tdd, pytest, pure-python]

# Dependency graph
requires:
  - phase: 09-01
    provides: "WeaponData, ArmorData, SRD_WEAPONS, SRD_ARMORS, SIZE_DICE_MULTIPLIER in src/equipment/data.py; Monster.size, Action.damage_bonus fields in domain/models.py"
provides:
  - "EquipmentService with compute_weapon_action, compute_armor_ac, compute_shield_bonus, compute_focus_bonus"
  - "scale_dice() module-level helper for weapon dice size scaling"
  - "49-test TDD suite covering EQUIP-01 through EQUIP-08"
affects:
  - "09-03 (MonsterEditorDialog) — will call EquipmentService methods when equipping weapons/armor"
  - "09-04 (Equipment section UI) — auto-action generation uses compute_weapon_action output dict"
  - "09-05 (persistence round-trip) — equipment math drives the persisted action state"

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "TDD (RED → GREEN) for pure-Python service math"
    - "Inline _PROF_BY_CR table in EquipmentService avoids coupling to MonsterMathEngine internals"
    - "Finesse ability selection: max(STR_mod, DEX_mod); ranged always DEX; thrown non-finesse STR"
    - "scale_dice() splits NdM, multiplies N by SIZE_DICE_MULTIPLIER[size], returns {N*mult}d{M}"

key-files:
  created:
    - src/equipment/service.py
    - src/tests/test_equipment_service.py
  modified: []

key-decisions:
  - "EquipmentService computes _PROF_BY_CR inline (copied from engine.py) — avoids coupling to MonsterMathEngine which requires a fully-formed Monster object"
  - "scale_dice() is a module-level function (not a method) to allow standalone import by other services"
  - "compute_armor_ac str_requirement_met uses >= comparison: monster.ability_scores.get('STR', 10) >= armor.str_requirement; str_requirement=0 means always met"
  - "Ranged non-thrown weapons always use DEX regardless of STR; thrown non-finesse use STR (not ranged DEX rule)"

patterns-established:
  - "EquipmentService returns plain dicts (not dataclasses) for easy JSON serialization in persistence layer"
  - "Weapon action result always includes is_equipment_generated=True for UI distinction from parsed actions"

requirements-completed:
  - EQUIP-01
  - EQUIP-02
  - EQUIP-03
  - EQUIP-04
  - EQUIP-05
  - EQUIP-06
  - EQUIP-07
  - EQUIP-08

# Metrics
duration: 4min
completed: 2026-02-25
---

# Phase 09 Plan 02: EquipmentService TDD Summary

**Pure-Python EquipmentService with 49 TDD tests covering D&D 5e weapon to-hit/damage (finesse/ranged/thrown/size-scaling), armor AC (light/medium/heavy DEX limits), shield bonus, and spellcasting focus bonus**

## Performance

- **Duration:** 4 min
- **Started:** 2026-02-25T22:24:20Z
- **Completed:** 2026-02-25T22:27:41Z
- **Tasks:** 2 (RED + GREEN)
- **Files modified:** 2

## Accomplishments

- 49 failing tests written covering all EQUIP requirements (RED phase confirmed via pytest)
- EquipmentService fully implemented with correct D&D 5e math (GREEN: all 49 pass)
- Full test suite expanded from 419 to 485 tests with zero regressions

## Task Commits

Each task was committed atomically:

1. **Task 1: RED — Write failing tests for EquipmentService** - `01358ca` (test)
2. **Task 2: GREEN — Implement EquipmentService** - `a277576` (feat)

_Note: TDD plan — two commits (test stub → full implementation)_

## Files Created/Modified

- `src/equipment/service.py` - EquipmentService with scale_dice(), compute_weapon_action(), compute_armor_ac(), compute_shield_bonus(), compute_focus_bonus()
- `src/tests/test_equipment_service.py` - 49 TDD tests grouped by requirement class (EQUIP-01 through EQUIP-08 + proficiency bonus spot-checks)

## Decisions Made

- Inline _PROF_BY_CR table in EquipmentService (copied from engine.py) — avoids coupling to MonsterMathEngine which needs a full Monster and returns a DerivedStats object; simpler to keep inline for this pure-math service
- scale_dice() is a module-level function (not instance method) for standalone import
- compute_armor_ac str_requirement_met: `str_score >= armor.str_requirement`; since str_requirement=0 for no-requirement armor, this correctly returns True for any monster STR

## Deviations from Plan

None — plan executed exactly as written. Plan 01's prerequisite artifacts (equipment/data.py, domain model extensions) were already committed from a prior partial execution before this session.

## Issues Encountered

None. The prerequisite Plan 01 Task 1 commit (`758c52a`) had already been made before this session, so all required imports (WeaponData, ArmorData, SRD_WEAPONS, SRD_ARMORS, SIZE_DICE_MULTIPLIER, Monster.size) were available immediately.

## Next Phase Readiness

- EquipmentService is the math backbone for Plans 03-05
- Plan 03 (MonsterEditorDialog skeleton) can proceed immediately — no EquipmentService blockers
- Plan 04 (Equipment section UI + auto-action generation) will call `svc.compute_weapon_action()` and place result dict into monster's actions list
- Plan 05 (persistence round-trip) will serialize EquipmentItem entries that drive these computations

---
*Phase: 09-monster-editor-and-equipment-presets*
*Completed: 2026-02-25*
