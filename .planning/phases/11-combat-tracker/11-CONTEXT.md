# Phase 11: Combat Tracker - Context

**Gathered:** 2026-02-26
**Status:** Ready for planning

<domain>
## Phase Boundary

New Combat Tracker tab with HP bars, condition tracking, initiative ordering, turn cycling, and player character subtab. DMs manage the full combat loop for all encounter combatants in a single dedicated tab, with state that persists across sessions. Creating save roller upgrades, output polish, and theming are separate phases.

</domain>

<decisions>
## Implementation Decisions

### Combatant Row Layout
- Wide horizontal card rows — each combatant is a card, not a table row
- Balanced layout: name/initiative and HP bar share roughly equal space; conditions below or to the right
- AC displayed as a permanent badge on every card (always visible, not toggleable)
- HP bar is color-coded (green/yellow/red); click the HP bar to reveal a damage/healing input (click-to-reveal, not always visible)
- Temp HP shown as a distinct-colored stacked bar segment on top of the regular HP bar (e.g., blue overlay)
- No card expansion on click — cards are fixed size; full stat block lives in the Library tab
- No per-combatant notes field

### Toggleable Stat Display
- Global toggle menu in the Combat Tracker toolbar (gear/filter icon → dropdown)
- Toggleable stats: walking speed, flying speed, climbing speed, swimming speed, burrowing speed, passive perception, legendary resistance (with uses tracker), legendary actions (with uses tracker), regeneration indicator
- Legendary resistance and legendary action uses auto-detected from monster traits (parsed from data), DM can override
- Legendary actions reset at the start of the creature's turn (per RAW); legendary resistance does not auto-reset in combat
- Regeneration: two toggles — display toggle (show "Regen: X HP" on card) and auto-apply toggle (auto-heals when round advances)

### Combat Log
- Right-side panel (alongside combatant list, replacing sidebar on this tab)
- Logs everything: HP changes, condition adds/removes/expiry, initiative changes, turn advances, round count changes
- Persistent until manually cleared by the DM (survives encounter changes)
- Copy-to-clipboard button at the top of the log panel for pasting into session notes

### Damage and Healing
- Click HP bar to reveal damage input; enter signed number (+12 for healing, -23 for damage) and press Enter
- Temp HP absorbed first, remainder from current HP
- AOE damage: separate "AOE Damage" button in the toolbar — opens damage input that applies the same damage to all selected combatants
- Single-target damage on collapsed group: damage goes to first alive individual, overflow to next
- AOE damage on collapsed group: all individuals in the group receive the same damage

### Defeated Combatants (0 HP)
- Health bar turns red; name gets strikethrough text
- Card stays in the initiative list (not moved to a separate section)
- Defeated combatants are still cycled through in turn order (important for PC death saves)

### Multi-Select
- Click-and-drag for box selection across combatant cards
- Ctrl-click to toggle individual combatants while keeping previous selection
- Shift-click to select range from last selected to clicked combatant
- Selected cards get a colored border highlight (e.g., blue) distinct from turn highlight
- When multiple combatants are selected, adding a condition or dealing damage applies to all selected

### Initiative and Ordering
- Initiative value is click-to-edit inline on the card; list re-sorts immediately on change
- Both initiative sort mode and manual drag-to-reorder mode, with a toggle between them
- Initiative mode toggle in the toolbar: ON = sorted by initiative descending with "Next Turn"/"Previous Turn" cycling; OFF = shows "Pass 1 Round" button instead

### Condition Display and Expiry
- Colored chips/tags below the HP bar: "Poisoned (2)" with a unique fixed color per condition type
- Indefinite conditions supported (no duration) — shown with no round count or "∞" symbol
- Conditions at 1 round remaining get a dotted red line border as a visual warning
- Expired conditions (0 rounds): chip stays on the card, grayed out/strikethrough, flagged as expired — stays until DM manually dismisses
- Click a condition chip to edit its duration or remove it (small popup)
- "+" button on each card opens a dropdown of preset conditions and buffs, plus custom entry field
- Preset conditions/buffs have pre-configured default durations (Bless=10 rounds, Shield=1 round, etc.) — DM can override before adding
- Custom conditions: DM enters name and optional duration

### Turn and Round Flow
- Current turn highlighted with BOTH an arrow/chevron indicator from the left edge AND a distinct glow/border on the active card
- Prominent round counter display ("Round 3") at the top of the Combat Tracker
- Next Turn and Previous Turn buttons in the toolbar alongside the round counter
- Previous Turn undoes condition counter decrements (full undo of the turn advance)
- No keyboard shortcuts for turn cycling — buttons only
- Auto-scroll behavior: Claude's discretion

### Grouped Initiative
- Auto-grouping on by default: same monster types share initiative, displayed as "Nx [Monster]"
- Toggle in toolbar to disable auto-grouping (shows all combatants individually)
- When ungrouped, each creature has its own initiative; conditions decrement per their individual turn
- When grouped, creatures share initiative; conditions decrement together as a group
- Collapsed group card: shows "4x Goblin" with average HP bar representing overall group health
- Expand group: compact sub-rows for each individual, indented to show group membership
- Click individual sub-row: expands to a full-size card
- Individual naming: auto number suffix (Goblin 1, Goblin 2, Goblin 3, etc.)

### Combat State Persistence
- Combat state (HP, conditions, initiative order, round count) persists across app restarts — reloading an encounter restores exact state
- "Reset Combat" button in toolbar with confirmation dialog — clears all HP, conditions, and initiative for a fresh start with the same encounter

### Player Characters
- PCs persist globally across encounters (saved separately from encounter data)
- PC subtab for managing the party: name, AC, HP, conditions
- All saved PCs auto-join every combat's initiative; DM can remove individuals not present
- PCs appear in initiative order alongside monsters with the same card layout

### Claude's Discretion
- Auto-scroll behavior when turn advances (scroll to center active combatant, or only when off-screen)
- Exact color palette for condition chips
- Color palette for the turn highlight glow vs selection border
- HP bar color thresholds (what % triggers yellow, red)
- Spacing and typography within cards
- Combat log entry formatting
- Exact toolbar layout and icon choices
- Pre-configured durations for each preset condition/buff

</decisions>

<specifics>
## Specific Ideas

- Damage feedback is through the combat log, not animations on cards
- Three-level progressive disclosure for groups: collapsed card → expanded compact sub-rows (indented) → click sub-row for full card
- The combat log serves as a full session timeline — the DM can copy it out for session notes after the game
- Multi-select feels like a desktop app: drag box, ctrl-click, shift-click — all standard desktop interaction patterns

</specifics>

<deferred>
## Deferred Ideas

None — discussion stayed within phase scope

</deferred>

---

*Phase: 11-combat-tracker*
*Context gathered: 2026-02-26*
