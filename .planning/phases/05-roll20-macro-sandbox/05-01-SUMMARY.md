---
phase: 05-roll20-macro-sandbox
plan: 01
subsystem: macro
tags: [roll20, macro, preprocessor, dice, tdd, regex, python]

# Dependency graph
requires:
  - phase: 01-dice-engine-and-domain-foundation
    provides: roll_expression(), Roller, DiceResult — macro preprocessor calls roll_expression() for inline roll resolution and final evaluation
provides:
  - src/macro/__init__.py package marker
  - src/macro/models.py with MacroWarning, MacroLineResult, MacroRollResult dataclasses
  - src/macro/preprocessor.py with MacroPreprocessor (process_line, resolve_inline_rolls, substitute_queries)
  - src/macro/service.py with MacroSandboxService (preprocess_all_lines, collect_all_queries, execute)
  - WORKSPACE_SUBFOLDERS updated to include "macros"
  - TDD test suites for preprocessor (16 tests) and service (16 tests)
affects:
  - 05-02 (MacroSandboxTab UI — consumes MacroSandboxService and MacroPreprocessor)
  - 05-03 (workspace macro file I/O — uses macros/ subfolder)

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Iterative inner-first [[inline roll]] resolution: loop _INLINE_ROLL_RE.search() until no matches, always finding the innermost (non-nested) bracket"
    - "Expression normalization: collapse ++ -> +, +- -> -, -+ -> -, -- -> + before roll_expression()"
    - "Two-phase service pattern: preprocess_all_lines() + collect_all_queries() before query panel, then execute() after answers collected"
    - "Query deduplication by raw token text (.raw field) — same ?{...} in multiple lines asked once"
    - "@{attr} stripped to empty string (not 0); resulting invalid expressions caught by try/except on roll_expression()"

key-files:
  created:
    - src/macro/__init__.py
    - src/macro/models.py
    - src/macro/preprocessor.py
    - src/macro/service.py
    - src/tests/test_macro_preprocessor.py
    - src/tests/test_macro_service.py
  modified:
    - src/workspace/setup.py
    - src/tests/test_workspace.py

key-decisions:
  - "[05-01]: @{attr} stripped to empty string (not 0) — substituting 0 creates semantically wrong results; empty string causes ParseError that is caught and reported as an error with warning"
  - "[05-01]: Iterative inner-first [[inline roll]] resolution via while loop — handles nested [[1d20+[[1d4]]]] correctly without custom parser"
  - "[05-01]: Double-sign normalization (++/+- etc.) done in service layer, not preprocessor — preprocessor is stateless text parser; normalization is execution-time concern"
  - "[05-01]: collect_all_queries deduplicates by .raw token text — same ?{...} in multiple lines should only prompt once"
  - "[05-01]: test_initialize_partial updated to derive expected set from WORKSPACE_SUBFOLDERS minus pre-created set — future subfolder additions won't break this test"

patterns-established:
  - "MacroPreprocessor is stateless — process_line, resolve_inline_rolls, substitute_queries are all pure transforms with no instance state"
  - "Service lazy-imports roll_expression inside execute() to match project import convention"
  - "TDD: write failing test file, commit RED, implement, all tests pass, commit GREEN"

requirements-completed: [SAND-01, SAND-03, SAND-05, SAND-06, SAND-07]

# Metrics
duration: 4min
completed: 2026-02-24
---

# Phase 5 Plan 01: Macro Preprocessor and Service Summary

**Pure-Python MacroPreprocessor and MacroSandboxService with TDD coverage: /roll stripping, iterative nested [[inline roll]] resolution, ?{query} extraction, @{attr}/@&{template} warning generation, and expression normalization**

## Performance

- **Duration:** ~4 min
- **Started:** 2026-02-24T00:00:00Z
- **Completed:** 2026-02-24T00:04:00Z
- **Tasks:** 2 (each with RED + GREEN phases)
- **Files modified:** 8

## Accomplishments

- MacroPreprocessor handles all Roll20 token types: /roll prefix stripping, [[inline roll]] resolution (including nested), ?{query} extraction, @{attr} and &{template:...} warning generation
- MacroSandboxService orchestrates multi-line input with query collection (deduplicated), expression normalization (++ -> +, +- -> -), inline roll resolution, and graceful error handling
- Full TDD suite: 16 preprocessor tests + 16 service tests, all pass; 339 total tests, 0 regressions
- WORKSPACE_SUBFOLDERS updated to include "macros" subfolder for future macro file persistence

## Task Commits

Each task was committed atomically:

1. **Task 1 RED: Failing tests for MacroPreprocessor** - `cacd050` (test)
2. **Task 1 GREEN: MacroPreprocessor + models + workspace update** - `7b45042` (feat)
3. **Task 2 RED: Failing tests for MacroSandboxService** - `17e766b` (test)
4. **Task 2 GREEN: MacroSandboxService + workspace test fix** - `a01cea8` (feat)

_Note: TDD tasks have multiple commits (test RED -> feat GREEN)_

## Files Created/Modified

- `src/macro/__init__.py` - Package marker for macro module
- `src/macro/models.py` - MacroWarning, MacroLineResult (has_result/has_warnings properties), MacroRollResult dataclasses
- `src/macro/preprocessor.py` - MacroPreprocessor with process_line(), resolve_inline_rolls(), substitute_queries(), _parse_query(); QuerySpec, ParseWarning, CleanedMacro dataclasses
- `src/macro/service.py` - MacroSandboxService with preprocess_all_lines(), collect_all_queries(), execute(); _normalize_expression() helper
- `src/workspace/setup.py` - Added "macros" to WORKSPACE_SUBFOLDERS tuple
- `src/tests/test_macro_preprocessor.py` - 16 TDD tests for MacroPreprocessor
- `src/tests/test_macro_service.py` - 16 TDD tests for MacroSandboxService
- `src/tests/test_workspace.py` - Updated test_initialize_partial to derive expected set from WORKSPACE_SUBFOLDERS

## Decisions Made

- `@{attr}` stripped to empty string (not `0`): substituting `0` would produce a semantically wrong result (e.g., `1d20+0` passes silently but the DM gets no warning their attr was missing). Empty string causes `ParseError` caught by the service, producing a proper error result alongside the `ParseWarning`.
- Iterative inner-first `[[inline roll]]` resolution: `_INLINE_ROLL_RE` (`[^\[\]]+`) never matches `[[` inside, so each pass of `while _INLINE_ROLL_RE.search()` finds the innermost bracket. This handles `[[1d20+[[1d4]]]]` correctly without a custom nested parser.
- Expression normalization in service layer (not preprocessor): the preprocessor is a pure text parser; normalization is an execution-time concern because the normalization input depends on what answer the user chose for `?{...}` queries.
- `collect_all_queries` deduplicates by `.raw` token text: if `?{Mod|STR,+2}` appears on lines 1 and 3, the user is asked only once. The single chosen value is substituted in both lines during `execute()`.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] Updated test_initialize_partial to use WORKSPACE_SUBFOLDERS dynamically**
- **Found during:** Task 2 GREEN verification (full test suite run)
- **Issue:** `test_initialize_partial` hardcoded `{"encounters", "exports"}` — adding "macros" to `WORKSPACE_SUBFOLDERS` broke it because the test didn't know about the new folder
- **Fix:** Changed assertion to `set(WORKSPACE_SUBFOLDERS) - {"monsters", "lists"}` — derives expected set from the actual constant, so future additions are covered automatically
- **Files modified:** `src/tests/test_workspace.py`
- **Verification:** All 339 tests pass including `test_initialize_partial`
- **Committed in:** `a01cea8` (Task 2 GREEN commit)

---

**Total deviations:** 1 auto-fixed (Rule 1 — Bug)
**Impact on plan:** Auto-fix was necessary to maintain test suite correctness after workspace update. No scope creep.

## Issues Encountered

None — implementation matched the RESEARCH.md Pattern 1 and Pattern 2 exactly. The iterative inline roll resolution correctly handles nested brackets without any additional complexity.

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness

- `MacroPreprocessor` and `MacroSandboxService` are complete and fully tested
- `src/macro/` package ready for consumption by `MacroSandboxTab` (Phase 5 Plan 02)
- `macros/` workspace subfolder registered — ready for file persistence (Phase 5 Plan 03)
- Concern resolved: `QDialog.exec()` pattern NOT used — inline `QWidget` + signals pattern confirmed in RESEARCH.md Pattern 5 for the query panel in 05-02

## Self-Check: PASSED

All files found, all commits verified, 32 macro tests pass (16 preprocessor + 16 service), 339 total tests pass.

---
*Phase: 05-roll20-macro-sandbox*
*Completed: 2026-02-24*
