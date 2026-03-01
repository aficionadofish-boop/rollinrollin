"""
TDD tests for MacroSandboxService.

Uses a seeded Roller(random.Random(42)) for deterministic results.
"""
from __future__ import annotations

import random

import pytest

from src.engine.roller import Roller
from src.macro.models import MacroLineResult, MacroRollResult
from src.macro.preprocessor import CleanedMacro, QuerySpec
from src.macro.service import MacroSandboxService


@pytest.fixture
def roller():
    return Roller(random.Random(42))


@pytest.fixture
def service():
    return MacroSandboxService()


# ---------------------------------------------------------------------------
# 1. preprocess_all_lines
# ---------------------------------------------------------------------------

class TestPreprocessAllLines:
    def test_preprocess_all_lines_skips_blank(self, service):
        """Blank and whitespace-only lines are skipped; 3 non-empty lines returned."""
        results = service.preprocess_all_lines("1d20+5\n\n2d6\n  \n1d4")
        assert len(results) == 3
        # None of the returned macros should be empty
        for macro in results:
            assert not macro.is_empty

    def test_preprocess_single_line(self, service):
        results = service.preprocess_all_lines("1d6+3")
        assert len(results) == 1
        assert results[0].expression == "1d6+3"

    def test_preprocess_empty_text(self, service):
        results = service.preprocess_all_lines("")
        assert results == []

    def test_preprocess_all_blank_text(self, service):
        results = service.preprocess_all_lines("\n\n   \n")
        assert results == []


# ---------------------------------------------------------------------------
# 2. execute — basic cases
# ---------------------------------------------------------------------------

class TestExecuteBasic:
    def test_execute_simple_expression(self, service, roller):
        cleaned = service.preprocess_all_lines("1d20+5")
        result = service.execute(cleaned, {}, roller)
        assert isinstance(result, MacroRollResult)
        assert len(result.line_results) == 1
        lr = result.line_results[0]
        assert isinstance(lr, MacroLineResult)
        assert lr.has_result
        assert lr.error is None
        assert isinstance(lr.dice_result.total, int)
        assert 6 <= lr.dice_result.total <= 25  # 1d20+5 range

    def test_execute_multi_line(self, service, roller):
        """3 non-empty lines produce 3 MacroLineResult entries."""
        cleaned = service.preprocess_all_lines("1d6\n2d6\n1d4")
        result = service.execute(cleaned, {}, roller)
        assert len(result.line_results) == 3
        # Line numbers should be sequential starting from 1
        line_nums = [lr.line_number for lr in result.line_results]
        assert line_nums == [1, 2, 3]

    def test_execute_returns_macro_roll_result(self, service, roller):
        cleaned = service.preprocess_all_lines("1d6")
        result = service.execute(cleaned, {}, roller)
        assert isinstance(result, MacroRollResult)


# ---------------------------------------------------------------------------
# 3. execute — query substitution
# ---------------------------------------------------------------------------

class TestExecuteQuerySubstitution:
    def test_execute_with_query_substitution(self, service, roller):
        """Query token substitution produces a valid roll result."""
        cleaned = service.preprocess_all_lines("1d20+?{Mod|STR,+2|DEX,+4}")
        answers = {"?{Mod|STR,+2|DEX,+4}": "+2"}
        result = service.execute(cleaned, answers, roller)
        assert len(result.line_results) == 1
        lr = result.line_results[0]
        assert lr.has_result
        assert lr.error is None
        # 1d20+2 range: 3..22
        assert 3 <= lr.dice_result.total <= 22

    def test_expression_normalization_double_plus(self, service, roller):
        """After query substitution, ++ is normalized to + before roll_expression()."""
        cleaned = service.preprocess_all_lines("1d20+?{Mod|STR,+2}")
        answers = {"?{Mod|STR,+2}": "+2"}
        result = service.execute(cleaned, answers, roller)
        assert len(result.line_results) == 1
        lr = result.line_results[0]
        # Should succeed (no ParseError from 1d20++2)
        assert lr.has_result
        assert lr.error is None

    def test_expression_normalization_plus_minus(self, service, roller):
        """After query substitution, +- is normalized to - before roll_expression()."""
        cleaned = service.preprocess_all_lines("1d20+?{Mod|Penalty,-2}")
        answers = {"?{Mod|Penalty,-2}": "-2"}
        result = service.execute(cleaned, answers, roller)
        lr = result.line_results[0]
        # Should succeed (no ParseError from 1d20+-2)
        assert lr.has_result
        assert lr.error is None


# ---------------------------------------------------------------------------
# 4. execute — error handling
# ---------------------------------------------------------------------------

class TestExecuteErrors:
    def test_execute_invalid_expression_produces_error(self, service, roller):
        """Attr token stripped leaves invalid expression; result has error, no dice_result."""
        # @{bad} will be stripped to "", leaving "1d20 + " — a trailing operator
        cleaned = service.preprocess_all_lines("1d20 + @{bad}")
        result = service.execute(cleaned, {}, roller)
        assert len(result.line_results) == 1
        lr = result.line_results[0]
        assert not lr.has_result
        assert lr.error is not None
        assert lr.dice_result is None

    def test_execute_completely_invalid_expression(self, service, roller):
        """A line that is just garbage text produces an error."""
        # Force an error by providing a cleaned macro with a truly invalid expression
        from src.macro.preprocessor import CleanedMacro
        bad_cleaned = [CleanedMacro(
            expression="not a dice expression!!! xyz",
            queries=[],
            warnings=[],
            is_empty=False,
        )]
        result = service.execute(bad_cleaned, {}, roller)
        assert len(result.line_results) == 1
        lr = result.line_results[0]
        assert not lr.has_result
        assert lr.error is not None


# ---------------------------------------------------------------------------
# 5. execute — inline rolls
# ---------------------------------------------------------------------------

class TestExecuteInlineRolls:
    def test_execute_with_inline_roll_plus_dice(self, service, roller):
        """[[2d6+3]]+1d4 — inline resolves to integer N, then N+1d4 evaluates."""
        cleaned = service.preprocess_all_lines("[[2d6+3]]+1d4")
        result = service.execute(cleaned, {}, roller)
        assert len(result.line_results) == 1
        lr = result.line_results[0]
        # inline_results should have one entry for [[2d6+3]]
        assert len(lr.inline_results) == 1
        # The final result should succeed
        assert lr.has_result
        # Total should be in range: (2+3)+(1) to (12+3)+(4) = 6..19
        assert 6 <= lr.dice_result.total <= 19


# ---------------------------------------------------------------------------
# 6. collect_all_queries
# ---------------------------------------------------------------------------

# ---------------------------------------------------------------------------
# 5b. execute — query substitution in template fields
# ---------------------------------------------------------------------------

class TestExecuteTemplateFieldQuerySubstitution:
    def test_keyed_template_field_query_resolved(self, service, roller):
        """{{Damage=?{Hits|1, [[1d6+3]]|2, [[2d6+6]]}}} — query substituted in field value."""
        raw = "&{template:default}{{name=Sneak Attack}}{{Damage=?{Hits|1, [[1d6+3]] P|2, [[2d6+6]] P}}}"
        cleaned = service.preprocess_all_lines(raw)
        queries = service.collect_all_queries(cleaned)
        assert len(queries) == 1
        assert queries[0].prompt == "Hits"

        # Simulate user picking option 1
        answers = {queries[0].raw: "[[1d6+3]] P"}
        result = service.execute(cleaned, answers, roller)
        lr = result.line_results[0]

        # template_fields should have the resolved value (no ?{...} token)
        assert len(lr.template_fields) == 1
        key, value = lr.template_fields[0]
        assert key == "Damage"
        assert "?{" not in value
        # The [[...]] tokens remain in template_fields (resolved by TemplateCard)
        assert "[[1d6+3]]" in value

    def test_bare_template_field_query_resolved(self, service, roller):
        """{{?{How Many|1, 1 Attack [[1d20+6]]|5, 5 Attacks ...}}} — bare query resolved."""
        raw = "&{template:default}{{name=Attacks}}{{?{How Many|1, 1 Attack [[1d20+6]]|2, 2 Attacks [[1d20+6]] [[1d20+6]]}}}"
        cleaned = service.preprocess_all_lines(raw)
        queries = service.collect_all_queries(cleaned)
        assert len(queries) == 1

        # Simulate user picking option 2
        answers = {queries[0].raw: "2 Attacks [[1d20+6]] [[1d20+6]]"}
        result = service.execute(cleaned, answers, roller)
        lr = result.line_results[0]

        # template_fields should have empty key with resolved value
        assert len(lr.template_fields) == 1
        key, value = lr.template_fields[0]
        assert key == ""
        assert "?{" not in value
        # Should have 2 inline results from the chosen option
        assert len(lr.inline_results) == 2

    def test_template_name_preserved_with_query_fields(self, service, roller):
        """Template name is preserved when fields contain queries."""
        raw = "&{template:default}{{name=My Roll}}{{Result=?{Type|A, [[1d20]]|B, [[2d10]]}}}"
        cleaned = service.preprocess_all_lines(raw)
        answers = {cleaned[0].queries[0].raw: "[[1d20]]"}
        result = service.execute(cleaned, answers, roller)
        lr = result.line_results[0]
        assert lr.template_name == "My Roll"
        assert lr.template_fields[0][0] == "Result"


class TestCollectAllQueries:
    def test_collect_all_queries_single_query_per_line(self, service):
        """collect_all_queries flattens all queries across lines."""
        cleaned = service.preprocess_all_lines(
            "1d20+?{A|X,1}\n2d6+?{B|Y,2}"
        )
        assert len(cleaned) == 2
        assert len(cleaned[0].queries) == 1
        assert len(cleaned[1].queries) == 1

        all_queries = service.collect_all_queries(cleaned)
        assert len(all_queries) == 2
        prompts = [q.prompt for q in all_queries]
        assert "A" in prompts
        assert "B" in prompts

    def test_collect_all_queries_deduplicates_by_raw(self, service):
        """Same ?{...} token in multiple lines appears only once."""
        cleaned = service.preprocess_all_lines(
            "1d20+?{Mod|STR,+2}\n2d6+?{Mod|STR,+2}"
        )
        all_queries = service.collect_all_queries(cleaned)
        # Same raw token -> deduplicated to 1 entry
        assert len(all_queries) == 1
        assert all_queries[0].prompt == "Mod"

    def test_collect_all_queries_empty(self, service):
        cleaned = service.preprocess_all_lines("1d6")
        all_queries = service.collect_all_queries(cleaned)
        assert all_queries == []
