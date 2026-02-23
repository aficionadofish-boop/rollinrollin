# Project State

## Project Reference

See: .planning/PROJECT.md (updated 2026-02-23)

**Core value:** DMs can roll attacks and saving throws for groups of monsters in seconds, with full D&D 5e rule fidelity and clear hit/miss/damage breakdowns.
**Current focus:** Phase 2 — Monster Import and Library (in progress)

## Current Position

Phase: 2 of 7 (Monster Import and Library)
Plan: 3 of 6 in current phase
Status: Plan 02-03 complete — ready for 02-04 (library tab UI)
Last activity: 2026-02-23 — Completed 02-03 (MonsterLibrary service + Qt model/view layer, 232 tests passing)

Progress: [████░░░░░░] 33%

## Performance Metrics

**Velocity:**
- Total plans completed: 5
- Average duration: 4 min
- Total execution time: 0.3 hours

**By Phase:**

| Phase | Plans | Total | Avg/Plan |
|-------|-------|-------|----------|
| 01-dice-engine-and-domain-foundation | 2/2 | 7 min | 4 min |
| 02-monster-import-and-library | 3/6 | 13 min | 4 min |

**Recent Trend:**
- Last 5 plans: 01-01 (5 min), 01-02 (2 min), 02-01 (4 min), 02-02 (4 min), 02-03 (5 min)
- Trend: stable

*Updated after each plan completion*

## Accumulated Context

### Decisions

Decisions are logged in PROJECT.md Key Decisions table.
Recent decisions affecting current work:

- Stack: Python 3.12 + PySide6 6.10.2 + PyInstaller 6.19.0 (confirmed HIGH confidence by research)
- Architecture: Strict layered dependency — engine/models import nothing from this project; services orchestrate; views call services only
- Dice Engine: Recursive descent parser with explicit precedence; never use eval(); seeded RNG via single Random instance per session
- Parser: Tolerant — incomplete=True on missing fields, rawText on every unparseable action; never fail silently
- Division uses int(a/b) NOT a//b: truncation toward zero matches 5e convention; -7/2 = -3 not -4 (01-01)
- Seed threading: Roller holds only random.Random; seed integer passed to roll_expression() for DiceResult.seed audit trail only (01-01)
- constant_bonus field tracks bare integer literals separately from die faces for clean breakdown (01-01)
- kl = keep-lowest N: 4d6kl3 keeps 3 lowest dice, drops highest (01-01)
- Domain layer imports only stdlib (dataclasses, typing, enum) — no Qt, pathlib, or I/O at model level (01-02)
- Monster.incomplete and Monster.tags on domain model directly to avoid wrapper type (01-02)
- MonsterList uses list[tuple[Monster, int]] for (monster, count) pairs; Encounter uses list[Monster] only (01-02)
- Test imports use src.domain.* and src.workspace.* to match src.engine.* project convention (01-02)
- WorkspaceManager.initialize() returns only newly-created folder names for caller logging (idempotent by design) (01-02)
- Action.to_hit_bonus: Optional[int] — non-attack actions have no attack roll; None is semantically correct (02-01)
- is_parsed=True only when to_hit_bonus is not None AND damage_parts non-empty — partial parse still stored as raw_text (02-01)
- ParseResult.monsters uses untyped list to avoid circular import between parser.models and domain.models (02-01)
- Lore collected as plain paragraphs after statblock block, before next >## heading (02-01)
- Segmentation anchors on >## heading scan (not blockquote boundary) for reliable multi-monster split (02-01)
- Shared _shared_patterns.py module: regex constants centralized for all format parsers; avoids duplication (02-02)
- Homebrewery segmentation merges adjacent ___ sections by ## heading scan — one monster spans multiple ___ blocks (02-02)
- ImportResult placed in models.py (not statblock_parser.py) to keep data types together without pulling in parser logic (02-02)
- Format detection priority: fivetools > homebrewery > plain > unknown; > prefix is unambiguous differentiator (02-02)
- MonsterLibrary dual-storage: list[Monster] for ordered iteration + dict[str, int] for O(1) has_name; dict rebuilt on remove() (02-03)
- QSortFilterProxyModel.invalidate() used instead of deprecated invalidateFilter()/invalidateRowsFilter() in PySide6 6.10.2 (02-03)
- _cr_to_float returns -1.0 for unknown/empty/dash CR — sorts to top in ascending order for easy identification (02-03)
- filterAcceptsRow uses filterRegularExpression().pattern() as plain string for substring matching, not regex (02-03)

### Pending Todos

None.

### Blockers/Concerns

- Phase 5: The ?{query} prompt must not block the Qt main thread — confirm QDialog.exec() callback pattern before implementing MacroParser
- Phase 7: Antivirus false positive rate on the packaged .exe is unknown; budget time to test and fall back to pyside6-deploy (Nuitka) if needed

## Session Continuity

Last session: 2026-02-23
Stopped at: Completed 02-03-PLAN.md — MonsterLibrary service + Qt model/view layer, 232 tests passing
Resume file: None
