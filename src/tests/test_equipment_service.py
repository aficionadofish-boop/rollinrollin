"""TDD test suite for EquipmentService.

Tests cover D&D 5e equipment math:
  EQUIP-01: Weapon to-hit and damage computation
  EQUIP-02: Ability score selection (STR/DEX/finesse/ranged/thrown)
  EQUIP-03: Weapon damage dice scaling by monster size
  EQUIP-04: Armor AC computation (light/medium/heavy with DEX limits)
  EQUIP-05: Stealth disadvantage flag from armor
  EQUIP-06: Strength requirement flag from armor
  EQUIP-07: Shield bonus (2 + magic_bonus)
  EQUIP-08: Spellcasting focus bonus (spell_attack and spell_save_dc)
"""
from __future__ import annotations

import pytest

from src.domain.models import Monster, Action
from src.equipment.data import (
    WeaponData,
    ArmorData,
    SRD_WEAPONS,
    SRD_ARMORS,
)
from src.equipment.service import EquipmentService


# ---------------------------------------------------------------------------
# Helper: build a Monster with specific ability scores, CR, and size
# ---------------------------------------------------------------------------

def _make_monster(
    str_score: int = 10,
    dex_score: int = 10,
    con_score: int = 10,
    int_score: int = 10,
    wis_score: int = 10,
    cha_score: int = 10,
    cr: str = "1",
    size: str = "Medium",
) -> Monster:
    """Create a Monster with the specified ability scores, CR, and size."""
    return Monster(
        name="Test Monster",
        ac=10,
        hp=10,
        cr=cr,
        size=size,
        ability_scores={
            "STR": str_score,
            "DEX": dex_score,
            "CON": con_score,
            "INT": int_score,
            "WIS": wis_score,
            "CHA": cha_score,
        },
    )


# ---------------------------------------------------------------------------
# Fixture: EquipmentService instance
# ---------------------------------------------------------------------------

@pytest.fixture
def svc() -> EquipmentService:
    return EquipmentService()


# ---------------------------------------------------------------------------
# Convenience: find weapon/armor by name
# ---------------------------------------------------------------------------

def _weapon(name: str) -> WeaponData:
    for w in SRD_WEAPONS:
        if w.name == name:
            return w
    raise KeyError(f"Weapon not found: {name!r}")


def _armor(name: str) -> ArmorData:
    for a in SRD_ARMORS:
        if a.name == name:
            return a
    raise KeyError(f"Armor not found: {name!r}")


# ===========================================================================
# EQUIP-01: Weapon to-hit and damage (STR-based, no finesse/ranged)
# ===========================================================================

class TestWeaponToHitAndDamage:
    """EQUIP-01: Basic weapon to-hit and damage computation."""

    def test_weapon_to_hit_str_monster(self, svc: EquipmentService) -> None:
        """STR 10 (mod +0), CR 1 (prof +2), Longsword +0 → to_hit = 0+2+0 = 2."""
        monster = _make_monster(str_score=10, cr="1")
        longsword = _weapon("Longsword")
        result = svc.compute_weapon_action(longsword, magic_bonus=0, monster=monster)
        assert result["to_hit_bonus"] == 2  # STR mod(0) + prof(2) + magic(0)

    def test_weapon_to_hit_magic_bonus(self, svc: EquipmentService) -> None:
        """STR 10 (mod +0), CR 1 (prof +2), Longsword +2 → to_hit = 0+2+2 = 4."""
        monster = _make_monster(str_score=10, cr="1")
        longsword = _weapon("Longsword")
        result = svc.compute_weapon_action(longsword, magic_bonus=2, monster=monster)
        assert result["to_hit_bonus"] == 4  # STR mod(0) + prof(2) + magic(2)

    def test_weapon_damage_bonus(self, svc: EquipmentService) -> None:
        """STR 10 (mod +0), Longsword +2 → damage_bonus = 0+2 = 2."""
        monster = _make_monster(str_score=10, cr="1")
        longsword = _weapon("Longsword")
        result = svc.compute_weapon_action(longsword, magic_bonus=2, monster=monster)
        assert result["damage_bonus"] == 2  # STR mod(0) + magic(2)

    def test_weapon_damage_dice_medium(self, svc: EquipmentService) -> None:
        """Medium monster with Longsword → damage_dice = '1d8' (no scaling)."""
        monster = _make_monster(size="Medium")
        longsword = _weapon("Longsword")
        result = svc.compute_weapon_action(longsword, magic_bonus=0, monster=monster)
        assert result["damage_dice"] == "1d8"

    def test_weapon_action_has_name(self, svc: EquipmentService) -> None:
        """Result dict includes weapon name."""
        monster = _make_monster()
        longsword = _weapon("Longsword")
        result = svc.compute_weapon_action(longsword, magic_bonus=0, monster=monster)
        assert result["name"] == "Longsword"

    def test_weapon_action_is_equipment_generated(self, svc: EquipmentService) -> None:
        """Result dict marks action as equipment-generated."""
        monster = _make_monster()
        longsword = _weapon("Longsword")
        result = svc.compute_weapon_action(longsword, magic_bonus=0, monster=monster)
        assert result["is_equipment_generated"] is True

    def test_weapon_action_has_damage_type(self, svc: EquipmentService) -> None:
        """Result dict includes weapon damage type."""
        monster = _make_monster()
        longsword = _weapon("Longsword")
        result = svc.compute_weapon_action(longsword, magic_bonus=0, monster=monster)
        assert result["damage_type"] == "slashing"

    def test_weapon_spotcheck_str16_cr5_magic2(self, svc: EquipmentService) -> None:
        """Spot-check: Longsword +2 on STR 16 (mod +3), CR 5 (prof +3), Medium → to_hit=8, damage_bonus=5, dice='1d8'."""
        monster = _make_monster(str_score=16, cr="5", size="Medium")
        longsword = _weapon("Longsword")
        result = svc.compute_weapon_action(longsword, magic_bonus=2, monster=monster)
        assert result["to_hit_bonus"] == 8   # STR(+3) + prof(+3) + magic(+2)
        assert result["damage_bonus"] == 5   # STR(+3) + magic(+2)
        assert result["damage_dice"] == "1d8"


# ===========================================================================
# EQUIP-02: Ability score selection (finesse, ranged, thrown)
# ===========================================================================

class TestAbilitySelection:
    """EQUIP-02: Correct ability score used for weapon attack rolls."""

    def test_finesse_uses_dex_when_higher(self, svc: EquipmentService) -> None:
        """Rapier (finesse): DEX 16 (mod +3) > STR 10 (mod +0) → uses DEX mod."""
        monster = _make_monster(str_score=10, dex_score=16, cr="1")
        rapier = _weapon("Rapier")
        result = svc.compute_weapon_action(rapier, magic_bonus=0, monster=monster)
        # CR 1 prof = 2; DEX mod = +3 → to_hit = 3+2 = 5
        assert result["to_hit_bonus"] == 5

    def test_finesse_uses_str_when_higher(self, svc: EquipmentService) -> None:
        """Rapier (finesse): STR 16 (mod +3) > DEX 10 (mod +0) → uses STR mod."""
        monster = _make_monster(str_score=16, dex_score=10, cr="1")
        rapier = _weapon("Rapier")
        result = svc.compute_weapon_action(rapier, magic_bonus=0, monster=monster)
        # CR 1 prof = 2; STR mod = +3 → to_hit = 3+2 = 5
        assert result["to_hit_bonus"] == 5

    def test_ranged_always_dex(self, svc: EquipmentService) -> None:
        """Longbow (ranged): STR 18 (mod +4), DEX 10 (mod +0) → still uses DEX."""
        monster = _make_monster(str_score=18, dex_score=10, cr="1")
        longbow = _weapon("Longbow")
        result = svc.compute_weapon_action(longbow, magic_bonus=0, monster=monster)
        # CR 1 prof = 2; DEX mod = +0 → to_hit = 0+2 = 2
        assert result["to_hit_bonus"] == 2

    def test_thrown_uses_str(self, svc: EquipmentService) -> None:
        """Javelin (thrown, not finesse): STR 16 (mod +3), DEX 10 (mod +0) → uses STR."""
        monster = _make_monster(str_score=16, dex_score=10, cr="1")
        javelin = _weapon("Javelin")
        result = svc.compute_weapon_action(javelin, magic_bonus=0, monster=monster)
        # CR 1 prof = 2; STR mod = +3 → to_hit = 3+2 = 5
        assert result["to_hit_bonus"] == 5

    def test_dagger_finesse_thrown_uses_dex_when_higher(self, svc: EquipmentService) -> None:
        """Dagger (finesse+thrown): DEX 16 (mod +3) > STR 10 (mod +0) → uses DEX."""
        monster = _make_monster(str_score=10, dex_score=16, cr="1")
        dagger = _weapon("Dagger")
        result = svc.compute_weapon_action(dagger, magic_bonus=0, monster=monster)
        # finesse wins → DEX mod +3; prof 2 → to_hit = 5
        assert result["to_hit_bonus"] == 5

    def test_dagger_finesse_thrown_uses_str_when_higher(self, svc: EquipmentService) -> None:
        """Dagger (finesse+thrown): STR 16 (mod +3) > DEX 10 (mod +0) → uses STR."""
        monster = _make_monster(str_score=16, dex_score=10, cr="1")
        dagger = _weapon("Dagger")
        result = svc.compute_weapon_action(dagger, magic_bonus=0, monster=monster)
        # finesse → pick higher (STR +3); prof 2 → to_hit = 5
        assert result["to_hit_bonus"] == 5

    def test_spot_check_rapier_dex18_str10(self, svc: EquipmentService) -> None:
        """Spot-check: Rapier on DEX 18 (mod +4), STR 10 (mod +0) → uses DEX (+4)."""
        monster = _make_monster(str_score=10, dex_score=18, cr="1")
        rapier = _weapon("Rapier")
        result = svc.compute_weapon_action(rapier, magic_bonus=0, monster=monster)
        # DEX mod +4 + prof 2 = 6
        assert result["to_hit_bonus"] == 6


# ===========================================================================
# EQUIP-03: Weapon damage dice scaling by monster size
# ===========================================================================

class TestSizeScaling:
    """EQUIP-03: Damage dice scale by monster size."""

    def test_size_scaling_medium_no_change(self, svc: EquipmentService) -> None:
        """Medium: 1d8 weapon → '1d8' (multiplier 1x)."""
        monster = _make_monster(size="Medium")
        longsword = _weapon("Longsword")
        result = svc.compute_weapon_action(longsword, magic_bonus=0, monster=monster)
        assert result["damage_dice"] == "1d8"

    def test_size_scaling_large(self, svc: EquipmentService) -> None:
        """Large: 1d8 weapon → '2d8' (multiplier 2x)."""
        monster = _make_monster(size="Large")
        longsword = _weapon("Longsword")
        result = svc.compute_weapon_action(longsword, magic_bonus=0, monster=monster)
        assert result["damage_dice"] == "2d8"

    def test_size_scaling_huge(self, svc: EquipmentService) -> None:
        """Huge: 1d8 weapon → '3d8' (multiplier 3x)."""
        monster = _make_monster(size="Huge")
        longsword = _weapon("Longsword")
        result = svc.compute_weapon_action(longsword, magic_bonus=0, monster=monster)
        assert result["damage_dice"] == "3d8"

    def test_size_scaling_gargantuan_2d6(self, svc: EquipmentService) -> None:
        """Gargantuan: 2d6 (Greatsword) → '8d6' (multiplier 4x)."""
        monster = _make_monster(size="Gargantuan")
        greatsword = _weapon("Greatsword")
        result = svc.compute_weapon_action(greatsword, magic_bonus=0, monster=monster)
        assert result["damage_dice"] == "8d6"

    def test_size_scaling_small_no_change(self, svc: EquipmentService) -> None:
        """Small: 1d8 weapon → '1d8' (multiplier 1x, same as Medium)."""
        monster = _make_monster(size="Small")
        longsword = _weapon("Longsword")
        result = svc.compute_weapon_action(longsword, magic_bonus=0, monster=monster)
        assert result["damage_dice"] == "1d8"

    def test_scale_dice_standalone(self, svc: EquipmentService) -> None:
        """scale_dice helper works correctly for 1d8 + Large."""
        from src.equipment.service import scale_dice
        assert scale_dice("1d8", "Large") == "2d8"
        assert scale_dice("2d6", "Gargantuan") == "8d6"
        assert scale_dice("1d12", "Huge") == "3d12"
        assert scale_dice("1d4", "Medium") == "1d4"


# ===========================================================================
# EQUIP-04: Armor AC computation (light/medium/heavy)
# ===========================================================================

class TestArmorAC:
    """EQUIP-04: Armor AC with DEX modifier and magic bonus."""

    def test_light_armor_full_dex(self, svc: EquipmentService) -> None:
        """Studded Leather (base 12, dex_limit=None) + DEX 16 (mod +3) → AC 15."""
        monster = _make_monster(dex_score=16)
        studded = _armor("Studded Leather")
        result = svc.compute_armor_ac(studded, magic_bonus=0, monster=monster)
        assert result["ac"] == 15  # 12 + 3 (full DEX)

    def test_medium_armor_dex_capped(self, svc: EquipmentService) -> None:
        """Half Plate (base 15, dex_limit=2) + DEX 18 (mod +4) → AC 17 (capped at +2)."""
        monster = _make_monster(dex_score=18)
        half_plate = _armor("Half Plate")
        result = svc.compute_armor_ac(half_plate, magic_bonus=0, monster=monster)
        assert result["ac"] == 17  # 15 + 2 (capped)

    def test_heavy_armor_no_dex(self, svc: EquipmentService) -> None:
        """Plate (base 18, dex_limit=0) + DEX 16 (mod +3) → AC 18 (no DEX)."""
        monster = _make_monster(dex_score=16)
        plate = _armor("Plate")
        result = svc.compute_armor_ac(plate, magic_bonus=0, monster=monster)
        assert result["ac"] == 18  # 18 + 0 (no DEX)

    def test_armor_magic_bonus(self, svc: EquipmentService) -> None:
        """Plate +2 → AC 20 (18 + 0 DEX + 2 magic)."""
        monster = _make_monster(dex_score=16)
        plate = _armor("Plate")
        result = svc.compute_armor_ac(plate, magic_bonus=2, monster=monster)
        assert result["ac"] == 20  # 18 + 0 (no DEX) + 2 magic

    def test_armor_result_has_armor_name(self, svc: EquipmentService) -> None:
        """Result dict includes armor_name."""
        monster = _make_monster()
        plate = _armor("Plate")
        result = svc.compute_armor_ac(plate, magic_bonus=0, monster=monster)
        assert result["armor_name"] == "Plate"

    def test_armor_result_has_magic_bonus(self, svc: EquipmentService) -> None:
        """Result dict includes magic_bonus used."""
        monster = _make_monster()
        plate = _armor("Plate")
        result = svc.compute_armor_ac(plate, magic_bonus=1, monster=monster)
        assert result["magic_bonus"] == 1

    def test_light_armor_no_dex_bonus_when_zero(self, svc: EquipmentService) -> None:
        """Light armor + DEX 10 (mod 0) → AC = base_ac + 0."""
        monster = _make_monster(dex_score=10)
        leather = _armor("Leather")
        result = svc.compute_armor_ac(leather, magic_bonus=0, monster=monster)
        assert result["ac"] == 11  # 11 + 0

    def test_spot_check_plate_dex14(self, svc: EquipmentService) -> None:
        """Spot-check: Plate +1 on DEX 14 (mod +2) monster → AC=19, stealth_disadvantage=True."""
        monster = _make_monster(dex_score=14)
        plate = _armor("Plate")
        result = svc.compute_armor_ac(plate, magic_bonus=1, monster=monster)
        assert result["ac"] == 19                    # 18 + 0 DEX + 1 magic
        assert result["stealth_disadvantage"] is True


# ===========================================================================
# EQUIP-05: Stealth disadvantage flag
# ===========================================================================

class TestStealthDisadvantage:
    """EQUIP-05: Stealth disadvantage computed from armor data."""

    def test_stealth_disadvantage_plate(self, svc: EquipmentService) -> None:
        """Plate armor → stealth_disadvantage=True."""
        monster = _make_monster()
        plate = _armor("Plate")
        result = svc.compute_armor_ac(plate, magic_bonus=0, monster=monster)
        assert result["stealth_disadvantage"] is True

    def test_no_stealth_disadvantage_leather(self, svc: EquipmentService) -> None:
        """Leather armor → stealth_disadvantage=False."""
        monster = _make_monster()
        leather = _armor("Leather")
        result = svc.compute_armor_ac(leather, magic_bonus=0, monster=monster)
        assert result["stealth_disadvantage"] is False

    def test_stealth_disadvantage_scale_mail(self, svc: EquipmentService) -> None:
        """Scale Mail → stealth_disadvantage=True."""
        monster = _make_monster()
        scale = _armor("Scale Mail")
        result = svc.compute_armor_ac(scale, magic_bonus=0, monster=monster)
        assert result["stealth_disadvantage"] is True

    def test_no_stealth_disadvantage_breastplate(self, svc: EquipmentService) -> None:
        """Breastplate → stealth_disadvantage=False."""
        monster = _make_monster()
        bp = _armor("Breastplate")
        result = svc.compute_armor_ac(bp, magic_bonus=0, monster=monster)
        assert result["stealth_disadvantage"] is False


# ===========================================================================
# EQUIP-06: Strength requirement flag
# ===========================================================================

class TestStrengthRequirement:
    """EQUIP-06: STR requirement met/not-met flag from armor."""

    def test_str_requirement_met(self, svc: EquipmentService) -> None:
        """Chain Mail (str_req=13), monster STR 14 → str_requirement_met=True."""
        monster = _make_monster(str_score=14)
        chain_mail = _armor("Chain Mail")
        result = svc.compute_armor_ac(chain_mail, magic_bonus=0, monster=monster)
        assert result["str_requirement_met"] is True

    def test_str_requirement_not_met(self, svc: EquipmentService) -> None:
        """Chain Mail (str_req=13), monster STR 10 → str_requirement_met=False."""
        monster = _make_monster(str_score=10)
        chain_mail = _armor("Chain Mail")
        result = svc.compute_armor_ac(chain_mail, magic_bonus=0, monster=monster)
        assert result["str_requirement_met"] is False

    def test_str_requirement_exactly_met(self, svc: EquipmentService) -> None:
        """Chain Mail (str_req=13), monster STR 13 → str_requirement_met=True."""
        monster = _make_monster(str_score=13)
        chain_mail = _armor("Chain Mail")
        result = svc.compute_armor_ac(chain_mail, magic_bonus=0, monster=monster)
        assert result["str_requirement_met"] is True

    def test_no_str_requirement(self, svc: EquipmentService) -> None:
        """Leather (str_req=0), any monster → str_requirement_met=True."""
        monster = _make_monster(str_score=6)  # even tiny STR
        leather = _armor("Leather")
        result = svc.compute_armor_ac(leather, magic_bonus=0, monster=monster)
        assert result["str_requirement_met"] is True


# ===========================================================================
# EQUIP-07: Shield bonus
# ===========================================================================

class TestShieldBonus:
    """EQUIP-07: Shield adds 2 + magic_bonus to AC."""

    def test_shield_basic(self, svc: EquipmentService) -> None:
        """Shield +0 → +2 AC bonus."""
        assert svc.compute_shield_bonus(magic_bonus=0) == 2

    def test_shield_magic_plus1(self, svc: EquipmentService) -> None:
        """Shield +1 → +3 AC bonus."""
        assert svc.compute_shield_bonus(magic_bonus=1) == 3

    def test_shield_magic_plus2(self, svc: EquipmentService) -> None:
        """Shield +2 → +4 AC bonus."""
        assert svc.compute_shield_bonus(magic_bonus=2) == 4

    def test_shield_magic_plus3(self, svc: EquipmentService) -> None:
        """Shield +3 → +5 AC bonus."""
        assert svc.compute_shield_bonus(magic_bonus=3) == 5


# ===========================================================================
# EQUIP-08: Spellcasting focus bonus
# ===========================================================================

class TestFocusBonus:
    """EQUIP-08: Spellcasting focus adds bonus to spell_attack and spell_save_dc."""

    def test_focus_bonus_spell_attack_plus2(self, svc: EquipmentService) -> None:
        """Focus +2 → spell_attack_bonus = 2."""
        result = svc.compute_focus_bonus(focus_magic_bonus=2)
        assert result["spell_attack_bonus"] == 2

    def test_focus_bonus_spell_dc_plus2(self, svc: EquipmentService) -> None:
        """Focus +2 → spell_dc_bonus = 2."""
        result = svc.compute_focus_bonus(focus_magic_bonus=2)
        assert result["spell_dc_bonus"] == 2

    def test_focus_bonus_plus1(self, svc: EquipmentService) -> None:
        """Focus +1 → spell_attack_bonus=1, spell_dc_bonus=1."""
        result = svc.compute_focus_bonus(focus_magic_bonus=1)
        assert result["spell_attack_bonus"] == 1
        assert result["spell_dc_bonus"] == 1

    def test_focus_bonus_plus3(self, svc: EquipmentService) -> None:
        """Focus +3 → spell_attack_bonus=3, spell_dc_bonus=3."""
        result = svc.compute_focus_bonus(focus_magic_bonus=3)
        assert result["spell_attack_bonus"] == 3
        assert result["spell_dc_bonus"] == 3


# ===========================================================================
# Proficiency bonus by CR — spot checks
# ===========================================================================

class TestProficiencyBonus:
    """Verify _PROF_BY_CR table is used correctly for various CRs."""

    def test_prof_cr_0(self, svc: EquipmentService) -> None:
        """CR 0 → prof +2."""
        monster = _make_monster(str_score=10, cr="0")
        longsword = _weapon("Longsword")
        result = svc.compute_weapon_action(longsword, magic_bonus=0, monster=monster)
        assert result["to_hit_bonus"] == 2  # 0 + 2

    def test_prof_cr_5(self, svc: EquipmentService) -> None:
        """CR 5 → prof +3."""
        monster = _make_monster(str_score=10, cr="5")
        longsword = _weapon("Longsword")
        result = svc.compute_weapon_action(longsword, magic_bonus=0, monster=monster)
        assert result["to_hit_bonus"] == 3  # 0 + 3

    def test_prof_cr_9(self, svc: EquipmentService) -> None:
        """CR 9 → prof +4."""
        monster = _make_monster(str_score=10, cr="9")
        longsword = _weapon("Longsword")
        result = svc.compute_weapon_action(longsword, magic_bonus=0, monster=monster)
        assert result["to_hit_bonus"] == 4  # 0 + 4

    def test_prof_cr_17(self, svc: EquipmentService) -> None:
        """CR 17 → prof +6."""
        monster = _make_monster(str_score=10, cr="17")
        longsword = _weapon("Longsword")
        result = svc.compute_weapon_action(longsword, magic_bonus=0, monster=monster)
        assert result["to_hit_bonus"] == 6  # 0 + 6
