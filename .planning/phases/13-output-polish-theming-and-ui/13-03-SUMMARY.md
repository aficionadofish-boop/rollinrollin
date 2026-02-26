---
phase: 13-output-polish-theming-and-ui
plan: 03
subsystem: macro
tags: [macro, preprocessor, template-fields, roll20, datamodel]

# Dependency graph
requires:
  - phase: 05-roll20-macro-sandbox
    provides: MacroPreprocessor, CleanedMacro, MacroLineResult, MacroSandboxService
provides:
  - CleanedMacro.template_fields — (key, raw_value) tuples for all non-name {{key=value}} template fields
  - MacroLineResult.template_fields — same data propagated through service execution
  - _extract_template_fields returns 3-tuple (cleaned, template_name, fields)
affects: [13-05-template-card-rendering, any plan that renders template macro output]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Template fields captured as (key, raw_value) tuples; values are RAW (may contain [[...]] tokens)"
    - "Bare {{value}} fields excluded from template_fields (expression-only); only {{key=value}} pairs captured"

key-files:
  created: []
  modified:
    - src/macro/preprocessor.py
    - src/macro/models.py
    - src/macro/service.py

key-decisions:
  - "template_fields values are RAW — they may contain [[...]] inline roll tokens that haven't been resolved; Plan 05 (TemplateCard) will match resolved inline_results to field values by token order"
  - "Bare {{value}} fields (no = sign) are NOT added to template_fields — they are expression-only values"
  - "{{name=...}} is NOT duplicated in template_fields — it is captured as template_name only"

patterns-established:
  - "Data model extension pattern: add field with default_factory=list to both CleanedMacro and MacroLineResult so existing tests need no modification"
  - "Service propagation pattern: same macro.template_fields value added to all 5 MacroLineResult construction sites in execute() mechanically"

requirements-completed: [OUTPUT-03]

# Metrics
duration: 10min
completed: 2026-02-26
---

# Phase 13 Plan 03: Template Fields Data Model Summary

**Macro preprocessor extended to capture {{key=value}} template field labels as (key, raw_value) tuples in CleanedMacro.template_fields and MacroLineResult.template_fields, enabling labeled template card rows in Plan 05**

## Performance

- **Duration:** 10 min
- **Started:** 2026-02-26T10:21:05Z
- **Completed:** 2026-02-26T10:31:00Z
- **Tasks:** 2
- **Files modified:** 3

## Accomplishments
- Extended CleanedMacro and MacroLineResult with template_fields: list[tuple[str, str]] field (default_factory=list — backward compatible)
- Updated _extract_template_fields to return 3-tuple and accumulate (key, raw_value) for all non-name key=value fields
- Propagated template_fields from macro to MacroLineResult in all 5 execute() code paths in MacroSandboxService
- All 510 existing tests pass with zero modification

## Task Commits

Each task was committed atomically:

1. **Task 1: Extend preprocessor and models with template_fields** - `a90d987` (feat)
2. **Task 2: Propagate template_fields through MacroSandboxService** - `147329f` (feat)

**Plan metadata:** (docs commit — see final commit)

## Files Created/Modified
- `src/macro/preprocessor.py` - Added template_fields to CleanedMacro dataclass; updated _extract_template_fields to return 3-tuple with fields list; updated process_line to unpack and pass template_fields to CleanedMacro
- `src/macro/models.py` - Added template_fields: list[tuple[str, str]] field to MacroLineResult
- `src/macro/service.py` - Added template_fields=macro.template_fields to all 5 MacroLineResult constructions in execute()

## Decisions Made
- template_fields values are RAW — they may contain [[...]] inline roll tokens that haven't been resolved yet. For example, `{{damage=[[8d6]]}}` produces `("damage", "[[8d6]]")`. Plan 05 (TemplateCard) will need to match resolved inline_results to field values by token order.
- Bare {{value}} fields (no = sign) are NOT added to template_fields — expression-only
- {{name=...}} is NOT duplicated in template_fields — only captured as template_name

## Deviations from Plan

None - plan executed exactly as written.

## Issues Encountered

None.

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness
- template_fields data is now available in MacroLineResult for Plan 05 (TemplateCard rendering)
- The field flows from preprocessor through all service code paths
- Values may contain unresolved [[...]] tokens — Plan 05 must handle token-order matching to resolved inline_results

## Self-Check: PASSED

- FOUND: src/macro/preprocessor.py
- FOUND: src/macro/models.py
- FOUND: src/macro/service.py
- FOUND: .planning/phases/13-output-polish-theming-and-ui/13-03-SUMMARY.md
- FOUND: a90d987 (Task 1 commit)
- FOUND: 147329f (Task 2 commit)
- All 510 tests passed

---
*Phase: 13-output-polish-theming-and-ui*
*Completed: 2026-02-26*
