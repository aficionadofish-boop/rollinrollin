# Project State

## Project Reference

See: .planning/PROJECT.md (updated 2026-02-25)

**Core value:** DMs can manage the full combat loop — prep monsters, roll attacks and saves, and track combat state — in seconds, with D&D 5e rule fidelity and persistent data.
**Current focus:** Phase 14 next — Bug Fixes & Critical Polish (16 bugs + 5 UX fixes from v2.0 manual testing round)

## Current Position

Phase: 18 (Storyteller System Dice Roller in a New Tab)
Plan: 3 of 3 in current phase — Complete
Status: Complete
Last activity: 2026-04-08 — Phase 18 Plan 03 complete (StorytellerTab wired into MainWindow at position 3, settings persistence, human-verified end-to-end)

Progress: [████████░░░░░░░░░░░░] Phase 18 complete (3/3 plans)

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
| 13 (v2.0) | 5/5 | Complete |
| Phase 14 P06 | 5 | 2 tasks | 1 files |

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
- [Phase 13-01]: ThemeService._PRESETS maps theme_name strings to full stylesheet strings; preset selection is O(1) dict lookup
- [Phase 13-01]: Dark theme remains default (AppSettings.theme_name = 'dark'); dark-background optimized per-widget colors already in codebase
- [Phase 13-01]: ThemeService.apply() lazy-imports QApplication to keep ThemeService Qt-free except at apply() call time
- [Phase 13-01]: main.py applies ThemeService.build_stylesheet(AppSettings()) at startup as flash-prevention before settings load
- [Phase 13-01]: MainWindow stores self._theme_service instance and exposes get_theme_service() for child widget accent color access
- [Phase 13-01]: Custom color template uses double-brace escaping ({{...}}) so .format() works without conflicting with CSS braces
- [Phase 13-02]: Physical damage types (slashing, piercing, bludgeoning) share neutral gray tones — understated to let magical types pop
- [Phase 13-02]: Full damage segment (number + type label) is colored as a unit; separator "+" between parts stays uncolored
- [Phase 13-02]: Crit rows use gold-tinted div rgba(212,175,55,0.25); miss rows use red-tinted rgba(180,0,0,0.18) via _wrap_crit_line()/_wrap_miss_line()
- [Phase 13-02]: append_html() uses QTextCursor.MoveOperation.End + insertHtml() — avoids plain-text/HTML mode-mixing pitfall
- [Phase 13-02]: All original plain-text format methods kept intact; HTML methods are additive for clipboard/future export compatibility
- [Phase 13-04]: Theme preset dropdown clears custom colors on switch (clean-slate) — prevents stale per-channel overrides from prior preset bleeding into new one
- [Phase 13-04]: Color picker buttons styled as swatches (background-color + contrast label) — simpler than icon squares, immediately obvious to DM
- [Phase 13-04]: Sandbox font applied on save (not live) — MacroEditor is in a different tab; live cross-tab font preview adds complexity for minimal benefit
- [Phase 13-04]: blockSignals(True) on theme combo during apply_settings() prevents _on_theme_changed() from clearing saved custom colors on load
- [Phase 13-05]: TemplateCard dispatch condition is lr.template_name AND lr.template_fields — template with name but no fields falls back to ResultCard (card would be empty except header)
- [Phase 13-05]: Accent color stored as _accent_color on ResultPanel; updated via set_accent_color() called on theme change via app.py _apply_settings
- [Phase 13-05]: _resolve_field_values uses left-to-right token matching by index — relies on preprocessor and inline roll resolution both processing left-to-right
- [Phase 14-01]: source_files_changed emitted only when at least one monster actually imported (not skip-all) — avoids spurious persistence writes
- [Phase 14-01]: Missing persisted monster files skipped silently on restart but kept in list — may be on removable drive and return later
- [Phase 14-01]: selectedRows() fixes single-result library selection — selected.indexes() returns per-cell delta empty for unchanged rows
- [Phase 14-01]: _RotatedButton uses QPainter.translate(width,0)+rotate(90) pattern for vertical text in 24px collapsed sidebar strip
- [Phase 14-02]: BUG-03 CR cascade uses _sync_save_toggles(recompute_values=True) + _cascade_skills_on_prof_change() to push new prof bonus into both saves and skills
- [Phase 14-02]: BUG-05 skill cascade determines current tier via old_mod comparison, recomputes with new_mod, leaves Custom skills unchanged
- [Phase 14-02]: BUG-04 skill coloring injected into preview _skills_label from _apply_highlights() — same pattern as save highlighting, no monster_detail.py changes needed
- [Phase 14-02]: BUG-07 focus display uses view-only display copy — _build_focus_annotated_display_copy() appends annotation to spellcasting action raw_text without mutating _working_copy
- [Phase 14-03]: Monster.legendary_actions and Monster.lair_actions added as separate list fields — Phase 15 traits separation builds on top
- [Phase 14-03]: SECTION_BOUNDARY_RE covers both #-style and bold-text (***Section***) section headers — handles all real-world statblock formats
- [Phase 14-03]: extract_named_section() fallback: when no section header found, returns "" so callers fall back to full-text parsing (backward compat)
- [Phase 14-03]: Lair Actions added to SECTION_BOUNDARY_RE (was absent from original ACTION_SECTION_RE) — this was the direct trigger for the Lich bug
- [Phase 14-04]: BUG-08 regular miss gets no background tint — only nat-1 misses call _wrap_miss_line(); removed _wrap_miss_line() from regular miss else-branch in _format_compare_line_html
- [Phase 14-04]: BUG-09+BUG-10 attack output wrappers changed from block div to inline span — div caused full-width gold fill and implicit paragraph margins (extra blank lines) in QTextEdit HTML renderer
- [Phase 14-05]: BUG-11 QMenu.exec() returns None for checkable action toggles in PySide6 — fix uses action.triggered.connect(lambda checked, key=k: _toggle_stat(k, checked)) per action
- [Phase 14-05]: BUG-15 dual root cause: (1) reset on every encounter_changed not just type-set change; (2) _lr_counters never seeded so _on_lr_used could never decrement from max
- [Phase 14-05]: LR counter seeding: seed _lr_counters[base_name] = lr_uses on first detection; always use persisted value on subsequent rolls
- [Phase 14-05]: Encounter type-change detection uses set comprehension {monster.name for monster, _ in members} vs _prev_encounter_names in app.py
- [Phase 14-05]: BUG-16 (0 HP) verified correct without code changes: service floors at 0, HpBar shows grey at 0, is_defeated is a computed property
- [Phase 14-06]: GroupCard damage distribution iterates members in display order; absorbed = min(remaining, current_hp+temp_hp) per non-defeated member; healing applies to first member (simple approach per spec)
- [Phase 14-06]: FlowLayout._MAX_ROWS=2 enforced at layout geometry time; items on row 3+ hidden via w.hide() — no +N badge widget required
- [Phase 14-06]: Card drag fully removed from CombatantCard — QDrag/QMimeData removed; left-button moves propagate to CombatantListArea rubber-band
- [Phase 14-06]: collapse_requested Signal on CombatantCard (double-click) connected in GroupCard._build_members_view; single-click via CompactSubRow.clicked still expands
- [Phase 15-01]: Trait classification uses absence of attack indicators (TO_HIT_RE and HIT_LINE_RE) — clean separation with no heuristics needed for D&D 5e statblocks
- [Phase 15-01]: Preamble fallback for traits: when no explicit Traits section exists, extract_all_sections().get('preamble', '') provides the pre-Actions text containing monster traits
- [Phase 15-01]: RECHARGE_RE includes unicode en-dash (\u2013) to handle copy-pasted statblock text from PDFs
- [Phase 15-01]: detect_recharge() returns (6, 6) for single-value recharge like "(Recharge 6)" — consistent tuple interface for consumers
- [Phase 15-01]: Monster.traits and Monster.speed use field defaults (list/str) so all existing Monster construction and MonsterModification.from_dict() backward compat is preserved
- [Phase 15-03]: After-text stored as _last_after_text on AttackRollerTab; avoids adding after_text to RollRequest domain model
- [Phase 15-03]: RAW mode always shows after-text; COMPARE mode shows only when at least one hit occurred
- [Phase 15-03]: _render_double_bracket is module-level function in monster_detail.py; replaces [[NdS]] with '{avg} [[NdS]]' display-only
- [Phase 15-03]: Speed row and traits section use QWidget wrapper setVisible(True/False) rather than layout manipulation
- [Phase 15]: Core Stats CR/HP/Speed compact horizontal row uses fixed-width combo/spinbox/lineedit with inline labels — keeps row narrow without a sub-section
- [Phase 15]: Traits undo: push snapshot BEFORE opening edit modal, pop on cancel — prevents phantom undo entries from cancelled edits
- [Phase 15]: _trait_items synced to _working_copy.traits in _push_undo() via getattr fallback — safe during __init__ before _trait_items is set
- [Phase 15]: TraitEditDialog modifies Trait object in-place (same reference as in _trait_items) — no return value needed
- [Phase 16-01]: BuffItem.targets: str replaced by affects_attacks/affects_saves/affects_ability_checks/affects_damage booleans; defaults are True/True/False/False (Bless-style)
- [Phase 16-01]: _BUFF_TARGET_MIGRATION module-level dict maps old targets string to 4 boolean dicts; "all" is fallback for unknown values
- [Phase 16-01]: from_dict() migration: pop "targets" when affects_attacks absent (old format); pop "targets" silently when affects_attacks present (already migrated)
- [Phase 16-01]: _BUFF_CHECKBOX_ATTRS tuple list [(label, attr)] drives both QCheckBox creation and stateChanged signal wiring in _rebuild_buff_rows()
- [Phase 16-02]: Buff dice injection: filter monster.buffs by affects_attacks/affects_saves boolean, map to BonusDiceEntry(formula=buff.bonus_value, label=buff.name)
- [Phase 16-02]: SaveParticipant.bonus_dice field carries per-participant buff dice; SaveRollService merges participant.bonus_dice + request.bonus_dice so global UI entries still apply to all
- [Phase 16-02]: _format_bonus_dice_part() uses 'd' in dice_notation to distinguish dice vs flat; first attack/row shows full '+ Bless 1d4(3)', subsequent show '+ 1d4(2)'
- [Phase 16-02]: Damage type summary only shown in COMPARE when len(type_totals) > 1; buff bonus_dice_results excluded from type aggregation (buff detail is per-roll only)
- [Phase 16-04]: HpBar 5-band label: font size set to 7pt (down from 8pt) to fit 'Badly Injured' (13 chars) in 24px bar; label='' for defeated state skips all text-drawing; full grey fill for defeated vs dark background
- [Phase 16-03]: Auto-name guard uses string comparison (current_text == _current_auto_name or empty) — no separate is_custom flag needed
- [Phase 16-03]: get_save_name() returns pure auto-name or '{custom} — {auto_base}' format at save time
- [Phase 16-03]: LoadEncounterDialog inline edit extracts name before first em-dash separator (creature count and date are display-only metadata)
- [Phase 16-03]: Renames processed before deletions in _on_sidebar_load so original indices remain valid when both occur in same dialog session
- [Phase 16-03]: resizeEvent tracks expanded width (>= 200) for persistence; _expand() restores via resize() not setMaximumWidth()
- [Phase 17-01]: showEvent() deferred setSizes() with _splitter_initialized guard — runs once after Qt layout pass, not during __init__ or _load_persisted_data()
- [Phase 17-01]: setObjectName("main_splitter") on QSplitter enables scoped CSS selector QSplitter#main_splitter::handle:horizontal, isolating main sidebar handle from all other splitters
- [Phase 17-01]: sidebar minimumWidth reduced from 200 to 150 in _expand() and __init__ — gives splitter 50px more drag range at 1100px window width; resizeEvent threshold and set_expanded_width() guard updated to match
- [Phase 17-01]: setHandleWidth(0/9) toggled in _on_sidebar_collapse_toggled: hides grab zone on collapse (no phantom area), restores 9px on expand to match CSS width
- [Phase 17-01]: Gradient CSS qlineargradient for splitter handle: thin 1-2px visible center line within 9px grab zone; hover state brightens color — all three themes covered
- [Phase 18]: Aberrant 1s never cancel successes — botch is purely (total==0 AND any 1)
- [Phase 18]: WoD 8/9-again is a loop (max 50 iterations), not a single extra pass — chain terminates when no qualifying dice in latest batch
- [Phase 18]: storyteller_last_config uses field(default_factory=dict) to avoid mutable default in AppSettings dataclass
- [Phase 18-02]: StorytellerTab._refresh_preset_combo() guarded with hasattr(_preset_combo) — _load_presets() runs before widget build in __init__; guard prevents AttributeError on first launch
- [Phase 18-02]: HTML dice rendering uses QTextCursor.insertHtml() exclusively — QTextEdit.append() causes implicit paragraph gaps in Qt HTML renderer
- [Phase 18-03]: _settings_tab_index uses indexOf() after all addTab() calls — auto-resolves to 6 after Storyteller insertion with no manual adjustment
- [Phase 18-03]: _on_tab_changed() sidebar logic uses widget identity (not index) — Storyteller tab falls into else branch (sidebar stays visible) with zero code changes
- [Phase 18-03]: hasattr guard on _storyteller_tab in _apply_settings() — defensive against future init reordering; object exists when called but guard is safe
- [Phase 18-03]: Session log separator uses <br><hr style="border:0; border-top:1px solid #333"> — <p> wrapper caused Qt HTML renderer paragraph gaps between roll entries

### Roadmap Evolution

- Phase 14 detailed: Bug Fixes & Critical Polish — 16 bugs (BUG-01 to BUG-16) covering persistence, parser, coloring, combat tracker groups, LR tracking + 5 UX fixes (UX-01 to UX-05) for sidebar, init box, rubber-band, conditions
- Phase 15 detailed: Editor & Parser Overhaul — 11 items (PARSE-01 to PARSE-11): traits/actions separation, traits tab UI, after-attack-text editing, action field labels, auto-dice detection, rollable trait buttons, recharge support, [[XdY]] notation, speed display, editor compaction, equipment reposition
- Phase 16 detailed: Buff System & Output Improvements — 10 items: buff per-roll-type toggles (BUFF-01 to BUFF-03), output header + damage type summary (OUT-01/02), encounter naming/editing/sidebar resize (ENC-01 to ENC-03), health bar descriptive text + color bands (COMBAT-UX-01/02)
- Phase 17 added: Sidebar handle fix — research and fix the sidebar handle of the encounter list tracker
- Phase 18 added: storyteller system dice roller in a new tab

### Pending Todos

None.

### Blockers/Concerns

- Phase 5 (Save Roller, mapped as Phase 12): Validate that Monster.actions contains parsed trait entries (not only attack actions) before implementing feature detection. If traits are absent, feature detection approach must change or parser must be extended first.
- Phase 6 (Theming, mapped as Phase 13): Audit volume of existing widget.setStyleSheet() calls in src/ui/ before building theming. High volume (>20) expands Phase 13 scope.

## Session Continuity

Last session: 2026-04-08
Stopped at: Completed 18-03-PLAN.md
Resume file: (Phase 18 complete — no next plan)
