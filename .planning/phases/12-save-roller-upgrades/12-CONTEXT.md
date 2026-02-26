# Phase 12: Save Roller Upgrades - Context

**Gathered:** 2026-02-26
**Status:** Ready for planning

<domain>
## Phase Boundary

Enhance the existing Save Roller with per-creature selection from the sidebar encounter, automatic trait detection (Magic Resistance, Legendary Resistance) from parsed monster traits, per-creature feature detection summary in results, and a customizable detection filter list. The Combat-to-Saves bridge (COMBAT-14) is already implemented; this phase adds subset selection and smart trait handling on top of it.

</domain>

<decisions>
## Implementation Decisions

### Creature Selection UI
- Selection happens via checkboxes directly on the sidebar encounter creatures — not a separate list in the Saves tab
- Quick-select shortcuts: Select All, Select None, and Invert Selection buttons on the sidebar
- Grouped creatures (e.g., 4x Goblin) toggle as a group by default; group can be expanded to toggle individuals
- Combat Tracker "Send to Saves" behavior is configurable in Settings: either CT selection overrides the sidebar encounter (default), or only sidebar creatures are considered for rolling
- When CT overrides, the sent creatures replace whatever was checked in the sidebar

### Feature Detection Display
- Dedicated "Features" column in the save results table showing plain text labels per creature (e.g., "MR (auto)", "LR 2/3")
- No color-coded badges — plain text consistent with current output style
- Feature summary appears only after rolling (in the results), not as a preview panel before rolling
- No distinction between auto-detected advantage and manual global advantage in the output — if advantage is on, it's on

### Legendary Resistance Tracking
- When a creature with LR fails a save, the entire result row is colored red to make it visually obvious
- Row text includes: "This creature has LR remaining (X/Y). Use?" with a clickable action to spend one
- When DM clicks "Use", the result flips from FAIL to PASS, the row recolors from red to green, and the LR counter decrements
- LR counter persists across multiple save rolls within the same encounter (not reset per roll)
- DM can click the LR counter directly to manually increment/decrement (for undo or correction)

### Custom Filter Editor
- Collapsible "Detection Rules" panel within the Saves tab itself — close to where it's used
- Four assignable behaviors: auto-advantage, auto-disadvantage, auto-fail, auto-pass
- Built-in rules: Magic Resistance → auto-advantage (when "Is save magical?" is on), Legendary Resistance → reminder
- Custom triggers use substring matching (e.g., "Evasion" matches "Improved Evasion", "Evasion (fire only)")
- Custom rules persist to disk via the persistence service — survive app restarts

### Claude's Discretion
- Exact UI layout of the Detection Rules panel (add/edit/delete flow)
- How the "Is save magical?" toggle interacts with the detection rules internally
- Keyword matching implementation for trait detection
- How to parse "Legendary Resistance (X/Day)" for the uses count

</decisions>

<specifics>
## Specific Ideas

- LR failed-save rows should be unmistakably red — the DM needs to notice instantly when a creature with LR fails
- Flipping from FAIL to PASS (red to green) when using LR should feel satisfying and clear
- The custom filter system should feel lightweight — adding a rule like "Evasion → reminder" should be quick, not a multi-step wizard

</specifics>

<deferred>
## Deferred Ideas

None — discussion stayed within phase scope

</deferred>

---

*Phase: 12-save-roller-upgrades*
*Context gathered: 2026-02-26*
