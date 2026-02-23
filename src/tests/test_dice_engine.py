"""
Golden tests for the dice expression engine.
TDD RED phase: these tests are written before the implementation exists.
All tests import from src.engine which does not exist yet — they will fail with ImportError.
"""
import random

import pytest

from src.engine.lexer import tokenize
from src.engine.models import DiceResult, DieFace
from src.engine.roller import Roller
from src.engine.parser import roll_expression


# ---------------------------------------------------------------------------
# Lexer tests
# ---------------------------------------------------------------------------

def test_tokenize_basic():
    """tokenize('2d6+5') produces [DICE(2d6), OP(+), INT(5)]."""
    tokens = tokenize("2d6+5")
    assert len(tokens) == 3
    assert tokens[0].type == "DICE"
    assert tokens[0].value == "2d6"
    assert tokens[1].type == "OP"
    assert tokens[1].value == "+"
    assert tokens[2].type == "INT"
    assert tokens[2].value == 5


def test_tokenize_keep():
    """tokenize('2d20kh1') returns a single DICE token — not split."""
    tokens = tokenize("2d20kh1")
    assert len(tokens) == 1
    assert tokens[0].type == "DICE"
    assert tokens[0].value == "2d20kh1"


def test_tokenize_whitespace():
    """tokenize('  2d6 + 3 ') returns same tokens as '2d6+3'."""
    tokens_padded = tokenize("  2d6 + 3 ")
    tokens_clean = tokenize("2d6+3")
    assert len(tokens_padded) == len(tokens_clean)
    for tp, tc in zip(tokens_padded, tokens_clean):
        assert tp.type == tc.type
        assert tp.value == tc.value


def test_tokenize_keep_lowest():
    """tokenize('4d6kl3') produces a single DICE token."""
    tokens = tokenize("4d6kl3")
    assert len(tokens) == 1
    assert tokens[0].type == "DICE"
    assert tokens[0].value == "4d6kl3"


def test_tokenize_parens():
    """tokenize('(1d6+2)*3') produces LPAREN, DICE, OP, INT, RPAREN, OP, INT."""
    tokens = tokenize("(1d6+2)*3")
    types = [t.type for t in tokens]
    assert types == ["LPAREN", "DICE", "OP", "INT", "RPAREN", "OP", "INT"]


# ---------------------------------------------------------------------------
# Roll constant
# ---------------------------------------------------------------------------

def test_roll_constant():
    """roll_expression('5', roller) → total=5, faces=(), constant_bonus=5."""
    roller = Roller(random.Random(1))
    result = roll_expression("5", roller, seed=None)
    assert result.total == 5
    assert result.faces == ()
    assert result.constant_bonus == 5


# ---------------------------------------------------------------------------
# Single die and basic sums
# ---------------------------------------------------------------------------

def test_roll_single_die():
    """roll_expression('1d6', roller) → total in [1,6], 1 face, sides==6."""
    roller = Roller(random.Random(1))
    result = roll_expression("1d6", roller, seed=None)
    assert 1 <= result.total <= 6
    assert len(result.faces) == 1
    assert result.faces[0].sides == 6


def test_roll_sum():
    """roll_expression('2d6', roller) → total equals sum of face values."""
    roller = Roller(random.Random(7))
    result = roll_expression("2d6", roller, seed=None)
    assert result.total == sum(f.value for f in result.faces)


# ---------------------------------------------------------------------------
# Operator precedence and parentheses
# ---------------------------------------------------------------------------

def test_precedence_mul_before_add():
    """With seed=42, '2d6+1d4*2' total matches d6sum + d4*2 (multiply first).

    seed=42 produces: d6s=6,1 then d4=1 → total = 6+1 + 1*2 = 9
    """
    roller = Roller(random.Random(42))
    result = roll_expression("2d6+1d4*2", roller, seed=42)
    assert result.total == 9


def test_parentheses():
    """With seed=1, '(1d6+2)*3' total == (d6+2)*3.

    seed=1 produces d6=2 → (2+2)*3 = 12
    """
    roller = Roller(random.Random(1))
    result = roll_expression("(1d6+2)*3", roller, seed=1)
    assert result.total == 12


# ---------------------------------------------------------------------------
# Keep highest / keep lowest
# ---------------------------------------------------------------------------

def test_keep_highest():
    """'2d20kh1' → exactly 1 kept=True, 1 kept=False; total == kept face value."""
    roller = Roller(random.Random(7))
    result = roll_expression("2d20kh1", roller, seed=None)
    assert len(result.faces) == 2
    kept = [f for f in result.faces if f.kept]
    dropped = [f for f in result.faces if not f.kept]
    assert len(kept) == 1
    assert len(dropped) == 1
    assert result.total == kept[0].value
    # Kept face must be the higher of the two
    assert kept[0].value >= dropped[0].value


def test_keep_lowest():
    """'2d20kl1' → exactly 1 kept=True; total == lower face value."""
    roller = Roller(random.Random(7))
    result = roll_expression("2d20kl1", roller, seed=None)
    assert len(result.faces) == 2
    kept = [f for f in result.faces if f.kept]
    assert len(kept) == 1
    assert result.total == kept[0].value
    # Kept face must be the lower of the two
    all_values = [f.value for f in result.faces]
    assert kept[0].value == min(all_values)


def test_keep_4d6kl3():
    """'4d6kl3' → 4 faces, 3 kept (highest 3), 1 dropped (lowest)."""
    roller = Roller(random.Random(5))
    result = roll_expression("4d6kl3", roller, seed=None)
    assert len(result.faces) == 4
    kept = [f for f in result.faces if f.kept]
    dropped = [f for f in result.faces if not f.kept]
    assert len(kept) == 3
    assert len(dropped) == 1
    # The dropped face must be the lowest
    all_values = sorted(f.value for f in result.faces)
    assert dropped[0].value == all_values[0]
    # Total must be sum of kept faces
    assert result.total == sum(f.value for f in kept)


# ---------------------------------------------------------------------------
# Seeded determinism
# ---------------------------------------------------------------------------

def test_seeded_determinism():
    """Two Roller(Random(42)) instances rolling '3d6' produce identical faces.

    seed=42 → faces = (6, 1, 1)
    """
    roller1 = Roller(random.Random(42))
    roller2 = Roller(random.Random(42))
    result1 = roll_expression("3d6", roller1, seed=42)
    result2 = roll_expression("3d6", roller2, seed=42)
    assert result1.faces == result2.faces
    # Known expected faces for seed=42 rolling 3d6
    values = tuple(f.value for f in result1.faces)
    assert values == (6, 1, 1)


def test_unseeded_varies():
    """100 rolls of '1d20' with unseeded Roller are not all identical."""
    results = set()
    for _ in range(100):
        roller = Roller(random.Random())
        r = roll_expression("1d20", roller, seed=None)
        results.add(r.total)
    # With 100 rolls of d20, we must see at least 2 different values
    assert len(results) > 1


# ---------------------------------------------------------------------------
# expression and seed stored on result
# ---------------------------------------------------------------------------

def test_expression_stored():
    """result.expression equals the original expression string."""
    roller = Roller(random.Random(1))
    result = roll_expression("2d6+1d4", roller, seed=None)
    assert result.expression == "2d6+1d4"


def test_seed_stored():
    """Passing seed=99 to roll_expression stores 99 on result.seed."""
    roller = Roller(random.Random(99))
    result = roll_expression("1d6", roller, seed=99)
    assert result.seed == 99


def test_seed_none_stored():
    """Passing seed=None stores None on result.seed."""
    roller = Roller(random.Random())
    result = roll_expression("1d6", roller, seed=None)
    assert result.seed is None


# ---------------------------------------------------------------------------
# Division truncation toward zero (5e convention)
# ---------------------------------------------------------------------------

def test_division_truncation():
    """'-7/2' evaluates to -3 (truncation toward zero), NOT -4 (floor)."""
    roller = Roller(random.Random(1))
    result = roll_expression("-7/2", roller, seed=None)
    assert result.total == -3


# ---------------------------------------------------------------------------
# Unary and binary minus
# ---------------------------------------------------------------------------

def test_unary_minus():
    """'-1d6' → total is negative; total == -(face value)."""
    roller = Roller(random.Random(1))
    result = roll_expression("-1d6", roller, seed=None)
    assert len(result.faces) == 1
    assert result.total == -result.faces[0].value
    assert result.total < 0


def test_binary_minus():
    """'10-1d6' → total == 10 - face value."""
    roller = Roller(random.Random(1))
    result = roll_expression("10-1d6", roller, seed=None)
    assert len(result.faces) == 1
    assert result.total == 10 - result.faces[0].value


# ---------------------------------------------------------------------------
# Whitespace tolerance
# ---------------------------------------------------------------------------

def test_whitespace_tolerance():
    """'  2d6  +  3  ' produces same total as '2d6+3' with the same seed."""
    roller1 = Roller(random.Random(7))
    roller2 = Roller(random.Random(7))
    result_padded = roll_expression("  2d6  +  3  ", roller1, seed=None)
    result_clean = roll_expression("2d6+3", roller2, seed=None)
    assert result_padded.total == result_clean.total
