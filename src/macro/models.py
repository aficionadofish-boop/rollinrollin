"""
Domain models for the macro sandbox layer.

MacroWarning  — an unsupported token that was stripped with a human-readable reason.
MacroLineResult — result of processing one non-empty line of macro text.
MacroRollResult — container for all per-line results from a multi-line macro.

No Qt dependencies. Pure Python + stdlib only.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional

# DiceResult imported here for type-hint only; the actual object is produced
# by src.engine.parser.roll_expression at runtime.
from src.engine.models import DiceResult


@dataclass
class MacroWarning:
    """An unsupported Roll20 token that was stripped with a human-readable reason."""

    token: str   # The matched token text, e.g. "@{target|ac}"
    reason: str  # Human-readable explanation, e.g. "Attribute reference removed..."


@dataclass
class MacroLineResult:
    """Result of evaluating one non-empty line of macro input."""

    line_number: int
    dice_result: Optional[DiceResult]  # None when error is set or template-only
    inline_results: list               # list of (original_expr_str, DiceResult) tuples
    warnings: list[MacroWarning]
    error: Optional[str]               # ParseError message; None on success
    template_name: Optional[str] = None  # Name from {{name=...}} if present

    @property
    def has_result(self) -> bool:
        """True if the line produced a valid DiceResult."""
        return self.dice_result is not None

    @property
    def has_inline_only(self) -> bool:
        """True if template-only result: no dice_result, no error, but has inline rolls."""
        return self.dice_result is None and self.error is None and bool(self.inline_results)

    @property
    def has_warnings(self) -> bool:
        """True if any unsupported tokens were encountered."""
        return bool(self.warnings)


@dataclass
class MacroRollResult:
    """Container for all per-line results from executing a multi-line macro."""

    line_results: list[MacroLineResult]
