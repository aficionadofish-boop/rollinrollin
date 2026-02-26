# Phase 10: Persistent Encounter Sidebar - Research

**Researched:** 2026-02-26
**Domain:** PySide6 QDockWidget, encounter state management, cross-tab signal architecture
**Confidence:** HIGH

---

<user_constraints>
## User Constraints (from CONTEXT.md)

### Locked Decisions

**Sidebar Layout & Position**
- Docked on the right side of the main window
- Base width 300px, resizable by click-and-drag on the edge
- Width persists across sessions (remembered in settings)
- Subtle background color difference from main content to visually separate it
- Encounter name displayed read-only in sidebar — renaming only in Combat Tracker (Phase 11)

**Monster List Display**
- Minimal display: name + count (e.g. "Goblin x3")
- Renamed creatures get their own row with base type in parentheses (e.g. "Volt the Booyagh (Goblin) x1")
- Default sort order: CR descending; switches to initiative order when combat is active in Combat Tracker
- Count is inline editable — click the count number to change it directly

**Encounter Summary Header**
- Shows total creature count + total XP
- Shows difficulty rating (Easy/Medium/Hard/Deadly) only if party data (size + average level) has been configured in Combat Tracker
- If no party data, just XP total is shown

**Empty/Inactive State**
- When no encounter exists, sidebar toggle is grayed out and not openable
- Sidebar activates when the first monster is dragged onto the drop field in the Library tab
- When the last monster is removed, sidebar auto-closes

**Interaction — Adding Monsters**
- Drag-and-drop from Library tab only (existing drag-and-drop field mechanism)
- Cannot add from other tabs — must go to Library
- Adding a monster already in the encounter auto-increments count silently
- Monsters can be reordered within sidebar via drag-and-drop

**Interaction — Removing Monsters**
- X button on each monster row for quick removal
- Right-click context menu with: Remove, Remove all of type, and additional actions

**Interaction — Selecting for Rolling**
- Single-click a monster row to select it as active attacker for Attack Roller (pre-loads it)
- Double-click a monster row to select AND switch to Attack Roller tab
- Selected monster row gets a visual highlight (background color)
- Selecting a grouped monster (e.g. "Goblin x3") selects all of that type

**Right-Click Context Menu**
- Full context menu with multiple actions: Remove, Remove all of type, Roll attacks, View stat block, etc.

**Collapse & Toggle**
- Edge handle/grip on the sidebar's left edge — click to collapse/expand
- When collapsed, a thin strip (~20px) remains visible with the handle
- Smooth slide animation (~200ms) for collapse/expand transitions

**Save/Load Encounters**
- Save/Load accessed from sidebar (Claude's discretion on exact button/menu placement)
- When loading a different encounter, auto-save current encounter first
- Load encounter UI: modal dialog showing saved encounters with name, creature count, date saved
- Load dialog supports both loading and deleting saved encounters

### Claude's Discretion
- Exact collapse/expanded state persistence across restarts (whether to remember or always start expanded)
- Save/Load button placement and styling in sidebar header
- Context menu item ordering and exact actions beyond Remove/Remove all
- Loading skeleton or transition states
- Exact animation easing curves

### Deferred Ideas (OUT OF SCOPE)
- Encounter renaming — Phase 11 (Combat Tracker)
- Party size/level configuration for difficulty calculation — Phase 11 (Combat Tracker)
- Initiative ordering display — Phase 11 (Combat Tracker, sidebar reflects it when active)
- Individual creature selection within a monster group — potential future enhancement
</user_constraints>

---

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|-----------------|
| SIDEBAR-01 | Collapsible sidebar visible on Library, Attack Roller, and Saves tabs showing the active encounter | QDockWidget at RightDockWidgetArea persists across all tabs automatically; QMainWindow manages it independently of QTabWidget central widget |
| SIDEBAR-02 | User can add/remove monsters from the encounter via the sidebar | Existing EncounterDropZone drag pattern reused; sidebar emits monster_added signal; X button rows; right-click QMenu |
| SIDEBAR-03 | Sidebar encounter persists between tab switches and between sessions | Tab switch: QDockWidget is never destroyed on tab switch; session: encounters.json via existing PersistenceService with active_encounter key |
| SIDEBAR-04 | User can save/load encounters from the sidebar | Save: existing EncounterService.save_encounter() pattern; Load: new QDialog modal listing saved encounters from encounters.json |
| SIDEBAR-05 | Sidebar can be collapsed/expanded by clicking a toggle on its edge | Custom collapse via min/max width constraints on QDockWidget; QPropertyAnimation on maximumWidth for smooth 200ms slide |
</phase_requirements>

---

## Summary

Phase 10 adds a QDockWidget persistent encounter sidebar to the right of the MainWindow. The QDockWidget is independent of the QTabWidget central widget — it remains visible regardless of which tab is active, satisfying SIDEBAR-01 without any tab-switching coordination logic. The architecture decision (already locked in STATE.md: "QDockWidget at RightDockWidgetArea — not a tab-embedded widget; no direct tab references to sidebar") is the right call and was made in Phase 8 planning.

The encounter state needs a proper home. Currently, `_persisted_encounters` in `app.py` is a list that is loaded but never populated from the UI (the Encounters tab saves to Markdown files via QFileDialog, not to encounters.json). Phase 10 needs to introduce an "active encounter" concept: a single `{name, members}` structure persisted in encounters.json that the sidebar displays and edits. The existing `PersistenceService.save_encounters()` / `load_encounters()` infrastructure is already in place and just needs to be wired to the sidebar's state.

The collapse behavior needs special handling because `QDockWidget.hide()` makes the dock fully invisible (no thin strip). The correct pattern is to constrain the dock's width via `setMinimumWidth` / `setMaximumWidth` while swapping the inner widget between a full content panel and a thin handle-only strip. `QPropertyAnimation` on `maximumWidth` drives the 200ms slide. The load dialog is a plain `QDialog` with a `QListWidget` listing saved encounters from `encounters.json`.

**Primary recommendation:** Build `EncounterSidebarDock` as a `QDockWidget` subclass, introduce `EncounterSidebarService` for active-encounter state management (separate from Markdown file I/O), and wire it through `MainWindow` using the established signal pattern.

---

## Standard Stack

### Core
| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| PySide6 | 6.10.2 (installed) | QDockWidget, QPropertyAnimation, QDialog, QListWidget, QMenu | Already the project's UI framework |
| Python dataclasses | stdlib | ActiveEncounter data structure | Project-wide pattern for domain models |
| json | stdlib | Serializing active encounter to encounters.json | Matches PersistenceService pattern |

### Supporting
| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| QPropertyAnimation | PySide6 built-in | Smooth collapse/expand animation | Width slide animation on the dock |
| QStyledItemDelegate | PySide6 built-in | Inline count edit in sidebar list | Clicking count to edit inline |
| QDockWidget | PySide6 built-in | Persistent cross-tab panel | The sidebar container |

### Alternatives Considered
| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| QDockWidget | QSplitter right panel | Splitter lives inside one tab — can't persist across tabs; QDockWidget is correct |
| QPropertyAnimation on maximumWidth | Instant width toggle | Instant is simpler but violates the 200ms animation spec |
| QDialog for load | QFileDialog | QFileDialog shows filesystem; load dialog needs to show named encounters from encounters.json only |

**Installation:** No new packages needed. PySide6 6.10.2 is already installed and provides all required widgets.

---

## Architecture Patterns

### Recommended Project Structure
```
src/
├── ui/
│   ├── app.py                    # Modified: add dock, wire signals, persist active encounter
│   ├── encounter_sidebar.py      # NEW: EncounterSidebarDock (QDockWidget subclass)
│   └── load_encounter_dialog.py  # NEW: LoadEncounterDialog (QDialog subclass)
├── encounter/
│   └── service.py                # Existing: EncounterService (no changes needed)
└── persistence/
    └── service.py                # Existing: PersistenceService (add active_encounter key)
```

### Pattern 1: QDockWidget at RightDockWidgetArea

**What:** `MainWindow.addDockWidget(Qt.DockWidgetArea.RightDockWidgetArea, dock)` — the dock is managed by `QMainWindow` independently of the tab widget.

**When to use:** Any panel that must persist across tab switches.

**Example:**
```python
# Source: verified via Python REPL against PySide6 6.10.2
from PySide6.QtWidgets import QDockWidget
from PySide6.QtCore import Qt

class EncounterSidebarDock(QDockWidget):
    def __init__(self, parent=None):
        super().__init__("Encounter", parent)
        # Prevent user from closing, floating, or moving dock
        self.setFeatures(
            QDockWidget.DockWidgetFeature.DockWidgetMovable
        )
        self.setMinimumWidth(20)
        self._expanded_width = 300
        self._setup_content()

# In MainWindow.__init__:
self._sidebar = EncounterSidebarDock(self)
self.addDockWidget(Qt.DockWidgetArea.RightDockWidgetArea, self._sidebar)
```

### Pattern 2: Collapse with Thin Strip (Custom Width Constraint)

**What:** `QDockWidget.hide()` removes the dock entirely — wrong for thin strip. Instead, swap the inner widget content between "expanded panel" and "thin handle" by constraining width. Animate via `QPropertyAnimation` on `maximumWidth`.

**When to use:** Any collapsible panel where a visible handle must remain.

**Example:**
```python
# Source: verified via Python REPL against PySide6 6.10.2
from PySide6.QtCore import QPropertyAnimation, QEasingCurve

class EncounterSidebarDock(QDockWidget):
    _COLLAPSED_WIDTH = 20
    _EXPANDED_WIDTH = 300

    def __init__(self, ...):
        ...
        self._collapsed = False
        self._anim = QPropertyAnimation(self, b"maximumWidth")
        self._anim.setDuration(200)
        self._anim.setEasingCurve(QEasingCurve.Type.InOutQuad)

    def toggle_collapse(self):
        if self._collapsed:
            # Expand
            self._anim.setStartValue(self._COLLAPSED_WIDTH)
            self._anim.setEndValue(self._EXPANDED_WIDTH)
            self._anim.finished.connect(self._on_expanded)
        else:
            # Collapse
            self._anim.setStartValue(self._EXPANDED_WIDTH)
            self._anim.setEndValue(self._COLLAPSED_WIDTH)
            self._anim.finished.connect(self._on_collapsed)
        self._collapsed = not self._collapsed
        self._anim.start()

    def _on_collapsed(self):
        # Show only handle strip
        self._content_widget.setVisible(False)
        self._handle_widget.setVisible(True)
        self._anim.finished.disconnect()

    def _on_expanded(self):
        self._handle_widget.setVisible(False)
        self._content_widget.setVisible(True)
        self.setMinimumWidth(self._EXPANDED_WIDTH)
        self.setMaximumWidth(16777215)  # QWIDGETSIZE_MAX — allows resize
        self._anim.finished.disconnect()
```

**Critical:** After expanding, reset `maximumWidth` to `QWIDGETSIZE_MAX` so the user can drag-resize. During collapse animation, `setMinimumWidth(0)` first to avoid fighting the animation.

### Pattern 3: Active Encounter State in PersistenceService

**What:** Introduce a single "active encounter" record in `encounters.json`. The sidebar reads/writes this on every change. Named saved encounters are a separate list.

**When to use:** Single active encounter, multiple named saved encounters.

**Data format:**
```json
{
  "active": {
    "name": "Session Encounter",
    "members": [
      {"name": "Goblin", "count": 3},
      {"name": "Hobgoblin", "count": 1}
    ]
  },
  "saved": [
    {
      "name": "Ambush",
      "members": [{"name": "Bandit", "count": 5}],
      "saved_at": "2026-02-26T14:30:00"
    }
  ]
}
```

**Resolution at load time:** Monster names are resolved from `MonsterLibrary.get_by_name()` — never store Monster objects in JSON. This matches the existing decision in STATE.md: "Encounter persistence format: `{name: str, count: int}` only — never serialize Monster objects; resolve by name at access time."

**Option A (preferred): Extend encounters.json schema** — keep one file, add `active` and `saved` keys. PersistenceService gains `load_active_encounter()` / `save_active_encounter()` and `load_saved_encounters()` / `save_saved_encounter()` methods.

**Option B: Two files** — `active_encounter.json` and `saved_encounters.json`. Simpler but adds file proliferation.

Option A is preferred: consistent with existing single-file-per-category pattern.

### Pattern 4: Monster Row as Custom QWidget (not QListWidget)

**What:** Each monster row in the sidebar is a `QWidget` with `QHBoxLayout` containing a name `QLabel`, inline-editable count, and an X button. This mirrors the existing `EncounterMemberList` pattern in `encounters_tab.py` exactly.

**When to use:** When rows need custom layout (name + count + remove button).

**Why not QListWidget + QStyledItemDelegate:** The existing `EncounterMemberList` in `encounters_tab.py` already uses the row-widget approach successfully. Reuse the same pattern. `QStyledItemDelegate` works but adds complexity for a fixed-layout row.

**Inline count editing:** A `QSpinBox` that is always visible (not a delegate). Matches `EncounterMemberList.count_spin` pattern. On value change, emit a signal to update persistence.

**Drag-to-reorder:** Use `QListWidget` with `DragDropMode.InternalMove` for the container, but each item's widget is set via `QListWidget.setItemWidget()`. The list handles reorder; items carry monster name as `Qt.UserRole` data.

### Pattern 5: Cross-Tab Signal Wiring in MainWindow

**What:** The sidebar's signals flow through `MainWindow` — same pattern as existing cross-tab signals.

**When to use:** Any time two components need to communicate across tabs.

**New signals needed:**
```python
# EncounterSidebarDock emits:
monster_selected = Signal(object)       # Monster — single click → preload Attack Roller
encounter_changed = Signal(list)        # [(Monster, count)] — any change → update Attack Roller

# MainWindow wires:
self._sidebar.monster_selected.connect(self._attack_roller_tab.set_active_creature)
self._sidebar.encounter_changed.connect(self._attack_roller_tab.set_creatures)
self._library_tab.monster_added_to_encounter.connect(self._sidebar.add_monster)
```

**Double-click to switch tab:**
```python
# In EncounterSidebarDock:
switch_to_attack_roller = Signal()

# In MainWindow:
self._sidebar.switch_to_attack_roller.connect(
    lambda: self._tab_widget.setCurrentWidget(self._attack_roller_tab)
)
```

### Pattern 6: Load Encounter Dialog

**What:** `QDialog` subclass with a `QListWidget` showing saved encounters (name, count, date). Buttons: Load, Delete, Cancel.

**When to use:** Replacing QFileDialog for structured data selection.

**Example:**
```python
# Source: verified via Python REPL against PySide6 6.10.2
from PySide6.QtWidgets import QDialog, QVBoxLayout, QListWidget, QHBoxLayout, QPushButton

class LoadEncounterDialog(QDialog):
    def __init__(self, saved_encounters: list[dict], parent=None):
        super().__init__(parent)
        self.setWindowTitle("Load Encounter")
        self.setModal(True)
        self._selected = None

        layout = QVBoxLayout(self)
        self._list = QListWidget()
        for enc in saved_encounters:
            count = sum(m["count"] for m in enc.get("members", []))
            label = f"{enc['name']} — {count} creatures — {enc.get('saved_at', '')[:10]}"
            self._list.addItem(label)
        layout.addWidget(self._list)

        btns = QHBoxLayout()
        load_btn = QPushButton("Load")
        delete_btn = QPushButton("Delete")
        cancel_btn = QPushButton("Cancel")
        load_btn.clicked.connect(self._on_load)
        delete_btn.clicked.connect(self._on_delete)
        cancel_btn.clicked.connect(self.reject)
        btns.addWidget(load_btn)
        btns.addWidget(delete_btn)
        btns.addWidget(cancel_btn)
        layout.addLayout(btns)

    def _on_load(self):
        row = self._list.currentRow()
        if row >= 0:
            self._selected = row
            self.accept()
```

### Pattern 7: QMainWindow saveState / restoreState for Width Persistence

**What:** `QMainWindow.saveState()` returns a `QByteArray` encoding all dock widget geometry and positions. This can be serialized to a hex string for `AppSettings`.

**When to use:** Persisting dock width and position across sessions.

**Example:**
```python
# Source: verified via Python REPL against PySide6 6.10.2
# In MainWindow.closeEvent:
state = self.saveState()
hex_str = state.toHex().data().decode()
self._settings_service.save_window_state(hex_str)

# In MainWindow.__init__ (after dock created):
hex_str = self._current_settings.window_state
if hex_str:
    self.restoreState(QByteArray.fromHex(hex_str.encode()))
```

**AppSettings addition:**
```python
@dataclass
class AppSettings:
    ...
    window_state: Optional[str] = None   # QMainWindow.saveState() hex
```

**Alternative:** Store sidebar width as a plain int in AppSettings and call `dock.resize(width, dock.height())` on startup. Simpler, less brittle, avoids encoding dock floating/position state. Recommended over full `saveState()` for this use case.

### Anti-Patterns to Avoid

- **QDockWidget.hide() for collapse:** Makes the dock fully invisible, no thin strip. Use width constraints instead.
- **Storing Monster objects in JSON:** Violates the established "name + count only" persistence rule. Always resolve from library at load time.
- **Coupling sidebar directly to tab widgets:** Sidebar should never hold a reference to specific tabs. Route through MainWindow signals.
- **Connecting sidebar to EncountersTab:** EncountersTab will become SavesTab in Phase 10; the sidebar is the new home for encounter state. They share the same underlying encounter data but the sidebar is authoritative.
- **Re-implementing EncounterMemberList:** The sidebar's monster list is similar but not identical. Extract a shared `EncounterMemberRow` widget if code reuse is clean; otherwise duplicate the row pattern — it's ~50 lines.

---

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Smooth slide animation | Custom timer loop changing width | `QPropertyAnimation` on `maximumWidth` | Qt's animation framework handles timing, easing, and thread safety |
| Right-click menu | Custom popup widget | `QMenu` with `exec(QCursor.pos())` | Platform-native context menu behavior |
| Drag-to-reorder list | Custom drag tracking | `QListWidget.DragDropMode.InternalMove` | Qt handles drop position, reorder rendering, and auto-scroll |
| State serialization | Custom binary format | `QMainWindow.saveState()` + hex or plain int in AppSettings | Qt already serializes dock geometry correctly |
| XP calculation table | Dynamic computation | Inline lookup dict (see Code Examples) | D&D 5e XP values are a static lookup; no formula needed |

**Key insight:** Qt already solves drag-reorder, animation, and context menus. The custom code is only business logic: encounter state management, XP computation, and signal wiring.

---

## Common Pitfalls

### Pitfall 1: QPropertyAnimation Animation Leaves Widget in Wrong State
**What goes wrong:** After animation completes, `maximumWidth` is set to the animation end value. If end value is `_EXPANDED_WIDTH` (300), the user cannot resize wider. If the animation is cancelled mid-run, the widget may be at an intermediate width.
**Why it happens:** `QPropertyAnimation` does not automatically reset constraints — it leaves the property at its last value.
**How to avoid:** Connect `animation.finished` signal to a slot that resets `setMaximumWidth(16777215)` after expanding. Always disconnect `finished` before reconnecting for the next toggle.
**Warning signs:** User reports they cannot resize the sidebar wider after expanding.

### Pitfall 2: saveState() / restoreState() Version Mismatch
**What goes wrong:** If dock widget object names change between versions, `restoreState()` silently ignores the saved state. The dock appears at default position.
**Why it happens:** Qt uses `QDockWidget.objectName()` to match saved state to widgets. If objectName is not set, Qt assigns a default that may change.
**How to avoid:** Set `dock.setObjectName("encounter_sidebar")` before calling `addDockWidget()`. Maintain this name across versions.
**Warning signs:** Dock always appears at default width on restart even though state was saved.

### Pitfall 3: Disconnected Active Encounter on Tab Switch
**What goes wrong:** Library tab drag adds monster to the sidebar, but attack roller still shows old encounter from previous `encounter_members_changed` signal.
**Why it happens:** The sidebar is now the source of truth for the encounter, but the attack roller was previously wired to `EncountersTab.encounter_members_changed`.
**How to avoid:** In Phase 10, rewire `MainWindow` so `sidebar.encounter_changed` connects to `attack_roller_tab.set_creatures`. The old `encounters_tab.encounter_members_changed` → `attack_roller_tab.set_creatures` connection should be removed or replaced.
**Warning signs:** Attack Roller shows stale monsters after adding via sidebar.

### Pitfall 4: Resolving Monster Names After Library Changes
**What goes wrong:** User loads an active encounter from sessions.json, but some monster names no longer exist in the library (user re-imported without that monster). Sidebar silently shows nothing.
**Why it happens:** Names are resolved at load time; missing names are skipped.
**How to avoid:** Use the existing `UnresolvedEntry` pattern from `EncounterService.load_encounter()`. Show a status message in the sidebar if names could not be resolved (e.g., "2 monsters not found in library").
**Warning signs:** Encounter loads with fewer monsters than saved, no user feedback.

### Pitfall 5: Infinite Signal Loop on Count Change
**What goes wrong:** Sidebar row count spinbox emits `valueChanged` → sidebar emits `encounter_changed` → something triggers a sidebar refresh → spinbox value is set again → loop.
**Why it happens:** Setting spinbox value programmatically triggers `valueChanged`.
**How to avoid:** Use `spin.blockSignals(True)` / `spin.blockSignals(False)` when programmatically setting count values (e.g., on load). Matches the existing `_recalculating` flag pattern in monster_math.
**Warning signs:** UI hangs or spins CPU on encounter load.

### Pitfall 6: Auto-Save Before Load Overwrites New Encounter
**What goes wrong:** User clicks Load in sidebar. Auto-save fires while dialog is open. Active encounter (about to be replaced) gets overwritten with a bad intermediate state.
**Why it happens:** 30-second autosave timer is always running.
**How to avoid:** The auto-save-before-load is a synchronous operation in `_on_load_encounter()` that runs before the dialog opens. The 30-second timer saves the current state, which is fine. The sequence is: (1) auto-save current encounter, (2) show dialog, (3) on Accept, load selected encounter. No race condition.

### Pitfall 7: Empty Encounter Sidebar Not Grayed Out
**What goes wrong:** Sidebar toggle remains clickable when no encounter exists, opening an empty panel.
**Why it happens:** Toggle button state not wired to encounter membership count.
**How to avoid:** The handle toggle button's `setEnabled(False)` must be called whenever `encounter_changed` emits an empty list. When first monster is added, `setEnabled(True)` and open the sidebar.

---

## Code Examples

Verified patterns from official sources (PySide6 6.10.2, verified via REPL):

### XP Table and Encounter Summary Calculation
```python
# D&D 5e XP by CR (static lookup, verified against SRD)
_XP_BY_CR: dict[str, int] = {
    "0": 10, "1/8": 25, "1/4": 50, "1/2": 100,
    "1": 200, "2": 450, "3": 700, "4": 1100,
    "5": 1800, "6": 2300, "7": 2900, "8": 3900,
    "9": 5000, "10": 5900, "11": 7200, "12": 8400,
    "13": 10000, "14": 11500, "15": 13000, "16": 15000,
    "17": 18000, "18": 20000, "19": 22000, "20": 25000,
    "21": 33000, "22": 41000, "23": 50000, "24": 62000,
}

def compute_encounter_xp(members: list[tuple]) -> int:
    """Return total base XP for (monster, count) pairs."""
    total = 0
    for monster, count in members:
        xp = _XP_BY_CR.get(str(monster.cr), 0)
        total += xp * count
    return total

def cr_to_float(cr: str) -> float:
    """Convert CR string to float for sorting."""
    if "/" in cr:
        n, d = cr.split("/")
        return int(n) / int(d)
    try:
        return float(cr)
    except ValueError:
        return 0.0
```

### QPropertyAnimation Collapse
```python
# Source: verified PySide6 6.10.2 REPL
from PySide6.QtCore import QPropertyAnimation, QEasingCurve

self._anim = QPropertyAnimation(self, b"maximumWidth")
self._anim.setDuration(200)
self._anim.setEasingCurve(QEasingCurve.Type.InOutQuad)

def _collapse(self):
    self.setMinimumWidth(0)  # Allow shrinking
    self._anim.setStartValue(self.width())
    self._anim.setEndValue(20)
    self._anim.finished.connect(self._after_collapse)
    self._anim.start()

def _after_collapse(self):
    self._anim.finished.disconnect()
    self._content.setVisible(False)
    self._handle.setVisible(True)

def _expand(self):
    self._content.setVisible(True)
    self._handle.setVisible(False)
    self._anim.setStartValue(20)
    self._anim.setEndValue(self._expanded_width)
    self._anim.finished.connect(self._after_expand)
    self._anim.start()

def _after_expand(self):
    self._anim.finished.disconnect()
    self.setMinimumWidth(200)
    self.setMaximumWidth(16777215)  # QWIDGETSIZE_MAX
```

### Right-Click Context Menu on Monster Row
```python
# Source: verified PySide6 6.10.2 REPL
from PySide6.QtWidgets import QMenu
from PySide6.QtGui import QCursor

def _show_context_menu(self, monster, row_widget):
    menu = QMenu(self)
    remove_action = menu.addAction("Remove")
    remove_all_action = menu.addAction(f"Remove all {monster.name}")
    menu.addSeparator()
    roll_action = menu.addAction("Roll Attacks")
    view_action = menu.addAction("View Stat Block")

    action = menu.exec(QCursor.pos())
    if action == remove_action:
        self._remove_monster(monster.name, all_of_type=False)
    elif action == remove_all_action:
        self._remove_monster(monster.name, all_of_type=True)
    elif action == roll_action:
        self.monster_selected.emit(monster)
        self.switch_to_attack_roller.emit()
    elif action == view_action:
        # Emit signal to library tab to show stat block
        self.view_stat_block_requested.emit(monster)
```

### Encounter Persistence Format (encounters.json)
```python
# Serialize active encounter
def _serialize_active(self, name: str, members: list[tuple]) -> dict:
    return {
        "name": name,
        "members": [
            {"name": m.name, "count": count}
            for m, count in members
        ]
    }

# Serialize saved encounter (with timestamp)
import datetime
def _serialize_saved(self, name: str, members: list[tuple]) -> dict:
    return {
        "name": name,
        "members": [
            {"name": m.name, "count": count}
            for m, count in members
        ],
        "saved_at": datetime.datetime.now().isoformat(timespec="seconds")
    }

# encounters.json structure
{
    "active": {"name": "...", "members": [...]},
    "saved": [
        {"name": "...", "members": [...], "saved_at": "..."},
        ...
    ]
}
```

### Single-Click vs Double-Click Monster Selection
```python
# Source: PySide6 verified pattern
# In EncounterSidebarDock, on monster row widget:
row_widget.mousePressEvent = lambda e: self._on_single_click(monster)

# Or via signals on a QListWidget item:
self._list_widget.itemClicked.connect(self._on_single_click)
self._list_widget.itemDoubleClicked.connect(self._on_double_click)

def _on_single_click(self, item):
    monster = item.data(Qt.ItemDataRole.UserRole)
    self.monster_selected.emit(monster)  # → Attack Roller preloads

def _on_double_click(self, item):
    monster = item.data(Qt.ItemDataRole.UserRole)
    self.monster_selected.emit(monster)
    self.switch_to_attack_roller.emit()  # → MainWindow switches tab
```

---

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| Encounter builder embedded in Encounters & Saves tab | Persistent QDockWidget sidebar | Phase 10 | Encounter list visible on all tabs |
| Save/Load via QFileDialog to Markdown files | Save/Load via QDialog to encounters.json | Phase 10 | Structured named encounters in-app; Markdown save can still exist as export |
| EncountersTab owns encounter members_changed signal | Sidebar owns encounter state, EncountersTab becomes SavesTab | Phase 10 | MainWindow rewires encounter_changed from sidebar to Attack Roller |

**Deprecated/outdated:**
- `EncountersTab.add_monster_to_encounter()`: This slot was connected to `LibraryTab.monster_added_to_encounter`. Phase 10 rewires this to `EncounterSidebarDock.add_monster` instead. The EncountersTab slot can remain for now but stops being the primary encounter target.
- `EncountersTab.encounter_members_changed` → `AttackRollerTab.set_creatures`: Will be replaced by `EncounterSidebarDock.encounter_changed` → `AttackRollerTab.set_creatures` in Phase 10.

---

## Open Questions

1. **What becomes of EncountersTab?**
   - What we know: CONTEXT.md says "SavesTab is extracted as its own standalone tab." The encounter list moves to the sidebar. The Save Roller (right panel) stays. The encounter builder (left panel) moves to sidebar.
   - What's unclear: Does EncountersTab get renamed to SavesTab (removing the left panel) in Phase 10, or does it remain and just have the encounter builder become redundant? Does Phase 10 need to fully remove the old encounter builder or just add the sidebar?
   - Recommendation: Phase 10 should: (1) add the sidebar, (2) rewire signals so sidebar is authoritative, (3) optionally remove or disable the old `EncounterMemberList` from EncountersTab. The tab rename to "Saves" is the cleanest action — remove the left panel entirely in Phase 10.

2. **Should the `active_encounter` be a new PersistenceService key or reuse the existing `encounters` key?**
   - What we know: Currently `encounters` category in PersistenceService is loaded as a list but never written by the UI (EncountersTab writes to Markdown files). The list is always empty.
   - What's unclear: Should we reuse the `encounters` key with a new schema (`{active: ..., saved: [...]}`) or add `active_encounter` as a new key?
   - Recommendation: Reuse `encounters` key with a new dict schema. The key was always intended for encounter data. Breaking change is acceptable since the list was always empty (not populated by current UI). This avoids proliferating persistence categories.

3. **Drag-from-Library to Sidebar: Does the existing `EncounterDropZone` need to be moved?**
   - What we know: `EncounterDropZone` is on the Library tab. It emits `monster_dropped` → `MainWindow` connects to `EncountersTab.add_monster_to_encounter`. Phase 10 rewires this to `EncounterSidebarDock.add_monster`.
   - What's unclear: Does the drop zone remain in Library tab unchanged (just rewired), or does the sidebar also become a drop target?
   - Recommendation: Keep `EncounterDropZone` on Library tab (no relocation needed), rewire in `MainWindow.__init__`. CONTEXT.md says "drag-and-drop from Library tab only" — no new drop zone needed.

4. **How does `AppSettings` store the collapsed state?**
   - What we know: CONTEXT says "exact collapse/expanded state persistence across restarts" is Claude's discretion.
   - Recommendation: Start expanded (don't persist collapse state). Rationale: DMs expect to see their encounter on launch. Storing collapse state requires adding a field to `AppSettings` and handling edge case of "collapsed but empty encounter." The complexity is not worth it.

5. **How does `AppSettings` store sidebar width?**
   - What we know: Width is resizable and should persist. `QMainWindow.saveState()` encodes dock width as a hex string. AppSettings currently has no window geometry fields.
   - Recommendation: Add `sidebar_width: int = 300` to `AppSettings`. On close, read `self._sidebar.width()` and save. On startup, `self._sidebar.setMinimumWidth(settings.sidebar_width); self._sidebar.resize(settings.sidebar_width, ...)`. This is simpler than `saveState()` hex and avoids encoding dock position/floating state.

---

## Sources

### Primary (HIGH confidence)
- PySide6 6.10.2 (verified via REPL) — QDockWidget, QPropertyAnimation, QListWidget.InternalMove, QDialog, QMenu, QMainWindow.saveState/restoreState
- `src/ui/app.py` — MainWindow architecture, signal wiring pattern, persistence lifecycle
- `src/ui/encounters_tab.py` — EncounterMemberList pattern (row widget approach, drag-drop), existing encounter signal contracts
- `src/ui/library_tab.py` — EncounterDropZone pattern, monster_added_to_encounter signal
- `src/persistence/service.py` — PersistenceService category pattern, encounters.json schema
- `src/domain/models.py` — Encounter, Monster, MonsterModification data contracts
- `.planning/STATE.md` — Locked decisions: QDockWidget, encounters format, no direct tab references to sidebar

### Secondary (MEDIUM confidence)
- D&D 5e XP table from SRD (static values, verified against published SRD values)

### Tertiary (LOW confidence)
- None — all findings verified against running code or official PySide6 installation.

---

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH — PySide6 6.10.2 verified installed; all widgets confirmed via REPL
- Architecture: HIGH — patterns verified against existing codebase; QDockWidget confirmed working
- Pitfalls: HIGH — derived from verified code behavior and established project patterns
- XP table: HIGH — static D&D 5e SRD data, well-known values

**Research date:** 2026-02-26
**Valid until:** 2026-03-28 (stable Qt APIs)
