"""TDD test suite for CombatTrackerService.

Tests are written first (RED phase), then the service is implemented to make them pass (GREEN phase).
"""
from __future__ import annotations

import random
from dataclasses import dataclass

import pytest

from src.combat.models import (
    COMMON_BUFFS,
    STANDARD_CONDITIONS,
    CombatantState,
    CombatState,
    ConditionEntry,
    PlayerCharacter,
)
from src.combat.service import CombatTrackerService
from src.engine.roller import Roller


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def make_roller(seed: int = 42) -> Roller:
    """Return a deterministic seeded Roller for initiative tests."""
    return Roller(random.Random(seed))


def _make_combatant(
    cid: str,
    name: str,
    max_hp: int = 10,
    current_hp: int | None = None,
    temp_hp: int = 0,
    initiative: int = 0,
    ac: int = 10,
    dex_score: int = 10,
    group_id: str = "",
    conditions: list | None = None,
    is_pc: bool = False,
) -> CombatantState:
    """Convenience factory for CombatantState in tests."""
    return CombatantState(
        id=cid,
        name=name,
        monster_name=None if is_pc else name,
        max_hp=max_hp,
        current_hp=current_hp if current_hp is not None else max_hp,
        temp_hp=temp_hp,
        initiative=initiative,
        ac=ac,
        dex_score=dex_score,
        group_id=group_id,
        conditions=conditions or [],
        is_pc=is_pc,
    )


def _service_with_combatants(*combatants: CombatantState) -> CombatTrackerService:
    """Return a CombatTrackerService whose state already contains the given combatants."""
    svc = CombatTrackerService()
    state = CombatState(combatants=list(combatants))
    svc.load_state(state)
    return svc


# ---------------------------------------------------------------------------
# Test 1: load_encounter creates individual combatants
# ---------------------------------------------------------------------------

class _MockMonster:
    """Minimal Monster-like object for testing load_encounter."""

    def __init__(self, name: str, hp: int = 10, ac: int = 12, dex: int = 14,
                 actions: list | None = None):
        self.name = name
        self.hp = hp
        self.ac = ac
        self.ability_scores = {"DEX": dex, "STR": 10, "CON": 10, "INT": 6, "WIS": 8, "CHA": 8}
        self.actions = actions or []


def test_load_encounter_creates_individual_combatants():
    """3 Goblins should produce Goblin 1, Goblin 2, Goblin 3 as separate CombatantState entries."""
    goblin = _MockMonster("Goblin", hp=7, ac=15)
    svc = CombatTrackerService()
    svc.load_encounter([(goblin, 3)], make_roller())

    combatants = svc.state.combatants
    assert len(combatants) == 3
    names = [c.name for c in combatants]
    assert "Goblin 1" in names
    assert "Goblin 2" in names
    assert "Goblin 3" in names
    # All should have Goblin's stats
    for c in combatants:
        assert c.max_hp == 7
        assert c.ac == 15
        assert c.group_id == "Goblin"


# ---------------------------------------------------------------------------
# Test 2: apply_damage healing caps at max HP
# ---------------------------------------------------------------------------

def test_apply_damage_healing_caps_at_max():
    """Healing beyond max_hp should stop at max_hp."""
    c = _make_combatant("hero_1", "Hero", max_hp=20, current_hp=15)
    svc = _service_with_combatants(c)

    log = svc.apply_damage("hero_1", +10)  # heal 10, but max is 20 so only +5

    combatant = svc.get_combatant("hero_1")
    assert combatant.current_hp == 20
    assert "healed" in log.lower() or "HP" in log


# ---------------------------------------------------------------------------
# Test 3: temp HP absorbs damage first
# ---------------------------------------------------------------------------

def test_apply_damage_temp_hp_absorbs_first():
    """Dealing -8 damage to a combatant with 5 temp HP: temp HP drops to 0, current_hp drops by 3."""
    c = _make_combatant("orc_1", "Orc", max_hp=15, current_hp=15, temp_hp=5)
    svc = _service_with_combatants(c)

    svc.apply_damage("orc_1", -8)

    combatant = svc.get_combatant("orc_1")
    assert combatant.temp_hp == 0
    assert combatant.current_hp == 12  # 15 - (8 - 5) = 12


# ---------------------------------------------------------------------------
# Test 4: apply_damage floors at 0
# ---------------------------------------------------------------------------

def test_apply_damage_floor_at_zero():
    """Damage exceeding current HP should floor current_hp at 0, not go negative."""
    c = _make_combatant("skeleton_1", "Skeleton", max_hp=13, current_hp=3)
    svc = _service_with_combatants(c)

    svc.apply_damage("skeleton_1", -50)  # massive damage

    combatant = svc.get_combatant("skeleton_1")
    assert combatant.current_hp == 0
    assert combatant.is_defeated


# ---------------------------------------------------------------------------
# Test 5: advance_turn decrements timed conditions
# ---------------------------------------------------------------------------

def test_advance_turn_decrements_conditions():
    """A condition with duration=3 should become duration=2 after the combatant's turn ends."""
    cond = ConditionEntry(name="Poisoned", duration=3)
    c1 = _make_combatant("hero_1", "Hero", conditions=[cond])
    c2 = _make_combatant("goblin_1", "Goblin")
    svc = _service_with_combatants(c1, c2)
    # current_turn_index = 0 (hero's turn)

    svc.advance_turn()  # hero's turn ends, goblin's turn begins

    hero = svc.get_combatant("hero_1")
    assert hero.conditions[0].duration == 2
    assert not hero.conditions[0].expired


# ---------------------------------------------------------------------------
# Test 6: advance_turn expires condition at duration=1
# ---------------------------------------------------------------------------

def test_advance_turn_expires_condition():
    """A condition at duration=1 should be marked expired=True after the turn ends."""
    cond = ConditionEntry(name="Bless", duration=1)
    c1 = _make_combatant("paladin_1", "Paladin", conditions=[cond])
    c2 = _make_combatant("guard_1", "Guard")
    svc = _service_with_combatants(c1, c2)

    svc.advance_turn()

    paladin = svc.get_combatant("paladin_1")
    assert paladin.conditions[0].duration == 0
    assert paladin.conditions[0].expired


# ---------------------------------------------------------------------------
# Test 7: advance_turn increments round when wrapping
# ---------------------------------------------------------------------------

def test_advance_turn_increments_round():
    """Advancing past the last combatant should increment round_number from 1 to 2."""
    c1 = _make_combatant("a_1", "A")
    c2 = _make_combatant("b_1", "B")
    svc = _service_with_combatants(c1, c2)
    # Start: round=1, turn_index=0

    svc.advance_turn()  # A's turn ends → B's turn (index 1), round still 1
    assert svc.state.round_number == 1
    assert svc.state.current_turn_index == 1

    svc.advance_turn()  # B's turn ends → wrap to index 0 (A), round becomes 2
    assert svc.state.round_number == 2
    assert svc.state.current_turn_index == 0


# ---------------------------------------------------------------------------
# Test 8: undo_advance restores conditions
# ---------------------------------------------------------------------------

def test_undo_advance_restores_conditions():
    """After advance_turn reduces a condition's duration, undo_advance should restore it."""
    cond = ConditionEntry(name="Poisoned", duration=3)
    c1 = _make_combatant("hero_1", "Hero", conditions=[cond])
    c2 = _make_combatant("goblin_1", "Goblin")
    svc = _service_with_combatants(c1, c2)

    svc.advance_turn()
    hero_after = svc.get_combatant("hero_1")
    assert hero_after.conditions[0].duration == 2

    result = svc.undo_advance()
    assert result is True

    hero_restored = svc.get_combatant("hero_1")
    assert hero_restored.conditions[0].duration == 3
    assert not hero_restored.conditions[0].expired


# ---------------------------------------------------------------------------
# Test 9: undo_advance restores round_number after boundary crossing
# ---------------------------------------------------------------------------

def test_undo_advance_restores_round_number():
    """If advance_turn crossed a round boundary, undo should decrement round_number back."""
    c1 = _make_combatant("a_1", "A")
    c2 = _make_combatant("b_1", "B")
    svc = _service_with_combatants(c1, c2)

    svc.advance_turn()  # A→B, still round 1
    svc.advance_turn()  # B→A (wrap), round becomes 2
    assert svc.state.round_number == 2
    assert svc.state.current_turn_index == 0

    result = svc.undo_advance()
    assert result is True
    assert svc.state.round_number == 1
    assert svc.state.current_turn_index == 1


# ---------------------------------------------------------------------------
# Test 10: roll_all_initiative sorts descending
# ---------------------------------------------------------------------------

def test_roll_initiative_sorts_descending():
    """After roll_all_initiative, combatants should be sorted by initiative descending."""
    c1 = _make_combatant("goblin_1", "Goblin 1", dex_score=10)
    c2 = _make_combatant("goblin_2", "Goblin 2", dex_score=10)
    c3 = _make_combatant("goblin_3", "Goblin 3", dex_score=10)
    svc = _service_with_combatants(c1, c2, c3)

    roller = make_roller(42)
    svc.roll_all_initiative(roller)

    initiatives = [c.initiative for c in svc.state.combatants]
    assert initiatives == sorted(initiatives, reverse=True), f"Expected descending order, got {initiatives}"


# ---------------------------------------------------------------------------
# Test 11: roll_all_initiative groups same monster type
# ---------------------------------------------------------------------------

def test_roll_initiative_grouped():
    """Combatants with the same group_id share a single initiative roll when grouping is enabled."""
    c1 = _make_combatant("goblin_1", "Goblin 1", group_id="Goblin", dex_score=10)
    c2 = _make_combatant("goblin_2", "Goblin 2", group_id="Goblin", dex_score=10)
    c3 = _make_combatant("orc_1", "Orc 1", group_id="Orc", dex_score=14)
    svc = _service_with_combatants(c1, c2, c3)
    svc.state.grouping_enabled = True

    roller = make_roller(42)
    svc.roll_all_initiative(roller)

    goblins = [c for c in svc.state.combatants if c.group_id == "Goblin"]
    assert goblins[0].initiative == goblins[1].initiative, (
        f"Goblins should share initiative; got {goblins[0].initiative} vs {goblins[1].initiative}"
    )


# ---------------------------------------------------------------------------
# Test 12: remove_combatant adjusts turn_index
# ---------------------------------------------------------------------------

def test_remove_combatant_adjusts_turn_index():
    """Removing a combatant at or before current_turn_index should decrement the index."""
    c1 = _make_combatant("a_1", "A")
    c2 = _make_combatant("b_1", "B")
    c3 = _make_combatant("c_1", "C")
    svc = _service_with_combatants(c1, c2, c3)
    svc.state.current_turn_index = 2  # C's turn

    # Remove B (index 1) which is before the current turn (index 2)
    svc.remove_combatant("b_1")

    # Current turn index should now be 1 (was 2, decremented because removed index < 2)
    assert svc.state.current_turn_index == 1
    # C should still be the active combatant
    assert svc.state.combatants[svc.state.current_turn_index].id == "c_1"


# ---------------------------------------------------------------------------
# Test 13: pass_one_round decrements all timed conditions
# ---------------------------------------------------------------------------

def test_pass_one_round_decrements_all():
    """pass_one_round should decrement all timed conditions on all combatants and increment round."""
    cond_a = ConditionEntry(name="Poisoned", duration=3)
    cond_b = ConditionEntry(name="Bless", duration=2)
    cond_c = ConditionEntry(name="Invisible", duration=None)  # indefinite, should not decrement
    c1 = _make_combatant("hero_1", "Hero", conditions=[cond_a, cond_c])
    c2 = _make_combatant("goblin_1", "Goblin", conditions=[cond_b])
    svc = _service_with_combatants(c1, c2)

    svc.pass_one_round()

    hero = svc.get_combatant("hero_1")
    goblin = svc.get_combatant("goblin_1")

    assert hero.conditions[0].duration == 2   # Poisoned: 3→2
    assert hero.conditions[1].duration is None  # Invisible stays None
    assert goblin.conditions[0].duration == 1   # Bless: 2→1
    assert svc.state.round_number == 2


# ---------------------------------------------------------------------------
# Test 14: reset_combat clears state
# ---------------------------------------------------------------------------

def test_reset_combat_clears_state():
    """reset_combat should restore HP to max, clear conditions, clear initiative, set round=1."""
    cond = ConditionEntry(name="Poisoned", duration=2)
    c1 = _make_combatant("hero_1", "Hero", max_hp=20, current_hp=5, conditions=[cond])
    c2 = _make_combatant("goblin_1", "Goblin", max_hp=7, current_hp=2)
    svc = _service_with_combatants(c1, c2)
    svc.state.round_number = 4
    svc.state.current_turn_index = 1

    svc.reset_combat()

    hero = svc.get_combatant("hero_1")
    goblin = svc.get_combatant("goblin_1")

    assert hero.current_hp == hero.max_hp == 20
    assert hero.conditions == []
    assert goblin.current_hp == goblin.max_hp == 7
    assert svc.state.round_number == 1
    assert svc.state.current_turn_index == 0


# ---------------------------------------------------------------------------
# Test 15: CombatantState serialization roundtrip
# ---------------------------------------------------------------------------

def test_combatant_state_serialization_roundtrip():
    """to_dict/from_dict should preserve all fields including conditions and booleans."""
    cond = ConditionEntry(name="Stunned", duration=2, expired=False, color="#ff0000")
    c = CombatantState(
        id="dragon_1",
        name="Ancient Dragon 1",
        monster_name="Ancient Dragon",
        max_hp=350,
        current_hp=275,
        temp_hp=20,
        initiative=18,
        ac=22,
        is_pc=False,
        group_id="Ancient Dragon",
        dex_score=10,
        speed="40 ft.",
        passive_perception=25,
        legendary_resistances=2,
        legendary_resistances_max=3,
        legendary_actions=3,
        legendary_actions_max=3,
        regeneration_hp=0,
        conditions=[cond],
    )

    d = c.to_dict()
    restored = CombatantState.from_dict(d)

    assert restored.id == c.id
    assert restored.name == c.name
    assert restored.monster_name == c.monster_name
    assert restored.max_hp == c.max_hp
    assert restored.current_hp == c.current_hp
    assert restored.temp_hp == c.temp_hp
    assert restored.initiative == c.initiative
    assert restored.ac == c.ac
    assert restored.is_pc == c.is_pc
    assert restored.group_id == c.group_id
    assert restored.dex_score == c.dex_score
    assert restored.speed == c.speed
    assert restored.passive_perception == c.passive_perception
    assert restored.legendary_resistances == c.legendary_resistances
    assert restored.legendary_resistances_max == c.legendary_resistances_max
    assert restored.legendary_actions == c.legendary_actions
    assert restored.legendary_actions_max == c.legendary_actions_max
    assert len(restored.conditions) == 1
    assert restored.conditions[0].name == "Stunned"
    assert restored.conditions[0].duration == 2
    assert restored.conditions[0].color == "#ff0000"


# ---------------------------------------------------------------------------
# Test 16: CombatState serialization roundtrip
# ---------------------------------------------------------------------------

def test_combat_state_serialization_roundtrip():
    """Full CombatState to_dict/from_dict roundtrip preserves all fields."""
    cond = ConditionEntry(name="Bless", duration=5)
    c1 = CombatantState(
        id="fighter_1", name="Fighter 1", monster_name=None,
        max_hp=45, current_hp=30, temp_hp=5, initiative=15, ac=18,
        is_pc=True, conditions=[cond],
    )
    c2 = CombatantState(
        id="goblin_1", name="Goblin 1", monster_name="Goblin",
        max_hp=7, current_hp=4, initiative=8, ac=15, is_pc=False,
    )
    state = CombatState(
        combatants=[c1, c2],
        round_number=3,
        current_turn_index=1,
        initiative_mode=True,
        grouping_enabled=False,
        log_entries=["Round 1: Combat began", "Goblin 1: -3 dmg"],
    )

    d = state.to_dict()
    restored = CombatState.from_dict(d)

    assert restored.round_number == 3
    assert restored.current_turn_index == 1
    assert restored.initiative_mode is True
    assert restored.grouping_enabled is False
    assert len(restored.log_entries) == 2
    assert len(restored.combatants) == 2
    assert restored.combatants[0].id == "fighter_1"
    assert restored.combatants[0].current_hp == 30
    assert restored.combatants[0].conditions[0].name == "Bless"
    assert restored.combatants[1].id == "goblin_1"


# ---------------------------------------------------------------------------
# Additional: STANDARD_CONDITIONS and COMMON_BUFFS constants
# ---------------------------------------------------------------------------

def test_standard_conditions_count():
    """STANDARD_CONDITIONS should have exactly 14 entries."""
    assert len(STANDARD_CONDITIONS) == 14
    names = [c["name"] for c in STANDARD_CONDITIONS]
    assert "Poisoned" in names
    assert "Paralyzed" in names
    assert "Unconscious" in names


def test_common_buffs_count():
    """COMMON_BUFFS should have at least 10 entries."""
    assert len(COMMON_BUFFS) >= 10
    names = [b["name"] for b in COMMON_BUFFS]
    assert "Bless" in names
    assert "Haste" in names


# ---------------------------------------------------------------------------
# Additional: undo_advance returns False if no snapshot
# ---------------------------------------------------------------------------

def test_undo_advance_returns_false_when_no_snapshot():
    """undo_advance should return False if called before any advance_turn."""
    svc = CombatTrackerService()
    c1 = _make_combatant("hero_1", "Hero")
    svc.load_state(CombatState(combatants=[c1]))

    result = svc.undo_advance()
    assert result is False


# ---------------------------------------------------------------------------
# Additional: add_condition and remove_condition
# ---------------------------------------------------------------------------

def test_add_and_remove_condition():
    """add_condition adds a ConditionEntry; remove_condition removes the first match by name."""
    c = _make_combatant("rogue_1", "Rogue")
    svc = _service_with_combatants(c)

    svc.add_condition("rogue_1", ConditionEntry(name="Prone", duration=None))
    rogue = svc.get_combatant("rogue_1")
    assert len(rogue.conditions) == 1
    assert rogue.conditions[0].name == "Prone"

    svc.remove_condition("rogue_1", "Prone")
    rogue = svc.get_combatant("rogue_1")
    assert len(rogue.conditions) == 0


# ---------------------------------------------------------------------------
# Additional: is_defeated property
# ---------------------------------------------------------------------------

def test_is_defeated_property():
    """CombatantState.is_defeated should be True when current_hp <= 0."""
    alive = _make_combatant("hero_1", "Hero", max_hp=10, current_hp=1)
    dead = _make_combatant("goblin_1", "Goblin", max_hp=7, current_hp=0)
    negative = _make_combatant("zombie_1", "Zombie", max_hp=22, current_hp=0)

    assert not alive.is_defeated
    assert dead.is_defeated
    assert negative.is_defeated


# ---------------------------------------------------------------------------
# Additional: PlayerCharacter serialization roundtrip
# ---------------------------------------------------------------------------

def test_player_character_serialization_roundtrip():
    """PlayerCharacter to_dict/from_dict preserves all fields."""
    cond = ConditionEntry(name="Bless", duration=10)
    pc = PlayerCharacter(
        name="Aria the Bold",
        ac=16,
        max_hp=45,
        current_hp=33,
        conditions=[cond],
    )

    d = pc.to_dict()
    restored = PlayerCharacter.from_dict(d)

    assert restored.name == "Aria the Bold"
    assert restored.ac == 16
    assert restored.max_hp == 45
    assert restored.current_hp == 33
    assert len(restored.conditions) == 1
    assert restored.conditions[0].name == "Bless"
    assert restored.conditions[0].duration == 10
