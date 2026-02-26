# Roadmap: RollinRollin

## Milestones

- [x] **v1.0 Bulk Dice Roller** - Phases 1-7 (shipped 2026-02-24)
- [x] **v2.0 Combat Manager** - Phases 8-13 (completed 2026-02-26)

## Phases

<details>
<summary>v1.0 Bulk Dice Roller (Phases 1-7) — SHIPPED 2026-02-24</summary>

- [x] **Phase 1: Dice Engine and Domain Foundation** - Pure-Python dice evaluator, seeded RNG, domain models, and workspace folder (completed 2026-02-23)
- [x] **Phase 2: Monster Import and Library** - Tolerant Markdown statblock parser, in-memory monster library with search and filtering, workspace file I/O (completed 2026-02-23)
- [x] **Phase 3: Attack Roller** - Full Attack Roller tab with RAW/COMPARE modes, all 5e toggles, roll breakdown output, and copy-to-clipboard (completed 2026-02-24)
- [x] **Phase 4: Lists, Encounters, and Save Roller** - Named monster lists and encounters with Markdown save/load, bulk per-participant Save Roller drawing from the active encounter (completed 2026-02-24)
- [x] **Phase 5: Roll20 Macro Sandbox** - Free-text macro input resolving Roll20 inline rolls and query dialogs, multi-line support, unsupported-syntax warnings (completed 2026-02-24)
- [x] **Phase 6: Settings** - Settings tab: seed toggle, default toggles, default AC/DC, default output mode (completed 2026-02-24)
- [x] **Phase 7: Packaging and Distribution** - Portable Windows 10 .exe via PyInstaller, build script, smoke-tested on clean machine (completed 2026-02-24)

</details>

### v2.0 Combat Manager (In Progress)

**Milestone Goal:** Evolve from bulk dice roller into a lightweight D&D 5e combat manager with monster editing, combat state tracking, data persistence, and polished output.

- [x] **Phase 8: Domain Expansion and Persistence Foundation** - New domain models, JSON persistence service, and Monster Math Engine — the prerequisite layer for all v2.0 features (completed 2026-02-25)
- [x] **Phase 9: Monster Editor and Equipment Presets** - Full stat editing with live cascading recalculation, equipment presets (+X weapons/armor/shields/foci), and persistent monster overrides (completed 2026-02-25)
- [x] **Phase 10: Persistent Encounter Sidebar** - QDockWidget sidebar visible across Library, Attack, and Saves tabs; SavesTab extracted from EncountersTab as standalone tab (completed 2026-02-26)
- [x] **Phase 11: Combat Tracker** - New Combat Tracker tab with HP bars, condition tracking, initiative ordering, turn cycling, and player character subtab (completed 2026-02-26)
- [x] **Phase 12: Save Roller Upgrades** - Subset creature selection, Magic Resistance and Legendary Resistance auto-detection, per-creature feature detection summary, Combat-to-Saves bridge (completed 2026-02-26)
- [x] **Phase 13: Output Polish, Theming, and UI** - Color-coded attack output, Roll20 template card rendering, theming system, and active toggle highlighting (completed 2026-02-26)

## Phase Details

### Phase 8: Domain Expansion and Persistence Foundation
**Goal**: All v2.0 domain data structures exist in code, modified monster data and encounter state survive app restarts, and derived values recalculate correctly from base attributes — the non-negotiable prerequisite for every other v2.0 phase
**Depends on**: Phase 7
**Requirements**: PERSIST-01, PERSIST-02, PERSIST-03, MATH-01, MATH-02, MATH-03, MATH-04, MATH-05
**Success Criteria** (what must be TRUE):
  1. After closing and reopening the app, previously loaded monsters, encounters, modified monsters, and macros are all present exactly as they were
  2. User can go to Settings and flush one data category (e.g. modified monsters) without affecting others; flushed data is gone on next open
  3. When any base attribute changes (e.g. STR, DEX, INT), all derived values that depend on it cascade automatically: ability modifier, relevant save bonuses, skill bonuses, attack to-hit, and damage bonuses
  4. When a monster's CR changes, the proficiency bonus updates and cascades to all save bonuses, skill bonuses, and attack bonuses that include proficiency
  5. The math engine validates saving throw bonuses as non-proficient (mod only), proficient (mod + prof), or expertise (mod + 2x prof) — any other value is flagged as custom; on modified spellcasters, spell attack bonus = casting mod + prof + focus, spell save DC = 8 + casting mod + prof + focus
**Plans**: 3 plans
Plans:
- [ ] 08-01-PLAN.md -- Domain models + PersistenceService (JSON persistence for 4 categories)
- [ ] 08-02-PLAN.md -- MonsterMathEngine + MathValidator + SpellcastingDetector (TDD)
- [ ] 08-03-PLAN.md -- App wiring: auto-save, closeEvent, statusBar, Settings flush UI

### Phase 9: Monster Editor and Equipment Presets
**Goal**: DMs can open any monster in an editor, tweak any stat or add equipment, see all dependent values recalculate live, and save the result — either as an override of the base monster or as a named copy — with overrides persisting across sessions
**Depends on**: Phase 8
**Requirements**: EDIT-01, EDIT-02, EDIT-03, EDIT-04, EDIT-05, EDIT-06, EDIT-07, EDIT-08, EDIT-09, EDIT-10, EDIT-11, EQUIP-01, EQUIP-02, EQUIP-03, EQUIP-04, EQUIP-05, EQUIP-06, EQUIP-07, EQUIP-08, EQUIP-09
**Success Criteria** (what must be TRUE):
  1. User can open the editor on any library monster, change its STR to 20, and immediately see all to-hit bonuses and STR-based saves update in the preview without saving
  2. User can give a monster a +2 longsword and see the correct to-hit (ability mod + prof + 2) and damage (size-scaled dice + ability mod + 2) appear in the action list; for a finesse weapon on a DEX-heavy monster, DEX is used automatically
  3. User can apply a full plate armor preset and see AC calculated as 18 + magic bonus; the stealth disadvantage flag appears on the statblock
  4. User can save an edited monster as a new named copy; both the original and the copy appear in the library independently; edited monsters display a badge next to their name in the library
  5. Equipment-modified stat values display in a distinct color on the statblock, distinguishing them from base values
  6. User can add a custom named bonus (e.g. "+1d4 Bless") to a monster and it persists when switching between Library, Attack, and Saves tabs
**Plans**: 5 plans
Plans:
- [ ] 09-01-PLAN.md -- Domain model patches + SRD equipment data tables
- [ ] 09-02-PLAN.md -- EquipmentService math (TDD)
- [ ] 09-03-PLAN.md -- MonsterEditorDialog skeleton with core editing sections
- [ ] 09-04-PLAN.md -- Equipment UI + Actions + Buffs + color highlighting
- [ ] 09-05-PLAN.md -- Save/copy workflow + library badge + persistence

### Phase 10: Persistent Encounter Sidebar
**Goal**: The active encounter is always visible and accessible no matter which main tab the DM is on — a collapsible sidebar panel that persists across tab switches and app restarts, with full add/remove/save/load capability
**Depends on**: Phase 8
**Requirements**: SIDEBAR-01, SIDEBAR-02, SIDEBAR-03, SIDEBAR-04, SIDEBAR-05
**Success Criteria** (what must be TRUE):
  1. The sidebar showing the active encounter is visible while the DM is on the Library tab, the Attack Roller tab, and the Saves tab simultaneously — switching tabs does not hide or reset it
  2. User can click a monster in the Library and add it to the encounter via the sidebar; it appears immediately in the sidebar list with a count field
  3. User can collapse the sidebar by clicking the toggle on its edge, reclaiming horizontal space, and expand it again; the encounter contents are unchanged
  4. After closing and reopening the app, the sidebar shows the same encounter that was active at close
  5. User can save the current encounter from the sidebar and load a different saved encounter; the sidebar updates to show the loaded encounter
**Plans**: 2 plans
Plans:
- [ ] 10-01-PLAN.md -- EncounterSidebarDock widget + persistence schema + AppSettings
- [ ] 10-02-PLAN.md -- MainWindow wiring + LoadEncounterDialog + SavesTab refactor + verification

### Phase 11: Combat Tracker
**Goal**: DMs can manage the full combat loop — initiative, HP damage and healing, conditions with duration, and turn order cycling — for all encounter combatants in a single dedicated tab, with state that persists across sessions
**Depends on**: Phase 10
**Requirements**: COMBAT-01, COMBAT-02, COMBAT-03, COMBAT-04, COMBAT-05, COMBAT-06, COMBAT-07, COMBAT-08, COMBAT-09, COMBAT-10, COMBAT-11, COMBAT-12, COMBAT-13, COMBAT-14, COMBAT-15
**Success Criteria** (what must be TRUE):
  1. User can load an encounter into the Combat Tracker and roll initiative for all monsters in one click; the list sorts by initiative descending
  2. User can enter "-23" in a combatant's damage field and see temp HP absorb the hit first, then the remainder come off current HP; the health bar updates color (green/yellow/red) to reflect current HP percentage
  3. User can add "Poisoned" from the condition preset dropdown with a 3-round duration; after clicking "Next Turn" three times, the condition is flagged as expired or auto-removed
  4. User can add player characters in the PC subtab with name, AC, HP, and conditions; PCs appear in the initiative order alongside monsters
  5. User can select one or more monsters in the Combat Tracker and click a button to jump to the Saves tab with exactly those monsters pre-loaded
**Plans**: 4 plans
Plans:
- [ ] 11-01-PLAN.md -- CombatTrackerService domain models + TDD + PersistenceService extension
- [ ] 11-02-PLAN.md -- Core UI: HpBar, CombatantCard, CombatLogPanel, CombatTrackerTab skeleton
- [ ] 11-03-PLAN.md -- Initiative ordering, grouped display, turn cycling, toggleable stats
- [ ] 11-04-PLAN.md -- PC subtab, multi-select, AOE damage, Saves integration, MainWindow wiring

### Phase 12: Save Roller Upgrades
**Goal**: The Save Roller works directly from the sidebar encounter with per-creature selection, auto-detects Magic Resistance and Legendary Resistance from parsed monster traits, and clearly shows which creatures have which advantages applied
**Depends on**: Phase 10, Phase 11
**Requirements**: SAVE-08, SAVE-09, SAVE-10, SAVE-11, SAVE-12, SAVE-13, SAVE-14
**Success Criteria** (what must be TRUE):
  1. User can uncheck specific creatures from the encounter list before rolling; only the checked creatures appear in the save results
  2. A monster with "Magic Resistance" in its traits automatically rolls with advantage when the "Is save magical?" toggle is on; the save result row shows "Magic Resistance (auto)" in the feature column
  3. A monster with "Legendary Resistance (3/Day)" displays a remaining-uses counter in its save row; the DM sees a reminder when legendary resistance could apply
  4. User can open the feature detection filter list and add a custom trigger (e.g. "Evasion") with an assigned behavior (reminder or auto-advantage); it applies on the next save roll for any monster with that trait
  5. The per-creature feature detection summary shows detected features vs manually overridden advantage for every row in the results
**Plans**: 3 plans
Plans:
- [ ] 12-01-PLAN.md -- Domain models + FeatureDetectionService + persistence + settings (TDD-ready)
- [ ] 12-02-PLAN.md -- Sidebar checkboxes + Select All/None/Invert selection shortcuts
- [ ] 12-03-PLAN.md -- SavesTab UI overhaul: toggles, detection rules, per-row results with LR interaction, MainWindow wiring

### Phase 13: Output Polish, Theming, and UI
**Goal**: The app looks and feels polished — attack output is color-coded by damage type, Roll20 template macros render as styled cards, the DM can switch to a high-contrast or custom color theme, and all active toggles are visually obvious
**Depends on**: Phase 8
**Requirements**: OUTPUT-01, OUTPUT-02, OUTPUT-03, OUTPUT-04, THEME-01, THEME-02, THEME-03, THEME-04, UI-01
**Success Criteria** (what must be TRUE):
  1. An attack roll producing fire damage and piercing damage displays each damage component in a distinct color matching its type; a critical hit line is highlighted in a different color from a normal hit
  2. Pasting a `&{template:default}{{name=Fireball}}{{DC=15}}{{Type=DEX}}` macro into the Sandbox and rolling renders a styled card with a colored header row and labeled key/value rows below — not plain text
  3. User can open Settings, select the "High Contrast" theme, and immediately see the entire app recolor without restarting; switching back to the default theme also takes effect immediately
  4. User can change the macro sandbox font independently from the rest of the app; the sandbox uses the selected font while all other tabs use the app default
  5. All active toggles across all tabs (e.g. "DEX" selected on Saves, "Advantage" on Attack) are visually highlighted so the DM can see at a glance what rules are currently active
**Plans**: 5 plans
Plans:
- [ ] 13-01-PLAN.md -- ThemeService + AppSettings fields + main.py migration + toggle highlighting
- [ ] 13-02-PLAN.md -- Attack output HTML with damage type colors and crit/miss highlights
- [ ] 13-03-PLAN.md -- Preprocessor template_fields extension for Roll20 card rendering
- [ ] 13-04-PLAN.md -- SettingsTab theming controls (preset dropdown, custom colors, sandbox font)
- [ ] 13-05-PLAN.md -- TemplateCard widget + ResultPanel dispatch for Roll20 template macros

## Progress

**Execution Order:**
Phase 8 → Phase 9 (parallel with 10) → Phase 10 → Phase 11 → Phase 12 → Phase 13

| Phase | Milestone | Plans Complete | Status | Completed |
|-------|-----------|----------------|--------|-----------|
| 1. Dice Engine and Domain Foundation | v1.0 | 2/2 | Complete | 2026-02-23 |
| 2. Monster Import and Library | v1.0 | 4/4 | Complete | 2026-02-24 |
| 3. Attack Roller | v1.0 | 4/4 | Complete | 2026-02-24 |
| 4. Lists, Encounters, and Save Roller | v1.0 | 4/4 | Complete | 2026-02-24 |
| 5. Roll20 Macro Sandbox | v1.0 | 4/4 | Complete | 2026-02-24 |
| 6. Settings | v1.0 | 2/2 | Complete | 2026-02-24 |
| 7. Packaging and Distribution | v1.0 | 2/2 | Complete | 2026-02-24 |
| 8. Domain Expansion and Persistence Foundation | v2.0 | 3/3 | Complete | 2026-02-25 |
| 9. Monster Editor and Equipment Presets | v2.0 | 5/5 | Complete | 2026-02-26 |
| 10. Persistent Encounter Sidebar | v2.0 | 2/2 | Complete | 2026-02-26 |
| 11. Combat Tracker | v2.0 | 4/4 | Complete | 2026-02-26 |
| 12. Save Roller Upgrades | v2.0 | 3/3 | Complete | 2026-02-26 |
| 13. Output Polish, Theming, and UI | v2.0 | 5/5 | Complete | 2026-02-26 |
| 14. Bug Fixes & Critical Polish | v2.1 | 0/6 | In Progress | - |
| 15. Editor & Parser Overhaul | v2.1 | 0/? | Planned | - |
| 16. Buff System & Output Improvements | v2.1 | 0/? | Planned | - |

### Phase 14: Bug Fixes & Critical Polish

**Goal:** Fix all verified bugs from the v2.0 manual testing round and apply quick UX improvements to the Combat Tracker, Attack Roller output, and Encounter Sidebar — every fix is a targeted change to existing code with no new tabs, services, or major UI restructuring required
**Depends on:** Phase 13
**Requirements**: BUG-01 through BUG-16, UX-01 through UX-05

#### Bug Fixes (BUG-01 through BUG-16)

**BUG-01: Imported monsters not retained after restart**
- Repro: Run main.py → import monsters from MD file → close app → run main.py again → imported monsters are gone
- Note: Encounters created from those monsters DO persist (e.g. a Young Red Shadow Dragon encounter survived restarts). The issue is specifically with the loaded_monsters persistence category — either the source file paths aren't being saved, or they aren't being re-parsed on startup.
- Files: `src/persistence/service.py` (loaded_monsters category), `src/main.py` or `src/ui/app.py` (_load_persisted_data)

**BUG-02: Library search single-result click selects cell, not row**
- Repro: Search for "Lich" in library search bar → single result appears → click on the result → only one cell (name or CR or type) gets selected, not the whole row → detail panel on right does not load the monster's statblock
- When multiple results are shown, clicking works correctly (selects whole row, loads detail panel)
- Files: `src/ui/library_tab.py` (_on_selection_changed, table selection behavior)

**BUG-03: CR change doesn't immediately cascade**
- Repro: Open editor on any monster → change Challenge Rating → proficiency bonus and all dependent values (saves, skills, attack bonuses) don't visibly update until other values are also modified
- Expected: Changing CR should immediately recalculate proficiency bonus and cascade to all saves, skills, and attack to-hit bonuses in the live preview
- Files: `src/ui/monster_editor.py` (CR change handler), `src/domain/math_engine.py`

**BUG-04: Added skill proficiency not shown in modified color**
- Repro: Open editor → add Arcana skill proficiency → proficiency appears in live preview but uses base/default color instead of the steel blue (equipment) or amber (manual) modified-value color
- Expected: Any user-added skill proficiency should display in the modified-value color to distinguish it from the base creature's skills
- Files: `src/ui/monster_editor.py` (skill coloring logic), `src/ui/monster_detail_panel.py`

**BUG-05: Ability score changes don't live-update dependent skills**
- Repro: Add Arcana proficiency to a monster → then change Intelligence score → Arcana bonus in live preview doesn't update to reflect the new INT modifier
- Expected: Changing any ability score should cascade to all skills that depend on that ability (INT→Arcana/History/Nature/Religion/Investigation, WIS→Perception/Insight/etc.)
- Files: `src/ui/monster_editor.py` (ability score change handlers, skill recalculation)

**BUG-06: After-attack-text detection wrong for Lich's Paralyzing Touch**
- Repro: Import Lich from bestiary.md → open editor → look at Paralyzing Touch action → the after-attack text shows "on a failed save, or half as much on a success. The apparitions then disappear." which is text from a Lair Action, NOT the actual Paralyzing Touch text
- Expected after-attack-text: "The target must succeed on a DC 18 Constitution saving throw or be paralyzed for 1 minute. The target can repeat the saving throw at the end of each of its turns, ending the effect on itself on a success."
- Root cause: The statblock parser is incorrectly splitting/attributing text between actions — likely grabbing text from a subsequent action or lair action section
- Files: `src/parsing/statblock_parser.py` (action text extraction logic)

**BUG-07: Spellcasting foci not modifying DC/spell attack bonus**
- Repro: Open Lich in editor → add a Spellcasting Focus (e.g. Rod of the Pact Keeper +1) → spell attack bonus and spell save DC do not change
- Expected: Focus +N should add N to both spell attack bonus and spell save DC
- Files: `src/services/equipment_service.py`, `src/ui/monster_editor.py` (focus application logic)

**BUG-08: Non-nat-1 misses incorrectly colored with red tint**
- Repro: Roll attacks with a target AC high enough to cause misses → every miss line gets the red background tint, even when the d20 roll is not a natural 1
- Expected: Only natural 1 misses should get the red-tinted background. Regular misses (e.g. rolled 5 vs AC 19) should have no special background color
- Files: `src/ui/attack_roller_tab.py` (_wrap_miss_line, _format_compare_line_html — the miss wrapping is applied to ALL misses instead of only nat-1 misses)

**BUG-09: Crit output gold coloring issues**
- Repro: Roll attacks with a low crit range (e.g. 15) so multiple crits occur → observe:
  - First crit row: the entire line including all space to the right is gold (screenwide gold block), plus an extra gold layer over the attack roll portion but NOT the damage portion
  - Subsequent crits: similar double-gold layering on the attack name portion
- Expected: Crit lines should have a uniform gold background tint (rgba(212,175,55,0.25)) across the entire line, with no double-layering or screenwide gold blocks
- Files: `src/ui/attack_roller_tab.py` (_wrap_crit_line, _format_compare_line_html — likely applying gold tint at two levels: once on the outer line div and again on an inner span)

**BUG-10: Extra empty newline below each crit line**
- Repro: Roll attacks producing crits → each crit line has an extra blank line below it that normal hits don't have, causing uneven spacing in the output
- Expected: All attack lines (hit, crit, miss) should have consistent vertical spacing with no extra blank lines
- Files: `src/ui/attack_roller_tab.py` (HTML formatting — likely a `<br>` or `<p>` tag issue in crit line wrapping)

**BUG-11: Stats toggle button in Combat Tracker does nothing**
- Repro: In Combat Tracker → click "Stats" button in top-right → dropdown appears with checkboxes (speed, passive perception, etc.) → check/uncheck items → nothing visible changes on the combatant cards
- Expected: Checking "Speed" should show/hide speed values on all combatant cards, etc.
- Files: `src/ui/combat_tracker_tab.py` (stats menu action handlers), `src/ui/combatant_card.py` (toggleable stats widget)

**BUG-12: Group monsters — damage input doesn't appear**
- Repro: Have grouped monsters (e.g. 3x Goblin) in combat tracker → click on the group's HP bar → damage input field does not pop up
- Expected: Clicking the group HP bar should open a damage input that applies first-come-first-served (damage applied to first non-defeated member, overflow to next)
- Files: `src/ui/combatant_card.py` (GroupCard HP bar click handling)

**BUG-13: Group member can't collapse back to compact**
- Repro: Open a group → click a member to expand to full CombatantCard → there is no way to collapse it back to CompactSubRow, except by collapsing and re-expanding the entire group or expanding another member
- Expected: Each expanded member should have a collapse button or clicking the expanded card again should return it to CompactSubRow
- Files: `src/ui/combatant_card.py` (CompactSubRow, GroupCard expand/collapse logic)

**BUG-14: Drag-to-select doesn't work inside groups**
- Repro: Expand a group → try to rubber-band select individual members → selection box doesn't work within the group container
- Expected: Rubber-band selection should work on individual members inside an expanded group, selecting them for AOE damage or Send to Saves
- Files: `src/ui/combat_tracker_tab.py` (CombatantListArea rubber-band), `src/ui/combatant_card.py` (GroupCard)

**BUG-15: Legendary resistances refill to max between saves**
- Repro: Roll saves on a creature with Legendary Resistance (3/Day) → use 1 LR (counter goes to 2) → roll saves again → LR counter is back at 3 instead of staying at 2
- Expected: LR counters should persist across multiple save rolls within the same encounter. Only reset on encounter change or explicit reset.
- Note from codebase: LR counters live in `SavesTab._lr_counters` dict keyed by monster_name. The issue is likely that counters are being reset on each roll or on tab switch.
- Files: `src/ui/encounters_tab.py` (SavesTab._lr_counters, _roll_saves logic)

**BUG-16: 0 HP healthbar behavior**
- Repro: Damage a combatant to exactly 0 HP → healthbar becomes grey instead of red → try to heal the combatant with positive HP input
- Expected: At 0 HP the healthbar should turn grey (correct). It should still accept positive health input (healing) but should not accept further negative input (HP cannot go below 0).
- Files: `src/ui/combatant_card.py` (HpBar, damage_entered handler), `src/combat/service.py` (apply_damage)

#### Quick UX Improvements (UX-01 through UX-05)

**UX-01: Sidebar "Show" text rotated sideways**
- Current: When sidebar is collapsed to 60px strip, the "Show" button text is horizontal, making the collapsed strip wider than necessary
- Change: Rotate the "Show" text 90° (vertical) so the collapsed sidebar strip can be narrower (e.g. 24-30px instead of 60px)
- Files: `src/ui/encounter_sidebar.py` (_COLLAPSED_WIDTH, collapse UI)

**UX-02: Initiative box — "Init" label outside spinbox**
- Current: The initiative spinbox tries to display "Init: [number]" inside the box, which is too small to fit
- Change: Move the "Init" label text outside the spinbox (to the left as a QLabel), and have only the numeric value inside the spinbox
- Files: `src/ui/combatant_card.py` (CombatantCard initiative spinbox setup)

**UX-03: Rubber-band selection — allow starting from outside monster list**
- Current: Rubber-band selection only works if the cursor starts in the tight space to the left of loaded creatures. Clicking and dragging from a monster card gets intercepted by the card's own drag handling.
- Change: Allow the rubber-band selection box to be drawn even when the drag starts from on top of a monster card (perhaps with a modifier key, or by distinguishing short click+drag from intentional rubber-band gesture)
- Files: `src/ui/combat_tracker_tab.py` (CombatantListArea mouse events), `src/ui/combatant_card.py` (drag handling)

**UX-04: Condition "+" button fixed to far left**
- Current: The "+" button for adding conditions moves horizontally as conditions are added, making it hard to find when many conditions exist
- Change: Fix the "+" button to the far-left side of each combatant card so it is always accessible regardless of how many condition chips are present
- Files: `src/ui/combatant_card.py` (CombatantCard layout, condition chip row)

**UX-05: Condition chip overflow — prevent horizontal scroll**
- Current: When many conditions are added to a combatant, the card gets wider and a horizontal scrollbar appears at the bottom
- Change: Condition chips should wrap to a new line (flow layout) instead of extending horizontally. This keeps the card width consistent and prevents the scrollbar.
- Files: `src/ui/combatant_card.py` (condition chip container layout)

**Success Criteria** (what must be TRUE):
  1. Imported monsters from MD files survive app close+reopen (BUG-01)
  2. Clicking a single search result in the library selects the full row and loads the statblock (BUG-02)
  3. Changing CR in the editor immediately cascades to all dependent values in live preview (BUG-03)
  4. User-added skill proficiencies display in the modified-value color (BUG-04)
  5. Changing an ability score live-updates all dependent skill bonuses (BUG-05)
  6. Lich's Paralyzing Touch shows the correct after-attack text, not lair action text (BUG-06)
  7. Spellcasting foci correctly modify spell attack bonus and spell save DC (BUG-07)
  8. Only natural-1 misses have red background tint; regular misses have no background color (BUG-08)
  9. Crit lines have uniform gold tint with no double-layering or screenwide blocks (BUG-09)
  10. No extra blank lines below crit output lines (BUG-10)
  11. Stats toggle checkboxes in Combat Tracker show/hide the corresponding stats on cards (BUG-11)
  12. Group HP bars accept damage input on click (BUG-12)
  13. Expanded group members can be collapsed back to compact view (BUG-13)
  14. Rubber-band selection works on individual members inside expanded groups (BUG-14)
  15. LR counters persist across multiple save rolls within the same encounter (BUG-15)
  16. 0 HP healthbar is grey; healing works; HP cannot go below 0 (BUG-16)
  17. Collapsed sidebar strip is narrower with rotated "Show" text (UX-01)
  18. Init label is outside the spinbox; only the number is inside (UX-02)
  19. Rubber-band selection can start from anywhere in the combat tracker area (UX-03)
  20. Condition "+" button is always at the far-left of each card (UX-04)
  21. Condition chips wrap to new lines instead of causing horizontal scroll (UX-05)

**Plans:** 6 plans
Plans:
- [ ] 14-01-PLAN.md -- Persistence fix + Library selection fix + Sidebar rotated text (BUG-01, BUG-02, UX-01)
- [ ] 14-02-PLAN.md -- Editor cascade fixes: CR, skills, ability scores, spellcasting focus (BUG-03, BUG-04, BUG-05, BUG-07)
- [ ] 14-03-PLAN.md -- Parser section boundaries + Monster model legendary/lair actions (BUG-06)
- [ ] 14-04-PLAN.md -- Attack output HTML: crit/miss wrapping and line spacing (BUG-08, BUG-09, BUG-10)
- [ ] 14-05-PLAN.md -- Combat Tracker: stats toggle, LR counter persistence, 0 HP behavior (BUG-11, BUG-15, BUG-16)
- [ ] 14-06-PLAN.md -- Combatant card: group damage/collapse, rubber-band, Init label, condition chips (BUG-12, BUG-13, BUG-14, UX-02, UX-03, UX-04, UX-05)

### Phase 15: Editor & Parser Overhaul

**Goal:** Restructure the Monster Editor to separate traits from actions into a dedicated Traits tab, add full after-attack-text editing, label all action input fields, add rollable trait buttons with auto-dice-detection to the Attack Roller, support recharge abilities, add [[XdY]] average notation, display monster speed everywhere, and compact the editor layout — transforming the editor from a flat action list into a structured traits+actions+rollable-abilities system
**Depends on:** Phase 14
**Requirements**: PARSE-01 through PARSE-11

#### Parser & Editor Changes (PARSE-01 through PARSE-11)

**PARSE-01: Separate Traits from Actions — new Traits tab in editor**
- Current: All monster traits (e.g. Magic Resistance, Devil's Sight, Amphibious) are listed alongside attack actions in the Actions section of the editor, even though they are fundamentally different — traits are passive features with no to-hit or damage, actions are rollable attacks
- Change: Create a new "Traits" collapsible section (or tab) in the editor. The parser should classify entries: if an action has no to_hit_bonus and no damage_parts, it is a trait and should go into the traits list. Actual attacks (with to_hit or damage) stay in Actions.
- Parser impact: `statblock_parser.py` needs to separate parsed entries into `monster.actions` (attacks only) and a new `monster.traits` list
- Domain impact: Add `traits: list[Trait]` field to Monster dataclass where Trait has `name: str` and `description: str`
- Files: `src/parsing/statblock_parser.py`, `src/domain/models.py`, `src/ui/monster_editor.py`

**PARSE-02: Traits tab UI — openable panels with title and text body**
- Each trait in the Traits section should be displayed as a collapsible/openable panel:
  - Collapsed: shows only the trait name (e.g. "Magic Resistance")
  - Expanded: shows a title text field (editable name) and a multiline text field (editable description body)
- The user should be able to add new traits and remove existing ones
- Files: `src/ui/monster_editor.py` (new traits section)

**PARSE-03: After-attack-text editing support in Actions**
- Current: The text that follows the to-hit and damage rolls in an attack (e.g. the secondary effects of an Aboleth's Tentacle or a dragon's bite) cannot be viewed or edited in the action editor
- Change: Add a multiline text field below each action's damage fields that contains the after-attack-text. This text is the portion of `Action.raw_text` that comes after the to-hit and damage dice portions.
- Example: Aboleth's Tentacle has a lengthy description about the disease effect after the initial 2d6+5 bludgeoning damage. This text should be editable.
- Parser impact: `Action` dataclass may need an `after_text: str` field extracted from `raw_text`
- Files: `src/domain/models.py` (Action), `src/parsing/statblock_parser.py`, `src/ui/monster_editor.py`

**PARSE-04: Action field header labels**
- Current: In the Actions editor section, input fields (name, to-hit, damage dice, damage type, etc.) are unlabeled — the user must guess what each field does
- Change: Add a header row above the action input fields that labels each column (e.g. "Name", "To-Hit", "Damage Dice", "Damage Type", "Bonus", etc.)
- Files: `src/ui/monster_editor.py` (actions section layout)

**PARSE-05: Auto dice formula detection in traits**
- The parser should automatically detect dice formulas within trait text (e.g. "54 (12d8) acid damage" in a dragon's breath weapon description)
- Detected dice should be stored as metadata on the trait so the UI can make them rollable
- Regex pattern: look for patterns like `N (XdY)` or `XdY` within trait descriptions
- Files: `src/parsing/statblock_parser.py`, `src/domain/models.py` (Trait model with detected dice)

**PARSE-06: Rollable trait buttons in Attack Roller tab**
- Current: The Attack Roller tab only shows weapon/spell attacks from the Actions list
- Change: Below the standard attack rows, add an additional row of buttons for traits that have rollable dice (detected via PARSE-05). Example: An Adult Black Dragon would show Claw, Bite, Tail as normal attack rows, then below them a row with an "Acid Breath" button.
- Clicking a rollable trait button should:
  1. Paste the full trait title and description body into the roll output
  2. Auto-roll any detected dice within the text (e.g. replace "54 (12d8)" with the actual roll result)
  3. Apply damage-type coloring to the rolled result
- Files: `src/ui/attack_roller_tab.py` (new trait button row), `src/domain/models.py`

**PARSE-07: Recharge ability support**
- Traits with recharge notation (e.g. "Acid Breath (Recharge 5-6)") should:
  1. Be detected by the parser and marked with recharge range (e.g. min=5, max=6)
  2. When the rollable trait button is clicked, automatically roll 1d6 for recharge
  3. Display the recharge roll in the output name: "Acid Breath (Recharge 5-6) [rolled: 4]" where the rolled value is colored green if it meets the recharge threshold, red if not
- Files: `src/parsing/statblock_parser.py` (recharge detection), `src/domain/models.py` (Trait.recharge_range), `src/ui/attack_roller_tab.py`

**PARSE-08: Double-bracket [[XdY]] auto-average notation**
- When a user types dice notation surrounded by double square brackets in any editable text field in the editor (e.g. `[[12d6]]`), the live preview should automatically display the average of that roll to the left of the bracketed dice.
- Example: User types `[[12d6]]` → preview shows `42 [[12d6]]` (where 42 is the average of 12d6 = 12 * 3.5 = 42)
- This follows the D&D convention of showing "average (dice)" in statblocks
- Files: `src/ui/monster_editor.py` (live preview rendering), `src/ui/monster_detail_panel.py`

**PARSE-09: Speed display in library and editor views**
- Current: Monster speed is not displayed in the library detail panel or the editor preview, making it impossible to verify equipment effects on speed (e.g. heavy armor reducing speed for low-STR creatures)
- Change: Add speed display to:
  1. The library tab's monster detail panel (right side)
  2. The editor's live preview panel
- Speed should show all speed types the monster has (e.g. "30 ft., fly 80 ft., swim 30 ft.")
- Files: `src/ui/monster_detail_panel.py`, `src/ui/monster_editor.py`, `src/domain/models.py` (verify Monster has speed field)

**PARSE-10: Editor layout compaction**
- Current: Challenge Rating, Skills, and Hit Points are in separate collapsible sections from the primary 6 ability scores, requiring extra scrolling
- Change: Merge CR, HP, and Skills into the same collapsible section as the ability scores (or at minimum, reduce the number of separate collapsible sections so these commonly-used fields are closer together)
- Files: `src/ui/monster_editor.py` (section layout)

**PARSE-11: Equipment section repositioned to bottom**
- Current: Equipment section position in the editor is mixed in with other sections
- Change: Move the Equipment section to the bottom of the editor's left column, positioned right above the Buffs section. This groups "gear and bonuses" together and keeps the stat-editing sections at the top.
- Files: `src/ui/monster_editor.py` (section ordering)

**Success Criteria** (what must be TRUE):
  1. Traits (e.g. Magic Resistance, Devil's Sight) appear in a separate Traits section, NOT in Actions (PARSE-01)
  2. Each trait can be expanded to show and edit its title and full description text (PARSE-02)
  3. After-attack-text for attacks like Aboleth's Tentacle is visible and editable in the action editor (PARSE-03)
  4. All action input fields have clear column header labels (PARSE-04)
  5. Dice formulas within trait text (e.g. "12d8" in dragon breath) are automatically detected (PARSE-05)
  6. The Attack Roller shows rollable trait buttons below the standard attack rows; clicking "Acid Breath" rolls the dice and outputs the full trait text with rolled results and damage-type coloring (PARSE-06)
  7. Recharge abilities auto-roll 1d6 and display the result in the output name with pass/fail coloring (PARSE-07)
  8. Typing `[[12d6]]` in a trait description shows `42 [[12d6]]` in the live preview (PARSE-08)
  9. Monster speed is visible in both the library detail panel and the editor preview (PARSE-09)
  10. CR, HP, and Skills sections are compacted alongside the ability scores in the editor (PARSE-10)
  11. Equipment section is at the bottom of the editor, right above Buffs (PARSE-11)

Plans:
- [ ] TBD (run /gsd:plan-phase 15 to break down)

### Phase 16: Buff System & Output Improvements

**Goal:** Revamp the buff system so each buff can independently target specific roll types (attacks, saves, ability checks, damage), auto-calculate buff dice into attack and save rolls, add creature/attack headers and per-damage-type summaries to attack output, implement encounter naming with timestamps and editable names, make the sidebar user-resizable, and add descriptive health-level text to combat tracker HP bars
**Depends on:** Phase 15
**Requirements**: BUFF-01 through BUFF-03, OUT-01 through OUT-02, ENC-01 through ENC-03, COMBAT-UX-01 through COMBAT-UX-02

#### Buff System Revamp (BUFF-01 through BUFF-03)

**BUFF-01: Per-roll-type buff targeting**
- Current: BuffItem.targets is a single value from (attack_rolls, saving_throws, all). Bless affects both saves and attacks but NOT ability checks or damage, and there is no way to select this combination without adding Bless twice.
- Change: Replace the single `targets` field with individual boolean toggles:
  - `affects_attacks: bool` — applies to attack rolls
  - `affects_saves: bool` — applies to saving throws
  - `affects_ability_checks: bool` — applies to ability checks
  - `affects_damage: bool` — applies to damage rolls
- The editor UI should show 4 checkboxes per buff, allowing any combination
- Bless default: attacks=True, saves=True, checks=False, damage=False
- Files: `src/domain/models.py` (BuffItem), `src/ui/monster_editor.py` (buff section UI), `src/persistence/service.py` (serialization)

**BUFF-02: Buff auto-calculation in attack rolls**
- Current: Bless appears as a label in the Attack Roller ("Buffs: Bless (+1d4 attack rolls)") but the +1d4 is NOT actually added to the attack roll calculation
- Change: When a monster has a buff targeting attacks, the buff dice/bonus should be:
  1. Automatically rolled alongside each attack roll
  2. Added to the to-hit total
  3. Shown in the output breakdown (e.g. `[d20=15] + 7 + 1d4(3) = 25 vs AC 19 → HIT`)
- Files: `src/ui/attack_roller_tab.py` (roll calculation), `src/rolling/attack_roller.py` (if applicable)

**BUFF-03: Buff display and calculation in saves**
- Current: Even when a buff is marked as affecting saves, it doesn't show up in the Saves tab and isn't used in save calculations
- Change: When a monster has a buff targeting saves:
  1. The buff should be visible in the saves result row (e.g. "Bless: +1d4")
  2. The buff dice/bonus should be automatically rolled and added to the save total
  3. Display should match the attack roller style (buff dice shown in breakdown)
- Files: `src/ui/encounters_tab.py` (SavesTab), `src/rolling/save_roller.py`

#### Output Improvements (OUT-01 through OUT-02)

**OUT-01: Attack output header**
- Current: When rolling attacks, the output starts directly with "#1: [d20=...]" with no indication of which creature or attack type was rolled
- Change: Add a header line above the attack results that identifies the creature and attack. Format: `"{Monster Name} — {Attack Name} ({count}x)"` e.g. "Young Red Dragon — Bite (13x)"
- This header should also appear in the copied-to-clipboard plain text version
- Files: `src/ui/attack_roller_tab.py` (output formatting, both HTML and plain text)

**OUT-02: Damage type breakdown in summary**
- Current: Summary line shows only total damage: `Summary: 12 hits / 1 misses (9 crit) | Total damage: 475`
- Change: To the right of the total damage, add per-damage-type subtotals with damage-type coloring. Example: `Summary: 12 hits / 1 misses (9 crit) | Total: 475 — 398 piercing, 77 fire`
  - "398 piercing" in the piercing damage color (slate gray)
  - "77 fire" in the fire damage color (#FF6B35)
- Files: `src/ui/attack_roller_tab.py` (_format_summary_html, damage tracking)

#### Encounter Management (ENC-01 through ENC-03)

**ENC-01: Encounter naming with hour:minute timestamps**
- Current: Saved encounters have an auto-generated name based on date, but no time component. Multiple encounters saved in the same day are hard to distinguish.
- Change: Auto-generated encounter names should include hour:minute timestamp (e.g. "2026-02-26 14:35 — 3 creatures"). The DM should also be able to type a custom name when saving.
- When a custom name is provided, format: `"{Custom Name} — 2026-02-26 14:35 — 3 creatures"`
- Files: `src/ui/encounter_sidebar.py` (save logic), `src/persistence/service.py`

**ENC-02: Encounter name editing in load dialog**
- Current: Encounter names cannot be changed after saving
- Change: In the Load Encounter dialog, the DM should be able to double-click an encounter's name to edit it inline. The new name auto-saves when the user presses Enter or clicks away (focus lost).
- Files: `src/ui/encounter_sidebar.py` (LoadEncounterDialog or equivalent)

**ENC-03: Sidebar user-resizable width**
- Current: The sidebar has a fixed expanded width (_DEFAULT_EXPANDED_WIDTH = 300). When monster names are long combined with the count spinbox and delete button, the content overflows and only a horizontal scrollbar provides access.
- Change: The sidebar should be resizable by the user dragging its left edge. The resized width should be persisted across sessions (AppSettings.sidebar_width already exists).
- QDockWidget may already support resize handles — verify and enable if so, or add a custom resize grip
- Files: `src/ui/encounter_sidebar.py`, `src/persistence/settings.py` (AppSettings.sidebar_width)

#### Combat UX (COMBAT-UX-01 through COMBAT-UX-02)

**COMBAT-UX-01: Health bar descriptive text labels**
- Current: HP bars change color (green/yellow/red) but there's no text description of the creature's health level
- Change: Add a small text label near or within the health bar that describes the health level:
  - 100% HP: "Uninjured"
  - 99%-76% HP: "Barely Injured"
  - 75%-51% HP: "Injured"
  - 50%-26% HP: "Badly Injured"
  - 25%-1% HP: "Near Death"
  - 0% HP: (grey bar, creature defeated)
- The health bar color should also follow these bands consistently
- Files: `src/ui/combatant_card.py` (HpBar widget)

**COMBAT-UX-02: Health bar color consistency**
- Current: HP bar transitions at >50% green, 25-50% yellow, <25% red — but these don't match the descriptive bands above, and the transition from the new descriptive labels needs to match
- Change: Align HP bar colors with the descriptive bands:
  - 100%: bright green (Uninjured)
  - 99%-76%: green-yellow (Barely Injured)
  - 75%-51%: yellow (Injured)
  - 50%-26%: orange (Badly Injured)
  - 25%-1%: red (Near Death)
  - 0%: grey (Defeated)
- Files: `src/ui/combatant_card.py` (HpBar paintEvent color calculation)

**Success Criteria** (what must be TRUE):
  1. A buff can be configured to affect attacks and saves but NOT ability checks or damage — using 4 independent checkboxes (BUFF-01)
  2. A monster with Bless (+1d4 attacks) has the d4 automatically rolled and added to each attack roll's to-hit total, visible in the output breakdown (BUFF-02)
  3. A monster with Bless (+1d4 saves) has the d4 automatically rolled and added to save roll totals, visible in the saves result row (BUFF-03)
  4. Attack output starts with a header line identifying the creature and attack type (OUT-01)
  5. Summary line shows per-damage-type subtotals with matching damage-type colors (OUT-02)
  6. Saved encounters include hour:minute timestamps and support custom names (ENC-01)
  7. Encounter names are editable by double-clicking in the load dialog (ENC-02)
  8. The sidebar can be resized by dragging its edge; width persists across sessions (ENC-03)
  9. HP bars show descriptive text ("Barely Injured", "Near Death", etc.) matching the HP percentage (COMBAT-UX-01)
  10. HP bar colors align with the 5-band health level system (COMBAT-UX-02)

Plans:
- [ ] TBD (run /gsd:plan-phase 16 to break down)
