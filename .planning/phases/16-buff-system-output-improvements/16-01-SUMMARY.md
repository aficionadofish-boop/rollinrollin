---
phase: 16-buff-system-output-improvements
plan: 01
subsystem: ui
tags: [PySide6, QCheckBox, dataclass, migration, buffs]

# Dependency graph
requires:
  - phase: 09-editor-and-persistence
    provides: BuffItem dataclass and MonsterModification.from_dict() pattern
  - phase: 15-editor-parser-overhaul
    provides: Monster editor collapsible section layout

provides:
  - BuffItem with 4 independent boolean fields (affects_attacks/saves/ability_checks/damage)
  - _BUFF_TARGET_MIGRATION for backward-compatible JSON deserialization
  - Buff editor section with 4 QCheckBox widgets per row replacing QComboBox
  - Attack roller tab buff label using boolean fields for display

affects: [16-02-attack-injection, 16-03-save-injection]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "_BUFF_TARGET_MIGRATION dict pattern for backward-compat field migration in from_dict()"
    - "QCheckBox row with _BUFF_CHECKBOX_ATTRS (label, attr) tuple list for declarative checkbox wiring"
    - "setattr dispatch in _on_buff_checkbox_changed for clean boolean field updates"

key-files:
  created: []
  modified:
    - src/domain/models.py
    - src/ui/monster_editor.py
    - src/ui/attack_roller_tab.py
    - src/tests/test_domain_models.py
    - src/tests/test_persistence_service.py

key-decisions:
  - "BuffItem defaults: affects_attacks=True, affects_saves=True, affects_ability_checks=False, affects_damage=False (Bless-style — most common buff type)"
  - "_BUFF_TARGET_MIGRATION maps old targets string to 4 booleans; unknown/missing targets key falls back to 'all' (all True)"
  - "from_dict() migration: pop 'targets' key when affects_attacks absent (old format); pop 'targets' silently when affects_attacks present (mixed/cleaned format)"
  - "attack_roller_tab buff display: _buff_targets_str() builds 'atk+sav+chk+dmg' abbreviation string from boolean fields"
  - "_BUFF_CHECKBOX_ATTRS replaces _BUFF_TARGETS — tuple list of (label, attr_name) drives both UI and signal wiring declaratively"

patterns-established:
  - "Migration mapping pattern: module-level dict maps old string values to new field dicts; injected via b.update() in from_dict()"
  - "Checkbox wiring pattern: iterate _BUFF_CHECKBOX_ATTRS, create QCheckBox, connect stateChanged with lambda capturing (idx, attr)"

requirements-completed: [BUFF-01]

# Metrics
duration: 25min
completed: 2026-02-28
---

# Phase 16 Plan 01: Buff Model Migration & Checkbox UI Summary

**BuffItem migrated from single targets string to 4 independent boolean fields with QCheckBox editor UI and backward-compatible JSON migration for existing saved monsters**

## Performance

- **Duration:** 25 min
- **Started:** 2026-02-28T00:00:00Z
- **Completed:** 2026-02-28T00:25:00Z
- **Tasks:** 2
- **Files modified:** 5

## Accomplishments

- Replaced `BuffItem.targets: str` with `affects_attacks/affects_saves/affects_ability_checks/affects_damage` booleans with correct Bless-style defaults (True/True/False/False)
- Added `_BUFF_TARGET_MIGRATION` mapping so old JSON data (`"targets": "attack_rolls"`) auto-migrates in `MonsterModification.from_dict()` without data loss
- Replaced the buff target QComboBox in the monster editor with a horizontal row of 4 labeled QCheckBox widgets per buff, connected via `_on_buff_checkbox_changed()`
- Updated `attack_roller_tab.py` buff display label to build target summary from boolean fields
- Added 6 new targeted tests: buff defaults, round-trip, and 3 migration cases (attack_rolls, saving_throws, all)

## Task Commits

Each task was committed atomically:

1. **Task 1: Migrate BuffItem model and add from_dict() migration logic** - `8f64cc1` (feat)
2. **Task 2: Replace buff target QComboBox with 4 QCheckBox widgets in editor** - `1cfa96b` (feat)

**Plan metadata:** (docs commit below)

## Files Created/Modified

- `src/domain/models.py` - BuffItem 4 boolean fields, _BUFF_TARGET_MIGRATION mapping, updated from_dict() migration logic
- `src/ui/monster_editor.py` - QCheckBox import, _BUFF_CHECKBOX_ATTRS constant, _rebuild_buff_rows checkbox wiring, _on_buff_checkbox_changed handler, _on_add_buff defaults, _on_buff_field_changed simplified
- `src/ui/attack_roller_tab.py` - _buff_targets_str() helper for boolean-field-based display label
- `src/tests/test_domain_models.py` - Updated existing buff tests, added 5 new tests (defaults, migration for attack_rolls/saving_throws/all)
- `src/tests/test_persistence_service.py` - Updated BuffItem construction in round-trip test

## Decisions Made

- BuffItem defaults match Bless (attacks+saves) — the most common use case for new buffs; Checks and Damage are opt-in
- `_BUFF_TARGET_MIGRATION["all"]` is the fallback for unrecognized targets strings — safer than rejecting old data
- `_BUFF_CHECKBOX_ATTRS` is a module-level tuple list driving both UI creation and signal wiring — single source of truth for label/attribute mapping
- attack_roller_tab uses abbreviated display ("atk+sav") rather than full labels to keep the buff info line compact

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 2 - Missing Critical] Updated attack_roller_tab.py buff display to use new boolean fields**
- **Found during:** Task 2 (editor QCheckBox replacement)
- **Issue:** `attack_roller_tab.py` still referenced `b.targets.replace('_', ' ')` which would AttributeError on the new BuffItem
- **Fix:** Added `_buff_targets_str()` helper function that builds abbreviated string from boolean fields
- **Files modified:** `src/ui/attack_roller_tab.py`
- **Verification:** All 514 tests pass; no AttributeError on .targets
- **Committed in:** `1cfa96b` (Task 2 commit)

---

**Total deviations:** 1 auto-fixed (Rule 2 - missing critical update in attack_roller_tab)
**Impact on plan:** Necessary for correctness — would have caused AttributeError at runtime. No scope creep.

## Issues Encountered

None — migration logic worked cleanly first attempt. Test suite confirmed all 514 tests pass after both tasks.

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness

- BuffItem now has `affects_attacks` and `affects_saves` boolean fields — Plans 02 and 03 can read these directly to decide whether to inject buff dice into attack and save roll calculations
- The foundation is set: `buff.affects_attacks` gates attack roll injection in Plan 02; `buff.affects_saves` gates save roll injection in Plan 03
- Existing saved monster data will auto-migrate on next load via `MonsterModification.from_dict()`

---
*Phase: 16-buff-system-output-improvements*
*Completed: 2026-02-28*
