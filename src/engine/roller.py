"""
Roller: wraps a random.Random instance and produces DiceResult objects.

Design decisions:
- Roller holds only the random.Random instance; it does NOT store the seed integer.
  The seed is passed separately to roll_expression() for the DiceResult audit trail.
- All random calls go through self._rng.randint — never bare random.randint.
  This prevents global RNG state contamination and enables seeded determinism.
- Keep-highest ('kh'): sort all faces descending, mark the first keep_count as kept.
- Keep-lowest ('kl'): sort all faces ascending, mark the first keep_count as kept.
- Total = sum of kept face values only.
"""
from __future__ import annotations

import random
from typing import Optional

from src.engine.models import DiceResult, DieFace


class Roller:
    """Wraps a random.Random instance for isolated, seeded die rolling."""

    def __init__(self, rng: random.Random) -> None:
        self._rng = rng

    def roll_one(self, sides: int) -> int:
        """Roll a single die with the given number of sides. Returns 1..sides."""
        return self._rng.randint(1, sides)

    def roll_dice(
        self,
        n_dice: int,
        sides: int,
        keep_type: Optional[str],
        keep_count: int,
        seed: Optional[int] = None,
    ) -> DiceResult:
        """
        Roll n_dice dice with the given number of sides and apply keep modifiers.

        Parameters
        ----------
        n_dice     : number of dice to roll
        sides      : number of sides per die
        keep_type  : None (keep all), 'kh' (keep highest N), or 'kl' (keep lowest N)
        keep_count : number of dice to keep (ignored when keep_type is None)
        seed       : passed through to DiceResult.seed for audit trail only

        Returns
        -------
        DiceResult with all faces (kept and dropped) and total = sum of kept faces.
        """
        raw_values = [self._rng.randint(1, sides) for _ in range(n_dice)]

        if keep_type is None:
            # Keep all dice
            faces = tuple(DieFace(value=v, sides=sides, kept=True) for v in raw_values)
            total = sum(f.value for f in faces)
        elif keep_type == "kh":
            # Keep the highest keep_count dice
            # Sort indices by value descending; first keep_count are kept
            indexed = sorted(range(n_dice), key=lambda i: raw_values[i], reverse=True)
            kept_indices = set(indexed[:keep_count])
            faces = tuple(
                DieFace(value=raw_values[i], sides=sides, kept=(i in kept_indices))
                for i in range(n_dice)
            )
            total = sum(f.value for f in faces if f.kept)
        elif keep_type == "kl":
            # Keep the lowest keep_count dice
            # Sort indices by value ascending; first keep_count are kept
            indexed = sorted(range(n_dice), key=lambda i: raw_values[i])
            kept_indices = set(indexed[:keep_count])
            faces = tuple(
                DieFace(value=raw_values[i], sides=sides, kept=(i in kept_indices))
                for i in range(n_dice)
            )
            total = sum(f.value for f in faces if f.kept)
        else:
            raise ValueError(f"Unknown keep_type: {keep_type!r}")

        return DiceResult(
            total=total,
            faces=faces,
            expression="",
            seed=seed,
            constant_bonus=0,
        )
