---
phase: 13-output-polish-theming-and-ui
plan: "01"
subsystem: ui
tags: [theming, stylesheet, pyside6, qapplication, theme-service, dark-mode, high-contrast]

# Dependency graph
requires:
  - phase: 12-save-roller-upgrades
    provides: AppSettings model with sidebar_width and ct_send_overrides_sidebar fields (pattern for adding settings fields)
provides:
  - ThemeService class with 3 preset stylesheets (Dark, Default, High Contrast) and custom color builder
  - AppSettings theme fields (theme_name, text_color, bg_color, accent_color, sandbox_font)
  - main.py delegates to ThemeService at startup (no hardcoded stylesheet)
  - MainWindow._apply_settings() calls ThemeService.apply() for live theme switching
  - QPushButton:checked toggle highlighting in all preset stylesheets
affects:
  - 13-02 through 13-05 (all subsequent Phase 13 plans build on ThemeService and theme fields)

# Tech tracking
tech-stack:
  added: []
  patterns:
    - ThemeService as single source of truth for all app-wide stylesheets
    - QApplication.setStyleSheet() for O(1) app-wide live recolor
    - QPushButton:checked stylesheet selector drives toggle highlighting automatically (no per-widget code)

key-files:
  created:
    - src/ui/theme_service.py
  modified:
    - src/settings/models.py
    - src/main.py
    - src/ui/app.py

key-decisions:
  - "ThemeService._PRESETS maps theme_name strings to full stylesheet strings; preset selection is O(1) dict lookup"
  - "Dark theme remains default (AppSettings.theme_name = 'dark'); dark-background optimized per-widget colors already in codebase"
  - "ThemeService.apply() lazy-imports QApplication to keep ThemeService Qt-free except at apply() call time"
  - "main.py applies ThemeService.build_stylesheet(AppSettings()) at startup as flash-prevention before settings load"
  - "MainWindow stores self._theme_service instance and exposes get_theme_service() for child widget accent color access"
  - "Custom color template uses double-brace escaping ({{...}}) so .format() works without conflicting with CSS braces"

patterns-established:
  - "ThemeService pattern: pure Python stylesheet builder, Qt only in apply(); testable without QApplication"
  - "_darken/_midtone helpers: module-level functions for deriving input_bg/border from custom user colors"

requirements-completed: [THEME-01, THEME-03, UI-01]

# Metrics
duration: 4min
completed: 2026-02-26
---

# Phase 13 Plan 01: ThemeService Foundation Summary

**ThemeService with Dark/Default/High Contrast presets replaces hardcoded main.py stylesheet; QPushButton:checked toggle highlighting applies app-wide automatically**

## Performance

- **Duration:** 4 min
- **Started:** 2026-02-26T10:21:05Z
- **Completed:** 2026-02-26T10:25:22Z
- **Tasks:** 2
- **Files modified:** 4 (1 created, 3 modified)

## Accomplishments
- Created ThemeService with three full preset stylesheets (4422+ chars each) and custom color template builder
- Removed 208-line hardcoded _DARK_STYLESHEET from main.py; main.py is now a thin launcher using ThemeService
- MainWindow._apply_settings() calls ThemeService.apply(settings) for live theme switching on settings save
- QPushButton:checked and QCheckBox::indicator:checked selectors in all presets provide automatic toggle highlighting (UI-01)
- AppSettings gains 5 new theme/font fields (theme_name, text_color, bg_color, accent_color, sandbox_font) with backward-compatible defaults

## Task Commits

Each task was committed atomically:

1. **Task 1: Create ThemeService with 3 preset stylesheets and AppSettings fields** - `9dad47c` (feat)
2. **Task 2: Migrate main.py to ThemeService and wire app.py** - `ad6052b` (feat)

**Plan metadata:** (docs commit follows)

## Files Created/Modified
- `src/ui/theme_service.py` - ThemeService class with Dark, Default, High Contrast presets and custom color builder
- `src/settings/models.py` - Added theme_name, text_color, bg_color, accent_color, sandbox_font fields to AppSettings
- `src/main.py` - Removed _DARK_STYLESHEET; now uses ThemeService().build_stylesheet(AppSettings()) at startup
- `src/ui/app.py` - Added ThemeService import, self._theme_service instance, get_theme_service() method, ThemeService.apply() call in _apply_settings()

## Decisions Made
- Dark theme remains the default (theme_name="dark") since existing per-widget color hardcodes are dark-background optimized
- ThemeService.apply() uses a lazy import for QApplication to keep the class pure Python outside apply() — testable without a QApplication instance
- main.py applies the default stylesheet at startup before MainWindow loads persisted settings as flash prevention; MainWindow._apply_settings() re-applies with correct saved theme after loading
- Custom color template uses Python double-brace escaping ({{...}}) so str.format() works correctly alongside CSS rule bodies

## Deviations from Plan

None - plan executed exactly as written.

## Issues Encountered

None.

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness
- ThemeService is live and tested; all 510 existing tests pass
- AppSettings theme fields ready for Phase 13 Plan 02 (SettingsTab theming UI with dropdown and color pickers)
- get_theme_service() on MainWindow ready for Plan 05 TemplateCard accent color access
- No blockers for subsequent Phase 13 plans

---
*Phase: 13-output-polish-theming-and-ui*
*Completed: 2026-02-26*
