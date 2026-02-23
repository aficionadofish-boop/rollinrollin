from src.domain.models import Monster, Action, DamagePart, MonsterList, Encounter, DamageType


def test_monster_minimal():
    m = Monster(name="Goblin", ac=15, hp=7, cr="1/4")
    assert m.name == "Goblin"
    assert m.ac == 15
    assert m.hp == 7
    assert m.cr == "1/4"
    assert m.actions == []
    assert m.saves == {}
    assert m.incomplete is False


def test_monster_no_shared_mutable_default():
    m1 = Monster(name="A", ac=10, hp=10, cr="0")
    m2 = Monster(name="B", ac=12, hp=12, cr="0")
    m1.actions.append(Action(name="Slam", to_hit_bonus=3))
    assert len(m2.actions) == 0, "mutable default shared between instances"


def test_damage_part_construction():
    dp = DamagePart(dice_expr="2d6+3", damage_type="slashing", raw_text="2d6+3 slashing")
    assert dp.condition is None


def test_damage_part_with_condition():
    dp = DamagePart(dice_expr="1d8", damage_type="poison", raw_text="1d8 poison", condition="on crit")
    assert dp.condition == "on crit"


def test_action_construction():
    a = Action(name="Bite", to_hit_bonus=4)
    assert a.damage_parts == []


def test_action_with_parts():
    dp = DamagePart(dice_expr="1d6", damage_type="piercing", raw_text="1d6 piercing")
    a = Action(name="Bite", to_hit_bonus=4, damage_parts=[dp])
    assert len(a.damage_parts) == 1


def test_monster_list_construction():
    goblin = Monster(name="Goblin", ac=15, hp=7, cr="1/4")
    ml = MonsterList(name="Horde", entries=[(goblin, 5)])
    assert ml.name == "Horde"
    assert ml.entries[0][1] == 5


def test_encounter_construction():
    goblin = Monster(name="Goblin", ac=15, hp=7, cr="1/4")
    enc = Encounter(name="Ambush", members=[goblin])
    assert len(enc.members) == 1


def test_damage_type_enum_values():
    assert DamageType.SLASHING.value == "slashing"
    assert DamageType.UNKNOWN.value == "unknown"
