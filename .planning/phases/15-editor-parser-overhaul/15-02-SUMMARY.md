---
phase: 15-editor-parser-overhaul
plan: 02
subsystem: ui
tags: [python, pyside6, monster-editor, traits, collapsible-section, modal-dialog, qt-widgets]

# Dependency graph
requires:
  - phase: 15-editor-parser-overhaul
    plan: 01
    provides: "Trait dataclass with rollable_dice/recharge_range, Monster.traits, Monster.speed, Action.after_text, detect_dice_in_text/detect_recharge helpers"

provides:
  - "_build_core_stats_section() merging ability scores, CR, HP, Speed, Skills into one CollapsibleSection"
  - "self._speed_edit QLineEdit wired to _working_copy.speed and _rebuild_preview()"
  - "_build_traits_section() with compact trait name list, rollable tag, Edit/Remove buttons"
  - "_rebuild_trait_rows() rebuilding trait row widgets from _trait_items"
  - "TraitEditDialog(QDialog) modal with name QLineEdit + description QTextEdit (OK/Cancel)"
  - "Action column header row above action rows with bold column labels"
  - "After-attack-text QTextEdit per action row with '...' toggle button (hidden by default)"
  - "Section order: Core Stats > Saving Throws > Traits > Actions > Equipment > Buffs"

affects:
  - "15-03 (attack roller rollable trait buttons — uses Trait.rollable_dice)"
  - "15-04 (after-attack-text rendered on hit in output)"
  - "Any code consuming MonsterEditorDialog"

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Core Stats merge pattern: ability scores + compact CR/HP/Speed row + inline skills in one CollapsibleSection"
    - "Trait edit pattern: _trait_items editor-local list mirrors _working_copy.traits; synced before every _push_undo call"
    - "Undo-safe modal pattern: push undo snapshot before opening modal; on cancel, pop snapshot and restore _trait_items"
    - "After-text toggle pattern: QTextEdit collapsed by default, '...' QPushButton(checkable) shows/hides on click"
    - "Action column header pattern: single header QWidget with bold QLabel columns inserted before action rows on rebuild"
    - "TraitEditDialog modifies Trait in-place; caller re-detects rollable_dice and recharge_range on Accepted"

key-files:
  created: []
  modified:
    - "src/ui/monster_editor.py — _build_core_stats_section(), _build_traits_section(), _rebuild_trait_rows(), TraitEditDialog, action column headers, after-text toggle, section reorder, speed field, trait undo integration"

key-decisions:
  - "Core Stats CR/HP/Speed compact horizontal row uses fixed-width combo/spinbox/lineedit with labels inline — keeps the row narrow without a separate sub-section"
  - "Traits undo: push snapshot BEFORE opening edit modal, pop on cancel — prevents phantom undo entries from cancelled edits"
  - "_trait_items synced to _working_copy.traits in _push_undo() via getattr fallback — safe during __init__ before _trait_items is set"
  - "TraitEditDialog modifies Trait object in-place (same reference as in _trait_items) — no return value needed"
  - "After-text QTextEdit height capped at 60px maximum to keep rows compact when expanded"
  - "Action column headers use rgba(255,255,255,15) background tint — subtle table-header feel without heavy styling"
  - "Cancel on new-trait add pops undo stack and restores _trait_items — prevents orphaned empty traits"

patterns-established:
  - "Trait editor pattern: editor-local list (_trait_items), sync to working_copy before undo push, sync on modal accept"
  - "Expandable row pattern: outer QVBoxLayout holds data row + QTextEdit; toggle button on data row shows/hides QTextEdit"

requirements-completed: [PARSE-02, PARSE-04, PARSE-10, PARSE-11]

# Metrics
duration: 15min
completed: 2026-02-28
---

# Phase 15 Plan 02: Monster Editor Layout Restructure Summary

**Core Stats collapsible section merging ability scores/CR/HP/Speed/Skills, Traits section with click-to-edit modal and rollable indicators, action column headers, and per-action expandable after-attack-text fields**

## Performance

- **Duration:** ~15 min
- **Started:** 2026-02-27T23:36:39Z
- **Completed:** 2026-02-28T00:00:00Z
- **Tasks:** 2 (committed together — same file, tightly coupled changes)
- **Files modified:** 1

## Accomplishments
- Created `_build_core_stats_section()` merging 4 old separate sections (ability scores, CR, HP, skills) plus new Speed field into one CollapsibleSection("Core Stats")
- Added `self._speed_edit` QLineEdit with `textChanged` signal wired to `_working_copy.speed` and preview rebuild
- Reordered sections: Core Stats > Saving Throws > Traits > Actions > Equipment > Buffs
- Built `_build_traits_section()` with compact name list, [rollable] tags where `trait.rollable_dice` non-empty, Edit and Remove buttons
- Created `TraitEditDialog(QDialog)` modal with name QLineEdit, description QTextEdit (multiline), OK/Cancel buttons
- Added column header row above action rows with bold labels: Name, To-Hit, Dmg Dice, Bonus, Dmg Type
- Added expandable after-attack-text QTextEdit per action with "..." toggle button (starts hidden)
- Trait undo integration: snapshot pushed before modal open, popped on cancel; `_push_undo()` syncs `_trait_items` to `_working_copy.traits` before every snapshot
- Zero test regressions: 510 tests pass

## Task Commits

Both tasks committed atomically (tightly coupled single-file changes):

1. **Tasks 1+2: Core Stats merge, section reorder, Traits UI, action headers, after-text** - `0779fff` (feat)

## Files Created/Modified
- `src/ui/monster_editor.py` - _build_core_stats_section(), _build_traits_section(), _rebuild_trait_rows(), TraitEditDialog, action column headers, after-text toggle, section reorder, speed field, trait undo integration; removed _build_ability_scores_section(), _build_skills_section(), _build_hp_section(), _build_cr_section()

## Decisions Made
- Core Stats CR/HP/Speed compact horizontal row: fixed-width widgets with inline labels keep the row narrow
- Trait undo: push snapshot BEFORE opening modal, pop on cancel — prevents phantom undo entries from cancelled edits
- `_trait_items` synced to `_working_copy.traits` in `_push_undo()` via `getattr(self, "_trait_items", [])` fallback — safe during `__init__` before `_trait_items` is set
- `TraitEditDialog` modifies the Trait object in-place (same reference as in `_trait_items`) — no return value needed
- After-text `QTextEdit` height capped at 60px maximum to keep rows compact
- Action column headers use `rgba(255,255,255,15)` background tint — subtle table-header feel

## Deviations from Plan

None - plan executed exactly as written.

## Issues Encountered
None.

## User Setup Required
None - no external service configuration required.

## Next Phase Readiness
- Traits section displays parsed traits from Plan 01 parser with rollable indicators
- `Trait.rollable_dice` available on each trait for Plan 03 to wire rollable trait buttons in Attack Roller
- `Action.after_text` editable in editor; Plan 03/04 can render it in roll output on hits
- Speed field shows parsed speed from statblock and is editable
- Editor section layout finalized — no further structural changes needed before Plans 03-05

---
*Phase: 15-editor-parser-overhaul*
*Completed: 2026-02-28*
