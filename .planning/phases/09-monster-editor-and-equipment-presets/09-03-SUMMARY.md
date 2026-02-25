---
phase: 09-monster-editor-and-equipment-presets
plan: 03
subsystem: ui
tags: [pyside6, qdialog, monster-editor, collapsible-section, undo-stack, live-preview]

# Dependency graph
requires:
  - phase: 09-01
    provides: "Monster.size, Monster.skills, SKILL_TO_ABILITY, domain model patches"
  - phase: 09-02
    provides: "EquipmentService — math backbone; MonsterMathEngine used for live preview"
  - phase: 08
    provides: "MonsterMathEngine.recalculate(), MathValidator.validate_saves(), DerivedStats"

provides:
  - "CollapsibleSection(QWidget) reusable collapsible widget with +/- toggle and summary text"
  - "MonsterEditorDialog: near-fullscreen two-column modal editor with live preview"
  - "Toolbar: editable monster name, Save dropdown stub, Discard, Undo"
  - "Section 1 (Ability Scores): 6 QSpinBox widgets, live preview cascade via MonsterMathEngine"
  - "Section 2 (Saving Throws): toggle Non-Prof/Prof/Expertise/Custom per ability + custom spinbox"
  - "Section 3 (Skills): existing skills with toggles, Add Skill combo, per-row Remove button"
  - "Section 4 (Hit Points): hit dice formula QLineEdit + flat max HP spinbox"
  - "Section 5 (Challenge Rating): CR QComboBox with proficiency bonus cascade"
  - "Unsaved-changes closeEvent guard (Save stub / Discard / Cancel)"
  - "Undo stack: deepcopy snapshots, _populate_form() repopulates all widgets on undo"
  - "MonsterDetailPanel.edit_requested Signal(Monster) wired to Library tab"
  - "Edit button added to MonsterDetailPanel (enabled when monster displayed)"
  - "MonsterLibraryTab._on_edit_monster() opens MonsterEditorDialog as modal"

affects:
  - "09-04 (Equipment section UI) — builds on CollapsibleSection and MonsterEditorDialog"
  - "09-05 (Persistence round-trip) — wires Save dropdown stubs with real save logic"

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "CollapsibleSection: QPushButton toggle header over hidden content QWidget, set_summary() for collapsed hint"
    - "_recalculating guard: bool flag prevents signal re-entry during programmatic widget population"
    - "_push_undo() / _undo(): deepcopy snapshot stack, _populate_form() + blockSignals() for undo restore"
    - "reject() routes through close() so Escape triggers closeEvent guard"
    - "edit_requested Signal on MonsterDetailPanel: emit monster for caller to open editor"

key-files:
  created:
    - src/ui/monster_editor.py
  modified:
    - src/ui/monster_detail.py
    - src/ui/library_tab.py

key-decisions:
  - "_on_hp_changed() updates monster.hp from flat spinbox; hp_formula stored in QLineEdit only (Monster dataclass has no hp_formula field — Plan 05 persistence will use MonsterModification.hp_formula)"
  - "Save dropdown stubs (Plan 05 wires): closeEvent Save button also stubs — accepts and closes rather than hanging on dialog"
  - "_apply_save_value() Non-Prof removes ability from saves dict (empty dict = no proficient saves on Monster)"
  - "reject() overrides base QDialog.reject() to route through close() ensuring closeEvent fires on Escape"
  - "Edit button placed in name row (QHBoxLayout) at top of MonsterDetailPanel for clear DM visibility"

patterns-established:
  - "CollapsibleSection: pass expanded=True for default-open sections (Ability Scores), False for collapsed"
  - "Signal guard pattern: _recalculating bool + blockSignals() prevents cascading recalculation"
  - "Undo restore: blockSignals() around all _populate_form() widget updates, then _rebuild_preview()"

requirements-completed:
  - EDIT-01
  - EDIT-02
  - EDIT-03
  - EDIT-04
  - EDIT-05
  - EDIT-06

# Metrics
duration: 4min
completed: 2026-02-25
---

# Phase 9 Plan 03: MonsterEditorDialog Skeleton Summary

**Two-column near-fullscreen QDialog editor with CollapsibleSection pattern, live MonsterMathEngine preview, undo stack, unsaved-changes guard, and Edit button wired from Library tab**

## Performance

- **Duration:** ~4 min
- **Started:** 2026-02-25T22:32:26Z
- **Completed:** 2026-02-25T22:36:02Z
- **Tasks:** 2 of 2
- **Files modified:** 3 (1 created + 2 modified)

## Accomplishments

- Created `src/ui/monster_editor.py` with CollapsibleSection helper and full MonsterEditorDialog (902 lines)
- MonsterEditorDialog: two-column layout (edit sections in scroll area left, MonsterDetailPanel preview right), toolbar with editable name + Save dropdown stub + Discard + Undo, five collapsible sections (Ability Scores expanded, four others collapsed by default)
- All edit changes call `MonsterMathEngine().recalculate()` and `MonsterDetailPanel.show_monster()` for live preview; `_recalculating` guard and `blockSignals()` prevent signal re-entry
- Undo stack stores `copy.deepcopy` snapshots; `_populate_form()` restores all widgets; closeEvent presents Save/Discard/Cancel guard
- Added `edit_requested Signal(object)` and Edit button to `MonsterDetailPanel`; wired through `MonsterLibraryTab._on_edit_monster()` to open dialog as modal
- All 485 existing tests pass with zero regressions

## Task Commits

Each task was committed atomically:

1. **Task 1: Create MonsterEditorDialog with core editing sections** - `ca5ff53` (feat)
2. **Task 2: Wire Edit button in Library tab to open MonsterEditorDialog** - `96b333d` (feat)

**Plan metadata:** (docs commit follows)

## Files Created/Modified

- `src/ui/monster_editor.py` - CollapsibleSection, MonsterEditorDialog with all 5 editing sections, toolbar, undo stack, closeEvent guard, monster_saved signal stub
- `src/ui/monster_detail.py` - Added `edit_requested = Signal(object)`, Edit QPushButton in name row, `_on_edit_clicked()` handler, enable/disable button on show/clear
- `src/ui/library_tab.py` - Imported MonsterEditorDialog and QDialog, connected `edit_requested` to `_on_edit_monster()`, added `_on_edit_monster()` method

## Decisions Made

- `_on_hp_changed()` writes flat HP only to `monster.hp`; the formula QLineEdit is UI state only because `Monster` has no `hp_formula` field — Plan 05 will store the formula via `MonsterModification.hp_formula` during persistence
- Save dropdown stubs: closeEvent "Save" button accepts and closes rather than hanging; Plan 05 replaces with real save logic
- `_apply_save_value()` removes ability from `saves` dict when Non-Prof is selected (clean dict = only proficient saves stored, matching Monster domain model convention)
- `reject()` is overridden to route through `close()` so pressing Escape triggers the closeEvent unsaved-changes guard rather than bypassing it

## Deviations from Plan

None - plan executed exactly as written.

## Issues Encountered

None.

## Next Phase Readiness

- Plan 04 (Equipment section UI): CollapsibleSection and MonsterEditorDialog are ready. `set_summary()` method on CollapsibleSection supports the equipment summary-in-header pattern Plan 04 requires.
- Plan 05 (Persistence round-trip): Save stubs are in place (`_save_override_stub`, `_save_copy_stub`, `monster_saved` signal). Plan 05 replaces the stubs with real save logic connecting MonsterModification persistence.

---
*Phase: 09-monster-editor-and-equipment-presets*
*Completed: 2026-02-25*
