---
phase: 11-combat-tracker
plan: 01
subsystem: combat
tags: [service, models, persistence, tdd, dataclasses]
dependency_graph:
  requires:
    - src/engine/roller.py
    - src/persistence/service.py
    - src/domain/models.py
  provides:
    - src/combat/models.py
    - src/combat/service.py
    - src/persistence/service.py (extended)
  affects:
    - All Phase 11 UI plans (depend on CombatTrackerService)
    - Phase 11 Plan 02+ (combatant cards, HP bars, conditions UI)
tech_stack:
  added: []
  patterns:
    - Pure Python dataclasses for domain models (established pattern)
    - MonsterModification.from_dict() known-field filtering pattern
    - PersistenceService category extension pattern
    - TDD RED-GREEN cycle
key_files:
  created:
    - src/combat/__init__.py
    - src/combat/models.py
    - src/combat/service.py
    - src/tests/test_combat_service.py
  modified:
    - src/persistence/service.py
decisions:
  - "CombatTrackerService holds _prev_snapshot as a dict (not a CombatState copy) for minimal memory overhead during undo"
  - "Grouped initiative rolls once per group_id when grouping_enabled=True; each monster in the group gets the same initiative value"
  - "ConditionEntry.color field preserved in serialization (set by UI layer, not service)"
  - "Auto-regen via advance_turn() only when regeneration_hp > 0; pass_one_round() does not auto-regen (pass-1-round mode is condition-focused)"
  - "Feature detection scans Monster.actions[*].raw_text with regex for Legendary Resistance count, Legendary Actions count, Regeneration HP"
metrics:
  duration: "4 minutes"
  completed: "2026-02-26"
  tasks_completed: 2
  files_created: 4
  files_modified: 1
  tests_added: 22
  tests_passing: 463
---

# Phase 11 Plan 01: Combat Domain Models and CombatTrackerService Summary

**One-liner:** Pure-Python combat service with temp-HP absorption, grouped-initiative rolling, one-level undo, and condition lifecycle — TDD-first with 22 passing tests.

## What Was Built

### Task 1: Combat domain models and CombatTrackerService (TDD)

**src/combat/models.py** — Four dataclasses and two constant lists:

- `ConditionEntry` — condition with name, optional duration, expired flag, UI color hint
- `CombatantState` — full combatant state: HP, temp HP, initiative, AC, DEX score, conditions, group membership, speed, passive perception, legendary resistance/actions, regeneration. Property `is_defeated` returns True when current_hp <= 0. `to_dict()` / `from_dict()` with known-field filtering for forward-compat.
- `CombatState` — full session state: combatant list, round_number, current_turn_index, initiative_mode, grouping_enabled, log_entries. Serializes cleanly.
- `PlayerCharacter` — global PC data: name, AC, max/current HP, conditions. Serializes cleanly.
- `STANDARD_CONDITIONS` — 14 standard 5e conditions with None duration (indefinite)
- `COMMON_BUFFS` — 15 common spells/effects with pre-configured durations

**src/combat/service.py** — `CombatTrackerService`:

- `load_encounter(members, roller)` — expands [(Monster, count)] into individually-numbered CombatantState entries; detects legendary resistance/actions/regeneration from action.raw_text keyword scan
- `add_pcs(pcs)` — adds PC combatants with auto-numbering on name collision
- `remove_combatant(combatant_id)` — removes by ID; decrements current_turn_index if removed index <= current turn (pitfall #2 from research)
- `roll_all_initiative(roller)` — uses Roller.roll_dice(1, 20) + DEX modifier; grouped combatants share one roll per group_id; sorts descending by (initiative, dex_score)
- `apply_damage(combatant_id, signed_value)` — positive heals (cap at max); negative absorbs temp HP first, then current HP (floor at 0)
- `apply_aoe_damage(combatant_ids, damage)` — applies same damage to multiple combatants
- `add_condition / remove_condition` — adds/removes ConditionEntry by name
- `advance_turn()` — snapshots state, decrements conditions on ending combatant, advances index (wraps), increments round on wrap, resets legendary actions for new active combatant
- `undo_advance()` — restores turn_index, round_number, all condition durations atomically from snapshot; returns False if no snapshot
- `pass_one_round()` — decrements all conditions on all combatants; increments round (pass-1-round mode)
- `set_initiative / reset_combat / get_combatant / load_state` — supporting methods

**src/tests/test_combat_service.py** — 22 TDD tests covering all service behaviors listed above plus STANDARD_CONDITIONS count, COMMON_BUFFS count, undo with no snapshot, add/remove condition, is_defeated property, and PlayerCharacter serialization roundtrip.

### Task 2: PersistenceService extension

**src/persistence/service.py** — Additive changes only:

- `_FILENAMES` — added `"combat_state": "combat_state.json"` and `"player_characters": "player_characters.json"`
- `_DICT_CATEGORIES` — added `"combat_state"` (uses dict root like encounters)
- Added `load_combat_state() / save_combat_state()` typed methods
- Added `load_player_characters() / save_player_characters()` typed methods
- Updated `count()` to handle `"combat_state"` by returning len(combatants) from the loaded dict

## Deviations from Plan

None — plan executed exactly as written.

## Test Results

- Task 1: 22 new combat service tests — all passing
- Task 2: All 463 tests passing (22 new + 441 pre-existing)

## Self-Check: PASSED

Files verified:
- FOUND: src/combat/__init__.py
- FOUND: src/combat/models.py
- FOUND: src/combat/service.py
- FOUND: src/tests/test_combat_service.py
- FOUND: src/persistence/service.py (modified)

Commits verified:
- f72e6d4: feat(11-01): add combat domain models and CombatTrackerService with TDD
- 0702f23: feat(11-01): extend PersistenceService with combat_state and player_characters
