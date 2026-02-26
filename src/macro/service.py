"""
MacroSandboxService — orchestrates multi-line macro preprocessing and execution.

Design:
  The service is called in two phases:
    1. preprocess_all_lines() — splits input into lines, skips blanks, calls
       MacroPreprocessor.process_line() on each, returns list[CleanedMacro].
    2. collect_all_queries() — flattens all QuerySpec objects across lines,
       deduplicates by raw token (same query asked in multiple lines = ask once).
    3. execute() — substitutes query answers, normalizes double-sign expressions,
       resolves inline rolls, evaluates final dice expression, returns MacroRollResult.

No Qt dependencies. Pure Python.

Exports: MacroSandboxService
"""
from __future__ import annotations

import re
from typing import Optional

from src.macro.models import MacroLineResult, MacroRollResult, MacroWarning
from src.macro.preprocessor import CleanedMacro, MacroPreprocessor, QuerySpec


# ---------------------------------------------------------------------------
# Expression normalization helpers
# ---------------------------------------------------------------------------

def _normalize_expression(expr: str) -> str:
    """
    Collapse double-sign artifacts left by query substitution or token stripping.

    Rules:
      ++  ->  +
      +-  ->  -
      -+  ->  -
      --  ->  +

    Applied repeatedly until stable (handles edge cases like +++).
    """
    prev = None
    while prev != expr:
        prev = expr
        expr = re.sub(r'\+\+', '+', expr)
        expr = re.sub(r'\+-', '-', expr)
        expr = re.sub(r'-\+', '-', expr)
        expr = re.sub(r'--', '+', expr)
    # Strip any trailing operator that would cause a ParseError
    expr = expr.strip()
    return expr


# ---------------------------------------------------------------------------
# MacroSandboxService
# ---------------------------------------------------------------------------

class MacroSandboxService:
    """
    Orchestrates multi-line Roll20 macro preprocessing and execution.

    Usage:
        service = MacroSandboxService()
        cleaned = service.preprocess_all_lines(raw_text)
        queries = service.collect_all_queries(cleaned)
        # ... collect answers from UI ...
        result = service.execute(cleaned, answers, roller)
    """

    def __init__(self) -> None:
        self._preprocessor = MacroPreprocessor()

    def preprocess_all_lines(self, raw_text: str) -> list[CleanedMacro]:
        """
        Parse all non-empty lines from raw_text.

        Splits on newlines, skips blank/whitespace-only lines, and calls
        MacroPreprocessor.process_line() on each non-empty line.

        Returns a list of CleanedMacro objects (only non-empty results).
        Line numbers are tracked via enumerate but not stored in CleanedMacro
        (the service assigns line_number in execute() based on position in list).
        """
        results: list[CleanedMacro] = []
        for raw_line in raw_text.splitlines():
            cleaned = self._preprocessor.process_line(raw_line)
            if not cleaned.is_empty:
                results.append(cleaned)
        return results

    def collect_all_queries(self, cleaned: list[CleanedMacro]) -> list[QuerySpec]:
        """
        Flatten and deduplicate all QuerySpec objects across all CleanedMacro lines.

        Deduplication is by QuerySpec.raw (the original ?{...} token text).
        Same query in multiple lines is asked only once.

        Returns an ordered list of unique QuerySpec objects (first-seen order).
        """
        seen: set[str] = set()
        queries: list[QuerySpec] = []
        for macro in cleaned:
            for q in macro.queries:
                if q.raw not in seen:
                    seen.add(q.raw)
                    queries.append(q)
        return queries

    def execute(
        self,
        cleaned: list[CleanedMacro],
        answers: dict,
        roller,
        seed: Optional[int] = None,
    ) -> MacroRollResult:
        """
        Execute all lines with query answers substituted.

        For each non-empty CleanedMacro:
          a. Substitute ?{...} query tokens via answers dict.
          b. Normalize double-sign expressions (++ -> +, +- -> -, etc.).
          c. Resolve [[inline rolls]] via MacroPreprocessor.resolve_inline_rolls().
          d. Evaluate the final expression via roll_expression().
          e. On ParseError or ValueError: create MacroLineResult with error string.

        Parameters
        ----------
        cleaned : list[CleanedMacro]
            Output from preprocess_all_lines(). Empty macros are skipped.
        answers : dict
            Mapping of raw ?{...} token -> chosen value string.
        roller  : Roller
            The seeded Roller instance from MainWindow.
        seed    : Optional[int]
            Audit-trail seed passed to roll_expression(); does NOT re-seed the roller.

        Returns
        -------
        MacroRollResult with one MacroLineResult per non-empty line.
        """
        from src.engine.parser import roll_expression, ParseError

        results: list[MacroLineResult] = []
        line_number = 1

        for macro in cleaned:
            if macro.is_empty:
                continue

            expr = macro.expression

            # Step a: Substitute query answers
            expr = self._preprocessor.substitute_queries(expr, answers)

            # Step b: Normalize double-sign artifacts
            expr = _normalize_expression(expr)

            # Step c: Resolve inline rolls
            try:
                expr, inline_results = self._preprocessor.resolve_inline_rolls(
                    expr, roller, seed
                )
            except (ValueError, ParseError) as e:
                results.append(MacroLineResult(
                    line_number=line_number,
                    dice_result=None,
                    inline_results=[],
                    warnings=[MacroWarning(token=w.token, reason=w.reason) for w in macro.warnings],
                    error=str(e),
                    template_name=macro.template_name,
                    template_fields=macro.template_fields,
                ))
                line_number += 1
                continue

            # Normalize again after inline roll substitution (result may start with +/-)
            expr = _normalize_expression(expr)

            # Convert warnings from ParseWarning to MacroWarning
            warnings = [
                MacroWarning(token=w.token, reason=w.reason) for w in macro.warnings
            ]

            # Step d: Evaluate the final expression
            # Skip evaluation for template-only lines where the expression is
            # empty or non-rollable after {{...}} field extraction
            expr_stripped = expr.strip()
            is_template_line = macro.template_name is not None or inline_results
            if is_template_line and (not expr_stripped or not re.search(r'\d+d\d+', expr_stripped)):
                # Template/inline-only — inline rolls ARE the results
                results.append(MacroLineResult(
                    line_number=line_number,
                    dice_result=None,
                    inline_results=inline_results,
                    warnings=warnings,
                    error=None,
                    template_name=macro.template_name,
                    template_fields=macro.template_fields,
                ))
            else:
                try:
                    dice_result = roll_expression(expr, roller, seed)
                    results.append(MacroLineResult(
                        line_number=line_number,
                        dice_result=dice_result,
                        inline_results=inline_results,
                        warnings=warnings,
                        error=None,
                        template_name=macro.template_name,
                        template_fields=macro.template_fields,
                    ))
                except (ValueError, ParseError) as e:
                    # If we have inline results or a template name, suppress the error —
                    # the inline rolls ARE the results for template-based macros
                    if inline_results or macro.template_name:
                        results.append(MacroLineResult(
                            line_number=line_number,
                            dice_result=None,
                            inline_results=inline_results,
                            warnings=warnings,
                            error=None,
                            template_name=macro.template_name,
                            template_fields=macro.template_fields,
                        ))
                    else:
                        results.append(MacroLineResult(
                            line_number=line_number,
                            dice_result=None,
                            inline_results=inline_results,
                            warnings=warnings,
                            error=str(e),
                            template_name=macro.template_name,
                            template_fields=macro.template_fields,
                        ))

            line_number += 1

        return MacroRollResult(line_results=results)
