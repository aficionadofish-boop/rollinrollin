# Requirements: RollinRollin

**Defined:** 2026-02-23
**Core Value:** DMs can roll attacks and saving throws for groups of monsters in seconds, with full D&D 5e rule fidelity and clear hit/miss/damage breakdowns.

## v1 Requirements

### Dice Engine

- [x] **DICE-01**: Dice engine evaluates standard notation: NdM, +, -, *, /, parentheses, integer literals, whitespace-tolerant
- [x] **DICE-02**: Engine supports keep-highest/keep-lowest syntax (NdMkhN / NdMklN) for advantage, Elven Accuracy, etc.
- [x] **DICE-03**: Roll result includes full per-die breakdown (each die face shown, not just the total)
- [x] **DICE-04**: Engine supports seeded RNG — a seed value produces a deterministic roll sequence for testing/reproduction
- [x] **DICE-05**: Engine uses a single `Random` instance per session; seed=None uses system entropy for real play

### Monster Import

- [x] **IMPORT-01**: User can import one or more monster statblocks from a single Markdown file
- [x] **IMPORT-02**: User can import multiple Markdown files in one operation (batch import)
- [x] **IMPORT-03**: Parser is tolerant: a monster with missing fields still imports and is flagged as "incomplete" rather than failing
- [x] **IMPORT-04**: Each action that cannot be parsed is stored with its raw text and has no roll button (not silently dropped)
- [x] **IMPORT-05**: Import result panel shows: count successful, count incomplete, count action parse failures (with details per failure)
- [x] **IMPORT-06**: Parser handles at least 3 real-world Markdown statblock format variants (e.g. bold field labels, plain text, table ability scores)
- [x] **IMPORT-07**: Parser detects `+X to hit`, `Hit:` damage patterns, multi-component damage ("plus … damage"), and damage type labels

### Monster Library

- [x] **LIB-01**: Imported monsters persist in a runtime library accessible across tabs
- [x] **LIB-02**: User can search the library by monster name with instant (keystroke-level) filtering
- [x] **LIB-03**: Library displays monster list with name, AC, HP, and "incomplete" badge where applicable
- [x] **LIB-04**: User can view monster detail: AC, HP, ability scores, saving throw bonuses, and all actions
- [x] **LIB-05**: Library supports a user-assignable tag per monster (for source or custom grouping)
- [x] **LIB-06**: User can filter library by "incomplete" status

### Attack Roller

- [x] **ATTACK-01**: User can select a monster from the library, then select one of its actions to roll
- [x] **ATTACK-02**: User can specify N (how many attacks to roll at once, e.g. roll 8 attacks)
- [x] **ATTACK-03**: RAW mode shows per-attack breakdown: all d20 result(s), to-hit bonus, flat modifier, bonus dice results, final attack total; per-damage-part die results and subtotals; damage type labels
- [x] **ATTACK-04**: COMPARE mode requires a Target AC input; shows each attack as hit/miss with margin; damage rolls only on hits; summary of total hits, total misses, total damage
- [x] **ATTACK-05**: Advantage/disadvantage toggle: rolls 2d20, displays both faces, uses higher (adv) or lower (disadv)
- [x] **ATTACK-06**: Nat-1 always miss and Nat-20 always hit toggles (independent on/off)
- [x] **ATTACK-07**: Crit enable toggle with configurable crit range (default 20; adjustable down to 18)
- [x] **ATTACK-08**: Crit damage rule: double all damage dice (default 5e rule)
- [x] **ATTACK-09**: Flat modifier input (positive or negative integer) applied to attack roll total
- [x] **ATTACK-10**: Bonus dice list: user can add one or more signed dice formulas (e.g. +1d4 Bless, -1d6) stacked and added to attack total
- [x] **ATTACK-11**: Roll output can be copied to clipboard in one click
- [x] **ATTACK-12**: Per-damage-part results show damage type (e.g. "14 slashing + 7 poison")

### Save Roller

- [ ] **SAVE-01**: User can select a save ability (STR/DEX/CON/INT/WIS/CHA) and set a DC
- [ ] **SAVE-02**: Participants can be loaded from the current encounter (each member rolls individually; monster's save bonus or ability modifier used automatically)
- [ ] **SAVE-03**: Per-participant result shows: d20 face(s), save bonus, total, success/fail, margin vs DC
- [ ] **SAVE-04**: Summary shows total success count and total fail count
- [ ] **SAVE-05**: Advantage/disadvantage toggle for saves (rolls 2d20, takes higher/lower)
- [ ] **SAVE-06**: Flat modifier input for saves (applied to all participants)
- [ ] **SAVE-07**: Save roll output can be copied to clipboard in one click

### Lists

- [x] **LIST-01**: User can create a named list by selecting monsters from the library with a count per monster
- [x] **LIST-02**: User can edit list member counts
- [x] **LIST-03**: User can save a list to a Markdown file in the workspace `lists/` folder
- [x] **LIST-04**: User can load/import a list from a Markdown file
- [x] **LIST-05**: On list import, if a monster name does not match the library, the unresolved entry is shown in an "Unresolved Entries" panel for manual re-linking (not silently dropped)

### Encounters

- [x] **ENC-01**: User can create a named encounter by selecting monsters from the library (or from a list) with a count per monster
- [x] **ENC-02**: User can edit encounter member counts and labels
- [ ] **ENC-03**: User can save an encounter to a Markdown file in the workspace `encounters/` folder
- [ ] **ENC-04**: User can load/import an encounter from a Markdown file
- [ ] **ENC-05**: On encounter import, unresolved monster names are shown in an "Unresolved Entries" panel for manual re-linking
- [ ] **ENC-06**: The active encounter can be loaded into the Save Roller as the participant list

### Macro Sandbox

- [ ] **SAND-01**: User can type or paste a free-text dice expression (e.g. `1d20+5+1d4`) and execute it with a Roll button
- [ ] **SAND-02**: Output shows total result and full per-die breakdown
- [ ] **SAND-03**: Sandbox resolves Roll20 inline rolls: `[[expr]]` expressions are evaluated and replaced with their numeric result
- [ ] **SAND-04**: Sandbox resolves Roll20 query rolls: `?{prompt|option,value|...}` shows a choice dialog; chosen value is substituted before evaluation
- [ ] **SAND-05**: Multi-line input: each non-empty line is processed as a separate roll; results displayed in order
- [ ] **SAND-06**: `/roll` and `/r` prefix is stripped before parsing (not treated as a syntax error)
- [ ] **SAND-07**: Unsupported Roll20 syntax (e.g. `@{attr}` references, `&{template:...}`) emits a visible parse warning rather than crashing

### Settings

- [ ] **SET-01**: User can enable/disable seeded RNG and set a seed value; all rolls in the session use the seed when enabled
- [ ] **SET-02**: User can configure default toggles: crit enable, nat-1 always miss, nat-20 always hit
- [ ] **SET-03**: User can set the default output mode (RAW or COMPARE) applied when opening the Attack Roller
- [ ] **SET-04**: User can set a default Target AC (pre-filled in COMPARE mode) and default Save DC (pre-filled in Save Roller)

### Workspace and Distribution

- [x] **WS-01**: User can select or change the workspace folder; app reads/writes all Markdown files within it under `monsters/`, `lists/`, `encounters/`, `exports/` subfolders
- [ ] **WS-02**: App launches and runs fully offline with no internet connection required
- [ ] **WS-03**: App is distributed as a single portable `.exe` for Windows 10 (no Python install required on target machine)

---

## v2 Requirements

### Save Roller Extensions

- **SAVE-V2-01**: Multi-round repeat: user specifies N rounds; save is rolled N times per participant in sequence
- **SAVE-V2-02**: Manual participant rows: add entries by name + bonus without needing an encounter

### Library Extensions

- **LIB-V2-01**: Monster fixup UI: user can manually correct parsed fields (AC, HP, ability scores, action to-hit/damage)
- **LIB-V2-02**: Dedup/merge on re-import: when a monster with the same name already exists, user is prompted to create a new copy or overwrite

### Output

- **OUT-V2-01**: Export roll log to `.txt` file for session notes

### Encounter Extensions

- **ENC-V2-01**: Member overrides: per-encounter save bonus override for individual members
- **ENC-V2-02**: Encounter-level presets: default Target AC and Save DC stored per encounter

### Sandbox Extensions

- **SAND-V2-01**: Toggle bar in sandbox (advantage/disadvantage, flat modifier, bonus dice)

### Crit Variants

- **ATTACK-V2-01**: Crit rule option: "max dice + roll dice" (for Champion Fighter / house rule)

---

## Out of Scope

| Feature | Reason |
|---------|--------|
| Character sheet / PC attribute lookups | Scope explosion toward a full VTT; would require session management, spell slots, proficiency tracking |
| Per-instance HP tracking | Each of "5 Goblins" becomes a separate stateful entity; UI complexity explodes without adding the core value |
| Token / grid map / line of sight | This is a VTT; explicitly out of scope per product premise |
| Online sync / cloud save | Product is offline-first; authentication and servers contradict the premise |
| Initiative tracker | A separate feature domain (turn order, delay, ready actions); not a dice roller concern |
| Full Roll20 template rendering (`&{template:...}`) | HTML rendering in an offline app with no browser; `@{attr}` attribute references require character sheets |
| Spellcasting modeling (slots, upcasting) | Spell math is combinatorial; only the damage roll expression matters, which the sandbox handles |
| Installer / auto-update | Portable .exe is the chosen distribution model |

---

## Traceability

Which phases cover which requirements. Confirmed during roadmap creation 2026-02-23.

| Requirement | Phase | Status |
|-------------|-------|--------|
| DICE-01 | Phase 1 | Complete |
| DICE-02 | Phase 1 | Complete |
| DICE-03 | Phase 1 | Complete |
| DICE-04 | Phase 1 | Complete |
| DICE-05 | Phase 1 | Complete |
| WS-01 | Phase 1 | Complete |
| IMPORT-01 | Phase 2 | Complete (02-01) |
| IMPORT-02 | Phase 2 | Complete |
| IMPORT-03 | Phase 2 | Complete (02-01) |
| IMPORT-04 | Phase 2 | Complete (02-01) |
| IMPORT-05 | Phase 2 | Complete |
| IMPORT-06 | Phase 2 | Complete (02-01) |
| IMPORT-07 | Phase 2 | Complete (02-01) |
| LIB-01 | Phase 2 | Complete |
| LIB-02 | Phase 2 | Complete |
| LIB-03 | Phase 2 | Complete |
| LIB-04 | Phase 2 | Complete |
| LIB-05 | Phase 2 | Complete |
| LIB-06 | Phase 2 | Complete |
| ATTACK-01 | Phase 3 | Complete |
| ATTACK-02 | Phase 3 | Complete |
| ATTACK-03 | Phase 3 | Complete |
| ATTACK-04 | Phase 3 | Complete |
| ATTACK-05 | Phase 3 | Complete |
| ATTACK-06 | Phase 3 | Complete |
| ATTACK-07 | Phase 3 | Complete |
| ATTACK-08 | Phase 3 | Complete |
| ATTACK-09 | Phase 3 | Complete |
| ATTACK-10 | Phase 3 | Complete |
| ATTACK-11 | Phase 3 | Complete |
| ATTACK-12 | Phase 3 | Complete |
| LIST-01 | Phase 4 | Complete |
| LIST-02 | Phase 4 | Complete |
| LIST-03 | Phase 4 | Complete |
| LIST-04 | Phase 4 | Complete |
| LIST-05 | Phase 4 | Complete |
| ENC-01 | Phase 4 | Complete |
| ENC-02 | Phase 4 | Complete |
| ENC-03 | Phase 4 | Pending |
| ENC-04 | Phase 4 | Pending |
| ENC-05 | Phase 4 | Pending |
| ENC-06 | Phase 4 | Pending |
| SAVE-01 | Phase 4 | Pending |
| SAVE-02 | Phase 4 | Pending |
| SAVE-03 | Phase 4 | Pending |
| SAVE-04 | Phase 4 | Pending |
| SAVE-05 | Phase 4 | Pending |
| SAVE-06 | Phase 4 | Pending |
| SAVE-07 | Phase 4 | Pending |
| SAND-01 | Phase 5 | Pending |
| SAND-02 | Phase 5 | Pending |
| SAND-03 | Phase 5 | Pending |
| SAND-04 | Phase 5 | Pending |
| SAND-05 | Phase 5 | Pending |
| SAND-06 | Phase 5 | Pending |
| SAND-07 | Phase 5 | Pending |
| SET-01 | Phase 6 | Pending |
| SET-02 | Phase 6 | Pending |
| SET-03 | Phase 6 | Pending |
| SET-04 | Phase 6 | Pending |
| WS-02 | Phase 7 | Pending |
| WS-03 | Phase 7 | Pending |

**Coverage:**
- v1 requirements: 56 total
- Mapped to phases: 56
- Unmapped: 0

---
*Requirements defined: 2026-02-23*
*Last updated: 2026-02-23 — traceability confirmed during roadmap creation*
