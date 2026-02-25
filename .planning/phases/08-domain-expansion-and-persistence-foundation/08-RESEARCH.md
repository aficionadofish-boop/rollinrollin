# Phase 8: Domain Expansion and Persistence Foundation - Research

**Researched:** 2026-02-25
**Domain:** Python dataclasses, JSON persistence, pure-Python math engine, PySide6 QTimer/closeEvent
**Confidence:** HIGH

<user_constraints>
## User Constraints (from CONTEXT.md)

### Locked Decisions

**Persistence categories:**
- Four categories: loaded monsters, encounters, modified monsters, macros
- Each category persisted independently with its own flush control
- Settings/preferences are NOT a flushable category (those stay separate)

**Flush UX in Settings:**
- Per-category flush buttons, each showing entry count (e.g. "Modified Monsters: 12 entries")
- "Clear All Data" button that flushes everything at once
- Always show a confirmation dialog before any flush operation (per-category and clear-all)

**Math validation flagging:**
- Flagged values shown in a distinct color (e.g. orange) with a hover tooltip
- Tooltip shows detailed breakdown: expected value vs actual, e.g. "Expected +5 (prof + STR), got +7 — custom +2"
- Engine distinguishes non-proficient / proficient / expertise / custom states for saves
- Engine validates attack to-hit and damage bonuses with the same detail level
- Validation only runs after edits — base imported monsters are NOT flagged
- When a mismatch is detected, offer a "Recalculate" button next to the flagged value (DM clicks to accept the calculated value); never auto-correct

**Spellcasting detection:**
- Auto-detect casting ability from Spellcasting trait text, pre-fill the field, DM can override
- Handle both 2014 dual-trait format (Spellcasting + Innate Spellcasting) and 2024 merged format
- Track multiple casting abilities per monster (Innate vs regular Spellcasting validate independently)
- When parser can't detect casting ability: default to highest mental stat (WIS, INT, CHA) and show a hint ("Spellcasting detected but casting ability assumed — verify")
- Spell attack bonus = casting mod + prof + focus bonus; spell save DC = 8 + casting mod + prof + focus bonus

**Save timing and feedback:**
- Periodic auto-save (e.g. every 30 seconds) plus save on close
- Subtle status bar text briefly showing "Saved" after each auto-save
- Data file lives in the same folder as the .exe (portable, consistent with v1.0 workspace approach)

### Claude's Discretion

- Corrupt data recovery strategy (backup + start fresh, or start fresh + warn)
- Auto-save interval (30s suggested, can adjust)
- JSON file structure and naming
- Internal domain model architecture
- Exact flag color choice

### Deferred Ideas (OUT OF SCOPE)

None — discussion stayed within phase scope

</user_constraints>

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|-----------------|
| PERSIST-01 | App stores loaded monsters, encounters, modified monsters, and macros in an internal data store that survives between sessions | PersistenceService pattern using JSON files in workspace root (same folder as .exe); four separate JSON files, one per category |
| PERSIST-02 | User can flush specific persistent data categories from Settings | Per-category flush buttons with entry count labels in SettingsTab; QMessageBox confirmation before flush; PersistenceService.flush_category() writes empty structure |
| PERSIST-03 | Data store loads automatically on app start and saves on close/change | MainWindow.__init__ calls PersistenceService.load_all(); MainWindow.closeEvent() calls PersistenceService.save_all(); QTimer repeating every 30s for auto-save |
| MATH-01 | When any base attribute changes, all derived values cascade automatically | MonsterMathEngine.recalculate(monster) returns DerivedStats; no mutations; caller applies; proficiency table covers all CR values |
| MATH-02 | When CR changes, proficiency bonus updates and cascades | CR-to-proficiency-bonus table in engine; recalculate() takes CR as input; same DerivedStats return covers all cascades |
| MATH-03 | Engine validates attack to-hit = proficiency + relevant ability modifier and flags mismatches | MathValidator.validate_action(action, monster) returns ValidationResult with expected, actual, delta, and state enum |
| MATH-04 | Engine validates saving throw bonuses against three accepted states (non-proficient, proficient, expertise); flags custom | MathValidator.validate_save(ability, bonus, monster) compares against three accepted values; returns SaveState enum |
| MATH-05 | On modified spellcasters, validates spell attack bonus and spell save DC | SpellcastingDetector.detect(monster) returns SpellcastingInfo(casting_ability, focus_bonus); MathValidator uses this for spell validation |

</phase_requirements>

---

## Summary

Phase 8 establishes the foundation that every subsequent v2.0 phase depends on. It has two distinct halves: a JSON persistence layer and a pure-Python Monster Math Engine. Both are service-layer components with no Qt dependencies — they are testable in pure Python and consumed by views in later phases.

The persistence layer extends the proven `SettingsService` pattern already in the codebase. The four data categories (loaded monsters, encounters, modified monsters, macros) each map to a separate JSON file in the workspace root. The CONTEXT.md decision to locate data "in the same folder as the .exe" is already the v1.0 workspace model: `WorkspaceManager` is initialized with `Path.home() / "RollinRollin"` at runtime and the `.exe` is portable within that folder. For the frozen build, the workspace root resolves to the same folder the `.exe` lives in via `sys.executable` resolution — this requires a small update to `WorkspaceManager` or `app.py` startup logic.

The Monster Math Engine is a pure recalculation service: given a `Monster` and optional modifications, it returns a `DerivedStats` dataclass. A companion `MathValidator` compares actual stored values against expected calculated values and returns structured `ValidationResult` objects — never modifying data. Both components are fully testable without a QApplication instance.

**Primary recommendation:** Model PersistenceService exactly like SettingsService (json.loads/json.dumps, workspace_root constructor arg, graceful fallback on missing/corrupt file). Build MonsterMathEngine as a pure function with a lookup table for proficiency bonuses. Separate validation into MathValidator so the engine and validator can be tested and evolved independently.

---

## Standard Stack

### Core

| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| Python stdlib `json` | 3.12 | JSON serialize/deserialize | Already used in SettingsService; zero new dependencies |
| Python stdlib `dataclasses` | 3.12 | Domain model dataclasses | Already the pattern in domain/models.py; `dataclasses.asdict()` produces JSON-serializable dicts |
| Python stdlib `pathlib.Path` | 3.12 | File path operations | Already used everywhere in the codebase |
| PySide6 `QTimer` | 6.10.2 | Auto-save periodic trigger | Already used in macro_editor.py for debounce; same pattern applies |
| PySide6 `QMainWindow.closeEvent` | 6.10.2 | Save-on-close hook | Standard Qt lifecycle override; not yet implemented in app.py |
| PySide6 `QMessageBox` | 6.10.2 | Flush confirmation dialogs | Already used in app.py for settings guard |
| PySide6 `QStatusBar` | 6.10.2 | "Saved" status feedback | QMainWindow.statusBar() always available; show temporary message with showMessage(text, timeout_ms) |

### Supporting

| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| Python stdlib `re` | 3.12 | Spellcasting trait text parsing | Detect "Spellcasting" and "Innate Spellcasting" trait names and extract casting ability |
| Python stdlib `copy` | 3.12 | Defensive copy of domain objects | Use `dataclasses.replace()` (preferred) or `copy.deepcopy()` when creating modified monster variants |

### Alternatives Considered

| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| `json` stdlib | `sqlite3` stdlib | SQLite adds schema migration complexity, no benefit at this data scale (KB-range files, tens of monsters). JSON mirrors the existing settings.json pattern exactly. |
| Separate JSON files per category | Single `app_data.json` with top-level keys | Single file is slightly simpler but means one corrupt entry can block loading all categories. Separate files enable independent flush and independent recovery. |
| Pure Python math engine | Inline QSpinBox signal recalculation | Inline recalculation in widgets is untestable, mixes UI with business rules, and cannot be reused by Phase 9 editor. Pure Python engine is the architectural mandate. |

**Installation:** No new packages required. All dependencies are in Python 3.12 stdlib or PySide6 (already installed).

---

## Architecture Patterns

### Recommended Project Structure

```
src/
├── domain/
│   └── models.py              # ADD new dataclasses here (ModifiedMonster, SpellcastingInfo, etc.)
├── persistence/               # NEW PACKAGE
│   ├── __init__.py
│   └── service.py             # PersistenceService
├── monster_math/              # NEW PACKAGE
│   ├── __init__.py
│   ├── engine.py              # MonsterMathEngine + proficiency table
│   ├── validator.py           # MathValidator (separate from engine)
│   └── spellcasting.py        # SpellcastingDetector
└── ui/
    ├── app.py                 # MODIFY: add closeEvent, auto-save timer, statusBar
    └── settings_tab.py        # MODIFY: add flush section with per-category buttons
```

### Pattern 1: PersistenceService — Mirror SettingsService

**What:** A single `PersistenceService` class that reads/writes JSON for all four data categories. Constructor takes `workspace_root: Path`. Each category has its own `load_X()` and `save_X()` method pair. `flush_X()` writes an empty structure (does not delete the file — keeps format consistent).

**When to use:** All persistence for loaded monsters, encounters, modified monsters, macros.

**Workspace root decision:** Current `app.py` uses `Path.home() / "RollinRollin"` as workspace root. The CONTEXT.md portable .exe requirement means the data file should live next to the `.exe`. For the frozen build, `Path(sys.executable).parent` gives the `.exe` folder. Implement a resolver function:

```python
# src/workspace/setup.py (add helper)
import sys
from pathlib import Path

def resolve_workspace_root() -> Path:
    """Return the workspace root: next to .exe when frozen, home/RollinRollin in dev."""
    if getattr(sys, 'frozen', False):
        return Path(sys.executable).parent
    return Path.home() / "RollinRollin"
```

Then in `app.py`:
```python
from src.workspace.setup import resolve_workspace_root
self._workspace_manager = WorkspaceManager(resolve_workspace_root())
```

**PersistenceService example:**

```python
# src/persistence/service.py
from __future__ import annotations
import json
from pathlib import Path

_FILENAMES = {
    "loaded_monsters": "loaded_monsters.json",
    "encounters":      "encounters.json",
    "modified_monsters": "modified_monsters.json",
    "macros":          "macros.json",
}

class PersistenceService:
    def __init__(self, workspace_root: Path) -> None:
        self._root = workspace_root

    def _load(self, category: str) -> dict | list:
        path = self._root / _FILENAMES[category]
        if not path.exists():
            return {} if category == "modified_monsters" else []
        try:
            return json.loads(path.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            # Corrupt data strategy: return empty, warn via return value
            return {} if category == "modified_monsters" else []

    def _save(self, category: str, data: dict | list) -> None:
        path = self._root / _FILENAMES[category]
        path.write_text(json.dumps(data, indent=2), encoding="utf-8")

    def flush(self, category: str) -> None:
        """Write empty structure for category. Does not delete file."""
        empty = {} if category == "modified_monsters" else []
        self._save(category, empty)

    def load_modified_monsters(self) -> dict:  # {name: {ability_scores, saves, ...}}
        return self._load("modified_monsters")

    def save_modified_monsters(self, data: dict) -> None:
        self._save("modified_monsters", data)

    def count(self, category: str) -> int:
        """Return entry count for flush button label."""
        data = self._load(category)
        return len(data)

    # ... load_loaded_monsters, save_loaded_monsters, etc.
```

**Corrupt data strategy (Claude's Discretion):** On `json.JSONDecodeError`, return the empty structure and do NOT write over the corrupt file on load — only overwrite on the next explicit save. This gives the user one chance to manually recover the file if needed. The UI will display as if the category is empty; on next auto-save it will be overwritten with the in-memory state (which was empty at load). No backup file is written — keeps the implementation simple and consistent with `SettingsService` which uses the same silent-fallback strategy.

### Pattern 2: Auto-Save with QTimer + Save on Close

**What:** `MainWindow` owns a `QTimer` that triggers every 30 seconds to persist all four categories. `closeEvent()` override calls save-all before accepting the close.

**Why QTimer:** Already used in `macro_editor.py` for debounce. Same API, same pattern. No new concepts.

**Example:**

```python
# src/ui/app.py additions
from PySide6.QtCore import QTimer
from PySide6.QtWidgets import QStatusBar

class MainWindow(QMainWindow):
    def __init__(self, parent=None):
        super().__init__(parent)
        # ... existing setup ...

        # Persistence service
        self._persistence = PersistenceService(self._workspace_manager.root)
        self._load_persisted_data()

        # Auto-save timer: 30 seconds
        self._autosave_timer = QTimer(self)
        self._autosave_timer.setInterval(30_000)
        self._autosave_timer.timeout.connect(self._autosave)
        self._autosave_timer.start()

        # Status bar for "Saved" feedback
        self.statusBar().showMessage("Ready")

    def _autosave(self) -> None:
        self._save_persisted_data()
        self.statusBar().showMessage("Saved", 2000)  # disappears after 2s

    def closeEvent(self, event) -> None:
        self._save_persisted_data()
        event.accept()  # allow close

    def _load_persisted_data(self) -> None:
        # Load each category and hydrate in-memory state
        ...

    def _save_persisted_data(self) -> None:
        # Serialize each in-memory category and write to disk
        ...
```

### Pattern 3: MonsterMathEngine — Pure Recalculation

**What:** `MonsterMathEngine.recalculate(monster: Monster) -> DerivedStats`. Pure Python, no Qt, no I/O. Takes current `Monster` state and returns a complete `DerivedStats` dataclass. Never mutates the input monster.

**Proficiency bonus table (D&D 5e, verified):**

```python
# src/monster_math/engine.py
_PROF_BY_CR: dict[str, int] = {
    "0": 2, "1/8": 2, "1/4": 2, "1/2": 2,
    "1": 2, "2": 2, "3": 2, "4": 2,
    "5": 3, "6": 3, "7": 3, "8": 3,
    "9": 4, "10": 4, "11": 4, "12": 4,
    "13": 5, "14": 5, "15": 5, "16": 5,
    "17": 6, "18": 6, "19": 6, "20": 6,
    "21": 7, "22": 7, "23": 7, "24": 7,
    "25": 8, "26": 8, "27": 8, "28": 8,
    "29": 9, "30": 9,
}

def _ability_mod(score: int) -> int:
    return (score - 10) // 2  # floor division — already established in encounter/service.py

def _prof_bonus(cr: str) -> int:
    return _PROF_BY_CR.get(cr, 2)  # default 2 for unknown CR
```

**DerivedStats dataclass:**

```python
# src/monster_math/engine.py (or models.py in same package)
from dataclasses import dataclass, field

@dataclass
class DerivedStats:
    proficiency_bonus: int
    ability_modifiers: dict[str, int]   # {"STR": 3, "DEX": 1, ...}
    expected_saves: dict[str, int]      # {"STR": -1, "DEX": 3, ...} — mod only for non-proficient
    expected_proficient_saves: dict[str, int]  # mod + prof for each ability
    expected_expertise_saves: dict[str, int]   # mod + 2*prof for each ability
```

### Pattern 4: MathValidator — Separate from Engine

**What:** `MathValidator` compares a `Monster`'s actual stored values against the `DerivedStats` from `MonsterMathEngine`. Returns `ValidationResult` objects per field. Never called on base imported monsters (only on modified ones). Engine and validator are separate classes in the same package.

**Rationale for separation:** The engine recalculates; the validator compares. Mixing them in one class would make the engine stateful and harder to test. The editor calls engine for live preview; it calls validator to flag mismatches.

```python
# src/monster_math/validator.py
from __future__ import annotations
from dataclasses import dataclass
from enum import Enum
from src.domain.models import Monster
from src.monster_math.engine import DerivedStats

class SaveState(Enum):
    NON_PROFICIENT = "non_proficient"  # actual == ability_mod
    PROFICIENT     = "proficient"      # actual == ability_mod + prof
    EXPERTISE      = "expertise"       # actual == ability_mod + 2*prof
    CUSTOM         = "custom"          # anything else

@dataclass
class SaveValidation:
    ability: str
    actual: int
    expected_non_proficient: int
    expected_proficient: int
    expected_expertise: int
    state: SaveState

    @property
    def is_flagged(self) -> bool:
        return self.state == SaveState.CUSTOM

    @property
    def tooltip(self) -> str:
        if not self.is_flagged:
            return ""
        delta = self.actual - self.expected_proficient
        sign = "+" if delta > 0 else ""
        return (
            f"Expected {self.expected_proficient:+d} (prof + {self.ability}), "
            f"got {self.actual:+d} — custom {sign}{delta}"
        )

class MathValidator:
    def validate_saves(self, monster: Monster, derived: DerivedStats) -> list[SaveValidation]:
        results = []
        for ability, actual in monster.saves.items():
            mod = derived.ability_modifiers.get(ability, 0)
            prof = derived.proficiency_bonus
            np_val = mod
            p_val  = mod + prof
            ex_val = mod + 2 * prof
            if actual == np_val:
                state = SaveState.NON_PROFICIENT
            elif actual == p_val:
                state = SaveState.PROFICIENT
            elif actual == ex_val:
                state = SaveState.EXPERTISE
            else:
                state = SaveState.CUSTOM
            results.append(SaveValidation(
                ability=ability, actual=actual,
                expected_non_proficient=np_val,
                expected_proficient=p_val,
                expected_expertise=ex_val,
                state=state,
            ))
        return results
```

### Pattern 5: SpellcastingDetector

**What:** `SpellcastingDetector.detect(monster: Monster) -> list[SpellcastingInfo]`. Scans `monster.actions` for entries whose `name` matches "Spellcasting" or "Innate Spellcasting" and extracts the casting ability from the `raw_text`. Returns a list (multiple entries for 2014 dual-trait format).

**STATE.md decision:** Feature detection searches `Monster.actions` (not `raw_text`) to avoid lore-paragraph false positives. The `raw_text` field on each `Action` contains the full trait text.

```python
# src/monster_math/spellcasting.py
from __future__ import annotations
import re
from dataclasses import dataclass
from src.domain.models import Monster

_ABILITY_PATTERN = re.compile(
    r"\b(Strength|Dexterity|Constitution|Intelligence|Wisdom|Charisma)\b",
    re.IGNORECASE,
)
_ABILITY_MAP = {
    "strength": "STR", "dexterity": "DEX", "constitution": "CON",
    "intelligence": "INT", "wisdom": "WIS", "charisma": "CHA",
}
_MENTAL_STATS = ["WIS", "INT", "CHA"]  # priority order for fallback

@dataclass
class SpellcastingInfo:
    trait_name: str          # "Spellcasting" or "Innate Spellcasting"
    casting_ability: str     # "INT", "WIS", "CHA", etc.
    is_assumed: bool         # True if we guessed rather than found in text
    focus_bonus: int = 0     # default 0; set by user in Monster Editor

class SpellcastingDetector:
    def detect(self, monster: Monster) -> list[SpellcastingInfo]:
        results = []
        for action in monster.actions:
            name_lower = action.name.lower()
            if "spellcasting" not in name_lower:
                continue
            match = _ABILITY_PATTERN.search(action.raw_text)
            if match:
                ability = _ABILITY_MAP[match.group(1).lower()]
                results.append(SpellcastingInfo(
                    trait_name=action.name,
                    casting_ability=ability,
                    is_assumed=False,
                ))
            else:
                # Fallback: highest mental stat
                assumed = max(
                    _MENTAL_STATS,
                    key=lambda a: monster.ability_scores.get(a, 10),
                )
                results.append(SpellcastingInfo(
                    trait_name=action.name,
                    casting_ability=assumed,
                    is_assumed=True,
                ))
        return results
```

### Pattern 6: Domain Model Additions (domain/models.py)

**What:** Phase 8 adds new dataclasses to `src/domain/models.py`. These are data shapes only — no logic. They define the contracts that Phase 9 (Monster Editor) and beyond will depend on.

**Required additions:**

```python
# src/domain/models.py additions

from enum import Enum

class SaveProficiencyState(Enum):
    NON_PROFICIENT = "non_proficient"
    PROFICIENT     = "proficient"
    EXPERTISE      = "expertise"
    CUSTOM         = "custom"

@dataclass
class SpellcastingInfo:
    trait_name: str
    casting_ability: str    # "INT", "WIS", "CHA"
    is_assumed: bool
    focus_bonus: int = 0    # user-settable in Phase 9 editor

@dataclass
class MonsterModification:
    """Overrides for a base monster. Stored in modified_monsters.json.
    Fields are Optional: None means 'use base monster value'.
    """
    base_name: str                              # key into MonsterLibrary
    custom_name: Optional[str] = None          # if user renamed the modified copy
    ability_scores: dict[str, int] = field(default_factory=dict)
    saves: dict[str, int] = field(default_factory=dict)
    hp: Optional[int] = None
    ac: Optional[int] = None
    cr: Optional[str] = None
    spellcasting_infos: list[SpellcastingInfo] = field(default_factory=list)
    # Phase 9 adds: equipment, custom_bonuses — placeholders only in Phase 8
```

**Serialization note:** `dataclasses.asdict()` on `MonsterModification` produces a JSON-serializable dict. On load, reconstruct with `MonsterModification(**filtered_data)` using the same `known` field filter as `SettingsService`.

### Pattern 7: Flush UI in Settings Tab

**What:** A new "Data" section at the bottom of `SettingsTab` with per-category flush rows. Each row: label with entry count + flush button. A "Clear All Data" button below. All trigger `QMessageBox.question()` confirmation.

**Count display:** `PersistenceService.count(category)` is called when the Settings tab is shown (not on every auto-save) to keep the count fresh without unnecessary disk reads. Connect to `SettingsTab.showEvent()` or a `refresh_counts()` method called when MainWindow switches to the Settings tab.

```python
# src/ui/settings_tab.py additions
def _build_data_flush_group(self) -> QGroupBox:
    group = QGroupBox("Data Management")
    layout = QVBoxLayout(group)

    self._flush_labels: dict[str, QLabel] = {}
    self._flush_btns: dict[str, QPushButton] = {}

    categories = [
        ("loaded_monsters", "Loaded Monsters"),
        ("encounters",      "Encounters"),
        ("modified_monsters", "Modified Monsters"),
        ("macros",          "Macros"),
    ]
    for key, display_name in categories:
        row = QHBoxLayout()
        label = QLabel(f"{display_name}: — entries")
        btn = QPushButton(f"Flush {display_name}")
        btn.clicked.connect(lambda checked, k=key, n=display_name: self._on_flush(k, n))
        self._flush_labels[key] = label
        self._flush_btns[key] = btn
        row.addWidget(label)
        row.addWidget(btn)
        layout.addLayout(row)

    clear_all_btn = QPushButton("Clear All Data")
    clear_all_btn.clicked.connect(self._on_clear_all)
    layout.addWidget(clear_all_btn)
    return group

def _on_flush(self, category: str, display_name: str) -> None:
    reply = QMessageBox.question(
        self, "Confirm Flush",
        f"Flush all {display_name} data? This cannot be undone.",
        QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.Cancel,
    )
    if reply == QMessageBox.StandardButton.Yes:
        self.flush_requested.emit(category)

def refresh_counts(self, counts: dict[str, int]) -> None:
    """Called by MainWindow when switching to Settings tab."""
    for key, label in self._flush_labels.items():
        n = counts.get(key, 0)
        entries = "entry" if n == 1 else "entries"
        display = key.replace("_", " ").title()
        label.setText(f"{display}: {n} {entries}")
```

**New signal on SettingsTab:** `flush_requested = Signal(str)` — emits category key. `clear_all_requested = Signal()`. MainWindow connects these to `PersistenceService.flush()` calls.

### Anti-Patterns to Avoid

- **Calling MonsterMathEngine from a QSpinBox signal directly:** Guard spin box `valueChanged` slots with a `_recalculating: bool` flag and `blockSignals(True/False)` to prevent signal cascades. Per STATE.md architectural decision.
- **Auto-correcting flagged values:** The validator identifies mismatches but never writes back. The "Recalculate" button is in Phase 9 (Monster Editor). Phase 8 only builds the engine and validator — no editor UI except the Settings flush section.
- **Serializing Monster objects directly to persistence JSON:** Serialize name references only for encounters and loaded monsters. Full serialization only for modified monsters (MonsterModification dict). Per STATE.md: encounter format is `{name: str, count: int}` only.
- **Flagging base imported monsters:** Validation flag (`is_modified = False` on a Monster) must gate all validation calls. Do not run MathValidator on monsters loaded fresh from Markdown import.
- **Single json file for all categories:** Separate files enable independent flush without touching other categories. The SettingsService pattern already proves this works.

---

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| JSON serialization of dataclasses | Custom serializer with __dict__ | `dataclasses.asdict()` | Handles nested dataclasses, lists, dicts; already used in SettingsService |
| Auto-save timer | Manual thread with sleep() | `QTimer` with `setInterval` + `start()` | Thread-safe Qt timer; already in codebase (macro_editor.py); no threading complexity |
| Save on close | Subclass QApplication | Override `QMainWindow.closeEvent()` | Standard Qt pattern; event.accept() proceeds; no QApplication changes needed |
| Status bar "Saved" message | Custom overlay widget | `QMainWindow.statusBar().showMessage(text, timeout_ms)` | Built-in; showMessage with non-zero timeout auto-clears; no timer needed |
| Proficiency bonus calculation | Formula `math.ceil(1 + CR/4)` | Lookup table `_PROF_BY_CR` | The formula doesn't work for fractional CRs (1/8, 1/4, 1/2). Lookup table is explicit, testable, and handles all edge cases. |
| Ability modifier | Custom rounding | `(score - 10) // 2` | Already established in encounter/service.py; floor division handles negative scores correctly (STR 8 → -1, STR 1 → -5) |

**Key insight:** The codebase already has all the patterns Phase 8 needs. PersistenceService is a copy of SettingsService with four category methods. MonsterMathEngine is a pure function with a lookup table. The only truly new concept is `closeEvent()` override and `statusBar()` usage — both one-liners in Qt.

---

## Common Pitfalls

### Pitfall 1: Workspace Root — Dev vs Frozen Mismatch

**What goes wrong:** In dev, `Path.home() / "RollinRollin"` works. In frozen .exe, users expect data next to the .exe (portable). If the resolver isn't updated, the frozen app writes to `%USERPROFILE%\RollinRollin\` while the user expects data alongside the .exe.

**Why it happens:** The current `app.py` hardcodes `Path.home() / "RollinRollin"`. The CONTEXT.md explicitly requires portable behavior ("same folder as the .exe").

**How to avoid:** Add `resolve_workspace_root()` to `workspace/setup.py`. Use `sys.frozen` check: `Path(sys.executable).parent` when frozen, `Path.home() / "RollinRollin"` in dev. Call this in `MainWindow.__init__` instead of the hardcoded path.

**Warning signs:** If settings.json is written to a different location than where the user's .exe lives — this is the symptom.

### Pitfall 2: QSpinBox Signal Cascade Loops

**What goes wrong:** If Phase 9's editor wires `QSpinBox.valueChanged` → recalculate → update another spin box → `valueChanged` fires again → infinite loop. Phase 8 establishes domain model and engine, but the signal guard pattern must be documented here for Phase 9.

**Why it happens:** Qt signal/slot connections are synchronous by default. Updating a widget in a slot triggers that widget's signals while still inside the first slot.

**How to avoid:** Use a `_recalculating: bool` flag in the editor widget. At the start of any recalculation triggered by a signal: if `_recalculating: return`. Set `_recalculating = True`, do updates, set `_recalculating = False`. Also wrap batch updates with `widget.blockSignals(True)` / `widget.blockSignals(False)`.

**Warning signs:** CPU spike on any stat change; app freezes on editing.

### Pitfall 3: `dataclasses.asdict()` Fails on Non-Primitive Fields

**What goes wrong:** If `MonsterModification` contains a field that is a custom class not made of basic Python types (int, str, list, dict), `dataclasses.asdict()` will produce un-JSON-serializable output (e.g., an `Enum` value becomes an `Enum` object, not a string).

**Why it happens:** `dataclasses.asdict()` recursively converts nested dataclasses but not Enums or custom types.

**How to avoid:** Use `Enum(str, ...)` pattern (`class SaveProficiencyState(str, Enum)`) so enum values serialize as plain strings automatically — exactly the same pattern as `DamageType(str, Enum)` already in `domain/models.py`. Alternatively, serialize explicitly: `{k: v.value for k, v in ...}`.

**Warning signs:** `TypeError: Object of type SaveState is not JSON serializable` on first save.

### Pitfall 4: Loading Persisted Monsters Requires Library to be Populated First

**What goes wrong:** On startup, `load_loaded_monsters()` returns a list of monster names. If `MonsterLibrary` is empty (no Markdown files imported yet), resolving by name fails silently and the persisted encounter is empty.

**Why it happens:** The persisted data stores names, not full Monster objects. Names must resolve against the library. But the library is populated from Markdown import, which is a user action.

**How to avoid:** Persisted loaded monsters = the Markdown files the user previously imported. The correct persistence for "loaded monsters" is the list of file paths (or folder paths) from the last import session. On startup, attempt to re-import those files silently. If a file is gone, report it as a warning (not an error) and skip it.

Alternatively: if "loaded monsters" means only the in-session monster library contents (not the source files), then the serialization format needs to be a full Monster dict, which is more complex. Clarification: per CONTEXT.md, the four categories are "loaded monsters, encounters, modified monsters, macros" — loaded monsters = what the user imported into the library. The simplest approach is to persist the import source paths.

**Warning signs:** Library is empty on app restart even though user previously imported monsters.

### Pitfall 5: Fractional CR Values in Proficiency Table

**What goes wrong:** `Monster.cr` is stored as a string (`"1/2"`, `"1/4"`, `"1/8"`, `"0"`). If the proficiency lookup uses `int(cr)` or `float(cr)`, fractional CRs raise `ValueError`.

**Why it happens:** Python `int("1/2")` raises ValueError. The CR field is intentionally a string to handle fractions.

**How to avoid:** The lookup table uses string keys (`"1/2"`, `"1/4"`, etc.) matching the `Monster.cr` format exactly. Never try to parse CR as a number — always use the lookup table with a default of 2 for unknown values.

**Warning signs:** `ValueError: invalid literal for int() with base 10: '1/2'` in test output.

### Pitfall 6: Count Display Staleness

**What goes wrong:** The flush button shows "Modified Monsters: 12 entries" but the user just flushed and it still shows 12.

**Why it happens:** `refresh_counts()` is only called when the Settings tab becomes visible (via `currentChanged` signal). If flush happens and the user stays on Settings tab, the count is not refreshed.

**How to avoid:** Call `refresh_counts()` after every flush operation completes, not just on tab show. Connect the `flush_requested` signal chain to refresh after the flush is executed.

---

## Code Examples

Verified patterns from official sources and existing codebase:

### Proficiency Bonus by CR (D&D 5e verified)

```python
# Source: D&D 5e Basic Rules (PHB p.8, Monster Manual p.8)
# Confirmed: proficiency by CR bracket, 4 CRs per step
_PROF_BY_CR: dict[str, int] = {
    "0": 2, "1/8": 2, "1/4": 2, "1/2": 2,
    "1": 2, "2": 2, "3": 2, "4": 2,
    "5": 3, "6": 3, "7": 3, "8": 3,
    "9": 4, "10": 4, "11": 4, "12": 4,
    "13": 5, "14": 5, "15": 5, "16": 5,
    "17": 6, "18": 6, "19": 6, "20": 6,
    "21": 7, "22": 7, "23": 7, "24": 7,
    "25": 8, "26": 8, "27": 8, "28": 8,
    "29": 9, "30": 9,
}
```

### Ability Modifier (already in codebase)

```python
# Source: src/encounter/service.py line 63 — established pattern
def _ability_mod(score: int) -> int:
    return (score - 10) // 2  # floor division: STR 8 → -1, STR 1 → -5
```

### QTimer Auto-Save (existing pattern in codebase)

```python
# Source: src/ui/macro_editor.py lines 133-137 — QTimer already in use
# Auto-save variant (repeating, not single-shot):
self._autosave_timer = QTimer(self)
self._autosave_timer.setInterval(30_000)   # 30 seconds
# NOT setSingleShot(True) — this one repeats
self._autosave_timer.timeout.connect(self._autosave)
self._autosave_timer.start()
```

### Status Bar Temporary Message

```python
# Source: PySide6 QMainWindow docs — statusBar() always available on QMainWindow
# 2000ms = 2 seconds before reverting to permanent message
self.statusBar().showMessage("Saved", 2000)
```

### closeEvent Override (new to this project)

```python
# Source: PySide6 QMainWindow.closeEvent documentation
def closeEvent(self, event: QCloseEvent) -> None:
    """Called by Qt when the window is about to close."""
    self._save_persisted_data()
    event.accept()  # proceed with close; call event.ignore() to cancel
```

### JSON Serialize/Deserialize with dataclasses (existing pattern)

```python
# Source: src/settings/service.py — established pattern
import dataclasses, json

# Serialize:
data = dataclasses.asdict(my_dataclass_instance)
path.write_text(json.dumps(data, indent=2), encoding="utf-8")

# Deserialize (with unknown-key filtering):
raw = json.loads(path.read_text(encoding="utf-8"))
known = {f.name for f in dataclasses.fields(MyDataclass)}
filtered = {k: v for k, v in raw.items() if k in known}
instance = MyDataclass(**filtered)
```

### Enum as String (existing pattern)

```python
# Source: src/domain/models.py DamageType — established pattern
class SaveProficiencyState(str, Enum):
    NON_PROFICIENT = "non_proficient"
    PROFICIENT     = "proficient"
    EXPERTISE      = "expertise"
    CUSTOM         = "custom"
# Serializes automatically: json.dumps(SaveProficiencyState.PROFICIENT) → '"proficient"'
```

### Spell Attack Bonus Validation

```python
# D&D 5e rule: spell_attack = casting_mod + prof_bonus + focus_bonus
# D&D 5e rule: spell_save_dc = 8 + casting_mod + prof_bonus + focus_bonus

def validate_spell_attack(
    actual_bonus: int,
    casting_ability: str,
    monster: Monster,
    derived: DerivedStats,
    focus_bonus: int = 0,
) -> tuple[int, int]:  # (expected, delta)
    mod = derived.ability_modifiers.get(casting_ability, 0)
    expected = mod + derived.proficiency_bonus + focus_bonus
    return expected, actual_bonus - expected

def expected_spell_save_dc(
    casting_ability: str,
    derived: DerivedStats,
    focus_bonus: int = 0,
) -> int:
    mod = derived.ability_modifiers.get(casting_ability, 0)
    return 8 + mod + derived.proficiency_bonus + focus_bonus
```

---

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| Markdown-only encounter files (EncounterService) | Markdown files PLUS internal JSON for session state | Phase 8 | Markdown stays for user-facing export; JSON handles runtime persistence transparently |
| No `closeEvent` override | `closeEvent()` saves persisted data | Phase 8 | App is no longer stateless between sessions |
| `Path.home() / "RollinRollin"` hardcoded | `resolve_workspace_root()` checks `sys.frozen` | Phase 8 | Portable .exe behavior matches user expectation |

**Deprecated/outdated:**
- EncountersTab as the sole source of encounter state: v2.0 moves encounter state into persistence; EncountersTab will be split in Phase 10. Phase 8 does not change EncountersTab — it only builds the infrastructure.

---

## Open Questions

1. **Loaded monsters serialization strategy**
   - What we know: "Loaded monsters" must survive app restart. Monster objects are large nested structures.
   - What's unclear: Should persistence store full Monster dicts (large, duplicates Markdown data) or source file paths (small, but requires re-parse on startup)?
   - Recommendation: Persist source file paths. On startup, silently re-import from those paths. If a path no longer exists, skip and warn via status bar. This keeps the JSON small and avoids maintaining a duplicate full-monster serialization format. Aligns with the Markdown-as-source-of-truth principle.

2. **Macro persistence format**
   - What we know: Macros are already saved as `.md` files in the `macros/` workspace subfolder by `MacroSidebar`.
   - What's unclear: Does "macros" as a persistence category mean the list of saved macro files, or something else?
   - Recommendation: "Macros" persistence = the contents of the last-active macro editor text (the unsaved buffer). This lets the DM resume where they left off without clicking "Save" on the macro. The `macros/` subfolder files remain separate. Store a single string in `macros.json`.

3. **Encounter persistence overlap with EncounterService**
   - What we know: `EncounterService` already saves/loads encounters as Markdown files. The new persistence layer adds JSON persistence.
   - What's unclear: Should the active encounter be stored in JSON (internal, auto-saved) or only via the existing Markdown save/load workflow?
   - Recommendation: Store the active encounter in `encounters.json` as `{name: str, members: [{name: str, count: int}]}`. This is the STATE.md decision ("Encounter persistence format: `{name: str, count: int}` only — never serialize Monster objects"). The Markdown save/load workflow stays for user-facing named encounter files; JSON handles session state.

---

## Sources

### Primary (HIGH confidence)

- Direct codebase inspection: `src/settings/service.py` — SettingsService pattern (json.loads/dumps, dataclasses.asdict, known-field filter, graceful fallback)
- Direct codebase inspection: `src/domain/models.py` — existing dataclass patterns, DamageType(str, Enum) pattern
- Direct codebase inspection: `src/ui/macro_editor.py` — QTimer debounce pattern (lines 128-137)
- Direct codebase inspection: `src/ui/app.py` — MainWindow structure, QMessageBox confirmation pattern, QTabWidget wiring
- Direct codebase inspection: `src/encounter/service.py` — `_resolve_save_bonus()` ability modifier formula established
- Direct codebase inspection: `src/workspace/setup.py` — WorkspaceManager, WORKSPACE_SUBFOLDERS
- Direct codebase inspection: `src/main.py` — `sys.frozen` / `sys._MEIPASS` pattern for frozen build detection
- `.planning/STATE.md` — architecture decisions: JSON-only, pure Python engine, no Qt in services, signal guard pattern
- `.planning/research/ARCHITECTURE.md` — v2.0 architecture design, PersistenceService pattern, MonsterMathEngine design, file naming plan
- `.planning/phases/08-domain-expansion-and-persistence-foundation/08-CONTEXT.md` — all locked decisions for this phase
- D&D 5e Basic Rules — proficiency bonus by CR bracket (0-4: +2, 5-8: +3, 9-12: +4, 13-16: +5, 17-20: +6, 21-24: +7, 25-28: +8, 29-30: +9)

### Secondary (MEDIUM confidence)

- PySide6 QMainWindow documentation: `closeEvent(QCloseEvent)` override pattern, `statusBar().showMessage(text, timeout_ms)`
- PySide6 QTimer documentation: `setInterval()`, `start()`, `timeout` signal, `setSingleShot()`

### Tertiary (LOW confidence)

- None — all claims in this document are supported by primary or secondary sources.

---

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH — all libraries are already in the project; no new dependencies
- Architecture: HIGH — PersistenceService pattern is a direct copy of SettingsService; MonsterMathEngine follows the documented v2.0 architecture
- Pitfalls: HIGH — fractional CR pitfall and signal cascade guard are verified against existing code; workspace root mismatch confirmed by reading app.py

**Research date:** 2026-02-25
**Valid until:** 2026-04-25 (stable Python/PySide6 APIs; D&D 5e rules don't change)
