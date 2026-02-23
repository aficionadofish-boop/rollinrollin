"""TDD tests for the Homebrewery/GM Binder format parser.

Format signature: ___ line delimiters + **Armor Class** bold labels (no '>' prefix).
Compact attack syntax: *MWA*: **+4, 1d6+2** slashing
Standard attack syntax: *Melee Weapon Attack: +4 to hit* ... *Hit: 7 (1d6 + 2) slashing damage*
"""
import pytest
from src.parser.formats.homebrewery import parse_homebrewery
from src.parser.models import ParseResult


# ---------------------------------------------------------------------------
# Minimal fixture: single Goblin statblock in Homebrewery format
# ---------------------------------------------------------------------------

HB_GOBLIN = """\
___
## Goblin
*Small Humanoid (goblinoid), Neutral Evil*
___
- **Armor Class** 15 (leather armor, shield)
- **Hit Points** 7 (2d6)
- **Speed** 30 ft.
___
|STR|DEX|CON|INT|WIS|CHA|
|:---:|:---:|:---:|:---:|:---:|:---:|
|8 (-1)|14 (+2)|10 (+0)|10 (+0)|8 (-1)|8 (-1)|
___
- **Challenge** 1/4 (50 XP)
___
### Actions
***Scimitar.*** *MWA*: **+4, 1d6+2** slashing
"""

# Standard attack syntax (Melee Weapon Attack style)
HB_GOBLIN_STANDARD = """\
___
## Goblin Standard
*Small Humanoid (goblinoid), Neutral Evil*
___
- **Armor Class** 15
- **Hit Points** 7 (2d6)
- **Speed** 30 ft.
___
- **Challenge** 1/4 (50 XP)
___
### Actions
***Scimitar.*** *Melee Weapon Attack: +4 to hit*, reach 5 ft., one target. *Hit: 7 (1d6 + 2) slashing damage.*
"""

# Monster with missing HP field
HB_MISSING_HP = """\
___
## Incomplete Orc
*Medium Humanoid (orc), Chaotic Evil*
___
- **Armor Class** 13
- **Speed** 30 ft.
___
- **Challenge** 1/2 (100 XP)
"""

# Monster with non-attack action (no attack syntax)
HB_NONATTACK_ACTION = """\
___
## Banshee
*Medium Undead, Chaotic Evil*
___
- **Armor Class** 12
- **Hit Points** 58 (13d8)
- **Speed** 0 ft., fly 40 ft.
___
- **Challenge** 4 (1100 XP)
___
### Actions
***Horrifying Visage.*** Each non-undead creature within 60 feet of the banshee must succeed on a DC 13 Wisdom saving throw or be frightened for 1 minute.
"""

# Multi-monster file: two ___ delimited blocks
HB_TWO_MONSTERS = """\
___
## Goblin
*Small Humanoid (goblinoid), Neutral Evil*
___
- **Armor Class** 15
- **Hit Points** 7 (2d6)
- **Challenge** 1/4 (50 XP)
___
### Actions
***Scimitar.*** *MWA*: **+4, 1d6+2** slashing
___
## Hobgoblin
*Medium Humanoid (goblinoid), Lawful Evil*
___
- **Armor Class** 18 (chain mail, shield)
- **Hit Points** 11 (2d8+2)
- **Challenge** 1/2 (100 XP)
___
### Actions
***Longsword.*** *MWA*: **+3, 1d8+1** slashing
"""


# ---------------------------------------------------------------------------
# Basic parsing: single monster
# ---------------------------------------------------------------------------

class TestHomebreweryBasic:
    """Test that parse_homebrewery returns a ParseResult with correct fields."""

    def test_returns_parse_result(self):
        result = parse_homebrewery(HB_GOBLIN)
        assert isinstance(result, ParseResult)

    def test_returns_one_monster(self):
        result = parse_homebrewery(HB_GOBLIN)
        assert len(result.monsters) == 1

    def test_monster_name(self):
        result = parse_homebrewery(HB_GOBLIN)
        assert result.monsters[0].name == "Goblin"

    def test_monster_ac(self):
        result = parse_homebrewery(HB_GOBLIN)
        assert result.monsters[0].ac == 15

    def test_monster_hp(self):
        result = parse_homebrewery(HB_GOBLIN)
        assert result.monsters[0].hp == 7

    def test_monster_cr(self):
        result = parse_homebrewery(HB_GOBLIN)
        assert result.monsters[0].cr == "1/4"

    def test_monster_not_incomplete(self):
        result = parse_homebrewery(HB_GOBLIN)
        assert result.monsters[0].incomplete is False


# ---------------------------------------------------------------------------
# Compact attack syntax: *MWA*: **+4, 1d6+2** slashing
# ---------------------------------------------------------------------------

class TestHomebreweryCompactAttack:
    """Test Homebrewery-specific compact attack syntax."""

    def test_action_extracted(self):
        result = parse_homebrewery(HB_GOBLIN)
        assert len(result.monsters[0].actions) >= 1

    def test_action_name_scimitar(self):
        result = parse_homebrewery(HB_GOBLIN)
        action = result.monsters[0].actions[0]
        assert action.name == "Scimitar"

    def test_compact_to_hit_bonus(self):
        result = parse_homebrewery(HB_GOBLIN)
        action = result.monsters[0].actions[0]
        assert action.to_hit_bonus == 4

    def test_compact_dice_expr(self):
        result = parse_homebrewery(HB_GOBLIN)
        action = result.monsters[0].actions[0]
        assert len(action.damage_parts) >= 1
        assert "1d6" in action.damage_parts[0].dice_expr

    def test_compact_is_parsed_true(self):
        result = parse_homebrewery(HB_GOBLIN)
        action = result.monsters[0].actions[0]
        assert action.is_parsed is True

    def test_compact_raw_text_set(self):
        result = parse_homebrewery(HB_GOBLIN)
        action = result.monsters[0].actions[0]
        assert action.raw_text != ""


# ---------------------------------------------------------------------------
# Standard attack syntax fallback
# ---------------------------------------------------------------------------

class TestHomebreweryStandardAttack:
    """Test that standard Melee Weapon Attack syntax is also handled."""

    def test_standard_action_extracted(self):
        result = parse_homebrewery(HB_GOBLIN_STANDARD)
        assert len(result.monsters[0].actions) >= 1

    def test_standard_to_hit_bonus(self):
        result = parse_homebrewery(HB_GOBLIN_STANDARD)
        action = result.monsters[0].actions[0]
        assert action.to_hit_bonus == 4

    def test_standard_dice_expr(self):
        result = parse_homebrewery(HB_GOBLIN_STANDARD)
        action = result.monsters[0].actions[0]
        assert len(action.damage_parts) >= 1
        assert "1d6" in action.damage_parts[0].dice_expr

    def test_standard_is_parsed_true(self):
        result = parse_homebrewery(HB_GOBLIN_STANDARD)
        action = result.monsters[0].actions[0]
        assert action.is_parsed is True


# ---------------------------------------------------------------------------
# Missing field: incomplete flag
# ---------------------------------------------------------------------------

class TestHomebreweryMissingField:
    """Test that missing HP sets incomplete=True with sentinel defaults."""

    def test_incomplete_flag_set(self):
        result = parse_homebrewery(HB_MISSING_HP)
        assert result.monsters[0].incomplete is True

    def test_hp_sentinel_zero(self):
        result = parse_homebrewery(HB_MISSING_HP)
        assert result.monsters[0].hp == 0

    def test_no_exception_on_missing_field(self):
        """Must never raise — tolerant parse only."""
        try:
            parse_homebrewery(HB_MISSING_HP)
        except Exception as e:
            pytest.fail(f"parse_homebrewery raised on missing field: {e}")


# ---------------------------------------------------------------------------
# Non-attack action: is_parsed=False, raw_text set
# ---------------------------------------------------------------------------

class TestHomebreweryNonAttackAction:
    """Test that actions without attack syntax have is_parsed=False."""

    def test_nonattack_is_parsed_false(self):
        result = parse_homebrewery(HB_NONATTACK_ACTION)
        action = result.monsters[0].actions[0]
        assert action.is_parsed is False

    def test_nonattack_to_hit_none(self):
        result = parse_homebrewery(HB_NONATTACK_ACTION)
        action = result.monsters[0].actions[0]
        assert action.to_hit_bonus is None

    def test_nonattack_raw_text_set(self):
        result = parse_homebrewery(HB_NONATTACK_ACTION)
        action = result.monsters[0].actions[0]
        assert action.raw_text != ""


# ---------------------------------------------------------------------------
# Multi-monster file
# ---------------------------------------------------------------------------

class TestHomebreweryMultiMonster:
    """Test parsing a file with multiple ___ delimited statblocks."""

    def test_two_monsters_returned(self):
        result = parse_homebrewery(HB_TWO_MONSTERS)
        assert len(result.monsters) == 2

    def test_first_monster_name(self):
        result = parse_homebrewery(HB_TWO_MONSTERS)
        assert result.monsters[0].name == "Goblin"

    def test_second_monster_name(self):
        result = parse_homebrewery(HB_TWO_MONSTERS)
        assert result.monsters[1].name == "Hobgoblin"

    def test_second_monster_ac(self):
        result = parse_homebrewery(HB_TWO_MONSTERS)
        assert result.monsters[1].ac == 18


# ---------------------------------------------------------------------------
# Edge cases
# ---------------------------------------------------------------------------

def test_empty_string_returns_empty_result():
    result = parse_homebrewery("")
    assert isinstance(result, ParseResult)
    assert result.monsters == []


def test_no_statblock_returns_empty_result():
    result = parse_homebrewery("# Just a heading\nSome text with no monster blocks.")
    assert isinstance(result, ParseResult)
    assert result.monsters == []


def test_never_raises_on_malformed():
    malformed = "___\n## \n___\n- **Armor Class**\n- **Hit Points**\n"
    try:
        parse_homebrewery(malformed)
    except Exception as e:
        pytest.fail(f"parse_homebrewery raised on malformed input: {e}")
