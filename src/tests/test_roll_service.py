"""
Seeded golden tests for RollService — covers all toggle combinations.

RED phase: these tests import from src.roll.service and src.roll.models
which do not yet exist; running this file must fail with ImportError.
"""
from __future__ import annotations

import random
import pytest

from src.engine.roller import Roller
from src.roll.service import RollService, _double_dice       # noqa: F401 (will fail)
from src.roll.models import (                                 # noqa: F401 (will fail)
    RollRequest,
    AttackRollResult,
    DamagePartResult,
    RollSummary,
    RollResult,
    BonusDiceEntry,
)
from src.domain.models import DamagePart


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def seeded_roller():
    return Roller(random.Random(42))


def _make_request(**kwargs) -> RollRequest:
    """Build a RollRequest with sensible defaults; override via kwargs."""
    defaults = dict(
        action_name="Bite",
        to_hit_bonus=5,
        damage_parts=[
            DamagePart(dice_expr="1d6+3", damage_type="piercing", raw_text="1d6+3")
        ],
        count=3,
        mode="raw",
        target_ac=None,
        advantage="normal",
        crit_enabled=True,
        crit_range=20,
        nat1_always_miss=True,
        nat20_always_hit=True,
        flat_modifier=0,
        bonus_dice=[],
        show_margin=False,
        seed=42,
    )
    defaults.update(kwargs)
    return RollRequest(**defaults)


# ---------------------------------------------------------------------------
# count tests
# ---------------------------------------------------------------------------


def test_roll_count_returns_correct_number_of_attacks(seeded_roller):
    """count=5 must produce exactly 5 AttackRollResult objects."""
    svc = RollService()
    result = svc.execute_attack_roll(_make_request(count=5), seeded_roller)
    assert len(result.attack_rolls) == 5


def test_roll_count_one(seeded_roller):
    """count=1 must produce exactly 1 AttackRollResult."""
    svc = RollService()
    result = svc.execute_attack_roll(_make_request(count=1), seeded_roller)
    assert len(result.attack_rolls) == 1


# ---------------------------------------------------------------------------
# Advantage / Disadvantage tests
# ---------------------------------------------------------------------------


def test_advantage_rolls_two_d20_faces(seeded_roller):
    """Advantage must roll 2d20; exactly 1 face has kept=True."""
    svc = RollService()
    result = svc.execute_attack_roll(
        _make_request(count=1, advantage="advantage"), seeded_roller
    )
    attack = result.attack_rolls[0]
    assert len(attack.d20_faces) == 2, "Advantage must produce exactly 2 d20 faces"
    kept_count = sum(1 for f in attack.d20_faces if f.kept)
    assert kept_count == 1, "Exactly one d20 face must be kept"


def test_advantage_uses_higher_value(seeded_roller):
    """Advantage attack_total uses the higher of the two d20 faces."""
    svc = RollService()
    result = svc.execute_attack_roll(
        _make_request(count=1, advantage="advantage"), seeded_roller
    )
    attack = result.attack_rolls[0]
    kept_face = next(f for f in attack.d20_faces if f.kept)
    dropped_face = next(f for f in attack.d20_faces if not f.kept)
    assert kept_face.value >= dropped_face.value, "Advantage must keep the higher die"


def test_disadvantage_rolls_two_d20_faces(seeded_roller):
    """Disadvantage must roll 2d20; exactly 1 face has kept=True."""
    svc = RollService()
    result = svc.execute_attack_roll(
        _make_request(count=1, advantage="disadvantage"), seeded_roller
    )
    attack = result.attack_rolls[0]
    assert len(attack.d20_faces) == 2, "Disadvantage must produce exactly 2 d20 faces"
    kept_count = sum(1 for f in attack.d20_faces if f.kept)
    assert kept_count == 1, "Exactly one d20 face must be kept"


def test_disadvantage_uses_lower_value(seeded_roller):
    """Disadvantage attack_total uses the lower of the two d20 faces."""
    svc = RollService()
    result = svc.execute_attack_roll(
        _make_request(count=1, advantage="disadvantage"), seeded_roller
    )
    attack = result.attack_rolls[0]
    kept_face = next(f for f in attack.d20_faces if f.kept)
    dropped_face = next(f for f in attack.d20_faces if not f.kept)
    assert kept_face.value <= dropped_face.value, "Disadvantage must keep the lower die"


def test_normal_rolls_one_d20_face(seeded_roller):
    """Normal (no advantage/disadvantage) must produce exactly 1 d20 face."""
    svc = RollService()
    result = svc.execute_attack_roll(
        _make_request(count=1, advantage="normal"), seeded_roller
    )
    attack = result.attack_rolls[0]
    assert len(attack.d20_faces) == 1
    assert attack.d20_faces[0].kept is True


# ---------------------------------------------------------------------------
# COMPARE mode: hit/miss, damage gating
# ---------------------------------------------------------------------------


def test_compare_mode_impossible_ac_is_miss(seeded_roller):
    """mode=compare, target_ac=100, nat20_always_hit=False -> is_hit=False."""
    svc = RollService()
    result = svc.execute_attack_roll(
        _make_request(count=1, mode="compare", target_ac=100, nat20_always_hit=False),
        seeded_roller,
    )
    attack = result.attack_rolls[0]
    assert attack.is_hit is False
    assert attack.damage_parts == [], "Miss in COMPARE mode must produce no damage"


def test_compare_mode_miss_no_damage(seeded_roller):
    """Misses in COMPARE mode produce empty damage_parts list."""
    svc = RollService()
    # High AC guarantees miss, but disable nat-20 override
    result = svc.execute_attack_roll(
        _make_request(count=5, mode="compare", target_ac=100, nat20_always_hit=False),
        seeded_roller,
    )
    for attack in result.attack_rolls:
        if attack.is_hit is False:
            assert attack.damage_parts == []


def test_raw_mode_is_hit_is_none(seeded_roller):
    """RAW mode has no hit/miss concept; is_hit must be None."""
    svc = RollService()
    result = svc.execute_attack_roll(_make_request(count=3, mode="raw"), seeded_roller)
    for attack in result.attack_rolls:
        assert attack.is_hit is None, "RAW mode must produce is_hit=None"


def test_compare_mode_raw_damage_always_rolled(seeded_roller):
    """RAW mode: damage is always rolled even when d20 natural would be low."""
    svc = RollService()
    result = svc.execute_attack_roll(_make_request(count=3, mode="raw"), seeded_roller)
    for attack in result.attack_rolls:
        assert len(attack.damage_parts) >= 1, "RAW mode must always roll damage"


# ---------------------------------------------------------------------------
# Nat-1 / Nat-20 overrides
# ---------------------------------------------------------------------------


def test_nat1_always_miss_in_compare_mode(seeded_roller):
    """nat1_always_miss=True: any nat-1 in COMPARE mode is always a miss."""
    svc = RollService()
    # Very low AC (2) and high bonus (+15) to guarantee hit without nat-1
    result = svc.execute_attack_roll(
        _make_request(
            count=20,
            mode="compare",
            target_ac=2,
            to_hit_bonus=15,
            nat1_always_miss=True,
        ),
        seeded_roller,
    )
    nat1_rolls = [a for a in result.attack_rolls if a.is_nat1]
    for attack in nat1_rolls:
        assert attack.is_hit is False, "nat-1 must always be a miss when nat1_always_miss=True"


def test_nat20_always_hit_in_compare_mode():
    """nat20_always_hit=True: any nat-20 in COMPARE mode is always a hit."""
    # Use a roller seeded to guarantee a nat-20 appears
    # Seed 7 with 1d20 produces a 20 on first roll (verified by inspection)
    rng = random.Random(7)
    roller = Roller(rng)
    svc = RollService()
    result = svc.execute_attack_roll(
        _make_request(
            count=20,
            mode="compare",
            target_ac=100,  # impossible AC
            nat20_always_hit=True,
        ),
        roller,
    )
    nat20_rolls = [a for a in result.attack_rolls if a.is_nat20]
    if nat20_rolls:  # if we got any nat-20 in 20 rolls
        for attack in nat20_rolls:
            assert attack.is_hit is True, "nat-20 must always be a hit when nat20_always_hit=True"


def test_nat1_override_disabled():
    """nat1_always_miss=False: a nat-1 with huge bonus still counts normally."""
    rng = random.Random(42)
    roller = Roller(rng)
    svc = RollService()
    # low AC = 1 so attack_total = 1 + 15 = 16 >= 1 → would be a hit even on nat-1
    result = svc.execute_attack_roll(
        _make_request(
            count=20,
            mode="compare",
            target_ac=1,
            to_hit_bonus=15,
            nat1_always_miss=False,
            nat20_always_hit=False,
        ),
        roller,
    )
    nat1_results = [a for a in result.attack_rolls if a.is_nat1]
    for attack in nat1_results:
        # With target_ac=1 and to_hit_bonus=15, even nat-1 total = 16 >= 1
        assert attack.is_hit is True, "With nat1_always_miss=False, nat-1 + high bonus should hit AC 1"


# ---------------------------------------------------------------------------
# Crit detection and damage doubling
# ---------------------------------------------------------------------------


def test_crit_is_nat20_by_default():
    """crit_range=20: nat-20 triggers is_crit=True."""
    # Find a seed that produces nat-20
    for seed in range(100):
        rng = random.Random(seed)
        roller = Roller(rng)
        svc = RollService()
        result = svc.execute_attack_roll(
            _make_request(count=1, mode="raw", crit_enabled=True, crit_range=20, seed=seed),
            roller,
        )
        attack = result.attack_rolls[0]
        if attack.is_nat20:
            assert attack.is_crit is True
            break


def test_crit_disabled_no_crit_even_on_nat20():
    """crit_enabled=False: nat-20 does not trigger is_crit."""
    for seed in range(100):
        rng = random.Random(seed)
        roller = Roller(rng)
        svc = RollService()
        result = svc.execute_attack_roll(
            _make_request(count=1, mode="raw", crit_enabled=False, crit_range=20, seed=seed),
            roller,
        )
        attack = result.attack_rolls[0]
        if attack.is_nat20:
            assert attack.is_crit is False, "crit_enabled=False must suppress crit even on nat-20"
            break


def test_crit_range_18():
    """crit_range=18: any natural 18, 19, or 20 triggers is_crit."""
    for seed in range(200):
        rng = random.Random(seed)
        roller = Roller(rng)
        svc = RollService()
        result = svc.execute_attack_roll(
            _make_request(count=1, mode="raw", crit_enabled=True, crit_range=18, seed=seed),
            roller,
        )
        attack = result.attack_rolls[0]
        if attack.d20_natural >= 18:
            assert attack.is_crit is True, f"Natural {attack.d20_natural} should crit with range 18"
            break


# ---------------------------------------------------------------------------
# _double_dice utility
# ---------------------------------------------------------------------------


def test_double_dice_with_constant_bonus():
    """_double_dice('2d6+3') -> '4d6+3' (constant NOT doubled)."""
    assert _double_dice("2d6+3") == "4d6+3"


def test_double_dice_no_bonus():
    """_double_dice('1d8') -> '2d8'."""
    assert _double_dice("1d8") == "2d8"


def test_double_dice_pure_constant():
    """_double_dice('3') -> '3' (no dice, pure constant unchanged)."""
    assert _double_dice("3") == "3"


def test_double_dice_negative_bonus():
    """_double_dice('1d8-1') -> '2d8-1' (negative constant not doubled)."""
    assert _double_dice("1d8-1") == "2d8-1"


def test_double_dice_3d6():
    """_double_dice('3d6') -> '6d6'."""
    assert _double_dice("3d6") == "6d6"


# ---------------------------------------------------------------------------
# Flat modifier
# ---------------------------------------------------------------------------


def test_flat_modifier_included_in_attack_total(seeded_roller):
    """flat_modifier=+3 is added to attack_total (beyond to_hit_bonus)."""
    svc = RollService()
    result_no_flat = svc.execute_attack_roll(
        _make_request(count=1, flat_modifier=0, seed=42),
        Roller(random.Random(42)),
    )
    result_with_flat = svc.execute_attack_roll(
        _make_request(count=1, flat_modifier=3, seed=42),
        Roller(random.Random(42)),
    )
    no_flat_total = result_no_flat.attack_rolls[0].attack_total
    with_flat_total = result_with_flat.attack_rolls[0].attack_total
    assert with_flat_total == no_flat_total + 3


def test_flat_modifier_stored_in_result(seeded_roller):
    """AttackRollResult.flat_modifier reflects the value from RollRequest."""
    svc = RollService()
    result = svc.execute_attack_roll(_make_request(count=1, flat_modifier=5), seeded_roller)
    assert result.attack_rolls[0].flat_modifier == 5


def test_negative_flat_modifier(seeded_roller):
    """flat_modifier=-2 reduces attack_total by 2."""
    svc = RollService()
    result_no_flat = svc.execute_attack_roll(
        _make_request(count=1, flat_modifier=0, seed=99),
        Roller(random.Random(99)),
    )
    result_neg_flat = svc.execute_attack_roll(
        _make_request(count=1, flat_modifier=-2, seed=99),
        Roller(random.Random(99)),
    )
    assert result_neg_flat.attack_rolls[0].attack_total == result_no_flat.attack_rolls[0].attack_total - 2


# ---------------------------------------------------------------------------
# Bonus dice
# ---------------------------------------------------------------------------


def test_bonus_dice_non_empty_results(seeded_roller):
    """bonus_dice=[BonusDiceEntry('+1d4', 'Bless')] → bonus_dice_results non-empty."""
    svc = RollService()
    result = svc.execute_attack_roll(
        _make_request(count=1, bonus_dice=[BonusDiceEntry(formula="+1d4", label="Bless")]),
        seeded_roller,
    )
    attack = result.attack_rolls[0]
    assert len(attack.bonus_dice_results) == 1, "One bonus die entry must produce one result"


def test_bonus_dice_included_in_attack_total(seeded_roller):
    """Bonus dice total is included in attack_total."""
    svc = RollService()
    result_no_bonus = svc.execute_attack_roll(
        _make_request(count=1, bonus_dice=[], seed=42),
        Roller(random.Random(42)),
    )
    result_with_bonus = svc.execute_attack_roll(
        _make_request(
            count=1,
            bonus_dice=[BonusDiceEntry(formula="+1d4", label="Bless")],
            seed=42,
        ),
        Roller(random.Random(42)),
    )
    no_bonus_total = result_no_bonus.attack_rolls[0].attack_total
    with_bonus_total = result_with_bonus.attack_rolls[0].attack_total
    assert with_bonus_total > no_bonus_total, "Bonus die must increase attack total"


def test_bonus_dice_result_formula_in_tuple(seeded_roller):
    """Each bonus_dice_result is a tuple of (formula, signed_total, label)."""
    svc = RollService()
    result = svc.execute_attack_roll(
        _make_request(count=1, bonus_dice=[BonusDiceEntry(formula="+1d4", label="Bless")]),
        seeded_roller,
    )
    bonus = result.attack_rolls[0].bonus_dice_results[0]
    # Tuple: (formula, signed_total, label)
    assert len(bonus) == 3
    formula, signed_total, label = bonus
    assert label == "Bless"
    assert signed_total >= 1  # 1d4 minimum 1


# ---------------------------------------------------------------------------
# Damage type labels
# ---------------------------------------------------------------------------


def test_damage_type_label_preserved(seeded_roller):
    """DamagePartResult.damage_type carries the label from DamagePart."""
    svc = RollService()
    result = svc.execute_attack_roll(
        _make_request(
            count=1,
            mode="raw",
            damage_parts=[
                DamagePart(dice_expr="2d6", damage_type="slashing", raw_text="2d6")
            ],
        ),
        seeded_roller,
    )
    attack = result.attack_rolls[0]
    assert len(attack.damage_parts) == 1
    assert attack.damage_parts[0].damage_type == "slashing"


def test_multiple_damage_types(seeded_roller):
    """Multi-part damage preserves each type label."""
    svc = RollService()
    result = svc.execute_attack_roll(
        _make_request(
            count=1,
            mode="raw",
            damage_parts=[
                DamagePart(dice_expr="2d6", damage_type="slashing", raw_text="2d6"),
                DamagePart(dice_expr="1d4", damage_type="poison", raw_text="1d4"),
            ],
        ),
        seeded_roller,
    )
    attack = result.attack_rolls[0]
    assert len(attack.damage_parts) == 2
    types = {dp.damage_type for dp in attack.damage_parts}
    assert types == {"slashing", "poison"}


# ---------------------------------------------------------------------------
# RollSummary
# ---------------------------------------------------------------------------


def test_summary_hits_count_correct():
    """RollSummary.hits == count of attacks with is_hit=True in COMPARE mode."""
    rng = random.Random(42)
    roller = Roller(rng)
    svc = RollService()
    result = svc.execute_attack_roll(
        _make_request(count=10, mode="compare", target_ac=10),
        roller,
    )
    expected_hits = sum(1 for a in result.attack_rolls if a.is_hit is True)
    assert result.summary.hits == expected_hits


def test_summary_misses_count_correct():
    """RollSummary.misses == count of attacks with is_hit=False in COMPARE mode."""
    rng = random.Random(42)
    roller = Roller(rng)
    svc = RollService()
    result = svc.execute_attack_roll(
        _make_request(count=10, mode="compare", target_ac=10),
        roller,
    )
    expected_misses = sum(1 for a in result.attack_rolls if a.is_hit is False)
    assert result.summary.misses == expected_misses


def test_summary_total_attacks():
    """RollSummary.total_attacks == count requested."""
    rng = random.Random(42)
    roller = Roller(rng)
    svc = RollService()
    result = svc.execute_attack_roll(
        _make_request(count=7, mode="raw"),
        roller,
    )
    assert result.summary.total_attacks == 7


def test_summary_crits_count():
    """RollSummary.crits == count of attacks with is_crit=True."""
    rng = random.Random(42)
    roller = Roller(rng)
    svc = RollService()
    result = svc.execute_attack_roll(
        _make_request(count=20, mode="raw", crit_enabled=True, crit_range=20),
        roller,
    )
    expected_crits = sum(1 for a in result.attack_rolls if a.is_crit)
    assert result.summary.crits == expected_crits


# ---------------------------------------------------------------------------
# to_hit_bonus stored in result
# ---------------------------------------------------------------------------


def test_to_hit_bonus_stored(seeded_roller):
    """AttackRollResult.to_hit_bonus reflects the value from RollRequest."""
    svc = RollService()
    result = svc.execute_attack_roll(_make_request(count=1, to_hit_bonus=7), seeded_roller)
    assert result.attack_rolls[0].to_hit_bonus == 7


def test_to_hit_bonus_included_in_attack_total(seeded_roller):
    """to_hit_bonus is included in attack_total."""
    svc = RollService()
    result_low = svc.execute_attack_roll(
        _make_request(count=1, to_hit_bonus=0, seed=42),
        Roller(random.Random(42)),
    )
    result_high = svc.execute_attack_roll(
        _make_request(count=1, to_hit_bonus=5, seed=42),
        Roller(random.Random(42)),
    )
    assert result_high.attack_rolls[0].attack_total == result_low.attack_rolls[0].attack_total + 5


# ---------------------------------------------------------------------------
# attack_number ordering
# ---------------------------------------------------------------------------


def test_attack_numbers_sequential(seeded_roller):
    """attack_rolls[i].attack_number == i + 1 (1-indexed)."""
    svc = RollService()
    result = svc.execute_attack_roll(_make_request(count=4), seeded_roller)
    for i, attack in enumerate(result.attack_rolls):
        assert attack.attack_number == i + 1


# ---------------------------------------------------------------------------
# RollResult structure
# ---------------------------------------------------------------------------


def test_rollresult_has_request(seeded_roller):
    """RollResult.request is the original RollRequest."""
    svc = RollService()
    request = _make_request(count=3)
    result = svc.execute_attack_roll(request, seeded_roller)
    assert result.request is request


# ---------------------------------------------------------------------------
# d20_natural field
# ---------------------------------------------------------------------------


def test_d20_natural_matches_kept_face(seeded_roller):
    """AttackRollResult.d20_natural == value of the kept d20 face."""
    svc = RollService()
    result = svc.execute_attack_roll(
        _make_request(count=5, advantage="advantage"), seeded_roller
    )
    for attack in result.attack_rolls:
        kept_face = next(f for f in attack.d20_faces if f.kept)
        assert attack.d20_natural == kept_face.value
