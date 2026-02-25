# Architecture Research

**Domain:** Desktop D&D 5e combat manager (Python + PySide6, Windows 10)
**Researched:** 2026-02-25
**Confidence:** HIGH — based on direct codebase inspection + verified PySide6 documentation

---

## System Overview

### Current v1.0 Layered Architecture

```
┌─────────────────────────────────────────────────────────────────────┐
│  VIEWS (src/ui/)                                                     │
│  ┌──────────────┐ ┌──────────────┐ ┌──────────────┐ ┌───────────┐  │
│  │ LibraryTab   │ │ AttackRoller │ │EncountersTab │ │MacroSandbox│  │
│  │              │ │     Tab      │ │  (Enc+Saves) │ │    Tab    │  │
│  └──────┬───────┘ └──────┬───────┘ └──────┬───────┘ └─────┬─────┘  │
├─────────┴────────────────┴────────────────┴───────────────┴─────────┤
│  SERVICES (src/*/service.py)                                         │
│  ┌──────────────┐ ┌──────────────┐ ┌──────────────┐ ┌───────────┐  │
│  │ MonsterLibrary│ │  RollService │ │EncounterSvc  │ │MacroSandbox│  │
│  │ (library/)   │ │  (roll/)     │ │ SaveRollSvc  │ │   Svc     │  │
│  └──────┬───────┘ └──────┬───────┘ └──────┬───────┘ └─────┬─────┘  │
├─────────┴────────────────┴────────────────┴───────────────┴─────────┤
│  DOMAIN / ENGINE (src/domain/, src/engine/)                          │
│  ┌──────────────┐ ┌──────────────┐ ┌──────────────┐               │
│  │domain/models │ │engine/lexer  │ │engine/parser │               │
│  │Monster,Action│ │engine/roller │ │roll_expression│               │
│  └──────────────┘ └──────────────┘ └──────────────┘               │
└─────────────────────────────────────────────────────────────────────┘
```

**Dependency rule (strict, upheld in v1.0):** engine/domain import nothing from project. Services import domain. Views import services. No upward or lateral imports across top-level packages.

### v2.0 Target Architecture (with new components)

```
┌────────────────────────────────────────────────────────────────────────────┐
│  VIEWS (src/ui/)                                                            │
│  ┌────────────┐ ┌───────────┐ ┌──────────┐ ┌──────────┐ ┌──────────────┐  │
│  │LibraryTab  │ │AttackRoller│ │SavesTab  │ │CombatTrkr│ │MacroSandbox  │  │
│  │+MonsterEd  │ │    Tab    │ │(extracted│ │   Tab    │ │    Tab       │  │
│  │            │ │           │ │from Enc) │ │          │ │+TemplateCard │  │
│  └────┬───────┘ └────┬──────┘ └────┬─────┘ └────┬─────┘ └──────┬───────┘  │
│       │              │              │              │              │          │
│  ┌────┴──────────────┴──────────────┴──────────────┴──────────────┴──────┐  │
│  │ EncounterSidebarWidget (QDockWidget, RIGHT area, persistent across tabs)│  │
│  └────────────────────────────────────────────────────────────────────────┘  │
│  ┌────────────────────────────────────────────────────────────────────────┐  │
│  │ ThemeManager (QApplication.setStyleSheet, loaded from ThemeService)    │  │
│  └────────────────────────────────────────────────────────────────────────┘  │
├───────────────────────────────────────────────────────────────────────────────┤
│  SERVICES (src/*/service.py)                                                  │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐           │
│  │Monster   │ │Roll      │ │Encounter │ │Combat    │ │Persistence│           │
│  │Library   │ │Service   │ │/SaveRoll │ │Tracker   │ │Service   │           │
│  │          │ │          │ │Service   │ │Service   │ │(NEW)     │           │
│  └──────────┘ └──────────┘ └──────────┘ └──────────┘ └──────────┘           │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐                                      │
│  │Monster   │ │Theme     │ │Macro     │                                       │
│  │Math      │ │Service   │ │Sandbox   │                                       │
│  │Engine    │ │(NEW)     │ │Service   │                                       │
│  │(NEW)     │ │          │ │+Template │                                       │
│  └──────────┘ └──────────┘ └──────────┘                                      │
├───────────────────────────────────────────────────────────────────────────────┤
│  DOMAIN / ENGINE (src/domain/, src/engine/)                                   │
│  ┌──────────────┐ ┌──────────────┐ ┌──────────────┐ ┌──────────────┐         │
│  │domain/models │ │CombatState   │ │engine/lexer  │ │engine/parser │         │
│  │+Equipment    │ │(NEW)         │ │engine/roller │ │roll_expression│         │
│  │+MonsterMods  │ │CombatantState│ │              │ │              │         │
│  └──────────────┘ └──────────────┘ └──────────────┘ └──────────────┘         │
├───────────────────────────────────────────────────────────────────────────────┤
│  PERSISTENCE (src/persistence/)  — NEW PACKAGE                                │
│  ┌──────────────────────────────────────────────────────────────────┐         │
│  │ PersistenceService: JSON files in workspace root                  │         │
│  │  monsters_overrides.json | equipment_presets.json | themes.json   │         │
│  │  combat_state.json (session) | custom_bonuses.json               │         │
│  └──────────────────────────────────────────────────────────────────┘         │
└───────────────────────────────────────────────────────────────────────────────┘
```

---

## Component Responsibilities

### New Components

| Component | Package | Responsibility | Communicates With |
|-----------|---------|---------------|-------------------|
| `MonsterMathEngine` | `src/monster_math/` | Recalculates derived values (AC, attack bonus, save bonuses, HP avg) from base stats + equipment + proficiency bonus | domain/models, domain/equipment |
| `PersistenceService` | `src/persistence/` | Reads/writes JSON files for modified monsters, equipment presets, custom bonuses, combat state, theme preferences | workspace/, domain/models |
| `CombatTrackerService` | `src/combat/` | Manages CombatantState list (HP, max HP, conditions, initiative); owned per-session in memory, optionally persisted as JSON | domain/models, persistence/ |
| `EncounterSidebarWidget` | `src/ui/` | Persistent QDockWidget (RIGHT) visible across all tabs; replaces EncountersTab encounter-builder panel | CombatTrackerService, domain/models |
| `CombatTrackerTab` | `src/ui/` | New tab: HP bars, condition list, initiative order, turn cycling, player characters subtab | CombatTrackerService, SavesTab signal bridge |
| `SavesTab` | `src/ui/` | Extracted from EncountersTab; save roller is a standalone tab in v2.0; receives encounter state from sidebar | encounter/, SaveRollService |
| `MonsterEditorDialog` | `src/ui/` | Modal or docked editor for full stat editing; calls MonsterMathEngine to preview derived values | MonsterMathEngine, PersistenceService |
| `ThemeService` | `src/theme/` | Loads/saves theme definitions (color pairs, high-contrast, font) as JSON; generates QSS strings | persistence/ |
| `ThemeManager` | `src/ui/` | Singleton UI coordinator; applies theme QSS to QApplication and notifies all tabs | ThemeService |
| `Roll20TemplateRenderer` | `src/macro/` | Converts parsed MacroLineResult.template_name + fields into styled QTextEdit HTML card output | macro/models, macro/service |

### Modified Components

| Component | Change | Why |
|-----------|--------|-----|
| `domain/models.py` | Add `Equipment`, `EquipmentPreset`, `MonsterModifiers`, `CombatantState`, `Condition` dataclasses | New features require new domain objects that the whole stack shares |
| `MonsterLibrary` | Add `update_modifiers(name, mods)` and `get_modified(name)` methods | Editors write per-monster overrides; attack roller reads them |
| `EncountersTab` | Split into `EncounterSidebarWidget` (dock) + `SavesTab` (tab); remove old encounter builder from EncountersTab | Sidebar persistence across tabs; saves becomes standalone |
| `RollOutputPanel` | Add `append_html(html)` alongside `append(text)` for color-coded damage type output | Attack roller and saves tab need per-damage-type coloring |
| `app.py` (MainWindow) | Add QDockWidget wiring; add CombatTrackerTab and SavesTab; remove EncountersTab; apply ThemeManager on startup | Tab restructure + persistent sidebar |
| `AppSettings` | Add theme fields: `theme_name`, `font_family`, `font_size` | Settings tab v2.0 covers theming |
| `settings/service.py` | No change — already handles unknown fields gracefully via `known` filter | Backward compatible with new AppSettings fields |

---

## Recommended Project Structure (v2.0 additions)

```
src/
├── domain/
│   └── models.py              # ADD: Equipment, EquipmentPreset, MonsterModifiers,
│                              #       CombatantState, Condition dataclasses
├── monster_math/              # NEW PACKAGE
│   ├── __init__.py
│   ├── models.py              # DerivedStats dataclass
│   ├── engine.py              # MonsterMathEngine (pure Python, no Qt, no I/O)
│   └── presets.py             # BUILTIN_EQUIPMENT_PRESETS constant dict
├── combat/                    # NEW PACKAGE
│   ├── __init__.py
│   ├── models.py              # CombatantState, CombatSession dataclasses
│   └── service.py             # CombatTrackerService (pure Python, no Qt)
├── persistence/               # NEW PACKAGE
│   ├── __init__.py
│   └── service.py             # PersistenceService (JSON I/O alongside workspace/)
├── theme/                     # NEW PACKAGE
│   ├── __init__.py
│   ├── models.py              # ThemeDefinition dataclass
│   ├── service.py             # ThemeService (load/save theme JSON, generate QSS)
│   └── defaults.py            # BUILTIN_THEMES constant dict
├── encounter/
│   ├── models.py              # unchanged
│   └── service.py             # unchanged
├── macro/
│   ├── models.py              # ADD: template_fields to MacroLineResult
│   ├── preprocessor.py        # ADD: template field extraction
│   ├── service.py             # unchanged
│   └── template_renderer.py   # NEW: Roll20TemplateRenderer → HTML string
├── ui/
│   ├── app.py                 # MODIFY: add dock, new tabs, ThemeManager
│   ├── encounter_sidebar.py   # NEW: EncounterSidebarWidget (QDockWidget)
│   ├── combat_tracker_tab.py  # NEW: CombatTrackerTab
│   ├── saves_tab.py           # NEW: SavesTab (extracted from encounters_tab.py)
│   ├── monster_editor.py      # NEW: MonsterEditorDialog
│   ├── theme_manager.py       # NEW: ThemeManager singleton
│   ├── roll_output.py         # MODIFY: add append_html()
│   ├── library_tab.py         # MODIFY: add Edit button → MonsterEditorDialog
│   ├── attack_roller_tab.py   # MODIFY: consume modified monsters, color output
│   ├── encounters_tab.py      # REMOVE or gut to stub (sidebar replaces it)
│   ├── settings_tab.py        # MODIFY: add theme/font controls
│   └── macro_sandbox_tab.py   # MODIFY: wire Roll20TemplateRenderer output
├── settings/
│   ├── models.py              # ADD: theme_name, font_family, font_size fields
│   └── service.py             # unchanged
└── workspace/
    └── setup.py               # unchanged (Markdown I/O stays)
```

---

## Architectural Patterns

### Pattern 1: Layered Dependency (Existing — Uphold Strictly)

**What:** engine/domain have no project imports. Services import domain only. Views import services only. No lateral imports between top-level packages.

**When to use:** Every new component without exception.

**Why critical for v2.0:** Three new packages (monster_math, combat, persistence) must each sit at the correct layer. MonsterMathEngine is pure Python and imports only domain/models — it belongs at the service layer boundary. CombatTrackerService is also pure Python, no Qt. PersistenceService is I/O-only, no Qt.

**Example — correct placement:**
```python
# src/monster_math/engine.py
from src.domain.models import Monster, Action, DamagePart  # domain only — correct

# src/combat/service.py
from src.domain.models import Monster                       # domain only — correct
from src.combat.models import CombatantState               # own package — correct

# src/ui/combat_tracker_tab.py
from src.combat.service import CombatTrackerService        # service — correct
# NEVER: from src.combat.models import ...                 # view imports domain = violation
```

### Pattern 2: JSON Persistence via PersistenceService (New)

**What:** A single `PersistenceService` reads/writes JSON files in the workspace root for all v2.0 mutable data. It is the only persistence code outside the already-existing `settings/service.py` and `workspace/setup.py`. SQLite is not used.

**Rationale for JSON over SQLite:** The data volume is small (tens of monsters, not thousands), the objects map cleanly to JSON dicts, the existing settings/ pattern is already JSON-based, and avoiding sqlite3 schema migrations keeps the codebase simpler. The workspace folder model means users can inspect and back up data as plain files.

**Files managed:**
```
workspace_root/
├── settings.json           # existing
├── monsters_overrides.json # v2.0: {name: {ability_scores, saves, actions, ...}}
├── equipment_presets.json  # v2.0: user-defined presets (default presets are code constants)
├── custom_bonuses.json     # v2.0: {monster_name: [{label, value}, ...]}
├── themes.json             # v2.0: {active_theme: str, custom_themes: [...]}
└── combat_state.json       # v2.0: session-only; last combat tracker state
```

**When to persist vs not:** Monster overrides persist when user clicks Save in MonsterEditorDialog. Combat state persists on app close (QMainWindow.closeEvent). Theme persists on settings save.

**Example:**
```python
# src/persistence/service.py
import json, dataclasses
from pathlib import Path
from src.domain.models import Monster

class PersistenceService:
    def __init__(self, workspace_root: Path) -> None:
        self._root = workspace_root

    def save_monster_overrides(self, overrides: dict[str, dict]) -> None:
        path = self._root / "monsters_overrides.json"
        path.write_text(json.dumps(overrides, indent=2), encoding="utf-8")

    def load_monster_overrides(self) -> dict[str, dict]:
        path = self._root / "monsters_overrides.json"
        if not path.exists():
            return {}
        try:
            return json.loads(path.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            return {}
```

### Pattern 3: MonsterMathEngine — Pure Recalculation

**What:** `MonsterMathEngine` takes a `Monster` + optional `Equipment` list + optional custom bonuses and returns a `DerivedStats` dataclass with recalculated values. It does not mutate the Monster. Callers decide whether to create a new Monster from the derived stats.

**D&D 5e derived value rules:**
- Ability modifier = `(score - 10) // 2` (already used in encounter/service.py)
- Proficiency bonus by CR: 0-4: +2, 5-8: +3, 9-12: +4, 13-16: +5, 17-20: +6, 21-24: +7, 25-28: +8, 29-30: +9
- Attack bonus = ability_modifier + proficiency_bonus (if proficient) + equipment_bonus
- AC = base_ac + shield_bonus + armor_bonus (armor replaces base if higher)
- HP average = hit_dice_count * ((hit_die_size / 2) + 0.5) + con_modifier * hit_dice_count
- Save bonus = ability_modifier + proficiency_bonus (if proficient in that save)

**Example:**
```python
# src/monster_math/engine.py
from src.domain.models import Monster
from src.monster_math.models import DerivedStats, EquipmentSet

_PROF_BONUS_BY_CR = {
    "0": 2, "1/8": 2, "1/4": 2, "1/2": 2,
    "1": 2, "2": 2, "3": 2, "4": 2,
    "5": 3, "6": 3, "7": 3, "8": 3,
    # ... full table
}

class MonsterMathEngine:
    def recalculate(self, monster: Monster, equipment: EquipmentSet) -> DerivedStats:
        prof = _PROF_BONUS_BY_CR.get(monster.cr, 2)
        str_mod = (monster.ability_scores.get("STR", 10) - 10) // 2
        dex_mod = (monster.ability_scores.get("DEX", 10) - 10) // 2
        # ... compute attack bonus, new AC, new saves, return DerivedStats
```

### Pattern 4: CombatantState — In-Memory with Optional JSON Snapshot

**What:** `CombatTrackerService` maintains a list of `CombatantState` objects in memory. Each combatant has: monster reference (name key), instance_index, current_hp, max_hp, conditions (list of `Condition(name, rounds_remaining)`), initiative, is_player_character.

**No deep condition rules:** Conditions are `name + rounds_remaining` only. No end-of-turn prompts, no concentration tracking. DM handles edge cases.

**State is not live-synced to disk.** It snapshots to `combat_state.json` on app close and reloads on startup. During a session it is pure in-memory state.

```python
# src/combat/models.py
from dataclasses import dataclass, field

@dataclass
class Condition:
    name: str
    rounds_remaining: int  # -1 = indefinite

@dataclass
class CombatantState:
    name: str                          # display name, e.g. "Goblin 2"
    monster_name: str                  # key into MonsterLibrary
    instance_index: int                # 1..N for multiple copies
    current_hp: int
    max_hp: int
    initiative: int
    is_player_character: bool = False
    conditions: list[Condition] = field(default_factory=list)
```

### Pattern 5: EncounterSidebarWidget as QDockWidget

**What:** The persistent encounter sidebar is a `QDockWidget` attached to `QMainWindow` in the `RightDockWidgetArea`. It is not part of any tab — it persists while the user switches tabs.

**Why QDockWidget:** Qt's `QMainWindow` layout has a dedicated dock widget area around the central `QTabWidget`. A dock widget placed here is always visible regardless of which tab is active. This is the correct Qt mechanism for a persistent sidebar. It cannot be implemented as a widget inside a tab without significant workaround.

**Integration with MainWindow:**
```python
# src/ui/app.py
from PySide6.QtCore import Qt
from PySide6.QtWidgets import QDockWidget
from src.ui.encounter_sidebar import EncounterSidebarWidget

class MainWindow(QMainWindow):
    def __init__(self):
        # ... existing setup ...
        self._sidebar_widget = EncounterSidebarWidget(
            library=self._library,
            combat_service=self._combat_service,
        )
        dock = QDockWidget("Encounter", self)
        dock.setAllowedAreas(Qt.DockWidgetArea.RightDockWidgetArea)
        dock.setFeatures(QDockWidget.DockWidgetFeature.NoDockWidgetFeatures)
        dock.setWidget(self._sidebar_widget)
        self.addDockWidget(Qt.DockWidgetArea.RightDockWidgetArea, dock)
```

**Signal flow from sidebar:** The sidebar emits `encounter_changed(list)` when members change. MainWindow routes this to AttackRollerTab and SavesTab, replacing the current `encounter_members_changed` signal from EncountersTab.

### Pattern 6: ThemeService + ThemeManager

**What:** `ThemeService` (service layer, pure Python, no Qt) loads/saves `ThemeDefinition` JSON from `workspace/themes.json`. `ThemeManager` (UI layer, has Qt import) holds a reference to `ThemeService`, generates a QSS string from the active theme, and calls `QApplication.instance().setStyleSheet(qss)`.

**Rationale for custom QSS over third-party library:** qt-material and QDarkStyleSheet are viable but add packaging complexity for a PyInstaller .exe. A hand-written QSS string that covers the key widget classes (QWidget, QPushButton, QLabel, QTextEdit, QGroupBox, QTabBar) is simpler to maintain and bundle.

**Theme model:**
```python
# src/theme/models.py
from dataclasses import dataclass

@dataclass
class ThemeDefinition:
    name: str
    background: str       # hex color, e.g. "#1e1e1e"
    foreground: str       # hex color
    accent: str           # hex color for buttons, selection
    is_high_contrast: bool = False
    font_family: str = "Segoe UI"
    font_size: int = 10   # points
```

**QSS generation:** `ThemeService.to_qss(theme: ThemeDefinition) -> str` produces a QSS string. `ThemeManager` calls this and applies via `QApplication.setStyleSheet()`. All tabs automatically repaint — no per-widget changes needed.

### Pattern 7: Roll20 Template Renderer

**What:** `Roll20TemplateRenderer` is added to `src/macro/` package. It receives a `MacroLineResult` where `template_name` is not None, and returns an HTML string suitable for `QTextEdit.insertHtml()`.

**Current state (v1.0):** `macro/service.py` already parses `&{template:default}{{name=XYZ}}{{field=value}}` syntax and populates `MacroLineResult.template_name`. The fields are already extracted by `MacroPreprocessor`. The missing piece is rendering them as a styled card.

**Rendering approach:** The renderer generates a simple HTML `<table>` with inline styles that mimic the Roll20 default template card: dark header row with monster name, alternating rows for fields. No external CSS dependencies — inline styles only, since QTextEdit renders a subset of HTML4 with inline style support.

```python
# src/macro/template_renderer.py
from src.macro.models import MacroLineResult

class Roll20TemplateRenderer:
    _HEADER_BG = "#4a1942"
    _ROW_BG_ODD = "#2b2b2b"
    _ROW_BG_EVEN = "#1e1e1e"

    def render(self, result: MacroLineResult) -> str:
        """Return HTML string for a Roll20 &{template:default} card."""
        # Extract name= field first, then render remaining fields as rows
        ...
```

---

## Data Flow

### Flow 1: Monster Editor → Persistent Override → Attack Roller

```
User edits stats in MonsterEditorDialog
    ↓
MonsterMathEngine.recalculate(monster, equipment) → DerivedStats
    ↓ (preview)
User clicks Save
    ↓
PersistenceService.save_monster_overrides({name: override_dict})
    ↓
MonsterLibrary.replace(updated_monster)
    ↓ (signal: library_changed)
AttackRollerTab.set_creatures() → rebuilds attack list with new stats
```

### Flow 2: Encounter Sidebar → Combat Tracker → Saves Tab

```
User drags monster from LibraryTab to EncounterSidebarWidget
    ↓
EncounterSidebarWidget.encounter_changed signal → MainWindow
    ↓
MainWindow routes to: AttackRollerTab.set_creatures()
                       SavesTab.set_encounter()
    ↓ (user clicks "Send to Combat Tracker")
CombatTrackerService.initialize_from_encounter(encounter)
    ↓
CombatTrackerTab refreshes HP bars and initiative rows
    ↓ (user selects monsters in CombatTrackerTab, clicks "Roll Saves")
SavesTab receives selected SaveParticipant list (bridge signal)
```

### Flow 3: Theme Change → Full Application Repaint

```
User selects theme in SettingsTab
    ↓
SettingsTab.settings_saved signal → MainWindow._on_settings_saved()
    ↓
ThemeService.get_theme(name) → ThemeDefinition
ThemeService.to_qss(theme) → qss_string
    ↓
QApplication.instance().setStyleSheet(qss_string)
    ↓
All widgets repaint automatically (Qt stylesheet cascade)
    ↓
PersistenceService.save(themes.json)
```

### Flow 4: Roll20 Template → Styled Card Output

```
User types &{template:default}{{name=Attack}}{{damage=[[2d6+4]]}} in MacroSandboxTab
    ↓
MacroPreprocessor.process_line() → CleanedMacro(template_name="default", fields={...})
    ↓
MacroSandboxService.execute() → MacroLineResult(template_name="default", inline_results=[...])
    ↓
Roll20TemplateRenderer.render(result) → html_string
    ↓
MacroSandboxTab._result_panel.append_html(html_string)
    ↓
QTextEdit renders HTML card (inline styles, no external CSS)
```

### State Management

```
In-memory state (session lifetime):
  MainWindow owns: MonsterLibrary, Roller, CombatTrackerService, current Encounter

Persisted state (disk, workspace root):
  SettingsService   → settings.json
  PersistenceService → monsters_overrides.json, equipment_presets.json,
                        custom_bonuses.json, themes.json, combat_state.json

Signals replace shared mutable state across tabs:
  EncounterSidebarWidget.encounter_changed → MainWindow → routes to tabs
  (tabs never hold references to each other — MainWindow is the bus)
```

---

## Integration Points

### Existing Boundaries (unchanged)

| Boundary | Communication | Notes |
|----------|--------------|-------|
| `views ↔ services` | Direct method calls only | No signal chains that cross the service boundary |
| `services ↔ domain` | Import + dataclass construction | Services never import from other services |
| `engine ↔ rest of project` | `roll_expression()` function call | Dice engine remains isolated |

### New Boundaries (v2.0)

| Boundary | Communication | Notes |
|----------|--------------|-------|
| `EncounterSidebarWidget ↔ tabs` | `encounter_changed` signal via MainWindow | MainWindow is the signal bus; tabs are signal consumers |
| `CombatTrackerTab ↔ SavesTab` | `jump_to_saves(participants)` signal via MainWindow | Bridge: select monsters in tracker → opens Saves tab with pre-loaded participants |
| `MonsterEditorDialog ↔ MonsterLibrary` | `editor_saved(monster)` signal | Editor emits; MainWindow calls `library.replace(monster)` |
| `ThemeManager ↔ all widgets` | `QApplication.setStyleSheet(qss)` | No per-widget signal needed; Qt stylesheet cascade handles repainting |
| `PersistenceService ↔ workspace/` | Both write to same folder | PersistenceService writes JSON files; WorkspaceManager manages subfolders. No conflict — JSON files go in workspace root, not subfolders |

---

## Anti-Patterns

### Anti-Pattern 1: Tabs Holding References to Each Other

**What people do:** `library_tab._encounters_tab.add_monster(m)` — direct attribute access between sibling tabs.

**Why it's wrong:** Creates tight coupling. If a tab is refactored or removed, every tab that references it breaks. v1.0 avoided this with signals through MainWindow.

**Do this instead:** All cross-tab communication through MainWindow signals. MainWindow is the routing bus. Each tab knows only about services and its own children.

### Anti-Pattern 2: Putting Qt in Service or Domain Layers

**What people do:** Importing `QObject`, emitting `Signal()`, or calling `QApplication.clipboard()` inside a service class.

**Why it's wrong:** Services become untestable (require a running QApplication), breaks the layer contract, and couples business logic to UI framework version.

**Do this instead:** Services return plain Python dataclasses. Views handle all Qt calls. The engine, domain, and services have zero Qt imports.

### Anti-Pattern 3: SQLite for This Project

**What people do:** Add SQLite for persistence because it's "more robust than JSON."

**Why it's wrong:** SQLite adds schema migration complexity (ALTER TABLE, version tracking), requires Python's sqlite3 module integration, and complicates PyInstaller packaging. The data set (tens of monsters, one combat session, one settings file) does not need a relational database.

**Do this instead:** JSON files in the workspace root, one file per data category. Already proven by `settings.json`. PersistenceService mirrors SettingsService's pattern.

### Anti-Pattern 4: Inlining MonsterMath Into the Editor Widget

**What people do:** Put all ability-score recalculation logic directly inside `MonsterEditorDialog._recalculate()`.

**Why it's wrong:** Cannot be unit-tested without a QWidget. Cannot be reused (e.g., by future import pipeline that auto-recalculates). Mixes UI with business rules.

**Do this instead:** `MonsterMathEngine` is pure Python in `src/monster_math/engine.py`. The editor calls `MonsterMathEngine.recalculate()` and displays the `DerivedStats` return value. Fully testable.

### Anti-Pattern 5: Global Stylesheet Override on Individual Widgets

**What people do:** Each widget calls `self.setStyleSheet(...)` with hardcoded colors to "fix" theming.

**Why it's wrong:** Widget-level stylesheets override application-level QSS with higher specificity. When the global theme changes, these widgets do not repaint. Results in a partially-themed UI that is hard to debug.

**Do this instead:** All color/font values come from the active `ThemeDefinition` via `ThemeService.to_qss()`, applied once at `QApplication` level. Individual widget `setStyleSheet()` calls are only permitted for structural, non-color properties (border, padding, spacing).

---

## Suggested Build Order

Dependencies between features drive the order. Features with no cross-feature dependencies are listed first.

### Phase 1: Domain Expansion + Persistence Foundation

Build first because everything else depends on it.

1. **Expand `domain/models.py`** — Add `Equipment`, `EquipmentPreset`, `MonsterModifiers`, `CombatantState`, `Condition` dataclasses. No logic, just data shapes.
2. **`src/persistence/service.py`** — PersistenceService for JSON read/write. Mirror SettingsService pattern. No UI.
3. **`src/monster_math/engine.py`** — MonsterMathEngine, pure Python. Add proficiency bonus table. Write tests.

### Phase 2: Monster Editor + Equipment Presets

Depends on Phase 1 (domain models, MonsterMathEngine, PersistenceService).

4. **`src/ui/monster_editor.py`** — MonsterEditorDialog. Calls MonsterMathEngine for live preview. Emits `editor_saved(Monster)` signal.
5. **Wire to LibraryTab** — Add Edit button in library_tab.py that opens MonsterEditorDialog for selected monster.
6. **Load overrides on startup** — MainWindow loads `monsters_overrides.json` via PersistenceService and applies to MonsterLibrary.

### Phase 3: Encounter Sidebar (Persistent Dock)

Depends on Phase 1 (domain models). Can proceed in parallel with Phase 2.

7. **`src/ui/encounter_sidebar.py`** — EncounterSidebarWidget as `QWidget` (content of the dock). Drag target, member list, encounter name, save/load buttons.
8. **Wire QDockWidget in MainWindow** — Wrap sidebar in QDockWidget, add to RightDockWidgetArea. Connect `encounter_changed` signal to AttackRollerTab and new SavesTab.
9. **`src/ui/saves_tab.py`** — Extract saves panel from EncountersTab into standalone SavesTab. Receives encounter from sidebar signal.

### Phase 4: Combat Tracker

Depends on Phase 1 (CombatantState domain model) and Phase 3 (EncounterSidebarWidget for initializing from encounter).

10. **`src/combat/service.py`** — CombatTrackerService. Methods: `initialize_from_encounter`, `apply_damage`, `heal`, `add_condition`, `tick_conditions`, `advance_turn`, `next_round`. Pure Python. Write tests.
11. **`src/ui/combat_tracker_tab.py`** — CombatTrackerTab. HP bar rows, condition chips, initiative order, player character subtab. Calls CombatTrackerService.
12. **Bridge signal: CombatTrackerTab → SavesTab** — "Roll Saves for selected" button emits selected participants; MainWindow routes to SavesTab.

### Phase 5: Save Roller Upgrades

Depends on Phase 3 (SavesTab extraction) and Phase 4 (CombatTracker bridge).

13. **Subset creature selection in SavesTab** — Checkboxes per participant row; only checked participants are rolled.
14. **Feature detection (Magic Resistance, Legendary Resistance)** — Keyword scan on `monster.raw_text` at import time OR at save-roll time. Add `has_magic_resistance`, `has_legendary_resistance` flags to domain model or detect at roll time.
15. **Auto-advantage toggles** — SavesTab shows detected features as checkboxes; checked = auto-advantage applied to those participants.

### Phase 6: Theming

No hard dependencies; can start after Phase 1 once the view layer is stable.

16. **`src/theme/` package** — ThemeDefinition, BUILTIN_THEMES dict, ThemeService.to_qss(), ThemeService load/save.
17. **`src/ui/theme_manager.py`** — ThemeManager singleton. Applies QSS to QApplication.
18. **Wire to SettingsTab** — Add theme selector, font picker to SettingsTab. On save, ThemeManager applies immediately.
19. **`RollOutputPanel.append_html()`** — Add HTML-aware append to support color-coded damage type output.
20. **Color-coded attack output** — AttackRollerTab renders damage types with colored spans (fire = orange, cold = blue, etc.) using `append_html()`.

### Phase 7: Roll20 Template Renderer

Depends on existing macro pipeline (stable since v1.0).

21. **`src/macro/template_renderer.py`** — Roll20TemplateRenderer. Takes MacroLineResult with template_name + inline_results, returns HTML string for default card.
22. **Wire to MacroSandboxTab** — When `MacroLineResult.template_name` is not None, render via template renderer instead of plain text output.

---

## Scaling Considerations

This is a single-user desktop application. Scaling is not a concern. The constraints that matter are:

| Concern | Bound | Approach |
|---------|-------|---------|
| Monster library size | ~500 monsters max in practice | In-memory MonsterLibrary is sufficient; no index needed |
| Combat tracker entries | ~20 combatants per encounter | In-memory list; no performance concern |
| JSON file sizes | KB range | No streaming or batching needed |
| Startup time | <2s target | Defer MonsterLibrary populate to first library tab activation if needed |
| PyInstaller .exe size | minimize | No third-party theme libraries; hand-written QSS avoids qt-material dependency |

---

## Sources

- PySide6 QDockWidget documentation: https://doc.qt.io/qtforpython-6/PySide6/QtWidgets/QDockWidget.html
- PySide6 QMainWindow documentation: https://doc.qt.io/qtforpython-6/PySide6/QtWidgets/QMainWindow.html
- Qt Dock Widget Example: https://doc.qt.io/qtforpython-6/examples/example_widgets_mainwindows_dockwidgets.html
- PySide6 Styling tutorial: https://doc.qt.io/qtforpython-6/tutorials/basictutorial/widgetstyling.html
- PySide6 QTextEdit (HTML support): https://doc.qt.io/qtforpython-6/PySide6/QtWidgets/QTextEdit.html
- Roll20 Roll Templates wiki: https://wiki.roll20.net/Roll_Templates
- D&D 5e SRD ability scores and modifiers: https://dnd5e.info/using-ability-scores/ability-scores-and-modifiers/
- D&D 5e Basic Rules / Monsters (proficiency bonus table): https://www.dndbeyond.com/sources/dnd/basic-rules-2014/monsters
- Direct codebase inspection: src/domain/models.py, src/encounter/service.py, src/ui/app.py, src/ui/encounters_tab.py, src/ui/attack_roller_tab.py, src/library/service.py, src/settings/service.py, src/workspace/setup.py

---

*Architecture research for: RollinRollin v2.0 Combat Manager*
*Researched: 2026-02-25*
