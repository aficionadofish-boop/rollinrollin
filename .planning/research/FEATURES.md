# Feature Research

**Domain:** D&D 5e combat manager desktop application (v2.0 milestone)
**Researched:** 2026-02-25
**Confidence:** HIGH (rules from official SRD), MEDIUM (UX patterns from competitive analysis)

---

## Scope

This file covers only the **new features** targeted for v2.0. Existing v1.0 features (Attack Roller, Library, Encounter Lists, Bulk Save Roller, Roll20 Macro Sandbox, Settings) are already shipped and are referenced here only when v2.0 features depend on or extend them.

---

## Feature Domain 1: Combat / Initiative Tracker

### What existing tools do

The dominant pattern across tools (Improved Initiative, DnD Metrics, Foundry CTG, donjon, DM Tools) is:

- A sorted list of combatants ordered by initiative (descending), tiebroken by dex modifier or DM preference
- Active combatant highlighted; advancing turn cycles through the list
- HP displayed as current/max; clicking applies damage or healing inline
- Conditions shown as icon badges or labeled chips on each combatant row
- Round counter increments when the last combatant in the list takes their turn

**Grouped vs individual initiative** is a genuine design fork:

- **Individual:** each monster gets its own row. Turn-by-turn granularity. Every Goblin has its own HP bar. Standard in Foundry default mode and Improved Initiative.
- **Grouped:** monsters of the same type share one initiative row; DM advances the whole group as one turn. Common for large identical groups (eight wolves, ten zombies). Foundry's Combat Tracker Groups module adds this. Roll20's GroupInitiative API script supports it. Better for table flow when there are many identical enemies.

The practical pattern for a DM tool: support both. Individual initiative is the default; grouped mode (same initiative, user collapses the group) reduces screen noise for monster swarms.

**Player characters in the tracker** are a near-universal expectation. DMs enter name + initiative roll manually (PCs roll their own dice at the table). PC HP is tracked or omitted — most tools leave PC HP to the player, showing only initiative position.

### Table Stakes (Users Expect These)

| Feature | Why Expected | Complexity | Notes |
|---------|--------------|------------|-------|
| Sorted combatant list with active highlight | Every tracker does this | LOW | Descending initiative, advance-turn button |
| HP bar per combatant (current/max) | Core combat loop | LOW | Click-to-edit or +/- buttons; allow negative HP or clamp at 0 |
| Round counter | DMs rely on it for spell durations | LOW | Increment at end of list |
| Manual initiative entry per combatant | Table-rolled initiative | LOW | Editable number field |
| Add/remove combatants mid-combat | Reinforcements, deaths | LOW | Death = mark defeated or remove row |
| Condition badges on each combatant | Visual state at a glance | MEDIUM | Name + round countdown (per PROJECT.md constraint) |
| Player Character entries (manual) | PCs are always in combat | LOW | Name + initiative only; HP optional |
| Import monsters from active encounter | Bridge from sidebar | MEDIUM | Pulls monster data, creates combatant rows |

### Differentiators

| Feature | Value Proposition | Complexity | Notes |
|---------|-------------------|------------|-------|
| Grouped initiative mode | Reduces row count for monster swarms (8 goblins = 1 row) | MEDIUM | Shared initiative + individual HP bars expand on click |
| One-click "Roll initiative for all" | Skips manual entry for all encounter monsters | LOW | Use existing dice engine; PCs still manual |
| Combat Tracker → Saves tab bridge | Select monsters in tracker, jump to Save Roller with them pre-loaded | MEDIUM | Passes participant list with HP/condition state |
| Defeated combatant display | Crossed-out or dimmed row stays visible for reference | LOW | Preserves who died and when |
| Temp HP field | Separate from max HP, absorbed first | LOW | Common rule, reduces DM mental load |

### Anti-Features

| Feature | Why Requested | Why Problematic | Alternative |
|---------|---------------|-----------------|-------------|
| Automatic turn-end condition countdown | Seems convenient | "End of whose turn?" is ambiguous (caster vs target); implementing correctly requires tracking condition source, not just a countdown | Decrement round counter manually; DM decides when condition expires |
| Concentration tracking with prompts | Feels like automation | Concentration ends on damage; requires integrating damage events with condition state — high coupling for low payoff | Condition named "Concentrating" with optional note; DM manages |
| Token/map integration | VTT-style spatial awareness | Explicitly out of scope in PROJECT.md; scope explosion | Not applicable |

---

## Feature Domain 2: Monster Stat Editor with Equipment Presets

### D&D 5e Rules Summary (HIGH confidence, SRD-verified)

**Magic weapons (+X):**
- Add +X to both attack roll and damage roll
- Maximum official bonus is +3
- Bonus is flat; applies to every attack action with that weapon

**Armor AC formulas (from 5e SRD):**

| Armor | AC | Stealth Disadvantage | Str Req |
|-------|----|----------------------|---------|
| Padded | 11 + full Dex | YES | — |
| Leather | 11 + full Dex | No | — |
| Studded Leather | 12 + full Dex | No | — |
| Hide | 12 + Dex (max +2) | No | — |
| Chain Shirt | 13 + Dex (max +2) | No | — |
| Scale Mail | 14 + Dex (max +2) | YES | — |
| Breastplate | 14 + Dex (max +2) | No | — |
| Half Plate | 15 + Dex (max +2) | YES | — |
| Ring Mail | 14 (no Dex) | YES | — |
| Chain Mail | 16 (no Dex) | YES | Str 13 |
| Splint | 17 (no Dex) | YES | Str 15 |
| Plate | 18 (no Dex) | YES | Str 15 |
| Shield | +2 to AC | No | — |
| Magic armor (+X) | base AC + X bonus | Inherits base | Inherits base |

**Weapon damage dice scaling by creature size (HIGH confidence, DMG-verified):**
- Medium: base weapon dice (1d8, 1d6, etc.)
- Large: double weapon dice
- Huge: triple weapon dice
- Gargantuan: quadruple weapon dice

**Casting foci (HIGH confidence, SRD-verified):**
Standard arcane focuses and holy symbols do NOT modify spell attack bonus or spell save DC. They only replace material components without gold cost. Magical versions (Rod of the Pact Keeper, Wand of the War Mage) do provide +X to spell attacks and save DCs. For RollinRollin's purposes, a "+X casting focus" preset is a custom/homebrew bonus that adds to the monster's spell attack bonus and/or save DC — this is not a core 5e rule but is a legitimate DM option and the user will know this.

### What existing tools do

Monstershuffler recalculates to-hit and damage automatically when proficiency or ability modifiers change. Falindrith's 5e Monster Maker computes CR and formats statblocks. The 5e Monster Maker (ebshimizu) auto-updates attack bonuses when stats change. None of the web tools offer equipment preset dropdowns specifically for "+X weapons" or armor swaps.

### Table Stakes (Users Expect These)

| Feature | Why Expected | Complexity | Notes |
|---------|--------------|------------|-------|
| Edit all core stat block fields | Basic editor expectation | MEDIUM | STR/DEX/CON/INT/WIS/CHA, HP, AC, speed, name, CR, type |
| Cascading recalculation on stat change | Changing STR 16→18 should update STR mod, attack bonus, damage | MEDIUM | Derived values: ability mod = floor((score-10)/2); attack bonus = mod + prof bonus |
| Save-as-copy vs overwrite vs discard | Edit workflow | LOW | Three explicit buttons; no silent auto-save |
| Weapon preset selector (+0 to +3) | Fast equip workflow | LOW | Dropdown; applies bonus to to-hit and damage for that weapon |
| Armor preset selector | Fast equip workflow | MEDIUM | Dropdown of all 14 types + magic bonus; auto-calculates AC formula |
| Shield toggle | Common equipment | LOW | +2 AC; flag for "wearing shield" |
| Stealth disadvantage auto-flag | Armor rule consequence | LOW | Derived from armor selection; display as note |
| Strength requirement check | Armor rule consequence | LOW | Compare monster STR score vs armor requirement; flag if not met |

### Differentiators

| Feature | Value Proposition | Complexity | Notes |
|---------|-------------------|------------|-------|
| Per-monster custom bonus (named modifier) | "Bless +1d4", "Rage +2", arbitrary DM effects | MEDIUM | Named bonus with die expression or flat value; persists across tabs |
| Weapon size scaling display | Auto-shows scaled dice (e.g. Large Ogre's greatclub = 2d8 not 1d8) | LOW | Read-only derived display; not user-entered |
| Casting focus preset (+X) | DM can model wand-of-the-war-mage equipped spellcasters | LOW | Applies +X to spell attack bonus and save DC; labeled as "magic focus bonus" |
| Diff view of modified vs imported baseline | Shows what changed from the original Markdown import | MEDIUM | Useful for DM reference; not required for function |

### Anti-Features

| Feature | Why Requested | Why Problematic | Alternative |
|---------|---------------|-----------------|-------------|
| Full CR recalculation on edit | Seems authoritative | CR is a complex formula (DMG offensive/defensive CR averaging); wrong values mislead DMs | Show offensive/defensive CR hints as guidance only, not locked values |
| Spell slot tracking in editor | Spellcasting monster has slots | Spell slots change in combat, not in the stat block; conflates prep-time and combat-time data | Combat tracker handles remaining resources; editor sets max values only |
| Equipment with specific named magic items | "+1 Sword of Wounding" etc. | Item database is enormous; out of scope | Free-text weapon name + numeric bonus covers the case |

---

## Feature Domain 3: Condition / Buff Tracking with Duration Countdowns

### What existing tools do

Consistent pattern across D&D tools (DnD Metrics, Foundry, Roll20, Improved Initiative):
- Conditions shown as labeled chips/badges on combatant rows
- Standard 5e conditions are a fixed list: Blinded, Charmed, Deafened, Exhaustion, Frightened, Grappled, Incapacitated, Invisible, Paralyzed, Petrified, Poisoned, Prone, Restrained, Stunned, Unconscious
- Buffs (non-standard conditions): usually free-text labels; some tools provide a template
- Duration: most tools express as "rounds remaining"; decrement manually or on turn end
- Linking condition countdown to initiative order is the advanced pattern — when the conditioned creature's turn ends, decrement by 1

### Table Stakes (Users Expect These)

| Feature | Why Expected | Complexity | Notes |
|---------|--------------|------------|-------|
| Add condition to combatant (from list) | Standard 5e conditions | LOW | Chip/badge on the row; single-click add |
| Free-text custom condition/buff | Non-standard effects (Bless, Rage, Web) | LOW | Label-only; no mechanical enforcement |
| Round countdown per condition | Duration management | LOW | Integer field; blank = permanent/manual |
| Remove condition | Conditions end | LOW | X button on badge |
| Visual indicator (color or icon) | At-a-glance state | LOW | Color per severity or type is nice-to-have |

### Differentiators

| Feature | Value Proposition | Complexity | Notes |
|---------|-------------------|------------|-------|
| Auto-decrement on turn advance | Reduces DM cognitive load | MEDIUM | Requires Combat Tracker turn events to fire condition logic |
| Condition note field | "Stunned until Meriel's turn" annotation | LOW | Tooltip or small text below badge |
| Multiple conditions per combatant | Common in play (Prone + Restrained) | LOW | List of badges, not single slot |

### Anti-Features

| Feature | Why Requested | Why Problematic | Alternative |
|---------|---------------|-----------------|-------------|
| End-of-turn save prompts for conditions | Paralyzed requires CON save each turn | Requires turn event hooks + save DC storage + rolling — high coupling | DM handles; note field documents "save DC 15 CON each turn" |
| Concentration prompts on damage | Automatic rule enforcement | Same coupling problem; damage source tracking needed | Condition named "Concentrating" + DM manages |
| Full condition rules text popup | Reference convenience | Large content payload; can be a tooltip or link | Note field for DM reminder |

---

## Feature Domain 4: Roll20 Template Card Rendering

### How the default template actually works (HIGH confidence, Roll20 Wiki-verified)

The `&{template:default}` syntax takes any number of `{{key=value}}` pairs. The **name** field becomes the card header. Every other key-value pair becomes a labeled row in a two-column table card. Values can be plain text or inline roll expressions (`[[1d20+5]]`).

**Syntax:**
```
&{template:default} {{name=Goblin Shortsword}} {{Attack=[[1d20+4]]}} {{Damage=[[1d6+2]] piercing}}
```

**Rendered card layout:**
```
┌─────────────────────────────┐
│     Goblin Shortsword        │  ← name field = header
├────────────┬────────────────┤
│ Attack     │ [roll result]  │
│ Damage     │ [roll result]  │
│ (any key)  │ (any value)    │
└────────────┴────────────────┘
```

The card is styled with Roll20's dark-red/parchment theme. In RollinRollin's sandbox, this must be emulated as a Qt widget with similar visual structure — a styled QFrame or QGroupBox with a header label and key/value rows.

**Fields the default template supports:**
- `name` — header text (special, styled differently)
- Any arbitrary key — becomes a labeled row
- Values can contain pre-evaluated inline roll results (the sandbox already resolves `[[expr]]`)

### What existing tools do

No standalone desktop tool emulates Roll20 template rendering to this level. The RollinRollin sandbox is already unique in supporting the macro syntax. Visual card output is a genuine differentiator.

### Table Stakes (Users Expect These, given the existing Macro Sandbox)

| Feature | Why Expected | Complexity | Notes |
|---------|--------------|------------|-------|
| Parse `&{template:default}{{...}}` syntax | Users expect the sandbox to handle it | MEDIUM | Regex extraction of `name` field and all `{{k=v}}` pairs |
| Render card with header + key/value rows | Visual fidelity to Roll20 output | MEDIUM | Qt styled widget; header = name, rows = other pairs |
| Inline roll values resolved before display | `[[1d20+5]]` must show the result, not the expression | LOW | Already implemented in sandbox; re-use |
| Graceful handling of missing name field | `&{template:default}{{attack=...}}` (no name) | LOW | Header shows blank or generic label |

### Differentiators

| Feature | Value Proposition | Complexity | Notes |
|---------|-------------------|------------|-------|
| Parchment/dark-red visual theme matching Roll20 | Familiar to existing Roll20 users | LOW | CSS-equivalent styling on the QFrame; color tokens in theme system |
| Copy-to-clipboard as plain text | Share result via Discord/chat | LOW | Format: "Name: X, Attack: Y, Damage: Z" |
| Multi-template in one macro | Multiple `&{template:default}` blocks in one macro | MEDIUM | Parse all blocks; render each as a card in sequence |

### Anti-Features

| Feature | Why Requested | Why Problematic | Alternative |
|---------|---------------|-----------------|-------------|
| Custom template support (`&{template:mytemplate}`) | Full Roll20 parity | Custom templates require HTML/CSS authoring — far beyond scope | Render as default card regardless of template name; warn user |
| Live Roll20 API connection | Real Roll20 integration | Internet dependency; breaks offline-first constraint | Sandbox is local-only by design |

---

## Feature Domain 5: Save Roller with Feature Detection

### D&D 5e Feature Text (HIGH confidence, SRD-verified)

**Magic Resistance** (exact 2024 SRD wording):
> "The creature has Advantage on saving throws against spells and other magical effects."

Older (2014) wording:
> "The creature has advantage on Saving Throws against Spells and other magical effects."

**Legendary Resistance** (exact SRD wording):
> "If the creature fails a saving throw, it can choose to succeed instead." (with uses per day, e.g., "3/Day")

Both are in the **Traits** or **Special Traits** section of a statblock. In RollinRollin's Markdown format, these appear under the monster's top-level prose section (before `### Actions`).

**Immunity:** appears in the "Damage Immunities" and "Condition Immunities" lines. e.g., `Condition Immunities: frightened, poisoned`.

### What existing tools do

Most save rollers (RandomTools, D&D Beyond) require the user to manually toggle advantage. Auto-detection from text parsing is not a standard feature anywhere in the ecosystem. This is a genuine differentiator for RollinRollin.

### Pattern matching approach (MEDIUM confidence — inferred from PROJECT.md constraints)

Because RollinRollin already parses Markdown statblocks with tolerant keyword matching, extending the parser to detect these known phrases is a natural fit:

- Magic Resistance: match `magic resistance` (case-insensitive) in traits section
- Legendary Resistance: match `legendary resistance` (case-insensitive); also capture the uses per day with `(\d+)/[Dd]ay`
- Condition Immunities: parse `Condition Immunities:` line, split by comma
- Damage Immunities: parse `Damage Immunities:` line, split by comma

### Table Stakes (Users Expect These)

| Feature | Why Expected | Complexity | Notes |
|---------|--------------|------------|-------|
| Subset creature selection from encounter | Rolling saves for one creature, not all | LOW | Checkbox list from the encounter sidebar |
| Manual advantage toggle per creature | Override for any reason | LOW | Already exists in v1.0 as global toggle; needs per-row |
| Legendary Resistance toggle (uses remaining) | DM tracks when LR is spent | LOW | Checkbox or counter per creature; when active, success regardless of roll |
| Display save type label per row | "CON save DC 15" clarity | LOW | Label column in the bulk save table |

### Differentiators

| Feature | Value Proposition | Complexity | Notes |
|---------|-------------------|------------|-------|
| Auto-detect Magic Resistance from parsed traits | Advantage checkbox auto-checked for eligible monsters | MEDIUM | Keyword match on `magic resistance` in trait text; checkbox is toggleable override |
| Auto-detect Legendary Resistance (count) | Counter pre-populated from trait text | MEDIUM | Parse `N/Day` from trait text; DM can adjust |
| Auto-detect condition/damage immunity | Warn DM if the save being rolled is immune | MEDIUM | Cross-reference save type against condition immunity list |
| Feature detection summary column | Small icon/label showing which features were auto-detected | LOW | Transparency; DM can confirm/override |

### Anti-Features

| Feature | Why Requested | Why Problematic | Alternative |
|---------|---------------|-----------------|-------------|
| NLP trait parsing for other features | "Detect all advantage-granting traits" | Unbounded scope; brittleness; Gnome's Gnomish Cunning, Halfling Luck, Dwarven Resilience all grant advantage on specific saves | Keyword match only for the three documented patterns; DM sets others manually |
| Automatic spell-vs-non-spell tracking | Apply Magic Resistance only to spell saves | Requires knowing whether the current save is from a spell — needs save context that the user provides | Toggle labeled "Spell Save" that gates Magic Resistance auto-advantage |

---

## Feature Domain 6: Persistent Encounter Sidebar

### What existing tools do

Foundry VTT and 5etools DM screen both use persistent sidebars that remain visible across tabs. The dominant pattern is a collapsible panel anchored to one side of the application window. Content in the sidebar shows the active encounter with member counts, HP, and quick-action buttons.

The RollinRollin-specific version replaces the current per-tab encounter management. In v1.0, the encounter is context-specific to each tab. In v2.0, one sidebar serves Library, Attack Roller, and Saves tabs.

### Table Stakes (Users Expect These)

| Feature | Why Expected | Complexity | Notes |
|---------|--------------|------------|-------|
| Sidebar visible across Library, Attack, Saves tabs | Core premise of the feature | MEDIUM | Qt dockable widget or permanent QWidget in main layout |
| Active encounter displayed with combatant list | DM needs to see who is in the encounter | LOW | Name, count, HP summary |
| Add/remove monsters from encounter in sidebar | Quick prep | LOW | Drag from library or +/- buttons |
| Encounter persists between tab switches | State not lost on navigation | LOW | Single data model, not per-tab state |
| Send to Combat Tracker button | Bridge to tracker tab | LOW | Passes encounter data to tracker |
| Send to Save Roller button | Bridge to saves tab | LOW | Passes selected subset to saves |

### Differentiators

| Feature | Value Proposition | Complexity | Notes |
|---------|-------------------|------------|-------|
| Collapse/expand sidebar | Screen space management | LOW | Toggle button; remembers state in settings |
| HP summary in sidebar (encounter-level totals) | Quick reference | LOW | Sum of current/max HP across encounter |
| Sidebar "quick save" for current encounter | One-click save to workspace | LOW | Appends to workspace encounters folder as Markdown |

### Anti-Features

| Feature | Why Requested | Why Problematic | Alternative |
|---------|---------------|-----------------|-------------|
| Multiple active encounters simultaneously | Complex campaigns | Requires encounter tabs or a switcher; significant UI complexity | One active encounter in sidebar; save/load to switch |
| Sync sidebar with Combat Tracker HP in real time | Live HP mirroring | Bidirectional state sync is fragile; sidebar and tracker serve different purposes | Tracker is the HP authority during combat; sidebar is prep-time view |

---

## Feature Dependencies

```
[Data Persistence (JSON store)]
    └──required by──> [Combat Tracker — HP state survives tab switches]
    └──required by──> [Monster Editor — modified stats persist]
    └──required by──> [Persistent Sidebar — active encounter persists]
    └──required by──> [Condition Tracking — condition state per combatant]

[Monster Editor]
    └──required by──> [Equipment Presets — editing context]
    └──enhances──> [Combat Tracker — edited HP/AC used in tracker]

[Persistent Encounter Sidebar]
    └──required by──> [Combat Tracker → Saves Bridge — sidebar is the source]
    └──required by──> [Save Roller Subset Selection — sidebar provides participant list]

[Combatant List (tracker)]
    └──required by──> [Condition/Buff Tracking — conditions are per-combatant]
    └──required by──> [Combat → Saves Bridge — selects from combatant list]

[Monster Markdown Parser (existing v1.0)]
    └──extended by──> [Feature Detection (Magic Resistance, Legendary Resistance)]

[Macro Sandbox (existing v1.0)]
    └──extended by──> [Roll20 Template Card Rendering]

[Save Roller (existing v1.0)]
    └──extended by──> [Feature Detection (auto-advantage)]
    └──extended by──> [Subset Creature Selection]
```

### Dependency Notes

- **Data persistence is the foundation:** Monster Editor, Combat Tracker, and Persistent Sidebar all require a persistent store. This must be built first in the milestone.
- **Persistent Sidebar must exist before bridges:** The Combat Tracker → Saves bridge and Saves subset selection both assume the sidebar owns the active encounter participant list.
- **Monster Editor requires the editor UI before equipment presets:** Equipment preset dropdowns are UI elements within the editor; the base editing form must exist first.
- **Feature detection is a parser extension:** It extends the existing Markdown parser from v1.0. No new architectural layer needed — it is an additional extraction step during import and a re-scan when the editor updates trait text.
- **Roll20 template rendering is a sandbox extension:** The sandbox already resolves inline rolls. Template rendering is a new output formatter on top of the existing resolved result.

---

## MVP Definition for v2.0

### Launch With (v2.0 core)

These features deliver the "combat loop" value proposition from PROJECT.md and are directly dependent on each other.

- [ ] Data persistence (JSON store) — all other v2.0 features depend on it
- [ ] Monster Editor (core fields, cascading recalculation) — required for equipment presets
- [ ] Equipment presets: +X weapon, armor by type, shield toggle — primary editor value
- [ ] Persistent Encounter Sidebar — connects Library, Attack, Saves
- [ ] Combat Tracker: combatant list, HP, initiative, turn cycling, round counter
- [ ] Condition tracking with round countdown on combatant rows
- [ ] Save Roller: subset selection from sidebar encounter
- [ ] Save Roller: Magic Resistance and Legendary Resistance auto-detection

### Add After Core Is Working (v2.0 polish)

- [ ] Roll20 template card rendering — sandbox extension; non-blocking
- [ ] Theming (color pairs, high contrast, font selection) — usability polish
- [ ] Color-coded attack output (damage types, crits) — output polish
- [ ] Grouped initiative mode — combat tracker enhancement
- [ ] PC subtab in Combat Tracker — expansion once monsters work
- [ ] Combat Tracker → Saves bridge — convenience once both features work

### Defer to v2.1+

- [ ] Diff view (modified vs imported baseline) — niche, not blocking any workflow
- [ ] Multi-template rendering in a single macro — edge case
- [ ] Auto-decrement conditions on turn advance — low priority given PROJECT.md scoping of conditions to "name + countdown only"

---

## Feature Prioritization Matrix

| Feature | User Value | Implementation Cost | Priority |
|---------|------------|---------------------|----------|
| Data persistence (JSON store) | HIGH | MEDIUM | P1 |
| Monster Editor + recalculation | HIGH | MEDIUM | P1 |
| Equipment presets (+X weapon, armor, shield) | HIGH | LOW | P1 |
| Persistent Encounter Sidebar | HIGH | MEDIUM | P1 |
| Combat Tracker (HP, initiative, turn cycle) | HIGH | MEDIUM | P1 |
| Condition tracking per combatant | HIGH | LOW | P1 |
| Save Roller subset selection | HIGH | LOW | P1 |
| Feature detection (Magic/Legendary Resistance) | HIGH | LOW | P1 |
| Roll20 template card rendering | MEDIUM | MEDIUM | P2 |
| Theming (color pairs, high contrast) | MEDIUM | MEDIUM | P2 |
| Color-coded attack output | MEDIUM | LOW | P2 |
| Grouped initiative mode | MEDIUM | MEDIUM | P2 |
| PC subtab in Combat Tracker | MEDIUM | LOW | P2 |
| Combat Tracker → Saves bridge | MEDIUM | LOW | P2 |
| Casting focus preset (+X) | LOW | LOW | P2 |
| Temp HP field | LOW | LOW | P2 |
| Defeated combatant display (dimmed) | LOW | LOW | P3 |
| Sidebar HP totals | LOW | LOW | P3 |
| Diff view (modified vs baseline) | LOW | HIGH | P3 |

**Priority key:**
- P1: Must have for v2.0 launch
- P2: Should have; add when core is working
- P3: Nice to have; future consideration

---

## Competitor Feature Analysis

| Feature | Improved Initiative | Foundry VTT (default) | DnD Metrics | RollinRollin v2.0 Approach |
|---------|--------------------|-----------------------|-------------|---------------------------|
| Combat tracker | Yes, minimal | Yes, full-featured | Yes, web-based | Desktop Qt widget, sidebar-integrated |
| Grouped initiative | No | Via module (CTG) | No | Supported (collapsed rows) |
| Monster editor | Stat tweak only | Full sheet editor | No | Full editor with equipment presets |
| Equipment presets | No | Via system sheets | No | Explicit +X weapon/armor/shield dropdowns |
| Condition tracking | Name only | Icon + duration | Name + rounds | Name + round countdown (PROJECT.md scope) |
| Save roller | No dedicated tool | Via macros | No | Existing v1.0 + subset + feature detection |
| Feature auto-detection | No | No | No | YES — Magic/Legendary Resistance from parsed text |
| Roll20 template rendering | No | No | No | YES — existing sandbox extended |
| Persistent sidebar | No | Permanent tracker panel | No | YES — unified sidebar across tabs |
| Offline desktop | No (browser) | Electron (online-optional) | No (web) | YES — standalone .exe |

RollinRollin's advantages are: offline Windows .exe, feature auto-detection from Markdown text, equipment presets with correct 5e AC math, and Roll20 template rendering in a desktop sandbox.

---

## Sources

- D&D 5e SRD armor table: [5thsrd.org/adventuring/equipment/armor/](https://5thsrd.org/adventuring/equipment/armor/)
- Magic Resistance / Legendary Resistance wording: [5esrd.com/database/feats/magic-resistance/](https://www.5esrd.com/database/feats/magic-resistance/) and [5esrd.com/database/feats/legendary-resistance/](https://www.5esrd.com/database/feats/legendary-resistance/)
- Weapon damage dice by size: [Roll20 Compendium — Monsters](https://roll20.net/compendium/dnd5e/Monsters)
- Arcane focus rules: [arcaneeye.com/mechanic-overview/spellcasting-focus-5e/](https://arcaneeye.com/mechanic-overview/spellcasting-focus-5e/)
- Roll20 default template syntax: [wiki.roll20.net/Roll_Templates/Default](https://wiki.roll20.net/Roll_Templates/Default)
- Foundry VTT grouped initiative: [foundryvtt.com/packages/ctg](https://foundryvtt.com/packages/ctg)
- Improved Initiative (competitive reference): [improvedinitiative.app](https://improvedinitiative.app/)
- Condition tracking design: [dndmetrics.com/tracker](https://dndmetrics.com/tracker)
- Monster editor competitive analysis: [monstershuffler.com](https://www.monstershuffler.com/), [ebshimizu/5e-monster-maker](https://github.com/ebshimizu/5e-monster-maker)

---

*Feature research for: RollinRollin v2.0 Combat Manager*
*Researched: 2026-02-25*
