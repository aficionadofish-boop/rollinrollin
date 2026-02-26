# Phase 10: Persistent Encounter Sidebar - Context

**Gathered:** 2026-02-26
**Status:** Ready for planning

<domain>
## Phase Boundary

A collapsible QDockWidget sidebar on the right side of the main window that shows the active encounter across all main tabs (Library, Attack Roller, Saves). The encounter list that currently lives inside the "Encounters & Saves" tab becomes a persistent, always-visible panel. SavesTab is extracted as its own standalone tab. The sidebar is a view of the active encounter — the same data that the Combat Tracker (Phase 11) will manage.

</domain>

<decisions>
## Implementation Decisions

### Sidebar Layout & Position
- Docked on the **right side** of the main window
- Base width **300px**, resizable by click-and-drag on the edge
- Width persists across sessions (remembered in settings)
- Subtle background color difference from main content to visually separate it
- Encounter name displayed read-only in sidebar — renaming only in Combat Tracker (Phase 11)

### Monster List Display
- Minimal display: **name + count** (e.g. "Goblin x3")
- Renamed creatures get their own row with base type in parentheses (e.g. "Volt the Booyagh (Goblin) x1")
- Default sort order: **CR descending**; switches to **initiative order** when combat is active in Combat Tracker
- Count is **inline editable** — click the count number to change it directly

### Encounter Summary Header
- Shows **total creature count + total XP**
- Shows **difficulty rating** (Easy/Medium/Hard/Deadly) only if party data (size + average level) has been configured in Combat Tracker
- If no party data, just XP total is shown

### Empty/Inactive State
- When no encounter exists, sidebar toggle is **grayed out and not openable**
- Sidebar activates when the first monster is dragged onto the drop field in the Library tab
- When the last monster is removed, sidebar **auto-closes**

### Interaction — Adding Monsters
- Drag-and-drop from Library tab only (existing drag-and-drop field mechanism)
- Cannot add from other tabs — must go to Library
- Adding a monster already in the encounter **auto-increments count** silently
- Monsters can be **reordered within sidebar via drag-and-drop**

### Interaction — Removing Monsters
- **X button** on each monster row for quick removal
- **Right-click context menu** with: Remove, Remove all of type, and additional actions

### Interaction — Selecting for Rolling
- **Single-click** a monster row to select it as active attacker for Attack Roller (pre-loads it)
- **Double-click** a monster row to select AND switch to Attack Roller tab
- Selected monster row gets a **visual highlight** (background color)
- Selecting a grouped monster (e.g. "Goblin x3") selects **all of that type**

### Right-Click Context Menu
- Full context menu with multiple actions: Remove, Remove all of type, Roll attacks, View stat block, etc.

### Collapse & Toggle
- **Edge handle/grip** on the sidebar's left edge — click to collapse/expand
- When collapsed, a **thin strip (~20px)** remains visible with the handle
- **Smooth slide animation** (~200ms) for collapse/expand transitions

### Save/Load Encounters
- Save/Load accessed from sidebar (Claude's discretion on exact button/menu placement)
- When loading a different encounter, **auto-save current** encounter first
- Load encounter UI: **modal dialog** showing saved encounters with name, creature count, date saved
- Load dialog supports both **loading and deleting** saved encounters

### Claude's Discretion
- Exact collapse/expanded state persistence across restarts (whether to remember or always start expanded)
- Save/Load button placement and styling in sidebar header
- Context menu item ordering and exact actions beyond Remove/Remove all
- Loading skeleton or transition states
- Exact animation easing curves

</decisions>

<specifics>
## Specific Ideas

- The encounter list from the current "Encounters & Saves" tab is being extracted — it stays as a list but moves to the Combat Tracker tab (Phase 11). The sidebar is a persistent cross-tab view of that same encounter.
- The drag-and-drop field on the Library tab that currently adds to the encounter list stays — this is the primary way monsters enter the encounter.
- Sidebar monster selection feeds directly into Attack Roller as the active attacker — this is a core DM workflow optimization (see monster in sidebar → click → roll attacks).

</specifics>

<deferred>
## Deferred Ideas

- Encounter renaming — Phase 11 (Combat Tracker)
- Party size/level configuration for difficulty calculation — Phase 11 (Combat Tracker)
- Initiative ordering display — Phase 11 (Combat Tracker, sidebar reflects it when active)
- Individual creature selection within a monster group — potential future enhancement

</deferred>

---

*Phase: 10-persistent-encounter-sidebar*
*Context gathered: 2026-02-26*
