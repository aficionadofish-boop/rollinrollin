"""
RollService: the pure-Python D&D 5e rule translation layer.

Translates RollRequest (toggle state + monster action) into concrete dice
engine calls and returns a RollResult containing AttackRollResult objects.

All 5e rule logic lives here:
- Advantage/disadvantage → 2d20kh1 / 2d20kl1 / 1d20
- Crit detection (natural >= crit_range)
- Crit damage doubling (_double_dice utility)
- Nat-1 always miss / nat-20 always hit overrides
- Flat modifier + bonus dice accumulation
- Hit/miss determination in COMPARE mode
- Damage gating (miss in COMPARE = no damage rolled)

The dice engine (src.engine.parser) knows NONE of these rules — it only
evaluates concrete dice expressions.
"""
from __future__ import annotations

import re
from typing import Optional

from src.engine.parser import roll_expression
from src.engine.roller import Roller
from src.roll.models import (
    AttackRollResult,
    BonusDiceEntry,
    DamagePartResult,
    RollRequest,
    RollResult,
    RollSummary,
)


# ---------------------------------------------------------------------------
# Public utility
# ---------------------------------------------------------------------------

_DICE_COUNT_RE = re.compile(r"^(\d+)(d\d+)", re.IGNORECASE)


def _extract_dice_part(expr: str) -> str | None:
    """Extract just the 'NdM' prefix from an expression.

    Returns None for pure constants (no dice component).

    Examples
    --------
    "1d6+3"  -> "1d6"
    "2d8"    -> "2d8"
    "3"      -> None
    """
    m = _DICE_COUNT_RE.match(expr)
    return f"{m.group(1)}{m.group(2)}" if m else None


def _maximize_expr(expr: str) -> int:
    """Compute the maximum possible value of a dice expression.

    Examples
    --------
    "2d6+3"  -> 15  (2*6 + 3)
    "1d8"    -> 8
    "1d8-1"  -> 7
    "3"      -> 3
    """
    m = _DICE_COUNT_RE.match(expr)
    if not m:
        try:
            return int(expr.strip())
        except ValueError:
            return 0
    count = int(m.group(1))
    die_size = int(m.group(2)[1:])  # strip leading 'd'
    max_dice = count * die_size
    remainder = expr[m.end():]
    if remainder:
        const_m = re.match(r"([+-]\d+)", remainder.strip())
        if const_m:
            return max_dice + int(const_m.group(1))
    return max_dice


def _double_dice(expr: str) -> str:
    """Double the dice count in a dice expression for crit damage.

    Only the leading NdM prefix is doubled; constant bonuses are unchanged.

    Examples
    --------
    "2d6+3"  -> "4d6+3"   (constant NOT doubled)
    "1d8"    -> "2d8"
    "3"      -> "3"        (pure constant — unchanged)
    "1d8-1"  -> "2d8-1"   (negative constant not doubled)
    "3d6"    -> "6d6"
    """
    return _DICE_COUNT_RE.sub(
        lambda m: f"{int(m.group(1)) * 2}{m.group(2)}", expr, count=1
    )


# ---------------------------------------------------------------------------
# RollService
# ---------------------------------------------------------------------------


class RollService:
    """Translates D&D 5e RollRequest into dice engine calls and returns RollResult."""

    def execute_attack_roll(self, request: RollRequest, roller: Roller) -> RollResult:
        """
        Execute N attack rolls as specified by request.

        Parameters
        ----------
        request : RollRequest
            All toggle state, monster action info, and roll configuration.
        roller : Roller
            Shared roller instance (pre-seeded by the caller if determinism needed).

        Returns
        -------
        RollResult
            Contains one AttackRollResult per attack plus a RollSummary.
        """
        attack_rolls = []
        for i in range(request.count):
            attack_roll = self._roll_one_attack(request, roller, i + 1)
            attack_rolls.append(attack_roll)
        summary = self._build_summary(request, attack_rolls)
        return RollResult(request=request, attack_rolls=attack_rolls, summary=summary)

    # ------------------------------------------------------------------
    # Internal: single attack
    # ------------------------------------------------------------------

    def _roll_one_attack(
        self,
        request: RollRequest,
        roller: Roller,
        attack_number: int,
    ) -> AttackRollResult:
        # 1. Roll d20 — translate advantage mode into concrete dice expression
        if request.advantage == "advantage":
            d20_result = roll_expression("2d20kh1", roller, request.seed)
        elif request.advantage == "disadvantage":
            d20_result = roll_expression("2d20kl1", roller, request.seed)
        else:
            d20_result = roll_expression("1d20", roller, request.seed)

        # 2. Find natural value of the kept die.
        #    NEVER use d20_result.total for nat-1/nat-20 check — it is the
        #    mathematical total (same as kept face value for a single die, but
        #    must be verified from the face for correctness and clarity).
        kept_face = next(f for f in d20_result.faces if f.kept)
        natural = kept_face.value

        # 3. Nat-1 / nat-20 flags
        is_nat1 = natural == 1
        is_nat20 = natural == 20

        # 4. Crit detection (before hit/miss so crit flag flows into damage)
        is_crit = request.crit_enabled and natural >= request.crit_range

        # 5. Evaluate bonus dice
        #    Strip leading '+' before passing to roll_expression (Pitfall 5).
        #    Detect negative from formula.startswith('-').
        bonus_total = 0
        bonus_dice_results: list = []
        for entry in request.bonus_dice:
            formula_clean = entry.formula.lstrip("+")
            b_result = roll_expression(formula_clean, roller, request.seed)
            # Determine sign from original formula
            sign = -1 if entry.formula.startswith("-") else 1
            signed_total = sign * b_result.total
            bonus_total += signed_total
            bonus_dice_results.append((entry.formula, signed_total, entry.label))

        # 6. Compute attack total (integer arithmetic — NEVER concatenate to_hit_bonus
        #    into the dice expression string, see Pitfall 7)
        attack_total = (
            d20_result.total
            + request.to_hit_bonus
            + request.flat_modifier
            + bonus_total
        )

        # 7. Determine hit/miss (COMPARE mode only)
        #    Priority: nat-1 override → nat-20 override → general comparison
        is_hit: Optional[bool]
        if request.mode == "compare":
            if request.nat1_always_miss and is_nat1:
                is_hit = False
            elif request.nat20_always_hit and is_nat20:
                is_hit = True
            else:
                is_hit = attack_total >= (request.target_ac or 0)
        else:
            is_hit = None  # RAW mode — no hit/miss concept

        # 8. Roll damage (always in RAW; only on hit in COMPARE)
        damage_parts: list[DamagePartResult] = []
        crit_extra_parts: list[DamagePartResult] = []
        if request.mode == "raw" or is_hit is True:
            for dp in request.damage_parts:
                if is_crit:
                    dice_part = _extract_dice_part(dp.dice_expr)  # e.g. "1d6" from "1d6+3"
                    if request.brutal_crits:
                        # Maximize both base and extra dice — no rolls needed
                        base_total = _maximize_expr(dp.dice_expr)
                        damage_parts.append(DamagePartResult(
                            total=base_total,
                            damage_type=dp.damage_type,
                            dice_expr=dp.dice_expr,
                            faces=(),
                        ))
                        if dice_part:
                            extra_total = _maximize_expr(dice_part)
                            crit_extra_parts.append(DamagePartResult(
                                total=extra_total,
                                damage_type=dp.damage_type,
                                dice_expr=dice_part,
                                faces=(),
                            ))
                    elif request.crunchy_crits:
                        # Maximize base dice, roll extra dice normally
                        base_total = _maximize_expr(dp.dice_expr)
                        damage_parts.append(DamagePartResult(
                            total=base_total,
                            damage_type=dp.damage_type,
                            dice_expr=dp.dice_expr,
                            faces=(),
                        ))
                        if dice_part:
                            extra_result = roll_expression(dice_part, roller, request.seed)
                            crit_extra_parts.append(DamagePartResult(
                                total=extra_result.total,
                                damage_type=dp.damage_type,
                                dice_expr=dice_part,
                                faces=extra_result.faces,
                            ))
                    else:
                        # Standard crit: roll base expression, then roll extra dice separately
                        base_result = roll_expression(dp.dice_expr, roller, request.seed)
                        damage_parts.append(DamagePartResult(
                            total=base_result.total,
                            damage_type=dp.damage_type,
                            dice_expr=dp.dice_expr,
                            faces=base_result.faces,
                        ))
                        if dice_part:
                            extra_result = roll_expression(dice_part, roller, request.seed)
                            crit_extra_parts.append(DamagePartResult(
                                total=extra_result.total,
                                damage_type=dp.damage_type,
                                dice_expr=dice_part,
                                faces=extra_result.faces,
                            ))
                else:
                    dmg_result = roll_expression(dp.dice_expr, roller, request.seed)
                    damage_parts.append(DamagePartResult(
                        total=dmg_result.total,
                        damage_type=dp.damage_type,
                        dice_expr=dp.dice_expr,
                        faces=dmg_result.faces,
                    ))

        # 8b. Roll damage bonus dice (buff damage — only when damage is dealt)
        damage_bonus_results: list = []
        if damage_parts and request.damage_bonus_dice:
            for entry in request.damage_bonus_dice:
                formula_clean = entry.formula.lstrip("+")
                dmg_b_result = roll_expression(formula_clean, roller, request.seed)
                sign = -1 if entry.formula.startswith("-") else 1
                signed_total = sign * dmg_b_result.total
                damage_bonus_results.append((entry.formula, signed_total, entry.label))

        # 9. Margin (COMPARE + show_margin only)
        margin: Optional[int] = None
        if request.mode == "compare" and request.show_margin:
            margin = attack_total - (request.target_ac or 0)

        return AttackRollResult(
            attack_number=attack_number,
            d20_faces=d20_result.faces,
            d20_natural=natural,
            attack_total=attack_total,
            to_hit_bonus=request.to_hit_bonus,
            flat_modifier=request.flat_modifier,
            bonus_dice_results=bonus_dice_results,
            is_hit=is_hit,
            is_crit=is_crit,
            is_nat1=is_nat1,
            is_nat20=is_nat20,
            damage_parts=damage_parts,
            margin=margin,
            crit_extra_parts=crit_extra_parts,
            damage_bonus_results=damage_bonus_results,
        )

    # ------------------------------------------------------------------
    # Internal: summary
    # ------------------------------------------------------------------

    def _build_summary(
        self, request: RollRequest, attack_rolls: list[AttackRollResult]
    ) -> RollSummary:
        hits = sum(1 for r in attack_rolls if r.is_hit is True)
        misses = sum(1 for r in attack_rolls if r.is_hit is False)
        crits = sum(1 for r in attack_rolls if r.is_crit)
        total_damage = (
            sum(dp.total for r in attack_rolls for dp in r.damage_parts)
            + sum(ep.total for r in attack_rolls for ep in r.crit_extra_parts)
            + sum(db[1] for r in attack_rolls for db in r.damage_bonus_results)
        )
        return RollSummary(
            total_attacks=len(attack_rolls),
            hits=hits,
            misses=misses,
            crits=crits,
            total_damage=total_damage,
        )
