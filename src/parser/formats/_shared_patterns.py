"""Shared regex constants and helper functions for all format parsers.

Imported by fivetools.py, homebrewery.py, and plain.py to keep regex
maintenance in one place.
"""
from __future__ import annotations
import re
from typing import Optional


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
