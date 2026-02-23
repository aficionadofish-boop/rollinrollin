"""
Lexer for dice expressions.

Converts a dice expression string into a flat list of Token objects.

Token types:
  DICE    - a dice expression atom: NdM or NdMkhN or NdMklN
            e.g. "2d6", "2d20kh1", "4d6kl3"
  INT     - a bare integer literal: e.g. "5", "10"
  OP      - an arithmetic operator: +, -, *, /
  LPAREN  - literal '('
  RPAREN  - literal ')'

Whitespace is silently skipped.

CRITICAL ordering: DICE pattern must appear BEFORE INT in the regex alternation.
If INT matched first, "2d6" would tokenize as INT(2) then fail on 'd6'.

Token.value:
  - For DICE tokens: the raw matched string (e.g. "2d20kh1")
  - For INT tokens: the integer value (int)
  - For OP/LPAREN/RPAREN: the raw character string
"""
from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Literal, Union

TokenType = Literal["DICE", "INT", "OP", "LPAREN", "RPAREN"]

# Token regex pattern.
# Order matters: DICE must be first so that "2d6" is consumed as one token
# before INT can consume the leading "2".
# re.IGNORECASE allows '2D6' and '2d6' to both tokenize correctly.
_TOKEN_RE = re.compile(
    r"(?P<DICE>\d+[dD]\d+(?:k[hl]\d+)?)"  # 2d6, 2d20kh1, 4d6kl3 — MUST be first
    r"|(?P<INT>\d+)"                        # bare integer: 5, 10
    r"|(?P<OP>[+\-*/])"                     # arithmetic operators
    r"|(?P<LPAREN>\()"
    r"|(?P<RPAREN>\))"
    r"|\s+",                                # whitespace: skip (no named group)
    re.IGNORECASE,
)


@dataclass
class Token:
    """A single lexer token."""

    type: TokenType
    value: Union[str, int]


def tokenize(expr: str) -> list[Token]:
    """
    Tokenize a dice expression string into a list of Token objects.

    Whitespace is silently discarded. Raises ValueError on unrecognized characters.

    Parameters
    ----------
    expr : str
        The dice expression to tokenize (e.g. "2d6+5", "2d20kh1", "(1d6+2)*3")

    Returns
    -------
    list[Token]
        Flat list of typed tokens in the order they appear in the expression.

    Raises
    ------
    ValueError
        If any character in the expression cannot be matched by the token grammar.
    """
    tokens: list[Token] = []
    pos = 0
    length = len(expr)

    for m in _TOKEN_RE.finditer(expr):
        # Check for gaps between matches — unrecognized characters
        if m.start() != pos:
            bad = expr[pos : m.start()]
            raise ValueError(
                f"Unexpected character(s) in expression at position {pos}: {bad!r}"
            )
        pos = m.end()

        kind = m.lastgroup
        if kind is None:
            # Matched whitespace (no named group) — skip
            continue
        elif kind == "DICE":
            tokens.append(Token(type="DICE", value=m.group()))
        elif kind == "INT":
            tokens.append(Token(type="INT", value=int(m.group())))
        elif kind in ("OP", "LPAREN", "RPAREN"):
            tokens.append(Token(type=kind, value=m.group()))

    # Check for trailing unrecognized characters
    if pos != length:
        bad = expr[pos:]
        raise ValueError(
            f"Unexpected character(s) at end of expression: {bad!r}"
        )

    return tokens
