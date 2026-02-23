---
phase: 02-monster-import-and-library
plan: 03
subsystem: ui
tags: [python, pyside6, qt, qabstracttablemodel, qsortfilterproxymodel, library, service]

# Dependency graph
requires:
  - phase: 02-monster-import-and-library
    plan: 01
    provides: "Extended Monster domain model with creature_type, incomplete, tags fields"

provides:
  - "MonsterLibrary: in-memory runtime store with add, replace, remove, clear, has_name, all, search, creature_types"
  - "MonsterTableModel(QAbstractTableModel): 4-column Name/CR/Type/badge table model with numeric CR sort via UserRole"
  - "MonsterFilterProxyModel(QSortFilterProxyModel): AND-logic filter across text/type/incomplete with numeric CR sort"
  - "_cr_to_float(): CR string to float converter for fraction, integer, and unknown CR values"
  - "conftest.py with session-scoped qapp fixture for Qt model tests"
  - "69 new tests (24 library service + 45 Qt model) all passing"

affects:
  - 02-04-library-tab-ui
  - 02-05-import-log-panel
  - 03-library-ui

# Tech tracking
tech-stack:
  added:
    - "PySide6 6.10.2 — Qt bindings for Python, installed for model/view layer"
  patterns:
    - "MonsterLibrary: dual-storage pattern (list for ordered iteration + dict for O(1) has_name)"
    - "Qt model: Qt.UserRole on CR column carries float sort key (_cr_to_float) for numeric comparison"
    - "QSortFilterProxyModel.invalidate() (not deprecated invalidateFilter/invalidateRowsFilter) for filter re-evaluation"
    - "conftest.py qapp fixture: session-scoped QApplication singleton shared across all Qt tests"
    - "Qt model tests isolated in test_monster_table_model.py — qapp fixture only loaded for Qt tests"

key-files:
  created:
    - "src/library/__init__.py — library package marker"
    - "src/library/service.py — MonsterLibrary with add/replace/remove/clear/has_name/all/search/creature_types"
    - "src/ui/__init__.py — ui package marker"
    - "src/ui/monster_table.py — MonsterTableModel + _cr_to_float helper"
    - "src/ui/monster_filter.py — MonsterFilterProxyModel with AND-logic filter"
    - "src/tests/conftest.py — session-scoped qapp fixture for Qt model tests"
    - "src/tests/test_library_service.py — 24 unit tests for MonsterLibrary"
    - "src/tests/test_monster_table_model.py — 45 tests for MonsterTableModel and MonsterFilterProxyModel"
  modified: []

key-decisions:
  - "MonsterLibrary dual-storage: list[Monster] for ordered iteration, dict[str, int] for O(1) has_name lookup; list is ground truth, dict is index cache"
  - "QSortFilterProxyModel.invalidate() used instead of invalidateFilter() or invalidateRowsFilter() — both are deprecated in PySide6 6.10; invalidate() resets both sort and filter caches cleanly"
  - "_cr_to_float returns -1.0 for unknown/empty/dash CR values — sorts to top of ascending list for easy identification of incomplete entries"
  - "filterAcceptsRow uses filterRegularExpression().pattern() as raw text string for AND-logic (not regex matching) to avoid regex special-character issues in monster names"

patterns-established:
  - "Library service: pure stdlib + domain imports only — no Qt at service layer"
  - "Qt model tests: session-scoped qapp fixture in conftest.py; tests isolated to test_monster_table_model.py"
  - "CR sort: MonsterTableModel.data(index, Qt.UserRole) on CR column returns float — proxy setSortRole(Qt.UserRole) makes sort numeric"

requirements-completed: [LIB-01, LIB-02, LIB-03, LIB-05, LIB-06]

# Metrics
duration: 5min
completed: 2026-02-23
---

# Phase 2 Plan 03: Library Service and Qt Model/View Layer Summary

**MonsterLibrary in-memory store with O(1) name lookup, plus MonsterTableModel and MonsterFilterProxyModel delivering 4-column display with numeric CR sort and AND-logic text/type/incomplete filtering**

## Performance

- **Duration:** 5 min
- **Started:** 2026-02-23T22:36:36Z
- **Completed:** 2026-02-23T22:41:25Z
- **Tasks:** 2
- **Files modified:** 8

## Accomplishments

- Implemented MonsterLibrary service (pure Python, no Qt) with dual list+dict storage for ordered iteration and O(1) has_name; covers add, replace, remove, clear, search (case-insensitive substring across name/cr/type), creature_types
- Implemented MonsterTableModel as QAbstractTableModel with 4 columns (Name/CR/Type/badge), Qt.UserRole on CR column carrying _cr_to_float() float for numeric proxy sort, and reset_monsters() with proper beginResetModel/endResetModel
- Implemented MonsterFilterProxyModel with AND-logic across text search, type equality filter, and incomplete-only toggle; setSortRole(Qt.UserRole) enables numeric CR sort (10 after 2, 1/2 = 0.5)
- 69 new tests added (24 library service + 10 _cr_to_float + 35 Qt model); full suite is 232 tests all green

## Task Commits

Each task was committed atomically:

1. **Task 1: MonsterLibrary Service** - `fdbfe9d` (feat)
2. **Task 2: MonsterTableModel + MonsterFilterProxyModel** - `3ce20cf` (feat)

## Files Created/Modified

- `src/library/__init__.py` — library package marker
- `src/library/service.py` — MonsterLibrary: add/replace/remove/clear/has_name/all/search/creature_types
- `src/ui/__init__.py` — ui package marker
- `src/ui/monster_table.py` — MonsterTableModel(QAbstractTableModel) + _cr_to_float(), COLUMNS constant
- `src/ui/monster_filter.py` — MonsterFilterProxyModel(QSortFilterProxyModel) with AND-logic filterAcceptsRow
- `src/tests/conftest.py` — session-scoped qapp fixture for Qt test isolation
- `src/tests/test_library_service.py` — 24 unit tests for MonsterLibrary (add/replace/remove/clear/search/creature_types)
- `src/tests/test_monster_table_model.py` — 45 tests: _cr_to_float, MonsterTableModel data/header/reset, MonsterFilterProxyModel text/type/incomplete/AND filters, CR sort order

## Decisions Made

- MonsterLibrary dual-storage (list + dict): list is the source of truth for ordered all() and search(); dict maps name to index for O(1) has_name; dict rebuilt on remove() since indices shift
- Used QSortFilterProxyModel.invalidate() instead of invalidateFilter() or invalidateRowsFilter() — both are marked deprecated in PySide6 6.10.2; invalidate() is the correct non-deprecated replacement that clears both sort and filter caches
- _cr_to_float returns -1.0 for unknown/empty/dash CR values so they sort to the top in ascending order — easy visual flag for DMs reviewing incomplete entries
- filterAcceptsRow reads filterRegularExpression().pattern() as a plain string for substring matching rather than applying it as a regex — avoids issues with regex metacharacters in monster names like "Tiamat (Form 1/2/3)"

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] Replaced deprecated invalidateFilter()/invalidateRowsFilter() with invalidate()**
- **Found during:** Task 2 (MonsterFilterProxyModel implementation + testing)
- **Issue:** Plan specified invalidateFilter() which is marked deprecated in PySide6 6.10.2; invalidateRowsFilter() (attempted substitute) is also deprecated; DeprecationWarnings appeared in test output
- **Fix:** Replaced both calls with invalidate() which is not deprecated and correctly resets both sort and filter state
- **Files modified:** src/ui/monster_filter.py
- **Verification:** python -m pytest src/tests/test_monster_table_model.py -v passes 45 tests with zero warnings
- **Committed in:** 3ce20cf (Task 2 commit)

**2. [Rule 3 - Blocking] Installed PySide6 6.10.2 (not yet in requirements-dev.txt)**
- **Found during:** Task 2 (MonsterTableModel imports fail without PySide6)
- **Issue:** PySide6 was not installed in the Python environment; conftest.py import failed with ModuleNotFoundError
- **Fix:** pip install PySide6 (installed 6.10.2, matching the project's target version documented in STATE.md decisions)
- **Files modified:** none (runtime install, not committed to requirements-dev.txt as that is pre-existing and out of scope for this task)
- **Verification:** All Qt imports succeed; 45 model tests pass
- **Committed in:** 3ce20cf (Task 2 commit)

---

**Total deviations:** 2 auto-fixed (1 deprecated API fix, 1 blocking dependency install)
**Impact on plan:** Both fixes essential for correctness and operation. No scope creep.

## Issues Encountered

- PySide6 was not pre-installed; discovered when conftest.py import failed. Installed PySide6 6.10.2 (project's documented target version) via pip. No code changes needed.

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness

- MonsterLibrary service ready for use by LibraryTab (Plan 04) and import workflow (Plan 05)
- MonsterTableModel + MonsterFilterProxyModel ready to be assembled into LibraryTab QTableView
- creature_types() ready to populate the type-filter QComboBox
- monster_at(row) ready for LibraryTab to retrieve selected Monster on row click
- All 232 tests green; no blockers

---
*Phase: 02-monster-import-and-library*
*Completed: 2026-02-23*

## Self-Check: PASSED

All created files found on disk. All task commits verified in git log.

| Item | Status |
|------|--------|
| src/library/__init__.py | FOUND |
| src/library/service.py | FOUND |
| src/ui/__init__.py | FOUND |
| src/ui/monster_table.py | FOUND |
| src/ui/monster_filter.py | FOUND |
| src/tests/conftest.py | FOUND |
| src/tests/test_library_service.py | FOUND |
| src/tests/test_monster_table_model.py | FOUND |
| .planning/phases/02-monster-import-and-library/02-03-SUMMARY.md | FOUND |
| Commit fdbfe9d (Task 1) | FOUND |
| Commit 3ce20cf (Task 2) | FOUND |
