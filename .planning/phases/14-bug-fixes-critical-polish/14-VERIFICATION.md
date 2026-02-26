---
phase: 14-bug-fixes-critical-polish
verified: 2026-02-27T00:00:00Z
status: passed
score: 21/21 must-haves verified
re_verification: false
human_verification:
  - test: "Collapsed sidebar shows 24px narrow strip with 'Show' text rendered vertically (bottom-to-top)"
    expected: "The collapsed sidebar edge strip is ~24px wide. 'Show' text is legible when rotated 90 degrees. Clicking the strip expands the sidebar normally."
    why_human: "QPainter rotation rendering can only be verified visually."
  - test: "Crit attack lines show gold tint covering text width only — not full QTextEdit line width"
    expected: "Roll attacks with crits. The gold background behind the crit line ends at the text boundary, not the edge of the panel. No extra blank line below the crit line."
    why_human: "QTextEdit HTML span vs div rendering difference is visual only."
  - test: "Regular misses have no background tint; nat-1 misses have red tint"
    expected: "Roll attacks producing misses. Regular misses are plain text (no color). Nat-1 misses have a red background tint on the text only."
    why_human: "HTML span rendering is visual. Nat-1 requires observing the actual die face."
  - test: "Stats toggle shows/hides stat labels on combatant cards"
    expected: "Open Combat Tracker with an encounter loaded. Click Stats button. Check 'Speed'. Speed values appear on all combatant cards. Uncheck 'Speed'. Values disappear."
    why_human: "PySide6 widget visibility is a runtime behavior; triggering QMenu actions requires live app interaction."
  - test: "Group HP bar click opens damage input; damage distributes first-come-first-served"
    expected: "Load a group of 3 monsters. Click the group HP bar. A damage input appears. Enter -15. Damage applies to first non-defeated member; overflow goes to next. Verify individual HP bars update."
    why_human: "Group card interaction and HP distribution require live app testing."
  - test: "Double-click an expanded group member card collapses it back to CompactSubRow"
    expected: "Expand a group member by clicking its CompactSubRow. The full CombatantCard appears. Double-click the expanded card. It collapses back to the CompactSubRow."
    why_human: "Double-click mouse event sequence requires manual interaction."
  - test: "LR counters persist across multiple save rolls; reset only on encounter membership change"
    expected: "Load an encounter with a legendary-resistance creature. Roll saves. Use 1 LR (counter goes from 3 to 2). Roll saves again without changing the encounter. Counter should still show 2. Add or remove a monster. Counter resets to 3."
    why_human: "Multi-step session state requires live app interaction to verify."
  - test: "Condition chips wrap to 2 rows via FlowLayout; '+' button always at far left"
    expected: "Add 5+ conditions to a combatant. Chips wrap to a second row. No horizontal scroll. The '+' button is always the leftmost element. Chips on row 3+ are hidden."
    why_human: "FlowLayout geometry depends on widget width at runtime; can only be verified visually."
  - test: "Init label is outside the spinbox as a separate QLabel"
    expected: "Combatant cards show 'Init' as a grey label to the left of the initiative spinbox. The spinbox shows only the number, no prefix text."
    why_human: "Visual widget layout requires live app inspection."
---

# Phase 14: Bug Fixes and Critical Polish — Verification Report

**Phase Goal:** Fix all verified bugs from the v2.0 manual testing round and apply quick UX improvements to the Combat Tracker, Attack Roller output, and Encounter Sidebar — every fix is a targeted change to existing code with no new tabs, services, or major UI restructuring required.

**Verified:** 2026-02-27
**Status:** PASSED
**Re-verification:** No — initial verification

---

## Goal Achievement

### Observable Truths

| #  | Truth                                                                                               | Status     | Evidence                                                                                          |
|----|-----------------------------------------------------------------------------------------------------|------------|---------------------------------------------------------------------------------------------------|
| 1  | Imported monsters from MD files survive app close+reopen                                            | VERIFIED   | `source_files_changed` signal in library_tab.py; `_reload_persisted_monster_files` in app.py     |
| 2  | Clicking a single search result in the library selects the full row and loads the statblock         | VERIFIED   | `_on_selection_changed` uses `selectedRows()` not `selected.indexes()`                            |
| 3  | Collapsed sidebar strip is narrow (~24px) with vertically rotated 'Show' text                       | VERIFIED   | `_RotatedButton` class with `paintEvent` override; `_COLLAPSED_WIDTH = 24`                        |
| 4  | CR change cascades proficiency to all dependent values in form AND preview                          | VERIFIED   | `_on_cr_changed` calls `_sync_save_toggles(recompute_values=True)` + `_cascade_skills_on_prof_change()` |
| 5  | User-added skill proficiencies display in amber modified-value color                                | VERIFIED   | `_apply_highlights()` builds `skill_parts` with `<span style="color: {COLOR_MANUAL};">` wrapping |
| 6  | Changing an ability score live-updates all dependent skill bonuses in the editor                    | VERIFIED   | `_on_ability_changed` calls `_cascade_skills_on_ability_change(old_scores)`                       |
| 7  | Spellcasting foci correctly annotate spell attack bonus and spell save DC in the editor preview     | VERIFIED   | `_rebuild_preview` calls `_build_focus_annotated_display_copy()` when `_focus_bonus > 0`         |
| 8  | Parser never lets text from Legendary Actions or Lair Actions bleed into regular Actions            | VERIFIED   | `extract_named_section()` used in all 3 parsers; `_extract_section_actions()` populates separate fields |
| 9  | Monster model has separate `legendary_actions` and `lair_actions` fields                            | VERIFIED   | `src/domain/models.py` lines 62-63 declare both fields with `field(default_factory=list)`        |
| 10 | Only natural-1 misses have red background tint; regular misses have no special styling              | VERIFIED   | Regular miss branch returns plain text; nat-1 path only calls `_wrap_miss_line()`                 |
| 11 | Crit lines have gold tint on text content width only via inline `<span>` — no full-width blocks    | VERIFIED   | `_wrap_crit_line` uses `<span>` not `<div>`; `_wrap_miss_line` also corrected to `<span>`        |
| 12 | No extra blank lines below crit output lines                                                        | VERIFIED   | Block `<div>` (which adds implicit margins in QTextEdit) replaced with inline `<span>`            |
| 13 | Stats toggle checkboxes show/hide corresponding stats on combatant cards                            | VERIFIED   | `action.triggered.connect(lambda checked, key=stat_key: self._toggle_stat(key, checked))`        |
| 14 | LR counters persist across save rolls; seeded at max on first detection                             | VERIFIED   | `_lr_counters[base_name] = lr_uses` seed on first detection; `reset_lr_counters` on type-change only |
| 15 | At 0 HP the healthbar is grey, healing works, and no damage goes below 0                           | VERIFIED   | `apply_damage` uses `max(0, c.current_hp - remaining)`; `is_defeated` is a property              |
| 16 | Group HP bars accept damage input on click, distributing first-come-first-served                    | VERIFIED   | `_avg_hp_bar.clicked.connect(_toggle_group_damage_input)`; `_on_group_damage_submitted()` distributes |
| 17 | Double-clicking an expanded CombatantCard in a group collapses it back to CompactSubRow             | VERIFIED   | `mouseDoubleClickEvent` emits `collapse_requested`; `GroupCard._on_collapse_requested` handles it |
| 18 | Rubber-band selection works anywhere — no card drag blocks it                                       | VERIFIED   | `QDrag`/`QMimeData`/`_drag_start_pos` fully removed from `combatant_card.py`                     |
| 19 | Init label is outside the spinbox as a separate QLabel; only the number is inside the spinbox       | VERIFIED   | `QLabel("Init")` added before `_initiative_spin` in both `CombatantCard` and `GroupCard`; no `setPrefix` |
| 20 | Condition '+' button is always at the far-left of each card, before all chips                       | VERIFIED   | `_rebuild_condition_chips` adds `_plus_btn` first via `addWidget(self._plus_btn)` before loop    |
| 21 | Condition chips wrap to new lines via FlowLayout with max 2 rows                                    | VERIFIED   | `FlowLayout` class implemented with `_MAX_ROWS = 2`; `_do_layout` hides widgets on row 3+        |

**Score:** 21/21 truths verified

---

## Required Artifacts

### Plan 01 Artifacts

| Artifact                         | Expected                                        | Status    | Details                                                                 |
|----------------------------------|-------------------------------------------------|-----------|-------------------------------------------------------------------------|
| `src/ui/library_tab.py`          | Import persistence + fixed selection handler    | VERIFIED  | `source_files_changed` signal present; `_imported_paths` set; `selectedRows()` fix confirmed |
| `src/ui/app.py`                  | Startup re-parse of persisted file paths        | VERIFIED  | `_persisted_monsters`, `_reload_persisted_monster_files`, `_on_source_files_changed` all present |
| `src/ui/encounter_sidebar.py`    | Narrow collapsed sidebar with rotated Show text | VERIFIED  | `_RotatedButton` class with `paintEvent`; `_COLLAPSED_WIDTH = 24`      |

### Plan 02 Artifacts

| Artifact                         | Expected                                                    | Status    | Details                                                                 |
|----------------------------------|-------------------------------------------------------------|-----------|-------------------------------------------------------------------------|
| `src/ui/monster_editor.py`       | CR cascade, ability-skill cascade, focus bonus, skill highlight | VERIFIED  | `_on_cr_changed`, `_cascade_skills_on_prof_change`, `_cascade_skills_on_ability_change`, `_build_focus_annotated_display_copy`, `_apply_highlights` all present with correct logic |

### Plan 03 Artifacts

| Artifact                                     | Expected                                                   | Status    | Details                                                                 |
|----------------------------------------------|------------------------------------------------------------|-----------|-------------------------------------------------------------------------|
| `src/domain/models.py`                       | `legendary_actions` and `lair_actions` list fields         | VERIFIED  | Both fields present at lines 62-63 with `field(default_factory=list)`  |
| `src/parser/formats/_shared_patterns.py`     | `SECTION_BOUNDARY_RE` + `extract_named_section` helper     | VERIFIED  | All three present: `SECTION_BOUNDARY_RE`, `extract_named_section()`, `extract_all_sections()` |
| `src/parser/formats/plain.py`                | Section-aware action extraction                            | VERIFIED  | `extract_named_section` imported and used; `_extract_section_actions` populates `legendary_actions`/`lair_actions` |
| `src/parser/formats/homebrewery.py`          | Section-aware action extraction                            | VERIFIED  | Same pattern as `plain.py` — confirmed present                         |
| `src/parser/formats/fivetools.py`            | Section-aware action extraction                            | VERIFIED  | Same pattern confirmed; replaced dead `ACTION_SECTION_RE` usage        |

### Plan 04 Artifacts

| Artifact                         | Expected                                               | Status    | Details                                                                 |
|----------------------------------|--------------------------------------------------------|-----------|-------------------------------------------------------------------------|
| `src/ui/attack_roller_tab.py`    | Fixed `_wrap_crit_line`, `_wrap_miss_line`, miss logic | VERIFIED  | Both wrappers use `<span>`; nat-1 branch only calls `_wrap_miss_line`; regular miss returns plain text |

### Plan 05 Artifacts

| Artifact                         | Expected                                                        | Status    | Details                                                                 |
|----------------------------------|-----------------------------------------------------------------|-----------|-------------------------------------------------------------------------|
| `src/ui/combat_tracker_tab.py`   | Stats menu toggle via `triggered` signal; `_toggle_stat` helper | VERIFIED  | `action.triggered.connect(lambda checked, key=stat_key: self._toggle_stat(...))` confirmed |
| `src/ui/encounters_tab.py`       | LR counters persist; seed on first detection                    | VERIFIED  | `_lr_counters[base_name] = lr_uses` seed; `reset_lr_counters` correctly called |
| `src/combat/service.py`          | `apply_damage` floors at 0 HP                                   | VERIFIED  | `max(0, c.current_hp - remaining)` at line 332                         |

### Plan 06 Artifacts

| Artifact                         | Expected                                                                            | Status    | Details                                                                 |
|----------------------------------|-------------------------------------------------------------------------------------|-----------|-------------------------------------------------------------------------|
| `src/ui/combatant_card.py`       | `FlowLayout`; group damage input; `collapse_requested`; drag removed; Init label; flow chips | VERIFIED  | All present: `FlowLayout` class; `_avg_hp_bar.clicked.connect(_toggle_group_damage_input)`; `collapse_requested` Signal; no `QDrag`/`QMimeData`; `QLabel("Init")` before spinbox; `FlowLayout(spacing=4)` for chip container |

---

## Key Link Verification

### Plan 01 Key Links

| From                     | To                    | Via                                             | Status    | Details                                                       |
|--------------------------|-----------------------|-------------------------------------------------|-----------|---------------------------------------------------------------|
| `library_tab.py`         | `app.py`              | `source_files_changed` signal → persist paths   | VERIFIED  | `self._library_tab.source_files_changed.connect(self._on_source_files_changed)` confirmed in `app.py:96` |
| `app.py`                 | `library_tab.py`      | `_reload_persisted_monster_files` re-parses paths | VERIFIED  | `_load_persisted_data` calls `_reload_persisted_monster_files`; populates `_library_tab._imported_paths = set(paths)` |

### Plan 02 Key Links

| From                     | To                          | Via                                                    | Status    | Details                                                       |
|--------------------------|-----------------------------|--------------------------------------------------------|-----------|---------------------------------------------------------------|
| `monster_editor.py`      | `math_engine.py` (indirect) | `_on_cr_changed` → `_cascade_skills_on_prof_change`    | VERIFIED  | Method exists and is called in `_on_cr_changed`               |
| `monster_editor.py`      | preview panel               | `_rebuild_preview` → `_build_focus_annotated_display_copy` | VERIFIED  | `_rebuild_preview` invokes `_build_focus_annotated_display_copy()` when `_focus_bonus > 0` |

### Plan 03 Key Links

| From                           | To                          | Via                                                    | Status    | Details                                                       |
|--------------------------------|-----------------------------|--------------------------------------------------------|-----------|---------------------------------------------------------------|
| `_shared_patterns.py`          | `plain.py`                  | `import extract_named_section`                         | VERIFIED  | Import confirmed at `plain.py:19`                             |
| `plain.py`                     | `models.py`                 | Populates `monster.legendary_actions` and `monster.lair_actions` | VERIFIED  | `legendary_actions=legendary_actions` and `lair_actions=lair_actions` in Monster constructor call |

### Plan 04 Key Links

| From                     | To                    | Via                                             | Status    | Details                                                       |
|--------------------------|-----------------------|-------------------------------------------------|-----------|---------------------------------------------------------------|
| `attack_roller_tab.py`   | `roll_output.py`      | `append_html` inserts spans into QTextEdit      | VERIFIED  | `_wrap_crit_line` and `_wrap_miss_line` both use inline `<span>`; no block elements |

### Plan 05 Key Links

| From                     | To                       | Via                                                     | Status    | Details                                                       |
|--------------------------|--------------------------|---------------------------------------------------------|-----------|---------------------------------------------------------------|
| `combat_tracker_tab.py`  | `combatant_card.py`      | `_apply_stat_visible_to_all` → `card.set_stat_visible()` | VERIFIED  | `_apply_stat_visible_to_all` iterates `_cards.values()` and calls `card.set_stat_visible(stat_key, visible)` |
| `app.py`                 | `encounters_tab.py`      | `_on_sidebar_encounter_changed` → `reset_lr_counters` on membership change | VERIFIED  | Guards on `current_names != self._prev_encounter_names` before calling `reset_lr_counters()` |

### Plan 06 Key Links

| From                     | To                       | Via                                                          | Status    | Details                                                       |
|--------------------------|--------------------------|--------------------------------------------------------------|-----------|---------------------------------------------------------------|
| `combatant_card.py`      | `combat_tracker_tab.py`  | Card drag removed — events propagate to `CombatantListArea` rubber-band | VERIFIED  | No `QDrag` or `QMimeData` imports remaining in `combatant_card.py` |
| `combatant_card.py`      | `combat/service.py`      | `GroupCard.damage_entered` → `apply_damage` per member       | VERIFIED  | `self.damage_entered.emit(member.id, -absorbed)` called per member in `_on_group_damage_submitted` |

---

## Requirements Coverage

Phase 14 uses phase-internal bug/UX tracking IDs (BUG-01 through BUG-16, UX-01 through UX-05) defined in `14-RESEARCH.md`. These IDs do NOT appear in the central `REQUIREMENTS.md` which covers formal v2.0 requirements (PERSIST-xx, EDIT-xx, etc.) mapped to earlier phases.

The BUG/UX IDs document regressions and polish items discovered during v2.0 manual testing. They are sub-requirements of the formal requirements already marked Complete in REQUIREMENTS.md (e.g., BUG-01 is a defect in PERSIST-01/PERSIST-03; BUG-11 is a defect in COMBAT-01). No orphaned IDs exist — all 21 IDs are claimed and completed across the 6 plans.

| Plan | Requirements Declared | Requirements Completed | Status     |
|------|-----------------------|------------------------|------------|
| 14-01 | BUG-01, BUG-02, UX-01 | BUG-01, BUG-02, UX-01 | SATISFIED  |
| 14-02 | BUG-03, BUG-04, BUG-05, BUG-07 | BUG-03, BUG-04, BUG-05, BUG-07 | SATISFIED  |
| 14-03 | BUG-06 | BUG-06 | SATISFIED  |
| 14-04 | BUG-08, BUG-09, BUG-10 | BUG-08, BUG-09, BUG-10 | SATISFIED  |
| 14-05 | BUG-11, BUG-15, BUG-16 | BUG-11, BUG-15, BUG-16 | SATISFIED  |
| 14-06 | BUG-12, BUG-13, BUG-14, UX-02, UX-03, UX-04, UX-05 | BUG-12, BUG-13, BUG-14, UX-02, UX-03, UX-04, UX-05 | SATISFIED  |

**Note on BUG-06 orphan (BUG-06 is not in the `statblock_parser.py` artifact list in 14-03-PLAN.md):** The plan listed `statblock_parser.py` as a file to be modified for task 2, but the SUMMARY correctly noted it was not modified — the fix was entirely in the shared helper and format parsers. This is a deviation that does NOT affect correctness; the parser orchestration already passed through the `legendary_actions`/`lair_actions` fields from the format parsers.

---

## Anti-Patterns Found

| File | Pattern | Severity | Impact |
|------|---------|----------|--------|
| `src/ui/combatant_card.py` (FlowLayout `_do_layout`) | Comment says "+N more badge" but implementation only hides widgets — no badge widget | Info | Cosmetic: users won't see a count of hidden chips. Plan deviated intentionally (simpler = correct). No functional regression. |
| `src/ui/combat_tracker_tab.py` (`_CardContainer`) | `dragEnterEvent`/`dragMoveEvent`/`dropEvent` dead code remains | Info | Drag acceptance code without any drag source. Harmless dead code. Not a blocker. |

No blocker or warning-level anti-patterns found.

---

## Human Verification Required

9 items require human verification (all UI rendering/interaction behaviors):

### 1. Collapsed Sidebar Rotated Text

**Test:** Run the app. Collapse the encounter sidebar by clicking Hide. Observe the collapsed strip.
**Expected:** Strip is approximately 24px wide. "Show" text is rendered vertically and is legible (readable bottom-to-top). Clicking the strip expands the sidebar normally. The expanded sidebar and "Hide" button look unchanged.
**Why human:** `QPainter` coordinate rotation rendering can only be verified visually.

### 2. Crit Line Gold Tint Coverage

**Test:** Roll attacks with a low crit range or high attack bonus to produce several critical hits. Observe the output panel.
**Expected:** Gold background tint covers only the text content width, not the full width of the output panel. No extra blank line appears below crit output lines. No double-layering of gold tint visible.
**Why human:** QTextEdit `<span>` vs `<div>` layout behavior is visual only.

### 3. Miss Tint Distinction

**Test:** Roll attacks with low bonus vs high AC to produce regular misses. Also roll and wait for a natural 1 miss.
**Expected:** Regular misses appear as plain text with no background color. Natural-1 misses have a red tint background on the text only.
**Why human:** Requires observing actual output during live attack rolls.

### 4. Stats Toggle in Combat Tracker

**Test:** Load an encounter into Combat Tracker. Click the "Stats" button. Check "Speed". Verify speed values appear on all combatant cards. Uncheck "Speed". Verify values disappear.
**Expected:** All combatant cards immediately show/hide the toggled stat. Works for all stat types (Speed, Passive Perception, LR, LA, Regen). State persists after scrolling.
**Why human:** PySide6 `QMenu` triggered signal wiring requires runtime interaction.

### 5. Group Damage Input and Distribution

**Test:** Load 3 identical grouped monsters. Click the group HP bar. Enter "-50" (enough to defeat one or two members).
**Expected:** Damage input appears when HP bar is clicked. After submitting, damage applies to first non-defeated member, overflow to second, etc. Individual HP bars update correctly.
**Why human:** Group card interaction and overflow distribution require live app testing.

### 6. Double-Click Group Collapse

**Test:** In Combat Tracker with a group, click a CompactSubRow to expand it. The full CombatantCard appears. Double-click the expanded card.
**Expected:** The card collapses back to the CompactSubRow view. Single-click still works for re-expansion.
**Why human:** Double-click event sequence requires manual mouse interaction.

### 7. LR Counter Persistence

**Test:** Load an encounter with a legendary resistance creature (e.g., 3 LR uses). Roll saves. Click "Used LR" to consume 1 resistance (counter: 3 → 2). Roll saves again without changing the encounter.
**Expected:** LR counter remains at 2 on the second roll (not reset to 3). Add or remove a different monster. Counter resets to 3.
**Why human:** Multi-step session state across UI interactions requires live manual testing.

### 8. Condition Chip Flow Layout

**Test:** Add 5+ conditions to a single combatant in Combat Tracker.
**Expected:** Chips wrap to a second row. No horizontal scrollbar appears. The "+" button is always the leftmost element on the first row. Chips that would go to a third row are hidden. Card height grows to accommodate 2 rows.
**Why human:** `FlowLayout` geometry depends on widget width at runtime and card resize behavior.

### 9. Initiative Label Presentation

**Test:** Open Combat Tracker with any loaded encounter. Observe individual combatant cards and group card headers.
**Expected:** "Init" appears as a small grey label to the left of the initiative spinbox. The spinbox shows only the numeric value with no "Init " prefix text inside the spinbox widget.
**Why human:** Visual widget layout requires live app inspection.

---

## Gaps Summary

No gaps. All 21 observable truths verified from direct codebase inspection. All artifacts exist and contain substantive, wired implementations.

**Key findings confirming correctness:**

- **BUG-01 (monster persistence):** Full round-trip verified — `source_files_changed` emitted on import, `_on_source_files_changed` saves to persistence, `_reload_persisted_monster_files` called from `_load_persisted_data` on startup, `_library_tab._imported_paths` repopulated.
- **BUG-02 (library selection):** `selectedRows()` correctly replaces per-cell `selected.indexes()`.
- **UX-01 (sidebar):** `_RotatedButton` subclasses `QPushButton`, overrides `paintEvent` with `QPainter.rotate(90)`, `_COLLAPSED_WIDTH = 24`.
- **BUG-03/05 (editor cascades):** `_cascade_skills_on_prof_change()` and `_cascade_skills_on_ability_change()` both exist and are called from their respective change handlers.
- **BUG-04 (skill highlight):** `_apply_highlights()` builds HTML skill text with `<span style="color: {COLOR_MANUAL};">` for modified skills.
- **BUG-07 (focus bonus):** `_build_focus_annotated_display_copy()` called in `_rebuild_preview()` when `_focus_bonus > 0`.
- **BUG-06 (parser bleed):** `SECTION_BOUNDARY_RE`, `extract_named_section()`, and `_extract_section_actions()` all verified in all three format parsers. Both new Monster fields confirmed.
- **BUG-08/09/10 (attack HTML):** Both wrappers use inline `<span>`; regular miss branch returns plain string; nat-1 branch is the only caller of `_wrap_miss_line`.
- **BUG-11 (stats toggle):** `action.triggered.connect(lambda...)` pattern replaces `menu.exec()` return value check. `_toggle_stat()` updates `_visible_stats` and propagates to all cards.
- **BUG-15 (LR counter):** Dual root cause fixed — counter seeded on first detection, reset guarded by `current_names != self._prev_encounter_names`.
- **BUG-16 (0 HP):** Verified correct — `max(0, ...)` in service; no code change needed.
- **BUG-12 (group damage):** `_avg_hp_bar.clicked` connected; `_on_group_damage_submitted` implements first-come-first-served logic.
- **BUG-13 (collapse):** `mouseDoubleClickEvent` emits `collapse_requested`; `GroupCard._on_collapse_requested` handler present.
- **BUG-14/UX-03 (rubber-band):** `QDrag`, `QMimeData`, `_drag_start_pos` all removed from `combatant_card.py` — confirmed zero matches.
- **UX-02 (Init label):** `QLabel("Init")` added before spinbox in both `CombatantCard` and `GroupCard`; no `setPrefix` call remaining.
- **UX-04 (+ button):** `_plus_btn` added first in `_rebuild_condition_chips` before the condition loop.
- **UX-05 (FlowLayout):** `FlowLayout` class with `_MAX_ROWS = 2`; `_do_layout` hides rows 3+; `hasHeightForWidth()` returns `True`.

**Commits verified:** 4291d27, fe24e77, 9a05449, 3e4e7cf, b47fefa, ebdeed1, 3e925b6, 0efed7a, 12b6c90 — all 9 fix/feat commits from phase 14 confirmed present in git log.

---

_Verified: 2026-02-27_
_Verifier: Claude (gsd-verifier)_
