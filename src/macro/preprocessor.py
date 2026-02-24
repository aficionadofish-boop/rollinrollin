"""
MacroPreprocessor — pure-Python text transformation engine for Roll20 macro syntax.

Handles:
  - /roll and /r prefix stripping
  - [[inline roll]] extraction and resolution (iterative, inner-first for nested rolls)
  - ?{query|opt,val} parsing and substitution
  - @{attr} warning generation and stripping
  - &{template:...} warning generation and stripping
  - #macro-name warning generation and stripping

No Qt dependencies. All logic is pure Python with stdlib re only.
Designed for thorough unit testing (TDD).

Exports: MacroPreprocessor, QuerySpec, ParseWarning, CleanedMacro
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Optional

# ---------------------------------------------------------------------------
# Regex constants
# ---------------------------------------------------------------------------

# Strip /roll or /r prefix (case-insensitive), allowing leading whitespace
_ROLL_PREFIX_RE = re.compile(r"^\s*/r(?:oll)?\s+", re.IGNORECASE)

# Inline roll: [[...]] — uses [^\[\]] to match non-bracket content (innermost only)
# In iterative resolution, this will always find the innermost [[...]] first
_INLINE_ROLL_RE = re.compile(r"\[\[([^\[\]]+)\]\]")

# Query: ?{...} — matches the whole ?{...} token
_QUERY_RE = re.compile(r"\?\{([^}]+)\}")

# Unsupported: @{attr} references
_ATTR_RE = re.compile(r"@\{[^}]+\}")

# Unsupported: &{template:...} roll template references
_TEMPLATE_RE = re.compile(r"&\{template:[^}]+\}")

# Unsupported: #macro-name references
_MACRO_REF_RE = re.compile(r"#\w[\w-]*")


# ---------------------------------------------------------------------------
# Data classes
# ---------------------------------------------------------------------------

@dataclass
class QuerySpec:
    """A parsed ?{...} query token."""

    prompt: str                  # The prompt text shown to the user
    options: list[tuple[str, str]]  # (label, value) pairs; empty = free-text input
    raw: str                     # The original ?{...} token for substitution


@dataclass
class ParseWarning:
    """An unsupported Roll20 token that was stripped with a human-readable explanation."""

    token: str   # The matched token text, e.g. "@{target|ac}"
    reason: str  # Human-readable explanation


@dataclass
class CleanedMacro:
    """Result of preprocessing one raw macro line."""

    expression: str              # Expression ready for roll_expression() after query substitution
    queries: list[QuerySpec]     # ?{...} specs in left-to-right order; empty = no queries
    warnings: list[ParseWarning] # Warnings for stripped unsupported tokens
    is_empty: bool               # True if the original line was blank or whitespace-only
    template_name: str | None = None  # Name from {{name=...}} template field, if present


# ---------------------------------------------------------------------------
# MacroPreprocessor
# ---------------------------------------------------------------------------

class MacroPreprocessor:
    """
    Stateless text-transformation engine for Roll20 macro syntax.

    Call process_line() for each raw input line to get a CleanedMacro.
    Call resolve_inline_rolls() to evaluate [[...]] tokens in the expression.
    Call substitute_queries() to substitute ?{...} tokens with chosen values.
    """

    def process_line(self, raw_line: str) -> CleanedMacro:
        """
        Transform a raw macro line into a CleanedMacro.

        Steps:
        1. Strip /roll or /r prefix.
        2. Return is_empty=True for blank lines.
        3. Strip @{attr} tokens, emit ParseWarning for each.
        4. Strip &{template:...} tokens, emit ParseWarning for each.
        5. Strip #macro-name tokens, emit ParseWarning for each.
        6. Extract ?{query} specs into QuerySpec list (in order).
        7. Return CleanedMacro.

        Note: resolve_inline_rolls() is called separately (after process_line)
        because it needs a Roller and is not part of the initial parse pass.
        """
        line = _ROLL_PREFIX_RE.sub("", raw_line).strip()

        if not line:
            return CleanedMacro(expression="", queries=[], warnings=[], is_empty=True)

        warnings: list[ParseWarning] = []

        # --- Warn and strip @{attr} tokens ---
        for m in _ATTR_RE.finditer(line):
            warnings.append(ParseWarning(
                token=m.group(),
                reason="Attribute reference removed — expression may be incomplete",
            ))
        line = _ATTR_RE.sub("", line)

        # --- Warn and strip &{template:...} tokens ---
        for m in _TEMPLATE_RE.finditer(line):
            warnings.append(ParseWarning(
                token=m.group(),
                reason="Roll template removed — not supported",
            ))
        line = _TEMPLATE_RE.sub("", line)

        # --- Extract {{key=value}} template fields ---
        line, template_name = self._extract_template_fields(line)

        # --- Warn and strip #macro-name tokens ---
        for m in _MACRO_REF_RE.finditer(line):
            warnings.append(ParseWarning(
                token=m.group(),
                reason="Macro reference removed — nested macros are not supported",
            ))
        line = _MACRO_REF_RE.sub("", line)

        # --- Extract ?{query} specs (leave tokens in expression for later substitution) ---
        queries: list[QuerySpec] = []
        for m in _QUERY_RE.finditer(line):
            queries.append(self._parse_query(m.group(1), m.group()))

        # Strip leftover parentheses from template-wrapped expressions like ({{...}})
        stripped = line.strip()
        if template_name is not None and stripped in ("()", "(", ")"):
            line = ""

        return CleanedMacro(
            expression=line,
            queries=queries,
            warnings=warnings,
            is_empty=False,
            template_name=template_name,
        )

    def resolve_inline_rolls(
        self,
        expression: str,
        roller,
        seed: Optional[int] = None,
    ) -> tuple[str, list]:
        """
        Resolve all [[...]] inline rolls in the expression.

        Uses iterative inner-first resolution so that nested rolls like
        [[1d20+[[1d4]]]] are handled correctly: inner [[1d4]] is resolved
        first, then the outer [[1d20+N]] sees a plain integer.

        Returns
        -------
        (resolved_expr, inline_results)
            resolved_expr   : expression with all [[...]] replaced by integers
            inline_results  : list of (original_token_str, DiceResult) tuples
        """
        from src.engine.parser import roll_expression

        inline_results: list = []
        expr = expression

        while _INLINE_ROLL_RE.search(expr):
            # Find the leftmost innermost [[...]] (no nested [[ inside)
            m = _INLINE_ROLL_RE.search(expr)
            if m is None:
                break

            inner_expr = m.group(1)
            original_token = m.group(0)  # the full [[...]] text

            result = roll_expression(inner_expr, roller, seed)
            inline_results.append((original_token, result))

            # Replace only this one occurrence (leftmost)
            expr = expr[:m.start()] + str(result.total) + expr[m.end():]

        return expr, inline_results

    def substitute_queries(self, expression: str, answers: dict) -> str:
        """
        Substitute ?{...} tokens with the chosen values.

        Parameters
        ----------
        expression : str
            The expression string (may still contain ?{...} tokens).
        answers : dict
            Mapping of raw ?{...} token text -> chosen value string.
            e.g. {"?{Mod|STR,+2|DEX,+4}": "+2"}

        Returns
        -------
        str
            Expression with each matching token replaced by its chosen value.
            Double-sign normalization (++ -> +) is NOT done here — that is the
            service layer's responsibility.
        """
        for raw_token, value in answers.items():
            expression = expression.replace(raw_token, value, 1)
        return expression

    # ---------------------------------------------------------------------------
    # Private helpers
    # ---------------------------------------------------------------------------

    def _extract_template_fields(self, text: str) -> tuple[str, str | None]:
        """Extract ``{{key=value}}`` Roll20 template fields from the expression.

        Returns ``(cleaned_expression, template_name)``.

        - ``{{name=...}}`` is extracted as the template name and stripped entirely.
        - Other ``{{key=value}}`` fields have ``key=`` stripped; the value is kept
          so that inline rolls and queries within remain available for resolution.
        - ``{{bare_value}}`` (no ``=``) is kept as-is (e.g. ``{{?{query}}}``).
        - Correctly handles ``}}}`` where the first ``}`` closes an inner
          ``?{...}`` and the next ``}}`` closes the template field.
        """
        if "{{" not in text:
            return text, None

        template_name: str | None = None
        result_parts: list[str] = []
        last_end = 0
        i = 0

        while i < len(text) - 1:
            start = text.find("{{", i)
            if start == -1:
                break

            # Find closing }} — handle }}} by skipping a } that's followed by }}
            j = start + 2
            end = -1
            while j < len(text) - 1:
                if text[j] == "}" and text[j + 1] == "}":
                    # Is this really the closing }}?
                    if j + 2 >= len(text) or text[j + 2] != "}":
                        end = j
                        break
                    else:
                        # }}} — skip one } (it belongs to inner construct)
                        j += 1
                else:
                    j += 1

            if end == -1:
                # Fallback: check if string ends with }}
                if len(text) >= 2 and text[-2:] == "}}":
                    end = len(text) - 2
                else:
                    break

            content = text[start + 2 : end]

            # Keep any text before this field
            result_parts.append(text[last_end:start])

            # Parse field content
            if "=" in content:
                key, _, value = content.partition("=")
                if key.strip().lower() == "name":
                    template_name = value.strip()
                    # Name field is informational — don't add to expression
                else:
                    # Keep the value (may contain [[inline rolls]], ?{queries})
                    result_parts.append(" " + value.strip() + " ")
            else:
                # Bare value (e.g. ?{query} inside template field)
                result_parts.append(" " + content.strip() + " ")

            last_end = end + 2
            i = end + 2

        # Append any remaining text after the last field
        result_parts.append(text[last_end:])

        cleaned = " ".join(part.strip() for part in result_parts if part.strip())
        return cleaned, template_name

    def _parse_query(self, inner: str, raw: str) -> QuerySpec:
        """
        Parse the inner content of a ?{...} token into a QuerySpec.

        inner : the text between ?{ and }
        raw   : the full ?{...} token (for substitution reference)
        """
        parts = inner.split("|", 1)
        prompt = parts[0].strip()

        if len(parts) == 1:
            # Free-text query: ?{Prompt} with no options
            return QuerySpec(prompt=prompt, options=[], raw=raw)

        # Dropdown query: ?{Prompt|Label,Value|Label,Value|...}
        option_strs = parts[1].split("|")
        options: list[tuple[str, str]] = []
        for opt in option_strs:
            if "," in opt:
                label, value = opt.split(",", 1)
                options.append((label.strip(), value.strip()))
            else:
                # Label-only: use option text as both label and value
                options.append((opt.strip(), opt.strip()))

        return QuerySpec(prompt=prompt, options=options, raw=raw)
