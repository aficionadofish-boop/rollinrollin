---
phase: 07-packaging-and-distribution
plan: 01
subsystem: infra
tags: [pyinstaller, pillow, packaging, windows, ico, versioninfo]

# Dependency graph
requires:
  - phase: 06-settings
    provides: Complete application with AppSettings, SettingsService, SettingsTab — ready to package
provides:
  - build/make_icon.py: Pillow script generating multi-resolution dice-themed ICO
  - build/icon.ico: 10.9KB committed multi-resolution ICO (16/32/48/64/128/256px)
  - build/version.txt: Windows VERSIONINFO v1.0.0.0 with RollinRollin product metadata
  - build/RollinRollin.spec: PyInstaller onefile+windowed spec with Qt excludes
  - build.bat: Fail-fast one-command build (pytest then pyinstaller)
  - smoke_test.py: Post-build exe launcher that verifies 8s alive check
affects: [07-02-execute-build]

# Tech tracking
tech-stack:
  added: [PyInstaller 6.19.0, Pillow 12.1.1]
  patterns: [committed ICO artifact generated from committed script, fail-fast build pipeline, separated smoke test from build script]

key-files:
  created:
    - build/make_icon.py
    - build/icon.ico
    - build/version.txt
    - build/RollinRollin.spec
    - build.bat
    - smoke_test.py
  modified:
    - .gitignore

key-decisions:
  - "Pillow saves ICO using sizes= parameter (resizes master 256px image to each target size) — append_images= does not produce multi-resolution ICO in Pillow 12.x"
  - "build.bat assumes venv already activated — does not set up venv or install dependencies (developer concern, not build concern)"
  - "smoke_test.py checks alive-after-8s only — no window title or tab verification (no pywinauto dependency)"
  - "dist/ and build/work/ gitignored; build assets (icon.ico, version.txt, spec) committed to repo for reproducible builds"

patterns-established:
  - "Build infrastructure in build/ subdirectory, build scripts at repo root"
  - "Fail-fast build script: run tests first, abort on failure before packaging"

requirements-completed: [WS-02, WS-03]

# Metrics
duration: 5min
completed: 2026-02-24
---

# Phase 7 Plan 01: Build Infrastructure Summary

**PyInstaller 6.19.0 onefile+windowed build pipeline with Pillow-generated dice ICO, Windows VERSIONINFO v1.0.0, Qt module exclusions, and fail-fast build.bat**

## Performance

- **Duration:** 5 min
- **Started:** 2026-02-24T07:35:13Z
- **Completed:** 2026-02-24T07:40:34Z
- **Tasks:** 2
- **Files modified:** 7 (6 created, 1 updated)

## Accomplishments
- Generated multi-resolution dice-themed ICO (6 sizes: 16/32/48/64/128/256px, 10.9KB) using Pillow
- Created Windows VERSIONINFO resource with RollinRollin v1.0.0.0 product metadata
- Wrote PyInstaller spec with onefile+windowed mode, pathex=[.], full Qt excludes list, icon and version wired
- Created fail-fast build.bat (pytest then pyinstaller, abort on error) and standalone smoke_test.py

## Task Commits

Each task was committed atomically:

1. **Task 1: Generate dice icon and Windows version resource** - `358b721` (feat)
2. **Task 2: Create PyInstaller spec, build script, smoke test, update .gitignore** - `87b2c8c` (feat)

**Plan metadata:** (docs commit follows)

## Files Created/Modified
- `build/make_icon.py` - Pillow script: draws d6 face (dark blue body, 6 pip circles, rounded rect), saves multi-res ICO
- `build/icon.ico` - 10.9KB committed multi-resolution ICO (16/32/48/64/128/256px, 6 frames in header)
- `build/version.txt` - Windows VERSIONINFO Python-syntax resource for PyInstaller, RollinRollin v1.0.0.0
- `build/RollinRollin.spec` - PyInstaller spec: Analysis pathex=[.], 27 Qt excludes, onefile console=False, icon+version wired
- `build.bat` - Batch build script: pytest -q then pyinstaller --noconfirm, exit /b 1 on any failure
- `smoke_test.py` - Launches dist/RollinRollin.exe via subprocess.Popen, waits 8s, checks proc.poll() is None
- `.gitignore` - Added dist/, build/work/, __pycache__/, *.pyc; excludes build outputs, keeps build assets

## Decisions Made
- **Pillow ICO save method:** `sizes=` parameter resizes master 256px image to each target size. `append_images=` does NOT produce multi-resolution ICO in Pillow 12.x — it only creates a single-frame file. Found during Task 1 debugging (auto-fixed inline, no deviation from plan intent).
- **build.bat venv scope:** Script assumes activated venv. No venv setup in build.bat — developer responsibility, not packaging responsibility. Keeps build.bat simple and avoids hardcoded paths.
- **smoke_test.py depth:** Alive-after-8s check only. No window title/tab verification — would require pywinauto which is out of scope.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] Fixed Pillow ICO multi-resolution save — wrong API call**
- **Found during:** Task 1 (icon generation)
- **Issue:** Initial implementation used `append_images=images[1:]` with explicit sizes. In Pillow 12.x, `append_images=` with `save()` does not produce a multi-resolution ICO — it creates a single-frame 16x16 file (169 bytes). The `sizes=` parameter is the correct approach: Pillow resizes the master image to each requested size.
- **Fix:** Updated `make_icon.py` to save with `sizes=[(s,s) for s in sizes]` from a single 256px master image. Verified: 10.9KB output, ICO header count=6 confirmed via binary inspection.
- **Files modified:** build/make_icon.py
- **Verification:** `python build/make_icon.py` outputs 10.9KB file; ICO header `count=6`
- **Committed in:** 358b721 (Task 1 commit)

---

**Total deviations:** 1 auto-fixed (Rule 1 - bug in Pillow API usage)
**Impact on plan:** Fix required for correct multi-resolution ICO output. No scope creep.

## Issues Encountered
- Pillow 12.x ICO save behavior differs from older docs/examples. `append_images` does not work for multi-resolution ICO; `sizes=` is the correct parameter. Resolved inline.

## User Setup Required
None - no external service configuration required.

## Next Phase Readiness
- All build infrastructure complete and committed — Plan 02 can execute `build.bat` immediately
- PyInstaller 6.19.0 installed in current venv
- Antivirus false positive risk acknowledged (documented in STATE.md blocker) — test on dev machine during Plan 02

---
*Phase: 07-packaging-and-distribution*
*Completed: 2026-02-24*
