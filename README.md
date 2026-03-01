# RollinRollin

A D&D 5e dice roller desktop app for DMs. Import monster stat blocks, then roll attacks and saves, track combat with initiative and HP, or just view the statblock and lore. Also has a built-in Roll20-esque macro field which should run just about any macro you take from Roll20 (though obviously things that point to tokens, other macros, or character sheets won't work). The idea is that it's pretty lightweight and any old piece of junk with Windows should be able to run it, and it's helpful to DMs who plan to run encounters with a multitude of monsters in an IRL game, or a game with theater of the mind.

## Features

**Monster Library** — Import monster statblocks from markdown files (5etools, Homebrewery, or plain text). Search, filter by creature type, and view full statblocks with traits, actions, and lore. Drag-and-drop from the library into your encounter list. Edit any monster with the built-in editor, or create your own from scratch.

**Monster Editor** — Full stat editing with cascading math (change an ability score and saves/skills/attack bonuses update automatically). Add traits, actions, buffs, skill proficiencies with expertise, and equipment. Save as a new copy or override the original. Modified monsters get a badge in the library so you can tell them apart.

**Attack Roller** — All creatures in your encounter have their attacks listed and grouped by monster. Pick an attack, set the number of dice, and roll. Has advantage, disadvantage, critical hits, and bonus dice. Output is color-coded by damage type (piercing, fire, acid, etc.) with gold crit highlights and a damage summary line. Rollable trait buttons for things like dragon breath and recharge abilities. Buffs (like Bless) auto-inject into rolls.

**Combat Tracker** — Initiative tracker with turn cycling, HP bars, and condition management. HP bars show a 5-band color system with labels like "Healthy", "Bloodied", and "Critical" (inspired by Baldur's Gate 1). Standard D&D conditions from a dropdown plus custom conditions with duration tracking. Handles grouped monsters (e.g., "3x Goblin") with per-member damage. Multi-select for AOE. Player character sub-tab so you can track PCs in the same initiative order. Send selected combatants to the Save Roller with one click.

**Encounters & Save Roller** — Build an encounter list with multiple creatures and counts. Roll saving throws for groups of monsters against a target DC. Auto-detects Magic Resistance, Legendary Resistance, and Evasion from stat blocks. Tracks Legendary Resistance uses per creature. Custom detection rules if you want auto-advantage for homebrew features. Buffs inject into save rolls too.

**Encounter Sidebar** — Always-visible collapsible sidebar shared across tabs. Save and load named encounters. Shows XP summary and creature count. Single-click to select a creature, double-click to jump to the Attack Roller. Drag-resize with a styled handle that disappears when collapsed.

**Macro Sandbox** — Write and execute Roll20-style dice macros with query prompts, inline rolls, and other basic macro stuff. Supports `&{template:}` card rendering with styled output. Save and load macros, give them silly names. Configurable font independent of app theme.

**Theming** — Three preset themes: Dark, Default (Light), and High Contrast. Custom color overrides if you want to pick your own background, text, accent, and input colors. Switches instantly.

**Settings** — RNG seeding, default combat toggles (crit range, nat 1/nat 20 rules, advantage mode), default AC/DC, theme selection, sandbox font, and individual data flush controls for each persistence category.

**Auto-Save** — Everything persists: loaded monsters, modified monsters, encounters, combat state, player characters, macros, sidebar width, and window state. Auto-saves every 30 seconds.

## Download

Grab `RollinRollin.exe` from the [Releases](../../releases) page.

A sample bestiary file (`bestiary.md`) is included for you to test the program with.

## Usage

1. Launch `RollinRollin.exe`
2. Go to the **Library** tab and paste a monster stat block (or import a markdown bestiary file)
3. Drag creatures from the library into the encounter sidebar
4. Switch to the **Attack Roller** tab to see grouped attacks and start rolling
5. Use the **Encounters & Saves** tab to roll saving throws for groups of creatures
6. Use the **Combat Tracker** tab to run full initiative-tracked encounters with HP and conditions

## Building from Source

Requires Python 3.10+ and PySide6.

```
pip install -r requirements-dev.txt
python src/main.py
```

To build the standalone EXE:

```
build.bat
```

Output: `dist/RollinRollin.exe`
