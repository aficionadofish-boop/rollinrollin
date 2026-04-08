---
phase: 18-storyteller-system-dice-roller-in-a-new-tab
plan: "01"
subsystem: storyteller
tags: [engine, models, persistence, settings, dice]
dependency_graph:
  requires: []
  provides:
    - src/storyteller package (engine + models)
    - PersistenceService storyteller_presets category
    - AppSettings storyteller fields
  affects:
    - src/persistence/service.py
    - src/settings/models.py
tech_stack:
  added: []
  patterns:
    - Qt-free engine with injected random.Random (matches Roller pattern)
    - dataclass domain models with to_dict/from_dict for JSON persistence
    - _FILENAMES + _DICT_CATEGORIES registry in PersistenceService
key_files:
  created:
    - src/storyteller/__init__.py
    - src/storyteller/models.py
    - src/storyteller/engine.py
  modified:
    - src/persistence/service.py
    - src/settings/models.py
decisions:
  - "Aberrant 1s never cancel successes — botch is purely (total==0 AND any 1)"
  - "WoD 8/9-again is a loop (max 50 iterations), not a single extra pass"
  - "Rote pass re-rolls non-success non-1 dice once; rote batch then seeds the threshold chain"
  - "ones_count counts only non-success dice showing 1 (success die showing 1 is impossible on d10 vs difficulty>=2, but rule is structural)"
  - "storyteller_last_config uses field(default_factory=dict) to avoid mutable default"
metrics:
  duration: "~2 minutes"
  completed: "2026-04-08"
  tasks_completed: 2
  files_created: 3
  files_modified: 2
---

# Phase 18 Plan 01: Storyteller Engine and Data Infrastructure Summary

**One-liner:** Qt-free WoD/Aberrant dice engine with 8/9-again loop, rote support, mega dice, and cross-session preset persistence via PersistenceService.

## What Was Built

The pure-Python foundation layer for the Storyteller system dice roller tab. No Qt dependencies anywhere in this plan — fully testable in isolation.

### src/storyteller/ package

**models.py** — Five dataclasses:
- `DieResult`: Single d10 result with success/one/reroll flags
- `MegaDieResult`: Aberrant mega die with sux_count (0/2/3) and one flag
- `WodRollResult`: Full WoD roll with all dice, net/raw/ones counts, botch/exceptional flags
- `AberrantRollResult`: Full Aberrant roll with normal+mega dice, total successes, tier, botch flag
- `StorytellerPreset`: Named roll configuration with to_dict/from_dict for JSON round-trips

**engine.py** — `StorytellerEngine` class:
- `roll_wod(pool, difficulty, reroll_threshold, rote_enabled)`: Implements the full chain — initial roll, optional rote pass (re-rolls non-success non-1 dice once), then 8/9-again loop (max 50 iterations) until no qualifying dice in latest batch
- `roll_aberrant(pool, mega_pool, auto_successes, successes_required)`: Normal dice (success >= 7), mega dice (10=3sux, 7-9=2sux), 1s never cancel, botch only when total==0 AND any 1

### PersistenceService extension

Added `"storyteller_presets": "storyteller_presets.json"` to `_FILENAMES` and `"storyteller_presets"` to `_DICT_CATEGORIES`. Added `load_storyteller_presets()` and `save_storyteller_presets()` public methods following existing category method pattern.

### AppSettings extension

Added `storyteller_system: str = "wod"` and `storyteller_last_config: dict = field(default_factory=dict)` after `ui_scale`. Updated `from dataclasses import dataclass` to `from dataclasses import dataclass, field`.

## Verification Results

All must-have truths verified:
- WoD all-10s pool with 8-again threshold produces 3 batches (chain terminates itself, not after one extra pass)
- Aberrant [7, 1, 1] = 1 success, not a botch
- Cross-session preset persistence: save in session 1, retrieve by name in session 2
- WoD [1, 1, 3] = net -2, is_botch=True
- Aberrant [1, 3, 4] = total 0, is_botch=True

## Deviations from Plan

None — plan executed exactly as written.

## Self-Check

Files created:
- src/storyteller/__init__.py — exists
- src/storyteller/models.py — exists
- src/storyteller/engine.py — exists

Files modified:
- src/persistence/service.py — storyteller_presets in _FILENAMES and _DICT_CATEGORIES, two new methods
- src/settings/models.py — two new fields, field import added

Commits:
- 242eb27: feat(18-01): add storyteller package with models and engine
- 385ea5b: feat(18-01): extend PersistenceService and AppSettings for storyteller
