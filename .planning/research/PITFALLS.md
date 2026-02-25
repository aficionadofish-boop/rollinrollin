# Pitfalls Research

**Domain:** Desktop D&D combat manager — adding persistence, complex editor UI, combat state, cross-tab shared state, theming, Roll20 template rendering, and feature detection to an existing PySide6 app
**Researched:** 2026-02-25
**Confidence:** HIGH (based on direct codebase analysis + verified patterns)

---

## Critical Pitfalls

### Pitfall 1: Orphaned Encounter References After Persistence Is Added

**What goes wrong:**
The existing `Encounter` model stores live `Monster` object references (`list[tuple[Monster, int]]`). When SQLite/JSON persistence is added, monsters saved to disk get deserialized into *new* Python objects. The in-memory `MonsterLibrary` now holds different object instances than those embedded in a saved encounter. After a session reload, encounter members point to stale in-memory objects that are not the same instances as what the library holds — monsters edited in the editor do not update the encounter, and HP bars in the combat tracker show pre-edit data.

**Why it happens:**
The current architecture was designed for single-session use: `library.get_by_name()` returns the in-memory reference, which is passed directly into `Encounter.members`. Persistence breaks this identity contract — deserialization always produces fresh objects.

**How to avoid:**
Design the persistence layer to use **name-based references** throughout, not object references. Encounters persist as `{name: str, count: int}` pairs only. On load, encounters are resolved by name lookup against the current in-memory library. The `EncounterService.load_encounter()` method already does this correctly for Markdown files — extend this exact pattern to the internal store. Never store `Monster` objects inside `Encounter` in the persistent format; always store only the monster name string and resolve at access time.

**Warning signs:**
- `Encounter.members` tuples hold the same `Monster` Python object at both the library level and inside the encounter after edit — this was correct before persistence, but is the identity you need to actively break and re-resolve.
- If you see code that serializes `Encounter` by calling `dataclasses.asdict()` on the whole tree, you are serializing monster data redundantly into the encounter file — this is wrong.
- Combat tracker showing old HP/AC values after a monster is edited and the editor is closed.

**Phase to address:**
Phase that introduces the internal data store (JSON/SQLite) — this must be the first thing locked down before any other persistence work begins.

---

### Pitfall 2: SQLite Schema Version Not Set From Day One

**What goes wrong:**
A SQLite database is created in v2.0 without using `PRAGMA user_version`. In v2.1, a schema change is needed (e.g., adding a `conditions` column to a combat_state table). There is no mechanism to detect which schema version a user's existing database is on. The migration code either re-runs on an already-migrated database, breaks on old databases that lack the new column, or requires deleting and recreating the database entirely — losing all user data.

**Why it happens:**
Schema versioning feels premature when writing the first migration. The v2.0 schema seems "final." It never is.

**How to avoid:**
On first database creation, immediately execute `PRAGMA user_version = 1`. Every schema migration increments this value atomically inside a transaction. On app startup, read `PRAGMA user_version`, compare to the expected version constant in code, and run any outstanding migrations in sequence. Keep each migration in a numbered function: `_migrate_1_to_2()`, `_migrate_2_to_3()`. Wrap each migration in `BEGIN TRANSACTION / COMMIT` so a failed migration rolls back cleanly without corrupting the database.

```python
EXPECTED_VERSION = 1

def _get_version(conn) -> int:
    return conn.execute("PRAGMA user_version").fetchone()[0]

def _migrate_0_to_1(conn):
    conn.execute("CREATE TABLE monsters (...)")
    conn.execute("PRAGMA user_version = 1")
```

**Warning signs:**
- Database file is created without any version check logic at startup.
- `CREATE TABLE IF NOT EXISTS` used without version gating — this hides schema drift silently instead of detecting it.
- Any `ALTER TABLE` executed unconditionally without checking `user_version` first.

**Phase to address:**
Phase that introduces the internal data store. Build the migration runner before writing any table definitions.

---

### Pitfall 3: Monster Editor Cascading Recalculation Creates Infinite Signal Loops

**What goes wrong:**
The monster editor has fields that recalculate each other: changing a STR score recalculates the STR modifier, which affects attack bonus, which may affect save DC display. In PySide6, each field change emits `valueChanged` or `textChanged`, which triggers a slot that updates derived fields, which triggers their `valueChanged`, which re-triggers the original slot — producing either an infinite loop or excessive redundant recalculations.

**Why it happens:**
`QSpinBox.valueChanged` fires even on programmatic `setValue()` calls. A naive recalculation slot connected to `valueChanged` will re-enter when the slot itself calls `setValue()` on another field.

**How to avoid:**
Use a **recalculation lock flag** (`self._recalculating = False`) in the editor widget. In every slot that performs recalculation: check the flag, set it to `True`, perform all derived-value updates with `blockSignals(True)` on each target widget, restore `blockSignals(False)`, then set the flag back to `False`. Alternatively, use Qt's `QSignalBlocker` context manager for the scope. The key rule: programmatic updates to derived fields must never trigger further recalculation cascades.

```python
def _on_str_changed(self, value: int):
    if self._recalculating:
        return
    self._recalculating = True
    try:
        mod = (value - 10) // 2
        self._str_mod_label.setText(f"+{mod}" if mod >= 0 else str(mod))
        # Update attack bonuses that depend on STR
        self._refresh_attack_bonuses()
    finally:
        self._recalculating = False
```

**Warning signs:**
- UI freezes or becomes unresponsive when editing ability scores.
- `RecursionError` in Python traceback involving `valueChanged`.
- `setValue()` calls inside `valueChanged` slots without `blockSignals()`.
- Any derived-value widget connected to `valueChanged` without a guard.

**Phase to address:**
Phase that builds the monster editor. Must be established before any field is connected to another.

---

### Pitfall 4: Combat Tracker State Drift Between In-Memory Model and Widget Display

**What goes wrong:**
The combat tracker displays HP bars, conditions, and turn order for combatants. If the HP state lives inside the widgets themselves (e.g., a `QSpinBox` value IS the current HP), rather than in a separate model, state becomes unrecoverable: filtering the list, sorting by initiative, switching tabs, or minimizing the window can lose combatant state. Sorting the table re-creates rows, resetting HP fields to their initial values.

**Why it happens:**
It is tempting to derive "current HP" directly from a spinbox value because it is already a widget. The widget IS the data. This works until rows are ever reordered or hidden.

**How to avoid:**
Combat state must live in a dedicated service/model class (`CombatStateService` or similar) that is independent of widget lifetime. Widgets read from and write to this model; they do not hold authoritative state themselves. Use a stable combatant ID (e.g., `"Goblin 1"`) as the key. When the tracker's view needs to refresh (sort, filter, tab switch), it re-reads from the model — it never treats widget state as ground truth. This follows the existing architecture pattern already established for `MonsterLibrary` and `EncounterService`.

**Warning signs:**
- Combat tracker row widget has an `__init__` that takes `current_hp` and stores it only in a `QSpinBox` — no external model.
- HP spinbox changes are not written back to a backing store.
- "Load encounter into tracker" re-creates combatant rows from scratch each time.
- Any code that iterates over `self._rows` to extract HP values from spinboxes.

**Phase to address:**
Phase that builds the combat tracker. Model-first: `CombatState` dataclass and service before any tracker widget.

---

### Pitfall 5: Persistent Encounter Sidebar Becomes a Circular Dependency Hub

**What goes wrong:**
The encounter sidebar must be visible across Library, Attack, and Saves tabs. The naive implementation passes the sidebar widget directly to each tab's constructor: `LibraryTab(sidebar=self._sidebar)`. Each tab then holds a direct reference to the sidebar. The sidebar also holds references to the library and encounter state. The result is a web of circular object references across tabs — when one breaks, others break silently, and testing any tab in isolation becomes impossible.

**Why it happens:**
The sidebar is "shared state" so it feels natural to pass it everywhere. The existing `app.py` cross-tab wiring (signal connections) already shows the correct pattern, but it is easy to abandon this discipline when adding a more complex shared component.

**How to avoid:**
Apply the same signal-mediated wiring already used in `app.py`. The sidebar is owned by `MainWindow`. Tabs do NOT receive the sidebar as a constructor argument. Instead:
- Library tab emits `monster_added_to_encounter(Monster)` — `MainWindow` connects this to the sidebar's add slot.
- Attack tab reads from the sidebar via a signal `encounter_changed(list)` that the sidebar emits whenever its state changes.
- Saves tab subscribes to the same `encounter_changed` signal.

The sidebar is a signal emitter; each tab is a subscriber. No tab holds a reference to the sidebar. This matches the existing `encounter_members_changed` signal pattern already in `EncountersTab`.

**Warning signs:**
- Any tab constructor receives `sidebar=` as a parameter.
- `self._sidebar.get_members()` called from inside a tab's method.
- Importing a sidebar class from within a tab module.
- Tests that cannot instantiate a single tab without also constructing the sidebar.

**Phase to address:**
Phase that introduces the persistent encounter sidebar. Architecture must be locked before the sidebar widget is built.

---

### Pitfall 6: QSS Theming Applied to Existing Widgets Does Not Refresh Without Force Polish

**What goes wrong:**
When `QApplication.setStyleSheet()` is called to switch themes at runtime (e.g., switching from default to high-contrast), existing widgets that were constructed before the new stylesheet was applied do not visually update. Their cached style is stale. This is especially pronounced for custom widgets that set inline `setStyleSheet()` calls — those inline styles take precedence over the application-level QSS and are never overridden by a theme change.

**Why it happens:**
Qt caches style calculations per-widget. Setting a new application stylesheet invalidates the cache at the application level, but widgets with *widget-level* stylesheet overrides (`widget.setStyleSheet(...)`) override the cascade and ignore the application stylesheet. The existing codebase uses inline `setStyleSheet` calls in several places (e.g., `header.setStyleSheet("font-weight: bold;")` in `encounters_tab.py`) — these will not be theme-aware.

**How to avoid:**
Two rules for theme-compatible styling:
1. Never use `widget.setStyleSheet()` for any property that a theme might want to control (colors, fonts). Use it only for structural properties that are theme-neutral (e.g., `border-radius`), or replace with `setProperty()` + QSS dynamic property selectors.
2. After calling `QApplication.setStyleSheet(new_stylesheet)`, call `app.style().unpolish(app)` followed by `app.style().polish(app)` and then `app.processEvents()`. This forces a full re-polish of the widget tree.

For the existing inline `setStyleSheet("color: gray; font-size: 10px;")` calls already in the codebase: audit and replace any color references with named QSS classes or `setObjectName()` + QSS selectors before theme support is built.

**Warning signs:**
- Switching themes in the Settings tab does not update colors in already-open Library or Attack Roller tabs.
- Some labels remain gray in high-contrast mode after theme switch.
- Grep for `setStyleSheet` in `src/ui/` — any calls that set color or font should be replaced before theming is added.
- Theme toggle works correctly on first launch but fails after the first tab switch.

**Phase to address:**
Phase that introduces theming. Audit and replace inline stylesheet calls as a prerequisite step before building theme switching.

---

### Pitfall 7: Roll20 Template Rendering Treating `{{key=value}}` as Dice Expressions

**What goes wrong:**
The current `MacroPreprocessor` strips `&{template:...}` tokens and extracts `{{name=value}}` fields, keeping the value expressions for dice resolution. The existing v1 code works correctly for the sandbox use case. For v2 template *rendering* (displaying `&{template:default}` as a styled card), a new code path is needed. The pitfall is reusing or tangling the sandbox's expression-evaluation path with template card rendering: template field values like `{{name=Fireball}}` are not dice expressions and must not be passed to `roll_expression()`.

**Why it happens:**
`_extract_template_fields` currently keeps non-name field values in the expression string so they can contain inline rolls. When rendering a visual card, all fields need to be collected as key-value pairs, not concatenated into an expression. The two use cases — "evaluate whatever dice are in these template fields" (sandbox) vs. "render all fields as a styled display card" (v2 rendering) — require different extraction logic.

**How to avoid:**
Create a separate `TemplateRenderer` class in the macro module that parses `&{template:name} {{key=value}} {{key=value}}` into a structured `RenderedTemplate(name: str, fields: list[tuple[str, str]])` object. This renderer does NOT evaluate dice expressions — it is purely structural. The existing `MacroPreprocessor` path remains unchanged for expression evaluation. The template renderer feeds a new `TemplateCard` widget that displays the styled card. Keep the two code paths strictly separate: evaluation path vs. rendering path.

**Warning signs:**
- Template field values being passed directly to `roll_expression()` without checking whether they contain a dice expression.
- `_extract_template_fields` being modified to serve both sandbox evaluation and visual rendering.
- Template card displaying dice expressions as literal strings (e.g., showing "1d6+3" instead of rolling and showing the result).
- Template card displaying rolled results when it should show static values.

**Phase to address:**
Phase that implements Roll20 template rendering. Design the `TemplateRenderer` as a new class, not a modification of `MacroPreprocessor`.

---

### Pitfall 8: Feature Detection False Positives on Lore and Flavor Text

**What goes wrong:**
Feature detection for "Magic Resistance" and "Legendary Resistance" uses substring matching on `Monster.raw_text`. A monster's lore section contains the sentence "The ancient dragon has long been known to resist magical effects" — this matches a naive `"magic resist" in text.lower()` check. Alternatively, homebrew statblocks may have "Greater Magic Resistance" as a trait name, which should match, or "Partial Legendary Resistance" which may or may not match depending on intent. False positives auto-apply advantage in the Saves tab when the DM did not intend it.

**Why it happens:**
Keyword matching on the full `raw_text` field does not distinguish between structured trait sections and lore paragraphs. The existing parser preserves the full source text in `Monster.raw_text` specifically for debugging — it was not designed to be the target for feature detection.

**How to avoid:**
Feature detection must operate on the **structured action text only**, not `raw_text`. The existing `Monster.actions` list contains `Action` objects with `raw_text` per action. Feature detection should:
1. Search `action.name` (case-insensitive) for exact trait names: `"Magic Resistance"`, `"Legendary Resistance"`.
2. Only fall back to `action.raw_text` for the trait description text, not `Monster.raw_text` (the full statblock).
3. Require the trait to appear in the `### Traits` or top-level section, not in `### Actions` (attacks do not grant resistance).

Accept as a known limitation: if the user's statblock format does not result in the trait being parsed into `Monster.actions` (e.g., a flat-text format with no section headers), feature detection will silently fail. This is preferable to false positives. The existing constraint in `PROJECT.md` — "Keyword matching on known phrases" and "homebrew edge cases accepted as limitation" — is the correct stance.

**Warning signs:**
- Feature detection running `"magic resistance" in monster.raw_text.lower()`.
- Traits from monster lore paragraphs (not action blocks) triggering auto-advantage.
- Feature detection toggling advantage for monsters that the DM knows do not have the trait.
- Saves tab showing advantage checkbox pre-checked for a basic Goblin (which has no special traits).

**Phase to address:**
Phase that implements feature detection in the Saves tab upgrades. Must use `Monster.actions` as the search scope, not `Monster.raw_text`.

---

## Technical Debt Patterns

| Shortcut | Immediate Benefit | Long-term Cost | When Acceptable |
|----------|-------------------|----------------|-----------------|
| Storing `Monster` objects directly in `Encounter.members` for the internal store (not just in-memory) | Avoids adding a resolution step on load | Combat tracker and editor edits do not propagate to encounters; save/load breaks | Never — use name references in persistent formats |
| Using `dataclasses.asdict()` to serialize `Monster` to JSON for the internal store | No custom serialization code needed | Nested enum values (`DamageType`) serialize as strings but do not round-trip cleanly; `Optional[int]` fields serialize as `null` JSON which deserializes correctly but loses type safety | Acceptable for initial implementation if a typed deserializer is added in the same phase |
| Inline `widget.setStyleSheet("color: X")` calls for visual feedback (e.g., red border on validation error) | Fast to write | Overrides application-level theme cascade permanently for that widget | Only for structural/non-color properties (border shape, border-radius); never for color or font |
| Combat tracker HP state living in `QSpinBox.value()` | No separate model needed | HP resets on any row reorder or refresh; no persistence possible | Never for a tracker that needs persistence |
| Single flat JSON file for all persistence (monsters, equipment, combat state) | Simple to implement | Entire file must be parsed and re-written on every small change; file grows large; concurrent writes corrupt data | Acceptable for initial implementation if combat state is kept separate from monsters/equipment |
| Skipping `PRAGMA user_version` on first database write | Saves 2 lines of code | Impossible to migrate existing databases safely in future releases | Never |
| Re-using `MacroPreprocessor._extract_template_fields()` for template card rendering | No new parsing code | Evaluation and rendering logic become entangled; changing one breaks the other | Never — create `TemplateRenderer` as a separate class |

---

## Integration Gotchas

| Integration | Common Mistake | Correct Approach |
|-------------|----------------|------------------|
| SQLite + Python dataclasses | Using `dataclasses.asdict()` then `json.dumps()` and assuming round-trip fidelity; `DamageType` enum serializes as `"acid"` string but does not deserialize back to `DamageType` | Write explicit serializers per model type; on deserialization, reconstruct enums explicitly: `DamageType(data["damage_type"])` |
| SQLite + PyInstaller packaging | Database file path resolved relative to `sys.argv[0]` or `__file__` — both are wrong in a PyInstaller bundle; database ends up inside the frozen archive and is read-only | Use `Path(sys.executable).parent` for the database path in packaged mode; detect packaging with `getattr(sys, 'frozen', False)` |
| QSS theming + existing inline stylesheets | Application-level `setStyleSheet()` does not override widget-level `setStyleSheet()` calls | Audit all `widget.setStyleSheet()` calls; replace color/font overrides with `setObjectName()` + application-level QSS selectors |
| Cross-tab signals + tab construction order | Connecting signals before all tabs are fully constructed causes `AttributeError` if a connected slot references a widget that does not exist yet | Follow the existing `app.py` pattern: construct ALL tabs first, THEN wire all cross-tab signals |
| Monster editor + shared MonsterLibrary | Editor edits a copy of the Monster object; saving back to library requires an explicit `library.replace()` call | Editor works on a detached copy (`copy.deepcopy(monster)`); the save action calls `library.replace(edited_monster)` and emits a library-changed signal |
| Combat tracker + encounter sidebar | Sidebar encounter members and combat tracker combatants are separate lists that can drift out of sync | Combat tracker is initialized from the sidebar but then owns its own combatant list; explicit "reload from encounter" action resynchronizes them rather than live-syncing |

---

## Performance Traps

| Trap | Symptoms | Prevention | When It Breaks |
|------|----------|------------|----------------|
| Recalculating all derived monster stats on every keystroke in the editor | UI lag when typing in ability score fields | Debounce recalculation using `QTimer.singleShot(150, self._recalculate)` so the recalculation fires 150ms after the last keystroke | Immediately visible with 6 ability score fields each triggering a full stat recalculation chain |
| Rebuilding the entire combat tracker widget tree on every combatant state change | Tracker flickers and loses focus on each HP change | Update only the specific row widget that changed; use `CombatStateService` to emit targeted `combatant_changed(combatant_id)` signals | Noticeable at 5+ combatants; severe at 20+ |
| Writing the full monsters JSON file to disk on every monster edit | Disk I/O on each character typed in monster name field | Write to disk only on explicit save actions; keep unsaved changes in memory | Immediately problematic on HDDs or network drives; acceptable on SSDs for single-user desktop use |
| Loading all monsters from disk on every library search/filter operation | Library tab becomes sluggish | Keep monsters in the in-memory `MonsterLibrary`; only read from disk on explicit import or app startup | At 200+ monsters in the library |
| QSS cascade recomputation on frequent style changes | Noticeable repaint lag when changing combat conditions (which may update row colors) | Apply condition-based styling via `setProperty()` + `style().unpolish()` / `style().polish()` on the specific row widget only, not via full application stylesheet re-application | At 10+ combatant rows with condition icons |

---

## UX Pitfalls

| Pitfall | User Impact | Better Approach |
|---------|-------------|-----------------|
| Monster editor "Save" button with no visual dirty-state indicator | DM edits a monster then switches tabs, not knowing changes were not saved | Show a `*` in the editor title or enable a "Discard" button only when changes exist; mirror the existing Settings tab `is_dirty()` pattern |
| Combat tracker initiative order not updating when a combatant's initiative is changed | DM manually sorts, changes a value, and list order is wrong | Provide an explicit "Sort by Initiative" button rather than auto-sorting on every change (auto-sort causes disorienting jumps during entry) |
| Theming color picker with no preview | DM sets an unusable color combination (e.g., white text on white background) | Show a live preview panel in the Settings tab alongside the color picker; do not apply the theme until "Save" is clicked |
| "Load encounter into saves" button still present after persistent sidebar replaces the old encounter builder | Two ways to get monsters into the saves roller; DMs confused about which to use | Remove the old encounter-builder-based loading path when the persistent sidebar takes over the encounter state |
| Feature detection checkboxes appearing with no explanation | DM does not know why "Magic Resistance" checkbox is pre-checked | Show the detected trait name as a tooltip on the checkbox; use label text "Magic Resistance (detected)" vs "Magic Resistance (manual)" |

---

## "Looks Done But Isn't" Checklist

- [ ] **Monster editor save:** Verify that editing a monster and saving updates the shared `MonsterLibrary` instance AND any open encounter that references that monster — not just the editor's local copy.
- [ ] **Combat tracker persistence:** Verify that closing and reopening the app while a combat is in progress restores HP values, conditions, and initiative order — not just the combatant names.
- [ ] **Feature detection:** Verify that auto-detected advantage (Magic Resistance) is reflected in the `SaveRequest.advantage` field passed to `SaveRollService`, not just visually checked in the UI.
- [ ] **Theme switch:** Verify that switching themes while on the Library tab and then switching to the Attack Roller tab shows the new theme on the Attack Roller tab's widgets — not the pre-switch style.
- [ ] **SQLite on first run:** Verify that first launch on a machine with no existing database creates the database, applies schema version 1, and does not error or show a migration prompt.
- [ ] **Equipment presets:** Verify that applying a +X weapon preset to a monster in the editor and then saving actually modifies the attack bonus stored in the `Action` for that weapon — not just a display-only field.
- [ ] **Roll20 template card:** Verify that `[[1d6+3]]` inside a template `{{damage=[[1d6+3]]}}` is evaluated and the card shows a number — not the literal string `[[1d6+3]]`.
- [ ] **Cross-tab encounter sidebar:** Verify that adding a monster from the Library tab immediately appears in the Attack Roller tab's creature list without requiring a manual refresh or tab switch.

---

## Recovery Strategies

| Pitfall | Recovery Cost | Recovery Steps |
|---------|---------------|----------------|
| Orphaned encounter references discovered after persistence is built | HIGH | Audit all `Encounter` serialization paths; replace object-reference storage with name-string storage; add a data migration for any existing saved encounters |
| `user_version` missing from database shipped to users | MEDIUM | Add a version detection heuristic (check for existence of specific tables); assign retroactive version 0 for unversioned databases; add `_migrate_0_to_1()` that is a no-op if tables already exist via `CREATE TABLE IF NOT EXISTS` |
| Infinite recalculation loop shipped in monster editor | LOW-MEDIUM | Add `_recalculating` guard flag; wrap all `setValue()` calls in `blockSignals(True/False)` pairs; detectable immediately in manual testing |
| Combat tracker HP state lost on row reorder | HIGH | Introduce `CombatStateService` as backing store; refactor all tracker rows to read from service on construction; existing widget HP values seed the service on first migration |
| Inline stylesheets blocking theme switch | MEDIUM | Grep for `setStyleSheet` in `src/ui/`; replace each color/font override with `setObjectName()` + application-level QSS; test each tab after change |

---

## Pitfall-to-Phase Mapping

| Pitfall | Prevention Phase | Verification |
|---------|------------------|--------------|
| Orphaned encounter references | Data store phase (first persistence phase) | Load a session, edit a monster, confirm encounter member reflects the edit |
| Missing SQLite schema version | Data store phase | Inspect `PRAGMA user_version` in created database equals expected constant |
| Cascading recalculation loops | Monster editor phase | Edit each ability score field; confirm no freeze or recursion error; confirm derived fields update exactly once |
| Combat tracker state drift | Combat tracker phase (model-first) | Sort tracker by initiative; confirm all HP values survive the reorder |
| Circular sidebar dependency | Encounter sidebar phase | Confirm each tab can be instantiated in isolation in tests without importing sidebar |
| QSS theming refresh failure | Theming phase | Switch theme while on Library tab; switch to every other tab; confirm new theme is visible on all |
| Template rendering entanglement | Roll20 template rendering phase | Confirm `MacroPreprocessor` unit tests still pass without modification after renderer is added |
| Feature detection false positives | Saves tab upgrades phase | Test with a monster whose lore text contains "resist magic" but has no Magic Resistance trait; confirm no auto-advantage |

---

## Sources

- Direct codebase analysis: `src/domain/models.py`, `src/library/service.py`, `src/encounter/service.py`, `src/ui/app.py`, `src/ui/encounters_tab.py`, `src/macro/preprocessor.py`, `src/parser/formats/_shared_patterns.py`
- [SQLite Versioning and Migration Strategies](https://www.sqliteforum.com/p/sqlite-versioning-and-migration-strategies) — PRAGMA user_version patterns
- [Qt Style Sheets — Styling the Widgets Application](https://doc.qt.io/qtforpython-6/tutorials/basictutorial/widgetstyling.html) — QSS cascade behavior
- [PySide6 QAbstractItemModel documentation](https://doc.qt.io/qtforpython-6/PySide6/QtCore/QAbstractItemModel.html) — dataChanged signal requirements
- [Roll20 Roll Templates Wiki](https://wiki.roll20.net/Roll_Templates) — template field syntax
- [Roll20 Default Template Fields](https://wiki.roll20.net/Roll_Templates/Default) — `{{name=}}`, `{{desc=}}` field semantics
- PROJECT.md constraints: keyword matching scope, conditions = name + rounds only, offline-first, no VTT

---
*Pitfalls research for: RollinRollin v2.0 Combat Manager — adding features to existing PySide6 app*
*Researched: 2026-02-25*
