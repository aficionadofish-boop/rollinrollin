"""
MonsterMathEngine — pure-Python derived stat calculation for D&D 5e monsters.

No Qt dependencies. Pure function design: recalculate() never mutates input.
"""
from __future__ import annotations

from dataclasses import dataclass, field

from src.domain.models import Monster


# ---------------------------------------------------------------------------
# Proficiency bonus table indexed by CR string
# ---------------------------------------------------------------------------

_PROF_BY_CR: dict[str, int] = {
    "0": 2,
    "1/8": 2,
    "1/4": 2,
    "1/2": 2,
    "1": 2,
    "2": 2,
    "3": 2,
    "4": 2,
    "5": 3,
    "6": 3,
    "7": 3,
    "8": 3,
    "9": 4,
    "10": 4,
    "11": 4,
    "12": 4,
    "13": 5,
    "14": 5,
    "15": 5,
    "16": 5,
    "17": 6,
    "18": 6,
    "19": 6,
    "20": 6,
    "21": 7,
    "22": 7,
    "23": 7,
    "24": 7,
    "25": 8,
    "26": 8,
    "27": 8,
    "28": 8,
    "29": 9,
    "30": 9,
}


def _ability_mod(score: int) -> int:
    """Compute 5e ability modifier using floor division.

    Correct for negative scores: (8-10)//2 = -1, not int(-2/2) = -1 (same
    result for -2, but for -1: (-1-10)//2 = -6 vs. -5.5 truncated to -5).
    Python's // always floors, matching D&D 5e rules.
    """
    return (score - 10) // 2


@dataclass
class DerivedStats:
    """Derived mathematical stats for a Monster.

    All dictionaries use uppercase ability abbreviations as keys:
    {"STR", "DEX", "CON", "INT", "WIS", "CHA"}
    """
    proficiency_bonus: int
    ability_modifiers: dict[str, int] = field(default_factory=dict)
    # Non-proficient baseline: ability modifier only
    expected_saves: dict[str, int] = field(default_factory=dict)
    # Proficient save: mod + proficiency_bonus
    expected_proficient_saves: dict[str, int] = field(default_factory=dict)
    # Expertise save: mod + 2 * proficiency_bonus
    expected_expertise_saves: dict[str, int] = field(default_factory=dict)


class MonsterMathEngine:
    """Calculates derived stats from a Monster's base attributes.

    Pure calculation engine — no state, no Qt, no I/O.
    """

    def recalculate(self, monster: Monster) -> DerivedStats:
        """Return DerivedStats computed from monster's CR and ability scores.

        Parameters
        ----------
        monster : Monster
            Source monster. Never mutated.

        Returns
        -------
        DerivedStats
            Complete derived stat block.
        """
        # Use manual override if set, otherwise derive from CR
        if getattr(monster, "proficiency_bonus", None) is not None:
            prof = monster.proficiency_bonus
        else:
            prof = _PROF_BY_CR.get(monster.cr, 2)  # default 2 for unknown CRs

        ability_modifiers: dict[str, int] = {}
        expected_saves: dict[str, int] = {}
        expected_proficient_saves: dict[str, int] = {}
        expected_expertise_saves: dict[str, int] = {}

        for ability, score in monster.ability_scores.items():
            mod = _ability_mod(score)
            ability_modifiers[ability] = mod
            expected_saves[ability] = mod
            expected_proficient_saves[ability] = mod + prof
            expected_expertise_saves[ability] = mod + 2 * prof

        return DerivedStats(
            proficiency_bonus=prof,
            ability_modifiers=ability_modifiers,
            expected_saves=expected_saves,
            expected_proficient_saves=expected_proficient_saves,
            expected_expertise_saves=expected_expertise_saves,
        )
