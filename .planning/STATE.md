# Project State

## Project Reference

See: .planning/PROJECT.md (updated 2026-02-23)

**Core value:** DMs can roll attacks and saving throws for groups of monsters in seconds, with full D&D 5e rule fidelity and clear hit/miss/damage breakdowns.
**Current focus:** Phase 2 — Monster Import and Library (in progress)

## Current Position

Phase: 2 of 7 (Monster Import and Library)
Plan: 5 of 6 in current phase (Plan 04 complete; Plans 05-06 remaining)
Status: Plan 02-04 complete — all 3 tasks done including bug fixes from human verification
Last activity: 2026-02-24 — Completed 02-04 Tasks 1-3: all UI bugs fixed (sorting, incomplete detection, lore section)

Progress: [██████░░░░] 50%

## Performance Metrics

**Velocity:**
- Total plans completed: 6
- Average duration: 5 min
- Total execution time: 0.5 hours

**By Phase:**

| Phase | Plans | Total | Avg/Plan |
|-------|-------|-------|----------|
| 01-dice-engine-and-domain-foundation | 2/2 | 7 min | 4 min |
| 02-monster-import-and-library | 4/6 | 32 min | 5 min |

**Recent Trend:**
- Last 5 plans: 02-01 (4 min), 02-02 (4 min), 02-03 (5 min), 02-04-tasks1-2 (2 min), 02-04-task3 (15 min)
- Trend: stable

*Updated after each plan completion*
| Phase 02-monster-import-and-library P04 | 3 | 3 tasks | 8 files |

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
- [Phase 02-04]: blockSignals guard on tags QLineEdit prevents spurious monster.tags mutation when show_monster() updates the field
- [Phase 02-04]: set_complete_only and set_incomplete_only are mutually exclusive flags in MonsterFilterProxyModel
- [Phase 02-04]: QPushButton toggle + QTextEdit setVisible for lore section — QGroupBox setChecked(False) only greys, does not hide (02-04)
- [Phase 02-04]: Qt.UserRole must return non-None for ALL columns when setSortRole(Qt.UserRole) is set — col0 returns name.lower() (02-04)
- [Phase 02-04]: Fivetools format detected by >## heading (structural marker) not **Armor Class** presence (02-04)
- [Phase 02-04]: Qt '&&' in text displays literal '&' — single '&' is treated as keyboard accelerator prefix (02-04)

### Pending Todos

None.

### Blockers/Concerns

- Phase 5: The ?{query} prompt must not block the Qt main thread — confirm QDialog.exec() callback pattern before implementing MacroParser
- Phase 7: Antivirus false positive rate on the packaged .exe is unknown; budget time to test and fall back to pyside6-deploy (Nuitka) if needed

## Session Continuity

Last session: 2026-02-24
Stopped at: Completed 02-04-PLAN.md — all tasks including Task 3 human verification and bug fixes
Resume file: None
