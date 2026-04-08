from __future__ import annotations
import random
from .models import DieResult, MegaDieResult, WodRollResult, AberrantRollResult


class StorytellerEngine:
    """Qt-free dice engine for World of Darkness and Aberrant systems.

    Takes a random.Random instance in the constructor (matches Roller pattern)
    so callers can inject a seeded RNG for deterministic testing.
    """

    def __init__(self, rng: random.Random | None = None) -> None:
        self._rng = rng or random.Random()

    # ------------------------------------------------------------------
    # World of Darkness
    # ------------------------------------------------------------------

    def roll_wod(
        self,
        pool: int,
        difficulty: int,
        reroll_threshold: int | None = None,
        rote_enabled: bool = False,
    ) -> WodRollResult:
        """Roll a WoD dice pool.

        Args:
            pool: Number of d10s to roll.
            difficulty: Target number for a success (value >= difficulty).
            reroll_threshold: If set (8 or 9), dice meeting or exceeding this
                value are re-rolled and added to the pool (8-again / 9-again).
            rote_enabled: If True, non-success non-1 dice are re-rolled once
                (rote quality). Rote dice that meet reroll_threshold then enter
                the normal chain.
        """
        all_dice: list[DieResult] = []

        # --- Step 1: Roll initial pool ---
        initial_batch = self._roll_batch(pool, difficulty, is_reroll=False)
        all_dice.extend(initial_batch)
        latest_batch = initial_batch

        # --- Step 2: Rote pass (if enabled) ---
        if rote_enabled:
            # Re-roll dice that are not a success and not showing 1
            rote_dice = [
                d for d in latest_batch if not d.is_success and not d.is_one
            ]
            if rote_dice:
                rote_batch = self._roll_batch(len(rote_dice), difficulty, is_reroll=True)
                all_dice.extend(rote_batch)
                # Rote batch becomes the "latest batch" for the threshold chain
                latest_batch = rote_batch

        # --- Step 3: 8-again / 9-again chain ---
        if reroll_threshold is not None:
            iterations = 0
            while iterations < 50:
                qualifying = [d for d in latest_batch if d.value >= reroll_threshold]
                if not qualifying:
                    break
                new_batch = self._roll_batch(len(qualifying), difficulty, is_reroll=True)
                all_dice.extend(new_batch)
                latest_batch = new_batch
                iterations += 1

        # --- Step 4: Compute totals ---
        raw_successes = sum(1 for d in all_dice if d.is_success)
        ones_count = sum(1 for d in all_dice if d.is_one and not d.is_success)
        net_successes = raw_successes - ones_count
        is_botch = net_successes < 0
        is_exceptional = net_successes >= 5

        return WodRollResult(
            dice=all_dice,
            net_successes=net_successes,
            raw_successes=raw_successes,
            ones_count=ones_count,
            is_botch=is_botch,
            is_exceptional=is_exceptional,
            reroll_threshold=reroll_threshold,
            rote_enabled=rote_enabled,
            pool=pool,
            difficulty=difficulty,
        )

    def _roll_batch(
        self, count: int, difficulty: int, *, is_reroll: bool
    ) -> list[DieResult]:
        """Roll `count` d10s and return DieResult objects."""
        results = []
        for _ in range(count):
            value = self._rng.randint(1, 10)
            is_success = value >= difficulty
            is_one = value == 1
            results.append(
                DieResult(
                    value=value,
                    is_success=is_success,
                    is_one=is_one,
                    is_reroll=is_reroll,
                )
            )
        return results

    # ------------------------------------------------------------------
    # Aberrant
    # ------------------------------------------------------------------

    def roll_aberrant(
        self,
        pool: int,
        mega_pool: int,
        auto_successes: int,
        successes_required: int,
    ) -> AberrantRollResult:
        """Roll an Aberrant dice pool.

        Normal dice: success on value >= 7, is_one on value == 1.
        Mega dice: 10 -> 3 successes, 7-9 -> 2 successes, else 0; is_one on value == 1.

        CRITICAL: Aberrant 1s NEVER cancel successes. The botch check is
        purely (total_successes == 0 AND any die shows 1).
        """
        # Roll normal dice
        normal_dice: list[DieResult] = []
        for _ in range(pool):
            value = self._rng.randint(1, 10)
            normal_dice.append(
                DieResult(
                    value=value,
                    is_success=value >= 7,
                    is_one=value == 1,
                )
            )

        # Roll mega dice
        mega_dice: list[MegaDieResult] = []
        for _ in range(mega_pool):
            value = self._rng.randint(1, 10)
            if value == 10:
                sux_count = 3
            elif value >= 7:
                sux_count = 2
            else:
                sux_count = 0
            mega_dice.append(
                MegaDieResult(
                    value=value,
                    sux_count=sux_count,
                    is_one=value == 1,
                )
            )

        # Compute totals
        normal_sux = sum(1 for d in normal_dice if d.is_success)
        mega_sux = sum(d.sux_count for d in mega_dice)
        total_successes = auto_successes + normal_sux + mega_sux

        any_one = any(d.is_one for d in normal_dice) or any(d.is_one for d in mega_dice)
        is_botch = (total_successes == 0 and any_one)

        # Success tier
        if total_successes == 0:
            success_tier = "none"
        elif total_successes >= 13:
            success_tier = "13-16"
        elif total_successes >= 9:
            success_tier = "9-12"
        elif total_successes >= 5:
            success_tier = "5-8"
        else:
            success_tier = "1-4"

        return AberrantRollResult(
            normal_dice=normal_dice,
            mega_dice=mega_dice,
            auto_successes=auto_successes,
            total_successes=total_successes,
            is_botch=is_botch,
            success_tier=success_tier,
            pool=pool,
            mega_pool=mega_pool,
            successes_required=successes_required,
        )
