---
phase: 14-bug-fixes-critical-polish
plan: 02
subsystem: ui
tags: [pyside6, monster-editor, spellcasting, skills, cascading]

# Dependency graph
requires:
  - phase: 09-monster-editor-and-equipment
    provides: MonsterEditorDialog, _sync_save_toggles, _apply_highlights, SKILL_TO_ABILITY
provides:
  - CR changes cascade proficiency to saves and skills in editor form and preview
  - Ability score changes cascade to all dependent skill bonuses in editor
  - User-added/modified skills display in amber modified-value color
  - Spellcasting focus bonus correctly annotates spell attack and DC in preview
affects: [phase-14, phase-15]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Skill cascade on ability change: detect tier via old modifier, recompute with new modifier"
    - "Prof cascade on CR change: read UI toggle state, recompute via _apply_skill_value"
    - "Focus display: build view-only annotated display copy, never mutate _working_copy"
    - "Skill color highlighting: direct HTML span injection into preview _skills_label from _apply_highlights()"

key-files:
  created: []
  modified:
    - src/ui/monster_editor.py

key-decisions:
  - "BUG-03: _on_cr_changed uses _sync_save_toggles(recompute_values=True) to cascade new prof bonus into saves; new _cascade_skills_on_prof_change() reads UI toggle state for skills"
  - "BUG-05: _cascade_skills_on_ability_change() detects skill tier from old ability mod (Non-Prof/Prof/Expertise) and recomputes with new mod; Custom tier is left unchanged"
  - "BUG-04: Skill coloring injected directly into _skills_label from _apply_highlights() — same pattern as save highlighting; no changes to monster_detail.py required"
  - "BUG-07: Focus bonus displayed via _build_focus_annotated_display_copy() — creates a copy with annotation appended to spellcasting action raw_text; _working_copy never mutated"

patterns-established:
  - "View-only display copies: when editor state needs to annotate display without persisting, build a copy in _rebuild_preview() rather than mutating _working_copy"
  - "Skill tier detection: compare value against old_mod, old_mod+prof, old_mod+2*prof to classify tier before cascading"

requirements-completed: [BUG-03, BUG-04, BUG-05, BUG-07]

# Metrics
duration: 25min
completed: 2026-02-26
---

# Phase 14 Plan 02: Monster Editor Cascade Bugs Summary

**Four editor cascade bugs fixed: CR cascade to prof-dependent form values, ability-to-skill cascade, modified-skill amber coloring, and spellcasting focus annotation in preview.**

## Performance

- **Duration:** 25 min
- **Started:** 2026-02-26T22:37:36Z
- **Completed:** 2026-02-26T23:02:00Z
- **Tasks:** 2
- **Files modified:** 1

## Accomplishments
- CR changes now cascade to saves AND skills in both the editor form and the preview (BUG-03)
- Ability score changes cascade to all dependent skill bonuses maintaining Prof/Expertise tiers (BUG-05)
- Skills that differ from base monster display in amber color in the preview panel (BUG-04)
- Spellcasting focus shows expected spell attack bonus and DC annotation in the preview (BUG-07)

## Task Commits

Each task was committed atomically:

1. **Task 1+2: Fix CR cascade, ability-to-skill cascade, skill color, spellcasting focus** - `9a05449` (fix)

## Files Created/Modified
- `src/ui/monster_editor.py` - Added _cascade_skills_on_prof_change(), _cascade_skills_on_ability_change(), _build_focus_annotated_display_copy(); updated _on_cr_changed, _on_ability_changed, _apply_highlights, _rebuild_preview

## Decisions Made
- BUG-03 CR cascade uses recompute_values=True in _sync_save_toggles so the new prof bonus is applied to whatever tier each save is currently toggled to. New _cascade_skills_on_prof_change() reads each skill row's UI toggle and calls _apply_skill_value() with the new prof.
- BUG-05 skill cascade determines tier using the OLD ability modifier snapshot before new values are applied, then recomputes. This correctly handles all three tiers. Custom skills are left unchanged.
- BUG-04 skill highlighting is implemented directly in _apply_highlights() using the same pattern as save highlighting (direct HTML span injection into preview panel's _skills_label). No changes to monster_detail.py needed.
- BUG-07 focus bonus uses a view-only display copy approach: _build_focus_annotated_display_copy() creates a copy with SpellcastingDetector + MathValidator to compute expected attack/DC with focus, then injects an annotation line into each spellcasting action's display text. _working_copy is never touched.

## Deviations from Plan

### Auto-fixed Issues

None - plan executed exactly as written, though the skill-color implementation did not require monster_detail.py changes as the existing _apply_highlights() pattern (injecting HTML directly into the preview label) was sufficient.

## Issues Encountered
None.

## User Setup Required
None - no external service configuration required.

## Next Phase Readiness
- All four editor cascade bugs resolved; editor now works as a coherent live-update system
- Plan 14-03 (parser section boundaries) can proceed independently

---
*Phase: 14-bug-fixes-critical-polish*
*Completed: 2026-02-26*
