# Project State

## Project Reference

See: .planning/PROJECT.md (updated 2026-02-23)

**Core value:** DMs can roll attacks and saving throws for groups of monsters in seconds, with full D&D 5e rule fidelity and clear hit/miss/damage breakdowns.
**Current focus:** Phase 4 — Lists, Encounters, and Save Roller (in progress)

## Current Position

Phase: 4 of 7 (Lists, Encounters, and Save Roller)
Plan: 2 of 5 in current phase (Plan 04-02 complete)
Status: Plan 04-02 complete — EncounterService + SaveRollService TDD, 307 tests pass
Last activity: 2026-02-24 — Completed 04-02: EncounterService Markdown save/load, SaveRollService d20 saves, 307 tests

Progress: [████████░░] 78%

## Performance Metrics

**Velocity:**
- Total plans completed: 7
- Average duration: 5 min
- Total execution time: 0.6 hours

**By Phase:**

| Phase | Plans | Total | Avg/Plan |
|-------|-------|-------|----------|
| 01-dice-engine-and-domain-foundation | 2/2 | 7 min | 4 min |
| 02-monster-import-and-library | 4/6 | 32 min | 5 min |
| 03-attack-roller | 3/3 | 14 min | 5 min |

**Recent Trend:**
- Last 5 plans: 02-03 (5 min), 02-04-tasks1-2 (2 min), 02-04-task3 (15 min), 03-01 (10 min)
- Trend: stable

*Updated after each plan completion*
| Phase 02-monster-import-and-library P04 | 3 | 3 tasks | 8 files |
| Phase 03-attack-roller P01 | 1 | 1 TDD task | 4 files |
| Phase 03-attack-roller P02 | 1 | 2 tasks | 2 files |
| Phase 03-attack-roller P03 | 3 | 2 tasks | 2 files |
| Phase 04-lists-encounters-and-save-roller P01 | 4 | 2 tasks | 5 files |
| Phase 04-lists-encounters-and-save-roller P02 | 3 | 2 TDD tasks | 3 files |

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
- [Phase 03-01]: RollRequest uses to_hit_bonus: int (not formula string) — d20 rolled separately to avoid ParseError on negative bonuses (03-01)
- [Phase 03-01]: _double_dice() regex doubles only leading NdM prefix; constant bonuses unchanged per 5e crit rules (03-01)
- [Phase 03-01]: Nat-1/nat-20 extracted from DieFace.kept=True (not d20_result.total) for correctness with advantage/disadvantage (03-01)
- [Phase 03-01]: Bonus dice formula: strip leading '+' before roll_expression(); sign detected from formula.startswith('-') (03-01)
- [Phase 03-01]: COMPARE mode damage gating: is_hit is True (explicit identity check, not truthy) before rolling damage (03-01)
- [Phase 03-02]: ToggleBar default falls back to options[0] if provided default not in options dict
- [Phase 03-02]: BonusDiceList.get_entries() lazy-imports BonusDiceEntry from src.roll.models to avoid Qt circular dependency
- [Phase 03-attack-roller]: RollOutputPanel is a QWidget container (not QTextEdit subclass) — owns QTextEdit internally for encapsulation and Copy button
- [Phase 03-attack-roller]: Target AC widget uses setVisible(False/True) in _on_mode_changed — hides in RAW mode per CONTEXT.md decision (not setEnabled)
- [Phase 03-attack-roller]: Result re-render: _last_result stores RollResult; mode switch calls _render_results() with no re-roll (03-03)
- [Phase 03-attack-roller]: MainWindow connects monster_selected AFTER both tabs constructed — avoids signal-before-init pitfall
- [Phase 03-attack-roller]: Roller(random.Random()) constructed once in MainWindow; unseeded; Phase 6 wires seed
- [Phase 04-01]: Encounter.members changed to list[tuple[Monster, int]] — same (monster, count) convention as MonsterList.entries
- [Phase 04-01]: get_by_name raises KeyError on miss — callers must call has_name() first; no Optional return
- [Phase 04-01]: SaveRequest.bonus_dice typed as list (untyped) — avoids importing BonusDiceEntry from roll.models into encounter layer
- [Phase 04-02]: (score-10)//2 for ability modifier fallback — floor division is correct for negatives; int(score/2) used only for damage (01-01 convention does NOT apply here)
- [Phase 04-02]: SaveRollService defines its own bonus dice handling inline — no import from src.roll; avoids coupling between attack-roll and save-roll layers
- [Phase 04-02]: _resolve_save_bonus and _expand_participants are module-level helpers, not class methods — independently testable pure functions

### Pending Todos

None.

### Blockers/Concerns

- Phase 5: The ?{query} prompt must not block the Qt main thread — confirm QDialog.exec() callback pattern before implementing MacroParser
- Phase 7: Antivirus false positive rate on the packaged .exe is unknown; budget time to test and fall back to pyside6-deploy (Nuitka) if needed

## Session Continuity

Last session: 2026-02-24
Stopped at: Completed 04-02-PLAN.md — EncounterService Markdown save/load, SaveRollService d20 saves, 307 tests passing
Resume file: None
