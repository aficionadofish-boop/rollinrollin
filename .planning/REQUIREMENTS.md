# Requirements: RollinRollin

**Defined:** 2026-02-25
**Core Value:** DMs can manage the full combat loop — prep monsters, roll attacks and saves, and track combat state — in seconds, with D&D 5e rule fidelity and persistent data.

## v2.0 Requirements

Requirements for milestone v2.0 (Combat Manager). Each maps to roadmap phases.

### Data Persistence

- [x] **PERSIST-01**: App stores loaded monsters, encounters, modified monsters, and macros in an internal data store that survives between sessions
- [x] **PERSIST-02**: User can flush specific persistent data categories (loaded monsters, encounters, modified monsters, macros) from Settings
- [x] **PERSIST-03**: Data store loads automatically on app start and saves on close/change

### Monster Editor

- [x] **EDIT-01**: User can activate edit mode on a selected monster in the Library tab
- [x] **EDIT-02**: User can modify base attributes (STR, DEX, CON, INT, WIS, CHA)
- [x] **EDIT-03**: User can modify saving throw bonuses
- [x] **EDIT-04**: User can modify hit points
- [x] **EDIT-05**: User can modify skill bonus values
- [x] **EDIT-06**: User can modify challenge rating (recalculates proficiency bonus)
- [ ] **EDIT-07**: User can edit existing actions (name, to-hit, damage)
- [ ] **EDIT-08**: User can add new actions to a monster
- [x] **EDIT-09**: When saving, user chooses: save as new copy (custom name), overwrite base monster, or discard
- [x] **EDIT-10**: User can add custom named bonuses to a monster (e.g. "+1d4 Bless", "+2 Rage") that persist across tabs
- [x] **EDIT-11**: Edited monsters display a badge next to their name in the library indicating they have been modified

### Monster Math Engine

- [x] **MATH-01**: When any base attribute changes (STR, DEX, CON, INT, WIS, CHA), all derived values cascade: ability modifier, save bonuses, skill bonuses, attack to-hit, damage bonuses for all actions using that attribute
- [x] **MATH-02**: When CR changes, proficiency bonus updates and cascades to saves, skills, and attack bonuses
- [x] **MATH-03**: Engine validates attack to-hit = proficiency + relevant ability modifier and damage bonuses on attacks; flags mismatches
- [x] **MATH-04**: Engine validates saving throw bonuses against three accepted states: non-proficient (ability mod only), proficient (ability mod + prof bonus), expertise (ability mod + 2x prof bonus); any other value flagged as custom
- [x] **MATH-05**: On modified monsters with spellcasting features, engine validates spell attack bonus = spellcasting ability mod + prof bonus + focus bonus, and spell save DC = 8 + spellcasting ability mod + prof bonus + focus bonus

### Equipment Presets

- [x] **EQUIP-01**: User can give a monster a +0/+1/+2/+3 weapon with correct to-hit (ability mod + prof + magic) and damage (size-scaled dice + ability mod + magic)
- [x] **EQUIP-02**: Weapon uses STR by default; DEX if finesse and DEX > STR; always DEX for ranged (except thrown like javelin)
- [x] **EQUIP-03**: Weapon damage dice scale by monster size: Medium=1x, Large=2x, Huge=3x, Gargantuan=4x
- [x] **EQUIP-04**: User can give a monster armor from the full SRD armor list with correct AC calculation (armor type + DEX mod + magic bonus)
- [x] **EQUIP-05**: Armor with stealth disadvantage displays that flag on the statblock
- [x] **EQUIP-06**: Armor with strength requirements checks if the monster meets them; flags movement penalty if not
- [x] **EQUIP-07**: User can give a monster a +0/+1/+2/+3 shield (+2 AC + magic); only the highest-bonus shield applies
- [x] **EQUIP-08**: User can give a monster a +1/+2/+3 spellcasting focus item (Rod of the Pact Keeper, Bloodwell Vial, Moon Sickle, Arcane Grimoire) which adds +X to spell attack bonus and spell save DC
- [ ] **EQUIP-09**: All equipment-modified values display in a distinct color on the statblock

### Persistent Encounter Sidebar

- [ ] **SIDEBAR-01**: Collapsible sidebar visible on Library, Attack Roller, and Saves tabs showing the active encounter
- [ ] **SIDEBAR-02**: User can add/remove monsters from the encounter via the sidebar
- [ ] **SIDEBAR-03**: Sidebar encounter persists between tab switches and between sessions
- [ ] **SIDEBAR-04**: User can save/load encounters from the sidebar
- [ ] **SIDEBAR-05**: Sidebar can be collapsed/expanded by clicking a toggle on its edge

### Combat Tracker

- [ ] **COMBAT-01**: New Combat Tracker tab showing all combatants from the active encounter
- [ ] **COMBAT-02**: Each combatant has a visual health bar with editable current/max HP
- [ ] **COMBAT-03**: Each combatant has a temp HP field (absorbed before regular HP)
- [ ] **COMBAT-04**: Each combatant can have multiple conditions/buffs with name and round duration
- [ ] **COMBAT-05**: Preset dropdown with standard 5e conditions (Blinded, Charmed, Deafened, Frightened, Grappled, Incapacitated, Invisible, Paralyzed, Petrified, Poisoned, Prone, Restrained, Stunned, Unconscious)
- [ ] **COMBAT-06**: Preset dropdown with common D&D buffs/effects (Bless, Shield, Hypnotic Pattern, Fear, Web, Entangle, Maze, etc.)
- [ ] **COMBAT-07**: User can add custom conditions with name and duration
- [ ] **COMBAT-08**: Conditions have unique colors per type
- [ ] **COMBAT-09**: One-button initiative roll for all encounter monsters using existing dice engine
- [ ] **COMBAT-10**: Grouped initiative option: same monster types share initiative, displayed as "Nx [Monster]" with expandable dropdown for individual HP/condition tracking
- [ ] **COMBAT-11**: Player character subtab with name, AC, HP, condition trackers; PCs can be added to initiative
- [ ] **COMBAT-12**: Initiative mode toggle: enabled sorts by initiative (descending) with "Next Turn" cycling; disabled shows "Pass 1 Round" button
- [ ] **COMBAT-13**: When turn advances or "Pass 1 Round" is clicked, all condition round counters decrement by 1; conditions at 0 are flagged/removed
- [ ] **COMBAT-14**: User can select specific monsters in tracker and click a button to jump to Saves tab with those loaded
- [ ] **COMBAT-15**: User can enter a signed number (+12, -23) in a damage/healing field per combatant; app auto-applies (temp HP absorbed first, remainder from current HP)

### Save Roller Upgrades

- [ ] **SAVE-08**: User can select a subset of creatures from the encounter for save rolls (not all-or-nothing)
- [ ] **SAVE-09**: App detects Magic Resistance from monster traits via keyword matching; auto-applies advantage when "Spell Save" toggle is on
- [ ] **SAVE-10**: App detects Legendary Resistance with uses/day count; displays reminder in save log
- [ ] **SAVE-11**: Toggleable checkboxes: "Is save magical?", enable/disable Magic Resistance detection, enable/disable Legendary Resistance detection
- [ ] **SAVE-12**: Detected features override the global advantage setting per-creature (e.g. Magic Resistance creature rolls with advantage even when global is normal)
- [ ] **SAVE-13**: Feature detection summary shown per creature in save results
- [ ] **SAVE-14**: User can open and edit the feature detection filter list to add custom triggers with a name and assigned behavior (reminder like Legendary Resistance, or auto-advantage like Magic Resistance)

### Output Polish

- [ ] **OUTPUT-01**: Attack roll outputs use different colors for different damage types
- [ ] **OUTPUT-02**: Critical hits and critical misses are color-coded in attack output
- [ ] **OUTPUT-03**: Macro sandbox parses `&{template:default}{{name=XYZ}}{{key=value}}` syntax
- [ ] **OUTPUT-04**: Template macros render as styled cards approximating Roll20 layout (colored header, labeled key/value rows)

### Theming

- [ ] **THEME-01**: Settings offers multiple text/background color pair presets
- [ ] **THEME-02**: User can set text and background colors separately
- [ ] **THEME-03**: High contrast mode available
- [ ] **THEME-04**: User can change fonts for the macro sandbox separately from the rest of the app

### UI Polish

- [ ] **UI-01**: Active toggles across all tabs are visually highlighted to clearly indicate the current selection (e.g. DEX on Saves tab, Advantage on Attack tab)

## v1.0 Requirements (Validated)

All 56 v1.0 requirements shipped and validated. See MILESTONES.md for full list.

Key categories: Dice Engine (5), Monster Import (7), Monster Library (6), Attack Roller (12), Save Roller (7), Lists (5), Encounters (6), Macro Sandbox (7), Settings (4), Workspace/Distribution (3).

## Future Requirements (Deferred)

### From v1 Planning

- **SAVE-V2-01**: Multi-round repeat: user specifies N rounds; save is rolled N times per participant in sequence
- **SAVE-V2-02**: Manual participant rows: add entries by name + bonus without needing an encounter
- **LIB-V2-02**: Dedup/merge on re-import: when a monster with the same name already exists, user is prompted to create a new copy or overwrite
- **OUT-V2-01**: Export roll log to `.txt` file for session notes
- **ENC-V2-02**: Encounter-level presets: default Target AC and Save DC stored per encounter
- **SAND-V2-01**: Toggle bar in sandbox (advantage/disadvantage, flat modifier, bonus dice)
- **ATTACK-V2-01**: Crit rule option: "max dice + roll dice" (for Champion Fighter / house rule)

### Deferred from v2.0 Scoping

- **EDIT-V3-01**: Diff view showing modified vs imported baseline monster values
- **OUTPUT-V3-01**: Multi-template rendering in a single macro (multiple `&{template:default}` blocks)

## Out of Scope

| Feature | Reason |
|---------|--------|
| VTT visuals (tokens, maps, line of sight) | Not the goal — lightweight combat manager, not a VTT |
| Full Roll20 macro ecosystem (API scripts, chat formatting) | Partial support only; templates are visual-only |
| Spellcasting modeling (spell slots, upcasting) | Only attack rolls, saves, and DC |
| Built-in monster database | User provides all data via Markdown import |
| Online sync / cloud save | Offline-first product |
| Deep condition rules (end-of-turn saves, concentration tracking) | Conditions are name + round countdown with auto-decrement only |
| Installer / auto-update | Portable .exe distribution model |
| Custom Roll20 templates (`&{template:mytemplate}`) | Only default template supported; custom templates require HTML/CSS authoring |
| Full CR recalculation on edit | Complex formula (DMG offensive/defensive averaging); would mislead DMs if wrong |
| Named magic item database | Scope explosion; free-text weapon name + numeric bonus covers the case |
| NLP trait parsing for all features | Unbounded scope; keyword match for known patterns only + user-editable triggers |

## Traceability

Which phases cover which requirements. Updated during roadmap creation.

| Requirement | Phase | Status |
|-------------|-------|--------|
| PERSIST-01 | Phase 8 | Complete |
| PERSIST-02 | Phase 8 | Complete |
| PERSIST-03 | Phase 8 | Complete |
| MATH-01 | Phase 8 | Complete |
| MATH-02 | Phase 8 | Complete |
| MATH-03 | Phase 8 | Complete |
| MATH-04 | Phase 8 | Complete |
| MATH-05 | Phase 8 | Complete |
| EDIT-01 | Phase 9 | Complete |
| EDIT-02 | Phase 9 | Complete |
| EDIT-03 | Phase 9 | Complete |
| EDIT-04 | Phase 9 | Complete |
| EDIT-05 | Phase 9 | Complete |
| EDIT-06 | Phase 9 | Complete |
| EDIT-07 | Phase 9 | Pending |
| EDIT-08 | Phase 9 | Pending |
| EDIT-09 | Phase 9 | Complete |
| EDIT-10 | Phase 9 | Complete |
| EDIT-11 | Phase 9 | Complete |
| EQUIP-01 | Phase 9 | Complete |
| EQUIP-02 | Phase 9 | Complete |
| EQUIP-03 | Phase 9 | Complete |
| EQUIP-04 | Phase 9 | Complete |
| EQUIP-05 | Phase 9 | Complete |
| EQUIP-06 | Phase 9 | Complete |
| EQUIP-07 | Phase 9 | Complete |
| EQUIP-08 | Phase 9 | Complete |
| EQUIP-09 | Phase 9 | Pending |
| SIDEBAR-01 | Phase 10 | Pending |
| SIDEBAR-02 | Phase 10 | Pending |
| SIDEBAR-03 | Phase 10 | Pending |
| SIDEBAR-04 | Phase 10 | Pending |
| SIDEBAR-05 | Phase 10 | Pending |
| COMBAT-01 | Phase 11 | Pending |
| COMBAT-02 | Phase 11 | Pending |
| COMBAT-03 | Phase 11 | Pending |
| COMBAT-04 | Phase 11 | Pending |
| COMBAT-05 | Phase 11 | Pending |
| COMBAT-06 | Phase 11 | Pending |
| COMBAT-07 | Phase 11 | Pending |
| COMBAT-08 | Phase 11 | Pending |
| COMBAT-09 | Phase 11 | Pending |
| COMBAT-10 | Phase 11 | Pending |
| COMBAT-11 | Phase 11 | Pending |
| COMBAT-12 | Phase 11 | Pending |
| COMBAT-13 | Phase 11 | Pending |
| COMBAT-14 | Phase 11 | Pending |
| COMBAT-15 | Phase 11 | Pending |
| SAVE-08 | Phase 12 | Pending |
| SAVE-09 | Phase 12 | Pending |
| SAVE-10 | Phase 12 | Pending |
| SAVE-11 | Phase 12 | Pending |
| SAVE-12 | Phase 12 | Pending |
| SAVE-13 | Phase 12 | Pending |
| SAVE-14 | Phase 12 | Pending |
| OUTPUT-01 | Phase 13 | Pending |
| OUTPUT-02 | Phase 13 | Pending |
| OUTPUT-03 | Phase 13 | Pending |
| OUTPUT-04 | Phase 13 | Pending |
| THEME-01 | Phase 13 | Pending |
| THEME-02 | Phase 13 | Pending |
| THEME-03 | Phase 13 | Pending |
| THEME-04 | Phase 13 | Pending |
| UI-01 | Phase 13 | Pending |

**Coverage:**
- v2.0 requirements: 64 total
- Mapped to phases: 64
- Unmapped: 0

---
*Requirements defined: 2026-02-25*
*Last updated: 2026-02-25 — traceability populated after roadmap creation*
