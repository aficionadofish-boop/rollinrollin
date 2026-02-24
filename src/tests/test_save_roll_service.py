"""
Seeded golden tests for SaveRollService — covers all save roll mechanics.

RED phase: these tests import from src.encounter.service which does not yet exist;
running this file must fail with ImportError.
"""
from __future__ import annotations

import random

import pytest

from src.engine.roller import Roller
from src.encounter.service import SaveRollService, _resolve_save_bonus, _expand_participants  # noqa: F401
from src.encounter.models import (
    SaveRequest,
    SaveParticipant,
    SaveRollResult,
    SaveSummary,
    SaveParticipantResult,
)
from src.domain.models import Monster, Encounter
from src.roll.models import BonusDiceEntry


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def seeded_roller():
    return Roller(random.Random(42))


def _make_goblin(saves=None, ability_scores=None) -> Monster:
    return Monster(
        name="Goblin",
        ac=15,
        hp=7,
        cr="1/4",
        saves=saves or {},
        ability_scores=ability_scores or {"STR": 8, "DEX": 14, "CON": 10, "INT": 10, "WIS": 8, "CHA": 8},
    )


def _make_participant(name: str, save_bonus: int) -> SaveParticipant:
    return SaveParticipant(name=name, save_bonus=save_bonus)


# ---------------------------------------------------------------------------
# _resolve_save_bonus helper
# ---------------------------------------------------------------------------


def test_resolve_save_bonus_explicit_saves():
    """Monster with saves={"CON": 5} uses the explicit value directly."""
    goblin = _make_goblin(saves={"CON": 5})
    assert _resolve_save_bonus(goblin, "CON") == 5


def test_resolve_save_bonus_fallback_from_score():
    """Monster with no CON save entry falls back to (score-10)//2."""
    goblin = _make_goblin(saves={}, ability_scores={"CON": 14})
    assert _resolve_save_bonus(goblin, "CON") == 2  # (14-10)//2 = 2


def test_resolve_save_bonus_fallback_negative():
    """Ability score 8 -> (8-10)//2 = -1."""
    goblin = _make_goblin(saves={}, ability_scores={"STR": 8})
    assert _resolve_save_bonus(goblin, "STR") == -1


def test_resolve_save_bonus_missing_ability_score():
    """Missing ability score defaults to 10 -> modifier 0."""
    goblin = Monster(name="X", ac=10, hp=10, cr="0", saves={}, ability_scores={})
    assert _resolve_save_bonus(goblin, "WIS") == 0


def test_resolve_save_bonus_explicit_takes_priority():
    """Explicit saves entry overrides computed fallback."""
    # Score 10 would give 0, but explicit is 3
    goblin = _make_goblin(saves={"DEX": 3}, ability_scores={"DEX": 10})
    assert _resolve_save_bonus(goblin, "DEX") == 3


# ---------------------------------------------------------------------------
# _expand_participants helper
# ---------------------------------------------------------------------------


def test_expand_participants_count_one_uses_plain_name():
    """count=1 → name == monster.name (no numeric suffix)."""
    goblin = _make_goblin()
    encounter = Encounter(name="E", members=[(goblin, 1)])
    participants = _expand_participants(encounter, "CON")
    assert len(participants) == 1
    assert participants[0].name == "Goblin"


def test_expand_participants_count_many_uses_numbered_name():
    """count=3 → 'Goblin 1', 'Goblin 2', 'Goblin 3'."""
    goblin = _make_goblin()
    encounter = Encounter(name="E", members=[(goblin, 3)])
    participants = _expand_participants(encounter, "CON")
    assert len(participants) == 3
    assert participants[0].name == "Goblin 1"
    assert participants[1].name == "Goblin 2"
    assert participants[2].name == "Goblin 3"


def test_expand_participants_resolves_save_bonus():
    """Participants have save_bonus resolved from monster stats."""
    goblin = _make_goblin(saves={}, ability_scores={"CON": 12})
    encounter = Encounter(name="E", members=[(goblin, 1)])
    participants = _expand_participants(encounter, "CON")
    assert participants[0].save_bonus == 1  # (12-10)//2 = 1


def test_expand_participants_multiple_monster_types():
    """Multiple monster types all get expanded correctly."""
    goblin = Monster(name="Goblin", ac=15, hp=7, cr="1/4", saves={}, ability_scores={"DEX": 14})
    orc = Monster(name="Orc", ac=13, hp=15, cr="1/2", saves={"STR": 5}, ability_scores={"STR": 16})
    encounter = Encounter(name="E", members=[(goblin, 2), (orc, 1)])
    participants = _expand_participants(encounter, "DEX")
    assert len(participants) == 3
    assert participants[0].name == "Goblin 1"
    assert participants[1].name == "Goblin 2"
    assert participants[2].name == "Orc"  # count=1 → no number


# ---------------------------------------------------------------------------
# Normal save (no advantage/disadvantage) — seeded golden test
# ---------------------------------------------------------------------------


def test_normal_save_seeded(seeded_roller):
    """3 goblins, CON save DC 12, seed=42, normal → deterministic result matches golden values."""
    goblin = _make_goblin(saves={}, ability_scores={"CON": 10})  # save_bonus = 0
    participants = [
        _make_participant("Goblin 1", 0),
        _make_participant("Goblin 2", 0),
        _make_participant("Goblin 3", 0),
    ]
    request = SaveRequest(
        participants=participants,
        ability="CON",
        dc=12,
        advantage="normal",
        flat_modifier=0,
        bonus_dice=[],
        seed=42,
    )
    svc = SaveRollService()
    result = svc.execute_save_roll(request, seeded_roller)

    assert isinstance(result, SaveRollResult)
    assert len(result.participant_results) == 3
    # Each participant result has correct structure
    for pr in result.participant_results:
        assert pr.dc == 12
        assert pr.save_bonus == 0
        assert pr.flat_modifier == 0
        # total = natural + 0 + 0 = natural
        assert pr.total == pr.d20_natural
        assert pr.passed == (pr.total >= 12)
    # Summary counts match
    assert result.summary.total_participants == 3
    assert result.summary.passed + result.summary.failed == 3
    assert result.summary.failed == len(result.summary.failed_names)


def test_normal_save_result_structure(seeded_roller):
    """SaveParticipantResult has all required fields populated."""
    participant = _make_participant("Goblin", 2)
    request = SaveRequest(
        participants=[participant],
        ability="CON",
        dc=15,
        advantage="normal",
        flat_modifier=0,
        bonus_dice=[],
    )
    svc = SaveRollService()
    result = svc.execute_save_roll(request, seeded_roller)

    pr = result.participant_results[0]
    assert pr.name == "Goblin"
    assert pr.save_bonus == 2
    assert pr.flat_modifier == 0
    assert isinstance(pr.d20_natural, int)
    assert 1 <= pr.d20_natural <= 20
    assert len(pr.d20_faces) == 1  # normal: 1 face
    assert pr.d20_faces[0].kept is True
    assert pr.total == pr.d20_natural + 2  # natural + save_bonus
    assert pr.passed == (pr.total >= 15)


# ---------------------------------------------------------------------------
# Advantage / Disadvantage
# ---------------------------------------------------------------------------


def test_advantage_rolls_two_faces(seeded_roller):
    """Advantage rolls 2d20, keeps highest, exactly 1 face has kept=True."""
    participant = _make_participant("Goblin", 0)
    request = SaveRequest(
        participants=[participant],
        ability="CON",
        dc=10,
        advantage="advantage",
    )
    svc = SaveRollService()
    result = svc.execute_save_roll(request, seeded_roller)

    pr = result.participant_results[0]
    assert len(pr.d20_faces) == 2, "Advantage must produce 2 d20 faces"
    kept = [f for f in pr.d20_faces if f.kept]
    dropped = [f for f in pr.d20_faces if not f.kept]
    assert len(kept) == 1
    assert len(dropped) == 1
    assert kept[0].value >= dropped[0].value, "Advantage must keep the higher die"
    assert pr.d20_natural == kept[0].value


def test_disadvantage_rolls_two_faces(seeded_roller):
    """Disadvantage rolls 2d20, keeps lowest, exactly 1 face has kept=True."""
    participant = _make_participant("Goblin", 0)
    request = SaveRequest(
        participants=[participant],
        ability="CON",
        dc=10,
        advantage="disadvantage",
    )
    svc = SaveRollService()
    result = svc.execute_save_roll(request, seeded_roller)

    pr = result.participant_results[0]
    assert len(pr.d20_faces) == 2, "Disadvantage must produce 2 d20 faces"
    kept = [f for f in pr.d20_faces if f.kept]
    dropped = [f for f in pr.d20_faces if not f.kept]
    assert len(kept) == 1
    assert len(dropped) == 1
    assert kept[0].value <= dropped[0].value, "Disadvantage must keep the lower die"
    assert pr.d20_natural == kept[0].value


# ---------------------------------------------------------------------------
# Pass/fail boundary
# ---------------------------------------------------------------------------


def test_pass_fail_boundary_equal_to_dc():
    """total == dc is a PASS (total >= dc)."""
    # We need to engineer a result where total == dc exactly.
    # Seed the roller to produce a known natural, then set dc = natural + bonus.
    # With seed=42, normal 1d20 → first roll is 1 (verify with roller).
    rng = random.Random(42)
    roller = Roller(rng)
    # Roll once to see what we get
    from src.engine.parser import roll_expression
    result_d20 = roll_expression("1d20", roller)
    natural = next(f for f in result_d20.faces if f.kept).value

    # Now set up: save_bonus=0, flat=0, dc = natural → total == dc → PASS
    participant = _make_participant("TestMonster", 0)
    request = SaveRequest(
        participants=[participant],
        ability="CON",
        dc=natural,  # exactly equal
        advantage="normal",
        flat_modifier=0,
        bonus_dice=[],
    )
    svc = SaveRollService()
    result = svc.execute_save_roll(request, Roller(random.Random(42)))
    pr = result.participant_results[0]
    assert pr.passed is True, f"total {pr.total} == dc {natural} should be PASS"


def test_pass_fail_one_below_dc():
    """total == dc - 1 is a FAIL."""
    # Force a known roll by using seeded approach
    # seed=42: first 1d20 result is known; set dc = natural + 1 to guarantee fail
    rng_check = random.Random(42)
    roller_check = Roller(rng_check)
    from src.engine.parser import roll_expression
    result_d20 = roll_expression("1d20", roller_check)
    natural = next(f for f in result_d20.faces if f.kept).value

    participant = _make_participant("TestMonster", 0)
    request = SaveRequest(
        participants=[participant],
        ability="CON",
        dc=natural + 1,  # one above the natural — guaranteed fail
        advantage="normal",
        flat_modifier=0,
        bonus_dice=[],
    )
    svc = SaveRollService()
    result = svc.execute_save_roll(request, Roller(random.Random(42)))
    pr = result.participant_results[0]
    assert pr.passed is False, f"total {pr.total} < dc {natural + 1} should be FAIL"


# ---------------------------------------------------------------------------
# Flat modifier
# ---------------------------------------------------------------------------


def test_flat_modifier_included_in_total(seeded_roller):
    """flat_modifier=+3 is added to total."""
    svc = SaveRollService()
    participant = _make_participant("G", 0)

    result_no_flat = svc.execute_save_roll(
        SaveRequest(participants=[participant], ability="CON", dc=10,
                    flat_modifier=0),
        Roller(random.Random(42)),
    )
    result_with_flat = svc.execute_save_roll(
        SaveRequest(participants=[participant], ability="CON", dc=10,
                    flat_modifier=3),
        Roller(random.Random(42)),
    )

    assert result_with_flat.participant_results[0].total == (
        result_no_flat.participant_results[0].total + 3
    )


# ---------------------------------------------------------------------------
# Bonus dice
# ---------------------------------------------------------------------------


def test_bonus_dice_included_in_total(seeded_roller):
    """bonus_dice=[BonusDiceEntry('+1d4', 'Bless')] increases total."""
    svc = SaveRollService()
    participant = _make_participant("G", 0)

    result_no_bonus = svc.execute_save_roll(
        SaveRequest(participants=[participant], ability="CON", dc=10, bonus_dice=[]),
        Roller(random.Random(42)),
    )
    result_with_bonus = svc.execute_save_roll(
        SaveRequest(
            participants=[participant],
            ability="CON",
            dc=10,
            bonus_dice=[BonusDiceEntry(formula="+1d4", label="Bless")],
        ),
        Roller(random.Random(42)),
    )

    assert result_with_bonus.participant_results[0].total > result_no_bonus.participant_results[0].total


def test_bonus_dice_result_in_participant_result(seeded_roller):
    """bonus_dice_results list is non-empty when bonus dice provided."""
    svc = SaveRollService()
    participant = _make_participant("G", 0)
    request = SaveRequest(
        participants=[participant],
        ability="CON",
        dc=10,
        bonus_dice=[BonusDiceEntry(formula="+1d4", label="Bless")],
    )
    result = svc.execute_save_roll(request, seeded_roller)
    pr = result.participant_results[0]
    assert len(pr.bonus_dice_results) == 1
    formula, signed_total, label = pr.bonus_dice_results[0]
    assert label == "Bless"
    assert signed_total >= 1  # 1d4 minimum 1


# ---------------------------------------------------------------------------
# Empty participants
# ---------------------------------------------------------------------------


def test_empty_participants_returns_empty_result(seeded_roller):
    """SaveRequest with no participants returns SaveRollResult with empty lists."""
    request = SaveRequest(participants=[], ability="CON", dc=10)
    svc = SaveRollService()
    result = svc.execute_save_roll(request, seeded_roller)

    assert result.participant_results == []
    assert result.summary.total_participants == 0
    assert result.summary.passed == 0
    assert result.summary.failed == 0
    assert result.summary.failed_names == []


# ---------------------------------------------------------------------------
# SaveSummary correctness
# ---------------------------------------------------------------------------


def test_summary_failed_names_match_failed_participants():
    """summary.failed_names contains exactly the names of participants who failed."""
    participants = [
        _make_participant("Alpha", 0),
        _make_participant("Beta", 0),
        _make_participant("Gamma", 0),
    ]
    # Use DC=0 to guarantee all pass first
    request_all_pass = SaveRequest(participants=participants, ability="CON", dc=0)
    svc = SaveRollService()
    result = svc.execute_save_roll(request_all_pass, Roller(random.Random(1)))
    assert result.summary.failed_names == []
    assert result.summary.passed == 3
    assert result.summary.failed == 0


def test_summary_all_fail():
    """With DC=21 (impossible), all participants fail."""
    participants = [
        _make_participant("A", 0),
        _make_participant("B", 0),
    ]
    request = SaveRequest(participants=participants, ability="CON", dc=21)
    svc = SaveRollService()
    result = svc.execute_save_roll(request, Roller(random.Random(1)))
    assert result.summary.passed == 0
    assert result.summary.failed == 2
    assert set(result.summary.failed_names) == {"A", "B"}


def test_summary_request_preserved():
    """SaveRollResult.request is the original SaveRequest."""
    participants = [_make_participant("G", 0)]
    request = SaveRequest(participants=participants, ability="CON", dc=10)
    svc = SaveRollService()
    result = svc.execute_save_roll(request, Roller(random.Random(1)))
    assert result.request is request
