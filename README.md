# RollinRollin

A D&D 5e dice roller desktop app for DMs. Import monster stat blocks, then roll attacks and saves, or simply view the statblock and lore for it. Also has a built in roll20-esque macro field which should run just about any macro that you take from roll20, though obviously things that point to tokens, other macros or character sheets won't work. Idea is that its pretty lightweight and any old piece of junk with windows should be able to run it, and it is helpful to DMs who plan to run encounters with a multitude of monsters in an IRL game, or a game with theater of the mind.  

## Features

**Monster Library:** Import monster statblocks in markdown files (5etools, Homebrewery, or plain text (maybe)). Drag-and-drop from the library into your encounter list. Encounter list is shared between attack roller and save roller, and can be edited in save roller.

**Attack Roller:** All creatures in your encounter have their attacks listed and grouped by monster. Pick an attack, set the number of dice, and roll. Has advantage, disadvantage, critical hits, and custom bonus dice. Also has some homebrew rules for critical hits, more coming in the future (soon^tm)

**Encounters & Save Roller:** Build an encounter list with multiple creatures and counts. Roll saving throws for groups of monsters at once against a target DC. Also has bonus dice and modifiers. Yet to add detection for magic resistance, legendary resistance or magic immunity, so you gotta figure those out by yourself, but otherwise fully functional.

**Macro Sandbox:** Write and execute Roll20-style dice macros with query prompts, inline rolls and other basic macro stuff. You can save and load them as well, give them silly names and whatnot. It isn't quite as smart as roll20, but if you can write a macro, you can also interpret the output easily.

**Settings:** Just settings for default values.

## Download

Grab `RollinRollin.exe` from the [Releases](../../releases) page.

A sample bestiary file (`bestiary.md`) is included for you to test the program with.

## Usage

1. Launch `RollinRollin.exe`
2. Go to the **Library** tab and paste a monster stat block (or import a markdown bestiary file)
3. Drag creatures from the library into the encounter drop zone
4. Switch to the **Attack Roller** tab to see grouped attacks and start rolling
5. Use the **Encounters & Saves** tab to roll saving throws for groups of creatures

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
