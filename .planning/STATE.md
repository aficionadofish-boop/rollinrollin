# Project State

## Project Reference

See: .planning/PROJECT.md (updated 2026-02-25)

**Core value:** DMs can manage the full combat loop — prep monsters, roll attacks and saves, and track combat state — in seconds, with D&D 5e rule fidelity and persistent data.
**Current focus:** Phase 12 in progress — Save Roller Upgrades Plan 03 complete (SavesTab UI wiring with feature detection, LR interaction, sidebar integration, CT override setting)

## Current Position

Phase: 12 of 13 (Save Roller Upgrades)
Plan: 3 of 3 in current phase (Plan 03 complete — all SAVE requirements implemented)
Status: In Progress
Last activity: 2026-02-26 — Phase 12 Plan 03 complete (SavesTab feature detection toggles, detection rules panel, per-row result widgets with LR tracking, sidebar wiring, CT override setting in Settings)

Progress: [████████████████] Phase 12 Plan 03 complete (3/3 plans)

## Performance Metrics

**Velocity:**
- Total plans completed: 18 (16 v1.0 + 2 v2.0 Phase 8 + 5 v2.0 Phase 9 + 2 v2.0 Phase 10... wait, 16 + 3 + 5 + 2 = 26 total)

**By Phase:**

| Phase | Plans | Status |
|-------|-------|--------|
| 1-7 (v1.0) | 16/16 | Complete |
| 8 (v2.0) | 3/3 | Complete |
| 9 (v2.0) | 5/5 | Complete |
| 10 (v2.0) | 2/2 | Complete |
| 11 (v2.0) | 4/4 | Complete |
| 12 (v2.0) | 3/3 | Complete |
| 13 (v2.0) | 0/? | Not started |

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
- [Phase 10-01]: encounters PersistenceService category changed from list to dict schema {active, saved} — list was never populated by UI; dict enables active+saved CRUD
- [Phase 10-01]: count('encounters') returns len(saved) + (1 if active else 0) — reflects both active and saved encounters
- [Phase 10-01]: sidebar_width: int = 300 added to AppSettings for cross-session width persistence
- [Phase 10-01]: EncounterSidebarDock collapse uses width constraints (not QDockWidget.hide()) so thin strip remains visible
- [Phase 10-01]: sidebar always starts expanded — collapse state not persisted (DM expects to see encounter on launch)
- [Phase 10-02]: SavesTab keeps file name encounters_tab.py to avoid breaking any future imports — only class name changed
- [Phase 10-02]: LoadEncounterDialog tracks row_to_original mapping so deletions do not shift the index used for load
- [Phase 10-02]: set_active_creature adds monster to creature list if not already present (sidebar single-click preload)
- [Phase 10-02]: _load_persisted_data called AFTER sidebar is constructed so set_encounter() works during startup
- [Phase 10-02]: _persisted_encounters removed — sidebar is now the authoritative in-memory encounter state
- [Phase 10-UAT]: QPropertyAnimation removed — instant collapse/expand via setVisible + width constraints (user preference)
- [Phase 10-UAT]: Dark theme: no forced background colors, translucent selection overlay rgba(255,255,255,30), plain text button labels
- [Phase 10-UAT]: Collapsed strip width 60px (originally 20px) — text labels need more space than symbols
- [Phase 10-UAT]: Duplicate encounter save prevention in _on_sidebar_save — exact name+members match check
- [Phase 11-01]: CombatTrackerService holds _prev_snapshot as a dict (not a CombatState copy) for minimal memory overhead during undo
- [Phase 11-01]: Grouped initiative rolls once per group_id when grouping_enabled=True; each monster in the group gets the same initiative value
- [Phase 11-01]: ConditionEntry.color field preserved in serialization (set by UI layer, not service)
- [Phase 11-01]: Auto-regen via advance_turn() only when regeneration_hp > 0; pass_one_round() does not auto-regen
- [Phase 11-01]: Feature detection scans Monster.actions[*].raw_text with regex for Legendary Resistance count, Legendary Actions count, Regeneration HP
- [Phase 11-02]: HpBar uses direct QPainter in paintEvent — no Qt stylesheets for bar segments (avoids stylesheet z-order issues with overlapping fill rects)
- [Phase 11-02]: _ConditionChip subclasses QLabel with mousePressEvent override — installEventFilter avoided; each chip captures its own condition name in closure
- [Phase 11-02]: CombatTrackerTab._on_start_combat is a no-op without encounter members — actual start_combat(members) called by MainWindow in Plan 04 wiring
- [Phase 11-03]: GroupCard uses hidden _members_container QWidget (show/hide) rather than rebuilding the whole QFrame on expand/collapse — avoids layout thrashing
- [Phase 11-03]: CompactSubRow intercepts mousePressEvent on entire frame (not just expand button) — clicking anywhere on the row expands to full CombatantCard
- [Phase 11-03]: Stat visibility defaults to False for all toggleable stats — DM must opt in via Stats menu
- [Phase 11-03]: _CardContainer handles drag drops (not CombatantCards) so drop works regardless of card sub-widget hit
- [Phase 11-03]: _auto_regen defaults to False; advance_turn() gates regen on _auto_regen flag (changed from always-on when regeneration_hp > 0)
- [Phase 11-03]: GroupCard initiative spinbox emits initiative_changed for first group member only (shared group roll)
- [Phase 11-04]: card_clicked Signal on CombatantCard carries (combatant_id, Qt.KeyboardModifiers); CombatTrackerTab handles all selection logic centrally
- [Phase 11-04]: CombatantListArea subclasses QScrollArea to own QRubberBand state; emits box_selected(set[str]) after mouse release
- [Phase 11-04]: start_combat_requested Signal pattern — tab signals MainWindow which reads sidebar and calls start_combat(members) back; tab holds no sidebar reference
- [Phase 11-04]: Send to Saves resolves to SaveParticipant with CON save bonus by default; PCs without monster_name get save_bonus=0
- [Phase 11-04]: Combat state saved only when combatants list is non-empty (prevents overwriting good persisted state with empty dict)
- [Phase 11-04]: Sidebar setVisible(False) when Combat Tracker tab is active; setVisible(True) on any other tab switch
- [Phase 12-01]: Per-participant advantage: SaveParticipant.advantage (Optional) overrides SaveRequest.advantage when not None — backward compat preserved
- [Phase 12-01]: FeatureDetectionService is stateless — LR counters live in SavesTab._lr_counters dict keyed by monster_name (not participant name)
- [Phase 12-01]: LR count uses max() across all action raw_text entries to avoid double-counting duplicate action entries
- [Phase 12-01]: save_rules persistence category uses list default (not dict) — list of custom rule dicts
- [Phase 12-01]: ct_send_overrides_sidebar: bool = True — CT send replaces sidebar checked state by default
- [Phase 12-02]: Sidebar checkbox state NOT persisted to disk — all rows start checked on set_encounter() and app launch (avoids confusion when DM returns days later)
- [Phase 12-02]: One checkbox per monster type row (grouped creatures toggle as a group) — individual-creature toggling deferred
- [Phase 12-02]: get_checked_members() returns filtered (Monster, count) list; get_members() unchanged (still returns all)
- [Phase 12-03]: Detection Rules panel collapsed by default (QGroupBox setCheckable) — minimizes visual noise for standard sessions
- [Phase 12-03]: LR counters reset only on encounter change, not on each roll — critical for multi-roll LR tracking within a fight
- [Phase 12-03]: monster_name monkey-patched onto SaveParticipantResult at roll time — avoids domain model churn for UI-layer concern
- [Phase 12-03]: Tab switch to Saves auto-loads only if sidebar has checked members — avoids noisy empty-participant message

### Pending Todos

None.

### Blockers/Concerns

- Phase 5 (Save Roller, mapped as Phase 12): Validate that Monster.actions contains parsed trait entries (not only attack actions) before implementing feature detection. If traits are absent, feature detection approach must change or parser must be extended first.
- Phase 6 (Theming, mapped as Phase 13): Audit volume of existing widget.setStyleSheet() calls in src/ui/ before building theming. High volume (>20) expands Phase 13 scope.

## Session Continuity

Last session: 2026-02-26
Stopped at: Completed 12-03-PLAN.md (SavesTab UI wiring, feature detection, LR interaction, sidebar integration, CT override setting — Phase 12 complete)
Resume file: .planning/ROADMAP.md
