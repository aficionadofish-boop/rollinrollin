# Phase 16: Buff System & Output Improvements - Context

**Gathered:** 2026-02-28
**Status:** Ready for planning

<domain>
## Phase Boundary

Revamp the buff system with per-roll-type targeting (4 independent checkboxes), auto-calculate buff dice into attack and save rolls, add creature/attack headers and per-damage-type summaries to attack output, implement encounter naming with timestamps and editable names, make the sidebar user-resizable, and add descriptive health-level text to combat tracker HP bars.

</domain>

<decisions>
## Implementation Decisions

### Buff editor defaults & layout
- **Default checkboxes:** Attacks and Saves checked, Ability Checks and Damage unchecked (matches common buffs like Bless)
- **Checkbox labels:** Short form — Attacks | Saves | Checks | Damage
- **Checkbox layout:** Single horizontal row of all 4 checkboxes

### Buff output formatting
- **Inline labeled** — Each buff is named in the roll breakdown: `[d20=15] + 7 + Bless 1d4(3) + Shield(2) = 27`
- Multiple buffs appear with their names so the DM can trace which buff contributed what
- **First line full, then abbreviated** — On bulk rolls (e.g., 13x attacks), the first roll line shows full buff labels (`+ Bless 1d4(3)`), subsequent lines use shortened form (`+ 1d4(2)` or similar abbreviation)
- **Summary stays clean** — The summary line (hits/misses/crits/total damage + damage type breakdown) does NOT include buff contribution totals. Buff detail lives in per-roll lines only
- **Saves mirror attack format** — Save roll buff display uses the same inline-labeled, abbreviate-after-first style as attack rolls for consistency across the app

### Encounter naming & save flow
- **Inline name field in sidebar** — A name field sits in the sidebar, always visible (not a popup dialog on save)
- **Pre-filled auto-name** — Field shows the auto-generated name (e.g., "2026-02-28 14:35 — 3 creatures") by default. DM can clear and type a custom name, which becomes `"{Custom} — 2026-02-28 14:35 — 3 creatures"`
- **Live-updating auto-name** — The auto-generated portion updates as creatures are added/removed (creature count stays current)

### Health bar labels
- **Always visible** — Descriptive text shown at all times, no hover required
- **Overlaid on the bar** — Text rendered directly on the colored HP bar (like a progress bar label), no extra space needed
- **Description only** — Just the label ("Injured", "Near Death"), no HP percentage. Clean, thematic, DM-screen feel

### Claude's Discretion
- Buff data migration strategy (old single `targets` field → new 4-checkbox format)
- Exact abbreviated buff label format for subsequent roll lines
- Encounter name edit confirmation pattern in Load dialog (ENC-02)
- Health label text color/contrast approach across the 5 color bands
- All other technical implementation details — requirements in ROADMAP.md are very specific and locked

</decisions>

<specifics>
## Specific Ideas

- Buff traceability matters — DM needs to see which buff contributed what to a roll
- Bulk rolls (13x attacks) should stay readable, not cluttered — hence abbreviation after first line
- Summary line should remain focused on combat outcomes (hits/damage), not buff accounting
- Encounter name field should feel like part of the sidebar, not a separate save workflow
- Health labels should give a DM-screen feel — thematic descriptions, not numbers

</specifics>

<deferred>
## Deferred Ideas

None — discussion stayed within phase scope

</deferred>

---

*Phase: 16-buff-system-output-improvements*
*Context gathered: 2026-02-28*
