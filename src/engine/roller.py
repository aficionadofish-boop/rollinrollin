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

Extended features:
- Exploding dice (!): if a die hits max, roll again and add. Chains. Cap at 100.
- Success counting (>N / <N): total = count of faces passing threshold.
- Critical marking (cs>N): mark faces >= N as critical (display only).
"""
from __future__ import annotations

import random
from typing import Optional

from src.engine.models import DiceResult, DieFace

_MAX_EXPLOSIONS = 100


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
        keep_type: Optional[str] = None,
        keep_count: int = 0,
        seed: Optional[int] = None,
        *,
        explode: bool = False,
        success_op: Optional[str] = None,
        success_threshold: Optional[int] = None,
        crit_op: Optional[str] = None,
        crit_threshold: Optional[int] = None,
    ) -> DiceResult:
        """
        Roll n_dice dice with the given number of sides and apply modifiers.

        Parameters
        ----------
        n_dice     : number of dice to roll
        sides      : number of sides per die
        keep_type  : None (keep all), 'kh' (keep highest N), or 'kl' (keep lowest N)
        keep_count : number of dice to keep (ignored when keep_type is None)
        seed       : passed through to DiceResult.seed for audit trail only
        explode    : if True, dice that roll max explode (reroll and add)
        success_op : ">" or "<" for success counting (total = count of passes)
        success_threshold : threshold for success counting
        crit_op    : "cs>" for critical success marking (display only)
        crit_threshold : threshold for critical marking (>= comparison)

        Returns
        -------
        DiceResult with all faces (kept and dropped) and total.
        """
        # Phase 1: Roll initial dice
        raw_values = [self._rng.randint(1, sides) for _ in range(n_dice)]
        is_exploded = [False] * n_dice

        # Phase 2: Exploding dice
        if explode:
            explosion_count = 0
            check_idx = 0
            while check_idx < len(raw_values) and explosion_count < _MAX_EXPLOSIONS:
                if raw_values[check_idx] == sides:
                    new_val = self._rng.randint(1, sides)
                    raw_values.append(new_val)
                    is_exploded.append(True)
                    explosion_count += 1
                check_idx += 1

        # Phase 3: Keep modifiers (operate on full pool including explosions)
        actual_count = len(raw_values)

        if keep_type is None:
            faces = tuple(
                DieFace(value=raw_values[i], sides=sides, kept=True,
                        exploded=is_exploded[i])
                for i in range(actual_count)
            )
            total = sum(f.value for f in faces)
        elif keep_type == "kh":
            indexed = sorted(range(actual_count), key=lambda i: raw_values[i], reverse=True)
            kept_indices = set(indexed[:keep_count])
            faces = tuple(
                DieFace(value=raw_values[i], sides=sides, kept=(i in kept_indices),
                        exploded=is_exploded[i])
                for i in range(actual_count)
            )
            total = sum(f.value for f in faces if f.kept)
        elif keep_type == "kl":
            indexed = sorted(range(actual_count), key=lambda i: raw_values[i])
            kept_indices = set(indexed[:keep_count])
            faces = tuple(
                DieFace(value=raw_values[i], sides=sides, kept=(i in kept_indices),
                        exploded=is_exploded[i])
                for i in range(actual_count)
            )
            total = sum(f.value for f in faces if f.kept)
        else:
            raise ValueError(f"Unknown keep_type: {keep_type!r}")

        # Phase 4: Success counting (overrides kept flags and total)
        if success_op is not None and success_threshold is not None:
            new_faces = []
            success_count = 0
            for f in faces:
                if success_op == ">" and f.value > success_threshold:
                    new_faces.append(DieFace(value=f.value, sides=f.sides, kept=True,
                                             exploded=f.exploded))
                    success_count += 1
                elif success_op == "<" and f.value < success_threshold:
                    new_faces.append(DieFace(value=f.value, sides=f.sides, kept=True,
                                             exploded=f.exploded))
                    success_count += 1
                else:
                    new_faces.append(DieFace(value=f.value, sides=f.sides, kept=False,
                                             exploded=f.exploded))
            faces = tuple(new_faces)
            total = success_count

        # Phase 5: Critical marking (display only — does NOT change total)
        if crit_op == "cs>" and crit_threshold is not None:
            new_faces = []
            for f in faces:
                if f.value >= crit_threshold:
                    new_faces.append(DieFace(value=f.value, sides=f.sides, kept=f.kept,
                                             exploded=f.exploded, critical=True))
                else:
                    new_faces.append(f)
            faces = tuple(new_faces)

        return DiceResult(
            total=total,
            faces=faces,
            expression="",
            seed=seed,
            constant_bonus=0,
        )
