"""TDD tests for the 5etools blockquote statblock parser.

Fixtures are derived from the actual bestiary(1).md content in .claude/.
All behavior specified here is tested against parse_fivetools() output.
"""
from src.parser.formats.fivetools import parse_fivetools
from src.parser.models import ParseResult


# ---------------------------------------------------------------------------
# Test fixtures — derived from bestiary(1).md format
# ---------------------------------------------------------------------------

MEDUSA_BLOCK = """\
___
>## Medusa
>*Medium Monstrosity, Lawful Evil*
>___
>- **Armor Class** 15 (natural armor)
>- **Hit Points** 127 (17d8 + 51)
>- **Speed** 30 ft.
>- **Initiative** +2 (12)
>___
>|STR|DEX|CON|INT|WIS|CHA|
>|:---:|:---:|:---:|:---:|:---:|:---:|
>|10 (+0)|15 (+2)|16 (+3)|12 (+1)|13 (+1)|15 (+2)|
>___
>- **Saving Throws** Dex +5, Con +6, Wis +4, Cha +5
>- **Skills** Deception +5, Insight +4, Perception +4, Stealth +5
>- **Challenge** 6 (XP 2,300; PB +3)
>___
>***Petrifying Gaze.*** When a creature that can see the medusa's eyes starts its turn within 30 feet of the medusa, the medusa can force it to make a DC 14 Constitution saving throw.
>
>### Actions
>***Multiattack.*** The medusa makes either three melee attacks—one with its snake hair and two with its shortsword—or two ranged attacks with its longbow.
>
>***Snake Hair.*** *Melee Weapon Attack:*  +5 to hit, reach 5 ft., one creature. *Hit:* 4 (1d4 + 2) piercing damage plus 14 (4d6) poison damage.
>
>***Shortsword.*** *Melee Weapon Attack:*  +5 to hit, reach 5 ft., one target. *Hit:* 5 (1d6 + 2) piercing damage.
>
>***Longbow.*** *Ranged Weapon Attack:*  +5 to hit, range 150/600 ft., one target. *Hit:* 6 (1d8 + 2) piercing damage plus 7 (2d6) poison damage."""

GOBLIN_BLOCK = """\
___
>## Goblin
>*Small Humanoid (Goblinoid), Neutral Evil*
>___
>- **Armor Class** 15 (leather armor, shield)
>- **Hit Points** 7 (2d6)
>- **Speed** 30 ft.
>___
>|STR|DEX|CON|INT|WIS|CHA|
>|:---:|:---:|:---:|:---:|:---:|:---:|
>|8 (-1)|14 (+2)|10 (+0)|10 (+0)|8 (-1)|8 (-1)|
>___
>- **Challenge** 1/4 (XP 50; PB +2)
>___
>### Actions
>***Scimitar.*** *Melee Weapon Attack:*  +4 to hit, reach 5 ft., one target. *Hit:* 5 (1d6 + 2) slashing damage."""

MEDUSA_WITH_LORE = MEDUSA_BLOCK + "\n\nMedusas are cursed beings.\n\nThey dwell in ruins."

MISSING_AC_BLOCK = """\
___
>## Medusa
>*Medium Monstrosity, Lawful Evil*
>___
>- **Hit Points** 127 (17d8 + 51)
>- **Speed** 30 ft.
>___
>|STR|DEX|CON|INT|WIS|CHA|
>|:---:|:---:|:---:|:---:|:---:|:---:|
>|10 (+0)|15 (+2)|16 (+3)|12 (+1)|13 (+1)|15 (+2)|
>___
>- **Challenge** 6 (XP 2,300; PB +3)
>___
>### Actions
>***Multiattack.*** The medusa makes three attacks."""

TWO_BLOCK = MEDUSA_BLOCK + "\n\n" + GOBLIN_BLOCK


# ---------------------------------------------------------------------------
# Single-monster parsing: basic fields
# ---------------------------------------------------------------------------

class TestMedusaBasicFields:
    """Verify correct extraction of name, AC, HP, CR from a real-format block."""

    def setup_method(self):
        result = parse_fivetools(MEDUSA_BLOCK)
        assert isinstance(result, ParseResult)
        assert len(result.monsters) == 1
        self.monster = result.monsters[0]

    def test_name(self):
        assert self.monster.name == "Medusa"

    def test_ac(self):
        assert self.monster.ac == 15

    def test_hp(self):
        assert self.monster.hp == 127

    def test_cr(self):
        assert self.monster.cr == "6"

    def test_creature_type(self):
        assert self.monster.creature_type == "Monstrosity"

    def test_ability_scores_all_six(self):
        scores = self.monster.ability_scores
        assert scores == {"STR": 10, "DEX": 15, "CON": 16, "INT": 12, "WIS": 13, "CHA": 15}

    def test_saving_throws(self):
        saves = self.monster.saves
        assert saves == {"DEX": 5, "CON": 6, "WIS": 4, "CHA": 5}

    def test_at_least_three_actions(self):
        # Petrifying Gaze (trait) + Multiattack + Snake Hair (+ Shortsword + Longbow)
        assert len(self.monster.actions) >= 3


# ---------------------------------------------------------------------------
# Action parsing: Snake Hair (has to_hit_bonus + multi-component damage)
# ---------------------------------------------------------------------------

class TestSnakeHairAction:
    """Verify correct parsing of an attack action with multi-component damage."""

    def setup_method(self):
        result = parse_fivetools(MEDUSA_BLOCK)
        self.monster = result.monsters[0]
        snake_hair_actions = [a for a in self.monster.actions if a.name == "Snake Hair"]
        assert len(snake_hair_actions) == 1, f"Expected 1 Snake Hair action, got {len(snake_hair_actions)}"
        self.action = snake_hair_actions[0]

    def test_to_hit_bonus(self):
        assert self.action.to_hit_bonus == 5

    def test_is_parsed(self):
        assert self.action.is_parsed is True

    def test_two_damage_parts(self):
        assert len(self.action.damage_parts) == 2

    def test_primary_damage_dice_expr(self):
        assert self.action.damage_parts[0].dice_expr == "1d4+2"

    def test_primary_damage_type(self):
        assert self.action.damage_parts[0].damage_type == "piercing"

    def test_secondary_damage_dice_expr(self):
        assert self.action.damage_parts[1].dice_expr == "4d6"

    def test_secondary_damage_type(self):
        assert self.action.damage_parts[1].damage_type == "poison"

    def test_raw_text_non_empty(self):
        assert self.action.raw_text != ""


# ---------------------------------------------------------------------------
# Action parsing: Multiattack (no attack roll)
# ---------------------------------------------------------------------------

class TestMultiattackAction:
    """Verify that non-attack actions are stored with raw_text and is_parsed=False."""

    def setup_method(self):
        result = parse_fivetools(MEDUSA_BLOCK)
        self.monster = result.monsters[0]
        multiattack_actions = [a for a in self.monster.actions if a.name == "Multiattack"]
        assert len(multiattack_actions) == 1, f"Expected 1 Multiattack action, got {len(multiattack_actions)}"
        self.action = multiattack_actions[0]

    def test_to_hit_bonus_is_none(self):
        assert self.action.to_hit_bonus is None

    def test_is_parsed_false(self):
        assert self.action.is_parsed is False

    def test_raw_text_contains_multiattack(self):
        assert "Multiattack" in self.action.raw_text


# ---------------------------------------------------------------------------
# Multi-monster file parsing
# ---------------------------------------------------------------------------

class TestMultiMonsterFile:
    """Verify that two statblocks in one file produce two Monster objects."""

    def setup_method(self):
        self.result = parse_fivetools(TWO_BLOCK)

    def test_two_monsters_returned(self):
        assert len(self.result.monsters) == 2

    def test_first_monster_name(self):
        assert self.result.monsters[0].name == "Medusa"

    def test_second_monster_name(self):
        assert self.result.monsters[1].name == "Goblin"


# ---------------------------------------------------------------------------
# Incomplete monster (missing required field)
# ---------------------------------------------------------------------------

class TestMissingACBlock:
    """Verify tolerant parsing: missing AC sets incomplete=True with sentinel 0."""

    def setup_method(self):
        self.result = parse_fivetools(MISSING_AC_BLOCK)
        assert len(self.result.monsters) == 1
        self.monster = self.result.monsters[0]

    def test_incomplete_flag_set(self):
        assert self.monster.incomplete is True

    def test_ac_sentinel_zero(self):
        assert self.monster.ac == 0

    def test_no_failures_recorded(self):
        # Name was found, so this is incomplete (not failed)
        assert self.result.failures == []


# ---------------------------------------------------------------------------
# Lore capture
# ---------------------------------------------------------------------------

class TestLoreCapture:
    """Verify that plain paragraphs after a statblock are captured in lore."""

    def setup_method(self):
        result = parse_fivetools(MEDUSA_WITH_LORE)
        assert len(result.monsters) == 1
        self.monster = result.monsters[0]

    def test_lore_contains_cursed_beings(self):
        assert "cursed beings" in self.monster.lore


# ---------------------------------------------------------------------------
# No-statblock file (no >## heading)
# ---------------------------------------------------------------------------

def test_no_statblock_returns_empty_result():
    """Files with no blockquote statblock produce empty ParseResult without crashing."""
    result = parse_fivetools("# Just a title\nSome text without any statblock")
    assert isinstance(result, ParseResult)
    assert result.monsters == []
    assert result.failures == []


def test_empty_string_returns_empty_result():
    """Empty string input produces empty ParseResult without crashing."""
    result = parse_fivetools("")
    assert isinstance(result, ParseResult)
    assert result.monsters == []
    assert result.failures == []


# ---------------------------------------------------------------------------
# Goblin CR fraction parsing
# ---------------------------------------------------------------------------

def test_goblin_cr_fraction():
    """CR values expressed as fractions (1/4) are parsed correctly."""
    result = parse_fivetools(GOBLIN_BLOCK)
    assert len(result.monsters) == 1
    assert result.monsters[0].cr == "1/4"


def test_goblin_ability_scores():
    """Goblin ability scores extracted correctly from pipe table."""
    result = parse_fivetools(GOBLIN_BLOCK)
    scores = result.monsters[0].ability_scores
    assert scores == {"STR": 8, "DEX": 14, "CON": 10, "INT": 10, "WIS": 8, "CHA": 8}
