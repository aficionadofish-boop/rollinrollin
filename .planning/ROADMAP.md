# Roadmap: RollinRollin

## Overview

Seven phases, innermost dependencies first. The Dice Engine and domain models are pure Python with zero UI dependencies — they ship first and are tested in isolation. The Statblock Parser and Monster Library unlock every feature that follows. The Attack Roller (primary daily use case) is built next, establishing the ToggleBar widget and Roll Service design that all subsequent rollers reuse. Lists, Encounters, and the Bulk Save Roller form a single data domain and ship together. The Roll20 Macro Sandbox is architecturally independent and builds on the already-proven engine. Settings and Polish close out the feature work. Packaging produces the portable Windows .exe that is the actual shipped product.

## Phases

**Phase Numbering:**
- Integer phases (1, 2, 3): Planned milestone work
- Decimal phases (2.1, 2.2): Urgent insertions (marked with INSERTED)

Decimal phases appear between their surrounding integers in numeric order.

- [x] **Phase 1: Dice Engine and Domain Foundation** - Pure-Python dice evaluator, seeded RNG, domain models, and workspace folder — the inner ring everything else imports (completed 2026-02-23)
- [x] **Phase 2: Monster Import and Library** - Tolerant Markdown statblock parser, in-memory monster library with search and filtering, workspace file I/O (completed 2026-02-23)
- [x] **Phase 3: Attack Roller** - Full Attack Roller tab with RAW/COMPARE modes, all 5e toggles, roll breakdown output, and copy-to-clipboard (completed 2026-02-24)
- [x] **Phase 4: Lists, Encounters, and Save Roller** - Named monster lists and encounters with Markdown save/load, bulk per-participant Save Roller drawing from the active encounter (completed 2026-02-24)
- [x] **Phase 5: Roll20 Macro Sandbox** - Free-text macro input resolving Roll20 inline rolls and query dialogs, multi-line support, unsupported-syntax warnings (completed 2026-02-24)
- [x] **Phase 6: Settings** - Settings tab: seed toggle, default toggles, default AC/DC, default output mode (completed 2026-02-24)
- [ ] **Phase 7: Packaging and Distribution** - Portable Windows 10 .exe via PyInstaller, build script, smoke-tested on clean machine

## Phase Details

### Phase 1: Dice Engine and Domain Foundation
**Goal**: The project's foundational layer is built and fully tested in isolation — correct dice evaluation with operator precedence, seeded RNG, and all domain data structures exist before any UI or parser work begins
**Depends on**: Nothing (first phase)
**Requirements**: DICE-01, DICE-02, DICE-03, DICE-04, DICE-05, WS-01
**Success Criteria** (what must be TRUE):
  1. A dice expression like `2d6+1d4*2` evaluates to the correct total with full per-die breakdown (operator precedence verified: multiply before add)
  2. With a fixed seed, rolling `3d6` twice produces the same sequence both times; with seed=None, successive rolls differ
  3. Keep-highest syntax `2d20kh1` returns only the higher die face in the result total, but both faces are stored in the breakdown
  4. Domain model objects (Monster, Action, DamagePart, List, Encounter) can be constructed and inspected without importing any Qt or I/O code
  5. User can select a workspace folder and the app creates the expected subfolder structure (monsters/, lists/, encounters/, exports/)
**Plans**: 2 plans

Plans:
- [ ] 01-01-PLAN.md — Dice engine (lexer, parser, roller, models) — TDD with golden tests
- [ ] 01-02-PLAN.md — Domain models (Monster, Action, DamagePart, MonsterList, Encounter) + WorkspaceManager

### Phase 2: Monster Import and Library
**Goal**: DMs can import monster statblocks from real-world Markdown files and immediately browse, search, and inspect the resulting library — the data foundation for every rolling feature
**Depends on**: Phase 1
**Requirements**: IMPORT-01, IMPORT-02, IMPORT-03, IMPORT-04, IMPORT-05, IMPORT-06, IMPORT-07, LIB-01, LIB-02, LIB-03, LIB-04, LIB-05, LIB-06
**Success Criteria** (what must be TRUE):
  1. User can import a single Markdown file containing multiple monster statblocks and see each monster appear in the library with correct name, AC, and HP
  2. User can batch-import an entire folder of Markdown files in one operation and see a summary showing successful count, incomplete count, and per-failure details
  3. A statblock with a missing field (e.g., no AC) still imports and displays an "incomplete" badge rather than failing silently or crashing
  4. An action whose damage pattern cannot be parsed appears in the monster detail view with its raw text and no roll button — it is not dropped
  5. User can type a partial monster name in the search field and the library list filters instantly to matching monsters
  6. Parser correctly extracts `+X to hit`, `Hit:` damage, multi-component damage (e.g., "plus N piercing damage"), and damage type labels from at least 3 distinct real-world Markdown format variants
**Plans**: 4 plans

Plans:
- [x] 02-01-PLAN.md — Domain model extensions + 5etools blockquote parser (TDD) — completed 2026-02-23
- [x] 02-02-PLAN.md — Homebrewery + plain-Markdown parsers + format dispatcher + ImportResult (TDD) — completed 2026-02-23
- [x] 02-03-PLAN.md — MonsterLibrary service + MonsterTableModel + MonsterFilterProxyModel — completed 2026-02-23
- [x] 02-04-PLAN.md — MonsterLibraryTab UI: splitter layout, import toolbar, search/filter/sort, detail panel, import log — completed 2026-02-24

### Phase 3: Attack Roller
**Goal**: DMs can select any imported monster action and roll any number of attacks with full 5e rule fidelity — hit/miss, damage breakdown, and all relevant toggles working correctly
**Depends on**: Phase 2
**Requirements**: ATTACK-01, ATTACK-02, ATTACK-03, ATTACK-04, ATTACK-05, ATTACK-06, ATTACK-07, ATTACK-08, ATTACK-09, ATTACK-10, ATTACK-11, ATTACK-12
**Success Criteria** (what must be TRUE):
  1. User can select a monster, select one of its actions, enter N=8, and receive 8 independent attack roll results each showing all d20 face(s), to-hit bonus, flat modifier, bonus dice results, and final total
  2. In COMPARE mode with a Target AC entered, each attack result shows "Hit" or "Miss" with margin; damage dice are only rolled for hits; a summary shows total hits, total misses, and total damage dealt
  3. With advantage enabled, both d20 faces are visible in the output and the higher value is used for the attack total
  4. Enabling the crit toggle with range 19 causes a roll of 19 to trigger double damage dice; a roll of 18 does not
  5. Adding a +1d4 bonus die entry causes each attack to include the d4 result in its total and breakdown
  6. The full roll output for any result can be copied to clipboard with a single click
**Plans**: 4 plans

Plans:
- [x] 03-01-PLAN.md — RollService + roll models (TDD): pure-Python 5e rule translation layer with seeded golden tests — completed 2026-02-24
- [x] 03-02-PLAN.md — ToggleBar + BonusDiceList reusable UI widgets — completed 2026-02-24
- [x] 03-03-PLAN.md — AttackRollerTab + RollOutputPanel: full rolling UI with RAW/COMPARE modes, action list, all toggles — completed 2026-02-24
- [x] 03-04-PLAN.md — MainWindow + cross-tab wiring + end-to-end human verification — completed 2026-02-24

### Phase 4: Lists, Encounters, and Save Roller
**Goal**: DMs can organize monsters into named encounters, save and reload them as Markdown files, and run bulk saving throw rolls against the active encounter's participants — single combined Encounters & Saves tab
**Depends on**: Phase 3
**Requirements**: LIST-01, LIST-02, LIST-03, LIST-04, LIST-05, ENC-01, ENC-02, ENC-03, ENC-04, ENC-05, ENC-06, SAVE-01, SAVE-02, SAVE-03, SAVE-04, SAVE-05, SAVE-06, SAVE-07
**Success Criteria** (what must be TRUE):
  1. User can create a named list of monsters with counts, save it to the workspace lists/ folder as a Markdown file, close the app, reopen it, load that file, and see the same list restored
  2. User can create a named encounter from library monsters, save it as Markdown, and load it back; any monster name that no longer exists in the library appears in an "Unresolved Entries" panel rather than being silently dropped
  3. User can load an encounter into the Save Roller, select CON save DC 15, click Roll, and see a per-participant result showing each monster's d20 face(s), save bonus, total, success/fail status, and margin vs DC
  4. The Save Roller summary shows the correct count of successes and failures across all participants
  5. With disadvantage enabled on saves, both d20 faces are shown per participant and the lower value is used
**Plans**: 4 plans

Plans:
- [x] 04-01-PLAN.md — Domain model patch (Encounter.members) + MonsterLibrary.get_by_name + encounter DTOs package — completed 2026-02-24
- [x] 04-02-PLAN.md — EncounterService (Markdown I/O) + SaveRollService (seeded save mechanics) — TDD — completed 2026-02-24
- [x] 04-03-PLAN.md — EncounterMemberList widget + drag-drop MonsterTableModel + EncountersTab + app.py wiring — completed 2026-02-24
- [x] 04-04-PLAN.md — End-to-end human verification checkpoint — completed 2026-02-24

### Phase 5: Roll20 Macro Sandbox
**Goal**: DMs with existing Roll20 macros can paste them into the Sandbox, resolve any query prompts, and get correct dice results — without needing Roll20 or an internet connection
**Depends on**: Phase 1
**Requirements**: SAND-01, SAND-02, SAND-03, SAND-04, SAND-05, SAND-06, SAND-07
**Success Criteria** (what must be TRUE):
  1. User can type `1d20+5+1d4` into the Sandbox, press Roll, and see the correct total plus a full per-die breakdown
  2. A macro containing `[[2d6+3]]` evaluates the inline expression and displays the numeric result in place of the bracket syntax
  3. A macro containing `?{Save type|STR,+2|DEX,+4}` shows a dialog prompting the user to choose, then substitutes the chosen value before evaluating
  4. A multi-line input with 3 non-empty lines produces 3 separate results displayed in order; a `/roll 1d20` prefix on any line is stripped without error
  5. A macro containing `@{target|ac}` emits a visible parse warning rather than crashing or silently producing a wrong result
**Plans**: 4 plans

Plans:
- [x] 05-01-PLAN.md — MacroPreprocessor + models + workspace update (TDD: /roll stripping, inline rolls, query extraction, unsupported token warnings) — completed 2026-02-24
- [x] 05-02-PLAN.md — MacroEditor (code-editor with line numbers, syntax highlighting, debounce) + QueryPanel (inline query resolution widget) — completed 2026-02-24
- [x] 05-03-PLAN.md — ResultPanel + MacroSidebar + MacroSandboxTab assembly + MainWindow wiring — completed 2026-02-24
- [x] 05-04-PLAN.md — End-to-end human verification checkpoint — completed 2026-02-24

### Phase 6: Settings
**Goal**: DMs can configure the app's default behaviors once and have every session start with the right toggles, AC, DC, and RNG mode pre-set
**Depends on**: Phase 5
**Requirements**: SET-01, SET-02, SET-03, SET-04
**Success Criteria** (what must be TRUE):
  1. User enables seeded RNG, enters seed 42, rolls any attack, restarts the session with the same seed, rolls again, and gets the identical sequence
  2. User sets crit range default to 19 and nat-1 always miss to off in Settings; opening the Attack Roller shows those toggles pre-set accordingly
  3. User sets default Target AC to 14 and default Save DC to 12; opening COMPARE mode and the Save Roller shows those values pre-filled
**Plans**: 2 plans

Plans:
- [ ] 06-01-PLAN.md — AppSettings model + SettingsService persistence layer (TDD)
- [ ] 06-02-PLAN.md — SettingsTab UI widget + MainWindow wiring + apply_defaults + seeded badge + unsaved-changes guard

### Phase 7: Packaging and Distribution
**Goal**: The complete app ships as a single portable Windows 10 .exe that runs offline on a machine with no Python installed
**Depends on**: Phase 6
**Requirements**: WS-02, WS-03
**Success Criteria** (what must be TRUE):
  1. Running the .exe on a clean Windows 10 machine (no Python, no PySide6 installed) opens the app fully with all tabs functional
  2. The app operates completely offline — no network requests are made and no internet connection is required at any point
  3. A build.bat script in the repo produces the .exe from source in a single command when run inside the correct venv
**Plans**: 2 plans

Plans:
- [ ] 07-01-PLAN.md — Build infrastructure: icon generation, version resource, PyInstaller spec, build.bat, smoke test
- [ ] 07-02-PLAN.md — Execute build, run smoke test, human verification of packaged .exe

## Progress

**Execution Order:**
Phases execute in numeric order: 1 → 2 → 3 → 4 → 5 → 6 → 7

| Phase | Plans Complete | Status | Completed |
|-------|----------------|--------|-----------|
| 1. Dice Engine and Domain Foundation | 2/2 | Complete   | 2026-02-23 |
| 2. Monster Import and Library | 4/4 | Complete   | 2026-02-24 |
| 3. Attack Roller | 4/4 | Complete   | 2026-02-24 |
| 4. Lists, Encounters, and Save Roller | 4/4 | Complete   | 2026-02-24 |
| 5. Roll20 Macro Sandbox | 4/4 | Complete   | 2026-02-24 |
| 6. Settings | 2/2 | Complete    | 2026-02-24 |
| 7. Packaging and Distribution | 0/2 | Not started | - |
