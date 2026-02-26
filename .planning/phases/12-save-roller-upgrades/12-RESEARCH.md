# Phase 12: Save Roller Upgrades - Research

**Researched:** 2026-02-26
**Domain:** PySide6 UI enhancement, Python service layer, regex trait detection, JSON persistence
**Confidence:** HIGH

<user_constraints>
## User Constraints (from CONTEXT.md)

### Locked Decisions

**Creature Selection UI**
- Selection happens via checkboxes directly on the sidebar encounter creatures — not a separate list in the Saves tab
- Quick-select shortcuts: Select All, Select None, and Invert Selection buttons on the sidebar
- Grouped creatures (e.g., 4x Goblin) toggle as a group by default; group can be expanded to toggle individuals
- Combat Tracker "Send to Saves" behavior is configurable in Settings: either CT selection overrides the sidebar encounter (default), or only sidebar creatures are considered for rolling
- When CT overrides, the sent creatures replace whatever was checked in the sidebar

**Feature Detection Display**
- Dedicated "Features" column in the save results table showing plain text labels per creature (e.g., "MR (auto)", "LR 2/3")
- No color-coded badges — plain text consistent with current output style
- Feature summary appears only after rolling (in the results), not as a preview panel before rolling
- No distinction between auto-detected advantage and manual global advantage in the output — if advantage is on, it's on

**Legendary Resistance Tracking**
- When a creature with LR fails a save, the entire result row is colored red to make it visually obvious
- Row text includes: "This creature has LR remaining (X/Y). Use?" with a clickable action to spend one
- When DM clicks "Use", the result flips from FAIL to PASS, the row recolors from red to green, and the LR counter decrements
- LR counter persists across multiple save rolls within the same encounter (not reset per roll)
- DM can click the LR counter directly to manually increment/decrement (for undo or correction)

**Custom Filter Editor**
- Collapsible "Detection Rules" panel within the Saves tab itself — close to where it's used
- Four assignable behaviors: auto-advantage, auto-disadvantage, auto-fail, auto-pass
- Built-in rules: Magic Resistance → auto-advantage (when "Is save magical?" is on), Legendary Resistance → reminder
- Custom triggers use substring matching (e.g., "Evasion" matches "Improved Evasion", "Evasion (fire only)")
- Custom rules persist to disk via the persistence service — survive app restarts

### Claude's Discretion
- Exact UI layout of the Detection Rules panel (add/edit/delete flow)
- How the "Is save magical?" toggle interacts with the detection rules internally
- Keyword matching implementation for trait detection
- How to parse "Legendary Resistance (X/Day)" for the uses count

### Deferred Ideas (OUT OF SCOPE)
None — discussion stayed within phase scope
</user_constraints>

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|-----------------|
| SAVE-08 | User can select a subset of creatures from the encounter for save rolls (not all-or-nothing) | Sidebar checkboxes on `_MonsterRowWidget`; `EncounterSidebarDock.get_members()` returns checked subset; `SavesTab.load_participants()` accepts the filtered list |
| SAVE-09 | App detects Magic Resistance from monster traits via keyword matching; auto-applies advantage when "Spell Save" toggle is on | Regex scan of `Monster.actions[*].raw_text`; same pattern CombatTrackerService already uses; `SaveParticipant` must carry per-creature advantage override |
| SAVE-10 | App detects Legendary Resistance with uses/day count; displays reminder in save log | LR regex already exists in `CombatTrackerService.load_encounter()`; per-creature LR counter in save state; clickable "Use?" inline in output |
| SAVE-11 | Toggleable checkboxes: "Is save magical?", enable/disable Magic Resistance detection, enable/disable Legendary Resistance detection | Three `QCheckBox` widgets in `SavesTab`; feed into feature detection at roll time |
| SAVE-12 | Detected features override global advantage per-creature (Magic Resistance creature rolls with advantage even when global is normal) | Per-participant advantage field on extended `SaveParticipant`; `SaveRollService` reads per-participant advantage when set |
| SAVE-13 | Feature detection summary shown per creature in save results | `SaveParticipantResult` carries `detected_features: list[str]`; `_format_participant_line()` appends features column |
| SAVE-14 | User can open and edit the feature detection filter list to add custom triggers with a name and assigned behavior | Collapsible panel in `SavesTab` with add/edit/delete; rules stored as list of dicts in new `save_detection_rules` persistence category |
</phase_requirements>

---

## Summary

Phase 12 enhances the existing Save Roller in `src/ui/encounters_tab.py` (the `SavesTab` class) with four interconnected capabilities: per-creature checkbox selection from the sidebar, automatic feature detection (Magic Resistance, Legendary Resistance) from already-parsed `Monster.actions[*].raw_text`, interactive LR "Use?" inline rows in the results, and an editable detection rule list that persists across sessions.

The project already has all the foundational infrastructure needed. The `CombatTrackerService` already detects Legendary Resistance via regex on `raw_text`. The `EncounterSidebarDock` already renders monster rows as `_MonsterRowWidget` instances. `SaveRollService.execute_save_roll()` accepts a `SaveRequest` with participants and per-request advantage. The `PersistenceService` already handles arbitrary JSON categories. This phase layers new behavior on top of all of these without requiring new third-party libraries.

The critical architectural decision is where per-creature advantage state lives. Currently `SaveRequest.advantage` is a single value applied to all participants. This phase requires per-participant advantage (e.g., Magic Resistance creature rolls with advantage even when global is Normal). This means either extending `SaveParticipant` with an `advantage` field (cleanest) or adding a parallel `per_participant_advantage` list to `SaveRequest`. The cleanest approach — adding `advantage: Optional[Literal["normal", "advantage", "disadvantage"]] = None` to `SaveParticipant` — keeps the service pure and backward-compatible (None = inherit from global request).

**Primary recommendation:** Extend `SaveParticipant` with per-creature advantage and feature tracking; extend `SaveParticipantResult` with detected features; add checkboxes to `_MonsterRowWidget`; add a `FeatureDetectionService` (pure Python) for trait scanning; add a collapsible detection rules panel to `SavesTab`; persist detection rules in a new `save_rules` PersistenceService category.

---

## Standard Stack

### Core
| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| PySide6 | Already installed | All UI widgets (QCheckBox, QScrollArea, QFrame, QGroupBox, QPushButton, QHBoxLayout) | Project-wide Qt binding; no alternatives |
| Python stdlib `re` | Always available | Regex trait detection from raw_text | CombatTrackerService already uses this pattern |
| Python stdlib `dataclasses` | Always available | Extended SaveParticipant, SaveParticipantResult models | All domain models use dataclasses |
| Python stdlib `json` | Always available | Persistence of custom detection rules | PersistenceService already uses json directly |

### Supporting
| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| PySide6 QTextEdit HTML/styled text | Already installed | Colored LR fail rows in output (red/green) | For the LR fail row color coding and clickable "Use?" |

### Alternatives Considered
| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| QTextEdit HTML for colored rows | QListWidget with QListWidgetItem.setForeground | QListWidget is item-based and harder to insert clickable actions mid-text; QTextEdit HTML is already the output panel's backing widget |
| Pure QTextEdit HTML links for "Use?" | Separate QPushButton per row injected into a QVBoxLayout | QPushButton rows are cleaner to wire but require a different output panel architecture than the existing `RollOutputPanel.append(text)` pattern |

**Installation:** No new packages needed.

---

## Architecture Patterns

### Recommended Project Structure

The phase adds/modifies these files:

```
src/
├── encounter/
│   ├── models.py          # extend SaveParticipant, SaveParticipantResult, add FeatureRule
│   └── service.py         # extend SaveRollService for per-participant advantage; add FeatureDetectionService
├── ui/
│   ├── encounters_tab.py  # SavesTab: add toggles, detection rules panel, new output rendering
│   └── encounter_sidebar.py  # _MonsterRowWidget: add checkbox; sidebar: add Select All/None/Invert
├── persistence/
│   └── service.py         # add save_rules category (_FILENAMES + methods)
└── settings/
    └── models.py          # AppSettings: add ct_send_overrides_sidebar: bool = True
```

No new top-level modules are needed; everything integrates into existing modules.

### Pattern 1: Extended SaveParticipant with Per-Creature Advantage

**What:** Add `advantage`, `detected_features`, `lr_uses`, and `lr_max` fields to `SaveParticipant`. The service reads `participant.advantage` first; falls back to `request.advantage` when None.

**When to use:** The SAVE-12 requirement mandates per-creature advantage overrides. This is the only pure-service approach that keeps `SaveRollService` testable without Qt.

```python
# src/encounter/models.py

from typing import Optional, Literal

@dataclass
class SaveParticipant:
    """One participant in a save roll — name plus resolved save bonus."""
    name: str
    save_bonus: int
    advantage: Optional[Literal["normal", "advantage", "disadvantage"]] = None
    # None = inherit from SaveRequest.advantage
    detected_features: list[str] = field(default_factory=list)
    # e.g. ["MR (auto)", "LR 2/3"]
    lr_uses: int = 0       # remaining legendary resistance uses at roll time
    lr_max: int = 0        # max LR for this creature
    monster_name: Optional[str] = None  # for re-detection when ability changes
```

```python
# In SaveRollService._roll_one_participant():
# Resolve effective advantage for this participant
effective_advantage = participant.advantage if participant.advantage is not None else request.advantage
if effective_advantage == "advantage":
    d20_result = roll_expression("2d20kh1", roller, request.seed)
elif effective_advantage == "disadvantage":
    d20_result = roll_expression("2d20kl1", roller, request.seed)
else:
    d20_result = roll_expression("1d20", roller, request.seed)
```

```python
# SaveParticipantResult also gains detected_features for display
@dataclass
class SaveParticipantResult:
    name: str
    d20_faces: tuple
    d20_natural: int
    save_bonus: int
    flat_modifier: int
    bonus_dice_results: list
    total: int
    passed: bool
    dc: int
    detected_features: list[str] = field(default_factory=list)  # NEW
    lr_uses: int = 0       # NEW: remaining LR at time of roll (for "Use?" UI)
    lr_max: int = 0        # NEW
```

### Pattern 2: FeatureDetectionService (pure Python)

**What:** New class in `src/encounter/service.py` that scans `Monster.actions[*].raw_text` for trait keywords and builds per-participant advantage/feature lists.

**When to use:** Called by `SavesTab._execute_roll()` before building `SaveRequest`. Not called in the service layer (keeps separation of concerns).

```python
# src/encounter/service.py

@dataclass
class FeatureRule:
    """A single detection rule for save feature detection."""
    trigger: str          # substring to match against action raw_text (case-insensitive)
    label: str            # display label, e.g. "MR (auto)", "Evasion"
    behavior: Literal["auto-advantage", "auto-disadvantage", "auto-fail", "auto-pass", "reminder"]
    enabled: bool = True
    is_builtin: bool = False  # True = cannot be deleted, only disabled


# Built-in rules (not persisted; always loaded at construction)
_BUILTIN_RULES: list[FeatureRule] = [
    FeatureRule(
        trigger="magic resistance",
        label="MR (auto)",
        behavior="auto-advantage",
        is_builtin=True,
    ),
    FeatureRule(
        trigger="legendary resistance",
        label="LR",
        behavior="reminder",
        is_builtin=True,
    ),
]

# Legendary Resistance count regex (reuse pattern from CombatTrackerService)
_LR_COUNT_RE = re.compile(r"legendary resistance\s*\(?(\d+)/day\)?", re.IGNORECASE)
_MR_RE = re.compile(r"magic resistance", re.IGNORECASE)


class FeatureDetectionService:
    """Scans Monster.actions[*].raw_text and applies FeatureRules.

    Produces per-participant advantage and feature label lists.
    """

    def detect_for_participant(
        self,
        monster,               # Monster | None
        rules: list[FeatureRule],
        is_magical_save: bool,
    ) -> tuple[Optional[str], list[str], int, int]:
        """Return (advantage_override, detected_labels, lr_uses, lr_max).

        advantage_override is None if no rule overrides (caller uses global).
        """
        if monster is None:
            return None, [], 0, 0

        actions = getattr(monster, "actions", [])
        all_raw = " ".join(getattr(a, "raw_text", "") or "" for a in actions)

        advantage_override = None
        labels: list[str] = []
        lr_uses = 0
        lr_max = 0

        for rule in rules:
            if not rule.enabled:
                continue
            if rule.trigger.lower() not in all_raw.lower():
                continue

            # Magic Resistance special case: only triggers when is_magical_save
            if rule.trigger.lower() == "magic resistance" and not is_magical_save:
                continue

            if rule.behavior == "auto-advantage":
                advantage_override = "advantage"
                labels.append(rule.label)
            elif rule.behavior == "auto-disadvantage":
                advantage_override = "disadvantage"
                labels.append(rule.label)
            elif rule.behavior == "auto-fail":
                # Represented as "auto-fail" label; service must handle in roll
                labels.append(f"{rule.label} (auto-fail)")
            elif rule.behavior == "auto-pass":
                labels.append(f"{rule.label} (auto-pass)")
            elif rule.behavior == "reminder":
                # Legendary Resistance: extract count
                if rule.trigger.lower() == "legendary resistance":
                    lr_m = _LR_COUNT_RE.search(all_raw)
                    if lr_m:
                        lr_max = int(lr_m.group(1))
                        lr_uses = lr_max  # reset each encounter load; real tracking is in UI
                    labels.append(f"LR {lr_uses}/{lr_max}")
                else:
                    labels.append(f"{rule.label} (reminder)")

        return advantage_override, labels, lr_uses, lr_max
```

### Pattern 3: Sidebar Checkbox Selection

**What:** Add `QCheckBox` to each `_MonsterRowWidget`. Add Select All / Select None / Invert buttons to the sidebar header. `EncounterSidebarDock.get_checked_members()` returns only checked `(Monster, count)` pairs.

**When to use:** SAVE-08 requires per-creature selection at the sidebar level.

```python
# In _MonsterRowWidget.__init__():
self._check = QCheckBox()
self._check.setChecked(True)   # checked by default
layout.addWidget(self._check)  # prepend before name label

def is_checked(self) -> bool:
    return self._check.isChecked()

def set_checked(self, checked: bool) -> None:
    self._check.setChecked(checked)
```

```python
# In EncounterSidebarDock:
def get_checked_members(self) -> list[tuple]:
    """Return [(Monster, count)] for checked rows only."""
    result = []
    for i in range(self._list_widget.count()):
        item = self._list_widget.item(i)
        monster = item.data(Qt.ItemDataRole.UserRole)
        entry = self._find_row_by_monster(monster)
        if entry and entry[1].is_checked():
            result.append((monster, entry[1].get_count()))
    return result

def select_all(self) -> None:
    for _, rw, _ in self._rows:
        rw.set_checked(True)

def select_none(self) -> None:
    for _, rw, _ in self._rows:
        rw.set_checked(False)

def invert_selection(self) -> None:
    for _, rw, _ in self._rows:
        rw.set_checked(not rw.is_checked())
```

**Select All / None / Invert buttons** are added to the sidebar header as a compact button row below the Save/Load row.

**Group expand for individual toggling:** The CONTEXT.md specifies grouped creatures toggle as a group. Since the sidebar uses a single `_MonsterRowWidget` per monster type with a count spinbox (not individual creature rows), the checkbox state applies to all N creatures of that type. Individual-creature expansion is a deferred complexity: the current sidebar model `(Monster, count)` expands to `SaveParticipant` list in `_expand_participants()`, so toggling a group checkbox naturally includes/excludes all copies.

### Pattern 4: LR Interactive Output Rows

**What:** The existing `RollOutputPanel` uses a `QTextEdit` with `append(text)` for plain text. The LR "Use?" interaction requires either: (a) switching to HTML-formatted output with `<a href>` hyperlinks, or (b) replacing the output panel with a `QScrollArea` containing per-row widgets that include inline buttons.

**Recommendation:** Replace the results display in `SavesTab` with a `QVBoxLayout` inside a `QScrollArea` that renders one `_SaveResultRow` widget per participant. This avoids fighting `QTextEdit`'s read-only anchor behavior and keeps the UI clean. The existing `RollOutputPanel` is retained for the summary line only (or replaced entirely).

```python
# _SaveResultRow widget pattern
class _SaveResultRow(QWidget):
    lr_used = Signal(str)  # participant name — to update LR counter

    def __init__(self, result: SaveParticipantResult, parent=None):
        super().__init__(parent)
        layout = QHBoxLayout(self)

        # Name + roll + bonus + total + PASS/FAIL
        self._text_label = QLabel(self._format_line(result))
        layout.addWidget(self._text_label, 1)

        # Features column (always present; empty if no features)
        self._feature_label = QLabel(", ".join(result.detected_features))
        layout.addWidget(self._feature_label)

        # LR "Use?" button — only shown when creature has LR and FAILED
        self._lr_btn = None
        if result.lr_uses > 0 and not result.passed:
            self._lr_btn = QPushButton(f"Use LR ({result.lr_uses}/{result.lr_max})?")
            self._lr_btn.clicked.connect(lambda: self._on_use_lr(result))
            layout.addWidget(self._lr_btn)

        self._result = result
        self._apply_row_color(result.passed)

    def _apply_row_color(self, passed: bool) -> None:
        if not passed and self._result.lr_uses > 0:
            self.setStyleSheet("background-color: rgba(220, 50, 50, 40);")  # red tint
        elif passed:
            self.setStyleSheet("")  # no tint on pass (green only after LR flip)

    def _on_use_lr(self, result: SaveParticipantResult) -> None:
        # Flip row to green, update label, hide button
        self.setStyleSheet("background-color: rgba(50, 200, 50, 40);")
        text = self._text_label.text().replace("FAIL", "PASS (LR)")
        self._text_label.setText(text)
        if self._lr_btn:
            self._lr_btn.hide()
        self.lr_used.emit(result.name)
```

**LR counter persistence across rolls:** The LR counter starts at detection time (from `FeatureDetectionService`) but is decremented via the UI "Use?" button. The counter is stored in the `SavesTab` itself as a dict `_lr_counters: dict[str, int]` keyed by monster name (not participant name, since "Goblin 1" and "Goblin 2" share the same LR pool by monster type). This state persists across multiple roll clicks within the same session but resets when participants are reloaded.

**Manual LR counter editing:** The sidebar shows the LR counter per row (from `_MonsterRowWidget` or a separate display). The DM can click the counter to increment/decrement. This is cleaner as a direct `QSpinBox` on the `_MonsterRowWidget` when LR is detected, or as a `QSpinBox` in the save result row widget.

### Pattern 5: Detection Rules Persistence

**What:** Custom `FeatureRule` objects (trigger, label, behavior, enabled) persist to `save_rules.json` via `PersistenceService`.

**When to use:** SAVE-14 requires rules to survive app restarts.

```python
# src/persistence/service.py additions
_FILENAMES = {
    ...
    "save_rules": "save_rules.json",   # NEW
}

def load_save_rules(self) -> list:
    """Return list of custom detection rule dicts."""
    return self._load("save_rules")

def save_save_rules(self, data: list) -> None:
    self._save("save_rules", data)
```

FeatureRule serialization is a list of plain dicts. Built-in rules are never serialized — they are always re-created in code. Only user-added rules are saved.

### Pattern 6: "Is Save Magical?" Toggle Integration

The "Is save magical?" toggle is a `QCheckBox` in `SavesTab`. When checked AND a creature has "magic resistance" in its actions, `FeatureDetectionService.detect_for_participant()` returns `advantage_override = "advantage"`. When unchecked, Magic Resistance does not trigger even if detected. This logic lives entirely in `SavesTab._execute_roll()` which passes `is_magical_save=self._magical_toggle.isChecked()` to `FeatureDetectionService`.

### Anti-Patterns to Avoid

- **Do not scan `Monster.raw_text` or `Monster.lore`** for Magic Resistance/Legendary Resistance. The project STATE.md explicitly records: "Feature detection: search Monster.actions (not raw_text) to avoid lore-paragraph false positives." Scan `Monster.actions[*].raw_text` only.
- **Do not modify `SaveRollService` to call UI code** or accept `Monster` objects. Keep the service pure-Python. Trait detection happens before building `SaveRequest` (in the UI layer).
- **Do not use `QTextEdit.setHtml()` for the entire output panel.** HTML injection into a rolling log makes undo/styling of individual rows fragile. Prefer `QScrollArea` + per-row widgets for the save results display.
- **Do not reset `_lr_counters` on each roll.** LR uses persist across rolls within the same encounter load — this is explicitly locked in CONTEXT.md.
- **Do not build a multi-step wizard for custom rules.** CONTEXT.md says "should feel lightweight." A single inline add row (trigger text box + behavior dropdown + Add button) is sufficient.

---

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Substring matching for trait detection | Custom tokenizer, fuzzy matcher | Python `str.lower()` + `in` check | Exact substring match is the locked decision from CONTEXT.md; no NLP needed |
| Collapsible panel | Custom animation | `QWidget.setVisible(True/False)` + height toggle (same pattern as sidebar collapse) | The project already does instant show/hide — QPropertyAnimation was rejected in Phase 10 UAT |
| Per-row colored output | QTextEdit HTML spans | Per-row QWidget with setStyleSheet background-color rgba | Consistent with combatant card style from Phase 11 |
| Rule persistence | SQLite, custom format | JSON via PersistenceService._save() | Project decision: JSON only, zero new dependencies |

---

## Common Pitfalls

### Pitfall 1: Scanning Wrong Text Source for Traits
**What goes wrong:** Searching `Monster.raw_text` or `Monster.lore` for "Magic Resistance" produces false positives when a creature's lore paragraph describes having resistance to magic in narrative form.
**Why it happens:** The parser stores the full source text in `Monster.raw_text` and lore text in `Monster.lore`; these contain much more text than the statblock traits.
**How to avoid:** Use `Monster.actions[*].raw_text` only. The `CombatTrackerService` sets this precedent.
**Warning signs:** MR detected on creatures that have "magic" anywhere in lore.

### Pitfall 2: LR Count Wrong When Monster Has Multiple LR Actions
**What goes wrong:** If a monster's actions list contains two entries that both mention "Legendary Resistance (3/Day)", the `max()` reduction in the existing pattern handles this correctly. But a naively written scanner might double-count.
**Why it happens:** Some format parsers split statblock sections differently, producing duplicate raw_text entries.
**How to avoid:** Use `max(lr_max, int(lr_m.group(1)))` rather than accumulating.  This is already the CombatTrackerService pattern — replicate it.

### Pitfall 3: SaveParticipant Backward Compatibility
**What goes wrong:** Adding required fields to `SaveParticipant` breaks `CombatTrackerTab._on_send_to_saves()` which constructs `SaveParticipant(name=..., save_bonus=...)` positionally.
**Why it happens:** New fields are not keyword-only by default in dataclasses if positional args precede them.
**How to avoid:** Use `field(default_factory=...)` or `= None` defaults for all new fields. Keep `name` and `save_bonus` as the first two positional fields. All other fields keyword-only with defaults.

### Pitfall 4: LR Counter State in Wrong Layer
**What goes wrong:** Storing LR per-creature counters in the service layer (e.g., inside `FeatureDetectionService`) means the UI cannot update them without round-tripping through the service.
**Why it happens:** Temptation to centralize all state in services.
**How to avoid:** `_lr_counters: dict[str, int]` lives in `SavesTab` itself. The service is stateless. The counter is passed IN via `SaveParticipant.lr_uses` at roll time; updates go back to `SavesTab._lr_counters` when the DM clicks "Use?".

### Pitfall 5: QCheckBox on _MonsterRowWidget Breaks Sort
**What goes wrong:** `_sort_by_cr()` rebuilds the `QListWidget` by clearing and re-adding all rows. If checkbox state is not captured before the rebuild and restored after, checked state is lost.
**Why it happens:** `_sort_by_cr()` creates new `_MonsterRowWidget` instances.
**How to avoid:** Before sort, capture `{monster_name: is_checked}` dict. After sort, apply via `row_widget.set_checked(checked_state[monster_name])`.

### Pitfall 6: "Send to Saves" from Combat Tracker Bypasses Checkbox State
**What goes wrong:** COMBAT-14 sends participants directly to `SavesTab.load_participants()`, bypassing any sidebar checkbox selection entirely. The locked decision says this should be configurable: CT selection overrides sidebar (default) or sidebar checkboxes are authoritative.
**Why it happens:** Current `_on_send_to_saves` in `app.py` calls `self._saves_tab.load_participants(participants)` which replaces all participants unconditionally.
**How to avoid:** Add `AppSettings.ct_send_overrides_sidebar: bool = True`. In `MainWindow._on_send_to_saves()`, if `ct_send_overrides_sidebar=False`, filter the incoming participants against the sidebar's currently-checked member names before passing to `load_participants()`. This setting also needs a checkbox in `SettingsTab`.

### Pitfall 7: Collapsible Detection Rules Panel Height
**What goes wrong:** A collapsible panel inside `SavesTab` (which already has a `QVBoxLayout`) pushes the Roll Saves button off screen when expanded.
**Why it happens:** `QVBoxLayout` distributes space equally if no stretch factors are set.
**How to avoid:** Put the detection rules panel in a `QScrollArea` with a fixed maximum height, or use a `QGroupBox` with a checkable toggle (Qt's `QGroupBox.setCheckable(True)` collapses on uncheck).

---

## Code Examples

Verified patterns from the project codebase:

### Existing Legendary Resistance Detection (from CombatTrackerService)
```python
# src/combat/service.py — proven pattern to replicate in FeatureDetectionService
leg_res_match = re.search(
    r"legendary resistance\s*\(?(\d+)/day\)?", raw, re.IGNORECASE
)
if leg_res_match:
    leg_res_max = max(leg_res_max, int(leg_res_match.group(1)))
```

### Existing _MonsterRowWidget Structure (extend with checkbox)
```python
# src/ui/encounter_sidebar.py — current layout: name_label | count_spin | remove_btn
# Phase 12 adds QCheckBox as the FIRST widget:
layout.addWidget(self._check)    # NEW: prepend checkbox
layout.addWidget(self._name_label)
layout.addWidget(self._count_spin)
layout.addWidget(self._remove_btn)
```

### Existing SavesTab._execute_roll() Flow (current — extend this)
```python
# src/ui/encounters_tab.py
def _execute_roll(self) -> None:
    ability = self._save_type_bar.value()
    request = SaveRequest(
        participants=self._participants,  # Phase 12: participants come from sidebar checked list
        ability=ability,
        dc=self._dc_spin.value(),
        advantage=advantage,
        ...
    )
    result = self._save_roll_service.execute_save_roll(request, self._roller)
    # Phase 12: result rows go to _SaveResultRow widgets, not plain text append
    for pr in result.participant_results:
        self._output_panel.append(self._format_participant_line(pr))
```

### Existing PersistenceService Category Pattern (extend with save_rules)
```python
# src/persistence/service.py
_FILENAMES = {
    "loaded_monsters": "loaded_monsters.json",
    "encounters": "encounters.json",
    "modified_monsters": "modified_monsters.json",
    "macros": "macros.json",
    "combat_state": "combat_state.json",
    "player_characters": "player_characters.json",
    # Phase 12 adds:
    "save_rules": "save_rules.json",
}
```

### Collapsible Panel Pattern (QGroupBox approach — simplest for Detection Rules)
```python
# QGroupBox with setCheckable(True) gives built-in collapse toggle
rules_group = QGroupBox("Detection Rules")
rules_group.setCheckable(True)
rules_group.setChecked(False)   # collapsed by default
rules_layout = QVBoxLayout(rules_group)
# ... add rule widgets to rules_layout
```

### FeatureRule Serialization/Deserialization
```python
@dataclass
class FeatureRule:
    trigger: str
    label: str
    behavior: str   # "auto-advantage" | "auto-disadvantage" | "auto-fail" | "auto-pass" | "reminder"
    enabled: bool = True
    is_builtin: bool = False

    def to_dict(self) -> dict:
        return {
            "trigger": self.trigger,
            "label": self.label,
            "behavior": self.behavior,
            "enabled": self.enabled,
            # Never serialize is_builtin — built-ins are code-only
        }

    @classmethod
    def from_dict(cls, d: dict) -> "FeatureRule":
        return cls(
            trigger=d.get("trigger", ""),
            label=d.get("label", ""),
            behavior=d.get("behavior", "reminder"),
            enabled=d.get("enabled", True),
            is_builtin=False,   # all persisted rules are user rules
        )
```

---

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| Single global advantage for all save participants | Per-participant advantage via `SaveParticipant.advantage` | Phase 12 | Magic Resistance creatures roll with advantage even when global is Normal |
| All-or-nothing encounter → saves | Checkbox-filtered subset from sidebar | Phase 12 | DM can exclude already-dead or immune creatures |
| Plain text output only | Per-row QWidget with inline LR button | Phase 12 | Interactive "Use LR" without modal dialogs |
| Hard-coded MR/LR detection | Configurable FeatureRule list | Phase 12 | DM can add "Evasion → reminder" without code changes |

---

## Open Questions

1. **Where does the LR counter per monster-type live across rolls?**
   - What we know: `SavesTab._lr_counters: dict[str, int]` keyed by `monster.name` (not participant name)
   - What's unclear: Should "Goblin 1" and "Goblin 2" share one LR pool? Yes — they're the same stat block.
   - Recommendation: Key by `monster_name` (the base type), not participant display name. When "Goblin 1" uses LR, counter for "Goblin" decrements; next roll of "Goblin 2" sees the decremented count.

2. **Does the sidebar checkbox state persist to disk?**
   - What we know: Sidebar encounter persistence only stores `{name, count}` pairs, no selection state.
   - What's unclear: Should checked state persist between sessions?
   - Recommendation: Do NOT persist checkbox state. Start all checked on each app launch (and on `set_encounter()`). This avoids confusion when a DM returns to a saved encounter days later.

3. **How does load_participants() interact with sidebar checked state when CT sends participants?**
   - What we know: `AppSettings.ct_send_overrides_sidebar = True` (locked decision). When CT overrides, the sent list replaces sidebar checked state.
   - Recommendation: `SavesTab.load_participants()` accepts the CT-sent list directly. The sidebar checkbox state is only read when the DM clicks "Roll Saves" without CT override. The Settings toggle controls which path MainWindow uses in `_on_send_to_saves()`.

4. **Can auto-fail/auto-pass behaviors from custom rules skip the dice roll entirely?**
   - What we know: `SaveRollService` currently always rolls d20. The service design keeps it pure — it doesn't know about feature rules.
   - Recommendation: For auto-fail/auto-pass, roll the dice anyway (for transparency) but force `passed = False / True` in the result. The feature label "(auto-fail)" in the Features column explains the override. This avoids changing `SaveRollService`'s pure-dice contract.

---

## Sources

### Primary (HIGH confidence)
- Direct codebase inspection: `src/ui/encounters_tab.py` — current SavesTab implementation
- Direct codebase inspection: `src/encounter/models.py` — SaveParticipant, SaveRequest, SaveParticipantResult, SaveRollResult
- Direct codebase inspection: `src/encounter/service.py` — SaveRollService, _expand_participants
- Direct codebase inspection: `src/combat/service.py` — existing LR/MR regex pattern (lines 159-177)
- Direct codebase inspection: `src/ui/encounter_sidebar.py` — _MonsterRowWidget, get_members(), _sort_by_cr()
- Direct codebase inspection: `src/persistence/service.py` — _FILENAMES pattern for new category
- Direct codebase inspection: `src/ui/app.py` — _on_send_to_saves(), signal wiring pattern
- Direct codebase inspection: `src/settings/models.py` — AppSettings dataclass extension pattern
- Direct codebase inspection: `.planning/STATE.md` — project decisions (raw_text scan scope, JSON-only persistence, no QPropertyAnimation)

### Secondary (MEDIUM confidence)
- PySide6 `QGroupBox.setCheckable(True)` — built-in collapsible panel toggle; standard Qt feature, HIGH confidence from Qt docs knowledge
- PySide6 `QCheckBox` in QListWidget item widget — standard pattern, HIGH confidence

### Tertiary (LOW confidence)
- None — all claims are grounded in codebase inspection or well-known Qt API

---

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH — no new libraries; all existing project dependencies
- Architecture: HIGH — based on direct codebase reading of all affected files
- Pitfalls: HIGH — pitfalls 1-3 grounded in existing code patterns; pitfalls 4-7 from architectural analysis

**Research date:** 2026-02-26
**Valid until:** 2026-04-26 (stable codebase; 60 days)
