# Phase 15: Editor & Parser Overhaul - Context

**Gathered:** 2026-02-27
**Status:** Ready for planning

<domain>
## Phase Boundary

Transform the Monster Editor from a flat action list into a structured traits + actions + rollable abilities system. Separate traits from actions with a new Traits section, add after-attack-text editing, label action fields, add rollable trait buttons with auto-dice-detection to the Attack Roller, support recharge abilities, add [[XdY]] average notation, display monster speed, and compact the editor layout. Requirements: PARSE-01 through PARSE-11.

</domain>

<decisions>
## Implementation Decisions

### Traits section design
- Traits are a new collapsible section in the editor column, positioned between Core Stats (abilities/CR/HP/skills) and Actions — NOT a separate tab
- Individual traits display as a compact name list; clicking a trait opens an edit modal with title + multiline description fields
- Add/remove traits: Claude's discretion on approach (match existing editor patterns)
- Traits with detected rollable dice show a small dice icon or "rollable" tag next to their name in the compact list

### Rollable trait output
- Full trait text is shown in output when a trait button is clicked
- Both the average AND the dice formula are replaced with just the rolled result in brackets — e.g. "deals (47) acid damage" not "deals 54 (12d8) acid damage"
- Rolled values are color-highlighted using damage type colors (fire = red, acid = green, etc.) — same color system as attack rolls
- Recharge roll appears in the output header: "Acid Breath (Recharge 5-6) [rolled: 4]" with green/red coloring for pass/fail
- Trait buttons in the Attack Roller tab use the same button style as attack rows, but in a clearly separated row with a "Traits" label divider

### Editor layout compaction
- CR, HP, Speed, and Skills merge into the ability scores section inside one collapsible section called "Core Stats"
- Internal layout: ability scores at top, then CR/HP/Speed row, then Skills — stacked rows within the single section
- Speed display (PARSE-09) goes inside Core Stats section
- Full section order top-to-bottom: Name > Core Stats > Traits > Actions > Equipment > Buffs

### After-attack-text & field labels
- After-attack-text field is expandable on demand — a toggle/button reveals the multiline text area, keeps default action view clean
- Action field labels use column header style — a single header row above all action rows with column labels ("Name", "To-Hit", "Damage", etc.) like a table
- After-attack-text only displays in roll output on hits, not on misses
- [[XdY]] average is always auto-calculated from the dice formula — not editable by the user

### Claude's Discretion
- Trait add/remove UX (buttons, context menus — match existing patterns)
- After-text toggle button placement and styling
- Column header label exact text and alignment
- Exact spacing and typography within Core Stats section
- Trait edit modal layout and sizing
- How to handle traits with no description text

</decisions>

<specifics>
## Specific Ideas

- Trait roll output should strip the average entirely — "deals (47) acid damage" not "deals 54 (rolled: 47) acid damage"
- The recharge roll display in the header mirrors the D&D convention: ability name, recharge range in parens, rolled value in brackets with pass/fail color
- Column headers for action fields should feel like a table/spreadsheet header row

</specifics>

<deferred>
## Deferred Ideas

None — discussion stayed within phase scope.

</deferred>

---

*Phase: 15-editor-parser-overhaul*
*Context gathered: 2026-02-27*
