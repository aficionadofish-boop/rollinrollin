"""Plain Markdown format statblock parser.

Parses the plain Markdown format: ## Monster Name headings with bullet-line
field labels (- **Armor Class** N) and no blockquote '>' prefix.

Public API:
    parse_plain(content: str) -> ParseResult
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
)


# ---------------------------------------------------------------------------
# Segmentation: split on ## headings
# ---------------------------------------------------------------------------

def _segment_monsters(content: str) -> list[str]:
    """Split content into segments, one per ## heading.

    Uses re.split on lines that start with '## ' (two hashes + space).
    Returns segments that begin with '## Name'.
    """
    # Split on ## headings (keep the delimiter by using lookahead)
    segments = re.split(r'(?m)(?=^## )', content)
    # Keep only non-empty segments that start with ## heading
    return [s.strip() for s in segments if s.strip() and re.match(r'^## ', s.strip())]


# ---------------------------------------------------------------------------
# Field extractors
# ---------------------------------------------------------------------------

def _extract_name(segment: str) -> str:
    """Extract name from the first '## Name' line."""
    m = re.match(r'^## (.+)$', segment, re.MULTILINE)
    if m:
        return m.group(1).strip()
    return ""


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
# Action extraction (same logic as fivetools/homebrewery)
# ---------------------------------------------------------------------------

def _parse_action(action_text: str) -> Optional[Action]:
    """Parse a single action block. Returns None if name cannot be extracted."""
    joined = ' '.join(line.strip() for line in action_text.splitlines() if line.strip())

    first_line = action_text.strip().splitlines()[0].strip() if action_text.strip() else ""
    name_m = ACTION_NAME_RE.match(first_line) or ACTION_NAME_RE.match(joined)
    if not name_m:
        return None
    name = name_m.group(1).strip()

    to_hit_m = TO_HIT_RE.search(joined)
    to_hit_bonus: Optional[int] = int(to_hit_m.group(1)) if to_hit_m else None

    damage_parts: list[DamagePart] = []
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
    """Extract all actions from a monster segment's text."""
    blocks = _split_action_blocks(text)
    actions: list[Action] = []
    for block in blocks:
        action = _parse_action(block)
        if action is not None:
            actions.append(action)
    return actions


# ---------------------------------------------------------------------------
# Main entry point
# ---------------------------------------------------------------------------

def parse_plain(content: str) -> ParseResult:
    """Parse a plain Markdown statblock string.

    Each '## Name' heading section produces one Monster.
    Missing required fields (AC, HP, CR) set incomplete=True with sentinel
    defaults (ac=0, hp=0, cr='?').
    Actions without a parseable attack are stored with raw_text only and
    is_parsed=False.

    Args:
        content: Raw string content of a plain Markdown file.

    Returns:
        ParseResult with monsters list. Never raises on malformed input.
    """
    if not content or not content.strip():
        return ParseResult(monsters=[], failures=[], warnings=[])

    segments = _segment_monsters(content)
    if not segments:
        return ParseResult(monsters=[], failures=[], warnings=[])

    monsters: list[Monster] = []
    for segment in segments:
        name = _extract_name(segment)
        if not name:
            continue

        ac = _extract_ac(segment)
        hp = _extract_hp(segment)
        cr = _extract_cr(segment)
        incomplete = any(v is None for v in [ac, hp, cr])

        creature_type = _extract_type(segment)
        ability_scores = _extract_ability_scores(segment)
        saves = _extract_saves(segment)
        actions = _extract_actions(segment)

        monster = Monster(
            name=name,
            ac=ac if ac is not None else 0,
            hp=hp if hp is not None else 0,
            cr=cr if cr is not None else "?",
            actions=actions,
            saves=saves,
            creature_type=creature_type,
            ability_scores=ability_scores,
            lore="",
            raw_text=segment,
            incomplete=incomplete,
        )
        monsters.append(monster)

    return ParseResult(monsters=monsters, failures=[], warnings=[])
