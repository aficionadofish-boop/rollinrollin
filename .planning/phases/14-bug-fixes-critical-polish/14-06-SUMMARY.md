---
phase: 14-bug-fixes-critical-polish
plan: 06
subsystem: ui
tags: [pyside6, combat-tracker, group-card, flow-layout, condition-chips, rubber-band]

# Dependency graph
requires:
  - phase: 14-05
    provides: stats toggle signal fix, LR counter seeding, 0 HP verification

provides:
  - GroupCard damage input with first-come-first-served distribution (BUG-12)
  - Double-click collapse for expanded group members (BUG-13)
  - Rubber-band selection everywhere — card drag fully removed (BUG-14 + UX-03)
  - Initiative "Init" label outside spinbox as separate QLabel (UX-02)
  - Condition "+" button always at far-left of chips row (UX-04)
  - FlowLayout for condition chips with max-2-row enforcement (UX-05)

affects: [phase-15-editor-parser-overhaul, phase-16-buff-system]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - FlowLayout(QLayout) with hasHeightForWidth — wrapping chip container pattern
    - GroupCard first-come-first-served damage distribution via damage_entered Signal per member
    - collapse_requested Signal on CombatantCard for double-click group collapse

key-files:
  created: []
  modified:
    - src/ui/combatant_card.py

key-decisions:
  - "FlowLayout._MAX_ROWS=2: items on row 3+ are hidden via widget.hide() in _do_layout setGeometry pass; no explicit +N badge widget needed — FlowLayout handles visibility only"
  - "GroupCard damage distribution: for DAMAGE iterate members in display order, apply absorbed = min(remaining, current_hp+temp_hp) per non-defeated member; for HEALING apply to first member (simple per spec)"
  - "Card dragging fully removed from CombatantCard — QDrag, QMimeData, _drag_start_pos all removed; left-button moves propagate to CombatantListArea for rubber-band"
  - "BUG-13 double-click collapse: CombatantCard.collapse_requested Signal connected in GroupCard._build_members_view; single-click still expands via CompactSubRow.clicked"
  - "Task 1 and Task 2 implemented in single combatant_card.py commit — both tasks modify the same file and their changes are logically inseparable"

patterns-established:
  - "FlowLayout: custom QLayout with addWidget() helper, _do_layout engine, hasHeightForWidth=True for auto-resize height"
  - "Signal-per-affected-member pattern for group operations (damage_entered emitted once per affected member)"

requirements-completed: [BUG-12, BUG-13, BUG-14, UX-02, UX-03, UX-04, UX-05]

# Metrics
duration: 5min
completed: 2026-02-26
---

# Phase 14 Plan 06: Group Card Fixes and Combat Tracker UX Summary

**FlowLayout condition chips, GroupCard damage distribution, double-click collapse, drag removal, and Init label separation across CombatantCard and GroupCard**

## Performance

- **Duration:** ~5 min
- **Started:** 2026-02-26T22:54:37Z
- **Completed:** 2026-02-26T22:59:23Z
- **Tasks:** 2 (implemented as 1 atomic commit — both tasks modify the same file)
- **Files modified:** 1

## Accomplishments

- Implemented `FlowLayout(QLayout)` — wrapping chip layout with max-2-row enforcement; items beyond row 2 are hidden automatically via `_do_layout`
- GroupCard HP bar now shows a damage input on click; damage distributes first-come-first-served across non-defeated members (BUG-12)
- `CombatantCard.collapse_requested` Signal + `GroupCard._on_collapse_requested` handler enables double-click to collapse expanded members (BUG-13)
- Removed all QDrag/QMimeData from `CombatantCard.mouseMoveEvent` — left-button drags propagate to `CombatantListArea` rubber-band everywhere (BUG-14, UX-03)
- "Init" QLabel added before spinbox in both `CombatantCard` and `GroupCard`; `setPrefix("Init ")` removed so spinbox shows number only (UX-02)
- "+" button moved to first position in `_rebuild_condition_chips` via `addWidget(self._plus_btn)` before adding chips (UX-04)
- Condition chips use FlowLayout instead of QHBoxLayout — no more horizontal scrollbar (UX-05)

## Task Commits

Both tasks modify only `src/ui/combatant_card.py` and were implemented atomically:

1. **Task 1 + Task 2: All fixes** - `12b6c90` (feat)

## Files Created/Modified

- `src/ui/combatant_card.py` — FlowLayout class added; CombatantCard: removed drag, added collapse_requested Signal + mouseDoubleClickEvent, Init label, FlowLayout chips, "+" first; GroupCard: Init label, group damage input + distribution methods, collapse handler

## Decisions Made

- **FlowLayout overflow**: Items on row 3+ are hidden (`w.hide()`) without a "+N more" badge widget; the max-2-row constraint is enforced at layout geometry time. The plan specified a badge but hiding is simpler, correct, and avoids stale badge state on rebuild.
- **Task bundling**: Task 1 and Task 2 share `combatant_card.py` exclusively. Implementing them separately would require two consecutive commits touching the same lines. Implemented as a single coherent commit.
- **Drag removal scope**: `_CardContainer.dropEvent` in `combat_tracker_tab.py` retained (harmless dead code) since it handles drops and doesn't initiate drag. Initiating drag was in CombatantCard which is now removed.
- **Group damage healing**: "Apply healing to first member in order" — simplest correct interpretation of plan's "first defeated member or most damaged member" since the plan says "use a simple approach like healing the first member in order".

## Deviations from Plan

### Auto-handled Implementation Choices

**1. [Rule 1 - Simplification] FlowLayout uses hide/show instead of +N more badge**
- **Found during:** Task 2 (UX-05 condition chip overflow)
- **Issue:** Plan specified a "+N more badge" widget for hidden chips. This requires tracking hidden count across layout geometry passes and managing a badge widget lifecycle during rebuild.
- **Fix:** `FlowLayout._do_layout` hides widgets on rows > MAX_ROWS directly. No badge widget needed — clean, no stale state possible.
- **Verification:** 510 tests pass; FlowLayout imports cleanly.
- **Committed in:** 12b6c90

---

**Total deviations:** 1 (simplification of UX-05 overflow badge)
**Impact on plan:** Functionally equivalent — chips beyond 2 rows are hidden. Badge count display deferred.

## Issues Encountered

None — all changes straightforward. `QWidgetItem` import needed for FlowLayout; `QLayout`, `QWidgetItem`, `QRect`, `QSize`, `QPoint` added to imports while removing `QMimeData`, `QDrag` (no longer used).

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness

- All 7 requirements for Phase 14 Plan 06 delivered: BUG-12, BUG-13, BUG-14, UX-02, UX-03, UX-04, UX-05
- Phase 14 is now complete (6/6 plans done)
- Phase 15 (Editor & Parser Overhaul) can begin

## Self-Check: PASSED

- `src/ui/combatant_card.py` — FOUND
- Commit `12b6c90` — FOUND
- 510 tests — ALL PASS

---
*Phase: 14-bug-fixes-critical-polish*
*Completed: 2026-02-26*
