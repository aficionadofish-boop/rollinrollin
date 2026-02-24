---
phase: 04-lists-encounters-and-save-roller
plan: "01"
subsystem: domain
tags: [dataclasses, domain-models, encounter, save-roller, dtos]

# Dependency graph
requires:
  - phase: 03-attack-roller
    provides: roll/models.py BonusDiceEntry shape referenced in SaveRequest.bonus_dice typing
  - phase: 01-dice-engine-and-domain-foundation
    provides: domain/models.py Monster, Encounter, MonsterList dataclasses
provides:
  - Encounter.members as list[tuple[Monster, int]] — replaces bare list[Monster]
  - MonsterLibrary.get_by_name(name) — O(1) lookup returning Monster or KeyError
  - src/encounter package with six Phase 4 DTOs: UnresolvedEntry, SaveParticipant, SaveRequest, SaveParticipantResult, SaveSummary, SaveRollResult
affects: [04-02-encounter-service, 04-03-save-roller-service, 04-04-ui-lists-encounters, 04-05-ui-save-roller]

# Tech tracking
tech-stack:
  added: []
  patterns: [encounter/models.py mirrors roll/models.py structure — pure stdlib dataclasses only, no Qt, no I/O]

key-files:
  created:
    - src/encounter/__init__.py
    - src/encounter/models.py
  modified:
    - src/domain/models.py
    - src/library/service.py
    - src/tests/test_domain_models.py

key-decisions:
  - "Encounter.members is list[tuple[Monster, int]] — same (monster, count) convention as MonsterList.entries, established in 01-02 for MonsterList"
  - "get_by_name raises KeyError on miss — callers must call has_name() first; no Optional return to avoid silent None dereferences in UI"
  - "SaveRequest.bonus_dice typed as list (untyped) to avoid importing BonusDiceEntry from roll.models at encounter layer — avoids cross-package coupling at the dataclass level"

patterns-established:
  - "Phase 4 DTOs live in src/encounter/models.py alongside src/roll/models.py pattern — one models.py per service domain"
  - "Encounter members shape: (Monster, int) tuples — count is always explicit, never inferred from list length"

requirements-completed: [LIST-01, LIST-02, LIST-03, LIST-04, LIST-05, ENC-01, ENC-02]

# Metrics
duration: 4min
completed: 2026-02-24
---

# Phase 4 Plan 01: Domain Model Extensions and Encounter DTOs Summary

**Encounter.members changed to list[tuple[Monster, int]], MonsterLibrary.get_by_name added, and all six Phase 4 save-roller DTOs created in new src/encounter package**

## Performance

- **Duration:** 4 min
- **Started:** 2026-02-24T02:50:34Z
- **Completed:** 2026-02-24T02:54:00Z
- **Tasks:** 2
- **Files modified:** 5

## Accomplishments
- Patched Encounter.members from `list[Monster]` to `list[tuple[Monster, int]]` — aligns with MonsterList.entries convention
- Added MonsterLibrary.get_by_name() for O(1) monster lookup by name; raises KeyError on miss so callers must guard with has_name()
- Created src/encounter/ package with all six Phase 4 DTOs (UnresolvedEntry, SaveParticipant, SaveRequest, SaveParticipantResult, SaveSummary, SaveRollResult) modelled after src/roll/models.py
- Updated test_encounter_construction to use (goblin, 1) tuple shape; 276 tests pass, no regressions

## Task Commits

Each task was committed atomically:

1. **Task 1: Patch Encounter.members + add MonsterLibrary.get_by_name** - `3c89380` (feat)
2. **Task 2: Create src/encounter package with all Phase 4 DTOs** - `78c240c` (feat)

**Plan metadata:** (docs commit — see below)

## Files Created/Modified
- `src/domain/models.py` - Encounter.members type changed to list[tuple[Monster, int]]
- `src/library/service.py` - get_by_name(name) method added after has_name()
- `src/tests/test_domain_models.py` - test_encounter_construction updated to (monster, count) tuple
- `src/encounter/__init__.py` - New package marker file
- `src/encounter/models.py` - New file: six Phase 4 DTOs for EncounterService and SaveRollService

## Decisions Made
- Encounter.members adopts the same (monster, count) tuple convention already used by MonsterList.entries — consistent shape across the domain
- get_by_name raises KeyError on miss (not Optional[Monster]) to force explicit has_name() guard at call sites, preventing silent None dereferences in UI layer
- SaveRequest.bonus_dice typed as `list` (untyped) to avoid importing BonusDiceEntry from src.roll.models into src.encounter.models — keeps encounter layer decoupled from roll layer at the dataclass level

## Deviations from Plan

None - plan executed exactly as written.

## Issues Encountered

None.

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness
- Plan 02 (EncounterService) can immediately use Encounter.members as (monster, count) tuples and MonsterLibrary.get_by_name()
- Plan 03 (SaveRollService) can import SaveRequest, SaveParticipant, SaveParticipantResult, SaveSummary, SaveRollResult from src.encounter.models
- All 276 existing tests pass — no regressions introduced

---
*Phase: 04-lists-encounters-and-save-roller*
*Completed: 2026-02-24*
