---
phase: 02-monster-import-and-library
plan: 04
subsystem: ui
tags: [python, pyside6, qt, library-tab, import, monster-detail, import-log]

# Dependency graph
requires:
  - phase: 02-monster-import-and-library
    plan: 02
    provides: "Multi-format statblock parser (5etools, Homebrewery, plain)"
  - phase: 02-monster-import-and-library
    plan: 03
    provides: "MonsterLibrary service, MonsterTableModel, MonsterFilterProxyModel"

provides:
  - "MonsterLibraryTab(QWidget): main library tab with toolbar, splitter layout, import, search/filter/sort"
  - "MonsterDetailPanel(QWidget): full statblock display with toggle-collapsible lore (QPushButton + QTextEdit, markdown stripped) and editable tags"
  - "ImportLogPanel(QTextEdit): scrollable per-file import result log panel"
  - "set_complete_only(bool) added to MonsterFilterProxyModel (complete-only filter)"
  - "Bug fixes: column sorting for all columns, incomplete detection for files missing AC/HP/CR, lore section UX"

affects:
  - 02-05-import-pipeline
  - 03-library-ui
  - main-window-assembly

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "QPushButton toggle + QTextEdit(setVisible): correct hide/show for lore section (replaces QGroupBox checkable which only greys, not hides)"
    - "_strip_markdown() strips ## headings and ***bold***/*italic* before display in QTextEdit"
    - "blockSignals(True/False) guard on tags QLineEdit to prevent spurious monster.tags mutation on show_monster()"
    - "QMenu attached to QPushButton via setMenu() for Import dropdown"
    - "set_complete_only/set_incomplete_only: mutually exclusive proxy filter flags"
    - "_clear_actions_layout: standard Qt clear pattern (takeAt + deleteLater) to rebuild actions section"
    - "Qt.UserRole for all table columns: non-None sortable value required for QSortFilterProxyModel.lessThan() to work"
    - "Format detection by structural marker (>## heading) not field presence (**Armor Class** line)"

key-files:
  created:
    - "src/ui/import_log.py — ImportLogPanel(QTextEdit): log(), log_result(), clear_log()"
    - "src/ui/monster_detail.py — MonsterDetailPanel(QWidget): show_monster(), clear(), toggle lore (hidden by default), tags editor, _strip_markdown()"
    - "src/ui/library_tab.py — MonsterLibraryTab(QWidget): full integration of parser + library + table + detail + log"
  modified:
    - "src/ui/monster_filter.py — added set_complete_only(bool) and _complete_only flag to filterAcceptsRow"
    - "src/ui/monster_table.py — Qt.UserRole returns sortable value for all columns (name.lower, cr float, type.lower, badge int)"
    - "src/parser/statblock_parser.py — format detection uses structural markers (>## heading) not field presence"
    - "src/tests/test_monster_table_model.py — updated test for col0 UserRole; added name sort tests"
    - "src/tests/test_parser_dispatch.py — added incomplete file detection and end-to-end incomplete=True tests"

key-decisions:
  - "QGroupBox checkable/checked=False for collapsible lore: no custom animation needed; Qt native toggle is idiomatic and accessible"
  - "blockSignals guard on tags QLineEdit: prevents _on_tags_changed firing with stale text when show_monster() updates the field to a new monster's tags"
  - "set_complete_only and set_incomplete_only are mutually exclusive: setting one clears the other in MonsterFilterProxyModel to maintain simple AND-logic invariant"
  - "_modifier_str uses Python // operator (floors toward negative infinity) for D&D 5e accuracy: score 9 -> modifier -1, not 0"
  - "QPushButton toggle for lore: setVisible(False/True) gives true hide/show; QGroupBox setChecked(False) only greys out"
  - "Fivetools format detected by >## heading not **Armor Class** — allows detection of incomplete monsters missing AC/HP/CR"
  - "UserRole returns sortable value for ALL columns: name.lower() for col0, _cr_to_float for col1, type.lower() for col2"
  - "Qt ampersand escaping: '&&' in button text displays literal '&' (avoids 'Lore_Description' underscore artifact)"

patterns-established:
  - "Import pipeline: parse_file() -> duplicate check -> library.add/replace -> ImportResult.from_parse_result() -> log_result()"
  - "Type combo refresh: blockSignals + clear + repopulate + restore selection — prevents spurious filter signal during repopulation"
  - "Toggle-hide pattern: QPushButton.clicked -> setVisible(!visible) + update button text with +/- prefix"
  - "Sortable proxy model: ALL columns must return a non-None value at Qt.UserRole when setSortRole(Qt.UserRole) is set"
  - "Format detection: use unambiguous structural markers (>## heading, ___ + ## heading) not field presence"

requirements-completed: [IMPORT-01, IMPORT-02, IMPORT-03, IMPORT-04, IMPORT-05, LIB-02, LIB-03, LIB-04, LIB-05, LIB-06]

# Metrics
duration: 17min
completed: 2026-02-24
---

# Phase 2 Plan 04: Library Tab UI Summary

**MonsterLibraryTab integrating 3-format parser, MonsterLibrary service, and Qt model/view into a full DM-facing library tab with import toolbar, sortable table, detail panel with toggle-collapsible lore (markdown stripped), and scrollable import log — completed with three bug fixes from human verification**

## Performance

- **Duration:** 17 min total (2 min Tasks 1-2 on 2026-02-23 + 15 min Task 3 bug fixes on 2026-02-24)
- **Started:** 2026-02-23T22:44:46Z
- **Completed:** 2026-02-24
- **Tasks:** 3 of 3 complete
- **Files modified:** 8

## Accomplishments

- Implemented ImportLogPanel as a read-only QTextEdit with log_result() that formats per-file import summaries
- Implemented MonsterDetailPanel with scroll area, stats grid (AC/HP/CR/Type), ability scores row (all 6 with modifiers), saving throws, dynamic action rows (Roll button for parsed attacks, raw text for unparsed), editable tags QLineEdit with blockSignals guard, and toggle-collapsible lore section
- Implemented MonsterLibraryTab integrating all components: Import toolbar with File(s)/Folder QMenu, search bar, type combo, incomplete/complete combo, QTableView with sorting, QSplitter layout, selection change -> detail panel
- Fixed column sorting: all columns return Qt.UserRole sortable data (name.lower for col 0, cr float for col 1, type.lower for col 2)
- Fixed incomplete detection: fivetools/homebrewery format detected by structural markers not field presence
- Fixed lore section: QPushButton toggle + QTextEdit (hidden by default), correct label escaping, markdown stripped
- 237 tests passing (5 new tests added for bug fixes)

## Task Commits

1. **Task 1: ImportLogPanel + MonsterDetailPanel** - `5912d2a` (feat)
2. **Task 2: MonsterLibraryTab Full Integration** - `8460905` (feat)
3. **BUG 1: Column sorting** - `b101be3` (fix)
4. **BUG 2: Incomplete detection** - `96468bd` (fix)
5. **BUG 3: Lore section** - `1a5d33c` (fix)

## Files Created/Modified

- `src/ui/import_log.py` — ImportLogPanel(QTextEdit): log(), log_result(), clear_log()
- `src/ui/monster_detail.py` — MonsterDetailPanel: toggle lore (QPushButton + hidden QTextEdit), _strip_markdown()
- `src/ui/library_tab.py` — MonsterLibraryTab: full integration tab
- `src/ui/monster_filter.py` — added set_complete_only(bool) and _complete_only filterAcceptsRow check
- `src/ui/monster_table.py` — Qt.UserRole returns sortable value for all columns
- `src/parser/statblock_parser.py` — format detection uses structural markers (>## heading) not field presence
- `src/tests/test_monster_table_model.py` — updated test for col0 UserRole; added name sort tests
- `src/tests/test_parser_dispatch.py` — added incomplete file detection and end-to-end incomplete=True tests

## Decisions Made

- QGroupBox with setCheckable(True)/setChecked(False): idiomatic Qt pattern used initially; replaced by QPushButton+QTextEdit after human verification confirmed it only greys content, not hides it
- blockSignals guard on tags QLineEdit prevents spurious monster.tags mutation when show_monster() replaces the field text
- set_complete_only and set_incomplete_only are mutually exclusive flags in MonsterFilterProxyModel
- _modifier_str(score) uses score // 2 (not int(score/2)) for negative scores: Python // floors toward -inf matching D&D convention
- Fivetools format detected by >## heading (unambiguous blockquote marker per STATE.md decision) not **Armor Class** presence

## Deviations from Plan

### Auto-fixed Issues (Tasks 1-2, prior session)

**1. [Rule 2 - Missing functionality] Added set_complete_only() to MonsterFilterProxyModel**
- **Found during:** Task 2 (MonsterLibraryTab implementation)
- **Issue:** Plan specified "Complete only" combo option; set_complete_only() was needed but not yet in the proxy
- **Fix:** Added set_complete_only(bool) with mutual exclusion guard and _complete_only filter check
- **Files modified:** src/ui/monster_filter.py
- **Committed in:** 8460905 (Task 2)

### Auto-fixed Issues (Task 3 — bug fixes from human verification)

**2. [Rule 1 - Bug] Column sorting broken — Qt.UserRole returned None for col 0**
- **Found during:** Task 3 (human verification check 6)
- **Issue:** MonsterTableModel.data() returned None for Qt.UserRole on Name and Type columns; QSortFilterProxyModel.lessThan() compared None vs None, producing no sort effect
- **Fix:** Added UserRole returns for all columns: name.lower() col 0, type.lower() col 2, int(incomplete) col 3
- **Files modified:** src/ui/monster_table.py, src/tests/test_monster_table_model.py
- **Committed in:** b101be3

**3. [Rule 1 - Bug] Incomplete detection failed for files missing AC/HP/CR**
- **Found during:** Task 3 (human verification check 7)
- **Issue:** detect_format() used **Armor Class** as fivetools signal; files without AC fell through to 'unknown', returning 0 monsters instead of 1 incomplete monster
- **Fix:** Changed fivetools detection to >## heading; homebrewery to ___ + ## heading
- **Files modified:** src/parser/statblock_parser.py, src/tests/test_parser_dispatch.py
- **Committed in:** 96468bd

**4. [Rule 1 - Bug] Lore section visible/expanded by default with wrong label and raw markdown**
- **Found during:** Task 3 (human verification check 8)
- **Issue:** QGroupBox setChecked(False) only greys content, does not hide it. Label "Lore_Description" was Qt rendering & as accelerator prefix (D underlined). Raw ## Medusa heading visible in text
- **Fix:** QPushButton toggle + QTextEdit setVisible(False). Added _strip_markdown(). Button uses && for literal &
- **Files modified:** src/ui/monster_detail.py
- **Committed in:** 1a5d33c

---

**Total deviations:** 4 auto-fixed (1 missing method + 3 Rule 1 bugs)
**Impact on plan:** All fixes necessary for correct UX. No scope creep.

## Issues Encountered

None blocking — all bugs had clear root causes. The QGroupBox checkable behavior is a common Qt misconception (checked=False greys but does not hide).

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness

- MonsterLibraryTab ready for integration into main application window (Phase 3)
- All import behaviors functional: File(s), Folder, duplicate dialog, log panel
- Search/filter/sort all working: text search, type filter, incomplete/complete filter, Name A-Z sort, CR numeric sort
- Detail panel shows full statblock with toggle lore (hidden by default, markdown stripped) and editable tags
- All 237 tests green; no blockers

---
*Phase: 02-monster-import-and-library*
*Completed: 2026-02-24*

## Self-Check: PASSED

All created/modified files found on disk. All task commits verified in git log.

| Item | Status |
|------|--------|
| src/ui/import_log.py | FOUND |
| src/ui/monster_detail.py | FOUND |
| src/ui/library_tab.py | FOUND |
| src/ui/monster_filter.py | FOUND |
| src/ui/monster_table.py | FOUND |
| src/parser/statblock_parser.py | FOUND |
| src/tests/test_monster_table_model.py | FOUND |
| src/tests/test_parser_dispatch.py | FOUND |
| .planning/phases/02-monster-import-and-library/02-04-SUMMARY.md | FOUND |
| Commit 5912d2a (Task 1) | FOUND |
| Commit 8460905 (Task 2) | FOUND |
| Commit b101be3 (BUG 1 - sorting) | FOUND |
| Commit 96468bd (BUG 2 - incomplete) | FOUND |
| Commit 1a5d33c (BUG 3 - lore) | FOUND |
