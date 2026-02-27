---
phase: 15-editor-parser-overhaul
verified: 2026-02-28T00:00:00Z
status: passed
score: 11/11 must-haves verified
re_verification: false
---

# Phase 15: Editor Parser Overhaul — Verification Report

**Phase Goal:** Restructure the Monster Editor to separate traits from actions into a dedicated Traits tab, add full after-attack-text editing, label all action input fields, add rollable trait buttons with auto-dice-detection to the Attack Roller, support recharge abilities, add [[XdY]] average notation, display monster speed everywhere, and compact the editor layout — transforming the editor from a flat action list into a structured traits+actions+rollable-abilities system
**Verified:** 2026-02-28
**Status:** PASSED
**Re-verification:** No — initial verification

---

## Goal Achievement

### Observable Truths (Success Criteria)

| # | Truth | Status | Evidence |
|---|-------|--------|----------|
| 1 | Traits (Magic Resistance, Devil's Sight) appear in a separate Traits section, NOT in Actions (PARSE-01) | VERIFIED | `Monster.traits: list[Trait]` field exists in models.py line 100. All three parsers call `_extract_traits()` and classify blocks with no `TO_HIT_RE` and no `HIT_LINE_RE` match as Trait, not Action. Live test: Amphibious and Legendary Resistance extracted to `m.traits`, Bite and Acid Breath stay in `m.actions`. |
| 2 | Each trait can be expanded to show and edit its title and full description text (PARSE-02) | VERIFIED | `TraitEditDialog(QDialog)` at monster_editor.py line 2610 — modal with `QLineEdit` for name and `QTextEdit` (multiline) for description, OK/Cancel buttons. Triggered from Edit button in `_rebuild_trait_rows()`. Modifies Trait in-place on Accept. |
| 3 | After-attack-text for attacks like Aboleth's Tentacle is visible and editable in the action editor (PARSE-03) | VERIFIED | `Action.after_text: str = ""` field in models.py line 78. Populated by all three parsers via `joined[hit_m.end():].strip()`. In editor, `after_text_edit` QTextEdit created per action at line 1613, initially hidden, revealed by "..." toggle button (line 1622). `_on_after_text_changed()` at line 1132 syncs edits to `_working_copy.actions[idx].after_text`. |
| 4 | All action input fields have clear column header labels (PARSE-04) | VERIFIED | Column header row built at monster_editor.py line 1516 with bold QLabels: "Name" (120px), "To-Hit" (55px), "Dmg Dice" (70px), "Bonus" (55px), "Dmg Type" (90px), plus "..." and spacer. Styled with `rgba(255,255,255,15)` background. |
| 5 | Dice formulas within trait text (e.g. "12d8" in dragon breath) are automatically detected (PARSE-05) | VERIFIED | `DICE_IN_TRAIT_RE` in _shared_patterns.py line 67 matches `N (XdY) type damage`. `detect_dice_in_text()` at line 135 returns list of `DetectedDie` stored in `Trait.rollable_dice`. Live test: `detect_dice_in_text('54 (12d8) acid damage')` returns `DetectedDie(full_match='54 (12d8) acid damage', dice_expr='12d8', damage_type='acid', average=54)`. |
| 6 | The Attack Roller shows rollable trait buttons below the standard attack rows; clicking "Acid Breath" rolls the dice and outputs the full trait text with rolled results and damage-type coloring (PARSE-06) | VERIFIED | `_rebuild_action_list()` in attack_roller_tab.py filters `rollable_traits = [t for t in monster.traits if t.rollable_dice]` (line 362). Inserts "Traits" QLabel divider (line 367) and calls `_make_trait_row(trait)` per trait (line 404). `_on_roll_trait()` at line 444 calls `roll_expression(die.dice_expr, self._roller)` for each die. `_format_trait_output()` at line 463 substitutes rolled values in colored `<span>` elements using `DAMAGE_COLORS`. |
| 7 | Recharge abilities auto-roll 1d6 and display the result in the output name with pass/fail coloring (PARSE-07) | VERIFIED | `RECHARGE_RE` in _shared_patterns.py line 73 matches `(Recharge X-Y)` including unicode en-dash. `detect_recharge()` at line 154 returns `(lo, hi)` tuple. In `_on_roll_trait()` at line 455: `recharge_roll = self._roller.roll_one(6)`, pass check `lo <= recharge_roll <= hi`. `_format_trait_output()` at line 479 colors result green `#4CAF50` if passed, red `#E63946` if failed. |
| 8 | Typing [[12d6]] in a trait description shows 42 [[12d6]] in the live preview (PARSE-08) | VERIFIED | `_render_double_bracket()` module-level function in monster_detail.py line 501 with `_DOUBLE_BRACKET_RE = re.compile(r'\[\[(\d+)d(\d+)\]\]')`. Computes `avg = (n * (s + 1)) // 2`. Applied to trait descriptions in `_add_trait_row()` (line 420), action raw_text in `_add_action_row()` (line 486), and extra effect text (line 472). Live test: `[[12d6]]` → `42 [[12d6]]`, `[[4d6]]` → `14 [[4d6]]`, `[[12d8]]` → `54 [[12d8]]`. |
| 9 | Monster speed is visible in both the library detail panel and the editor preview (PARSE-09) | VERIFIED | `_speed_row_widget` built in monster_detail.py lines 154-163. `show_monster()` at line 288 sets `_speed_label_val.setText(speed)` and `setVisible(True)` when speed non-empty. Editor `_speed_edit` QLineEdit in Core Stats (line 429-433), `_on_speed_changed()` at line 2045 updates `_working_copy.speed` and calls `_rebuild_preview()`. Editor preview uses same `MonsterDetailPanel.show_monster()`. |
| 10 | CR, HP, and Skills sections are compacted alongside the ability scores in the editor (PARSE-10) | VERIFIED | `_build_core_stats_section()` at monster_editor.py line 366 merges: ability scores grid, CR/HP/Speed compact row, inline skills (with Add Skill), all wrapped in `CollapsibleSection("Core Stats", content, expanded=True)`. Old separate section builders removed. |
| 11 | Equipment section is at the bottom of the editor, right above Buffs (PARSE-11) | VERIFIED | Section order in `_setup_ui()` lines 307-312: `_build_core_stats_section()`, `_build_saving_throws_section()`, `_build_traits_section()`, `_build_actions_section()`, `_build_equipment_section()`, `_build_buffs_section()`. Equipment is second-to-last, Buffs is last. |

**Score: 11/11 truths verified**

---

### Required Artifacts

| Artifact | Provides | Status | Evidence |
|----------|----------|--------|----------|
| `src/domain/models.py` | DetectedDie, Trait dataclasses; Monster.traits, Monster.speed; Action.after_text | VERIFIED | Lines 44-78: DetectedDie and Trait dataclasses with all specified fields. Monster.traits (line 100) with default_factory. Monster.speed (line 101) default "". Action.after_text (line 78) default "". |
| `src/parser/formats/_shared_patterns.py` | SPEED_RE, DICE_IN_TRAIT_RE, RECHARGE_RE, detect_dice_in_text(), detect_recharge(), extract_speed() | VERIFIED | Lines 64, 67, 73: all three regex patterns. Lines 135, 154, 168: all three helper functions. Imports DetectedDie and Trait from models (line 10). |
| `src/parser/formats/fivetools.py` | _extract_traits(), _extract_speed(); after_text; traits/speed wired into Monster constructor | VERIFIED | Lines 328-378: `_extract_traits()` and `_extract_speed()`. `parse_fivetools()` at lines 496-517 calls both and passes `traits=traits, speed=speed` to Monster constructor. `_parse_action()` sets `after_text = joined[hit_m.end():].strip()` at line 239. |
| `src/parser/formats/homebrewery.py` | _extract_traits(), _extract_speed(); after_text; traits/speed wired into Monster constructor | VERIFIED | Lines 295-341: `_extract_traits()` and `_extract_speed()`. `parse_homebrewery()` at lines 387-407 wires both. `_parse_action()` sets `after_text` (line 222 for standard, `after_text=""` for compact at line 195). |
| `src/parser/formats/plain.py` | _extract_traits(), _extract_speed(); after_text; traits/speed wired into Monster constructor | VERIFIED | Lines 218-264: `_extract_traits()` and `_extract_speed()`. `parse_plain()` at lines 310-329 wires both to Monster constructor. `_parse_action()` sets `after_text` at line 143. |
| `src/ui/monster_editor.py` | _build_core_stats_section(), _build_traits_section(), TraitEditDialog, action column headers, after-text toggle, section reorder | VERIFIED | All six elements present and wired. TraitEditDialog at line 2610. Section order verified at lines 307-312. |
| `src/ui/attack_roller_tab.py` | Trait button row, _make_trait_row(), _on_roll_trait(), _format_trait_output(), recharge support, after-text on hits | VERIFIED | Lines 361-495. All methods present and wired. Trait import at line 29. `roll_expression` imported at line 28. |
| `src/ui/monster_detail.py` | Speed row widget, traits section, _render_double_bracket(), speed/traits consumed | VERIFIED | Speed row at lines 154-163. Traits header/container at lines 210-223. `_render_double_bracket()` at line 501. `show_monster()` uses both `monster.speed` (line 288) and `monster.traits` (line 335). |

---

### Key Link Verification

| From | To | Via | Status | Evidence |
|------|----|----|--------|----------|
| `fivetools.py` | `models.py` | `from src.domain.models import Action, DamagePart, Monster, Trait` | WIRED | Line 15: Trait imported and used in `_extract_traits()` return type and `Monster(traits=...)` constructor |
| `homebrewery.py` | `models.py` | `from src.domain.models import ... Trait` | WIRED | Line 19: Trait imported; used in `_extract_traits()` and Monster constructor |
| `plain.py` | `models.py` | `from src.domain.models import ... Trait` | WIRED | Line 13: Trait imported; used in `_extract_traits()` and Monster constructor |
| `_shared_patterns.py` | fivetools/homebrewery/plain parsers | SPEED_RE, DICE_IN_TRAIT_RE, RECHARGE_RE imported | WIRED | Each parser imports `detect_dice_in_text`, `detect_recharge`, `extract_speed as _shared_extract_speed` from `_shared_patterns` |
| `monster_editor.py` | `models.py` | Trait import for trait list management | WIRED | Line 68: `Trait` in import list; used in `_trait_items: list[Trait]` (line 594) and `TraitEditDialog` |
| `monster_editor.py (_build_traits_section)` | `monster_editor.py (_rebuild_preview)` | Trait edit modal triggers preview rebuild | WIRED | `_rebuild_preview()` called in `_on_edit_trait()` at line 1216 and `_on_add_trait()` at line 1226 after dialog accept |
| `attack_roller_tab.py` | `models.py` | Trait import for trait button generation | WIRED | Line 29: `from src.domain.models import Trait` |
| `attack_roller_tab.py (trait roll)` | `attack_roller_tab.py (output panel)` | `_on_roll_trait()` → `_format_trait_output()` → `_output_panel.append_html()` | WIRED | Lines 444-461: full chain verified; `roll_expression` at line 449 executes dice, line 461 appends HTML |
| `monster_detail.py` | `models.py` | `monster.speed` and `monster.traits` consumed for display | WIRED | Lines 288-343: `getattr(monster, 'speed', '')` and `getattr(monster, 'traits', [])` both read and rendered |

---

### Requirements Coverage

| Requirement | Plans Claiming | Status | Evidence |
|-------------|----------------|--------|----------|
| PARSE-01 | 15-01, 15-02 | SATISFIED | Trait dataclass + Monster.traits in models.py; _extract_traits() in all 3 parsers; Traits CollapsibleSection in editor |
| PARSE-02 | 15-02 | SATISFIED | `_build_traits_section()` with compact list, `TraitEditDialog` modal with editable name and description, Add/Remove buttons |
| PARSE-03 | 15-01, 15-02 | SATISFIED | `Action.after_text` in models.py; all 3 parsers extract it; editor has per-action "..." toggle revealing QTextEdit |
| PARSE-04 | 15-02 | SATISFIED | Column header row with bold labels "Name", "To-Hit", "Dmg Dice", "Bonus", "Dmg Type" at monster_editor.py line 1516 |
| PARSE-05 | 15-01 | SATISFIED | `DICE_IN_TRAIT_RE` + `detect_dice_in_text()` in _shared_patterns.py; `Trait.rollable_dice` field populated by parsers |
| PARSE-06 | 15-03 | SATISFIED | `_make_trait_row()` + `_on_roll_trait()` + `_format_trait_output()` in attack_roller_tab.py; "Traits" divider label; dice substitution with damage-type coloring |
| PARSE-07 | 15-01, 15-03 | SATISFIED | `RECHARGE_RE` + `detect_recharge()` in _shared_patterns.py; `Trait.recharge_range` tuple; `_on_roll_trait()` rolls 1d6 with green/red pass/fail coloring |
| PARSE-08 | 15-03 | SATISFIED | `_render_double_bracket()` in monster_detail.py; applied to trait descriptions, action raw_text, extra effect text; `[[12d6]]` → `42 [[12d6]]` verified in live test |
| PARSE-09 | 15-01, 15-03 | SATISFIED | `Monster.speed` field with SPEED_RE extraction in all 3 parsers; speed row widget in MonsterDetailPanel; `_speed_edit` in editor Core Stats wired to `_working_copy.speed` and preview |
| PARSE-10 | 15-02 | SATISFIED | `_build_core_stats_section()` merges ability scores, CR, HP, Speed, Skills into one `CollapsibleSection("Core Stats")` |
| PARSE-11 | 15-02 | SATISFIED | Section order in _setup_ui(): Core Stats > Saving Throws > Traits > Actions > Equipment > Buffs — Equipment is second-to-last, directly above Buffs |

**All 11 requirements (PARSE-01 through PARSE-11) are SATISFIED. No orphaned requirements.**

---

### Anti-Patterns Found

No blockers or stubs detected. The placeholder text found in the codebase (`setPlaceholderText(...)`) is all legitimate Qt widget hint text, not implementation stubs. No `TODO`, `FIXME`, `return null`, or empty handler patterns found in any Phase 15 modified file.

---

### Test Suite

**510 tests pass with zero regressions.** Verified by running `python -m pytest` on 2026-02-28.

---

### Human Verification Required

The following items can only be confirmed by running the application, as they involve visual layout, real-time interaction, and UI widget behavior:

#### 1. Trait Edit Modal Interaction

**Test:** Import a monster with traits (e.g. Adult Black Dragon from bestiary.md). Open the editor. Expand the Traits section. Click "Edit" on "Amphibious". Modify the description text. Click OK.
**Expected:** The trait description updates, the traits list rebuilds, the live preview reflects the changed description.
**Why human:** Modal dialog interaction and live preview update cannot be verified by static analysis.

#### 2. After-Attack-Text Toggle and Editing

**Test:** Open the editor on a monster with complex attack actions. Expand the Actions section. Click the "..." toggle button on any action.
**Expected:** A multiline text area expands below the action row showing `action.after_text`. Editing the text updates the live preview.
**Why human:** QTextEdit visibility toggle behavior and real-time preview sync require runtime confirmation.

#### 3. Attack Roller Trait Buttons with Recharge

**Test:** Import Adult Black Dragon. Open the Attack Roller tab. Select the dragon.
**Expected:** Below standard attack buttons (Bite, Claw, Tail), a "Traits" italic divider appears, then "Acid Breath (Recharge 5-6)" with a Roll button. Clicking Roll shows colored output with 1d6 recharge result in green or red.
**Why human:** Tab rendering and dice roll output with coloring require visual confirmation.

#### 4. [[XdY]] Live Preview Rendering

**Test:** Open the editor. Click "Add Trait". In the description field, type `The breath deals [[12d8]] acid damage.`. Click OK.
**Expected:** The editor live preview (right panel) shows `The breath deals 54 [[12d8]] acid damage.`
**Why human:** Live preview rendering requires the editor to be running.

#### 5. Speed Display in Library Panel

**Test:** Import a statblock containing a `**Speed** 40 ft., fly 80 ft.` line. Select the monster in the Library tab.
**Expected:** The detail panel (right side) shows a "Speed" row below HP with value "40 ft., fly 80 ft."
**Why human:** Library panel rendering requires the application running with imported data.

---

## Summary

Phase 15 fully achieves its goal. All 11 PARSE requirements are satisfied with substantive, wired implementations across the domain model (models.py), three format parsers (fivetools, homebrewery, plain), the monster editor (monster_editor.py), the attack roller (attack_roller_tab.py), and the detail panel (monster_detail.py). The parser correctly separates traits from actions, the editor presents them in a structured layout, the attack roller makes traits rollable with damage-type coloring and recharge support, and the detail panel renders speed and [[XdY]] notation across all display paths. 510 tests pass with zero regressions.

---

_Verified: 2026-02-28_
_Verifier: Claude (gsd-verifier)_
