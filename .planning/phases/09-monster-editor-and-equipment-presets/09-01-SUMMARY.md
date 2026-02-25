---
phase: 09-monster-editor-and-equipment-presets
plan: 01
subsystem: domain
tags: [dataclasses, srd-data, parser, testing, d&d-5e, equipment]

requires:
  - phase: 08-domain-expansion-and-persistence-foundation
    provides: MonsterModification persistence layer, SpellcastingInfo, Monster domain model base

provides:
  - Monster.size field (default "Medium") with parser extraction from statblock type line
  - Monster.skills dict field with parser extraction from Skills line
  - Action.damage_bonus and Action.is_equipment_generated formal fields
  - EquipmentItem and BuffItem dataclasses with full asdict() round-trip
  - MonsterModification extended with skills, hp_formula, size, equipment, buffs, actions fields
  - MonsterModification.from_dict() classmethod handling old and new JSON formats
  - SKILL_TO_ABILITY constant dict mapping all 18 D&D 5e skills
  - SRD_WEAPONS (33 entries), SRD_ARMORS (12 entries), SIZE_DICE_MULTIPLIER in src/equipment/data.py
  - WeaponData and ArmorData dataclasses

affects:
  - 09-02 (EquipmentService uses WeaponData, ArmorData, SIZE_DICE_MULTIPLIER, Monster.size)
  - 09-03 (MonsterEditorDialog uses Monster.size, Monster.skills, MonsterModification all new fields)
  - 09-04 (Equipment section UI uses EquipmentItem, SRD_WEAPONS, SRD_ARMORS)
  - 09-05 (Persistence round-trip uses MonsterModification.from_dict())

tech-stack:
  added: []
  patterns:
    - MonsterModification.from_dict() filters unknown keys for forward-compat JSON loading
    - EquipmentItem/BuffItem as flat dataclasses serialized via dataclasses.asdict()
    - Parser size/skills extraction via dedicated helper functions with regex
    - SIZE_DICE_MULTIPLIER as module-level dict for weapon dice scaling

key-files:
  created:
    - src/equipment/__init__.py
    - src/equipment/data.py
  modified:
    - src/domain/models.py
    - src/parser/formats/fivetools.py
    - src/tests/test_domain_models.py
    - src/tests/test_persistence_service.py

key-decisions:
  - "SKILL_TO_ABILITY covers 5 ability scores (no CON — D&D 5e has no CON-based skill)"
  - "MonsterModification.from_dict() does shallow copy of input dict to avoid mutation"
  - "Parser _extract_size() returns 'Medium' as default when no valid size found in type line"
  - "SRD_WEAPONS includes 33 entries (simple melee + martial melee + ranged weapons)"
  - "EquipmentService (pre-placed for Plan 02 TDD) fully implemented to unblock test suite import"

patterns-established:
  - "from_dict() pattern: shallow copy + reconstruct nested dataclasses + filter unknown keys"
  - "Parser extractor pattern: dedicated private function per field, defaults on failure"

requirements-completed:
  - EQUIP-03
  - EDIT-05
  - EDIT-04

duration: 7min
completed: 2026-02-25
---

# Phase 9 Plan 01: Domain Model Patches and SRD Equipment Data Summary

**Monster domain model extended with size/skills fields, Action formalized with damage_bonus/is_equipment_generated, MonsterModification extended with equipment/buffs/skills/hp_formula plus from_dict(), and SRD weapon/armor tables created as Python dataclasses**

## Performance

- **Duration:** ~7 min
- **Started:** 2026-02-25T22:22:06Z
- **Completed:** 2026-02-25T22:29:22Z
- **Tasks:** 2 of 2
- **Files modified:** 6 (2 modified + 4 created including service.py)

## Accomplishments

- Extended Monster dataclass with `size` (default "Medium") and `skills` dict fields; parser now extracts both from statblock text
- Added `Action.damage_bonus` and `Action.is_equipment_generated` formal fields, formalizing the Phase 8 getattr fallback
- Added `EquipmentItem` and `BuffItem` dataclasses and extended `MonsterModification` with all new Phase 9 fields plus `from_dict()` classmethod with round-trip safety
- Created `src/equipment/data.py` with `SRD_WEAPONS` (33 entries), `SRD_ARMORS` (12 entries), `WeaponData`, `ArmorData`, `SIZE_DICE_MULTIPLIER`
- Added 20 new tests across `test_domain_models.py` and `test_persistence_service.py`; all 485 tests pass

## Task Commits

Each task was committed atomically:

1. **Task 1: Extend domain models and create SRD equipment data** - `758c52a` (feat)
2. **Task 2: Extend parser for size extraction and add round-trip tests** - `de324de` (feat)

**Plan metadata:** (docs commit follows)

## Files Created/Modified

- `src/domain/models.py` - Monster.size, Monster.skills, Action.damage_bonus, Action.is_equipment_generated, EquipmentItem, BuffItem, MonsterModification extended fields + from_dict(), SKILL_TO_ABILITY
- `src/equipment/__init__.py` - Package marker for equipment module
- `src/equipment/data.py` - WeaponData, ArmorData dataclasses; SRD_WEAPONS (33), SRD_ARMORS (12), SIZE_DICE_MULTIPLIER
- `src/parser/formats/fivetools.py` - Added _extract_size(), _extract_skills(), SKILLS_RE, SKILL_ENTRY_RE, _VALID_SIZES; wired into parse_fivetools()
- `src/tests/test_domain_models.py` - 17 new tests for all Phase 9 domain model extensions
- `src/tests/test_persistence_service.py` - 3 new tests for equipment+buffs round-trip and old-format compatibility

## Decisions Made

- SKILL_TO_ABILITY covers 5 ability scores (STR, DEX, INT, WIS, CHA) — there is no CON-based skill in D&D 5e; the initial test that asserted CON was corrected
- MonsterModification.from_dict() does a shallow copy of input dict before mutating to avoid side effects on caller
- Parser defaults Monster.size to "Medium" when the type/alignment line doesn't contain a recognizable size word
- Pre-placed EquipmentService (`src/equipment/service.py`) was already fully implemented by the planner for Plan 02's TDD RED step; it was left as-is since it passed all 46 equipment service tests

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] Fixed incorrect test assertion for SKILL_TO_ABILITY ability coverage**
- **Found during:** Task 2 (add round-trip tests)
- **Issue:** Test `test_skill_to_ability_covers_all_abilities` asserted that all 6 ability scores (including CON) were covered, but D&D 5e has no CON-based skill
- **Fix:** Renamed test to `test_skill_to_ability_covers_expected_abilities` and corrected assertion to check for exactly 5 abilities (excluding CON)
- **Files modified:** src/tests/test_domain_models.py
- **Verification:** Test passes; SKILL_TO_ABILITY correctly has no CON entry
- **Committed in:** de324de (Task 2 commit)

---

**Total deviations:** 1 auto-fixed (Rule 1 - Bug: incorrect test assertion)
**Impact on plan:** Minor correction to test logic. No scope creep. The SKILL_TO_ABILITY dict itself was correct; only the test expectation was wrong.

## Issues Encountered

- `src/tests/test_equipment_service.py` was a pre-placed untracked file referencing `src.equipment.service` which didn't exist yet, causing the full test suite import to fail. Discovered that `src/equipment/service.py` was also pre-created and fully implemented by the planner. No action needed — both files were already correct and all 46 equipment service tests pass.

## Next Phase Readiness

- Plan 02 (EquipmentService TDD): All domain model prerequisites in place. `src/equipment/service.py` is pre-created and all TDD tests pass — Plan 02 can proceed to verify and document rather than implement from scratch.
- Plan 03 (MonsterEditorDialog skeleton): Monster.size, Monster.skills, all MonsterModification fields are ready.
- Plan 04 (Equipment section UI): SRD_WEAPONS, SRD_ARMORS, EquipmentItem, BuffItem all ready.
- Plan 05 (Persistence round-trip): MonsterModification.from_dict() handles both old and new JSON formats.

---
*Phase: 09-monster-editor-and-equipment-presets*
*Completed: 2026-02-25*
