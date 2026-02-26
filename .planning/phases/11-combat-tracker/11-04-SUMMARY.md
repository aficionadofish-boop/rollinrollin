---
phase: 11-combat-tracker
plan: 04
subsystem: ui
tags: [pyside6, combat-tracker, pc-subtab, multi-select, rubber-band, aoe-damage, persistence]

# Dependency graph
requires:
  - phase: 11-03
    provides: GroupCard, initiative mode, turn cycling, drag-reorder, stat toggles, CombatTrackerTab base
  - phase: 10-02
    provides: EncounterSidebarDock.get_members(), SavesTab.load_participants()

provides:
  - PCSubtab with Add/Del PC rows, get_pcs()/set_pcs()/clear_pcs() API
  - CombatantListArea (QScrollArea subclass) with QRubberBand box drag selection
  - Ctrl-click toggle, Shift-click range, box-drag multi-select in CombatTrackerTab
  - AOE Damage button wired: applies same damage to all selected combatants
  - Send to Saves button: resolves selected combatants to SaveParticipant list, emits to MainWindow
  - start_combat_requested signal replaces no-op _on_start_combat
  - CombatTrackerTab wired into MainWindow (tab order: Library, Attack Roller, Combat Tracker, Saves, Macro Sandbox, Settings)
  - Sidebar hidden when Combat Tracker tab is active
  - Combat state and PCs persist via PersistenceService on autosave/close/startup
  - Flush integration for combat_state and player_characters categories

affects:
  - 12-save-roller (Send to Saves cross-tab flow provides integration point)
  - 13-theming (CombatTrackerTab now in main tab bar, subject to theme)

# Tech tracking
tech-stack:
  added: []
  patterns:
    - QRubberBand for box drag selection in QScrollArea subclass
    - start_combat_requested Signal pattern: tab signals MainWindow which reads sidebar, then calls tab method back
    - PCSubtab debounced pc_changed Signal (QTimer 500ms) for auto-save trigger
    - Sidebar hidden via setVisible(False) on tab change to Combat Tracker tab

key-files:
  created: []
  modified:
    - src/ui/combat_tracker_tab.py
    - src/ui/combatant_card.py
    - src/ui/app.py

key-decisions:
  - "card_clicked Signal on CombatantCard carries (combatant_id, Qt.KeyboardModifiers) so CombatTrackerTab handles all selection logic centrally"
  - "CombatantListArea (QScrollArea subclass) owns rubber-band state; emits box_selected(set[str]) to CombatTrackerTab"
  - "Send to Saves resolves combatants to SaveParticipant with CON save bonus by default; PCs without monster_name get save_bonus=0"
  - "start_combat_requested Signal: CombatTrackerTab tells MainWindow it needs encounter data; MainWindow reads sidebar and calls start_combat(members) — avoids tab needing sidebar reference"
  - "Combat state saved only when combatants list is non-empty to avoid overwriting good persisted state with empty dict"
  - "Sidebar setVisible(False) when Combat Tracker tab is active; setVisible(True) on any other tab (does not toggle collapsed state)"

patterns-established:
  - "Tab requests data from sibling via MainWindow signal chain: tab.signal → MainWindow._on_handler → sibling.method()"
  - "PCSubtab uses QTimer debounce (500ms) on pc_changed to avoid excessive autosave triggers"
  - "Multi-select action (damage/condition) applies to all selected_ids when len > 1 and the acted-on card is in the selection"

requirements-completed: [COMBAT-01, COMBAT-11, COMBAT-14, COMBAT-15]

# Metrics
duration: 45min
completed: 2026-02-26
---

# Phase 11 Plan 04: PC Subtab, Multi-Select, AOE Damage, MainWindow Wiring Summary

**PCSubtab with multi-select (Ctrl/Shift/box-drag), AOE damage, Send to Saves cross-tab flow, CombatTrackerTab wired into MainWindow with full persistence lifecycle**

## Performance

- **Duration:** ~45 min
- **Started:** 2026-02-26T00:00:00Z
- **Completed:** 2026-02-26T00:45:00Z
- **Tasks:** 2
- **Files modified:** 3

## Accomplishments

- PCSubtab lets DM add/edit/remove persistent player characters; PCs auto-join every combat's initiative
- Multi-select via Ctrl-click (toggle), Shift-click (range), and QRubberBand box drag in CombatantListArea subclass
- AOE Damage dialog applies same damage to all selected combatants via apply_aoe_damage()
- Send to Saves resolves selected combatants to SaveParticipant list; MainWindow switches to Saves tab
- Combat Tracker tab inserted into MainWindow at index 2 (Library, Attack Roller, Combat Tracker, Saves, Macro Sandbox, Settings)
- Combat state and PCs persist across app restarts via PersistenceService load/save lifecycle
- Sidebar hides when Combat Tracker is the active tab (combat log replaces sidebar visual role)
- Flush integration: combat_state and player_characters categories wired into Settings tab flush

## Task Commits

Each task was committed atomically:

1. **Task 1: PC subtab and multi-select with AOE damage** - `f4f7f7d` (feat)
2. **Task 2: MainWindow wiring and persistence lifecycle** - `0bb62bf` (feat)

## Files Created/Modified

- `src/ui/combat_tracker_tab.py` - Added PCSubtab, _PCRow, CombatantListArea, _AOEDamageDialog; wired multi-select, AOE damage, Send to Saves, start_combat_requested signal, persistence API (get_pcs/set_pcs/reset_combat_ui/clear_pcs)
- `src/ui/combatant_card.py` - Added card_clicked Signal (combatant_id, modifiers) to CombatantCard; emits on left mouse press
- `src/ui/app.py` - Added CombatTrackerTab import and construction, _on_start_combat/_on_send_to_saves handlers, persistence lifecycle wiring, sidebar visibility on tab change, flush category handlers for combat_state/player_characters

## Decisions Made

- `card_clicked` Signal on CombatantCard carries Qt.KeyboardModifiers so CombatTrackerTab handles all selection logic in one place (no inter-card communication needed).
- `CombatantListArea` subclasses QScrollArea and owns the rubber-band state, emitting `box_selected(set[str])` after mouse release. The inner widget's card layout is walked to find intersecting geometries.
- Send to Saves uses CON as the default save ability when resolving MonsterLibrary entries; PCs not in the library get `save_bonus=0` as a safe default.
- `start_combat_requested` Signal pattern: the tab does not hold a reference to the sidebar. MainWindow wires the signal to `_on_start_combat()` which reads `_sidebar.get_members()` and calls `start_combat(members)`.
- Combat state is saved only when `combatants` list is non-empty — prevents overwriting a good persisted state with an empty dict on a fresh session.

## Deviations from Plan

None — plan executed exactly as written. The plan's explicit guidance on rubber-band selection, signal chain, and sidebar visibility was followed directly.

## Issues Encountered

None.

## Next Phase Readiness

- Phase 11 (Combat Tracker) is now feature-complete: all planned requirements COMBAT-01, COMBAT-11, COMBAT-14, COMBAT-15 are implemented and persisted.
- Phase 12 (Save Roller enhancements) can use the Send to Saves cross-tab flow — SaveParticipant list is already emitted in the correct format.
- Phase 13 (Theming) will need to audit CombatTrackerTab widgets for stylesheet coverage.

---
*Phase: 11-combat-tracker*
*Completed: 2026-02-26*

## Self-Check: PASSED

- FOUND: src/ui/combat_tracker_tab.py
- FOUND: src/ui/combatant_card.py
- FOUND: src/ui/app.py
- FOUND: .planning/phases/11-combat-tracker/11-04-SUMMARY.md
- FOUND commit f4f7f7d (Task 1)
- FOUND commit 0bb62bf (Task 2)
- 510 tests passing, 0 failures
