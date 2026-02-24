---
phase: 05-roll20-macro-sandbox
plan: 03
subsystem: ui
tags: [pyside6, qframe, qsplitter, qscrollarea, qlistwidget, roll20, macro, workspace]

# Dependency graph
requires:
  - phase: 05-01
    provides: MacroSandboxService (preprocess_all_lines, collect_all_queries, execute), MacroRollResult, MacroLineResult, MacroWarning — consumed by ResultPanel and MacroSandboxTab
  - phase: 05-02
    provides: MacroEditor (QPlainTextEdit + line numbers + syntax highlighting), QueryPanel (inline query widget with answered Signal) — embedded in MacroSandboxTab
provides:
  - src/ui/macro_result_panel.py with ResultCard and ResultPanel
  - src/ui/macro_sidebar.py with MacroSidebar
  - src/ui/macro_sandbox_tab.py with MacroSandboxTab
  - Updated src/ui/app.py with 4-tab MainWindow including Macro Sandbox
affects:
  - 05-04 (end-to-end verification — exercises the complete tab assembled here)

# Tech tracking
tech-stack:
  added: []  # All PySide6 classes already in project; no new pip packages
  patterns:
    - "QSplitter nested layout: horizontal splitter (main | sidebar) wrapping vertical splitter (editor | results)"
    - "ResultCard collapsible pattern: QFrame StyledPanel + QWidget detail hidden by default, toggled via QPushButton"
    - "Auto-trim roll sets: list of (divider, cards) tuples; pop oldest and call deleteLater() when over limit"
    - "Scroll-to-bottom via QTimer.singleShot(50, ...) to ensure layout is settled before scrolling"
    - "Tab-owns-save pattern: sidebar Save button clicked -> tab._on_save_macro -> sidebar.save_macro(editor.toPlainText())"

key-files:
  created:
    - src/ui/macro_result_panel.py
    - src/ui/macro_sidebar.py
    - src/ui/macro_sandbox_tab.py
  modified:
    - src/ui/app.py

key-decisions:
  - "[05-03]: ResultPanel stores (divider, cards) tuples for clean auto-trim — allows removal of the correct divider+card group without index bookkeeping"
  - "[05-03]: MacroSandboxTab._on_save_macro() is the Save button handler — tab mediates between sidebar and editor so neither widget needs a reference to the other"
  - "[05-03]: WorkspaceManager(Path.home() / 'RollinRollin') created in MainWindow with initialize() — gives macros/ folder a real location without requiring user setup"
  - "[05-03]: QSplitter.setCollapsible(0, False) on main content — sidebar (index 1) is collapsible, main area is not"
  - "[05-03]: QTimer.singleShot(50, scroll_to_bottom) gives layout time to settle before scroll position is set"

patterns-established:
  - "Pattern: QSplitter nested (H outer, V inner) for three-zone tab layout — editor | results | sidebar"
  - "Pattern: Auto-trim widget list: store (divider_widget, [card_widgets]) tuples, pop and deleteLater() on overflow"
  - "Pattern: sidebar._save_btn.clicked connects to tab._on_save_macro — tab mediates between editor and sidebar"

requirements-completed: [SAND-01, SAND-02, SAND-03, SAND-04, SAND-05, SAND-06, SAND-07]

# Metrics
duration: 5min
completed: 2026-02-24
---

# Phase 5 Plan 03: Macro Sandbox Tab Assembly Summary

**Complete Macro Sandbox tab with collapsible ResultCards, MacroSidebar file persistence, and MacroSandboxTab orchestrating the full preprocess -> query -> execute -> display flow, wired into MainWindow as the 4th tab**

## Performance

- **Duration:** ~5 min
- **Started:** 2026-02-24T04:28:29Z
- **Completed:** 2026-02-24T04:33:00Z
- **Tasks:** 2
- **Files modified:** 4

## Accomplishments

- ResultCard: collapsible QFrame showing total (bold), error (red), warnings (orange), expandable per-die breakdown with inline roll tooltips; per-card Copy button and to_text() for clipboard
- ResultPanel: scrollable container with timestamp dividers, auto-trim to 20 roll sets (oldest deleted via deleteLater()), Copy All button, Clear button, and scroll-to-bottom after each update
- MacroSidebar: QListWidget of .md files from workspace macros/ folder; save (QInputDialog name prompt), load (double-click), delete (QMessageBox confirmation), right-click context menu
- MacroSandboxTab: horizontal+vertical QSplitter layout assembling MacroEditor, QueryPanel, ResultPanel, and MacroSidebar into a complete working tab with Roll/Clear toolbar
- MainWindow updated with WorkspaceManager(Path.home() / "RollinRollin"), initialized on startup, passed to MacroSandboxTab; 4 tabs total

## Task Commits

Each task was committed atomically:

1. **Task 1: ResultPanel + MacroSidebar widgets** - `0a31292` (feat)
2. **Task 2: MacroSandboxTab assembly + MainWindow wiring** - `bf94a74` (feat)

## Files Created/Modified

- `src/ui/macro_result_panel.py` - ResultCard (collapsible QFrame) and ResultPanel (scroll area with auto-trim)
- `src/ui/macro_sidebar.py` - MacroSidebar with save/load/delete controls and macro_loaded Signal
- `src/ui/macro_sandbox_tab.py` - MacroSandboxTab orchestrating full roll flow
- `src/ui/app.py` - MainWindow updated with WorkspaceManager and Macro Sandbox tab

## Decisions Made

- ResultPanel stores `(divider_widget, [card_widgets])` tuples for auto-trim: when roll set count exceeds 20, the oldest divider + its card list are popped and each widget receives `deleteLater()`. This avoids index arithmetic across a flat layout.
- Tab-owns-save pattern: the sidebar's Save button click signal is connected to `tab._on_save_macro`, which calls `sidebar.save_macro(editor.toPlainText())`. Neither sidebar nor editor holds a reference to the other.
- `WorkspaceManager(Path.home() / "RollinRollin")` created in MainWindow and `.initialize()` called on startup. This ensures the macros/ folder exists before MacroSandboxTab is constructed. Consistent with the workspace pattern from Plan 01.
- `QTimer.singleShot(50, _scroll_to_bottom)`: 50ms delay ensures the new widgets are laid out before the scroll position maximum is set. Avoids scrolling to stale maximum.
- Horizontal splitter: main content (index 0) is non-collapsible; sidebar (index 1) is collapsible. Prevents the user from accidentally hiding the editor+results area.

## Deviations from Plan

None - plan executed exactly as written.

## Issues Encountered

None — all PySide6 classes and widget patterns were already established in prior plans. Implementation matched the plan's layout specification directly.

## User Setup Required

None - no external service configuration required. The workspace folder `~/RollinRollin/macros/` is created automatically on first launch.

## Next Phase Readiness

- Macro Sandbox tab is fully assembled and functional
- All 7 SAND requirements now complete (SAND-01 through SAND-07)
- Phase 5 Plan 04 (end-to-end verification) can proceed — all tab components in place
- 339 tests pass, no regressions

## Self-Check: PASSED

- FOUND: src/ui/macro_result_panel.py
- FOUND: src/ui/macro_sidebar.py
- FOUND: src/ui/macro_sandbox_tab.py
- FOUND: src/ui/app.py (modified)
- FOUND commit: 0a31292 (Task 1)
- FOUND commit: bf94a74 (Task 2)
- 339 tests pass

---
*Phase: 05-roll20-macro-sandbox*
*Completed: 2026-02-24*
