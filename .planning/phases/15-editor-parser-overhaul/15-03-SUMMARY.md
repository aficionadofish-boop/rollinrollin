---
phase: 15-editor-parser-overhaul
plan: 03
subsystem: ui
tags: [python, pyside6, attack-roller, monster-detail, trait-buttons, dice-coloring, recharge, speed-display, double-bracket-notation]

# Dependency graph
requires:
  - phase: 15-editor-parser-overhaul
    plan: "01"
    provides: "Trait/DetectedDie dataclasses, Monster.traits/speed, Action.after_text, _extract_traits/_extract_speed in all three parsers"

provides:
  - "Rollable trait buttons in Attack Roller tab with Traits divider section"
  - "Per-die damage-type colored roll substitution in trait output (_format_trait_output)"
  - "Recharge 1d6 auto-roll with green/red pass/fail coloring in trait header"
  - "After-attack-text appended once per roll batch when hits occur (COMPARE) or always (RAW)"
  - "Speed line in MonsterDetailPanel stats section (hidden when empty)"
  - "Traits section in MonsterDetailPanel with bold-italic D&D statblock formatting"
  - "_render_double_bracket() replacing [[NdS]] with '{avg} [[NdS]]' in all displayed text"

affects:
  - "15-04 (editor UI — both files already wired for traits/speed display)"
  - "15-05 (any further UI polish — rollable traits and speed now render in library and editor preview)"

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Trait roll output: _format_trait_output escapes description, replaces full_match with colored span per damage type"
    - "Recharge display: recharge_range tuple (lo, hi) used for label and 1d6 pass/fail check, green #4CAF50 pass / red #E63946 fail"
    - "After-text display: stored separately as _last_after_text on tab, rendered once at end of _render_results only on hit (COMPARE) or always (RAW)"
    - "Speed row: QWidget wrapper for the speed row toggled visible/invisible rather than adding/removing layout items"
    - "Traits section: _clear_traits_layout + _add_trait_row pattern mirroring existing _clear_actions_layout + _add_action_row"
    - "[[XdY]] notation: _render_double_bracket() module-level function with DOUBLE_BRACKET_RE applied to trait descriptions, action raw_text, and extra effect text"

key-files:
  created: []
  modified:
    - "src/ui/attack_roller_tab.py — trait button row building in _rebuild_action_list, _make_trait_row, _on_roll_trait, _format_trait_output, after_text in _on_roll/_render_results"
    - "src/ui/monster_detail.py — speed row widget in setup/show/clear, traits section in setup/show/clear, _clear_traits_layout, _add_trait_row, _render_double_bracket module function, applied to action display text"

key-decisions:
  - "Trait button row insertion: rollable_traits filtered from monster.traits inside existing _rebuild_action_list loop — no separate rebuild method needed"
  - "After-text storage: _last_after_text field on AttackRollerTab rather than adding after_text to RollRequest — avoids domain model changes, matches existing _last_result pattern"
  - "After-text timing: displayed once after summary (or attacks in RAW mode) to avoid per-attack repetition across N rolls"
  - "RAW mode after-text: always shown (RAW has no hit concept); COMPARE mode: only shown when at least one hit occurred"
  - "Speed row visibility: QWidget wrapper toggled with setVisible(True/False) — cleaner than add/remove from layout"
  - "Traits section: separate header QLabel + container QWidget both toggled visible/invisible for clean show/hide without layout rebuilding"
  - "_render_double_bracket: module-level function (not method) for reuse potential; applied in _add_trait_row, unparsed action text, and extra effect text"

patterns-established:
  - "Trait output pattern: HTML escape full description, then replace HTML-escaped full_match strings with colored spans — safe HTML injection via targeted replacement"
  - "Speed/traits conditional visibility: QWidget row wrapper toggled via setVisible rather than layout manipulation"

requirements-completed: [PARSE-06, PARSE-07, PARSE-08, PARSE-09]

# Metrics
duration: 3min
completed: 2026-02-27
---

# Phase 15 Plan 03: Attack Roller Trait Buttons, Speed Display, and [[XdY]] Notation Summary

**Rollable trait buttons with damage-type coloring, recharge 1d6 support, after-attack-text on hits, monster speed display, traits in statblock, and [[XdY]] auto-average notation across all detail panel text**

## Performance

- **Duration:** ~3 min
- **Started:** 2026-02-27T23:36:09Z
- **Completed:** 2026-02-27T23:39:00Z
- **Tasks:** 2
- **Files modified:** 2

## Accomplishments
- Attack Roller now shows a "Traits" divider with roll buttons for all traits that have rollable dice (e.g. Acid Breath, Recharge 5-6)
- Clicking a trait button rolls all detected dice, substitutes results with per-damage-type colors, and auto-rolls 1d6 for recharge with green/red pass/fail header
- After-attack-text (Action.after_text) displayed once per roll batch: always in RAW mode, only when hits occur in COMPARE mode
- MonsterDetailPanel now shows Speed below the HP/CR/Type stats grid (hidden when no speed data)
- Traits section added to MonsterDetailPanel with bold-italic D&D statblock formatting (before Actions)
- _render_double_bracket() replaces [[NdS]] with auto-calculated average in all displayed text (trait descriptions, action raw_text, extra effect text)
- Zero test regressions: 510 tests pass

## Task Commits

Each task was committed atomically:

1. **Task 1: Add rollable trait buttons, recharge support, and after-text on hits** - `bcba422` (feat)
2. **Task 2: Add speed display, traits statblock section, and [[XdY]] auto-average rendering** - `926498a` (feat)

## Files Created/Modified
- `src/ui/attack_roller_tab.py` - Added Trait import, roll_expression import, _last_after_text field, trait button row building in _rebuild_action_list, _make_trait_row(), _on_roll_trait(), _format_trait_output(), after_text handling in _on_roll() and _render_results()
- `src/ui/monster_detail.py` - Added speed row widget, traits header/container section, _clear_traits_layout(), _add_trait_row(), _render_double_bracket() module function, applied to action display text paths

## Decisions Made
- After-text stored as `_last_after_text` on the tab instance rather than adding to `RollRequest` — avoids domain model changes, matches `_last_result` pattern
- RAW mode always shows after-text (no hit/miss concept); COMPARE mode shows only when at least one hit occurred
- Trait output uses HTML escaping on the full description first, then replaces HTML-escaped `full_match` strings — safe targeted HTML injection without re-parsing
- `_render_double_bracket` is a module-level function (not method) in monster_detail.py for potential reuse

## Deviations from Plan

None - plan executed exactly as written.

## Issues Encountered
None.

## User Setup Required
None - no external service configuration required.

## Next Phase Readiness
- All rollable trait UI complete: trait buttons visible in Attack Roller, trait descriptions in MonsterDetailPanel
- Speed display live in both library detail panel and editor preview (editor uses MonsterDetailPanel.show_monster)
- [[XdY]] notation renders automatically in all detail panel text paths
- Plan 04 and 05 can build on the complete trait/speed/after_text pipeline

---
*Phase: 15-editor-parser-overhaul*
*Completed: 2026-02-27*
