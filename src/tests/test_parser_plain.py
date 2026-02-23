"""TDD tests for the plain Markdown format parser.

Format signature: ## Monster Name headings + - **Armor Class** N bullet lines.
No blockquote '>' prefix. Actions after ### Actions heading.
"""
import pytest
from src.parser.formats.plain import parse_plain
from src.parser.models import ParseResult


# ---------------------------------------------------------------------------
# Fixtures: plain Markdown statblocks
# ---------------------------------------------------------------------------

PLAIN_GOBLIN = """\
## Goblin
*Small Humanoid (goblinoid), Neutral Evil*

- **Armor Class** 15 (leather armor, shield)
- **Hit Points** 7 (2d6)
- **Speed** 30 ft.

|STR|DEX|CON|INT|WIS|CHA|
|:---:|:---:|:---:|:---:|:---:|:---:|
|8 (-1)|14 (+2)|10 (+0)|10 (+0)|8 (-1)|8 (-1)|

- **Challenge** 1/4 (50 XP)

### Actions

***Scimitar.*** *Melee Weapon Attack: +4 to hit*, reach 5 ft., one target. *Hit: 7 (1d6 + 2) slashing damage.*
"""

PLAIN_MISSING_CR = """\
## Skeleton
*Medium Undead, Lawful Evil*

- **Armor Class** 13 (armor scraps)
- **Hit Points** 13 (2d8+4)
- **Speed** 30 ft.

### Actions

***Shortsword.*** *Melee Weapon Attack: +4 to hit*, reach 5 ft., one target. *Hit: 5 (1d6 + 2) piercing damage.*
"""

PLAIN_NONATTACK = """\
## Specter
*Medium Undead, Chaotic Evil*

- **Armor Class** 12
- **Hit Points** 22 (5d8)
- **Speed** 0 ft., fly 50 ft. (hover)

- **Challenge** 1 (200 XP)

### Actions

***Life Drain.*** The specter targets one creature it can see within 5 feet. The target must succeed on a DC 10 Constitution saving throw or take 10 (3d6) necrotic damage.
"""

PLAIN_TWO_MONSTERS = """\
## Goblin
*Small Humanoid (goblinoid), Neutral Evil*

- **Armor Class** 15
- **Hit Points** 7 (2d6)
- **Challenge** 1/4 (50 XP)

### Actions

***Scimitar.*** *Melee Weapon Attack: +4 to hit*, reach 5 ft., one target. *Hit: 7 (1d6 + 2) slashing damage.*

## Hobgoblin
*Medium Humanoid (goblinoid), Lawful Evil*

- **Armor Class** 18 (chain mail, shield)
- **Hit Points** 11 (2d8+2)
- **Challenge** 1/2 (100 XP)

### Actions

***Longsword.*** *Melee Weapon Attack: +3 to hit*, reach 5 ft., one target. *Hit: 7 (1d8 + 3) slashing damage.*
"""

PLAIN_WITH_SAVES = """\
## Mage
*Medium Humanoid, Neutral*

- **Armor Class** 12 (15 with mage armor)
- **Hit Points** 40 (9d8)
- **Speed** 30 ft.
- **Saving Throws** Int +6, Wis +4

- **Challenge** 6 (2300 XP)

### Actions

***Dagger.*** *Melee Weapon Attack: +4 to hit*, reach 5 ft., one target. *Hit: 4 (1d4 + 2) piercing damage.*
"""


# ---------------------------------------------------------------------------
# Basic parsing: single monster
# ---------------------------------------------------------------------------

class TestPlainBasic:
    """Test that parse_plain returns a ParseResult with correct fields."""

    def test_returns_parse_result(self):
        result = parse_plain(PLAIN_GOBLIN)
        assert isinstance(result, ParseResult)

    def test_returns_one_monster(self):
        result = parse_plain(PLAIN_GOBLIN)
        assert len(result.monsters) == 1

    def test_monster_name(self):
        result = parse_plain(PLAIN_GOBLIN)
        assert result.monsters[0].name == "Goblin"

    def test_monster_ac(self):
        result = parse_plain(PLAIN_GOBLIN)
        assert result.monsters[0].ac == 15

    def test_monster_hp(self):
        result = parse_plain(PLAIN_GOBLIN)
        assert result.monsters[0].hp == 7

    def test_monster_cr(self):
        result = parse_plain(PLAIN_GOBLIN)
        assert result.monsters[0].cr == "1/4"

    def test_monster_not_incomplete(self):
        result = parse_plain(PLAIN_GOBLIN)
        assert result.monsters[0].incomplete is False

    def test_creature_type_extracted(self):
        result = parse_plain(PLAIN_GOBLIN)
        assert result.monsters[0].creature_type == "Humanoid"


# ---------------------------------------------------------------------------
# Ability scores
# ---------------------------------------------------------------------------

class TestPlainAbilityScores:
    """Test ability score extraction from pipe table."""

    def test_str_score(self):
        result = parse_plain(PLAIN_GOBLIN)
        assert result.monsters[0].ability_scores.get("STR") == 8

    def test_dex_score(self):
        result = parse_plain(PLAIN_GOBLIN)
        assert result.monsters[0].ability_scores.get("DEX") == 14


# ---------------------------------------------------------------------------
# Attack parsing
# ---------------------------------------------------------------------------

class TestPlainAttack:
    """Test standard attack line parsing."""

    def test_action_extracted(self):
        result = parse_plain(PLAIN_GOBLIN)
        assert len(result.monsters[0].actions) >= 1

    def test_action_name(self):
        result = parse_plain(PLAIN_GOBLIN)
        action = result.monsters[0].actions[0]
        assert action.name == "Scimitar"

    def test_to_hit_bonus(self):
        result = parse_plain(PLAIN_GOBLIN)
        action = result.monsters[0].actions[0]
        assert action.to_hit_bonus == 4

    def test_dice_expr(self):
        result = parse_plain(PLAIN_GOBLIN)
        action = result.monsters[0].actions[0]
        assert len(action.damage_parts) >= 1
        assert "1d6" in action.damage_parts[0].dice_expr

    def test_is_parsed_true(self):
        result = parse_plain(PLAIN_GOBLIN)
        action = result.monsters[0].actions[0]
        assert action.is_parsed is True

    def test_raw_text_set(self):
        result = parse_plain(PLAIN_GOBLIN)
        action = result.monsters[0].actions[0]
        assert action.raw_text != ""


# ---------------------------------------------------------------------------
# Missing field: incomplete flag
# ---------------------------------------------------------------------------

class TestPlainMissingField:
    """Test that missing CR sets incomplete=True with sentinel defaults."""

    def test_incomplete_flag_set(self):
        result = parse_plain(PLAIN_MISSING_CR)
        assert result.monsters[0].incomplete is True

    def test_cr_sentinel_question_mark(self):
        result = parse_plain(PLAIN_MISSING_CR)
        assert result.monsters[0].cr == "?"

    def test_no_exception_on_missing_field(self):
        """Must never raise."""
        try:
            parse_plain(PLAIN_MISSING_CR)
        except Exception as e:
            pytest.fail(f"parse_plain raised on missing field: {e}")


# ---------------------------------------------------------------------------
# Non-attack action: is_parsed=False, raw_text set
# ---------------------------------------------------------------------------

class TestPlainNonAttackAction:
    """Test that Life Drain-style actions without hit bonus have is_parsed=False."""

    def test_nonattack_is_parsed_false(self):
        result = parse_plain(PLAIN_NONATTACK)
        action = result.monsters[0].actions[0]
        assert action.is_parsed is False

    def test_nonattack_to_hit_none(self):
        result = parse_plain(PLAIN_NONATTACK)
        action = result.monsters[0].actions[0]
        assert action.to_hit_bonus is None

    def test_nonattack_raw_text_set(self):
        result = parse_plain(PLAIN_NONATTACK)
        action = result.monsters[0].actions[0]
        assert action.raw_text != ""


# ---------------------------------------------------------------------------
# Multi-monster file
# ---------------------------------------------------------------------------

class TestPlainMultiMonster:
    """Test parsing a file with multiple ## headings."""

    def test_two_monsters_returned(self):
        result = parse_plain(PLAIN_TWO_MONSTERS)
        assert len(result.monsters) == 2

    def test_first_monster_name(self):
        result = parse_plain(PLAIN_TWO_MONSTERS)
        assert result.monsters[0].name == "Goblin"

    def test_second_monster_name(self):
        result = parse_plain(PLAIN_TWO_MONSTERS)
        assert result.monsters[1].name == "Hobgoblin"

    def test_second_monster_cr(self):
        result = parse_plain(PLAIN_TWO_MONSTERS)
        assert result.monsters[1].cr == "1/2"

    def test_second_monster_ac(self):
        result = parse_plain(PLAIN_TWO_MONSTERS)
        assert result.monsters[1].ac == 18


# ---------------------------------------------------------------------------
# Saving throws
# ---------------------------------------------------------------------------

class TestPlainSavingThrows:
    def test_saves_extracted(self):
        result = parse_plain(PLAIN_WITH_SAVES)
        assert result.monsters[0].saves.get("INT") == 6

    def test_wis_save(self):
        result = parse_plain(PLAIN_WITH_SAVES)
        assert result.monsters[0].saves.get("WIS") == 4


# ---------------------------------------------------------------------------
# Edge cases
# ---------------------------------------------------------------------------

def test_empty_string_returns_empty_result():
    result = parse_plain("")
    assert isinstance(result, ParseResult)
    assert result.monsters == []


def test_no_heading_returns_empty_result():
    result = parse_plain("Just some text.\nNo ## heading here.")
    assert isinstance(result, ParseResult)
    assert result.monsters == []


def test_never_raises_on_malformed():
    malformed = "## \n- **Armor Class**\n- **Hit Points**\n"
    try:
        parse_plain(malformed)
    except Exception as e:
        pytest.fail(f"parse_plain raised on malformed input: {e}")
