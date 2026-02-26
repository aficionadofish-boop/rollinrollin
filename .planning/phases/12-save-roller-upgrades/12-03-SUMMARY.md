---
phase: 12-save-roller-upgrades
plan: 03
subsystem: ui
tags: [pyside6, feature-detection, save-roller, legendary-resistance, magic-resistance, detection-rules, sidebar-integration]

# Dependency graph
requires:
  - phase: 12-save-roller-upgrades
    plan: 01
    provides: "FeatureDetectionService, FeatureRule, BUILTIN_RULES, extended SaveParticipant/SaveParticipantResult"
  - phase: 12-save-roller-upgrades
    plan: 02
    provides: "EncounterSidebarDock.get_checked_members() API"
provides:
  - "SavesTab with three feature detection toggles (Is save magical?, MR detection, LR detection)"
  - "_SaveResultRow: per-row result widget with features column and LR 'Use?' button"
  - "_DetectionRulesPanel: collapsible QGroupBox with built-in + custom rule management"
  - "SavesTab.load_participants_from_sidebar() accepting (Monster, count) tuples"
  - "SavesTab.reset_lr_counters() for encounter-change lifecycle"
  - "MainWindow._on_sidebar_encounter_changed() auto-loading SavesTab on encounter change"
  - "MainWindow._on_tab_changed() auto-loading SavesTab checked members on tab switch"
  - "CT override flow: ct_send_overrides_sidebar controls whether CT or sidebar is authoritative"
  - "SettingsTab ct_send_overrides_sidebar QCheckBox"
affects:
  - "Any future plan that extends SavesTab feature detection or adds new rule types"

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "QFrame subclass for per-row result widgets with inline action buttons"
    - "QGroupBox with setCheckable(True)/setChecked(False) for collapsible panel"
    - "Monkey-patch monster_name onto SaveParticipantResult at roll time (DM-facing LR tracking)"
    - "LR counter dict keyed by base monster name (not participant name) for group LR pool"
    - "Signal chain: sidebar.encounter_changed -> _on_sidebar_encounter_changed -> load_participants_from_sidebar"

key-files:
  created: []
  modified:
    - src/ui/encounters_tab.py
    - src/ui/app.py
    - src/ui/settings_tab.py

key-decisions:
  - "Feature detection toggles placed after Advantage row and before Flat Modifier — visible before rolling"
  - "Detection Rules panel collapsed by default (setChecked(False)) to minimize visual noise for standard use"
  - "_SaveResultRow uses QFrame subclass with Signal — not QWidget — to allow stylesheet background-color on named class"
  - "LR counter NOT reset per roll — only reset_lr_counters() clears it (called on encounter change)"
  - "monster_name monkey-patched onto SaveParticipantResult at roll time — avoids adding field to domain dataclass"
  - "Tab switch to Saves only auto-loads if sidebar has checked members (no empty-list noise)"
  - "_on_sidebar_encounter_changed always resets LR counters — encounter change = fresh LR pool"

patterns-established:
  - "_DetectionRulesPanel pattern: QGroupBox checkable as collapsible container; rules_layout with stretch at end"
  - "Capture idx=i in lambda for delete buttons to avoid closure-variable capture bug"

requirements-completed: [SAVE-08, SAVE-09, SAVE-10, SAVE-11, SAVE-12, SAVE-13, SAVE-14]

# Metrics
duration: 4min
completed: 2026-02-26
---

# Phase 12 Plan 03: SavesTab UI Wiring — Feature Detection, LR Interaction, Sidebar Integration Summary

**Full-featured SavesTab with MR/LR feature detection toggles, collapsible detection rules panel, per-row result widgets with LR 'Use?' button, sidebar checked-member integration, and CT override setting**

## Performance

- **Duration:** ~4 min
- **Started:** 2026-02-26T06:14:50Z
- **Completed:** 2026-02-26T06:18:03Z
- **Tasks:** 2 of 2
- **Files modified:** 3

## Accomplishments

- Rebuilt `SavesTab` in `src/ui/encounters_tab.py` with feature detection infrastructure:
  - Three toggles: "Is save magical?", "MR detection", "LR detection"
  - `_DetectionRulesPanel`: collapsible QGroupBox showing built-in (MR auto-advantage, LR reminder) + custom rules with inline add/delete
  - `_SaveResultRow`: per-row QFrame with Features column, LR spinbox, "Use LR?" button, red/green tinting
  - `_execute_roll()` calls `FeatureDetectionService.detect_for_participant()` per creature before building SaveRequest
  - `_lr_counters` dict persists LR state across rolls within same encounter load
  - `load_participants_from_sidebar()` accepts `(Monster, count)` tuples from sidebar API
  - `reset_lr_counters()` clears session LR state on encounter change
- Updated `src/ui/app.py` MainWindow:
  - Passes `persistence_service` to `SavesTab` constructor
  - Connects `sidebar.encounter_changed` to `_on_sidebar_encounter_changed` (reloads SavesTab + resets LR)
  - Auto-loads checked sidebar members when DM switches to Saves tab
  - `_on_send_to_saves()` respects `ct_send_overrides_sidebar` setting
- Updated `src/ui/settings_tab.py`:
  - Added "Combat Tracker 'Send to Saves' overrides sidebar selection" checkbox to Combat Defaults group
  - Wired through `apply_settings()` and `current_settings()`

## Task Commits

Each task was committed atomically:

1. **Task 1: Rebuild SavesTab with feature detection toggles, detection rules panel, and per-row result widgets** - `fb81e7a` (feat)
2. **Task 2: Wire sidebar checked members and CT override setting into MainWindow** - `fcbc889` (feat)

## Files Created/Modified

- `src/ui/encounters_tab.py` - Full rework: _SaveResultRow, _DetectionRulesPanel, SavesTab with feature detection
- `src/ui/app.py` - persistence_service pass-through, encounter_changed connection, tab-switch auto-load, CT override logic
- `src/ui/settings_tab.py` - ct_send_overrides_sidebar QCheckBox in combat defaults group

## Decisions Made

- Feature detection toggles placed after Advantage row — visible prominently before rolling
- Detection Rules panel collapsed by default (QGroupBox setCheckable) to minimize visual noise for standard D&D sessions
- LR counters reset only on encounter change, not on each roll — critical for multi-roll LR tracking within a fight
- monster_name monkey-patched onto `SaveParticipantResult` at roll time (not added to domain dataclass) — avoids domain model churn for UI-layer concern
- Tab switch auto-load is conditional: only fires if sidebar has checked members (avoids noisy empty-participant message)

## Deviations from Plan

None - plan executed exactly as written.

## Issues Encountered

None.

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness

- All SAVE-08 through SAVE-14 requirements are implemented end-to-end
- SavesTab feature detection is complete; no blockers for Phase 13 (Theming)
- All 510 existing tests pass unchanged

---
*Phase: 12-save-roller-upgrades*
*Completed: 2026-02-26*

## Self-Check: PASSED

- src/ui/encounters_tab.py: FOUND
- src/ui/app.py: FOUND
- src/ui/settings_tab.py: FOUND
- .planning/phases/12-save-roller-upgrades/12-03-SUMMARY.md: FOUND
- Commit fb81e7a (Task 1): FOUND
- Commit fcbc889 (Task 2): FOUND
- 510 tests passing: CONFIRMED
