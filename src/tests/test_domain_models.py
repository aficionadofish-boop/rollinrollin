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
