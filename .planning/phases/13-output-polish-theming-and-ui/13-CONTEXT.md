# Phase 13: Output Polish, Theming, and UI - Context

**Gathered:** 2026-02-26
**Status:** Ready for planning

<domain>
## Phase Boundary

Color-coded attack output by damage type, Roll20 template card rendering in the macro sandbox, an app-wide theming system with presets and custom colors, and visual highlighting of active toggles across all tabs. This is the visual polish layer on top of all existing v2.0 functionality.

</domain>

<decisions>
## Implementation Decisions

### Damage type color palette
- Grouped by physical vs magical: physical types (slashing, piercing, bludgeoning) share a neutral/gray tone family (slate, silver, steel); magical types each get a distinct intuitive color
- Full damage component coloring — the entire "2d6+4 fire" segment is colored by its damage type, not just the numbers
- Crits use color + full row background highlight (e.g. gold/bright background); misses also get row highlight treatment (muted/red background)

### Roll20 template card rendering
- Approximate Roll20 look: same structure (colored header, key/value rows) but styled to match the app's own visual language, not a pixel-perfect replica
- Card header is theme-aware — picks up the active theme's accent color rather than a fixed Roll20 maroon
- Cards render inline in the sandbox output area, replacing the raw text for that macro
- Mixed macros (template + regular inline rolls): template portion renders as a card, non-template output renders as plain text above/below the card

### Theme system
- Three presets: Default (light), High Contrast, and Dark
- Beyond presets, users can customize: text color, background color, and accent color
- Theme switching via dropdown with live preview — applies immediately on selection, no Apply button
- Sandbox font: preset dropdown list of 5-8 curated monospace fonts (Consolas, Fira Code, Courier New, etc.), independent from app font

### Toggle highlighting
- Active toggles get a colored border + colored text treatment (no background fill)
- Toggle highlight color follows the theme's accent color
- Applies to buttons and checkboxes only — not dropdowns or other selection controls
- Inactive toggles remain normal/unstyled Qt controls — no special treatment

### Claude's Discretion
- Exact color values for each of the 13 damage types (within the physical=neutral, magical=distinct constraint)
- Crit/miss row highlight exact colors and opacity
- Template card internal layout, spacing, and typography
- Which monospace fonts to include in the sandbox preset list
- Dark theme and High Contrast theme color values
- How the theme system is architecturally implemented (stylesheet approach, etc.)

</decisions>

<specifics>
## Specific Ideas

- Physical damage types (slashing, piercing, bludgeoning) should feel understated — they're the "default" damage, so neutral grays let the magical colors pop
- Template cards should feel native to the app, not like an embedded iframe from Roll20
- Theme switching should be instant — no restart, no flash of unstyled content

</specifics>

<deferred>
## Deferred Ideas

None — discussion stayed within phase scope

</deferred>

---

*Phase: 13-output-polish-theming-and-ui*
*Context gathered: 2026-02-26*
