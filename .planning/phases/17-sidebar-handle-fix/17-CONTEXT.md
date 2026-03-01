# Phase 17: Sidebar Handle Fix - Context

**Gathered:** 2026-03-01
**Status:** Ready for planning

<domain>
## Phase Boundary

Make the encounter sidebar's QSplitter resize handle visible, discoverable, and reliably operable. The sidebar already uses a QSplitter (uncommitted working tree) — this phase fixes the handle so users know they can drag to resize and the interaction works cleanly. No new sidebar features, no changes to sidebar content or encounter management.

</domain>

<decisions>
## Implementation Decisions

### Handle appearance
- Subtle divider line (1-2px) between the tab area and the sidebar
- Line brightens or widens slightly on hover to indicate draggability
- Fits the existing dark theme — not a bulky grip dots pattern

### Cursor feedback
- Show the horizontal resize cursor on hover over the handle zone
- Standard OS convention for draggable dividers

### Grab zone
- Medium grabbable zone (8-10px) — easy to grab without looking oversized
- Visual line stays thin; the detection/click area is wider than the visible line

### Collapsed state
- No resize handle visible when sidebar is collapsed (24px _RotatedButton strip)
- The "Show" button strip is the only interaction when collapsed
- Resize handle appears only when sidebar is expanded

### Claude's Discretion
- Exact hover highlight color/opacity for the divider line
- Whether grab zone is exactly 8px or 10px
- QSplitter handle styling implementation (stylesheet vs custom paint)
- Minimum/maximum sidebar width constraints during drag
- Width persistence behavior (already partially implemented in working tree)

</decisions>

<specifics>
## Specific Ideas

- Current QSplitter is already in the uncommitted working tree (Architecture Approach 3 from SIDEBAR_HANDLE_HISTORY.txt) — this phase stabilizes it rather than replacing it
- The _RotatedButton collapse handle at 24px is working and stays as-is
- SIDEBAR_HANDLE_HISTORY.txt documents all prior approaches and should be consulted during research

</specifics>

<deferred>
## Deferred Ideas

None — discussion stayed within phase scope

</deferred>

---

*Phase: 17-sidebar-handle-fix*
*Context gathered: 2026-03-01*
