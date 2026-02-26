# Roadmap: RollinRollin

## Milestones

- [x] **v1.0 Bulk Dice Roller** - Phases 1-7 (shipped 2026-02-24)
- [ ] **v2.0 Combat Manager** - Phases 8-13 (in progress)

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
- [ ] **Phase 10: Persistent Encounter Sidebar** - QDockWidget sidebar visible across Library, Attack, and Saves tabs; SavesTab extracted from EncountersTab as standalone tab
- [ ] **Phase 11: Combat Tracker** - New Combat Tracker tab with HP bars, condition tracking, initiative ordering, turn cycling, and player character subtab
- [ ] **Phase 12: Save Roller Upgrades** - Subset creature selection, Magic Resistance and Legendary Resistance auto-detection, per-creature feature detection summary, Combat-to-Saves bridge
- [ ] **Phase 13: Output Polish, Theming, and UI** - Color-coded attack output, Roll20 template card rendering, theming system, and active toggle highlighting

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
**Plans**: TBD

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
**Plans**: TBD

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
**Plans**: TBD

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
| 10. Persistent Encounter Sidebar | v2.0 | 2/2 | Human verify | - |
| 11. Combat Tracker | v2.0 | 0/? | Not started | - |
| 12. Save Roller Upgrades | v2.0 | 0/? | Not started | - |
| 13. Output Polish, Theming, and UI | v2.0 | 0/? | Not started | - |
