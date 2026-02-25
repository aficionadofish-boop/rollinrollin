# Project State

## Project Reference

See: .planning/PROJECT.md (updated 2026-02-25)

**Core value:** DMs can manage the full combat loop — prep monsters, roll attacks and saves, and track combat state — in seconds, with D&D 5e rule fidelity and persistent data.
**Current focus:** Phase 8 — Domain Expansion and Persistence Foundation

## Current Position

Phase: 8 of 13 (Domain Expansion and Persistence Foundation)
Plan: 2 of ? in current phase
Status: In progress
Last activity: 2026-02-25 — Plan 08-02 complete: Monster Math Engine, MathValidator, SpellcastingDetector

Progress: [███████░░░░░░] 54% (7/13 phases complete — v1.0 phases done, Phase 8 in progress)

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

### Pending Todos

None.

### Blockers/Concerns

- Phase 5 (Save Roller, mapped as Phase 12): Validate that Monster.actions contains parsed trait entries (not only attack actions) before implementing feature detection. If traits are absent, feature detection approach must change or parser must be extended first.
- Phase 6 (Theming, mapped as Phase 13): Audit volume of existing widget.setStyleSheet() calls in src/ui/ before building theming. High volume (>20) expands Phase 13 scope.

## Session Continuity

Last session: 2026-02-25
Stopped at: Completed 08-02-PLAN.md (Monster Math Engine, MathValidator, SpellcastingDetector)
Resume file: .planning/phases/08-domain-expansion-and-persistence-foundation/08-02-SUMMARY.md
