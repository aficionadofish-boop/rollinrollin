"""
TDD tests for MacroPreprocessor.

Uses a seeded Roller(random.Random(42)) for deterministic inline-roll results.
"""
from __future__ import annotations

import random

import pytest

from src.engine.roller import Roller
from src.macro.preprocessor import (
    CleanedMacro,
    MacroPreprocessor,
    ParseWarning,
    QuerySpec,
)


@pytest.fixture
def roller():
    return Roller(random.Random(42))


@pytest.fixture
def preprocessor():
    return MacroPreprocessor()


# ---------------------------------------------------------------------------
# 1. /roll prefix stripping
# ---------------------------------------------------------------------------

class TestStripRollPrefix:
    def test_strip_roll_prefix(self, preprocessor):
        result = preprocessor.process_line("/roll 1d20+5")
        assert result.expression == "1d20+5"
        assert not result.is_empty

    def test_strip_r_prefix(self, preprocessor):
        result = preprocessor.process_line("/r 2d6")
        assert result.expression == "2d6"
        assert not result.is_empty

    def test_plain_expression_unchanged(self, preprocessor):
        result = preprocessor.process_line("1d20")
        assert result.expression == "1d20"
        assert not result.is_empty

    def test_strip_roll_prefix_case_insensitive(self, preprocessor):
        for prefix in ("/Roll 1d6", "/ROLL 1d6", "/R 1d6"):
            result = preprocessor.process_line(prefix)
            assert result.expression == "1d6", f"Failed for prefix variant: {prefix!r}"
            assert not result.is_empty


# ---------------------------------------------------------------------------
# 2. Blank line handling
# ---------------------------------------------------------------------------

class TestBlankLines:
    def test_empty_string_is_empty(self, preprocessor):
        result = preprocessor.process_line("")
        assert result.is_empty
        assert result.expression == ""

    def test_whitespace_only_is_empty(self, preprocessor):
        result = preprocessor.process_line("   ")
        assert result.is_empty
        assert result.expression == ""


# ---------------------------------------------------------------------------
# 3. Query extraction
# ---------------------------------------------------------------------------

class TestQueryExtraction:
    def test_extract_query_with_options(self, preprocessor):
        result = preprocessor.process_line("?{Save|STR,+2|DEX,+4}")
        assert len(result.queries) == 1
        q = result.queries[0]
        assert isinstance(q, QuerySpec)
        assert q.prompt == "Save"
        assert q.options == [("STR", "+2"), ("DEX", "+4")]
        assert q.raw == "?{Save|STR,+2|DEX,+4}"

    def test_extract_query_label_only(self, preprocessor):
        """When no comma, label is used as both label and value."""
        result = preprocessor.process_line("?{Ability|STR|DEX}")
        assert len(result.queries) == 1
        q = result.queries[0]
        assert q.prompt == "Ability"
        assert q.options == [("STR", "STR"), ("DEX", "DEX")]

    def test_extract_free_text_query(self, preprocessor):
        """?{Modifier} with no pipe produces empty options list."""
        result = preprocessor.process_line("?{Modifier}")
        assert len(result.queries) == 1
        q = result.queries[0]
        assert q.prompt == "Modifier"
        assert q.options == []
        assert q.raw == "?{Modifier}"

    def test_multiple_queries_in_one_line(self, preprocessor):
        result = preprocessor.process_line("1d20+?{Mod|STR,+2}+?{Bonus}")
        assert len(result.queries) == 2
        assert result.queries[0].prompt == "Mod"
        assert result.queries[0].options == [("STR", "+2")]
        assert result.queries[1].prompt == "Bonus"
        assert result.queries[1].options == []


# ---------------------------------------------------------------------------
# 4. Unsupported token warnings
# ---------------------------------------------------------------------------

class TestUnsupportedTokenWarnings:
    def test_unsupported_attr_token(self, preprocessor):
        result = preprocessor.process_line("1d20+@{target|ac}")
        assert len(result.warnings) == 1
        w = result.warnings[0]
        assert isinstance(w, ParseWarning)
        assert w.token == "@{target|ac}"
        # The token should be stripped (removed) from the expression
        assert "@{target|ac}" not in result.expression

    def test_unsupported_template_token(self, preprocessor):
        result = preprocessor.process_line("&{template:default}")
        assert len(result.warnings) == 1
        w = result.warnings[0]
        assert w.token == "&{template:default}"
        assert "&{template:default}" not in result.expression

    def test_attr_partial_evaluation(self, preprocessor):
        """@{bonus} stripped; warning emitted; expression has no attr token."""
        result = preprocessor.process_line("1d20+5+@{bonus}")
        assert len(result.warnings) == 1
        assert "@{bonus}" not in result.expression
        # Expression may be "1d20+5+" or "1d20+5" depending on strip strategy
        # Either way, the attr token must be removed
        assert "1d20+5" in result.expression


# ---------------------------------------------------------------------------
# 5. Inline roll resolution
# ---------------------------------------------------------------------------

class TestInlineRolls:
    def test_inline_roll_resolution(self, preprocessor, roller):
        """[[2d6+3]] should be replaced with its integer total."""
        resolved, inline_results = preprocessor.resolve_inline_rolls(
            "The damage is [[2d6+3]]", roller
        )
        # The [[2d6+3]] bracket syntax should be gone
        assert "[[" not in resolved
        assert "]]" not in resolved
        # One inline result recorded
        assert len(inline_results) == 1
        # The resolved string should contain only the total as a number
        # (text "The damage is N")
        original_expr, dice_result = inline_results[0]
        assert original_expr == "[[2d6+3]]"
        assert isinstance(dice_result.total, int)
        assert dice_result.total >= 3 + 2  # min: 1+1+3=5
        assert dice_result.total <= 6 + 6 + 3  # max: 15

    def test_nested_inline_roll(self, preprocessor, roller):
        """Inner [[1d4]] resolves first, then outer [[1d20+N]] resolves."""
        resolved, inline_results = preprocessor.resolve_inline_rolls(
            "[[1d20+[[1d4]]]]", roller
        )
        # No brackets left in the resolved string
        assert "[[" not in resolved
        assert "]]" not in resolved
        # Two inline results: inner d4 and outer d20+N
        assert len(inline_results) == 2
        # The final resolved string should be a plain integer
        total = int(resolved.strip())
        assert 1 + 1 <= total <= 20 + 4  # 1d20 + 1d4 range


# ---------------------------------------------------------------------------
# 6. Query substitution
# ---------------------------------------------------------------------------

class TestQuerySubstitution:
    def test_substitute_queries(self, preprocessor):
        """substitute_queries replaces the raw token with chosen value."""
        result = preprocessor.substitute_queries(
            "1d20+?{Mod|STR,+2}", {"?{Mod|STR,+2}": "+2"}
        )
        assert result == "1d20++2"
        # Note: double-plus normalization happens in the service layer, not here
