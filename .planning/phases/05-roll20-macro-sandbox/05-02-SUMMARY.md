---
phase: 05-roll20-macro-sandbox
plan: 02
subsystem: ui
tags: [pyside6, qsyntaxhighlighter, qplaintextedit, qtimer, qwidget, signals, roll20]

# Dependency graph
requires:
  - phase: 05-01
    provides: QuerySpec from src.macro.preprocessor (used for duck-typed query list in QueryPanel)
provides:
  - MacroEditor QPlainTextEdit subclass with line number gutter, syntax highlighting, and debounce timer
  - MacroHighlighter QSyntaxHighlighter for Roll20 tokens ([[...]] blue, ?{...} orange, @{}/&{template:} red underline)
  - LineNumberArea gutter QWidget
  - QueryPanel inline QWidget for sequential ?{query} resolution — no modal dialogs
affects:
  - 05-03 (MacroSandboxTab assembles MacroEditor + QueryPanel)
  - 05-04 (end-to-end verification sees these widgets in action)

# Tech tracking
tech-stack:
  added: []  # All PySide6 classes already in project; no new pip packages
  patterns:
    - QSyntaxHighlighter subclass with _rules list of (pattern, QTextCharFormat) tuples
    - QTimer single-shot debounce connected to textChanged for full-document rehighlight
    - LineNumberArea QWidget delegating paintEvent to editor helper method
    - QStackedWidget switching between QComboBox and QLineEdit for different query types
    - answered = Signal(dict) driving sequential flow without QDialog.exec()

key-files:
  created:
    - src/ui/macro_editor.py
    - src/ui/macro_query_panel.py
  modified: []

key-decisions:
  - "QTextEdit must be imported from PySide6.QtWidgets not PySide6.QtGui (Rule 3 auto-fix)"
  - "QueryPanel uses QStackedWidget with page 0=QComboBox page 1=QLineEdit to switch input mode"
  - "QueryPanel._previous_answers persists per prompt text for session lifetime; not cleared by reset()"
  - "answered signal emits dict copy (dict(self._answers)) to prevent mutation after emission"
  - "Dropdown pre-selection restores by label text match, not by value — handles duplicate values safely"

patterns-established:
  - "Pattern: QSyntaxHighlighter subclass with _rules list — iterate patterns, call setFormat per match"
  - "Pattern: Debounce via QTimer(setSingleShot=True) + textChanged.connect(timer.start)"
  - "Pattern: Inline query panel — setVisible(True/False) driven by signals, never exec()"

requirements-completed: [SAND-01, SAND-04]

# Metrics
duration: 2min
completed: 2026-02-24
---

# Phase 5 Plan 02: MacroEditor and QueryPanel UI Widgets Summary

**MacroEditor (QPlainTextEdit with line number gutter + QSyntaxHighlighter) and QueryPanel (inline sequential query widget with Signal(dict)) built for Roll20 macro sandbox assembly**

## Performance

- **Duration:** 2 min
- **Started:** 2026-02-24T04:23:07Z
- **Completed:** 2026-02-24T04:25:31Z
- **Tasks:** 2
- **Files modified:** 2

## Accomplishments
- MacroEditor delivers a code-editor experience: monospace Courier New 10pt font, 4-space tabs, line number gutter painted by LineNumberArea, and current-line highlight
- MacroHighlighter (QSyntaxHighlighter subclass) applies token-based coloring: [[...]] blue bold, ?{...} orange, @{}/&{template:} red underline — debounced via 1.5s QTimer single-shot
- QueryPanel is a fully inline QWidget (zero QDialog.exec() calls) that presents ?{query} prompts sequentially, switching between QComboBox (dropdown) and QLineEdit (free-text) via QStackedWidget, emitting answered(dict) when complete and remembering previous answers per prompt text

## Task Commits

Each task was committed atomically:

1. **Task 1: MacroEditor with line number gutter and syntax highlighter** - `63801d5` (feat)
2. **Task 2: QueryPanel inline widget for sequential ?{query} resolution** - `15e154d` (feat)

**Plan metadata:** `4a8d813` (docs: complete plan)

## Files Created/Modified
- `src/ui/macro_editor.py` - MacroHighlighter + LineNumberArea + MacroEditor classes
- `src/ui/macro_query_panel.py` - QueryPanel inline widget with answered Signal(dict)

## Decisions Made
- `QTextEdit` is in `PySide6.QtWidgets`, not `PySide6.QtGui` — corrected import (auto-fix Rule 3)
- `QueryPanel._previous_answers` is keyed by prompt text and stores label (for dropdowns) or raw text (for free-text inputs); NOT cleared on `reset()` — session-level memory per CONTEXT.md
- `QStackedWidget` used rather than toggling visibility of two separate widgets — cleaner state management with two fixed pages

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 3 - Blocking] Fixed wrong PySide6 module for QTextEdit import**
- **Found during:** Task 1 (MacroEditor with line number gutter)
- **Issue:** Plan's import list included `QTextEdit` under `PySide6.QtGui` imports — `QTextEdit` is in `PySide6.QtWidgets`
- **Fix:** Moved `QTextEdit` to the `from PySide6.QtWidgets import ...` line
- **Files modified:** src/ui/macro_editor.py
- **Verification:** `python -c "from src.ui.macro_editor import MacroEditor, MacroHighlighter; print('OK')"` passes
- **Committed in:** 63801d5 (Task 1 commit)

---

**Total deviations:** 1 auto-fixed (1 blocking import error)
**Impact on plan:** Single import correction; no scope change.

## Issues Encountered
None beyond the import fix above.

## User Setup Required
None — no external service configuration required.

## Next Phase Readiness
- MacroEditor and QueryPanel are self-contained QWidget subclasses ready for assembly in Plan 03 (MacroSandboxTab)
- Both widgets verified to import cleanly from their modules
- No new pip packages required; all PySide6 components already in project

---
## Self-Check: PASSED

- FOUND: src/ui/macro_editor.py
- FOUND: src/ui/macro_query_panel.py
- FOUND: .planning/phases/05-roll20-macro-sandbox/05-02-SUMMARY.md
- FOUND commit: 63801d5 (Task 1)
- FOUND commit: 15e154d (Task 2)
- FOUND commit: 4a8d813 (docs/metadata)

---
*Phase: 05-roll20-macro-sandbox*
*Completed: 2026-02-24*
