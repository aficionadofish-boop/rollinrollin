"""Shared regex constants and helper functions for all format parsers.

Imported by fivetools.py, homebrewery.py, and plain.py to keep regex
maintenance in one place.
"""
from __future__ import annotations
import re
from typing import Optional

from src.domain.models import DetectedDie, Trait


# ---------------------------------------------------------------------------
# Compiled regex constants — shared across all format parsers
# ---------------------------------------------------------------------------

# Creature type from italic subheading: "*Medium Monstrosity, Lawful Evil*"
TYPE_RE = re.compile(r'^\*(\w[^,*]+),\s*([^*]+)\*\s*$')

# Required stat fields
AC_RE = re.compile(r'\*\*Armor Class\*\*\s+(\d+)')
HP_RE = re.compile(r'\*\*Hit Points\*\*\s+(\d+)')
CR_RE = re.compile(r'\*\*Challenge\*\*\s+([\d/]+)')

# Saving throws line: "**Saving Throws** Dex +5, Con +6, Wis +4, Cha +5"
SAVES_RE = re.compile(r'\*\*Saving Throws\*\*\s+(.+)')
SAVE_BONUS_RE = re.compile(r'(Str|Dex|Con|Int|Wis|Cha)\s*([+-]\d+)', re.IGNORECASE)

# Ability score table cell: "|10 (+0)|" or "|15 (+2)|"
ABILITY_CELL_RE = re.compile(r'\|(\d+)\s*\([+-]\d+\)')
ABILITIES = ['STR', 'DEX', 'CON', 'INT', 'WIS', 'CHA']

# Action section headings within a statblock
ACTION_SECTION_RE = re.compile(
    r'^#{1,3}\s+(Actions|Legendary Actions|Reactions|Bonus Actions|Traits)',
    re.IGNORECASE | re.MULTILINE
)

# Section boundary regex — matches all recognized section headers.
# Used to find the end of a named section (stop at next section header).
# Covers '#'-style headers (any level), bold-text format, and horizontal rules.
SECTION_BOUNDARY_RE = re.compile(
    r'(?:^#{1,6}\s+(?:Actions|Reactions|Legendary Actions|Lair Actions|Bonus Actions|Traits)\s*$'
    r'|^\*{2,3}(?:Actions|Reactions|Legendary Actions|Lair Actions|Bonus Actions|Traits)\*{2,3}\s*$'
    r'|^#{4,6}\s+\S)',   # any ####+ header signals end of current section
    re.IGNORECASE | re.MULTILINE
)

# Action name: "***Snake Hair.***" or "**Snake Hair.**"
ACTION_NAME_RE = re.compile(r'^\*{2,3}([^*]+?)\.\*{2,3}')

# Attack to-hit bonus: "+5 to hit" or "-1 to hit"
TO_HIT_RE = re.compile(r'([+-]\d+)\s+to\s+hit', re.IGNORECASE)

# Hit damage with optional second "plus" component:
# "Hit: 4 (1d4 + 2) piercing damage plus 14 (4d6) poison damage"
HIT_LINE_RE = re.compile(
    r'\*?Hit:\*?\s+'
    r'(\d+)\s*\(([^)]+)\)\s+(\w+)\s+damage'
    r'(?:\s+plus\s+\d+\s*\(([^)]+)\)\s+(\w+)\s+damage)?',
    re.IGNORECASE
)

# Speed line: "**Speed** 30 ft., fly 60 ft."
SPEED_RE = re.compile(r'\*\*Speed\*\*\s+(.+)', re.IGNORECASE)

# Dice formula in trait text: "54 (12d8) acid damage" — captures average, dice expr, damage type
DICE_IN_TRAIT_RE = re.compile(
    r'(\d+)\s*\((\d+d\d+(?:[+-]\d+)?)\)\s+(\w+)\s+damage',
    re.IGNORECASE
)

# Recharge pattern in trait names: "(Recharge 5-6)" or "(Recharge 6)"
RECHARGE_RE = re.compile(
    r'\(Recharge\s+(\d+)(?:\s*[-\u2013]\s*(\d+))?\)',
    re.IGNORECASE
)


# ---------------------------------------------------------------------------
# Shared helpers
# ---------------------------------------------------------------------------

def _cr_to_float(cr_str: str) -> float:
    """Convert CR string like '1/4', '1/2', '17' to float for comparison."""
    if '/' in cr_str:
        parts = cr_str.split('/')
        return int(parts[0]) / int(parts[1])
    try:
        return float(cr_str)
    except ValueError:
        return 0.0


def strip_blockquote(text: str) -> str:
    """Remove leading '>' from every blockquote line."""
    BLOCKQUOTE_PREFIX = re.compile(r'^>\s?', re.MULTILINE)
    lines = text.splitlines()
    stripped = [BLOCKQUOTE_PREFIX.sub('', line) for line in lines]
    return '\n'.join(stripped)


def extract_named_section(text: str, section_name: str) -> str:
    """Extract text belonging to a named section, stopping at the next section header.

    Supports both '#'-style headers (e.g. '### Actions') and bold-text format
    (e.g. '***Actions***' or '**Actions**').

    Args:
        text: Full statblock text (with blockquote prefix already stripped).
        section_name: Name of the section to extract, e.g. 'Actions',
                      'Legendary Actions', 'Lair Actions'.

    Returns:
        The text between the section header and the next section header (or
        end of text). Returns empty string if the section header is not found.
    """
    # Build a pattern matching both #-style and bold-style headers for the
    # specific section name.
    escaped = re.escape(section_name)
    section_start_re = re.compile(
        r'(?:^#{1,3}\s+' + escaped + r'\s*$'
        r'|^\*{2,3}' + escaped + r'\*{2,3}\s*$)',
        re.IGNORECASE | re.MULTILINE
    )
    m = section_start_re.search(text)
    if not m:
        return ""
    start = m.end()
    # Find the next section boundary after the start
    next_m = SECTION_BOUNDARY_RE.search(text, start)
    end = next_m.start() if next_m else len(text)
    return text[start:end]


def detect_dice_in_text(text: str) -> list[DetectedDie]:
    """Scan text for dice formula patterns like '54 (12d8) acid damage'.

    Returns a list of DetectedDie instances for every match found.
    """
    results: list[DetectedDie] = []
    for m in DICE_IN_TRAIT_RE.finditer(text):
        average_str = m.group(1)
        dice_expr = m.group(2)
        damage_type = m.group(3).lower()
        results.append(DetectedDie(
            full_match=m.group(0),
            dice_expr=dice_expr,
            damage_type=damage_type,
            average=int(average_str),
        ))
    return results


def detect_recharge(name: str) -> Optional[tuple[int, int]]:
    """Detect a recharge range from a trait name like 'Acid Breath (Recharge 5-6)'.

    Returns (min, max) tuple — e.g. (5, 6) for "Recharge 5-6" or (6, 6) for "Recharge 6".
    Returns None if no recharge pattern is found.
    """
    m = RECHARGE_RE.search(name)
    if not m:
        return None
    lo = int(m.group(1))
    hi = int(m.group(2)) if m.group(2) is not None else lo
    return (lo, hi)


def extract_speed(text: str) -> str:
    """Extract the speed value from a **Speed** line.

    Returns the speed text (e.g. "30 ft., fly 60 ft.") or "" if not found.
    """
    m = SPEED_RE.search(text)
    if not m:
        return ""
    # Strip trailing asterisks or markup that might appear at end of line
    return m.group(1).strip()


def extract_all_sections(text: str) -> dict[str, str]:
    """Split statblock text into named sections.

    Splits the text at all recognized section headers and returns a dict
    mapping section name (lowercase) to section body text.

    The text before the first section header is stored under the key
    'preamble' (contains traits and stats).

    Args:
        text: Full statblock text (blockquote prefix already stripped).

    Returns:
        Dict mapping section name (lowercase) to section body text.
        Keys include 'preamble' for text before first section header.
    """
    sections: dict[str, str] = {}
    all_boundaries = list(SECTION_BOUNDARY_RE.finditer(text))

    if not all_boundaries:
        sections['preamble'] = text
        return sections

    # Text before first section header
    sections['preamble'] = text[:all_boundaries[0].start()]

    for i, m in enumerate(all_boundaries):
        # Extract the section name from the matched header
        header_text = m.group(0).strip()
        # Strip leading '#' chars and surrounding '*' chars and whitespace
        section_name = re.sub(r'^[#*]+\s*|\s*[*]+$', '', header_text).strip().lower()
        # Section body: from end of this header to start of next header
        body_start = m.end()
        body_end = all_boundaries[i + 1].start() if i + 1 < len(all_boundaries) else len(text)
        sections[section_name] = text[body_start:body_end]

    return sections
