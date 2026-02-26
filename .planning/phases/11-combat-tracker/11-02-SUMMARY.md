---
phase: 11-combat-tracker
plan: 02
subsystem: ui
tags: [qt, pyside6, combat-tracker, hp-bar, paintEvent, custom-widget, conditions]

requires:
  - phase: 11-combat-tracker (plan 01)
    provides: CombatTrackerService, CombatantState, CombatState, ConditionEntry, STANDARD_CONDITIONS, COMMON_BUFFS
provides:
  - src/ui/hp_bar.py (HpBar QWidget with paintEvent color zones and click signal)
  - src/ui/combatant_card.py (CombatantCard QFrame with full signal wiring)
  - src/ui/combat_log_panel.py (CombatLogPanel with round-prefixed entries and clipboard)
  - src/ui/combat_tracker_tab.py (CombatTrackerTab skeleton with toolbar, cards, log)
affects:
  - Phase 11 Plan 03 (initiative ordering, turn navigation, grouping)
  - Phase 11 Plan 04 (AOE damage, multi-select, Send to Saves wiring)

tech-stack:
  added: []
  patterns:
    - Custom paintEvent widget (HpBar) — no Qt stylesheets, direct QPainter drawing
    - Click-to-reveal input pattern — HP bar click toggles a hidden QLineEdit next to it
    - Display-only cards — CombatantCard holds NO HP state; refresh() pulls from CombatantState
    - blockSignals guard on QSpinBox — _recalculating flag + blockSignals(True/False) pattern
    - Condition chip as QLabel subclass — mousePressEvent emits named signal

key-files:
  created:
    - src/ui/hp_bar.py
    - src/ui/combatant_card.py
    - src/ui/combat_log_panel.py
    - src/ui/combat_tracker_tab.py
  modified: []

key-decisions:
  - "HpBar uses direct QPainter in paintEvent — no Qt stylesheets for the bar itself (avoids stylesheet z-order issues with overlapping segments)"
  - "_ConditionChip subclasses QLabel with mousePressEvent override — installEventFilter avoided for simplicity since each chip has its own condition name"
  - "CombatTrackerTab._on_start_combat is a no-op without encounter members — actual start_combat(members) called by MainWindow in Plan 04 wiring"
  - "Initiative spinbox prefix 'Init ' chosen over suffix to differentiate from count spinboxes"

patterns-established:
  - "Display-only card pattern: all widget constructors accept a state object; refresh(state) is the only update path"
  - "Signal-out-only pattern: cards emit signals for every user action; no direct service calls from card layer"

requirements-completed: [COMBAT-01, COMBAT-02, COMBAT-03, COMBAT-04, COMBAT-05, COMBAT-06, COMBAT-07, COMBAT-08, COMBAT-15]

duration: 3min
completed: 2026-02-26
---

# Phase 11 Plan 02: Combat Tracker UI Components Summary

**Custom paintEvent HP bar with green/yellow/red zones and blue temp HP overlay, CombatantCard with condition chips and signal-out-only architecture, CombatLogPanel, and CombatTrackerTab skeleton with toolbar and Start Combat button.**

## Performance

- **Duration:** ~3 min
- **Started:** 2026-02-26T04:52:17Z
- **Completed:** 2026-02-26T04:55:28Z
- **Tasks:** 2
- **Files modified:** 4 (all new)

## Accomplishments

- HpBar QWidget renders three color zones via paintEvent: green (>50%), yellow (>25%), red (<=25%), plus blue temp HP segment stacked to the right of the HP segment
- CombatantCard displays name with strikethrough on defeat, AC badge, initiative spinbox with blockSignals guard, condition chips with per-condition colors, and click-to-reveal damage input
- CombatLogPanel appends round-prefixed entries, supports copy-to-clipboard, load_entries/get_entries for persistence roundtrip
- CombatTrackerTab orchestrates all cards via CombatTrackerService, exposes start_combat/load_combat_state/get_combat_state for MainWindow wiring

## Task Commits

Each task was committed atomically:

1. **Task 1: HpBar widget and CombatantCard widget** - `530e491` (feat)
2. **Task 2: CombatLogPanel and CombatTrackerTab skeleton** - `75ea498` (feat)

**Plan metadata:** (docs commit follows)

## Files Created/Modified

- `src/ui/hp_bar.py` - Custom QWidget HP bar with paintEvent, green/yellow/red segments, blue temp HP, click signal
- `src/ui/combatant_card.py` - Wide horizontal combatant card with CONDITION_COLORS map, chip subclass, damage input, refresh API
- `src/ui/combat_log_panel.py` - Timestamped combat log with copy-to-clipboard, clear, load/get for persistence
- `src/ui/combat_tracker_tab.py` - Main tab with QSplitter layout, toolbar (Start/Roll Initiative/Reset), card management, condition popup menus

## Decisions Made

- HpBar uses direct QPainter in paintEvent with no Qt stylesheets for the bar itself — avoids stylesheet z-order issues that arise when multiple overlapping fill rects need to respect each other's boundaries.
- _ConditionChip subclasses QLabel with mousePressEvent override — installEventFilter avoided for simplicity since each chip captures its own condition name in the closure.
- CombatTrackerTab._on_start_combat shows an informational QMessageBox when no encounter is loaded — actual start_combat(members) is called by MainWindow in Plan 04 wiring, not from this button directly.
- Initiative spinbox uses prefix "Init " rather than suffix to visually differentiate it from count spinboxes on the same row.

## Deviations from Plan

None — plan executed exactly as written.

## Issues Encountered

None.

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness

- HpBar, CombatantCard, CombatLogPanel, and CombatTrackerTab all importable and wired
- Plan 03 can wire Next/Previous Turn and Pass 1 Round buttons (already placed but hidden)
- Plan 03 can wire the Stats gear button for toggleable stat columns
- Plan 04 can wire AOE Damage, Send to Saves, and multi-select logic
- MainWindow integration (adding the Combat Tracker tab) happens in Plan 04

## Self-Check: PASSED

Files verified:
- FOUND: src/ui/hp_bar.py
- FOUND: src/ui/combatant_card.py
- FOUND: src/ui/combat_log_panel.py
- FOUND: src/ui/combat_tracker_tab.py
- FOUND: .planning/phases/11-combat-tracker/11-02-SUMMARY.md

Commits verified:
- 530e491: feat(11-02): add HpBar widget and CombatantCard widget
- 75ea498: feat(11-02): add CombatLogPanel and CombatTrackerTab skeleton

---
*Phase: 11-combat-tracker*
*Completed: 2026-02-26*
