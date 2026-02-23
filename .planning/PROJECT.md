# RollinRollin

## What This Is

A standalone Windows 10 desktop application that emulates Roll20-style dice rolling for D&D 5e combat — specifically designed for bulk monster attack and saving throw management. Users import monster statblocks from Markdown files, build encounter groups, and execute mass dice rolls with full toggle-based rule controls (advantage, crit range, nat 1/20, bonus dice). No VTT, no internet required.

## Core Value

DMs can roll attacks and saving throws for groups of monsters in seconds, with full D&D 5e rule fidelity and clear hit/miss/damage breakdowns.

## Requirements

### Validated

(None yet — ship to validate)

### Active

- [ ] Monster statblock import from Markdown files (single and batch)
- [ ] Monster Library with search, filter by tag/incomplete status
- [ ] Lists: named collections of monsters with counts, save/load as Markdown
- [ ] Encounters: named groups with member counts and optional overrides, save/load as Markdown
- [ ] Dice engine: NdM expressions, operators, parentheses, seeded RNG
- [ ] Roll20-compatible macro sandbox (inline rolls, query rolls, /roll prefix, multi-line)
- [ ] Attack Roller: RAW mode (full breakdown per roll) and COMPARE mode (vs Target AC)
- [ ] Bulk Saving Throw Roller: per-participant d20+bonus vs DC, success/fail summary
- [ ] Toggle-based rule controls: advantage/disadvantage, nat 1/20, crit range, bonus dice, flat modifier
- [ ] Settings: RNG seed toggle, default toggles, default output mode, default AC/DC
- [ ] Packaged as Windows 10 .exe (standalone/portable, offline)

### Out of Scope

- VTT visuals (tokens, maps, line of sight) — not the goal
- Character sheet / token attribute lookups — standalone only
- Full Roll20 macro ecosystem (templates, API scripts, chat formatting) — partial Roll20 support only
- Spellcasting modeling — only attack rolls and saving throws
- Built-in monster database — user provides all data via Markdown import

## Context

- Target users: D&D 5e DMs who want fast bulk rolling without a full VTT
- Example monster format: Markdown statblocks with `## Monster Name`, `### Actions`, `+X to hit`, `Hit: N(XdY+Z) type damage` patterns (see `.claude/bestiary(1).md` for sample)
- Roll20 macro syntax reference: inline rolls `[[expr]]`, query rolls `?{prompt|option,value}`, `NdMkhN` keep-highest syntax
- Stack: Windows 10 desktop GUI app, packaged as .exe — likely Python (tkinter/PyQt) or Electron, or similar
- Workspace model: user selects a local folder; app manages `monsters/`, `lists/`, `encounters/`, `exports/` subfolders

## Constraints

- **Platform**: Windows 10, offline — no cloud, no VTT dependencies
- **Data format**: Markdown only for all import/export (no JSON/XML user-facing formats)
- **Scope**: Attack rolls and save rolls only — no spell slots, no condition tracking
- **Parsing**: Tolerant — missing fields produce "incomplete" flag, not import failure
- **Testing**: Dice engine must support seeded RNG for deterministic golden tests

## Key Decisions

| Decision | Rationale | Outcome |
|----------|-----------|---------||
| Markdown-only file format | User owns their data in readable files; no proprietary format lock-in | — Pending |
| Toggle-based rules (not macro syntax) | Simpler UX; Roll20 syntax complexity kept only in Sandbox | — Pending |
| Workspace folder model | Portable; user controls where files live | — Pending |

---
*Last updated: 2026-02-23 after initialization*
