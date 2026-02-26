"""Homebrewery/GM Binder format statblock parser.

Parses the ___ delimiter format used in Homebrewery and GM Binder exports.
Each statblock is delimited by ___ lines. The ## heading within a block
gives the monster name.

Supports both compact Homebrewery attack syntax:
    *MWA*: **+4, 1d6+2** slashing
And standard Melee Weapon Attack syntax:
    *Melee Weapon Attack: +4 to hit* ... *Hit: 7 (1d6 + 2) slashing damage*

Public API:
    parse_homebrewery(content: str) -> ParseResult
"""
from __future__ import annotations
import re
from typing import Optional

from src.domain.models import Action, DamagePart, Monster
from src.parser.models import ParseResult
from src.parser.formats._shared_patterns import (
    AC_RE, HP_RE, CR_RE, TYPE_RE, SAVES_RE, SAVE_BONUS_RE,
    ABILITY_CELL_RE, ABILITIES,
    ACTION_SECTION_RE, ACTION_NAME_RE, TO_HIT_RE, HIT_LINE_RE,
    extract_named_section,
)


# ---------------------------------------------------------------------------
# Homebrewery-specific: compact attack regex
# ---------------------------------------------------------------------------

# Matches: *MWA*: **+4, 1d6+2** slashing
# Groups: (to_hit "+4", dice_expr "1d6+2", damage_type "slashing")
HB_COMPACT_RE = re.compile(
    r'\*(?:MWA|MRA|RWA|RRA)\*:\s*\*\*([+-]\d+),\s*([^*]+)\*\*\s+(\w+)',
    re.IGNORECASE
)


# ---------------------------------------------------------------------------
# Segmentation: split on ___ boundaries
# ---------------------------------------------------------------------------

def _segment_blocks(content: str) -> list[str]:
    """Split content on ___ delimiter lines into segments.

    Each segment may start with ## Name. Returns only non-empty segments
    that have a ## heading.
    """
    # Split on lines that are purely ___ (with optional whitespace)
    raw_segments = re.split(r'(?m)^___\s*$', content)
    segments: list[str] = []
    i = 0
    while i < len(raw_segments):
        seg = raw_segments[i].strip()
        # A monster block starts with ## Name
        if re.match(r'^##\s+\S', seg):
            segments.append(seg)
        i += 1
    return segments


def _merge_segments(content: str) -> list[str]:
    """Merge consecutive ___ segments that form a single monster block.

    In Homebrewery format a monster block is split across several ___ sections.
    We identify monster boundaries by ## headings and merge all the content
    between consecutive ## headings (inclusive).
    """
    # Split into raw ___ sections
    raw_sections = re.split(r'(?m)^___\s*$', content)

    # Group sections: when a new ## heading appears, start a new monster group
    monster_groups: list[list[str]] = []
    current_group: list[str] = []

    for section in raw_sections:
        stripped = section.strip()
        if not stripped:
            continue
        if re.match(r'^##\s+\S', stripped):
            # New monster starts here
            if current_group:
                monster_groups.append(current_group)
            current_group = [stripped]
        elif current_group:
            # Continuation of current monster (AC/HP, ability table, etc.)
            current_group.append(stripped)

    if current_group:
        monster_groups.append(current_group)

    # Merge each group into a single text block
    return ['\n'.join(group) for group in monster_groups]


# ---------------------------------------------------------------------------
# Field extractors
# ---------------------------------------------------------------------------

def _extract_name(block_text: str) -> str:
    """Extract monster name from first '## Name' line."""
    m = re.match(r'^##\s+(.+)$', block_text, re.MULTILINE)
    return m.group(1).strip() if m else ""


def _extract_ac(text: str) -> Optional[int]:
    m = AC_RE.search(text)
    return int(m.group(1)) if m else None


def _extract_hp(text: str) -> Optional[int]:
    m = HP_RE.search(text)
    return int(m.group(1)) if m else None


def _extract_cr(text: str) -> Optional[str]:
    m = CR_RE.search(text)
    return m.group(1) if m else None


def _extract_type(text: str) -> str:
    """Extract creature type from '*Size Type, Alignment*' italic line."""
    SIZES = {'Tiny', 'Small', 'Medium', 'Large', 'Huge', 'Gargantuan'}
    for line in text.splitlines():
        line = line.strip()
        m = TYPE_RE.match(line)
        if m:
            size_and_type = m.group(1).strip()
            parts = size_and_type.split()
            for part in parts:
                clean_part = part.strip('()')
                if clean_part not in SIZES:
                    return clean_part
    return ""


def _extract_ability_scores(text: str) -> dict[str, int]:
    """Extract 6 ability scores from pipe table row."""
    for line in text.splitlines():
        matches = ABILITY_CELL_RE.findall(line)
        if len(matches) == 6:
            return {ab: int(v) for ab, v in zip(ABILITIES, matches)}
    return {}


def _extract_saves(text: str) -> dict[str, int]:
    """Extract saving throw bonuses from **Saving Throws** line."""
    m = SAVES_RE.search(text)
    if not m:
        return {}
    return {
        ab.upper(): int(bonus)
        for ab, bonus in SAVE_BONUS_RE.findall(m.group(1))
    }


# ---------------------------------------------------------------------------
# Action extraction
# ---------------------------------------------------------------------------

def _parse_action(action_text: str) -> Optional[Action]:
    """Parse a single action block. Returns None if name cannot be extracted."""
    # Join lines for regex matching
    joined = ' '.join(line.strip() for line in action_text.splitlines() if line.strip())

    # Extract name
    first_line = action_text.strip().splitlines()[0].strip() if action_text.strip() else ""
    name_m = ACTION_NAME_RE.match(first_line) or ACTION_NAME_RE.match(joined)
    if not name_m:
        return None
    name = name_m.group(1).strip()

    # Try compact Homebrewery syntax first: *MWA*: **+4, 1d6+2** slashing
    compact_m = HB_COMPACT_RE.search(joined)
    if compact_m:
        to_hit_str = compact_m.group(1)  # e.g. "+4"
        to_hit_bonus: Optional[int] = int(to_hit_str.lstrip('+')) if to_hit_str[0] != '-' else int(to_hit_str)
        # Normalize: "+4" → 4, "-1" → -1
        to_hit_bonus = int(to_hit_str) if to_hit_str[0] == '-' else int(to_hit_str.lstrip('+'))
        dice_expr = compact_m.group(2).strip().replace(' ', '')  # e.g. "1d6+2"
        damage_type = compact_m.group(3).lower()                  # e.g. "slashing"
        damage_parts = [DamagePart(dice_expr=dice_expr, damage_type=damage_type, raw_text=joined)]
        return Action(
            name=name,
            to_hit_bonus=to_hit_bonus,
            damage_parts=damage_parts,
            raw_text=joined,
            is_parsed=True,
        )

    # Fall back to standard TO_HIT_RE / HIT_LINE_RE (same as fivetools)
    to_hit_m = TO_HIT_RE.search(joined)
    to_hit_bonus = int(to_hit_m.group(1)) if to_hit_m else None

    damage_parts = []
    hit_m = HIT_LINE_RE.search(joined)
    if hit_m:
        primary_dice = hit_m.group(2).replace(' ', '')
        primary_type = hit_m.group(3).lower()
        damage_parts.append(DamagePart(
            dice_expr=primary_dice,
            damage_type=primary_type,
            raw_text=hit_m.group(0),
        ))
        if hit_m.group(4) is not None:
            secondary_dice = hit_m.group(4).replace(' ', '')
            secondary_type = hit_m.group(5).lower()
            damage_parts.append(DamagePart(
                dice_expr=secondary_dice,
                damage_type=secondary_type,
                raw_text=hit_m.group(0),
            ))

    is_parsed = to_hit_bonus is not None and len(damage_parts) > 0

    return Action(
        name=name,
        to_hit_bonus=to_hit_bonus,
        damage_parts=damage_parts,
        raw_text=joined,
        is_parsed=is_parsed,
    )


def _split_action_blocks(text: str) -> list[str]:
    """Split statblock text into individual action text blocks."""
    pattern = re.compile(r'(?=^\*{2,3}[^*]+?\.\*{2,3})', re.MULTILINE)
    positions = [m.start() for m in pattern.finditer(text)]
    if not positions:
        return []
    blocks = []
    for i, pos in enumerate(positions):
        end = positions[i + 1] if i + 1 < len(positions) else len(text)
        block = text[pos:end].strip()
        if block:
            blocks.append(block)
    return blocks


def _extract_actions(text: str) -> list[Action]:
    """Extract all actions from a monster block's text.

    If an 'Actions' section header is found, only text within that section is
    parsed for regular actions (preventing text from Legendary Actions or Lair
    Actions from bleeding in). Falls back to parsing the whole text if no
    section headers are present.
    """
    actions_section = extract_named_section(text, "Actions")
    if actions_section:
        parse_text = actions_section
    else:
        parse_text = text

    blocks = _split_action_blocks(parse_text)
    actions: list[Action] = []
    for block in blocks:
        action = _parse_action(block)
        if action is not None:
            actions.append(action)
    return actions


def _extract_section_actions(text: str, section_name: str) -> list[Action]:
    """Extract actions from a named section (e.g. 'Legendary Actions', 'Lair Actions').

    Returns an empty list if the section is not found.
    """
    section_text = extract_named_section(text, section_name)
    if not section_text:
        return []
    blocks = _split_action_blocks(section_text)
    actions: list[Action] = []
    for block in blocks:
        action = _parse_action(block)
        if action is not None:
            actions.append(action)
    return actions


# ---------------------------------------------------------------------------
# Main entry point
# ---------------------------------------------------------------------------

def parse_homebrewery(content: str) -> ParseResult:
    """Parse a Homebrewery/GM Binder format Markdown string.

    Each ___ delimited section with a ## Name heading produces one Monster.
    Missing required fields (AC, HP, CR) set incomplete=True with sentinel
    defaults (ac=0, hp=0, cr='?').
    Actions without a parseable attack are stored with raw_text only and
    is_parsed=False.

    Args:
        content: Raw string content of a Homebrewery Markdown file.

    Returns:
        ParseResult with monsters list. Never raises on malformed input.
    """
    if not content or not content.strip():
        return ParseResult(monsters=[], failures=[], warnings=[])

    monster_blocks = _merge_segments(content)
    if not monster_blocks:
        return ParseResult(monsters=[], failures=[], warnings=[])

    monsters: list[Monster] = []
    for block_text in monster_blocks:
        name = _extract_name(block_text)
        if not name:
            continue  # skip blocks without a name

        ac = _extract_ac(block_text)
        hp = _extract_hp(block_text)
        cr = _extract_cr(block_text)
        incomplete = any(v is None for v in [ac, hp, cr])

        creature_type = _extract_type(block_text)
        ability_scores = _extract_ability_scores(block_text)
        saves = _extract_saves(block_text)
        actions = _extract_actions(block_text)
        legendary_actions = _extract_section_actions(block_text, "Legendary Actions")
        lair_actions = _extract_section_actions(block_text, "Lair Actions")

        monster = Monster(
            name=name,
            ac=ac if ac is not None else 0,
            hp=hp if hp is not None else 0,
            cr=cr if cr is not None else "?",
            actions=actions,
            legendary_actions=legendary_actions,
            lair_actions=lair_actions,
            saves=saves,
            creature_type=creature_type,
            ability_scores=ability_scores,
            lore="",
            raw_text=block_text,
            incomplete=incomplete,
        )
        monsters.append(monster)

    return ParseResult(monsters=monsters, failures=[], warnings=[])
