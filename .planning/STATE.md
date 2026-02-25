# Project State

## Project Reference

See: .planning/PROJECT.md (updated 2026-02-25)

**Core value:** DMs can manage the full combat loop — prep monsters, roll attacks and saves, and track combat state — in seconds, with D&D 5e rule fidelity and persistent data.
**Current focus:** Phase 9 — Monster Editor and Equipment Presets

## Current Position

Phase: 9 of 13 (Monster Editor and Equipment Presets)
Plan: 5 of 5 in current phase (Task 1 complete, awaiting human-verify checkpoint)
Status: Awaiting human verification (checkpoint:human-verify)
Last activity: 2026-02-26 — Plan 09-05 Task 1 complete: save workflows, library badge, cross-tab buff wiring implemented

Progress: [████████████░] 78% (Phase 8 complete, Phase 9 plan 05 task 1 of 2 done)

## Performance Metrics

**Velocity:**
- Total plans completed: 16 (all v1.0)
- Average duration: ~30-45 min per plan (estimated from v1.0 ship speed)
- Total execution time: v1.0 shipped same day as start (2026-02-24)

**By Phase:**

| Phase | Plans | Status |
|-------|-------|--------|
| 1-7 (v1.0) | 16/16 | Complete |
| 8-13 (v2.0) | 0/? | Not started |
| Phase 08 P03 | 2 | 2 tasks | 2 files |

## Accumulated Context

### Decisions

Decisions are logged in PROJECT.md Key Decisions table.
Recent decisions affecting current work:

- Persistence: JSON only — no SQLite; mirrors existing SettingsService pattern; zero new pip dependencies
- PersistenceService category defaults: modified_monsters={}, all others=[] (list vs dict by access pattern)
- Corrupt JSON files return empty defaults without overwriting (preserves user recovery chance)
- SpellcastingInfo is a standalone flat dataclass, not nested inside MonsterModification at model level
- Sidebar: QDockWidget at RightDockWidgetArea — not a tab-embedded widget; no direct tab references to sidebar
- Encounter persistence format: `{name: str, count: int}` only — never serialize Monster objects; resolve by name at access time
- Monster Math: pure Python engine (no Qt), guard all QSpinBox.valueChanged slots with _recalculating flag + blockSignals()
- damage_bonus on Action accessed via getattr with None default — forward-compat before formal domain model field addition
- SpellcastingInfo in spellcasting.py (runtime detection) is separate from any persistence domain model version
- SaveState uses (str, Enum) for JSON serialization without conversion overhead
- damage expected = ability_mod only (no prof) — D&D 5e rule: proficiency applies to attack rolls not damage
- Fallback mental stat: WIS > INT > CHA by score; WIS default when no mental stats present
- Combat state: CombatTrackerService is authoritative; widgets are display-only, never hold HP state
- Feature detection: search Monster.actions (not raw_text) to avoid lore-paragraph false positives
- QWebEngineView: explicitly rejected for template rendering — 130-150MB bundle bloat violates portable .exe constraint
- [Phase 08]: closeEvent guards unsaved settings before saving persistence data on close
- [Phase 08]: Lambda captures category and display_name by value in flush button wiring to avoid closure variable capture bug
- [Phase 08]: resolve_workspace_root() replaces hardcoded Path.home()/RollinRollin for portable exe support
- [Phase 09-01]: SKILL_TO_ABILITY covers 5 abilities (no CON — D&D 5e has no CON-based skill)
- [Phase 09-01]: MonsterModification.from_dict() shallow copies input dict and filters unknown keys for forward-compat
- [Phase 09-01]: Parser _extract_size() defaults to "Medium" when no valid size found in type/alignment line
- [Phase 09-02]: EquipmentService uses inline _PROF_BY_CR table (avoids coupling to MonsterMathEngine internals)
- [Phase 09-02]: scale_dice() is module-level function (not method) for standalone import by Plans 03-04
- [Phase 09-02]: compute_armor_ac str_requirement_met uses >= comparison; str_requirement=0 means always met
- [Phase 09-02]: Ranged non-thrown weapons always use DEX; thrown non-finesse use STR (D&D 5e rule)
- [Phase 09-03]: hp_formula stored in UI only (QLineEdit); Monster has no hp_formula field — Plan 05 persists via MonsterModification.hp_formula
- [Phase 09-03]: closeEvent Save button is stub (accepts+closes); Plan 05 replaces with real save logic
- [Phase 09-03]: _apply_save_value() Non-Prof removes ability from saves dict (clean Monster convention)
- [Phase 09-03]: reject() routes through close() so Escape triggers closeEvent unsaved-changes guard
- [Phase 09-05]: Monster.buffs lives on Monster dataclass (not editor-local) so buffs flow through library to AttackRollerTab without extra wiring
- [Phase 09-05]: Modification diff stores only changed fields — empty saves/skills/ability_scores if unchanged, keeps JSON minimal
- [Phase 09-05]: PersistenceService load+merge in _save_override: load current dict, update key, save back — avoids clobbering other saved modifications
- [Phase 09-05]: Badge collision priority: incomplete "!" > modified pencil > "" (incomplete takes precedence)
- [Phase 09-05]: closeEvent Save calls real _save_override() with event.ignore() so dialog controls its own close lifecycle

### Pending Todos

None.

### Blockers/Concerns

- Phase 5 (Save Roller, mapped as Phase 12): Validate that Monster.actions contains parsed trait entries (not only attack actions) before implementing feature detection. If traits are absent, feature detection approach must change or parser must be extended first.
- Phase 6 (Theming, mapped as Phase 13): Audit volume of existing widget.setStyleSheet() calls in src/ui/ before building theming. High volume (>20) expands Phase 13 scope.

## Session Continuity

Last session: 2026-02-26
Stopped at: 09-05-PLAN.md Task 1 complete — awaiting human verification (Task 2 checkpoint:human-verify)
Resume file: .planning/phases/09-monster-editor-and-equipment-presets/09-05-SUMMARY.md
