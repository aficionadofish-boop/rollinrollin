# RollinRollin

A D&D 5e dice roller desktop app for DMs. Paste or import monster stat blocks, then roll attacks and saves without leaving your screen.

## Features

**Monster Library** — Import monsters by pasting stat blocks (5etools, Homebrewery, or plain text). Drag-and-drop from the library into your encounter list.

**Attack Roller** — All creatures in your encounter have their attacks listed and grouped by monster. Pick an attack, set the number of dice, and roll. Supports advantage, disadvantage, critical hits, and custom bonus dice.

**Encounters & Save Roller** — Build an encounter list with multiple creatures and counts. Roll saving throws for groups of monsters at once against a target DC.

**Macro Sandbox** — Write and execute Roll20-style dice macros with query prompts, inline rolls, and variable substitution. Save macros for reuse.

**Settings** — Configure dice roller seed, default advantage mode, and other preferences. Settings persist across sessions.

## Download

Grab `RollinRollin.exe` from the [Releases](../../releases) page — single portable executable, no install required.

A sample bestiary file (`bestiary.md`) is included in the release if you want something to test with right away.

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
