"""
SpellcastingDetector — extract spellcasting info from Monster action traits.

Pure Python, no Qt. Parses action raw_text for casting ability, falls back to
highest mental stat (WIS, INT, CHA) when not found in text.
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field

from src.domain.models import Monster


# ---------------------------------------------------------------------------
# Ability name → abbreviation mapping
# ---------------------------------------------------------------------------

_ABILITY_NAME_TO_ABBR: dict[str, str] = {
    "strength": "STR",
    "dexterity": "DEX",
    "constitution": "CON",
    "intelligence": "INT",
    "wisdom": "WIS",
    "charisma": "CHA",
}

# Regex to capture a full ability name (word boundary, case-insensitive)
_ABILITY_RE = re.compile(
    r"\b(Strength|Dexterity|Constitution|Intelligence|Wisdom|Charisma)\b",
    re.IGNORECASE,
)

# Mental stats in priority order for fallback (highest score wins; tie → this order)
_MENTAL_STATS = ["WIS", "INT", "CHA"]


@dataclass
class SpellcastingInfo:
    """Result of detecting a spellcasting trait in a Monster's actions.

    NOTE: This is the runtime detection result used by the math engine.
    The domain model version (models.py) is for persistence serialization.
    Import this class for math operations.

    Attributes
    ----------
    trait_name : str
        Name of the spellcasting action (e.g. "Spellcasting", "Innate Spellcasting").
    casting_ability : str
        Uppercase abbreviation of the casting ability (e.g. "INT", "WIS", "CHA").
    is_assumed : bool
        True when casting_ability was inferred from highest mental stat (not explicit in text).
    focus_bonus : int
        Spellcasting focus bonus to add to attack/DC calculation (default 0).
    """
    trait_name: str
    casting_ability: str
    is_assumed: bool
    focus_bonus: int = 0


class SpellcastingDetector:
    """Detects and parses spellcasting traits from Monster actions."""

    def detect(self, monster: Monster) -> list[SpellcastingInfo]:
        """Scan monster.actions for spellcasting entries and extract casting ability.

        Parameters
        ----------
        monster : Monster
            The monster to inspect. Only `actions` and `ability_scores` are read.

        Returns
        -------
        list[SpellcastingInfo]
            One entry per detected spellcasting action. Empty list if none found.
        """
        results: list[SpellcastingInfo] = []

        for action in monster.actions:
            if "spellcasting" not in action.name.lower():
                continue

            casting_ability, is_assumed = self._extract_ability(
                action.raw_text, monster
            )
            results.append(
                SpellcastingInfo(
                    trait_name=action.name,
                    casting_ability=casting_ability,
                    is_assumed=is_assumed,
                )
            )

        return results

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _extract_ability(
        self, raw_text: str, monster: Monster
    ) -> tuple[str, bool]:
        """Extract casting ability from raw_text or fall back to highest mental stat.

        Returns
        -------
        (casting_ability, is_assumed)
        """
        match = _ABILITY_RE.search(raw_text)
        if match:
            ability_name = match.group(1).lower()
            abbr = _ABILITY_NAME_TO_ABBR.get(ability_name, "INT")
            return abbr, False

        # Fallback: highest mental stat by score
        best_abbr = "WIS"  # default if no mental stats in ability_scores
        best_score = -999
        for abbr in _MENTAL_STATS:
            score = monster.ability_scores.get(abbr, 0)
            if score > best_score:
                best_score = score
                best_abbr = abbr

        return best_abbr, True
