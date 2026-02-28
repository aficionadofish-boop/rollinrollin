# Phase 16: Buff System & Output Improvements - Context

**Gathered:** 2026-02-28
**Status:** Ready for planning

<domain>
## Phase Boundary

Revamp the buff system with per-roll-type targeting (4 independent checkboxes), auto-calculate buff dice into attack and save rolls, add creature/attack headers and per-damage-type summaries to attack output, implement encounter naming with timestamps and editable names, make the sidebar user-resizable, and add descriptive health-level text to combat tracker HP bars.

</domain>

<decisions>
## Implementation Decisions

### Buff output formatting
- **Inline labeled** — Each buff is labeled in the roll breakdown: `[d20=15] + 7 + Bless 1d4(3) + Shield of Faith(2) = 27`
- Multiple buffs appear with their names so the DM can trace which buff contributed what
- **First line full, then abbreviated** — On bulk rolls (e.g., 13x attacks), the first roll line shows full buff labels (`+ Bless 1d4(3)`), subsequent lines use shortened form (`+ 1d4(2)` or similar abbreviation)
- **Summary stays clean** — The summary line (hits/misses/crits/total damage + damage type breakdown) does NOT include buff contribution totals. Buff detail is visible in the per-roll lines only.
- **Saves mirror attack format** — Save roll buff display uses the same inline-labeled, abbreviate-after-first style as attack rolls for consistency across the app

### Claude's Discretion
- Buff editor checkbox layout and arrangement (BUFF-01 UI)
- Default checkbox states for new buffs
- Encounter save naming UX flow details (ENC-01)
- Health label positioning and prominence on HP bars (COMBAT-UX-01)
- Exact abbreviated buff label format for subsequent roll lines
- All other areas not discussed — requirements in ROADMAP.md are very specific and locked

</decisions>

<specifics>
## Specific Ideas

- User wants buff traceability — being able to see which buff contributed what to a roll matters
- Bulk rolls (13x attacks) should stay readable, not cluttered — hence the abbreviation after first line
- Summary line should remain focused on combat outcomes (hits/damage), not buff accounting

</specifics>

<deferred>
## Deferred Ideas

None — discussion stayed within phase scope

</deferred>

---

*Phase: 16-buff-system-output-improvements*
*Context gathered: 2026-02-28*
