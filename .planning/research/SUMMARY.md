# Project Research Summary

**Project:** RollinRollin v2.0 Combat Manager
**Domain:** Python desktop app — D&D 5e combat tool (PySide6, Windows, standalone .exe)
**Researched:** 2026-02-25
**Confidence:** HIGH

## Executive Summary

RollinRollin v2.0 adds a full combat loop to a validated v1.0 foundation: a Monster Editor with equipment presets, a persistent encounter sidebar, a combat initiative tracker with HP and condition tracking, Save Roller upgrades with auto-detection of monster traits, and Roll20 template card rendering. The overriding constraint is a portable, offline-first Windows .exe — every technology and architectural decision must preserve this. The research confirms that zero new pip dependencies are required for any v2.0 feature. The existing PySide6 + stdlib stack handles everything: QProgressBar for HP bars, QTextEdit for template cards, QSS template strings for theming, and plain JSON files for persistence. The existing `SettingsService` JSON pattern is the only persistence model needed.

The recommended architecture keeps the existing strict layering (engine/domain/service/view) and introduces three new service-layer packages: `monster_math/` (pure Python recalculation), `combat/` (in-memory combatant state), and `persistence/` (JSON I/O). A `QDockWidget` in the `RightDockWidgetArea` of `QMainWindow` is the correct mechanism for the persistent encounter sidebar — this is not achievable with a tab-embedded widget. Cross-tab communication must continue to route through `MainWindow` signals; no tab should hold a direct reference to another tab or to the sidebar. The feature dependency graph is clear: persistence is the foundation, the Monster Editor and Encounter Sidebar can be built in parallel once persistence exists, and the Combat Tracker depends on both.

The top risks are: orphaned `Monster` object references if encounters store objects instead of name strings into the persistent format; infinite recalculation signal loops in the Monster Editor if `QSpinBox.valueChanged` is not guarded with `blockSignals()`; and combat tracker state drift if HP lives in widget values rather than a backing `CombatantState` service. All three are entirely avoidable with known patterns already documented in the codebase. A secondary risk is QSS theming failing to refresh existing widgets — requires an audit of all `widget.setStyleSheet()` color calls before the theming phase.

## Key Findings

### Recommended Stack

The v2.0 stack requires no new pip installs. All feature areas are served by the existing PySide6 6.10.2 install and Python 3.12 stdlib. The `QWebEngineView` widget was considered for template rendering and explicitly rejected — it adds 130-150MB to the PyInstaller bundle, violating the portable .exe constraint. Qt's built-in HTML4 subset via `QTextEdit.setHtml()` renders the Roll20 default template card (a two-column header/value table) without any browser engine. Third-party serialization libraries (pydantic, msgspec) and theme libraries (qt-material, qdarktheme) are similarly rejected as unnecessary complexity with zero benefit at this codebase scale.

**Core technologies:**
- `PySide6 6.10.2` (existing): All UI — QProgressBar HP bars, QFrame condition badges, QTextEdit template cards, QDockWidget persistent sidebar, QSS application theming
- `stdlib json + dataclasses` (existing pattern): Persistence for monster overrides, combat state, themes — mirrors the validated `SettingsService` pattern exactly
- `Pure Python` (`src/monster_math/engine.py`, NEW): D&D 5e derived value recalculation — ability modifiers, proficiency bonus by CR, AC formulas, attack bonuses, save bonuses
- `PyInstaller 6.19.0` (existing): Windows .exe packaging — spec file must NOT import `QtWebEngineWidgets`
- `pytest >= 8.0` (existing): Test coverage for `MonsterMathEngine` and `CombatTrackerService` — both are pure Python and fully testable without a QApplication

**What NOT to add:** QWebEngineView, qt-material, qdarktheme, pydantic, SQLite, any ORM.

### Expected Features

**Must have for v2.0 launch (P1):**
- Data persistence (JSON store) — all other v2.0 features depend on it; build first
- Monster Editor: edit all core stat block fields with cascading recalculation on stat change
- Equipment presets: +0 to +3 weapon bonus, all 14 armor types, shield toggle, auto-AC formula
- Persistent Encounter Sidebar: visible across Library, Attack, and Saves tabs via QDockWidget
- Combat Tracker: sorted combatant list, HP bars, round counter, turn cycling, initiative entry
- Condition tracking: per-combatant condition badges with round countdown
- Save Roller subset selection: checkboxes from sidebar encounter
- Feature detection: Magic Resistance and Legendary Resistance auto-detected from parsed traits

**Should have — add when core is working (P2):**
- Roll20 template card rendering — extends existing Macro Sandbox; non-blocking
- Theming system: color pairs, high-contrast mode, font selection via QSS templates
- Color-coded attack output: damage type coloring via `append_html()` on RollOutputPanel
- Grouped initiative mode in Combat Tracker
- PC subtab in Combat Tracker
- Combat Tracker to Saves tab bridge signal

**Defer to v2.1+:**
- Diff view (modified vs imported baseline monster)
- Multi-template rendering in a single macro
- Auto-decrement conditions on turn advance (ambiguous "whose turn?" semantics)
- End-of-turn save prompts, concentration tracking (high coupling, low payoff)

**Anti-features to explicitly avoid:**
- Full CR recalculation (complex DMG formula; misleading output is worse than none)
- Token/map integration (out of scope per PROJECT.md)
- Custom Roll20 template support (requires HTML/CSS authoring; far beyond scope)

### Architecture Approach

The v2.0 architecture extends the existing four-layer model (domain/engine — services — views, with MainWindow as signal bus) with three new service packages and one new domain model. The persistent encounter sidebar as a `QDockWidget` is the most architecturally significant change — it replaces the per-tab encounter management in `EncountersTab` and requires extracting the Saves panel into a standalone `SavesTab`. All new business logic (monster math, combat state, JSON I/O) is pure Python with zero Qt imports, making it fully unit-testable. MainWindow remains the sole routing bus for all cross-tab signals.

**Major components:**
1. `src/persistence/service.py` (NEW) — JSON read/write for monster overrides, equipment presets, combat state, themes; mirrors SettingsService pattern
2. `src/monster_math/engine.py` (NEW) — Pure Python recalculation of AC, attack bonus, save bonuses from ability scores + CR + equipment; no Qt, no I/O; fully testable
3. `src/combat/service.py` (NEW) — In-memory `CombatantState` list (HP, conditions, initiative); snapshots to JSON on app close; pure Python
4. `src/ui/encounter_sidebar.py` (NEW) — `EncounterSidebarWidget` wrapped in `QDockWidget` at `RightDockWidgetArea`; emits `encounter_changed` signal; no tab holds a reference to it
5. `src/ui/combat_tracker_tab.py` (NEW) — HP bars, condition chips, initiative order, turn cycling; reads from and writes to `CombatTrackerService`; never holds authoritative state in widgets
6. `src/ui/saves_tab.py` (NEW, extracted) — Extracted from `EncountersTab`; receives encounter from sidebar signal; adds per-row advantage toggles and feature detection checkboxes
7. `src/ui/monster_editor.py` (NEW) — Modal editor calling `MonsterMathEngine` for live preview; emits `editor_saved(Monster)` signal; works on a `deepcopy` of the monster
8. `src/theme/` (NEW) — `ThemeDefinition`, `ThemeService.to_qss()`, `ThemeManager` applying QSS to `QApplication`; all widget color/font calls replaced with application-level QSS

**Key patterns to uphold:**
- Services and engine have zero Qt imports — testable in isolation
- All cross-tab communication routes through MainWindow signals, never direct tab references
- Encounters persist as `{name: str, count: int}` only — never serialize `Monster` objects into encounter files
- Combat state lives in `CombatTrackerService`, never in widget values
- `widget.setStyleSheet()` is only used for structural (non-color, non-font) properties

### Critical Pitfalls

1. **Orphaned encounter references** — Storing `Monster` objects (not name strings) in the persistent encounter format causes stale state after reload. Prevention: persist encounters as `{name: str, count: int}` only; resolve to `Monster` objects via name lookup at access time. Address this in Phase 1 before any other persistence work.

2. **Infinite recalculation signal loops in Monster Editor** — `QSpinBox.valueChanged` fires on programmatic `setValue()` calls, creating loops when derived fields update each other. Prevention: guard every recalculation slot with `self._recalculating` flag and `blockSignals(True/False)` on target widgets. Address this in the Monster Editor phase before wiring any field to another.

3. **Combat tracker state drift** — HP living in `QSpinBox.value()` resets on any row reorder or refresh. Prevention: build `CombatTrackerService` as the backing store first; widgets are display-only, never authoritative. Address this in the Combat Tracker phase, model-first.

4. **QSS theming refresh failure** — `widget.setStyleSheet()` color overrides take precedence over application-level QSS and do not repaint on theme change. Prevention: audit all `setStyleSheet()` calls in `src/ui/` before building theming; replace color/font references with `setObjectName()` + application-level QSS selectors. Address this as a prerequisite step in the Theming phase.

5. **Feature detection false positives** — Matching `"magic resistance"` against `Monster.raw_text` matches lore paragraphs, not just structured traits. Prevention: search `action.name` (case-insensitive) in `Monster.actions`, not the full statblock text. Address this in the Save Roller upgrades phase.

## Implications for Roadmap

Based on the combined feature dependency graph from FEATURES.md and the build order from ARCHITECTURE.md, seven phases are recommended:

### Phase 1: Domain Expansion and Persistence Foundation

**Rationale:** Every v2.0 feature depends on new domain models and JSON persistence. This has no UI deliverable but is the critical prerequisite for everything else. Building it first eliminates the orphaned-reference pitfall permanently.

**Delivers:** New domain dataclasses (`Equipment`, `EquipmentPreset`, `MonsterModifiers`, `CombatantState`, `Condition`), `PersistenceService` for JSON I/O, `MonsterMathEngine` with full 5e formula coverage and unit tests.

**Addresses:** Data persistence (P1), Monster math recalculation (prerequisite for P1 editor feature)

**Avoids:** Orphaned encounter references (Pitfall 1) — name-string-only persistence enforced here

**Research flag:** None. Pattern is directly validated by existing `SettingsService`.

---

### Phase 2: Monster Editor and Equipment Presets

**Rationale:** Depends on Phase 1 (domain models, MonsterMathEngine, PersistenceService). The editor is the primary DM workflow for customizing monsters and the highest-value standalone feature. Build it before the combat tracker so edited monsters flow into combat correctly.

**Delivers:** `MonsterEditorDialog` with live derived-value preview, +X weapon presets (0-3), all 14 armor types with correct AC formulas, shield toggle, stealth disadvantage auto-flag, "Save / Discard / Save As Copy" workflow, and override persistence to `monsters_overrides.json`.

**Addresses:** Monster Editor (P1), Equipment Presets (P1)

**Avoids:** Infinite signal loop (Pitfall 3) — `_recalculating` flag and `blockSignals()` enforced from first field wiring

**Research flag:** None. All 5e armor formulas and weapon bonus rules are HIGH confidence from SRD.

---

### Phase 3: Persistent Encounter Sidebar

**Rationale:** Can proceed in parallel with Phase 2 (shares Phase 1 dependency). Must exist before the Combat Tracker can be initialized from an encounter, and before the Saves tab can receive a participant list. Architecture of the sidebar (signal emitter, no direct tab references) must be locked before building.

**Delivers:** `EncounterSidebarWidget` in `QDockWidget` at `RightDockWidgetArea`, `encounter_changed` signal routed through `MainWindow`, `SavesTab` extracted from `EncountersTab` as standalone tab, "Send to Combat Tracker" and "Send to Save Roller" buttons.

**Addresses:** Persistent Encounter Sidebar (P1), Save Roller subset selection (partial P1)

**Avoids:** Circular sidebar dependency (Pitfall 5) — sidebar is never passed as a constructor argument to any tab

**Research flag:** None. `QDockWidget` at `RightDockWidgetArea` is the standard Qt pattern; PySide6 docs are HIGH confidence.

---

### Phase 4: Combat Tracker

**Rationale:** Depends on Phase 1 (CombatantState domain model) and Phase 3 (EncounterSidebarWidget for initialization). Must be built model-first: `CombatTrackerService` before any tracker UI widgets, to prevent combat state drift pitfall.

**Delivers:** `CombatTrackerTab` with sorted initiative list, QProgressBar HP bars (green/yellow/red), condition badge chips with round countdown, round counter, turn-cycling, add/remove combatant mid-combat, combat state JSON snapshot on app close.

**Addresses:** Combat Tracker HP/initiative/turn cycle (P1), Condition tracking (P1)

**Avoids:** Combat tracker state drift (Pitfall 4) — `CombatTrackerService` is authoritative; widgets are display-only

**Research flag:** None. QProgressBar QSS chunk styling is well-documented standard pattern.

---

### Phase 5: Save Roller Upgrades

**Rationale:** Depends on Phase 3 (SavesTab extraction) and Phase 4 (Combat Tracker bridge signal). Feature detection requires `Monster.actions` as the search scope — this must be specified before implementation to avoid false-positive pitfall.

**Delivers:** Per-row checkbox selection from sidebar encounter, Manual advantage toggle per row, Magic Resistance and Legendary Resistance auto-detection from `Monster.actions` (not `raw_text`), LR uses-remaining counter, feature detection summary column showing detected vs manual status, Combat Tracker to Saves bridge signal.

**Addresses:** Save Roller subset selection (P1), Feature detection Magic/Legendary Resistance (P1), Combat to Saves bridge (P2)

**Avoids:** Feature detection false positives (Pitfall 8) — search scope is `action.name` in `Monster.actions` only

**Research flag:** None for detection logic. MEDIUM confidence on the `action.name` exact wording matching across all SRD statblock formats — validate early with a sample of parsed monsters.

---

### Phase 6: Theming System

**Rationale:** No hard dependencies on other phases but requires the view layer to be stable. Must begin with an audit of existing `widget.setStyleSheet()` color calls before building the theme switcher. Can start after Phase 1 once major view structure is known.

**Delivers:** `src/theme/` package with `ThemeDefinition`, `BUILTIN_THEMES` (dark, light, high-contrast), `ThemeService.to_qss()`, `ThemeManager` singleton, `SettingsTab` theme selector and font picker, `RollOutputPanel.append_html()`, color-coded damage type output in AttackRollerTab.

**Addresses:** Theming color pairs and high-contrast (P2), Color-coded attack output (P2)

**Avoids:** QSS theming refresh failure (Pitfall 6) — prerequisite audit of `setStyleSheet()` calls before building; `app.style().unpolish()/polish()` on theme switch

**Research flag:** Flag for prerequisites audit. Grep `src/ui/` for `setStyleSheet` before starting implementation — volume of existing inline style calls is unknown and may expand scope.

---

### Phase 7: Roll20 Template Card Rendering

**Rationale:** Depends only on the existing v1.0 macro pipeline (stable since v1.0 launch). Positioned last because it is a P2 feature with no dependencies on other v2.0 phases — it cannot block any earlier work.

**Delivers:** `src/macro/template_renderer.py` as a new class (`Roll20TemplateRenderer`), styled HTML table card output via `QTextEdit.insertHtml()` with dark-red header + key/value rows, copy-to-clipboard as plain text. `MacroPreprocessor` is not modified — renderer is a new code path.

**Addresses:** Roll20 template card rendering (P2)

**Avoids:** Template rendering entanglement with evaluation path (Pitfall 7) — `TemplateRenderer` is a new class; `MacroPreprocessor` remains unchanged

**Research flag:** None. Roll20 default template structure is confirmed. QTextEdit HTML4 subset is HIGH confidence from Qt docs.

---

### Phase Ordering Rationale

- Phase 1 is the strict prerequisite for all other phases — no exceptions.
- Phases 2 and 3 can proceed in parallel once Phase 1 is complete; each teams can pick one.
- Phase 4 blocks on Phase 3 (needs the sidebar to initialize from encounter).
- Phase 5 blocks on Phases 3 and 4 (needs SavesTab extracted and Combat bridge signal).
- Phase 6 is independent after Phase 1 but benefits from the view layer being settled (after Phase 4).
- Phase 7 is fully independent of Phases 2-6 and can be done any time after Phase 1.

The dependency sequence: Phase 1 → (Phases 2 and 3 in parallel) → Phase 4 → Phase 5 → (Phases 6 and 7 in any order).

### Research Flags

Phases requiring additional research or early validation during planning:
- **Phase 5 (Save Roller):** Validate that `Monster.actions` actually contains parsed trait entries (not just attacks) for a representative sample of SRD monster statblocks. If traits are not parsed into `Monster.actions`, the feature detection approach must change before implementation begins.
- **Phase 6 (Theming):** Audit volume of existing `widget.setStyleSheet()` calls in `src/ui/` as a prerequisite step. High volume could expand scope unexpectedly.

Phases with standard, well-documented patterns (skip research-phase):
- **Phase 1:** Mirrors the existing `SettingsService` JSON pattern exactly.
- **Phase 2:** All 5e formulas are HIGH confidence from the SRD; PySide6 `QSpinBox` signal blocking is standard Qt.
- **Phase 3:** `QDockWidget` at `RightDockWidgetArea` is the canonical Qt persistent panel pattern.
- **Phase 4:** `QProgressBar` QSS chunk styling is well-documented; `CombatTrackerService` is pure Python data management.
- **Phase 7:** Roll20 default template structure is confirmed; `QTextEdit.setHtml()` HTML4 subset behavior is HIGH confidence.

## Confidence Assessment

| Area | Confidence | Notes |
|------|------------|-------|
| Stack | HIGH | No new dependencies. Existing stack validated in v1.0 ship. QWebEngineView bundle bloat is MEDIUM confidence (community report) but the rejection decision is firm regardless. |
| Features | HIGH | 5e SRD rules (armor AC, weapon bonus, Magic/Legendary Resistance wording) are HIGH from official sources. UX patterns from competitive analysis (Improved Initiative, Foundry, DnD Metrics) are MEDIUM — consistent across multiple tools. |
| Architecture | HIGH | Based on direct codebase inspection of v1.0 source. PySide6 `QDockWidget` pattern is HIGH confidence from Qt docs. Build order validated by feature dependency graph. |
| Pitfalls | HIGH | All critical pitfalls identified from direct codebase analysis of v1.0 source. Prevention strategies are established patterns (signal blocking, model-first state, name-reference persistence). Roll20 wiki content was 403 at research time — confirmed via community cross-reference (MEDIUM on template field details, but sufficient for implementation). |

**Overall confidence:** HIGH

### Gaps to Address

- **`Monster.actions` trait parsing coverage:** Feature detection (Phase 5) assumes traits like "Magic Resistance" are parsed into `Monster.actions` by the existing Markdown parser. This needs early validation against a sample of actual parsed monster files. If the parser does not produce action entries for traits (only for attack actions), Phase 5 must use a different search scope or extend the parser first.

- **Roll20 wiki template spec:** The Roll20 wiki returned a 403 during research. Template structure was confirmed via community forum cross-reference, which is sufficient for the default template. If users have macros using non-default templates (custom templates), those will silently render as default cards — this is documented as an accepted limitation, not a bug.

- **Existing `setStyleSheet()` audit:** The exact count and location of color/font inline style calls in `src/ui/` is unknown. This must be quantified before Phase 6 begins. If the count is high (>20 widget-level calls), Phase 6 scope must expand accordingly.

## Sources

### Primary (HIGH confidence)
- `src/settings/service.py`, `src/domain/models.py`, `src/ui/app.py`, `src/ui/encounters_tab.py`, `src/macro/preprocessor.py` — direct codebase inspection for all architectural patterns
- D&D 5e SRD armor table (5thsrd.org) — armor AC formulas and stealth disadvantage rules
- D&D Beyond Basic Rules (monsters) — proficiency bonus by CR table
- PySide6 QDockWidget docs (doc.qt.io/qtforpython-6) — persistent sidebar mechanism
- PySide6 QTextEdit docs (doc.qt.io/qtforpython-6) — HTML4 subset capabilities
- Qt Style Sheets Examples (doc.qt.io/qt-6/stylesheet-examples.html) — QProgressBar chunk styling

### Secondary (MEDIUM confidence)
- Roll20 default template structure — confirmed via community forum cross-reference (wiki returned 403)
- PyInstaller QWebEngineView bundle size (~130-150MB) — community discussion report, github.com/orgs/pyinstaller/discussions/7322
- Improved Initiative, Foundry VTT, DnD Metrics — competitive UX pattern analysis
- sqlite3 vs JSON for desktop apps — Qt forum discussion, consistent with stdlib docs guidance

### Tertiary (LOW confidence / needs validation)
- `Monster.actions` parsing coverage for trait entries — inferred from parser design; needs empirical validation against actual statblock files before Phase 5 begins

---
*Research completed: 2026-02-25*
*Ready for roadmap: yes*
