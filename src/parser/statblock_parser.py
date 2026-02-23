"""Multi-format statblock dispatcher.

Detects the format of a Markdown statblock file and routes to the
appropriate format-specific parser. Also provides ImportResult for
accumulating per-file statistics.

Public API:
    detect_format(content: str) -> str
    parse_file(path: Path) -> ParseResult
    ImportResult is imported from src.parser.models
"""
from __future__ import annotations
import re
from pathlib import Path

from src.parser.models import ParseResult, ParseFailure, ImportResult
from src.parser.formats.fivetools import parse_fivetools
from src.parser.formats.homebrewery import parse_homebrewery
from src.parser.formats.plain import parse_plain


# ---------------------------------------------------------------------------
# Format detection
# ---------------------------------------------------------------------------

def detect_format(content: str) -> str:
    """Detect the statblock format of the given content string.

    Detection is mutually exclusive, in priority order:
      1. fivetools  — content has '>- **Armor Class**' line (blockquote prefix)
      2. homebrewery — content has ___ line AND **Armor Class** (no > prefix)
      3. plain      — content has '## ' heading AND **Armor Class** (no > prefix)
      4. unknown    — none of the above matched

    Args:
        content: Raw string content of a Markdown file.

    Returns:
        One of: 'fivetools', 'homebrewery', 'plain', 'unknown'
    """
    if not content:
        return 'unknown'

    # Priority 1: 5etools blockquote format
    # Requires a '>-' or '> -' line with **Armor Class**
    if re.search(r'^>[-\s]+\*\*Armor Class\*\*', content, re.MULTILINE):
        return 'fivetools'

    # Priority 2: Homebrewery/GM Binder ___ delimiter format
    # Requires both a bare ___ line AND **Armor Class** without > prefix
    if re.search(r'^___\s*$', content, re.MULTILINE) and '**Armor Class**' in content:
        return 'homebrewery'

    # Priority 3: Plain Markdown ## heading format
    # Requires both a ## heading AND **Armor Class** bullet
    if (re.search(r'^##\s+\w', content, re.MULTILINE)
            and re.search(r'\*\*Armor Class\*\*', content)):
        return 'plain'

    return 'unknown'


# ---------------------------------------------------------------------------
# File reader + dispatcher
# ---------------------------------------------------------------------------

def parse_file(path: Path) -> ParseResult:
    """Read a Markdown file, detect its format, and parse it.

    On file read error (OSError, UnicodeDecodeError): returns a ParseResult
    with one ParseFailure (file-level) and no monsters.

    On unrecognized format: returns ParseResult with empty monsters list and
    a warning string.

    On known format: returns the ParseResult from the format-specific parser
    as-is (failures from the sub-parser are preserved).

    Args:
        path: Path object pointing to the Markdown file.

    Returns:
        ParseResult — never raises.
    """
    try:
        content = path.read_text(encoding='utf-8')
    except (OSError, UnicodeDecodeError) as e:
        return ParseResult(
            monsters=[],
            failures=[ParseFailure(
                source_file=str(path),
                monster_name="",
                reason=str(e),
            )],
            warnings=[],
        )

    fmt = detect_format(content)

    if fmt == 'fivetools':
        return parse_fivetools(content)
    if fmt == 'homebrewery':
        return parse_homebrewery(content)
    if fmt == 'plain':
        return parse_plain(content)

    # Unknown format — return empty result with a warning
    return ParseResult(
        monsters=[],
        failures=[],
        warnings=[f"Unrecognized format in {path.name}: skipped"],
    )
