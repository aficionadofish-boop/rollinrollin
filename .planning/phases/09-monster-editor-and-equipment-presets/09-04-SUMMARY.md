---
phase: 09-monster-editor-and-equipment-presets
plan: 04
subsystem: ui
tags: [equipment-presets, actions-editor, buffs, color-highlighting, pyside6]

# Dependency graph
requires:
  - phase: 09-03
    provides: "MonsterEditorDialog skeleton with collapsible sections and live preview"
  - phase: 09-02
    provides: "EquipmentService with compute_weapon_action, compute_armor_ac, compute_shield_bonus, compute_focus_bonus"
  - phase: 09-01
    provides: "EquipmentItem, BuffItem, SRD_WEAPONS, SRD_ARMORS, SIZE_DICE_MULTIPLIER"
---

## What was built

Extended MonsterEditorDialog from 902 to 1811 lines with three new collapsible sections and color highlighting on the preview panel.

### Equipment Section
- **Weapons**: Add from SRD list (33 weapons), select magic bonus (+0/+1/+2/+3), auto-generates action via EquipmentService.compute_weapon_action(). Conflict prompt: Replace or Add as New. Remove button deletes weapon and its generated action.
- **Armor**: Single armor slot from SRD list (12 armors), updates AC with correct DEX limits. Shows stealth disadvantage and STR requirement warnings.
- **Shield**: Single slot, adds 2 + magic_bonus to AC.
- **Focus**: Single slot (+1/+2/+3), updates spell attack and spell save DC.
- Collapsed header shows equipment summary (e.g. "Longsword +2, Plate Armor, Shield +1").

### Actions Section
- Structured editable rows for all monster actions: name, to-hit bonus, damage dice, damage bonus, damage type.
- "[auto]" badge on equipment-generated actions.
- Add Action button with sensible defaults. Remove button per row.

### Buffs Section
- Custom named bonuses: name, bonus value (e.g. "+1d4"), target (Attack Rolls / Saving Throws / Ability Checks / Damage / All).
- Add Buff / Remove per row.

### Three-Tier Color Highlighting
- **Steel blue (#4EA8DE)**: Equipment-modified values (AC after armor, actions from weapons)
- **Amber (#F4A261)**: Manually edited values (ability scores, HP, saves)
- **Red (#E63946)**: Custom overrides (saves that don't match proficiency math)
- Base value tooltips on modified labels in preview panel.

### Public Accessors for Plan 05
- `get_equipment_items()`, `get_buff_items()`, `get_focus_bonus()` exposed for persistence wiring.

## key-files

### created
(none — extended existing file)

### modified
- src/ui/monster_editor.py — +913 lines: Equipment, Actions, Buffs sections, color highlighting, modification source tracking

## deviations
None. Implementation follows plan specification.

## self-check
- [x] Equipment section with weapon/armor/shield/focus pickers
- [x] Auto-generated weapon actions with correct math
- [x] Action conflict prompts Replace or Add as New
- [x] Actions section with structured editable fields + Add/Remove
- [x] Buffs section with name + value + target + Add/Remove
- [x] Three-tier highlighting (equipment blue, manual amber, custom red)
- [x] Base value tooltips on modified labels
- [x] Equipment summary in collapsed section header
- [x] All 485 tests pass with zero regressions
