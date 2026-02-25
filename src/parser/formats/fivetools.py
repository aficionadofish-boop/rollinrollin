"""5etools blockquote statblock parser.

Parses the blockquote-wrapped format used in bestiary(1).md and similar
5etools-exported Markdown files. Each statblock begins with a '>## Name'
heading and ends when a non-blockquote line is encountered or a new '>##'
heading starts.

Public API:
    parse_fivetools(content: str) -> ParseResult
"""
from __future__ import annotations
import re
from typing import Optional

from src.domain.models import Action, DamagePart, Monster
from src.parser.models import ParseResult


# ---------------------------------------------------------------------------
# Compiled regex constants — module level for performance
# ---------------------------------------------------------------------------

# Strip leading '>' from blockquote lines
BLOCKQUOTE_PREFIX = re.compile(r'^>\s?', re.MULTILINE)

# Detect start of a blockquote statblock heading: ">## Name" or ">### Name"
BLOCK_START_RE = re.compile(r'^>#{1,2}\s+(.+)$', re.MULTILINE)

# Creature type from italic subheading: "*Medium Monstrosity, Lawful Evil*"
# Capture the size+type portion (before comma) and alignment (after comma)
TYPE_RE = re.compile(r'^\*(\w[^,*]+),\s*([^*]+)\*$')

# Required fields
AC_RE = re.compile(r'\*\*Armor Class\*\*\s+(\d+)')
HP_RE = re.compile(r'\*\*Hit Points\*\*\s+(\d+)')
CR_RE = re.compile(r'\*\*Challenge\*\*\s+([\d/]+)')

# Saving throws line: "**Saving Throws** Dex +5, Con +6, Wis +4, Cha +5"
SAVES_RE = re.compile(r'\*\*Saving Throws\*\*\s+(.+)')
SAVE_BONUS_RE = re.compile(r'(Str|Dex|Con|Int|Wis|Cha)\s*([+-]\d+)', re.IGNORECASE)

# Skills line: "**Skills** Perception +5, Stealth +4"
SKILLS_RE = re.compile(r'\*\*Skills\*\*\s+(.+)')
SKILL_ENTRY_RE = re.compile(r'([A-Za-z ]+?)\s*([+-]\d+)')

# Valid D&D 5e size names for extraction from type/alignment line
_VALID_SIZES = {"Tiny", "Small", "Medium", "Large", "Huge", "Gargantuan"}

# Ability score table cell: "|10 (+0)|" or "|15 (+2)|"
ABILITY_CELL_RE = re.compile(r'\|(\d+)\s*\([+-]\d+\)')
ABILITIES = ['STR', 'DEX', 'CON', 'INT', 'WIS', 'CHA']

# Action section headings within a statblock
ACTION_SECTION_RE = re.compile(
    r'^#{1,3}\s+(Actions|Legendary Actions|Reactions|Bonus Actions|Traits)',
    re.IGNORECASE | re.MULTILINE
)

# Action name: "***Snake Hair.***" → "Snake Hair"
# Also handles "**Snake Hair.**" (two asterisks)
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
# Helper: strip blockquote prefix
# ---------------------------------------------------------------------------

def _strip_blockquote(text: str) -> str:
    """Remove leading '>' from every blockquote line."""
    lines = text.splitlines()
    stripped = [BLOCKQUOTE_PREFIX.sub('', line) for line in lines]
    return '\n'.join(stripped)


# ---------------------------------------------------------------------------
# Field extractors — each returns Optional value; caller sets incomplete=True
# ---------------------------------------------------------------------------

def _extract_ac(clean_text: str) -> Optional[int]:
    m = AC_RE.search(clean_text)
    return int(m.group(1)) if m else None


def _extract_hp(clean_text: str) -> Optional[int]:
    m = HP_RE.search(clean_text)
    return int(m.group(1)) if m else None


def _extract_cr(clean_text: str) -> Optional[str]:
    m = CR_RE.search(clean_text)
    return m.group(1) if m else None


def _extract_type(clean_text: str) -> str:
    """Extract creature type from '*Size Type, Alignment*' italic line."""
    for line in clean_text.splitlines():
        line = line.strip()
        m = TYPE_RE.match(line)
        if m:
            # size_and_type is e.g. "Medium Monstrosity" — take the last word
            # (handles "Small Humanoid (Goblinoid)" → "Humanoid")
            size_and_type = m.group(1).strip()
            # Split on spaces, take the first non-size word
            # D&D sizes: Tiny, Small, Medium, Large, Huge, Gargantuan
            SIZES = {'Tiny', 'Small', 'Medium', 'Large', 'Huge', 'Gargantuan'}
            parts = size_and_type.split()
            for part in parts:
                clean_part = part.strip('()')
                if clean_part not in SIZES:
                    return clean_part
    return ""


def _extract_ability_scores(clean_text: str) -> dict[str, int]:
    """Extract 6 ability scores from pipe table row."""
    for line in clean_text.splitlines():
        matches = ABILITY_CELL_RE.findall(line)
        if len(matches) == 6:
            return {ab: int(v) for ab, v in zip(ABILITIES, matches)}
    return {}


def _extract_saves(clean_text: str) -> dict[str, int]:
    """Extract saving throw bonuses from **Saving Throws** line."""
    m = SAVES_RE.search(clean_text)
    if not m:
        return {}
    saves_text = m.group(1)
    return {
        ab.upper(): int(bonus)
        for ab, bonus in SAVE_BONUS_RE.findall(saves_text)
    }


def _extract_size(clean_text: str) -> str:
    """Extract monster size from the '*Size Type, Alignment*' italic line.

    The first word of that line is the size category. Returns "Medium" if
    no recognizable size can be found.
    """
    for line in clean_text.splitlines():
        line = line.strip()
        m = TYPE_RE.match(line)
        if m:
            size_and_type = m.group(1).strip()
            first_word = size_and_type.split()[0] if size_and_type.split() else ""
            if first_word in _VALID_SIZES:
                return first_word
    return "Medium"


def _extract_skills(clean_text: str) -> dict[str, int]:
    """Extract skill bonuses from '**Skills** Perception +5, Stealth +4' line."""
    m = SKILLS_RE.search(clean_text)
    if not m:
        return {}
    skills_text = m.group(1)
    result: dict[str, int] = {}
    # Split on commas then match each "Skill Name +N" pair
    for part in skills_text.split(","):
        part = part.strip()
        skill_m = SKILL_ENTRY_RE.match(part)
        if skill_m:
            skill_name = skill_m.group(1).strip().title()
            bonus = int(skill_m.group(2))
            result[skill_name] = bonus
    return result


# ---------------------------------------------------------------------------
# Action extraction
# ---------------------------------------------------------------------------

def _parse_action(action_text: str) -> Optional[Action]:
    """Parse a single action text block into an Action dataclass.

    Returns None if no name can be extracted.
    Handles *Hit:* on a second line by joining all non-blank lines.
    """
    # Join all lines into a single string for TO_HIT_RE / HIT_LINE_RE
    joined = ' '.join(line.strip() for line in action_text.splitlines() if line.strip())

    # Extract name from the first line (action text starts with "***Name.***")
    first_line = action_text.strip().splitlines()[0].strip() if action_text.strip() else ""
    name_m = ACTION_NAME_RE.match(first_line)
    if not name_m:
        # Try the joined version too
        name_m = ACTION_NAME_RE.match(joined)
    if not name_m:
        return None
    name = name_m.group(1).strip()

    # Extract to_hit_bonus
    to_hit_m = TO_HIT_RE.search(joined)
    to_hit_bonus: Optional[int] = int(to_hit_m.group(1)) if to_hit_m else None

    # Extract damage parts
    damage_parts: list[DamagePart] = []
    hit_m = HIT_LINE_RE.search(joined)
    if hit_m:
        # Primary damage component
        primary_dice = hit_m.group(2).replace(' ', '')  # "1d4+2"
        primary_type = hit_m.group(3).lower()            # "piercing"
        damage_parts.append(DamagePart(
            dice_expr=primary_dice,
            damage_type=primary_type,
            raw_text=hit_m.group(0),
        ))
        # Optional secondary "plus" component
        if hit_m.group(4) is not None:
            secondary_dice = hit_m.group(4).replace(' ', '')  # "4d6"
            secondary_type = hit_m.group(5).lower()            # "poison"
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


def _extract_actions(clean_text: str) -> list[Action]:
    """Extract all action entries from a statblock's clean text.

    Includes traits (before Actions heading) and all action sections.
    """
    actions: list[Action] = []

    # Find all action section boundaries
    section_matches = list(ACTION_SECTION_RE.finditer(clean_text))

    if not section_matches:
        # No action section headings — try the whole text for named entries
        action_text_block = clean_text
    else:
        # Text before first section heading = traits block
        # Include everything from first section to end
        action_text_block = clean_text[0:]

    # Split on "***Name.***" pattern to extract individual action blocks
    # Use a split that keeps the delimiter
    action_blocks = _split_action_blocks(action_text_block)

    for block in action_blocks:
        action = _parse_action(block)
        if action is not None:
            actions.append(action)

    return actions


def _split_action_blocks(text: str) -> list[str]:
    """Split statblock text into individual action text blocks.

    Each block starts with a '***Name.***' or '**Name.**' line.
    Returns list of raw action text strings.
    """
    # Find all action name positions
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


# ---------------------------------------------------------------------------
# Segmentation: split content into (name, block_text, lore_text) tuples
# ---------------------------------------------------------------------------

def _segment_blocks(content: str) -> list[tuple[str, str, str]]:
    """Find all >## statblock headings and extract block + following lore text.

    Returns list of (name, raw_block_text, lore_text) tuples.
    Each raw_block_text contains the raw '>'-prefixed lines.
    lore_text contains plain (non-blockquote) paragraphs immediately following.
    """
    lines = content.splitlines()
    segments: list[tuple[str, str, str]] = []

    # Find positions of all '>## Name' lines
    block_starts: list[tuple[int, str]] = []  # (line_index, name)
    for i, line in enumerate(lines):
        m = BLOCK_START_RE.match(line)
        if m:
            block_starts.append((i, m.group(1).strip()))

    if not block_starts:
        return []

    for seg_idx, (start_line, name) in enumerate(block_starts):
        # Determine end of blockquote region for this block:
        # ends at the next block_start OR at first non-blockquote, non-blank line
        # after the current block ends
        next_block_start = block_starts[seg_idx + 1][0] if seg_idx + 1 < len(block_starts) else len(lines)

        # Collect blockquote lines for this block
        block_lines: list[str] = []
        block_end_line = start_line
        for i in range(start_line, next_block_start):
            line = lines[i]
            if line.startswith('>') or line.strip() == '' or line.strip() == '___':
                block_lines.append(line)
                if line.startswith('>'):
                    block_end_line = i
            elif i > start_line:
                # Non-blockquote non-blank line inside our range but before next block
                # This shouldn't happen if format is clean, but stop here
                break

        raw_block_text = '\n'.join(block_lines)

        # Collect lore text: plain (non-'>') paragraphs after the block ends
        lore_lines: list[str] = []
        lore_start = block_end_line + 1
        lore_end = next_block_start

        i = lore_start
        while i < lore_end:
            line = lines[i]
            if line.startswith('>') or line.strip() == '___':
                pass  # skip residual blockquote or dividers
            elif line.strip() == '':
                if lore_lines:  # paragraph break inside lore
                    lore_lines.append('')
            else:
                lore_lines.append(line)
            i += 1

        # Strip trailing blank lines from lore
        while lore_lines and lore_lines[-1] == '':
            lore_lines.pop()

        lore_text = '\n'.join(lore_lines)

        segments.append((name, raw_block_text, lore_text))

    return segments


# ---------------------------------------------------------------------------
# Main entry point
# ---------------------------------------------------------------------------

def parse_fivetools(content: str) -> ParseResult:
    """Parse a 5etools-format Markdown string and return a ParseResult.

    Each '>## Name' blockquote section produces one Monster.
    Missing required fields (AC, HP, CR) set incomplete=True with sentinel
    defaults (ac=0, hp=0, cr='?') rather than raising an exception.
    Actions without a parseable attack roll are stored with raw_text only.
    Plain paragraphs following each statblock are stored in Monster.lore.

    Args:
        content: Raw string content of a 5etools Markdown file.

    Returns:
        ParseResult with monsters list and (currently empty) failures list.
        Returns empty ParseResult for files with no '>##' headings.
    """
    segments = _segment_blocks(content)
    if not segments:
        return ParseResult(monsters=[], failures=[], warnings=[])

    monsters: list[Monster] = []

    for name, raw_block_text, lore_text in segments:
        clean = _strip_blockquote(raw_block_text)

        ac = _extract_ac(clean)
        hp = _extract_hp(clean)
        cr = _extract_cr(clean)
        incomplete = any(v is None for v in [ac, hp, cr])

        creature_type = _extract_type(clean)
        ability_scores = _extract_ability_scores(clean)
        saves = _extract_saves(clean)
        actions = _extract_actions(clean)
        size = _extract_size(clean)
        skills = _extract_skills(clean)

        monster = Monster(
            name=name,
            ac=ac if ac is not None else 0,
            hp=hp if hp is not None else 0,
            cr=cr if cr is not None else "?",
            actions=actions,
            saves=saves,
            creature_type=creature_type,
            ability_scores=ability_scores,
            lore=lore_text,
            raw_text=raw_block_text,
            incomplete=incomplete,
            size=size,
            skills=skills,
        )
        monsters.append(monster)

    return ParseResult(monsters=monsters, failures=[], warnings=[])
