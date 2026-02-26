---
phase: 13-output-polish-theming-and-ui
plan: "05"
subsystem: ui
tags: [macro, template-card, roll20, pyside6, theming, accent-color, qframe]

# Dependency graph
requires:
  - phase: 13-01
    provides: ThemeService with get_accent_color(), MainWindow.get_theme_service(), AppSettings theme fields
  - phase: 13-03
    provides: MacroLineResult.template_fields and MacroLineResult.template_name populated from preprocessor
affects: []

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "TemplateCard dispatched from ResultPanel based on lr.template_name and lr.template_fields presence"
    - "Accent color propagation: app.py _apply_settings -> MacroSandboxTab.set_accent_color -> ResultPanel.set_accent_color"
    - "_resolve_field_values: left-to-right token order matching [[...]] to inline_results"

key-files:
  created: []
  modified:
    - src/ui/macro_result_panel.py
    - src/ui/macro_sandbox_tab.py
    - src/ui/app.py

key-decisions:
  - "TemplateCard dispatch condition is lr.template_name AND lr.template_fields — template with name but no fields falls back to ResultCard (card would be empty except header)"
  - "Accent color stored as instance variable on ResultPanel; updated via set_accent_color() called on theme change"
  - "app.py accent color wiring uses hasattr guard on _macro_tab for safety during init ordering"
  - "_resolve_field_values uses left-to-right token matching by index — relies on preprocessor and inline roll resolution both processing left-to-right"

patterns-established:
  - "TemplateCard pattern: QFrame with colored header (accent_color param) and labeled key/value rows from template_fields"
  - "Token resolution pattern: regex replace [[...]] tokens in raw field values with resolved dice totals by index"

requirements-completed: [OUTPUT-04]

# Metrics
duration: 2min
completed: 2026-02-26
---

# Phase 13 Plan 05: Template Card Rendering Summary

**TemplateCard QFrame widget renders Roll20 template macros as styled cards with an accent-colored header and labeled key/value rows; ResultPanel dispatches between TemplateCard and ResultCard based on template_name presence**

## Performance

- **Duration:** 2 min
- **Started:** 2026-02-26T10:29:35Z
- **Completed:** 2026-02-26T10:31:19Z
- **Tasks:** 2
- **Files modified:** 3

## Accomplishments
- Created TemplateCard(QFrame) with accent-colored header, labeled key/value rows from template_fields, inline [[...]] token resolution, and warning display
- ResultPanel._accent_color instance variable initialized to dark theme default (#4DA6FF); set_accent_color() enables live theme updates
- ResultPanel.add_roll_result() dispatches to TemplateCard when lr.template_name and lr.template_fields are both set; falls back to ResultCard otherwise
- MacroSandboxTab.set_accent_color() forwards to ResultPanel
- app.py _apply_settings() calls self._macro_tab.set_accent_color(accent) after ThemeService.apply() so header color matches active theme on every settings save

## Task Commits

Each task was committed atomically:

1. **Task 1: Create TemplateCard widget** - `5d419ce` (feat)
2. **Task 2: Wire ResultPanel to dispatch TemplateCard for template macros** - `2d35fba` (feat)

**Plan metadata:** (docs commit follows)

## Files Created/Modified
- `src/ui/macro_result_panel.py` - Added TemplateCard class with header, key/value rows, inline resolution, warnings; added _accent_color and set_accent_color() to ResultPanel; updated add_roll_result() dispatch
- `src/ui/macro_sandbox_tab.py` - Added set_accent_color() method forwarding to result panel
- `src/ui/app.py` - Added accent color wiring in _apply_settings() after ThemeService.apply()

## Decisions Made
- TemplateCard dispatch requires both template_name AND template_fields to be truthy — a template macro with only a name and no key/value fields renders as a ResultCard (empty header-only card is not useful)
- Accent color stored as `_accent_color` on ResultPanel; initialized to dark theme default so existing behavior is unchanged before any theme switch
- The `hasattr(self, '_macro_tab')` guard in app.py is defensive — _macro_tab always exists by the time _apply_settings is called, but the guard makes init-ordering robust
- _resolve_field_values processes tokens left-to-right by index, matching the preprocessor and inline roll resolver ordering guarantees established in Plan 03

## Deviations from Plan

None - plan executed exactly as written.

## Issues Encountered

None.

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness
- TemplateCard is live and tested; all 510 existing tests pass
- Template macros (e.g., `&{template:default}{{name=Fireball}}{{DC=15}}`) now render as styled cards with labeled rows
- Accent color updates on theme change via the _apply_settings wiring
- Phase 13 plans 01-05 all complete; phase is finished

## Self-Check: PASSED

- FOUND: src/ui/macro_result_panel.py
- FOUND: src/ui/macro_sandbox_tab.py
- FOUND: src/ui/app.py
- FOUND: 5d419ce (Task 1 commit)
- FOUND: 2d35fba (Task 2 commit)
- All 510 tests passed

---
*Phase: 13-output-polish-theming-and-ui*
*Completed: 2026-02-26*
