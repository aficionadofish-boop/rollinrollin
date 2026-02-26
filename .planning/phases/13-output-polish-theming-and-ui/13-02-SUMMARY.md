---
phase: 13-output-polish-theming-and-ui
plan: "02"
subsystem: ui
tags: [pyside6, html, qtextedit, damage-colors, rich-text]

# Dependency graph
requires:
  - phase: 09-monster-editing-and-attack-rolling
    provides: AttackRollerTab with plain-text _render_results and RollOutputPanel
provides:
  - RollOutputPanel.append_html() for HTML-formatted roll output
  - DAMAGE_COLORS palette for all 13 D&D 5e damage types
  - HTML-formatted attack roller output with per-type damage coloring
  - Gold crit row highlights and red miss row highlights
affects:
  - Any future phase that extends attack roller output formatting

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "HTML-first output rendering: _render_results uses append_html() exclusively after clear()"
    - "Parallel format methods: HTML variants (_format_*_html) coexist with plain-text (_format_*) methods"
    - "Module-level color palette: DAMAGE_COLORS dict as module constant, not class attribute"

key-files:
  created: []
  modified:
    - src/ui/roll_output.py
    - src/ui/attack_roller_tab.py

key-decisions:
  - "Physical damage types (slashing, piercing, bludgeoning) share neutral gray tones (#A0A8B0, #8A9BA8, #909090) — understated to let magical types pop"
  - "Magical damage types each get a distinct intuitive color: fire=orange-red, cold=ice-blue, lightning=gold, etc."
  - "Full damage segment (number + type label) is colored, not just the number"
  - "Crit lines use gold-tinted div background rgba(212,175,55,0.25); miss lines use red-tinted rgba(180,0,0,0.18)"
  - "All original plain-text format methods kept intact — HTML methods are additive, not replacements"
  - "append_html() uses QTextCursor.insertHtml() + End movement for correct scroll behavior"

patterns-established:
  - "HTML escape: _html_escape() called on any user-sourced text before HTML string construction"
  - "Damage span coloring: _color_damage_segment(total, dtype, note) produces <span style=color:X> wrapping entire segment"
  - "Row highlights: _wrap_crit_line() and _wrap_miss_line() wrap entire HTML line content in a styled <div>"

requirements-completed: [OUTPUT-01, OUTPUT-02]

# Metrics
duration: 2min
completed: 2026-02-26
---

# Phase 13 Plan 02: HTML-Rich Attack Roll Output with Damage Type Coloring Summary

**HTML-formatted attack roller output with per-type colored damage spans (13 D&D 5e types), gold crit row backgrounds, and red miss row backgrounds via QTextEdit.insertHtml()**

## Performance

- **Duration:** ~2 min
- **Started:** 2026-02-26T10:21:08Z
- **Completed:** 2026-02-26T10:23:27Z
- **Tasks:** 2
- **Files modified:** 2

## Accomplishments
- RollOutputPanel gains `append_html()` using QTextCursor.insertHtml() with proper End-positioning and auto-scroll; `setAcceptRichText(True)` made explicit
- DAMAGE_COLORS module-level dict maps all 13 D&D 5e damage types to hex colors (neutral grays for physical, distinct intuitive colors for magical)
- Full HTML format method suite added to AttackRollerTab: `_damage_str_html`, `_format_raw_line_html`, `_format_compare_line_html`, `_format_attack_line_html`, `_format_summary_html`
- `_render_results()` updated to use `append_html()` and HTML methods exclusively; all original plain-text methods kept intact
- `_html_escape()` helper protects user-sourced text (bonus dice labels) from HTML injection in output strings

## Task Commits

Each task was committed atomically:

1. **Task 1: Add append_html() to RollOutputPanel** - `3cbf71e` (feat)
2. **Task 2: Convert AttackRollerTab output to HTML with damage colors and crit/miss highlights** - `8818488` (feat)

**Plan metadata:** (docs commit — pending)

## Files Created/Modified
- `src/ui/roll_output.py` - Added `append_html()` method and explicit `setAcceptRichText(True)`, updated docstring
- `src/ui/attack_roller_tab.py` - Added DAMAGE_COLORS dict, HTML helper/format methods, updated `_render_results()`

## Decisions Made
- Physical damage types (slashing, piercing, bludgeoning) share neutral gray tones to feel understated; magical types each get a distinct intuitive color — per user decision from research phase
- Full damage segment (number + type label) is colored as a unit, not just the number — per user decision
- Crit row highlight uses gold tint `rgba(212,175,55,0.25)`, miss row uses red tint `rgba(180,0,0,0.18)` — `<div>` wrapping full line content
- All original plain-text format methods (`_format_raw_line`, `_format_compare_line`, `_damage_str`, `_format_summary`) kept intact for clipboard/future export use
- `append_html()` uses `QTextCursor.MoveOperation.End` positioning to avoid mode-mixing pitfalls with plain-text append on the same widget

## Deviations from Plan

None - plan executed exactly as written.

## Issues Encountered
None

## User Setup Required
None - no external service configuration required.

## Next Phase Readiness
- HTML output rendering fully operational; attack roller output is visually rich with per-type coloring
- Plan 13-03 (or subsequent plans) can build on this pattern for other output areas
- Clipboard copy already strips HTML automatically via `QTextEdit.toPlainText()` — no further work needed

## Self-Check: PASSED

- FOUND: src/ui/roll_output.py
- FOUND: src/ui/attack_roller_tab.py
- FOUND: .planning/phases/13-output-polish-theming-and-ui/13-02-SUMMARY.md
- FOUND commit: 3cbf71e (Task 1)
- FOUND commit: 8818488 (Task 2)

---
*Phase: 13-output-polish-theming-and-ui*
*Completed: 2026-02-26*
