---
phase: 12-save-roller-upgrades
plan: 01
subsystem: encounter
tags: [feature-detection, save-rolls, legendary-resistance, magic-resistance, persistence, dataclasses]

# Dependency graph
requires:
  - phase: 11-combat-tracker
    provides: CombatTrackerService LR regex pattern; SaveParticipant usage in _on_send_to_saves()
provides:
  - Extended SaveParticipant with advantage/detected_features/lr_uses/lr_max/monster_name fields
  - Extended SaveParticipantResult with detected_features/lr_uses/lr_max fields
  - SaveRollService per-participant advantage override (falls back to request-level)
  - FeatureRule dataclass with to_dict()/from_dict() serialization
  - BUILTIN_RULES constant (MR auto-advantage, LR reminder)
  - FeatureDetectionService.detect_for_participant() stateless trait scanner
  - PersistenceService save_rules category backed by save_rules.json
  - AppSettings ct_send_overrides_sidebar: bool = True
affects:
  - 12-02 (sidebar checkbox selection wiring)
  - 12-03 (SavesTab UI wiring — consumes all models and services built here)

# Tech tracking
tech-stack:
  added: []
  patterns:
    - Per-participant advantage override with request-level fallback (participant.advantage is not None)
    - Stateless feature detection service — all LR counter state lives in UI layer
    - FeatureRule dataclass with to_dict()/from_dict() for JSON persistence
    - actions[*].raw_text scan only (NOT monster.raw_text or lore) to avoid false positives
    - max() across all LR matches to avoid double-counting duplicate action entries

key-files:
  created: []
  modified:
    - src/encounter/models.py
    - src/encounter/service.py
    - src/persistence/service.py
    - src/settings/models.py

key-decisions:
  - "Per-participant advantage: participant.advantage (Optional) overrides request.advantage when not None — backward compat preserved"
  - "FeatureDetectionService is stateless — LR counters live in SavesTab._lr_counters dict keyed by monster_name"
  - "Feature detection scans Monster.actions[*].raw_text only — avoids lore-paragraph false positives (locked decision)"
  - "LR count uses max() across all action raw_text entries to avoid double-counting"
  - "save_rules not in _DICT_CATEGORIES — list-based default (not dict)"
  - "ct_send_overrides_sidebar: bool = True — CT send replaces sidebar checked state by default (locked decision)"

patterns-established:
  - "FeatureRule: trigger/label/behavior/enabled/is_builtin dataclass with to_dict() omitting is_builtin (code-only field)"
  - "BUILTIN_RULES constant at module level — always recreated from code, never persisted"

requirements-completed: [SAVE-09, SAVE-10, SAVE-12, SAVE-14]

# Metrics
duration: 3min
completed: 2026-02-26
---

# Phase 12 Plan 01: Domain Models and Feature Detection Foundation Summary

**FeatureDetectionService, FeatureRule dataclass, and extended SaveParticipant/SaveParticipantResult models enabling per-creature advantage overrides and MR/LR trait detection from Monster.actions[*].raw_text**

## Performance

- **Duration:** 3 min
- **Started:** 2026-02-26T06:08:08Z
- **Completed:** 2026-02-26T06:11:32Z
- **Tasks:** 2
- **Files modified:** 4

## Accomplishments
- Extended SaveParticipant with advantage/detected_features/lr_uses/lr_max/monster_name fields (all with defaults — 100% backward compatible)
- Extended SaveParticipantResult with detected_features/lr_uses/lr_max fields for UI display
- Updated SaveRollService to resolve per-participant advantage before falling back to request-level
- Added FeatureRule dataclass, BUILTIN_RULES constant, FeatureDetectionService — pure Python, stateless, no Qt
- Added save_rules persistence category to PersistenceService (load_save_rules/save_save_rules backed by save_rules.json)
- Added ct_send_overrides_sidebar: bool = True to AppSettings

## Task Commits

Each task was committed atomically:

1. **Task 1: Extend domain models and SaveRollService for per-creature feature detection** - `c296145` (feat)
2. **Task 2: Add save_rules persistence category and ct_send_overrides_sidebar setting** - `1f5bcc0` (feat)

**Plan metadata:** (docs commit — follows below)

## Files Created/Modified
- `src/encounter/models.py` - SaveParticipant and SaveParticipantResult extended with feature detection fields
- `src/encounter/service.py` - FeatureRule dataclass, BUILTIN_RULES, FeatureDetectionService added; SaveRollService per-participant advantage logic
- `src/persistence/service.py` - save_rules category in _FILENAMES; load_save_rules/save_save_rules methods
- `src/settings/models.py` - ct_send_overrides_sidebar: bool = True field added to AppSettings

## Decisions Made
- Per-participant advantage uses Optional field (None = inherit from request) — cleanest backward-compat approach
- FeatureDetectionService is stateless by design — LR counter tracking lives in SavesTab UI layer (Pitfall 4 from RESEARCH.md)
- scan Monster.actions[*].raw_text only — NOT Monster.raw_text or Monster.lore (locked project decision)
- LR count regex uses max() to handle duplicate action entries
- save_rules uses list default (not dict) — consistent with loaded_monsters/macros/player_characters pattern

## Deviations from Plan

None - plan executed exactly as written.

## Issues Encountered
None.

## User Setup Required
None - no external service configuration required.

## Next Phase Readiness
- All pure-Python foundation is complete for Plan 03 (SavesTab UI wiring)
- FeatureDetectionService.detect_for_participant() ready to be called from SavesTab._execute_roll()
- SaveParticipant.advantage field ready to carry per-creature overrides from feature detection
- PersistenceService.load_save_rules()/save_save_rules() ready for custom rule persistence
- All 510 existing tests pass unchanged

---
*Phase: 12-save-roller-upgrades*
*Completed: 2026-02-26*

## Self-Check: PASSED

- src/encounter/models.py: FOUND
- src/encounter/service.py: FOUND
- src/persistence/service.py: FOUND
- src/settings/models.py: FOUND
- .planning/phases/12-save-roller-upgrades/12-01-SUMMARY.md: FOUND
- Commit c296145 (Task 1): FOUND
- Commit 1f5bcc0 (Task 2): FOUND
- 510 tests passing: CONFIRMED
