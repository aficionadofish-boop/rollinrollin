---
phase: 11-combat-tracker
plan: 03
subsystem: ui
tags: [qt, pyside6, combat-tracker, grouping, initiative-mode, turn-cycling, drag-reorder, stat-toggle]

requires:
  - phase: 11-combat-tracker (plan 02)
    provides: CombatantCard, HpBar, CombatLogPanel, CombatTrackerTab skeleton
  - phase: 11-combat-tracker (plan 01)
    provides: CombatTrackerService, CombatantState, CombatState

provides:
  - src/ui/combatant_card.py (GroupCard, CompactSubRow added; CombatantCard drag support + set_stat_visible)
  - src/ui/combat_tracker_tab.py (initiative mode toggle, turn cycling, grouping, stat menu, drag-reorder)
  - src/combat/service.py (reorder_combatants, set_auto_regen, _auto_regen field)

affects:
  - Phase 11 Plan 04 (AOE damage, multi-select, Send to Saves, MainWindow wiring)

tech-stack:
  added: []
  patterns:
    - Three-level progressive disclosure (GroupCard collapsed → sub-rows → full card)
    - QDrag/QMimeData with custom MIME type for drag-to-reorder
    - _CardContainer drop target pattern — container handles drops, not individual cards
    - QToolButton checkable toggle for mode switching (initiative vs manual)
    - QMenu with checkable QActions for stat visibility toggles
    - Active turn highlight propagation: set_active_turn + set_member_active through GroupCard hierarchy

key-files:
  created: []
  modified:
    - src/ui/combatant_card.py
    - src/ui/combat_tracker_tab.py
    - src/combat/service.py

key-decisions:
  - "GroupCard uses a separate _members_container QWidget (hidden/shown) rather than rebuilding the whole frame — avoids layout thrashing on toggle"
  - "CompactSubRow intercepts mousePressEvent directly rather than using a button-only approach — click anywhere on the row to expand"
  - "Stat visibility defaults to False (hidden) for all toggleable stats — DM must opt in to show extra info"
  - "_CardContainer handles drops (not CombatantCards) so drag works regardless of which part of the card the drop lands on"
  - "_auto_regen defaults to False — auto-regen must be explicitly enabled via the Stats menu; advance_turn no longer applies regen unconditionally"
  - "GroupCard initiative spinbox emits initiative_changed for the first member only — groups share the same initiative roll so changing one changes all"
  - "set_stat_visible on GroupCard forwards only to expanded individual cards — collapsed group header does not show individual stat labels"

requirements-completed: [COMBAT-09, COMBAT-10, COMBAT-12, COMBAT-13]

duration: ~6min
completed: 2026-02-26
---

# Phase 11 Plan 03: Initiative Mode, Turn Cycling, Group Cards, and Stat Toggles Summary

**GroupCard three-level progressive disclosure, initiative mode toggle wiring Next/Prev Turn and Pass 1 Round, drag-to-reorder in manual mode, and a checkable stat visibility menu — all routed through CombatTrackerService as display-only widgets.**

## Performance

- **Duration:** ~6 min
- **Started:** 2026-02-26T04:58:46Z
- **Completed:** 2026-02-26T05:04:05Z
- **Tasks:** 2
- **Files modified:** 3

## Accomplishments

- GroupCard widget implements three-level progressive disclosure: collapsed "Nx Monster" card showing count, shared AC/initiative, and average HP bar across all group members; expanded compact sub-rows (CompactSubRow) showing individual HP bars, condition counts, and expand buttons with 20px left indent; individual full CombatantCard expansion when a sub-row is clicked
- CompactSubRow: 16px HP bar, condition chip count label, expand-to-full button, active member highlighting via set_active()
- GroupCard signals (damage_entered, condition_add_requested, condition_clicked, initiative_changed) pass through from individual cards or the group header to CombatTrackerTab
- CombatantCard gains drag-to-reorder via mousePressEvent/mouseMoveEvent emitting application/x-combatant-id MIME data
- CombatantCard.set_stat_visible() shows/hides individual stat labels; stats widget auto-shows/hides based on any-visible check
- Regen label added to CombatantCard stats widget (Regen: {hp})
- Initiative Mode QToolButton toggle: ON = Next/Prev Turn visible + sorted; OFF = Pass 1 Round visible + drag-to-reorder enabled
- _on_next_turn(): advance_turn() + log + refresh + active-turn highlight + auto-scroll via ensureWidgetVisible
- _on_previous_turn(): undo_advance() + log + refresh + highlight; shows "Nothing to undo" on failure
- _on_pass_one_round(): pass_one_round() + log + refresh round counter
- Active turn highlight: golden #FF9800 border + left-arrow ">" indicator on CombatantCard; same on GroupCard header with set_member_active() for member sub-rows
- Group toggle button: checked = auto-group enabled; unchecked = all individual cards
- Stats gear button: QMenu with checkable actions for speed, passive perception, legendary resistance, legendary actions, regeneration, and regen auto-apply toggle
- _CardContainer: drag-drop QWidget that computes insertion position from drop Y coordinate, emits reorder_requested
- CombatTrackerService.reorder_combatants(): reorders combatants list respecting initiative_mode guard, preserves current_turn_index
- CombatTrackerService.set_auto_regen() + _auto_regen field: advance_turn() now only auto-regens when _auto_regen=True

## Task Commits

Each task was committed atomically:

1. **Task 1: GroupCard widget and three-level progressive disclosure** — `2078a21` (feat)
2. **Task 2: Initiative mode, turn cycling, toggleable stats, drag-to-reorder** — `d478e8c` (feat)

## Files Created/Modified

- `src/ui/combatant_card.py` — Added GroupCard, CompactSubRow, drag support on CombatantCard, set_stat_visible(), regen label
- `src/ui/combat_tracker_tab.py` — Full rewrite of toolbar + card management to support initiative mode toggle, turn cycling, grouping, stat menu, drag-reorder
- `src/combat/service.py` — Added reorder_combatants(), set_auto_regen(), _auto_regen field; advance_turn() now gate-checks _auto_regen

## Decisions Made

- GroupCard uses a separate _members_container QWidget (hidden/shown) rather than rebuilding the whole QFrame — avoids layout thrashing on expand/collapse toggle.
- CompactSubRow intercepts mousePressEvent directly on the frame so clicking anywhere on the row expands it, not just the button.
- Stat visibility defaults to False (hidden) for all toggleable stats — DM must opt in via the Stats menu to see extra info per card.
- _CardContainer handles drops (not individual CombatantCards) so drag works regardless of which part of the card the pointer lands on during drop.
- _auto_regen defaults to False — auto-regen must be explicitly enabled via the Stats menu Regen Auto-Apply action; advance_turn() no longer auto-regens unconditionally.
- GroupCard initiative spinbox emits initiative_changed for the first group member only — groups share the same initiative roll.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] _auto_regen defaults to False instead of always-on**
- **Found during:** Task 2 — service.py advance_turn() previously always applied regen when regeneration_hp > 0; plan says to add _auto_regen flag and check it
- **Fix:** Added `self._auto_regen: bool = False` to __init__ and gated advance_turn() regen block behind `if self._auto_regen`
- **Files modified:** src/combat/service.py

## Issues Encountered

None beyond the regen flag defaulting noted above.

## User Setup Required

None — no external service configuration required.

## Next Phase Readiness

- Plan 04 can wire AOE Damage, multi-select, Send to Saves signal, and MainWindow tab integration
- Plan 04 wires start_combat() call from sidebar to CombatTrackerTab
- GroupCard.set_active_turn() and set_member_active() ready for active-turn highlight from any plan

## Self-Check: PASSED

Files verified:
- FOUND: src/ui/combatant_card.py
- FOUND: src/ui/combat_tracker_tab.py
- FOUND: src/combat/service.py
- FOUND: .planning/phases/11-combat-tracker/11-03-SUMMARY.md

Commits verified:
- 2078a21: feat(11-03): add GroupCard, CompactSubRow, and drag-to-reorder to combatant_card
- d478e8c: feat(11-03): wire initiative mode, turn cycling, grouping, stat toggles, drag-reorder

---
*Phase: 11-combat-tracker*
*Completed: 2026-02-26*
