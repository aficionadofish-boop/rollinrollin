---
phase: 02-monster-import-and-library
plan: 01
subsystem: parser
tags: [python, re, dataclasses, tdd, statblock, markdown, 5etools]

# Dependency graph
requires:
  - phase: 01-dice-engine-and-domain-foundation
    provides: "Domain models (Monster, Action, DamagePart) and test infrastructure"

provides:
  - "Extended Action with Optional[int] to_hit_bonus, raw_text, is_parsed fields"
  - "Extended Monster with creature_type, ability_scores, lore, raw_text fields"
  - "ParseResult and ParseFailure dataclasses in src/parser/models.py"
  - "5etools blockquote parser: parse_fivetools(content) -> ParseResult"
  - "Full TDD test suite for domain model extensions and parser (30 new tests)"

affects:
  - 02-monster-import-and-library
  - 03-library-ui

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Tolerant parse: missing required fields set incomplete=True with sentinel defaults; never raise"
    - "Never-drop-data: every action block stored with raw_text even if attack parsing fails"
    - "TDD RED-GREEN-REFACTOR: write failing tests first, then implement minimal code to pass"
    - "BLOCKQUOTE_PREFIX.sub to strip > prefix before applying field-level regex"
    - "ABILITY_CELL_RE.findall per line to extract all 6 ability scores from pipe table"
    - "HIT_LINE_RE with optional second group for multi-component damage (plus N (XdY) type)"

key-files:
  created:
    - "src/parser/__init__.py — parser package marker"
    - "src/parser/formats/__init__.py — formats subpackage marker"
    - "src/parser/models.py — ParseResult and ParseFailure dataclasses"
    - "src/parser/formats/fivetools.py — 5etools blockquote format parser"
    - "src/tests/test_parser_fivetools.py — TDD tests for fivetools parser (30 tests)"
  modified:
    - "src/domain/models.py — Action.to_hit_bonus Optional[int]; Action adds raw_text, is_parsed; Monster adds creature_type, ability_scores, lore, raw_text"
    - "src/tests/test_domain_models.py — 13 new tests for extended domain model fields and ParseResult/ParseFailure"

key-decisions:
  - "Action.to_hit_bonus: Optional[int] (not int) — non-attack actions (Multiattack, Gaze) have no attack roll"
  - "is_parsed=True only when to_hit_bonus is not None AND damage_parts is non-empty — a partial parse is not a successful parse"
  - "ParseResult.monsters typed as list (not list[Monster]) to avoid circular import between parser.models and domain.models"
  - "Lore collected as plain (non->) paragraphs immediately following each statblock block before next >## heading"
  - "creature_type extracted as first non-size word from '*Size Type, Alignment*' italic line"
  - "Segmentation anchors on >## headings (not blockquote boundaries) — reliable even when blank lines appear inside blockquotes"

patterns-established:
  - "Parser pattern: segment -> strip_blockquote -> extract fields -> build Monster"
  - "Action split pattern: find all ***Name.*** positions by regex, slice between positions"
  - "Multi-line action handling: join all non-blank lines before applying TO_HIT_RE and HIT_LINE_RE"

requirements-completed: [IMPORT-01, IMPORT-03, IMPORT-04, IMPORT-06, IMPORT-07]

# Metrics
duration: 4min
completed: 2026-02-23
---

# Phase 2 Plan 01: Domain Model Extensions and 5etools Parser Summary

**5etools blockquote statblock parser with tolerant field extraction, multi-component damage parsing, and extended domain models supporting Optional to_hit_bonus and creature_type/ability_scores**

## Performance

- **Duration:** 4 min
- **Started:** 2026-02-23T00:00:00Z
- **Completed:** 2026-02-23
- **Tasks:** 2
- **Files modified:** 7

## Accomplishments

- Extended domain models: Action gains Optional[int] to_hit_bonus, raw_text, is_parsed; Monster gains creature_type, ability_scores, lore, raw_text — all additive, zero regressions
- Created parser package (src/parser/) with ParseResult/ParseFailure dataclasses for the full Phase 2 parser pipeline
- Implemented parse_fivetools() that correctly extracts name, AC, HP, CR, creature_type, ability_scores (all 6), saving throws, and actions from real bestiary(1).md format including multi-component damage and multi-monster files
- 43 new tests added (13 domain model + 30 parser); full suite is 81 tests all green

## Task Commits

Each task was committed atomically:

1. **Task 1: Extend Domain Models + ParseResult Dataclasses** - `ada0dcc` (feat)
2. **Task 2: 5etools Format Parser (TDD against bestiary(1).md)** - `4e4e084` (feat)

_Note: Both TDD tasks went directly to GREEN without a separate RED commit — tests were written first, then implementation made them pass._

## Files Created/Modified

- `src/domain/models.py` — Action.to_hit_bonus is now Optional[int]; Action adds raw_text/is_parsed fields; Monster adds creature_type, ability_scores, lore, raw_text
- `src/tests/test_domain_models.py` — 13 new tests for extended fields and ParseResult/ParseFailure
- `src/parser/__init__.py` — Parser package marker
- `src/parser/formats/__init__.py` — Formats subpackage marker
- `src/parser/models.py` — ParseResult (monsters, failures, warnings) and ParseFailure (source_file, monster_name, reason) dataclasses
- `src/parser/formats/fivetools.py` — Full 5etools blockquote parser with _segment_blocks, _strip_blockquote, field extractors, action extraction, and parse_fivetools entry point
- `src/tests/test_parser_fivetools.py` — 30 TDD tests: Medusa basic fields, Snake Hair multi-damage, Multiattack raw_text, multi-monster files, incomplete flag, lore capture, no-statblock input

## Decisions Made

- Action.to_hit_bonus changed from `int` to `Optional[int]` — non-attack abilities (Multiattack, Petrifying Gaze) carry no attack roll; None is semantically correct vs any sentinel integer
- `is_parsed` is True only when BOTH to_hit_bonus is not None AND damage_parts is non-empty — partial parse results (to_hit with no damage, or damage with no to_hit) are still stored but flagged as unparsed to suppress roll buttons in UI
- ParseResult.monsters uses untyped `list` (not `list[Monster]`) to avoid circular import between src.parser.models and src.domain.models — both modules are stdlib-only with no cross-dependency
- Lore text is collected as plain paragraphs after each statblock ends and before the next `>##` heading — blank lines within lore are preserved as paragraph separators
- Segmentation uses `>##` heading scan (not blockquote boundary detection) for reliable multi-monster file splitting — blockquote regions can contain blank `>` lines which complicate boundary detection

## Deviations from Plan

None - plan executed exactly as written.

## Issues Encountered

None.

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness

- Parser foundation complete; parse_fivetools() ready for use in Phase 2 plan 02 (Homebrewery parser) and plan 03 (library service)
- domain/models.py extended with all fields required by library UI (creature_type for type column, ability_scores for detail panel, lore for expandable section)
- ParseResult/ParseFailure types ready for ImportResult accumulator in Phase 2 plan 05 (import log panel)
- All 81 tests green; no blockers

---
*Phase: 02-monster-import-and-library*
*Completed: 2026-02-23*
