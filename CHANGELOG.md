# Changelog

## v2.0.0 — 2026-03-01

Major release. Complete rewrite of internals and UI from v1.0.1. Everything below is new or significantly reworked.

### Combat Tracker (new)
- Full initiative tracker with turn cycling, HP bars, and condition management
- HP bars use a 5-band color system (green/yellow/orange/red/dark red) with descriptive text overlay ("Healthy", "Bloodied", "Critical", etc.). This is basically the system from Baldur's Gate 1.
- Standard D&D conditions from a dropdown, plus custom conditions with duration tracking and auto-expiration
- Player character sub-tab for tracking PCs alongside monsters in the same initiative order
- Grouped monster handling (e.g., "3x Goblin") with per-member damage distribution
- Multi-select for AOE damage across multiple combatants
- Stats toggle menu to show/hide speed, passive perception, AC on combatant cards
- "Send to Saves" button to push selected combatants to the Save Roller
- Combat state persists across sessions

### Monster Editor (new)
- Full stat editing: ability scores, AC, HP, CR, size, speed
- Cascading math: changing ability scores auto-updates saves, skills, attack bonuses
- Skill proficiency and expertise toggles with color-coded indicators
- Traits section with name/description editing and rollable dice detection
- Actions section with to-hit, damage dice, damage type, and after-attack text editing
- Buff system: per-roll-type targeting (attacks, saves, ability checks, damage) with dice like Bless (+1d4)
- Equipment effects shown with color differentiation from base stats
- Save as new copy or override the base monster; modified monsters get a badge in the library

### Buff System (new)
- Attach buffs to individual monsters with granular targeting (attacks, saves, ability checks, damage)
- Buff dice auto-rolled and injected into attack and save roll output
- Buffs persist across sessions

### Save Roller (reworked)
- Per-creature feature detection: Magic Resistance, Legendary Resistance, Evasion auto-detected from stat blocks
- Legendary Resistance tracking with per-creature usage counters that persist across rolls
- Custom detection rules panel for user-defined auto-advantage triggers
- Sidebar checkbox selection to filter which creatures participate in a save roll
- Buff injection into save output

### Attack Roller (reworked)
- HTML output with color-coded damage types (piercing, fire, acid, etc.)
- Critical hit highlighting (gold background), natural 1 miss highlighting (red tint)
- Output header showing creature name, attack name, and count
- Damage type summary line with totals per damage type
- Rollable trait buttons for special abilities (dragon breath, recharge abilities, etc.)
- Buff dice shown in attack breakdowns
- RAW mode (individual rolls) and COMPARE mode (grouped by result)

### Encounter Sidebar (reworked)
- Always-visible collapsible sidebar shared across Library, Attack Roller, and Saves tabs
- Drag-resize with a styled handle: subtle gradient line that brightens on hover, disappears when collapsed
- Save encounters with timestamps and optional custom names
- Load saved encounters with inline name editing in the load dialog
- XP summary and creature count display
- Single-click to set active creature, double-click to jump to Attack Roller
- "View Stat Block" button to inspect a monster in the Library tab
- Sidebar width persists across sessions
- Collapsed state shows a narrow strip with rotated "Show" text

### Theming (new)
- Three preset themes: Dark, Default (Light), High Contrast
- Custom color override support (background, text, accent, input colors)
- Theme switching without restart
- Scoped splitter handle styling per theme

### Macro Sandbox (improved)
- Template card rendering for Roll20 `&{template:}` macros with accent-colored headers
- Configurable sandbox font independent of app theme

### Parser (improved)
- Trait extraction from stat blocks (passive features separate from actions)
- Speed parsing for all movement types
- Recharge ability detection with auto-roll mechanics
- `[[XdY]]` average notation rendering in stat block display
- Section boundary detection to prevent action text bleed between entries
- Legendary action and lair action field support

### Settings (expanded)
- Theme selection with preset dropdown and per-color pickers
- Sandbox font selector
- "Send to Saves" behavior toggle for Combat Tracker
- Individual data flush controls per persistence category

### Infrastructure
- Auto-save every 30 seconds across all persistence categories
- Window state persistence (sidebar width, tab selection, theme)
- 521 unit tests

---

## v1.0.1 — 2026-02-24

- Shared encounter list between Attack Roller and Saves tabs
- Grouped attacks by monster in Attack Roller
- Removed Great Weapon Master stub

## v1.0.0 — 2026-02-24

Initial release.

- Dice engine with full 5e roll syntax
- Monster library with import from 5etools, Homebrewery, and plain markdown
- Attack Roller with advantage, disadvantage, critical hits, bonus dice
- Save Roller with group saving throws against a target DC
- Macro Sandbox with Roll20 inline roll syntax, query prompts, variable substitution
- Settings with RNG seed, default advantage mode, target AC/DC
- Single-file EXE build via PyInstaller
