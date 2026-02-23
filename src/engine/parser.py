"""
Recursive descent parser for dice expressions.

Entry point:
    roll_expression(expr: str, roller: Roller, seed: Optional[int] = None) -> DiceResult

Grammar (from RESEARCH.md — implemented exactly):
    expression  ::= term (('+' | '-') term)*
    term        ::= factor (('*' | '/') factor)*
    factor      ::= '-' factor | '(' expression ')' | atom
    atom        ::= dice_expr | INTEGER
    dice_expr   ::= INTEGER 'd' INTEGER keep_modifier?
    keep_modifier ::= ('kh' | 'kl') INTEGER

The parser builds DiceResult objects directly (no separate AST) by combining
sub-results using DiceResult arithmetic helpers.

Division uses int(a / b) — NOT a // b — to match 5e truncation toward zero.
e.g. -7/2 = -3 in this engine (Python's // would give -4).

The Roller instance is injected at call time (not stored as global state).
The seed integer is purely for the DiceResult audit trail — it is NOT used
to re-seed the Roller's RNG.

ParseError is raised for any malformed expression; it never fails silently.
"""
from __future__ import annotations

import re
from typing import Optional

from src.engine.lexer import Token, tokenize
from src.engine.models import DiceResult
from src.engine.roller import Roller

# Regex for splitting a raw DICE token value (e.g. "2d20kh1", "4d6kl3", "2d6")
_DICE_VALUE_RE = re.compile(
    r"^(?P<n_dice>\d+)[dD](?P<sides>\d+)(?:(?P<keep_type>k[hl])(?P<keep_count>\d+))?$",
    re.IGNORECASE,
)


class ParseError(ValueError):
    """Raised when the expression cannot be parsed."""
    pass


class _DiceParser:
    """
    Internal recursive descent parser.

    Consume tokens from left to right, building up DiceResult objects.
    """

    def __init__(self, tokens: list[Token], roller: Roller) -> None:
        self._tokens = tokens
        self._pos = 0
        self._roller = roller

    # ------------------------------------------------------------------
    # Public entry
    # ------------------------------------------------------------------

    def parse(self) -> DiceResult:
        result = self._expression()
        if self._pos != len(self._tokens):
            tok = self._tokens[self._pos]
            raise ParseError(
                f"Unexpected token at position {self._pos}: {tok.value!r}"
            )
        return result

    # ------------------------------------------------------------------
    # Grammar rules
    # ------------------------------------------------------------------

    def _expression(self) -> DiceResult:
        """expression ::= term (('+' | '-') term)*"""
        left = self._term()
        while self._peek_value() in ("+", "-"):
            op = self._consume_op()
            right = self._term()
            if op == "+":
                left = left.add(right)
            else:
                left = left.subtract(right)
        return left

    def _term(self) -> DiceResult:
        """term ::= factor (('*' | '/') factor)*"""
        left = self._factor()
        while self._peek_value() in ("*", "/"):
            op = self._consume_op()
            right = self._factor()
            if op == "*":
                left = left.multiply(right)
            else:
                left = left.divide(right)
        return left

    def _factor(self) -> DiceResult:
        """factor ::= '-' factor | '(' expression ')' | atom"""
        if self._peek_value() == "-":
            self._consume_op()  # consume unary minus
            return self._factor().negate()
        if self._peek_value() == "(":
            self._consume_lparen()
            result = self._expression()
            self._expect_rparen()
            return result
        return self._atom()

    def _atom(self) -> DiceResult:
        """atom ::= DICE | INT"""
        if self._pos >= len(self._tokens):
            raise ParseError("Unexpected end of expression; expected a value or die roll")
        token = self._tokens[self._pos]
        self._pos += 1

        if token.type == "DICE":
            return self._evaluate_dice_token(token)
        if token.type == "INT":
            return DiceResult.from_constant(int(token.value))
        raise ParseError(f"Unexpected token: type={token.type!r} value={token.value!r}")

    # ------------------------------------------------------------------
    # Dice token evaluation
    # ------------------------------------------------------------------

    def _evaluate_dice_token(self, token: Token) -> DiceResult:
        """Parse a DICE token value and delegate to the Roller."""
        m = _DICE_VALUE_RE.match(str(token.value))
        if not m:
            raise ParseError(f"Malformed dice token: {token.value!r}")

        n_dice = int(m.group("n_dice"))
        sides = int(m.group("sides"))
        raw_keep_type = m.group("keep_type")  # e.g. "kh" or "kl" or None
        keep_type = raw_keep_type.lower() if raw_keep_type else None
        keep_count_str = m.group("keep_count")
        keep_count = int(keep_count_str) if keep_count_str else n_dice

        return self._roller.roll_dice(
            n_dice=n_dice,
            sides=sides,
            keep_type=keep_type,
            keep_count=keep_count,
        )

    # ------------------------------------------------------------------
    # Token consumption helpers
    # ------------------------------------------------------------------

    def _peek_value(self) -> Optional[str]:
        """Return the value of the current token, or None if at end."""
        if self._pos >= len(self._tokens):
            return None
        tok = self._tokens[self._pos]
        return str(tok.value)

    def _consume_op(self) -> str:
        """Consume and return the current operator token's value."""
        tok = self._tokens[self._pos]
        self._pos += 1
        return str(tok.value)

    def _consume_lparen(self) -> None:
        tok = self._tokens[self._pos]
        if tok.type != "LPAREN":
            raise ParseError(f"Expected '(' but got {tok.value!r}")
        self._pos += 1

    def _expect_rparen(self) -> None:
        if self._pos >= len(self._tokens):
            raise ParseError("Expected ')' but reached end of expression")
        tok = self._tokens[self._pos]
        if tok.type != "RPAREN":
            raise ParseError(f"Expected ')' but got {tok.value!r}")
        self._pos += 1


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def roll_expression(
    expr: str,
    roller: Roller,
    seed: Optional[int] = None,
) -> DiceResult:
    """
    Evaluate a dice expression and return a structured DiceResult.

    Parameters
    ----------
    expr   : str
        The dice expression to evaluate (e.g. "2d6+5", "2d20kh1", "(1d6+2)*3").
        Whitespace is tolerated. Operators: +, -, *, /. Division truncates toward
        zero (5e convention).
    roller : Roller
        The Roller instance to use for all die rolls. The caller controls seeding.
    seed   : Optional[int]
        The seed passed to DiceResult.seed for the audit trail only. Does NOT
        re-seed the roller's RNG — the roller must already be seeded by the caller.

    Returns
    -------
    DiceResult
        Immutable result with total, all die faces, original expression, and seed.

    Raises
    ------
    ParseError
        If the expression is syntactically invalid.
    ValueError
        If a character in the expression cannot be tokenized.
    """
    tokens = tokenize(expr)
    parser = _DiceParser(tokens, roller)
    result = parser.parse()
    # Attach the original expression string and the audit-trail seed
    return result.with_context(expression=expr, seed=seed)
