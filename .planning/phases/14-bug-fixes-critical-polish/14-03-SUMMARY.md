---
phase: 14-bug-fixes-critical-polish
plan: 03
subsystem: parser
tags: [parser, domain-model, regex, section-boundary, legendary-actions, lair-actions]

# Dependency graph
requires:
  - phase: 14-bug-fixes-critical-polish
    provides: Phase 14 context and bug research (14-RESEARCH.md confirms BUG-06 root cause)
provides:
  - Monster model with legendary_actions and lair_actions list fields
  - Shared section boundary detection regex (SECTION_BOUNDARY_RE) in _shared_patterns.py
  - extract_named_section() shared helper used by all three format parsers
  - extract_all_sections() helper for downstream use
  - Section-aware action extraction in plain.py, homebrewery.py, fivetools.py
affects: [phase-15, parser, domain-model, feature-detection]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Section boundary detection: extract_named_section() splits statblock text by recognized headers before action parsing — prevents cross-section text bleed"
    - "Shared parser helpers: format-agnostic logic lives in _shared_patterns.py and is imported by all three format parsers"
    - "Graceful fallback: when no section headers are found, parsers fall back to full-text parsing (backward compatible)"

key-files:
  created: []
  modified:
    - src/domain/models.py
    - src/parser/formats/_shared_patterns.py
    - src/parser/formats/plain.py
    - src/parser/formats/homebrewery.py
    - src/parser/formats/fivetools.py

key-decisions:
  - "Model changes minimal: only legendary_actions and lair_actions added — Phase 15 adds traits separation on top"
  - "Section boundary regex covers both #-style headers and bold-text format (***Actions*** / **Actions**)"
  - "Fallback behavior preserved: statblocks without explicit section headers still parse correctly via full-text fallback"
  - "SECTION_BOUNDARY_RE includes Lair Actions even though it was not in original ACTION_SECTION_RE — covers the actual bug trigger"

patterns-established:
  - "Pattern: extract_named_section(text, section_name) — always use this before _split_action_blocks() when section isolation is needed"
  - "Pattern: _extract_section_actions(text, section_name) — standard helper pattern for legendary/lair action extraction in all parsers"

requirements-completed:
  - BUG-06

# Metrics
duration: 3min
completed: 2026-02-26
---

# Phase 14 Plan 03: Parser Section Boundary Detection Summary

**Section-aware statblock parsing with Monster.legendary_actions and Monster.lair_actions fields — Lich's Paralyzing Touch now shows Constitution save text instead of lair action text**

## Performance

- **Duration:** 3 min
- **Started:** 2026-02-26T22:37:31Z
- **Completed:** 2026-02-26T22:40:28Z
- **Tasks:** 2
- **Files modified:** 5

## Accomplishments
- Added legendary_actions and lair_actions fields to Monster dataclass (backward compatible, default empty list)
- Added SECTION_BOUNDARY_RE compiled regex to _shared_patterns.py matching all recognized section headers in both #-style and bold-text formats
- Added extract_named_section() and extract_all_sections() shared helpers to _shared_patterns.py
- Updated plain.py, homebrewery.py, and fivetools.py with section-aware _extract_actions() and _extract_section_actions()
- BUG-06 root cause eliminated: text from Legendary Actions and Lair Actions no longer bleeds into regular Actions section

## Task Commits

Each task was committed atomically:

1. **Task 1: Add legendary_actions and lair_actions fields to Monster model** - `3e4e7cf` (feat)
2. **Task 2: Add section boundary detection to all three format parsers** - `b47fefa` (fix)

## Files Created/Modified
- `src/domain/models.py` - Added legendary_actions: list[Action] and lair_actions: list[Action] fields to Monster dataclass
- `src/parser/formats/_shared_patterns.py` - Added SECTION_BOUNDARY_RE, extract_named_section(), extract_all_sections()
- `src/parser/formats/plain.py` - Section-aware _extract_actions(), new _extract_section_actions(), populate legendary_actions/lair_actions in Monster constructor
- `src/parser/formats/homebrewery.py` - Same section-aware pattern as plain.py
- `src/parser/formats/fivetools.py` - Same section-aware pattern, replaced dead ACTION_SECTION_RE usage with extract_named_section()

## Decisions Made
- Model changes kept minimal per user direction: only legendary_actions and lair_actions — Phase 15 adds traits separation
- SECTION_BOUNDARY_RE covers both '#'-style headers and bold-text format (***Section*** / **Section**) to handle all real-world statblock formats
- Fallback behavior preserved: when no 'Actions' section header exists, parsers fall back to full-text parsing so legacy statblocks without section headers continue to work identically
- Added 'Lair Actions' to SECTION_BOUNDARY_RE (was missing from the original ACTION_SECTION_RE) — this is the direct fix for the Lich bug

## Deviations from Plan

None - plan executed exactly as written.

## Issues Encountered

None. The fix was straightforward once the shared helper was in place. All 510 existing tests passed without modification, and the Lich scenario was manually verified to confirm Paralyzing Touch raw_text contains Constitution saving throw text and not Energy Drain lair action text.

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness
- Monster.legendary_actions and Monster.lair_actions are populated for all three parser formats — Phase 15 can access these for traits/legendary action display
- extract_named_section() helper is available for any future parser extension needing section isolation
- All 510 tests pass; no regressions

## Self-Check: PASSED

All created files exist, all commits verified:
- FOUND: src/domain/models.py
- FOUND: src/parser/formats/_shared_patterns.py
- FOUND: src/parser/formats/plain.py
- FOUND: src/parser/formats/homebrewery.py
- FOUND: src/parser/formats/fivetools.py
- FOUND: .planning/phases/14-bug-fixes-critical-polish/14-03-SUMMARY.md
- FOUND: commit 3e4e7cf (feat: Monster model fields)
- FOUND: commit b47fefa (fix: section boundary detection)
- 510 tests pass

---
*Phase: 14-bug-fixes-critical-polish*
*Completed: 2026-02-26*
