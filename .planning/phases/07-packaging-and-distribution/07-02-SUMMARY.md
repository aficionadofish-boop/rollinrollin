---
phase: 07-packaging-and-distribution
plan: "02"
subsystem: infra
tags: [pyinstaller, packaging, distribution, exe, windows, pyside6]

# Dependency graph
requires:
  - phase: 07-01
    provides: RollinRollin.spec, build.bat, smoke_test.py, icon.ico, version.txt

provides:
  - dist/RollinRollin.exe — portable single-file Windows application (45MB)
  - Human-verified working executable with correct metadata, icon, and functionality

affects: []

# Tech tracking
tech-stack:
  added: []
  patterns:
    - QApplication.setWindowIcon() required for taskbar/title-bar icon — PyInstaller icon= only sets Windows Explorer file icon

key-files:
  created:
    - dist/RollinRollin.exe
  modified:
    - src/main.py

key-decisions:
  - "QApplication.setWindowIcon() added in main.py with frozen/source path resolution — PyInstaller icon= parameter only sets Explorer icon, not runtime taskbar icon"
  - "Icon path resolution: sys._MEIPASS (frozen) for packaged exe, __file__-relative for dev run"

patterns-established:
  - "Taskbar icon pattern: QApplication.setWindowIcon(QIcon(icon_path)) with sys._MEIPASS guard for PyInstaller frozen apps"

requirements-completed: [WS-02, WS-03]

# Metrics
duration: 15min
completed: 2026-02-24
---

# Phase 7 Plan 02: Build Execution and Verification Summary

**45MB portable RollinRollin.exe produced by PyInstaller build pipeline — passes smoke test, human-verified with correct dice icon, windowed mode, version metadata, and full dice rolling functionality**

## Performance

- **Duration:** ~15 min
- **Started:** 2026-02-24
- **Completed:** 2026-02-24
- **Tasks:** 2 (1 auto + 1 human-verify)
- **Files modified:** 2 (dist/RollinRollin.exe, src/main.py)

## Accomplishments
- Built dist/RollinRollin.exe (45MB portable single-file executable) via build.bat
- All 375 tests passed before build (pytest fail-fast gate)
- Smoke test passed — exe launched and stayed alive for 8+ seconds
- Human verified: windowed mode (no console), dice icon in taskbar and title bar, correct version metadata (Product name, version 1.0.0.0, description), 1d20+5 dice roll works in Macro Sandbox, app closes cleanly

## Task Commits

Each task was committed atomically:

1. **Task 1: Run build and smoke test** - `9e1424e` (fix — spec SPECPATH path fix bundled in)
2. **Deviation fix: taskbar icon** - `97893d5` (fix — QApplication.setWindowIcon added to src/main.py)

**Plan metadata:** (this docs commit)

## Files Created/Modified
- `dist/RollinRollin.exe` - 45MB portable Windows application, produced by PyInstaller from source
- `src/main.py` - Added QApplication.setWindowIcon() with frozen/dev path resolution for taskbar icon

## Decisions Made
- QApplication.setWindowIcon() required for runtime taskbar/title-bar icon. PyInstaller's `icon=` parameter in the spec only affects the Windows Explorer file icon — it does not propagate to the running application's taskbar entry. Fix: detect sys._MEIPASS (frozen) vs __file__ (dev) and load the ICO at runtime.
- Icon path resolution pattern established as reusable pattern for any future bundled asset access.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] Missing taskbar/title-bar icon in packaged exe**
- **Found during:** Task 2 (Human verification of packaged application)
- **Issue:** PyInstaller icon= in spec only sets the Windows Explorer file icon. The running application had no icon in the taskbar or window title bar — it showed the default Qt window icon instead.
- **Fix:** Added `QApplication.setWindowIcon(QIcon(icon_path))` to src/main.py with sys._MEIPASS guard: uses `sys._MEIPASS / "icon.ico"` when frozen (PyInstaller), falls back to `Path(__file__).parent.parent / "build" / "icon.ico"` for dev runs.
- **Files modified:** src/main.py
- **Verification:** Human confirmed dice icon appears in taskbar and window title bar after fix.
- **Committed in:** 97893d5

---

**Total deviations:** 1 auto-fixed (Rule 1 - bug)
**Impact on plan:** Fix was necessary for correct Windows application presentation. No scope creep — icon was a stated requirement in the plan.

## Issues Encountered
- Spec file SPECPATH path resolution was fixed in Task 1 (inherited from 07-01 continuation) — SPECPATH correctly used as anchor for REPO_ROOT so build.bat works from any working directory. Committed in 9e1424e.

## User Setup Required
None - no external service configuration required. The exe is fully portable and self-contained.

## Next Phase Readiness
- Phase 7 complete — v1 shipping milestone reached
- dist/RollinRollin.exe is the deliverable: portable, offline, single-file, no Python required
- Requirements WS-02 (offline operation) and WS-03 (portable .exe) are satisfied
- No further phases planned (7 of 7 complete)

---
*Phase: 07-packaging-and-distribution*
*Completed: 2026-02-24*

## Self-Check: PASSED

- FOUND: .planning/phases/07-packaging-and-distribution/07-02-SUMMARY.md
- FOUND: commit 9e1424e (Task 1 — build and smoke test)
- FOUND: commit 97893d5 (Deviation fix — taskbar icon)
