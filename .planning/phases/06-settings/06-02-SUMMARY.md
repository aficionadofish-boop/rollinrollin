---
phase: 06-settings
plan: 02
subsystem: ui
tags: [python, pyside6, settings, qt-signals, dirty-tracking]

# Dependency graph
requires:
  - phase: 06-settings
    plan: 01
    provides: AppSettings dataclass and SettingsService persistence layer
  - phase: 05-roll20-macro-sandbox
    provides: MacroSandboxTab with _result_panel (ResultPanel)
  - phase: 03-attack-roller
    provides: AttackRollerTab with _output_panel (RollOutputPanel)
  - phase: 04-lists-encounters-and-save-roller
    provides: EncountersTab with _dc_spin
provides:
  - SettingsTab QWidget with two-column grid, all settings controls, dirty tracking, settings_saved signal
  - AttackRollerTab.apply_defaults() and set_seeded_mode() methods
  - EncountersTab.apply_defaults() method
  - RollOutputPanel.set_seeded_mode() with green Seeded badge
  - ResultPanel.set_seeded_mode() with [seeded] timestamp suffix
  - MainWindow with 5 tabs, SettingsService wired, _apply_settings(), unsaved-changes guard
affects: [07-packaging]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - QGridLayout two-column settings layout with QGroupBox sections
    - blockSignals(True/False) around bulk widget updates to prevent spurious dirty triggers
    - Tab change guard: _on_tab_changed() checks previous tab index against settings tab index
    - Delegate set_seeded_mode() on tab classes rather than reaching into private panel attributes from MainWindow

key-files:
  created:
    - src/ui/settings_tab.py
  modified:
    - src/ui/app.py
    - src/ui/attack_roller_tab.py
    - src/ui/encounters_tab.py
    - src/ui/roll_output.py
    - src/ui/macro_result_panel.py

key-decisions:
  - "blockSignals(True/False) on SettingsTab around apply_settings() body prevents _mark_dirty firing during bulk widget assignment"
  - "set_seeded_mode() added as thin public method on AttackRollerTab delegating to _output_panel — avoids MainWindow reaching into private attributes"
  - "seed_value stored as None in AppSettings when seeded RNG is disabled; current_settings() returns None when unchecked"
  - "Advantage mode capitalization: settings field stores lowercase ('normal'), ToggleBar labels are capitalized ('Normal') — .capitalize() converts both directions"
  - "crit_range_spin range is 18-20 in SettingsTab (matches D&D expanded crit range feature)"

patterns-established:
  - "Settings apply pattern: apply_settings() uses blockSignals(True) + sets all widgets + blockSignals(False) + resets dirty flag"
  - "Tab owns seeded_mode state: set_seeded_mode() on each tab/panel stores bool and uses it on next render"

requirements-completed: [SET-01, SET-02, SET-03, SET-04]

# Metrics
duration: 4min
completed: 2026-02-24
---

# Phase 6 Plan 02: Settings Tab UI Summary

**SettingsTab QWidget with two-column grid (RNG, Combat Defaults, AC/DC, Output) wired into MainWindow with apply_defaults(), seeded RNG badge, and unsaved-changes guard**

## Performance

- **Duration:** 4 min
- **Started:** 2026-02-24T06:47:14Z
- **Completed:** 2026-02-24T06:51:53Z
- **Tasks:** 2
- **Files modified:** 6 (1 created, 5 modified)

## Accomplishments
- SettingsTab with full two-column grid layout: RNG group (seed toggle + spinbox), Combat Defaults (advantage ToggleBar, GWM/SS, crit enabled, crit range, nat-1, nat-20), Default AC/DC group, Output mode toggle
- Dirty tracking with Save button that starts disabled; enables on any widget change; resets after save
- settings_saved Signal(AppSettings) emitted on save; apply_settings()/is_dirty()/current_settings()/save()/discard() public API
- AttackRollerTab.apply_defaults() applies mode, advantage, nat-1, nat-20, crit settings, target AC; stores GWM/SS default
- EncountersTab.apply_defaults() sets save DC spinbox
- RollOutputPanel.set_seeded_mode() shows/hides green "Seeded" badge label
- ResultPanel.set_seeded_mode() appends "[seeded]" to timestamp divider on roll results
- MainWindow: SettingsService loads settings at startup, all tabs initialized with apply_defaults(), shared Roller re-seeded in place, QMessageBox Save/Discard guard on tab leave, seeded badge applied to both output panels

## Task Commits

Each task was committed atomically:

1. **Task 1: Build SettingsTab UI widget and add apply_defaults to existing tabs** - `6245bef` (feat)
2. **Task 2: Wire SettingsTab into MainWindow with settings loading, apply_defaults, seed wiring, and unsaved-changes guard** - `b931fc1` (feat)

## Files Created/Modified
- `src/ui/settings_tab.py` - New SettingsTab QWidget with two-column grid, all controls, dirty tracking, settings_saved signal
- `src/ui/app.py` - MainWindow wired with SettingsService, SettingsTab, _apply_settings(), _on_settings_saved(), _on_tab_changed() guard
- `src/ui/attack_roller_tab.py` - Added apply_defaults(settings) and set_seeded_mode(bool) delegation methods
- `src/ui/encounters_tab.py` - Added apply_defaults(settings) method setting _dc_spin
- `src/ui/roll_output.py` - Added _seeded_label QLabel and set_seeded_mode(bool) method
- `src/ui/macro_result_panel.py` - Added _seeded_mode state and set_seeded_mode(bool); [seeded] appended to timestamp divider

## Decisions Made
- `blockSignals(True/False)` on SettingsTab around `apply_settings()` body — prevents _mark_dirty() from firing during bulk widget assignment after load; `_dirty = False` explicitly reset after unblock
- `set_seeded_mode()` added as thin public method on AttackRollerTab rather than MainWindow reaching into `_attack_roller_tab._output_panel` — cleaner encapsulation
- `seed_value` is set to `None` in `current_settings()` when seeded RNG is disabled — consistent with AppSettings typing (`Optional[int]`)
- Advantage mode uses `.capitalize()` to convert stored values ("normal") to ToggleBar labels ("Normal") in both `apply_settings()` and `apply_defaults()`
- Crit range spinbox in SettingsTab uses range 18-20 matching D&D expanded crit range feature (vs 2-20 in AttackRollerTab which allows any custom range)

## Deviations from Plan

None — plan executed exactly as written.

## Issues Encountered

None.

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness
- Complete settings pipeline: model (06-01) + UI + MainWindow wiring (06-02) fully delivered
- Phase 7 (packaging) can begin; all UI features are now complete
- WorkspaceManager.root confirmed as Path attribute — SettingsService(workspace_manager.root) is the correct constructor call

---
*Phase: 06-settings*
*Completed: 2026-02-24*

## Self-Check: PASSED

- FOUND: src/ui/settings_tab.py
- FOUND: src/ui/app.py
- FOUND: src/ui/attack_roller_tab.py
- FOUND: src/ui/encounters_tab.py
- FOUND: src/ui/roll_output.py
- FOUND: src/ui/macro_result_panel.py
- FOUND: .planning/phases/06-settings/06-02-SUMMARY.md
- FOUND commit: 6245bef (feat - Task 1)
- FOUND commit: b931fc1 (feat - Task 2)
