---
phase: 13-output-polish-theming-and-ui
plan: "04"
subsystem: ui
tags: [theming, qcolordialog, qcombobox, pyside6, settings-tab, sandbox-font, font-picker, live-preview]

# Dependency graph
requires:
  - phase: 13-output-polish-theming-and-ui
    plan: "01"
    provides: ThemeService with 3 preset stylesheets and AppSettings theme fields (theme_name, text_color, bg_color, accent_color, sandbox_font)
provides:
  - SettingsTab Theming group with preset dropdown (Dark/Default/High Contrast) and 3 live color picker buttons
  - Theme switching via dropdown applies immediately via ThemeService.apply() — no Apply button needed
  - Custom text/bg/accent color overrides via QColorDialog; per-channel override with preset fallback
  - Reset to Preset button clears all custom colors and reapplies preset
  - Sandbox font dropdown (installed-only filter from 5-font curated list) in Theming group
  - MacroSandboxTab.set_sandbox_font() applies chosen font to MacroEditor with fallback chain
  - app.py _apply_settings() calls set_sandbox_font() on settings save
affects:
  - settings persistence (sandbox_font and theme fields persisted via AppSettings save pipeline)

# Tech tracking
tech-stack:
  added: []
  patterns:
    - Live theme preview without Apply button: _on_theme_changed() calls ThemeService.apply() immediately
    - Per-channel custom color override: empty string = use preset default; non-empty = user override
    - Color button as visual swatch: setStyleSheet(background-color) shows effective color; contrast() picks readable label color
    - Installed-font filter: QFontDatabase.families() at init; only show what the OS has
    - Fallback font chain: family -> Consolas -> Courier New -> generic Monospace hint

key-files:
  created: []
  modified:
    - src/ui/settings_tab.py
    - src/ui/macro_sandbox_tab.py
    - src/ui/app.py

key-decisions:
  - "Theme dropdown clearing custom colors on preset switch is intentional clean-slate behavior — prevents stale overrides from prior preset bleeding into new one"
  - "Color picker buttons styled as swatches (background-color + contrast label) rather than icon squares — simpler, works across all themes"
  - "Sandbox font stored in Theming group (not a separate group) to keep theming controls together"
  - "Font applied on save, not live — MacroEditor is in a different tab and cross-tab live font preview adds complexity for minimal benefit"
  - "blockSignals(True) on theme combo during apply_settings() to prevent _on_theme_changed() from clearing saved custom colors on load"

patterns-established:
  - "Color button swatch: btn.setStyleSheet(background-color: {hex}; color: {contrast}) for live color preview without icons"
  - "Theme name -> index mapping via dict {dark:0, default:1, high_contrast:2} for deterministic combo sync"

requirements-completed: [THEME-02, THEME-04]

# Metrics
duration: 3min
completed: 2026-02-26
---

# Phase 13 Plan 04: Settings Tab Theming Controls Summary

**Live theme preset switching (Dark/Default/High Contrast) and per-channel color pickers in SettingsTab; sandbox font selector wired to MacroEditor with installed-font filtering**

## Performance

- **Duration:** 3 min
- **Started:** 2026-02-26T10:29:30Z
- **Completed:** 2026-02-26T10:32:19Z
- **Tasks:** 2
- **Files modified:** 3

## Accomplishments
- Added Theming QGroupBox to SettingsTab with preset dropdown (3 options) and 3 color picker buttons (Text, Background, Accent)
- Theme changes via dropdown apply immediately via ThemeService.apply() — no Apply button required
- Custom color buttons show current effective color as a visual swatch; Reset to Preset clears all overrides
- Sandbox font dropdown filters to installed fonts from curated 5-font list (Consolas, Cascadia Code, Courier New, Lucida Console, Cascadia Mono)
- MacroSandboxTab.set_sandbox_font() applies chosen font to MacroEditor with fallback chain; applied on save via app.py _apply_settings()

## Task Commits

Each task was committed atomically:

1. **Task 1: Add Theming group with preset dropdown and color pickers** - `59f6c08` (feat)
2. **Task 2: Add Sandbox Font selector and wire to MacroEditor** - `899ac6a` (feat)

**Plan metadata:** (docs commit follows)

## Files Created/Modified
- `src/ui/settings_tab.py` - Theming QGroupBox with preset dropdown, 3 color pickers, reset button, sandbox font dropdown; apply_settings/current_settings updated with theme and font fields
- `src/ui/macro_sandbox_tab.py` - Added set_sandbox_font() public method with fallback chain
- `src/ui/app.py` - _apply_settings() calls self._macro_tab.set_sandbox_font(settings.sandbox_font)

## Decisions Made
- Theme preset dropdown clears custom colors on switch (clean-slate behavior) — prevents stale per-channel overrides from a prior preset persisting into the new one
- Color picker buttons styled as color swatches (background-color CSS) rather than icon-based approach — simpler, theme-agnostic, immediately obvious to DM
- Sandbox font placed in the Theming group rather than a separate group — keeps all visual appearance controls together in one section
- Font applied on Settings save (not live) — MacroEditor is in a separate tab; live cross-tab font preview would add complex cross-widget coupling for marginal benefit
- `blockSignals(True)` on theme combo during `apply_settings()` prevents `_on_theme_changed()` from clearing saved custom colors when restoring persisted settings

## Deviations from Plan

None - plan executed exactly as written.

## Issues Encountered

None.

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness
- SettingsTab theming controls complete; theme fields (theme_name, text_color, bg_color, accent_color, sandbox_font) fully wired into the AppSettings save/load pipeline
- Plan 05 (TemplateCard accent color) can use get_theme_service() already available on MainWindow
- All 510 existing tests pass

---
*Phase: 13-output-polish-theming-and-ui*
*Completed: 2026-02-26*
