"""ParseResult and ParseFailure dataclasses for the statblock parser pipeline.

No Qt imports. No domain imports (avoids circular dependency).
ParseResult.monsters is list (not list[Monster]) — type documented here only.
"""
from __future__ import annotations
from dataclasses import dataclass, field


@dataclass
class ParseFailure:
    """Records a monster that could not be imported."""
    source_file: str          # path or filename of the source Markdown file
    monster_name: str         # name if extractable; "" if name could not be found
    reason: str               # human-readable description of the failure


@dataclass
class ParseResult:
    """Result of parsing one Markdown file.

    monsters: list[Monster] — successfully parsed Monster objects (may be incomplete)
    failures: list[ParseFailure] — blocks that could not produce a usable Monster
    warnings: list[str] — non-fatal issues (e.g. unrecognized format variant)
    """
    monsters: list                              # list[Monster]
    failures: list                              # list[ParseFailure]
    warnings: list[str] = field(default_factory=list)
