---
phase: 16-buff-system-output-improvements
verified: 2026-02-28T00:00:00Z
status: passed
score: 10/10 success criteria verified
re_verification: false
human_verification:
  - test: "Attack output header display"
    expected: "Bold header 'Young Red Dragon — Bite (5x)' appears before first attack line in output panel"
    why_human: "UI rendering of HTML in QTextBrowser requires visual inspection"
  - test: "Buff dice in attack output: first vs subsequent label"
    expected: "First attack shows '+ Bless 1d4(3)', subsequent attacks show '+ 1d4(2)'"
    why_human: "Abbreviated vs full label logic is in HTML output — needs visual confirmation"
  - test: "Damage type colored summary"
    expected: "COMPARE mode summary shows '475 — 398 piercing, 77 fire' with correct damage-type colors when multiple types present"
    why_human: "HTML color rendering in QTextBrowser requires visual inspection"
  - test: "Sidebar resize via drag"
    expected: "User can drag the sidebar left edge to resize; sidebar holds new width after release"
    why_human: "Qt dock widget resize behavior requires interactive testing"
  - test: "Sidebar width persists across sessions"
    expected: "After resizing and closing/reopening app, sidebar opens at previously set width"
    why_human: "Requires launching app twice"
  - test: "HP bar descriptive labels: all 5 bands"
    expected: "All 5 bands display correct label and color (Uninjured=bright green, Barely Injured=green-yellow, Injured=yellow, Badly Injured=orange, Near Death=red, Defeated=grey/no-text)"
    why_human: "Visual output of QPainter requires launching Combat Tracker and damaging combatants"
  - test: "Encounter name double-click inline edit in load dialog"
    expected: "Double-clicking an encounter name in the Load dialog makes it editable inline; pressing Enter saves the new name"
    why_human: "Qt QListWidget inline editing requires interactive UI testing"
---

# Phase 16: Buff System & Output Improvements — Verification Report

**Phase Goal:** Revamp the buff system so each buff can independently target specific roll types (attacks, saves, ability checks, damage), auto-calculate buff dice into attack and save rolls, add creature/attack headers and per-damage-type summaries to attack output, implement encounter naming with timestamps and editable names, make the sidebar user-resizable, and add descriptive health-level text to combat tracker HP bars

**Verified:** 2026-02-28
**Status:** passed (automated checks all green; human verification recommended for UI behaviors)
**Re-verification:** No — initial verification

---

## Goal Achievement

### Observable Truths (from ROADMAP.md Success Criteria)

| # | Truth | Status | Evidence |
|---|-------|--------|----------|
| 1 | A buff can be configured to affect attacks and saves but NOT ability checks or damage — 4 independent checkboxes (BUFF-01) | VERIFIED | `BuffItem` has `affects_attacks`, `affects_saves`, `affects_ability_checks`, `affects_damage` booleans. `_BUFF_CHECKBOX_ATTRS` drives 4 `QCheckBox` widgets per buff row in editor. `_on_buff_checkbox_changed()` wired. |
| 2 | A monster with Bless (+1d4 attacks) has the d4 automatically rolled and added to each attack roll's to-hit total (BUFF-02) | VERIFIED | `_build_roll_request()` filters `monster.buffs` by `affects_attacks=True`, creates `BonusDiceEntry(formula=buff.bonus_value, label=buff.name)` and appends to `RollRequest.bonus_dice`. Service rolls these entries and adds to to-hit total. |
| 3 | A monster with Bless (+1d4 saves) has the d4 automatically rolled and added to save roll totals (BUFF-03) | VERIFIED | `_expand_participants()` injects `BonusDiceEntry` per `affects_saves=True` buff into `SaveParticipant.bonus_dice`. `SaveRollService._roll_one_participant()` merges global + per-participant bonus dice and adds to total. CT path covered via `_execute_roll()` injection. |
| 4 | Attack output starts with a header line identifying the creature and attack type (OUT-01) | VERIFIED | `_on_roll()` builds `self._last_header = f"{monster.name} — {action.name} ({count}x)"`. `_render_results()` prepends `<b>{self._html_escape(self._last_header)}</b>` before attack lines. |
| 5 | Summary line shows per-damage-type subtotals with matching damage-type colors (OUT-02) | VERIFIED | `_format_summary_html()` aggregates `type_totals` from `ar.damage_parts` and `ar.crit_extra_parts`. When `len(type_totals) > 1`, appends colored segments via `_color_damage_segment()`. Buff totals excluded (bonus_dice_results not added to type_totals). |
| 6 | Saved encounters include hour:minute timestamps and support custom names (ENC-01) | VERIFIED | `_generate_auto_name()` returns `f"{ts} — {count} creature(s)"` with `strftime("%Y-%m-%d %H:%M")`. `get_save_name()` returns `"{custom} — {auto_base}"` when DM typed custom text, or pure auto-name otherwise. Used in `app._on_sidebar_save()`. |
| 7 | Encounter names are editable by double-clicking in the load dialog (ENC-02) | VERIFIED | `LoadEncounterDialog` sets `DoubleClicked` edit triggers, `ItemIsEditable` flag per item, `blockSignals` during population, `itemChanged` wired to `_on_item_renamed()`. `pending_renames()` accessor consumed by `app._on_sidebar_load()` via `rename_saved_encounter()`. |
| 8 | The sidebar can be resized by dragging its edge; width persists across sessions (ENC-03) | VERIFIED | `resizeEvent()` tracks `_expanded_width` when not collapsed and width >= 200. `_expand()` calls `resize(self._expanded_width, ...)`. `set_expanded_width()` restores on startup from `AppSettings.sidebar_width`. `closeEvent` saves `self._sidebar.width()` to settings. |
| 9 | HP bars show descriptive text matching the HP percentage (COMBAT-UX-01) | VERIFIED | `HpBar.paintEvent()` assigns label strings: "Near Death" (<=25%), "Badly Injured" (<=50%), "Injured" (<=75%), "Barely Injured" (<100%), "Uninjured" (100%), `""` (0%). Text drawn with white+shadow via `QPainter`. |
| 10 | HP bar colors align with the 5-band health level system (COMBAT-UX-02) | VERIFIED | `HpBar.paintEvent()` assigns matching colors: `#F44336` (red), `#FF6B35` (orange), `#FFC107` (yellow), `#8BC34A` (green-yellow), `#4CAF50` (bright green), `#666666` (grey/defeated). Matches ROADMAP spec exactly. |

**Score: 10/10 truths verified**

---

## Required Artifacts

| Artifact | Expected | Status | Details |
|----------|----------|--------|---------|
| `src/domain/models.py` | BuffItem with 4 boolean fields, `_BUFF_TARGET_MIGRATION` mapping, `from_dict()` migration | VERIFIED | `affects_attacks/saves/ability_checks/damage` booleans with correct defaults (True/True/False/False). `_BUFF_TARGET_MIGRATION` dict covers all 5 old string values. `from_dict()` migrates old "targets" key to booleans. No `targets: str` field on `BuffItem`. |
| `src/ui/monster_editor.py` | Buff section with 4 QCheckBox per row, `_on_buff_checkbox_changed()` | VERIFIED | `QCheckBox` imported. `_BUFF_CHECKBOX_ATTRS` constant drives 4 checkboxes per buff row with `_on_buff_checkbox_changed()` handler via `setattr` dispatch. |
| `src/ui/attack_roller_tab.py` | Buff injection into `RollRequest`, output header, damage type summary, `_format_bonus_dice_part()` | VERIFIED | `BonusDiceEntry` import. `_last_header`/`_last_monster` fields. `_build_roll_request(monster=None)` injects buff dice. `_render_results()` prepends header. `_format_summary_html(attack_rolls)` builds type_totals. `_format_bonus_dice_part()` handles full/abbreviated labels. |
| `src/ui/encounters_tab.py` | Buff injection into `SaveParticipant.bonus_dice`, `_SaveResultRow` with `is_first` | VERIFIED | `BonusDiceEntry` import. `_expand_participants()` injects save buffs. `_execute_roll()` handles CT path. `_SaveResultRow.__init__` and `_format_line()` accept `is_first` parameter. |
| `src/encounter/models.py` | `SaveParticipant.bonus_dice` field | VERIFIED | `bonus_dice: list = field(default_factory=list)` present on `SaveParticipant`. |
| `src/encounter/service.py` | `_roll_one_participant()` merges global + per-participant bonus dice | VERIFIED | `all_bonus_dice = list(request.bonus_dice) + list(getattr(participant, "bonus_dice", []))` — all entries rolled, results accumulated in `bonus_dice_results`. |
| `src/ui/encounter_sidebar.py` | `QLineEdit _name_edit`, `_generate_auto_name()`, `_update_auto_name()`, `get_save_name()`, `resizeEvent()`, `set_expanded_width()` | VERIFIED | All methods present and wired. `_name_edit` replaces former label. `_current_auto_name` tracks last auto-name for custom-name guard. `resizeEvent` tracks expanded width. |
| `src/ui/app.py` | `_on_sidebar_save()` uses `get_save_name()`, `_on_sidebar_load()` processes `pending_renames()` | VERIFIED | `name = self._sidebar.get_save_name()` in save handler. `dialog.pending_renames()` loop calls `rename_saved_encounter()`. Renames processed before deletions. |
| `src/ui/load_encounter_dialog.py` | Double-click inline edit, `_pending_renames`, `pending_renames()` accessor | VERIFIED | `DoubleClicked` edit trigger. `ItemIsEditable` flag per item. `blockSignals` during population. `_on_item_renamed()` extracts name before em-dash, stores in `_pending_renames`. `pending_renames()` returns copy of dict. |
| `src/persistence/service.py` | `rename_saved_encounter(index, new_name)` | VERIFIED | Loads encounters JSON, sets `saved[index]["name"] = new_name`, saves back. Bounds-checked. |
| `src/ui/hp_bar.py` | `HpBar` with 5-band color + descriptive text overlay in `paintEvent()` | VERIFIED | 6-state if/elif chain assigns both color and label. Text drawn with shadow+white. `if label:` guard skips drawing for defeated state. Temp HP and click behavior unchanged. |

---

## Key Link Verification

| From | To | Via | Status | Details |
|------|----|-----|--------|---------|
| `src/domain/models.py` | `src/ui/monster_editor.py` | `BuffItem` consumed by editor checkbox wiring via `_BUFF_CHECKBOX_ATTRS` | VERIFIED | `_rebuild_buff_rows()` iterates `_BUFF_CHECKBOX_ATTRS`, checks `getattr(buff, attr)` per item. `_on_buff_checkbox_changed()` uses `setattr`. |
| `src/domain/models.py` | `MonsterModification.from_dict()` | `_BUFF_TARGET_MIGRATION` mapping old targets to new booleans | VERIFIED | `_BUFF_TARGET_MIGRATION` defined at module level. `from_dict()` pops "targets" and calls `b.update(_BUFF_TARGET_MIGRATION.get(...))`. |
| `src/ui/attack_roller_tab.py` | `src/roll/models.py` | `BonusDiceEntry` injected from monster buffs into `RollRequest.bonus_dice` | VERIFIED | `_build_roll_request()` filters `affects_attacks=True` buffs, creates `BonusDiceEntry(formula=buff.bonus_value, label=buff.name)` appended to bonus_dice. |
| `src/ui/attack_roller_tab.py` | `DAMAGE_COLORS` | `_color_damage_segment` used for per-type summary coloring | VERIFIED | `_color_damage_segment(v, k)` called in list comprehension inside `_format_summary_html()`. `DAMAGE_COLORS` dict used inside that method. |
| `src/ui/encounters_tab.py` | `src/encounter/models.py` | `BonusDiceEntry` injected into `SaveParticipant.bonus_dice` for save buffs | VERIFIED | `_expand_participants()` creates `BonusDiceEntry` list for each monster's `affects_saves=True` buffs. CT path in `_execute_roll()` covers non-sidebar participants. |
| `src/ui/encounter_sidebar.py` | `src/ui/app.py` | `get_save_name()` consumed in save handler | VERIFIED | `app._on_sidebar_save()` calls `self._sidebar.get_save_name()`. |
| `src/ui/encounter_sidebar.py` | Qt resize persistence | `resizeEvent` tracks width, `set_expanded_width()` restores on startup, `closeEvent` saves to `AppSettings.sidebar_width` | VERIFIED | All three legs present: track, restore, save. `AppSettings.sidebar_width: int = 300` default. |
| `src/ui/hp_bar.py` | `HpBar.paintEvent` | `hp_pct` determines both color band and label text | VERIFIED | Single if/elif chain assigns both `hp_color` and `label` together from `hp_pct`. |

---

## Requirements Coverage

All phase 16 requirement IDs are defined in `ROADMAP.md` (not in `REQUIREMENTS.md` — these are phase-local IDs introduced in Phase 16 planning, not tracked in the v2.0 requirements table). Cross-referencing against plan frontmatter:

| Requirement | Source Plan | Description | Status | Evidence |
|-------------|-------------|-------------|--------|----------|
| BUFF-01 | 16-01-PLAN.md | Per-roll-type buff targeting via 4 boolean fields + checkboxes | SATISFIED | `BuffItem` has 4 booleans; editor shows 4 `QCheckBox` per buff; defaults = attacks+saves |
| BUFF-02 | 16-02-PLAN.md | Buff auto-calculation in attack rolls | SATISFIED | `BonusDiceEntry` injected into `RollRequest.bonus_dice` when `affects_attacks=True` |
| BUFF-03 | 16-02-PLAN.md | Buff display and calculation in saves | SATISFIED | `SaveParticipant.bonus_dice` populated from `affects_saves=True` buffs; merged in `_roll_one_participant()` |
| OUT-01 | 16-02-PLAN.md | Attack output header with creature/attack name | SATISFIED | `_last_header` built in `_on_roll()`, prepended as `<b>` tag in `_render_results()` |
| OUT-02 | 16-02-PLAN.md | Damage type breakdown in summary with colors | SATISFIED | `_format_summary_html()` builds `type_totals` and appends colored breakdown when `>1` types |
| ENC-01 | 16-03-PLAN.md | Encounter naming with hour:minute timestamps | SATISFIED | `_generate_auto_name()` uses `strftime("%Y-%m-%d %H:%M")`. `get_save_name()` composes custom + auto. |
| ENC-02 | 16-03-PLAN.md | Encounter name editing in load dialog | SATISFIED | `DoubleClicked` triggers + `ItemIsEditable` + `itemChanged` → `_on_item_renamed()` → `pending_renames()` → `rename_saved_encounter()` |
| ENC-03 | 16-03-PLAN.md | Sidebar user-resizable width with persistence | SATISFIED | `resizeEvent` + `_expand()` + `set_expanded_width()` + `AppSettings.sidebar_width` fully wired |
| COMBAT-UX-01 | 16-04-PLAN.md | Health bar descriptive text labels | SATISFIED | `HpBar.paintEvent()` assigns label string per band, draws with shadow+white `QPainter` text |
| COMBAT-UX-02 | 16-04-PLAN.md | Health bar color consistency with 5-band system | SATISFIED | `HpBar.paintEvent()` uses 6 distinct colors aligned to ROADMAP spec bands |

**Note on REQUIREMENTS.md:** BUFF-01 through BUFF-03, OUT-01 through OUT-02, ENC-01 through ENC-03, and COMBAT-UX-01 through COMBAT-UX-02 do not appear in `REQUIREMENTS.md` — these are phase-16-specific requirement IDs defined only in `ROADMAP.md`. This is not a gap; the requirements and their traceability live entirely within the roadmap for this phase. No orphaned requirements found.

---

## Anti-Patterns Found

Scanned all 11 modified files. No blockers or stubs found.

| File | Pattern | Severity | Impact |
|------|---------|----------|--------|
| `src/ui/attack_roller_tab.py:99` | `_placeholder_label` variable name | Info | UI placeholder label for "no monster selected" — legitimate UI element, not a stub |
| `src/persistence/service.py:37,92,135,168` | `return {}` / `return []` | Info | Error-path returns in JSON load functions — appropriate defensive fallbacks, not stub implementations |

---

## Human Verification Required

### 1. Attack Output Header

**Test:** Open app, select a monster (e.g. Young Red Dragon), roll 5 attacks in the Attack Roller tab.
**Expected:** A bold header line appears first in the output: "Young Red Dragon — Bite (5x)"
**Why human:** Qt HTML rendering in QTextBrowser requires visual inspection.

### 2. Buff Dice in Attack Output — Full vs Abbreviated Label

**Test:** Add a Bless buff (+1d4, Attacks checked) to a monster in the editor. Roll 5+ attacks.
**Expected:** First attack line shows `+ Bless 1d4(N)`, attacks 2-5 show `+ 1d4(N)`. The d4 value is added to the to-hit total on each attack.
**Why human:** HTML diff between first/subsequent lines requires visual inspection; math verification requires comparing totals.

### 3. Damage Type Colored Summary

**Test:** Use a dragon with both piercing and fire damage. Roll 10+ attacks in COMPARE mode.
**Expected:** Summary line shows `— 398 piercing, 77 fire` appended after total damage, with "piercing" in slate-gray and "fire" in orange (#FF6B35).
**Why human:** Color rendering in QTextBrowser and correct segmentation requires visual confirmation.

### 4. Sidebar Resize via Drag

**Test:** Launch app. Attempt to drag the sidebar's left/right edge to make it wider or narrower.
**Expected:** Sidebar resizes smoothly as the user drags. New width holds after releasing.
**Why human:** Qt dock widget resize handle behavior depends on OS/theme and requires interactive testing.

### 5. Sidebar Width Persists Across Sessions

**Test:** Resize the sidebar to a non-default width. Close the app. Reopen the app.
**Expected:** Sidebar opens at the previously set width, not the 300px default.
**Why human:** Requires launching the app twice and comparing sidebar widths.

### 6. HP Bar Descriptive Labels — All 5 Bands

**Test:** Start combat with a monster. Set HP to 100%, ~80%, ~60%, ~35%, ~15%, and 0%.
**Expected:** Each band shows the correct label and color: Uninjured (bright green), Barely Injured (green-yellow), Injured (yellow), Badly Injured (orange), Near Death (red), and 0% shows grey with no text.
**Why human:** QPainter text overlay and color bands require visual verification in the Combat Tracker.

### 7. Encounter Name Double-Click Inline Edit

**Test:** Save an encounter. Open the Load Encounter dialog. Double-click the encounter name.
**Expected:** The name field becomes editable inline. Type a new name and press Enter. Accept the dialog. Reopen Load dialog — the renamed encounter appears with the new name.
**Why human:** Qt QListWidget inline editing requires interactive UI testing.

---

## Gaps Summary

No gaps found. All 10 observable truths are verified against the actual codebase:

- All 4 plans executed with substantive implementation (not stubs)
- All 7 commits verified to exist in git history
- All key wiring verified: buff injection flows through to RollService and SaveRollService
- All artifacts exist with expected content patterns
- 514 tests collected; plan summaries report all passing after each task
- No blocker anti-patterns found

The phase goal is fully achieved programmatically. Human verification is recommended for 7 UI behaviors that require visual/interactive testing to confirm correct rendering and widget behavior.

---

_Verified: 2026-02-28_
_Verifier: Claude (gsd-verifier)_
