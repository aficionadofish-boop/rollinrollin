---
phase: 09-monster-editor-and-equipment-presets
plan: 05
subsystem: ui
tags: [monster-editor, persistence, library-badge, buff-wiring, pyside6, save-workflow]

# Dependency graph
requires:
  - phase: 09-04
    provides: "MonsterEditorDialog with Equipment/Actions/Buffs sections and public accessors"
  - phase: 09-03
    provides: "MonsterEditorDialog skeleton with collapsible sections and live preview"
  - phase: 09-01
    provides: "MonsterModification, EquipmentItem, BuffItem domain models with from_dict()"
  - phase: 08
    provides: "PersistenceService.save_modified_monsters/load_modified_monsters"
provides:
  - "Save override workflow: replaces base monster in library and persists MonsterModification"
  - "Save as copy workflow: adds new named monster with uniqueness check and re-prompt"
  - "Library badge: pencil symbol (U+270E) for modified monsters in MonsterTableModel column 3"
  - "Monster.buffs field carries BuffItem list from editor through library to AttackRollerTab"
  - "Startup restoration: _apply_persisted_modifications() rebuilds modified monsters from JSON"
  - "AttackRollerTab shows 'Buffs: ...' label below creature header for buffed monsters"
affects:
  - "Phase 12 (Save Roller) — buff cross-tab visibility foundation in place"
  - "Phase 13 (Theming) — new badge and buff label have inline styles"

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Modification diff: only store changed fields in MonsterModification (not full monster)"
    - "Library tab signal chain: monster_saved -> _on_monster_saved -> reset_monsters + set_modified_names"
    - "Startup apply pattern: _apply_persisted_modifications() called after tabs are built"
    - "buffs field on Monster dataclass: optional list[BuffItem] default empty, forward-compat"

key-files:
  created: []
  modified:
    - src/domain/models.py - Added Monster.buffs field (list[BuffItem]) for cross-tab persistence
    - src/ui/monster_editor.py - _save_override, _save_as_copy, _build_modification, _modification_to_dict; accepts library+persistence params; toolbar wired to real save actions; closeEvent Save calls _save_override
    - src/ui/monster_table.py - _modified_names set, set_modified_names(), badge logic in data() and ToolTipRole
    - src/ui/library_tab.py - accepts persistence param; _on_edit_monster passes library+persistence; _on_monster_saved + _get_modified_names
    - src/ui/app.py - passes persistence to MonsterLibraryTab; _apply_persisted_modifications() method; MonsterModification import
    - src/ui/attack_roller_tab.py - buff label below creature header in _rebuild_action_list

key-decisions:
  - "Monster.buffs lives on Monster dataclass (not editor-local) so it flows through library to any consumer without extra wiring"
  - "Modification diff stores only changed fields: empty saves/skills/ability_scores if unchanged — keeps JSON minimal"
  - "PersistenceService load+merge strategy in _save_override: load current dict, update key, save back — avoids clobbering other saved modifications"
  - "Badge collision priority: incomplete '!' > modified pencil > '' — incomplete status takes precedence"
  - "Save-as-copy re-prompt loop: validates non-empty name AND library uniqueness before accepting — shows separate error messages for each failure"
  - "Startup apply pattern: action override reconstruction from JSON dict to avoid forward-compat breakage"

patterns-established:
  - "closeEvent Save: calls real save method with event.ignore() so dialog controls its own close lifecycle"
  - "monster_saved signal connected before dialog.exec() so it fires before teardown"

requirements-completed: [EDIT-09, EDIT-10, EDIT-11]

# Metrics
duration: 35min
completed: 2026-02-26
---

# Phase 9 Plan 05: Save Workflows, Library Badge, and Cross-Tab Buff Wiring Summary

**Save override/copy workflow with MonsterModification persistence, pencil badge in library table, and Monster.buffs flowing to AttackRollerTab — completing the Phase 9 monster editing loop**

## Performance

- **Duration:** ~35 min
- **Started:** 2026-02-26T23:19:35Z
- **Completed:** 2026-02-26T23:54:00Z
- **Tasks:** 1 (of 2; Task 2 is human-verify checkpoint)
- **Files modified:** 6

## Accomplishments
- Save (override) replaces base monster in MonsterLibrary and persists MinimalMonsterModification to JSON
- Save as Copy adds new named monster with re-prompt loop for duplicate name validation
- Library table shows pencil symbol "✎" badge for all modified monster names; badge survives app restarts via startup restoration
- Monster.buffs field added to domain model; buffs flow from editor through library to AttackRollerTab buff label
- Startup: `_apply_persisted_modifications()` rebuilds all saved modifications into library on load

## Task Commits

Each task was committed atomically:

1. **Task 1: Implement save workflows, library badge, and cross-tab buff wiring** - `96e9fee` (feat)

**Plan metadata:** (to be committed with SUMMARY.md)

## Files Created/Modified
- `src/domain/models.py` - Added `buffs: list[BuffItem]` field to Monster dataclass
- `src/ui/monster_editor.py` - Real `_save_override` and `_save_as_copy` methods; `_build_modification` diff builder; `_modification_to_dict` serializer; updated constructor with library/persistence params; toolbar wired; closeEvent Save calls real save
- `src/ui/monster_table.py` - `_modified_names: set[str]`; `set_modified_names()` method; pencil badge in `data()` with priority logic; ToolTipRole for badge column
- `src/ui/library_tab.py` - Accepts persistence param; `_on_edit_monster` passes library+persistence to dialog; `_on_monster_saved` signal handler; `_get_modified_names()` helper
- `src/ui/app.py` - Passes persistence to MonsterLibraryTab; `_apply_persisted_modifications()` startup method; MonsterModification import
- `src/ui/attack_roller_tab.py` - Buff label (steel blue, 8pt) below creature header in `_rebuild_action_list` for monsters with non-empty buffs list

## Decisions Made
- Monster.buffs lives on Monster dataclass (not only editor-local) so it flows through library to any consumer without extra wiring
- Modification diff stores only changed fields: saves/skills/ability_scores dicts are empty if unchanged — keeps JSON minimal
- PersistenceService load+merge in _save_override: load current dict, update key, save back — avoids clobbering other saved modifications
- Badge collision priority: incomplete "!" > modified pencil > "" — incomplete status takes precedence
- Save-as-copy re-prompt loop: separate QMessageBox errors for empty name vs. collision before accepting
- Startup action override: reconstruct Action/DamagePart from JSON dict during _apply_persisted_modifications for forward-compat

## Deviations from Plan

None — plan executed exactly as written.

## Issues Encountered

None.

## User Setup Required

None — no external service configuration required.

## Next Phase Readiness
- All Phase 9 requirements (EDIT-01 through EDIT-11, EQUIP-01 through EQUIP-09) are implemented
- Task 2 is a human-verify checkpoint to confirm all 6 Phase 9 success criteria pass manually
- Phase 12 (Save Roller) can leverage Monster.buffs for mechanical buff integration
- Phase 13 (Theming) should audit the new badge symbol and buff label inline styles

## Self-Check

Files exist:
- [x] src/domain/models.py — confirmed Monster.buffs field added
- [x] src/ui/monster_editor.py — confirmed _save_override, _save_as_copy implemented
- [x] src/ui/monster_table.py — confirmed set_modified_names() and badge logic
- [x] src/ui/library_tab.py — confirmed _on_monster_saved, _get_modified_names
- [x] src/ui/app.py — confirmed _apply_persisted_modifications()
- [x] src/ui/attack_roller_tab.py — confirmed buff label in _rebuild_action_list

Commits exist:
- [x] 96e9fee — feat(09-05): implement save workflows, library badge, and cross-tab buff wiring

Tests: 485 passed, 0 failures

## Self-Check: PASSED

---
*Phase: 09-monster-editor-and-equipment-presets*
*Completed: 2026-02-26*
