"""ParseResult, ParseFailure, and ImportResult dataclasses for the statblock parser pipeline.

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


@dataclass
class ImportResult:
    """Per-file import statistics for the UI import log panel.

    Accumulates counts from a ParseResult so the UI can display
    how many monsters succeeded, how many were incomplete, and
    which specific monsters failed to parse.
    """
    filename: str                    # source filename (basename or full path)
    success_count: int               # number of monsters parsed (including incomplete)
    incomplete_count: int            # monsters with incomplete=True
    failures: list                   # list[ParseFailure] — monsters that could not be stored

    @classmethod
    def from_parse_result(cls, filename: str, result: ParseResult) -> "ImportResult":
        """Build an ImportResult from a ParseResult.

        success_count = len(result.monsters)  — all monsters that were produced
        incomplete_count = count of monsters where incomplete=True
        failures = result.failures
        """
        success_count = len(result.monsters)
        incomplete_count = sum(1 for m in result.monsters if getattr(m, 'incomplete', False))
        return cls(
            filename=filename,
            success_count=success_count,
            incomplete_count=incomplete_count,
            failures=list(result.failures),
        )
