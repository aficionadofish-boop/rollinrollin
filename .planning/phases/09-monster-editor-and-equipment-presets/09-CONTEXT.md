# Phase 9: Monster Editor and Equipment Presets - Context

**Gathered:** 2026-02-25
**Status:** Ready for planning

<domain>
## Phase Boundary

DMs can open any monster in an editor, tweak any stat or add equipment, see all dependent values recalculate live, and save the result — either as an override of the base monster or as a named copy — with overrides persisting across sessions. Custom named bonuses (Bless, Rage, etc.) persist across tabs.

</domain>

<decisions>
## Implementation Decisions

### Editor Layout and Access
- **Trigger:** Explicit "Edit" button in the monster details pane (no double-click shortcut)
- **Dialog type:** Modal overlay, near-fullscreen (~90%+ of window)
- **Layout:** Two-column — left column has editable fields, right column shows live statblock preview
- **Preview style:** Same format as the existing Library statblock display, updating in real-time
- **Edit fields:** Collapsible sections (Ability Scores, Saving Throws, Skills, HP, Actions, Equipment, Buffs)
- **Ability scores:** Classic 6-across grid (STR DEX CON INT WIS CHA) with spinner/number inputs
- **Actions:** Structured fields (separate name, to-hit, damage dice, damage bonus, damage type) — not inline text
- **Saving throws:** Toggle proficiency/expertise by default, with option to override with a custom number (flagged as "custom")
- **Skills:** Same toggle + override pattern as saving throws
- **HP editing:** Can edit both hit dice formula (e.g. 7d8+14) and/or flat max HP number
- **HP scope:** Max HP only — current HP is a combat tracker concern (Phase 11)
- **Toolbar:** Top toolbar with Save (dropdown), Discard, Undo actions
- **Undo:** Undo button reverts the last action (no separate "Reset to Base" — Discard already handles full reset)
- **Dialog title:** Live title showing "Editing: [Monster Name]" — updates if DM renames the monster
- **Monster name:** Editable text field at top of edit column — DM can rename freely

### Equipment Preset Flow
- **Location:** Own collapsible section in the editor, separate from Actions
- **Summary header:** Collapsed section shows one-line summary of equipped items (e.g. "Longsword +2, Plate Armor, Shield +1")
- **Weapon selection:** Pick from a list of SRD weapons; selecting one expands to show magic bonus options (+0 nonmagical, +1, +2, +3)
- **Armor selection:** Same pattern as weapons — pick from SRD armor list, expands to +0/+1/+2/+3
- **Shield selection:** Same pattern — select Shield, then +0/+1/+2/+3
- **Spellcasting focus:** Single item type "Spellcasting Focus" at +1/+2/+3 only (no +0, no type distinctions between Rod/Vial/Sickle/Grimoire)
- **Multiple weapons:** Yes — a monster can have multiple weapons equipped simultaneously
- **Auto-generated actions:** Equipping a weapon auto-creates a corresponding action entry with calculated to-hit and damage
- **Conflict handling:** If equipping a weapon that matches an existing action (e.g. monster already has "Scimitar"), prompt the DM: "Replace existing action or add as new?"
- **Removal:** Removing a weapon from equipment automatically removes its auto-generated action (no prompt)

### Custom Bonuses (Buffs Section)
- **Location:** Own collapsible "Buffs" section, separate from Equipment
- **Structure:** Name + bonus value + targeting (what it applies to: attack rolls, saving throws, etc.)
- **Persistence:** Custom bonuses persist across tabs (Library, Attack, Saves)

### Live Recalculation Display
- **Change highlighting:** Persistent color highlighting on modified values until saved — not a brief flash
- **Color distinction:** Three distinct colors for modification sources:
  - One color for equipment-modified values
  - One color for manually-edited values
  - One color for custom overrides (values that don't match proficiency math)
- **Base value display:** Tooltip only — hover over a modified value to see the original base value. Keeps statblock clean.

### Save and Copy Workflow
- **Save button:** Dropdown on the Save button with options: "Save (override base)" and "Save as Copy..."
- **Save as copy:** Opens a name dialog with an empty field — DM must provide a meaningful name (no auto-suggested names)
- **Edited badge:** Small icon badge next to modified monster names in the library list
- **Unsaved changes:** Confirm dialog on close attempt: "You have unsaved changes. Save / Discard / Cancel"

### Claude's Discretion
- Exact color choices for the three modification highlight tiers
- Collapsible section ordering and default expanded/collapsed state
- Specific icon for the "edited" badge
- Exact tooltip formatting for base values
- Animation/transition details for collapsing/expanding sections
- Internal layout spacing and typography within the editor

</decisions>

<specifics>
## Specific Ideas

- Equipment section collapsed header should show a quick summary line of what's equipped
- Weapon selection UX: list of items that expand into magic bonus tiers when selected (not separate dropdown + spinner)
- Spellcasting focus is deliberately simplified — no distinction between Rod of the Pact Keeper, Bloodwell Vial, Moon Sickle, Arcane Grimoire; just "Spellcasting Focus +X"
- The "custom" flag for saves/skills that don't match proficiency math should be visually distinct (third color) so DMs know at a glance what was manually overridden vs rules-derived

</specifics>

<deferred>
## Deferred Ideas

None — discussion stayed within phase scope

</deferred>

---

*Phase: 09-monster-editor-and-equipment-presets*
*Context gathered: 2026-02-25*
