---
phase: 15-editor-parser-overhaul
plan: 01
subsystem: parser
tags: [python, dataclasses, regex, statblock, trait-extraction, domain-models]

# Dependency graph
requires:
  - phase: 14-bug-fixes-critical-polish
    provides: "extract_named_section(), extract_all_sections(), SECTION_BOUNDARY_RE — shared parser infrastructure Plans 02/03 depend on"

provides:
  - "DetectedDie dataclass with full_match, dice_expr, damage_type, average fields"
  - "Trait dataclass with name, description, rollable_dice, recharge_range fields"
  - "Monster.traits (list[Trait]) and Monster.speed (str) fields with backward-compatible defaults"
  - "Action.after_text (str) field with backward-compatible default"
  - "SPEED_RE, DICE_IN_TRAIT_RE, RECHARGE_RE shared regex patterns in _shared_patterns.py"
  - "detect_dice_in_text(), detect_recharge(), extract_speed() helper functions in _shared_patterns.py"
  - "_extract_traits() and _extract_speed() in all three format parsers (fivetools, homebrewery, plain)"
  - "Action.after_text populated from text after hit/damage match in all three parsers"

affects:
  - "15-02 (editor UI for traits display)"
  - "15-03 (attack roller rollable traits)"
  - "Any code consuming Monster objects (traits and speed now always present)"

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Trait/action separation: blocks in preamble with no TO_HIT_RE or HIT_LINE_RE match classify as Trait, not Action"
    - "Explicit Traits section wins: extract_named_section('Traits') checked first; preamble fallback if absent"
    - "Dice detection: DICE_IN_TRAIT_RE scans trait description text for 'N (XdY) type damage' patterns"
    - "Recharge detection: RECHARGE_RE finds '(Recharge X-Y)' or '(Recharge X)' in trait names"
    - "after_text: text after HIT_LINE_RE.end() in joined action text captured on every attack action"

key-files:
  created: []
  modified:
    - "src/domain/models.py — DetectedDie and Trait dataclasses added; Monster.traits and Monster.speed added; Action.after_text added"
    - "src/parser/formats/_shared_patterns.py — SPEED_RE, DICE_IN_TRAIT_RE, RECHARGE_RE patterns; detect_dice_in_text(), detect_recharge(), extract_speed() helpers; imports Trait/DetectedDie from models"
    - "src/parser/formats/fivetools.py — _extract_traits(), _extract_speed(); Action.after_text; traits/speed in Monster constructor"
    - "src/parser/formats/homebrewery.py — _extract_traits(), _extract_speed(); Action.after_text; traits/speed in Monster constructor"
    - "src/parser/formats/plain.py — _extract_traits(), _extract_speed(); Action.after_text; traits/speed in Monster constructor"

key-decisions:
  - "Trait classification: blocks with no TO_HIT_RE AND no HIT_LINE_RE match are traits — simple and reliable for D&D 5e statblocks"
  - "Preamble fallback for traits: when no explicit Traits section exists, preamble text (before first section header) is the trait source"
  - "after_text for compact HB format: compact MWA actions always get after_text='' — no post-damage text in compact syntax"
  - "RECHARGE_RE uses \\u2013 (en-dash) alongside regular hyphen to handle copy-pasted unicode em/en dashes from PDFs"
  - "detect_recharge() single-value: (Recharge 6) returns (6, 6) — symmetric tuple ensures consumers only need min/max comparison"

patterns-established:
  - "Trait extraction pattern: try explicit section, fall back to preamble, filter by absence of attack indicators"
  - "Shared helper import pattern: parsers import detect_dice_in_text/detect_recharge/extract_speed from _shared_patterns via alias"

requirements-completed: [PARSE-01, PARSE-03, PARSE-05, PARSE-07, PARSE-09]

# Metrics
duration: 5min
completed: 2026-02-27
---

# Phase 15 Plan 01: Domain Model Extensions and Parser Trait Extraction Summary

**Trait dataclass with dice/recharge detection, Monster.speed/traits, Action.after_text, and trait separation logic added to all three statblock format parsers**

## Performance

- **Duration:** ~5 min
- **Started:** 2026-02-27T23:28:07Z
- **Completed:** 2026-02-27T23:33:11Z
- **Tasks:** 2
- **Files modified:** 5

## Accomplishments
- DetectedDie and Trait dataclasses added to domain models with full backward-compatible defaults
- Monster extended with traits (list[Trait]) and speed (str) fields; Action extended with after_text (str)
- Shared regex patterns and helper functions added to _shared_patterns.py: SPEED_RE, DICE_IN_TRAIT_RE, RECHARGE_RE, detect_dice_in_text(), detect_recharge(), extract_speed()
- All three format parsers (fivetools, homebrewery, plain) updated with _extract_traits(), _extract_speed(), and after_text population
- Zero test regressions: 510 tests pass

## Task Commits

Each task was committed atomically:

1. **Task 1: Add Trait, DetectedDie dataclasses and extend Monster/Action models** - `fa3ea52` (feat)
2. **Task 2: Add trait/speed/after-text extraction to all three format parsers** - `87438aa` (feat)

## Files Created/Modified
- `src/domain/models.py` - Added DetectedDie dataclass, Trait dataclass, Monster.traits, Monster.speed, Action.after_text
- `src/parser/formats/_shared_patterns.py` - Added SPEED_RE, DICE_IN_TRAIT_RE, RECHARGE_RE, detect_dice_in_text(), detect_recharge(), extract_speed(); imports Trait/DetectedDie
- `src/parser/formats/fivetools.py` - Added _extract_traits(), _extract_speed(); Action.after_text; wired traits/speed into Monster constructor
- `src/parser/formats/homebrewery.py` - Same additions as fivetools.py
- `src/parser/formats/plain.py` - Same additions as fivetools.py

## Decisions Made
- Trait classification uses absence of attack indicators (TO_HIT_RE and HIT_LINE_RE) — clean separation with no heuristics needed
- Preamble fallback for traits: when no explicit Traits section exists, `extract_all_sections().get('preamble', '')` provides the pre-Actions text containing monster traits
- RECHARGE_RE includes unicode en-dash (`\u2013`) to handle copy-pasted statblock text from PDFs
- detect_recharge() returns (6, 6) for single-value recharge like "(Recharge 6)" — consistent tuple interface for consumers
- Compact Homebrewery (MWA) actions always get after_text="" since no post-damage text exists in that compact syntax

## Deviations from Plan

None - plan executed exactly as written.

## Issues Encountered
None.

## User Setup Required
None - no external service configuration required.

## Next Phase Readiness
- Domain model layer complete: `monster.traits`, `monster.speed`, `action.after_text` available on all imported monsters
- Plan 02 can build the Traits UI section using `monster.traits` list
- Plan 03 can wire rollable trait buttons using `Trait.rollable_dice` and `Trait.recharge_range`
- `Trait.description` contains the full text for display and roll output
- Existing monsters in library have traits=[] and speed="" via defaults — no migration needed

---
*Phase: 15-editor-parser-overhaul*
*Completed: 2026-02-27*
