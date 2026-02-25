# Stack Research

**Domain:** Python desktop app — D&D 5e combat manager (v2.0 additions to existing PySide6 app)
**Researched:** 2026-02-25
**Confidence:** HIGH for persistence and UI patterns; MEDIUM for Roll20 template rendering approach

---

## Existing Stack (Do Not Change)

The v2.0 feature additions are layered on top of these validated, shipped technologies:

| Technology | Version | Role |
|------------|---------|------|
| Python | 3.12 | Runtime |
| PySide6 | 6.10.2 | All UI widgets, signals/slots, theming |
| PyInstaller | 6.19.0 | Windows portable .exe packaging |
| pytest | >=8.0 | Test framework |

All new additions must remain compatible with this base.

---

## New Stack Additions by Feature Area

### 1. Data Persistence (JSON over SQLite)

**Recommendation: stdlib `json` + `dataclasses.asdict()` — zero new dependencies.**

The existing `SettingsService` already demonstrates this pattern working correctly: `dataclasses.asdict()` serializes to dict, `json.dumps()` writes to file, `json.loads()` + field-filtered `AppSettings(**filtered)` reconstructs. V2.0 persistence (modified monsters, encounter state, combat tracker state) follows the same pattern.

**Why not SQLite:** SQLite is better when you need queries, joins, or concurrent writes across many rows. This app persists a few hundred monsters and one active combat state per session. The access pattern is load-all-on-start / write-on-change — no queries needed. JSON is immediately debuggable, directly diff-able in git, and requires no schema migrations. SQLite adds schema versioning overhead with zero benefit for this data scale.

**Why not third-party serialization (pydantic, dataclasses-json, msgspec):** The existing codebase uses pure stdlib dataclasses and zero runtime dependencies beyond PySide6. Adding a serialization library to handle nested dataclasses is unnecessary — custom `to_dict()` / `from_dict()` class methods per model achieve typed round-tripping with 20-30 lines of code per model. The models are stable and small.

**Implementation pattern for nested models:**
```python
# Each persistable dataclass gets explicit to_dict / from_dict
@dataclass
class MonsterOverride:
    monster_id: str
    hp_current: int
    conditions: list[str]

    def to_dict(self) -> dict:
        return dataclasses.asdict(self)

    @classmethod
    def from_dict(cls, data: dict) -> "MonsterOverride":
        return cls(**{k: v for k, v in data.items() if k in {f.name for f in dataclasses.fields(cls)}})
```

**Storage layout within workspace folder:**
```
~/RollinRollin/
  settings.json          # existing — AppSettings
  monster_overrides.json # NEW — modified monster stats
  combat_state.json      # NEW — active tracker state
  lists/                 # existing Markdown
  encounters/            # existing Markdown
```

**Sources:** Existing `src/settings/service.py` (validated pattern); stdlib `sqlite3` docs; community discussion on JSON vs SQLite for small desktop apps.

---

### 2. Combat Tracker UI (HP Bars, Conditions, Initiative)

**Recommendation: Pure PySide6 — `QProgressBar` with QSS chunk styling + `QFrame`-based condition tags. No new dependencies.**

**HP Bar:** `QProgressBar` styled via `QProgressBar::chunk` in the QSS stylesheet handles green/yellow/red HP display. Dynamic color change (green → yellow below 50% → red below 25%) requires updating the widget's individual stylesheet on each HP change. For a combat tracker with 10-20 combatants maximum, per-widget `setStyleSheet()` calls are acceptable — no performance concern at this scale.

```python
# HP bar with color shift
bar = QProgressBar()
bar.setRange(0, max_hp)
bar.setValue(current_hp)
pct = current_hp / max_hp
if pct > 0.5:
    color = "#4CAF50"   # green
elif pct > 0.25:
    color = "#FF9800"   # orange
else:
    color = "#F44336"   # red
bar.setStyleSheet(f"QProgressBar::chunk {{ background-color: {color}; }}")
```

**Condition badges:** `QLabel` with colored border + background via inline `setStyleSheet()` — already used extensively throughout the codebase. Each condition is a `QLabel` with text "Poisoned (2)" styled as a colored pill badge. No external badge library needed.

**Round countdown:** Stored as `int` in the combat state dataclass. Each `QLabel` badge shows `f"{condition_name} ({rounds_remaining})"` and is rebuilt on each end-of-turn tick.

**Initiative order:** `QListWidget` or custom `QVBoxLayout` of `QFrame` combatant rows, reordered by sorting on initiative value. `QListWidget` supports drag-to-reorder natively via `setDragDropMode(QAbstractItemView.DragDropMode.InternalMove)`.

**Sources:** Qt Style Sheets Examples (doc.qt.io/qt-6/stylesheet-examples.html) — QProgressBar chunk styling; existing `src/ui/macro_result_panel.py` — validated QLabel badge pattern; Qt docs — `QListWidget.setDragDropMode`.

---

### 3. Roll20 Template Card Rendering

**Recommendation: `QLabel.setTextFormat(Qt.TextFormat.RichText)` + `QTextEdit.setHtml()` — use Qt's built-in HTML4 subset. No QWebEngineView.**

**Why not `QWebEngineView`:** Qt WebEngine adds approximately 130-150MB to the PyInstaller bundle (validated: one user reported ~100MB → ~250MB after PyInstaller 5.7.0 added WebEngine hooks). The portable .exe constraint makes this unacceptable. The Roll20 default template (`&{template:default}`) renders a simple two-column table with a colored header row and key/value pairs — no JavaScript, no CSS Grid, no external fonts. Qt's HTML4 subset handles this.

**Qt HTML4 subset capabilities (QTextEdit):**
- `<table>`, `<tr>`, `<td>`, `<th>` with border/padding (supported for tables specifically)
- `<b>`, `<i>`, `<span style="color: ...">`, `<font color="...">` — all supported
- Inline `style=""` attributes for color, font-weight, background-color
- `setDefaultStyleSheet()` on `QTextDocument` for document-wide CSS

**Template rendering approach:** The existing `MacroPreprocessor._extract_template_fields()` already extracts `{{name=...}}` and all other `{{key=value}}` pairs from a macro line into `template_name` and residual expression. The `MacroLineResult.template_name` is already passed through. V2.0 adds a `TemplateCardWidget` (a `QFrame` subclass) that receives the extracted fields dict and renders an HTML table via `QTextEdit.setHtml()`:

```python
def _build_template_html(fields: dict[str, str]) -> str:
    name = fields.pop("name", "Roll")
    rows = "".join(
        f'<tr><td style="color:#aaa;padding:2px 6px">{k}</td>'
        f'<td style="padding:2px 6px">{v}</td></tr>'
        for k, v in fields.items()
    )
    return (
        f'<table style="border-collapse:collapse;width:100%">'
        f'<tr><th colspan="2" style="background:#4a3080;color:white;padding:4px 8px">{name}</th></tr>'
        f'{rows}'
        f'</table>'
    )
```

**What the default template renders:** The Roll20 `&{template:default}` puts `{{name=}}` in a purple header, then lists all other `{{key=value}}` pairs in alternating white/gray rows. This is fully reproducible with HTML table + inline styles in Qt's subset.

**Where it plugs in:** `MacroLineResult` already carries `template_name`. The `ResultCard` in `macro_result_panel.py` already checks `line_result.template_name`. V2.0 extends `ResultCard` to also carry the full `fields: dict` extracted from `{{key=value}}` pairs and renders the card as a styled table when `template_name` is present.

**Model change needed:** `CleanedMacro` and `MacroLineResult` need a new `template_fields: dict[str, str]` field (currently only `template_name` is extracted). `MacroPreprocessor._extract_template_fields()` needs to return the full dict instead of just the name.

**Sources:** PySide6 QTextEdit docs (doc.qt.io/qtforpython-6); PyInstaller QWebEngineView bundle size discussion (github.com/orgs/pyinstaller/discussions/7322); Roll20 wiki on default template fields; existing `src/macro/preprocessor.py`.

---

### 4. Color Theming System

**Recommendation: QSS template string with Python `.format()` substitution — zero new dependencies. No qt-material, no qdarktheme.**

**Why not qt-material or qdarktheme:** Both add runtime dependencies and impose their own visual language (Material Design, flat dark). The app already has a hand-crafted dark stylesheet in `main.py` (`_DARK_STYLESHEET`) that matches its own aesthetic. The requirement is user-selectable color pairs and high-contrast mode — not a full Material redesign.

**Pattern:** Define one QSS template string with `{bg}`, `{fg}`, `{accent}`, `{surface}` placeholders. At startup and on theme change, call `app.setStyleSheet(THEME_TEMPLATE.format(**theme_colors))`. Store the active theme name in `AppSettings`.

```python
THEME_TEMPLATE = """
QWidget {{ background-color: {bg}; color: {fg}; }}
QProgressBar::chunk {{ background-color: {accent}; }}
...
"""

THEMES = {
    "dark":          {"bg": "#2B2B2B", "fg": "#E0E0E0", "accent": "#4DA6FF", "surface": "#1E1E1E"},
    "high_contrast": {"bg": "#000000", "fg": "#FFFFFF", "accent": "#FFFF00", "surface": "#111111"},
    "light":         {"bg": "#F5F5F5", "fg": "#1A1A1A", "accent": "#1565C0", "surface": "#FFFFFF"},
}
```

**Font selection:** `QApplication.setFont(QFont(family, size))` applies globally. Store `font_family` and `font_size` in `AppSettings`. Apply on settings save.

**Damage type color coding** (attack output): The `roll_output.py` and `macro_result_panel.py` widgets already use `<span style="color: ...">` in RichText QLabels. V2.0 adds a `DAMAGE_COLORS` dict in a new `src/ui/theme.py` module:
```python
DAMAGE_COLORS = {
    "fire": "#FF6B35", "cold": "#74C7EC", "lightning": "#FFD700",
    "necrotic": "#9B59B6", "radiant": "#F8C471", "poison": "#58D68D",
    ...
}
```
All output widgets import from `theme.py` instead of hardcoding hex values.

**Integration point:** `MainWindow._apply_settings()` already applies settings to all tabs. Add `_apply_theme(theme_name, font)` called from `_apply_settings()`. The `AppSettings` dataclass gets two new fields: `theme: str = "dark"` and `font_size: int = 10`.

**Sources:** Existing `src/main.py` `_DARK_STYLESHEET` (validates the manual QSS approach); Qt Style Sheets tutorial (doc.qt.io/qtforpython-6/tutorials/basictutorial/widgetstyling.html); `SettingsService` pattern for persistence.

---

### 5. Monster Math Engine (Derived Value Recalculation)

**Recommendation: Pure Python in `src/engine/monster_math.py` — zero new dependencies. All formulas from 5e SRD, encoded directly.**

All 5e monster math is deterministic arithmetic. No library is needed.

**Core formulas to implement:**

```python
# Ability score modifier
def ability_modifier(score: int) -> int:
    return (score - 10) // 2

# Proficiency bonus by CR (2014 PHB table)
_CR_TO_PROF: dict[str, int] = {
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

def proficiency_bonus(cr: str) -> int:
    return _CR_TO_PROF.get(cr, 2)

# Save bonus (proficiency if proficient, else modifier only)
def save_bonus(score: int, cr: str, is_proficient: bool) -> int:
    mod = ability_modifier(score)
    return mod + (proficiency_bonus(cr) if is_proficient else 0)

# Attack bonus = ability modifier + proficiency bonus
def attack_bonus(score: int, cr: str) -> int:
    return ability_modifier(score) + proficiency_bonus(cr)

# AC from armor type + DEX modifier (capped for medium armor)
def armor_class(armor_type: str, dex_score: int, shield: bool = False) -> int:
    dex_mod = ability_modifier(dex_score)
    base = {
        "none": 10 + dex_mod,
        "natural": ...,       # stored directly, not recalculated
        "leather": 11 + dex_mod,
        "studded": 12 + dex_mod,
        "chain_shirt": 13 + min(dex_mod, 2),
        "scale": 14 + min(dex_mod, 2),
        "breastplate": 14 + min(dex_mod, 2),
        "half_plate": 15 + min(dex_mod, 2),
        "ring": 14,
        "chain": 16,
        "splint": 17,
        "plate": 18,
    }[armor_type]
    return base + (2 if shield else 0)
```

**Cascade order:** When a stat changes, recalculate in this order:
1. Ability score change → recalculate modifier → recalculate all saves, attack bonuses that use that score
2. CR change → recalculate proficiency bonus → recalculate all saves (proficient ones), all attack bonuses
3. Equipment change → recalculate AC only

**Monster Editor integration:** The `Monster` dataclass gets two new fields: `base_ability_scores: dict[str, int]` (the original imported values) and `equipment_overrides: list[EquipmentPreset]`. The `MonsterOverride` persistence model stores only the delta (what the user changed). `MonsterMathEngine.apply_overrides(base_monster, overrides) -> Monster` computes the fully-resolved monster for use in combat.

**Sources:** D&D 5e SRD (proficiency bonus table, ability modifier formula); D&D Beyond Basic Rules for monsters; existing `src/domain/models.py` Monster dataclass.

---

## Supporting Libraries Summary

| Library | Version | Purpose | Source |
|---------|---------|---------|--------|
| `json` (stdlib) | Python 3.12 | Persist monster overrides, combat state | Existing pattern validated |
| `dataclasses` (stdlib) | Python 3.12 | Model serialization via `asdict()` / `from_dict()` | Existing pattern validated |
| `sqlite3` (stdlib) | Python 3.12 | NOT recommended — see persistence section | Considered and rejected |
| PySide6 (existing) | 6.10.2 | QProgressBar HP bars, QFrame condition tags, QTextEdit template cards, QSS theming | All features in existing install |

**No new pip installs required for v2.0.**

---

## What NOT to Add

| Avoid | Why | Use Instead |
|-------|-----|-------------|
| `PySide6.QtWebEngineWidgets.QWebEngineView` | Adds ~130-150MB to PyInstaller bundle; violates portable .exe constraint | `QTextEdit.setHtml()` with Qt's HTML4 subset |
| `qt-material` or `qdarktheme` | Imposes external visual language; adds dependency; existing hand-crafted QSS works fine | Python `.format()` substitution on QSS template string |
| `pydantic` / `dataclasses-json` / `msgspec` | No trust boundary for serialization (internal data only); stdlib `asdict()` + `from_dict()` is sufficient | Explicit `to_dict()` / `from_dict()` class methods on dataclasses |
| `SQLite` for primary persistence | No query/join needs; load-all/write-on-change pattern; JSON is simpler and human-readable | stdlib `json` module |
| Any ORM (SQLAlchemy, peewee) | Massive overkill for 3 JSON files; schema migration overhead | Plain JSON I/O |
| `darkdetect` | System theme sync not in scope; user picks theme explicitly | `AppSettings.theme` field |

---

## Stack Patterns by Variant

**If combat tracker grows to 50+ combatants:**
- Switch HP bar from per-widget `setStyleSheet()` to `QPainter.paintEvent()` in a custom `QWidget` subclass
- Because `setStyleSheet()` triggers full style recomputation per widget; custom paint avoids this
- Unlikely at DnD table scale (typical: 5-20 combatants)

**If Roll20 template rendering needs JavaScript (e.g., roll buttons in template):**
- Use `QWebEngineView` in a separate optional widget (import-guarded)
- Because template rendering with JS requires a real browser engine
- The default template and most common macros do NOT need this

**If persistence grows to 1000+ monsters with frequent filtered queries:**
- Migrate to `sqlite3` with a schema migration helper
- Because JSON load-all-at-start becomes slow above ~500KB
- Current use case (hundreds of monsters) stays well within JSON limits

---

## Version Compatibility

| Package | Compatible With | Notes |
|---------|-----------------|-------|
| PySide6 6.10.2 | Python 3.12 | Validated in v1.0; no changes |
| PyInstaller 6.19.0 | PySide6 6.10.2 | Validated in v1.0 build; spec file must NOT import QtWebEngineWidgets |
| pytest >=8.0 | Python 3.12 | Dev dependency only; not bundled |
| stdlib `json`, `dataclasses`, `sqlite3` | Python 3.12 | All stdlib; no version concerns |

---

## Installation

No new packages required for v2.0.

```bash
# Existing dev environment — no changes needed
pip install PySide6==6.10.2 PyInstaller==6.19.0 pytest>=8.0
```

---

## Sources

- Existing `src/settings/service.py` — validated JSON+dataclass persistence pattern
- Existing `src/main.py` `_DARK_STYLESHEET` — validated QSS theming approach
- Existing `src/macro/preprocessor.py` — validated `{{key=value}}` template field extraction
- Existing `src/macro/models.py` — `MacroLineResult.template_name` already in model
- [Qt Style Sheets Examples — QProgressBar chunk styling](https://doc.qt.io/qt-6/stylesheet-examples.html)
- [PySide6 QTextEdit docs — HTML4 subset support](https://doc.qt.io/qtforpython-6/PySide6/QtWidgets/QTextEdit.html)
- [PySide6 QPainter — custom widget paint](https://doc.qt.io/qtforpython-6/PySide6/QtGui/QPainter.html)
- [PyInstaller QWebEngineView bundle size discussion](https://github.com/orgs/pyinstaller/discussions/7322) — ~150MB bundle bloat confirmed; MEDIUM confidence (community report, not official benchmark)
- [Roll20 default template structure](https://wiki.roll20.net/Roll_Templates/Default) — name= in header, key=value rows in table; MEDIUM confidence (403 on wiki fetch; confirmed via community forum cross-reference)
- [D&D 5e proficiency bonus by CR table](https://www.dndbeyond.com/sources/dnd/basic-rules-2014/monsters) — HIGH confidence (official source)
- [Python sqlite3 vs JSON desktop app tradeoffs](https://forum.qt.io/topic/98095/should-i-manage-my-data-in-memory-or-use-sqlite) — MEDIUM confidence (forum discussion, aligns with stdlib docs guidance)

---

*Stack research for: RollinRollin v2.0 combat manager features*
*Researched: 2026-02-25*
