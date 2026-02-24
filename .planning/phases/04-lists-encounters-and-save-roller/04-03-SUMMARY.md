---
phase: 04-lists-encounters-and-save-roller
plan: "03"
subsystem: ui
tags: [pyside6, drag-drop, encounters, save-roller, qtabwidget]

requires:
  - phase: 04-02
    provides: EncounterService, SaveRollService, SaveParticipant, SaveRequest, SaveRollResult

provides:
  - EncountersTab widget (QSplitter left=builder, right=Save Roller)
  - MonsterTableModel drag support (flags/mimeTypes/mimeData with application/x-monster-name)
  - EncounterMemberList drag-target widget with scroll area rows
  - MainWindow 'Encounters && Saves' third tab

affects:
  - 04-04 (any future plan referencing EncountersTab or encounter save/load UI)
  - 05-macros-and-workspace (will extend MainWindow tabs or encounter flow)

tech-stack:
  added: []
  patterns:
    - EncounterMemberList follows BonusDiceList pattern: dynamic rows in scroll area, insert-before-stretch
    - Drag MIME type application/x-monster-name: source model sets mimeData, EncounterMemberList.dropEvent decodes UTF-8
    - EncountersTab constructor receives library+roller from MainWindow (same pattern as AttackRollerTab)
    - QFileDialog for save/load starts in encounters/ workspace folder when workspace_manager provided

key-files:
  created:
    - src/ui/encounters_tab.py
  modified:
    - src/ui/monster_table.py
    - src/ui/library_tab.py
    - src/ui/app.py

key-decisions:
  - "EncounterMemberList receives library in __init__ for dropEvent resolution — avoids passing library at drop time"
  - "QFileDialog.getSaveFileName / getOpenFileName fall back to Path.home() when workspace_manager is None"
  - "_expand_participants defined in encounters_tab.py as module-level helper (mirrors service.py helper) to keep UI self-contained"
  - "Tab label 'Encounters && Saves' uses Qt '&&' convention (displays as 'Encounters & Saves')"

patterns-established:
  - "Drop target pattern: setAcceptDrops(True) + dragEnterEvent check hasFormat + dropEvent decode UTF-8 bytes"
  - "EncounterMemberList.add_monster deduplication: iterate rows, increment count on name match, else create new row"

requirements-completed: [ENC-01, ENC-02, ENC-06, LIST-01, LIST-02, LIST-05]

duration: 8min
completed: 2026-02-24
---

# Phase 4 Plan 3: Encounters Tab UI Summary

**Full Encounters & Saves tab with drag-from-library, encounter save/load via Markdown, and per-participant save roller with advantage/bonus dice and formatted output.**

## Performance

- **Duration:** ~8 min
- **Started:** 2026-02-24T02:55:00Z
- **Completed:** 2026-02-24T03:03:24Z
- **Tasks:** 2
- **Files modified:** 4

## Accomplishments
- Added drag support to MonsterTableModel (flags/mimeTypes/mimeData, MIME type application/x-monster-name)
- Built EncounterMemberList: scrollable widget with name label, count spinbox, and remove button per monster; accepts drops from Library table
- Built EncountersTab: left panel (encounter builder with name field, member list, New/Save/Load buttons, Load into Save Roller, unresolved entries panel); right panel (save type ToggleBar, DC spinbox, advantage ToggleBar, flat modifier, BonusDiceList, Roll Saves button, RollOutputPanel)
- Wired EncountersTab into MainWindow as third tab "Encounters && Saves"; 307 tests pass with no regressions

## Task Commits

1. **Task 1: Drag support + EncounterMemberList** - `c9b1ad9` (feat)
2. **Task 2: Full EncountersTab + MainWindow wire** - `e707aaf` (feat)

**Plan metadata:** (docs commit follows)

## Files Created/Modified
- `src/ui/encounters_tab.py` - New: EncounterMemberList + EncountersTab with full builder and save roller UI
- `src/ui/monster_table.py` - Added flags/mimeTypes/mimeData methods for drag support
- `src/ui/library_tab.py` - Added setDragEnabled(True) and setDefaultDropAction(CopyAction) on QTableView
- `src/ui/app.py` - Added EncountersTab import and third tab in MainWindow

## Decisions Made
- EncounterMemberList receives library in `__init__` for dropEvent name resolution; avoids needing it at drop time
- `_expand_participants` defined as module-level helper in encounters_tab.py (mirrors pattern from encounter/service.py) so the UI can call it directly after Load into Save Roller
- Tab label uses Qt `&&` convention: "Encounters && Saves" displays as "Encounters & Saves"
- File dialogs fall back to `Path.home()` when no workspace_manager is provided

## Deviations from Plan

None - plan executed exactly as written.

## Issues Encountered

None.

## Next Phase Readiness
- Encounters tab is complete; drag-drop, save/load, and save roller are all wired
- Phase 4 Plans 4 and 5 can proceed (workspace manager integration, polish)
- workspace_manager=None default means WorkspaceManager wiring can be added non-breakingly in a later plan

---
*Phase: 04-lists-encounters-and-save-roller*
*Completed: 2026-02-24*
