# Phase 14: Bug Fixes & Critical Polish - Context

**Gathered:** 2026-02-26
**Status:** Ready for planning

<domain>
## Phase Boundary

Fix all 16 verified bugs from the v2.0 manual testing round and apply 5 quick UX improvements to the Combat Tracker, Attack Roller output, and Encounter Sidebar. Every fix is a targeted change to existing code with no new tabs, services, or major UI restructuring — except BUG-06 which gets a broader parser fix with section boundary detection.

</domain>

<decisions>
## Implementation Decisions

### Combat Tracker UX

- **Rubber-band selection (UX-03):** Remove card dragging entirely from Combat Tracker — cards are not draggable. All click-drag in the combat area starts rubber-band selection. No modifier key needed.
- **Group damage (BUG-12):** First-come-first-served distribution — damage hits the first non-defeated member in the group, overflow passes to the next member. Like mowing through minions.
- **Condition chip overflow (UX-05):** Max 2 rows of condition chips, then a "+N more" badge for overflow. No horizontal scrollbar, no unlimited vertical growth.
- **Group member collapse (BUG-13):** Double-click to toggle — double-click a CompactSubRow to expand to full CombatantCard, double-click the expanded card to collapse back to CompactSubRow.

### Output Rendering

- **Regular misses (BUG-08):** No styling at all — regular misses look identical to normal text. Only natural-1 misses get the red background tint.
- **Crit gold tint (BUG-09):** Gold background wraps only the text content, not the full line width. Fix the double-layering bug — single gold tint layer only.
- **Nat-1 red tint (BUG-08):** Consistent with crit — red tint wraps text content only, not the full line width.
- **Line spacing (BUG-10):** All attack lines (hit, crit, miss) stack tightly with consistent single-line spacing. No gaps, no extra blank lines between lines.

### Parser Fix Scope

- **BUG-06 approach:** Broader action-text fix, not a Lich-specific patch. Fix the underlying text attribution logic so all monsters get correct after-attack-text.
- **Section boundary detection:** Parser should recognize section headers (Actions, Reactions, Legendary Actions, Lair Actions) and never let text cross section boundaries.
- **Model changes:** Add `legendary_actions` and `lair_actions` as separate list fields on the Monster model. Regular actions stay in `actions`. This gives Phase 15 (traits separation) a clean foundation to build on.
- **Phase 15 overlap:** Keep model changes minimal here — `legendary_actions` and `lair_actions` fields only. Phase 15 adds `traits` separation on top of this foundation.

### Claude's Discretion
- Fix prioritization order (which bugs to tackle first within each plan)
- Exact HTML structure for crit/miss/hit line wrapping
- How the "+N more" condition chip overflow badge looks and behaves
- Parser section header detection regex patterns
- How group damage first-come-first-served handles edge cases (all defeated, etc.)

</decisions>

<specifics>
## Specific Ideas

- Crit and nat-1 styling should be content-width only — the current full-line gold blocks look jarring
- Group damage should feel like mowing through minions — damage flows to next member automatically
- Double-click toggle for group members is consistent with common UI patterns (expand/collapse)
- Parser section boundaries are the root fix for BUG-06 — without them, after-attack-text will keep bleeding between sections for other monsters too

</specifics>

<deferred>
## Deferred Ideas

None — discussion stayed within phase scope. Parser traits separation explicitly deferred to Phase 15 (PARSE-01).

</deferred>

---

*Phase: 14-bug-fixes-critical-polish*
*Context gathered: 2026-02-26*
