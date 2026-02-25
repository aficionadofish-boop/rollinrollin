# Phase 8: Domain Expansion and Persistence Foundation - Context

**Gathered:** 2026-02-25
**Status:** Ready for planning

<domain>
## Phase Boundary

New domain models, JSON persistence service, and Monster Math Engine — the prerequisite layer for all v2.0 features. No new UI tabs; only the Settings tab gets a flush/clear section. The math engine and domain models are consumed by downstream phases (Monster Editor, Combat Tracker, etc.).

</domain>

<decisions>
## Implementation Decisions

### Persistence categories
- Four categories: loaded monsters, encounters, modified monsters, macros
- Each category persisted independently with its own flush control
- Settings/preferences are NOT a flushable category (those stay separate)

### Flush UX in Settings
- Per-category flush buttons, each showing entry count (e.g. "Modified Monsters: 12 entries")
- "Clear All Data" button that flushes everything at once
- Always show a confirmation dialog before any flush operation (per-category and clear-all)

### Math validation flagging
- Flagged values shown in a distinct color (e.g. orange) with a hover tooltip
- Tooltip shows detailed breakdown: expected value vs actual, e.g. "Expected +5 (prof + STR), got +7 — custom +2"
- Engine distinguishes non-proficient / proficient / expertise / custom states for saves
- Engine validates attack to-hit and damage bonuses with the same detail level
- Validation only runs after edits — base imported monsters are NOT flagged
- When a mismatch is detected, offer a "Recalculate" button next to the flagged value (DM clicks to accept the calculated value); never auto-correct

### Spellcasting detection
- Auto-detect casting ability from Spellcasting trait text, pre-fill the field, DM can override
- Handle both 2014 dual-trait format (Spellcasting + Innate Spellcasting) and 2024 merged format
- Track multiple casting abilities per monster (Innate vs regular Spellcasting validate independently)
- When parser can't detect casting ability: default to highest mental stat (WIS, INT, CHA) and show a hint ("Spellcasting detected but casting ability assumed — verify")
- Spell attack bonus = casting mod + prof + focus bonus; spell save DC = 8 + casting mod + prof + focus bonus

### Save timing and feedback
- Periodic auto-save (e.g. every 30 seconds) plus save on close
- Subtle status bar text briefly showing "Saved" after each auto-save
- Data file lives in the same folder as the .exe (portable, consistent with v1.0 workspace approach)

### Claude's Discretion
- Corrupt data recovery strategy (backup + start fresh, or start fresh + warn)
- Auto-save interval (30s suggested, can adjust)
- JSON file structure and naming
- Internal domain model architecture
- Exact flag color choice

</decisions>

<specifics>
## Specific Ideas

- Flush buttons should show counts so the DM knows what they're clearing before confirming
- Math validation tooltips should be genuinely helpful — show the math, not just "custom"
- Spellcasting fallback to highest mental stat is a sensible default that covers most monsters correctly
- Portable data storage (same folder as .exe) is important — this is a portable app

</specifics>

<deferred>
## Deferred Ideas

None — discussion stayed within phase scope

</deferred>

---

*Phase: 08-domain-expansion-and-persistence-foundation*
*Context gathered: 2026-02-25*
