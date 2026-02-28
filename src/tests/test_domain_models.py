import dataclasses

from src.domain.models import (
    Monster, Action, DamagePart, MonsterList, Encounter, DamageType,
    EquipmentItem, BuffItem, MonsterModification, SKILL_TO_ABILITY,
)


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
    enc = Encounter(name="Ambush", members=[(goblin, 1)])
    assert len(enc.members) == 1
    assert enc.members[0][0] is goblin
    assert enc.members[0][1] == 1


def test_damage_type_enum_values():
    assert DamageType.SLASHING.value == "slashing"
    assert DamageType.UNKNOWN.value == "unknown"


# --- Phase 2: New tests for extended domain models ---

def test_action_to_hit_bonus_optional():
    """Action.to_hit_bonus can be None (non-attack abilities like Multiattack)."""
    a = Action(name="Multiattack", to_hit_bonus=None)
    assert a.to_hit_bonus is None


def test_action_raw_text_default():
    """Action.raw_text defaults to empty string."""
    a = Action(name="Bite", to_hit_bonus=4)
    assert a.raw_text == ""


def test_action_is_parsed_default():
    """Action.is_parsed defaults to True."""
    a = Action(name="Bite", to_hit_bonus=4)
    assert a.is_parsed is True


def test_action_raw_text_and_is_parsed_settable():
    """Action raw_text and is_parsed can be explicitly set to unparsed state."""
    a = Action(name="Gaze", to_hit_bonus=None, raw_text="Petrifying...", is_parsed=False)
    assert a.raw_text == "Petrifying..."
    assert a.is_parsed is False
    assert a.to_hit_bonus is None


def test_monster_creature_type_default():
    """Monster.creature_type defaults to empty string."""
    m = Monster(name="Goblin", ac=15, hp=7, cr="1/4")
    assert m.creature_type == ""


def test_monster_ability_scores_default():
    """Monster.ability_scores defaults to empty dict with no shared mutable state."""
    m1 = Monster(name="Goblin", ac=15, hp=7, cr="1/4")
    m2 = Monster(name="Orc", ac=13, hp=15, cr="1/2")
    assert m1.ability_scores == {}
    m1.ability_scores["STR"] = 10
    assert m2.ability_scores == {}, "mutable default shared between Monster instances"


def test_monster_lore_default():
    """Monster.lore defaults to empty string."""
    m = Monster(name="Goblin", ac=15, hp=7, cr="1/4")
    assert m.lore == ""


def test_monster_raw_text_default():
    """Monster.raw_text defaults to empty string."""
    m = Monster(name="Goblin", ac=15, hp=7, cr="1/4")
    assert m.raw_text == ""


def test_monster_new_fields_settable():
    """Extended Monster fields can be set at construction."""
    m = Monster(
        name="Medusa",
        ac=15,
        hp=127,
        cr="6",
        creature_type="Monstrosity",
        ability_scores={"STR": 10, "DEX": 15, "CON": 16, "INT": 12, "WIS": 13, "CHA": 15},
        lore="Cursed beings...",
        raw_text="Full statblock text...",
    )
    assert m.creature_type == "Monstrosity"
    assert m.ability_scores["DEX"] == 15
    assert m.lore == "Cursed beings..."
    assert m.raw_text == "Full statblock text..."


# --- Phase 2: ParseResult and ParseFailure dataclasses ---

def test_parse_result_importable():
    """ParseResult and ParseFailure are importable from src.parser.models."""
    from src.parser.models import ParseResult, ParseFailure
    result = ParseResult(monsters=[], failures=[], warnings=[])
    assert result.monsters == []
    assert result.failures == []
    assert result.warnings == []


def test_parse_result_default_warnings():
    """ParseResult.warnings defaults to empty list."""
    from src.parser.models import ParseResult
    result = ParseResult(monsters=[], failures=[])
    assert result.warnings == []


def test_parse_failure_construction():
    """ParseFailure can be constructed with source_file, monster_name, reason."""
    from src.parser.models import ParseFailure
    f = ParseFailure(source_file="a.md", monster_name="", reason="no name found")
    assert f.source_file == "a.md"
    assert f.monster_name == ""
    assert f.reason == "no name found"


def test_parse_failure_with_name():
    """ParseFailure can carry a monster name and specific reason."""
    from src.parser.models import ParseFailure
    f = ParseFailure(source_file="b.md", monster_name="Goblin", reason="no AC")
    assert f.monster_name == "Goblin"
    assert f.reason == "no AC"


# --- Phase 9: Domain model extension tests ---

def test_monster_default_size():
    """Monster.size defaults to 'Medium'."""
    m = Monster(name="Goblin", ac=15, hp=7, cr="1/4")
    assert m.size == "Medium"


def test_monster_size_settable():
    """Monster.size can be explicitly set."""
    m = Monster(name="Fire Giant", ac=18, hp=162, cr="9", size="Huge")
    assert m.size == "Huge"


def test_monster_default_skills():
    """Monster.skills defaults to empty dict."""
    m = Monster(name="Goblin", ac=15, hp=7, cr="1/4")
    assert m.skills == {}


def test_monster_skills_no_shared_mutable_default():
    """Monster.skills dict is not shared between instances."""
    m1 = Monster(name="A", ac=10, hp=10, cr="0")
    m2 = Monster(name="B", ac=10, hp=10, cr="0")
    m1.skills["Perception"] = 5
    assert m2.skills == {}, "mutable default shared between Monster instances"


def test_action_default_damage_bonus():
    """Action.damage_bonus defaults to None."""
    a = Action(name="Bite", to_hit_bonus=4)
    assert a.damage_bonus is None


def test_action_default_is_equipment_generated():
    """Action.is_equipment_generated defaults to False."""
    a = Action(name="Bite", to_hit_bonus=4)
    assert a.is_equipment_generated is False


def test_action_damage_bonus_settable():
    """Action.damage_bonus can be set as an integer."""
    a = Action(name="Longsword", to_hit_bonus=5, damage_bonus=3)
    assert a.damage_bonus == 3


def test_action_is_equipment_generated_settable():
    """Action.is_equipment_generated can be set to True."""
    a = Action(name="Longsword", to_hit_bonus=5, is_equipment_generated=True)
    assert a.is_equipment_generated is True


def test_equipment_item_round_trip():
    """EquipmentItem round-trips via dataclasses.asdict()."""
    item = EquipmentItem(item_type="weapon", item_name="Longsword", magic_bonus=2)
    d = dataclasses.asdict(item)
    assert d == {"item_type": "weapon", "item_name": "Longsword", "magic_bonus": 2}
    restored = EquipmentItem(**d)
    assert restored == item


def test_buff_item_round_trip():
    """BuffItem round-trips via dataclasses.asdict() with 4 boolean fields."""
    buf = BuffItem(name="Bless", bonus_value="+1d4", affects_attacks=True, affects_saves=True, affects_ability_checks=False, affects_damage=False)
    d = dataclasses.asdict(buf)
    assert d == {
        "name": "Bless",
        "bonus_value": "+1d4",
        "affects_attacks": True,
        "affects_saves": True,
        "affects_ability_checks": False,
        "affects_damage": False,
    }
    restored = BuffItem(**d)
    assert restored == buf


def test_buff_item_defaults():
    """BuffItem defaults: Attacks=True, Saves=True, Checks=False, Damage=False."""
    buf = BuffItem(name="Bless", bonus_value="+1d4")
    assert buf.affects_attacks is True
    assert buf.affects_saves is True
    assert buf.affects_ability_checks is False
    assert buf.affects_damage is False


def test_monster_modification_from_dict_migrates_old_buff_targets():
    """MonsterModification.from_dict() migrates old 'targets' string to 4 boolean fields."""
    data = {
        "base_name": "Goblin",
        "buffs": [{"name": "Bless", "bonus_value": "+1d4", "targets": "attack_rolls"}],
    }
    mod = MonsterModification.from_dict(data)
    assert len(mod.buffs) == 1
    buf = mod.buffs[0]
    assert buf.affects_attacks is True
    assert buf.affects_saves is False
    assert buf.affects_ability_checks is False
    assert buf.affects_damage is False


def test_monster_modification_from_dict_migrates_saving_throws_target():
    """MonsterModification.from_dict() migrates 'saving_throws' target correctly."""
    data = {
        "base_name": "Goblin",
        "buffs": [{"name": "Bane", "bonus_value": "-1d4", "targets": "saving_throws"}],
    }
    mod = MonsterModification.from_dict(data)
    buf = mod.buffs[0]
    assert buf.affects_attacks is False
    assert buf.affects_saves is True
    assert buf.affects_ability_checks is False
    assert buf.affects_damage is False


def test_monster_modification_from_dict_migrates_all_target():
    """MonsterModification.from_dict() migrates 'all' target to all True."""
    data = {
        "base_name": "Goblin",
        "buffs": [{"name": "PowerSurge", "bonus_value": "+2", "targets": "all"}],
    }
    mod = MonsterModification.from_dict(data)
    buf = mod.buffs[0]
    assert buf.affects_attacks is True
    assert buf.affects_saves is True
    assert buf.affects_ability_checks is True
    assert buf.affects_damage is True


def test_monster_modification_from_dict_old_format():
    """MonsterModification.from_dict() handles old JSON format (missing new fields)."""
    old_data = {"base_name": "Goblin"}
    mod = MonsterModification.from_dict(old_data)
    assert mod.base_name == "Goblin"
    assert mod.equipment == []
    assert mod.buffs == []
    assert mod.skills == {}
    assert mod.hp_formula is None
    assert mod.size is None


def test_monster_modification_from_dict_new_format():
    """MonsterModification.from_dict() reconstructs EquipmentItem and BuffItem lists."""
    data = {
        "base_name": "Goblin",
        "equipment": [{"item_type": "weapon", "item_name": "Shortsword", "magic_bonus": 1}],
        "buffs": [{"name": "Rage", "bonus_value": "+2", "affects_attacks": True, "affects_saves": False, "affects_ability_checks": False, "affects_damage": True}],
        "skills": {"Stealth": 6},
        "hp_formula": "2d6",
        "size": "Small",
    }
    mod = MonsterModification.from_dict(data)
    assert len(mod.equipment) == 1
    assert isinstance(mod.equipment[0], EquipmentItem)
    assert mod.equipment[0].item_name == "Shortsword"
    assert mod.equipment[0].magic_bonus == 1
    assert len(mod.buffs) == 1
    assert isinstance(mod.buffs[0], BuffItem)
    assert mod.buffs[0].name == "Rage"
    assert mod.buffs[0].affects_attacks is True
    assert mod.buffs[0].affects_damage is True
    assert mod.skills == {"Stealth": 6}
    assert mod.hp_formula == "2d6"
    assert mod.size == "Small"


def test_monster_modification_from_dict_filters_unknown_keys():
    """MonsterModification.from_dict() ignores unknown future fields gracefully."""
    data = {"base_name": "Orc", "future_unknown_field": "should_be_ignored"}
    mod = MonsterModification.from_dict(data)
    assert mod.base_name == "Orc"
    assert not hasattr(mod, "future_unknown_field")


def test_skill_to_ability_has_18_entries():
    """SKILL_TO_ABILITY maps exactly 18 D&D 5e skills."""
    assert len(SKILL_TO_ABILITY) == 18


def test_skill_to_ability_covers_expected_abilities():
    """SKILL_TO_ABILITY covers the 5 ability scores that govern skills (CON has no skill in 5e)."""
    abilities = set(SKILL_TO_ABILITY.values())
    # D&D 5e has no CON-based skill — all other 5 abilities are represented
    assert abilities == {"STR", "DEX", "INT", "WIS", "CHA"}
    assert "CON" not in abilities
