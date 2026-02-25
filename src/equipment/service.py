"""EquipmentService — D&D 5e equipment math for the monster editor.

Computes weapon to-hit/damage, armor AC, shield bonus, and spellcasting focus
bonus. Pure Python — no Qt, no I/O, no side effects.

Public API:
    scale_dice(base_dice, size) -> str
    EquipmentService.compute_weapon_action(weapon, magic_bonus, monster) -> dict
    EquipmentService.compute_armor_ac(armor, magic_bonus, monster) -> dict
    EquipmentService.compute_shield_bonus(magic_bonus) -> int
    EquipmentService.compute_focus_bonus(focus_magic_bonus) -> dict
"""
from __future__ import annotations

from src.domain.models import Monster
from src.equipment.data import WeaponData, ArmorData, SIZE_DICE_MULTIPLIER


# ---------------------------------------------------------------------------
# Proficiency bonus table indexed by CR string
# Inline copy — avoids coupling to MonsterMathEngine internals.
# ---------------------------------------------------------------------------

_PROF_BY_CR: dict[str, int] = {
    "0": 2, "1/8": 2, "1/4": 2, "1/2": 2,
    "1": 2, "2": 2, "3": 2, "4": 2,
    "5": 3, "6": 3, "7": 3, "8": 3,
    "9": 4, "10": 4, "11": 4, "12": 4,
    "13": 5, "14": 5, "15": 5, "16": 5,
    "17": 6, "18": 6, "19": 6, "20": 6,
    "21": 7, "22": 7, "23": 7, "24": 7,
    "25": 8, "26": 8, "27": 8, "28": 8,
    "29": 9, "30": 9,
}


def _ability_mod(score: int) -> int:
    """Compute D&D 5e ability modifier using floor division (matches engine.py)."""
    return (score - 10) // 2


# ---------------------------------------------------------------------------
# Module-level helper: scale weapon dice by size
# ---------------------------------------------------------------------------

def scale_dice(base_dice: str, size: str) -> str:
    """Scale weapon damage dice by monster size.

    Parses 'NdM' format, multiplies N by SIZE_DICE_MULTIPLIER[size],
    returns 'ScaledNdM'.

    Parameters
    ----------
    base_dice : str
        Base dice string in 'NdM' format (e.g. '1d8', '2d6').
    size : str
        Monster size: 'Tiny', 'Small', 'Medium', 'Large', 'Huge', 'Gargantuan'.

    Returns
    -------
    str
        Scaled dice string (e.g. '2d8' for Large 1d8, '8d6' for Gargantuan 2d6).

    Examples
    --------
    >>> scale_dice('1d8', 'Large')
    '2d8'
    >>> scale_dice('2d6', 'Gargantuan')
    '8d6'
    """
    multiplier = SIZE_DICE_MULTIPLIER.get(size, 1)
    n_str, die = base_dice.split('d')
    scaled_n = int(n_str) * multiplier
    return f"{scaled_n}d{die}"


# ---------------------------------------------------------------------------
# EquipmentService
# ---------------------------------------------------------------------------

class EquipmentService:
    """Computes D&D 5e equipment math for the monster editor.

    Pure calculation class — no state, no Qt, no I/O.

    Design notes:
    - Proficiency bonus and ability modifiers are computed inline to avoid
      coupling to MonsterMathEngine (which takes a full Monster with all fields).
    - Ability selection for finesse weapons: uses whichever of DEX/STR mod is
      higher. Ranged (non-thrown) always use DEX. Thrown non-finesse use STR.
    """

    # ------------------------------------------------------------------
    # Weapon action
    # ------------------------------------------------------------------

    def compute_weapon_action(
        self,
        weapon: WeaponData,
        magic_bonus: int,
        monster: Monster,
    ) -> dict:
        """Compute weapon action stats (to-hit bonus, damage dice, damage bonus).

        Parameters
        ----------
        weapon : WeaponData
            SRD weapon entry with damage dice and property flags.
        magic_bonus : int
            Magic enhancement bonus (+0/+1/+2/+3).
        monster : Monster
            Monster receiving the weapon. Uses monster.cr, monster.ability_scores,
            and monster.size.

        Returns
        -------
        dict
            Keys: name, to_hit_bonus, damage_dice, damage_bonus,
                  damage_type, is_equipment_generated.

        Notes
        -----
        D&D 5e rules:
        - Ranged (non-thrown): always DEX
        - Finesse: use whichever of DEX/STR modifier is higher
        - Thrown (non-finesse): use STR
        - Default: STR
        """
        str_score = monster.ability_scores.get("STR", 10)
        dex_score = monster.ability_scores.get("DEX", 10)
        str_mod = _ability_mod(str_score)
        dex_mod = _ability_mod(dex_score)

        # Ability selection per D&D 5e rules
        if weapon.is_ranged and not weapon.is_thrown:
            # Pure ranged weapons (bow, crossbow) always use DEX
            ability_mod = dex_mod
        elif weapon.is_finesse:
            # Finesse: pick the higher of STR or DEX
            ability_mod = max(str_mod, dex_mod)
        else:
            # Default (melee) and thrown non-finesse: use STR
            ability_mod = str_mod

        prof_bonus = _PROF_BY_CR.get(monster.cr, 2)

        to_hit_bonus = ability_mod + prof_bonus + magic_bonus
        damage_dice = scale_dice(weapon.damage_dice, monster.size)
        damage_bonus = ability_mod + magic_bonus

        return {
            "name": weapon.name,
            "to_hit_bonus": to_hit_bonus,
            "damage_dice": damage_dice,
            "damage_bonus": damage_bonus,
            "damage_type": weapon.damage_type,
            "is_equipment_generated": True,
        }

    # ------------------------------------------------------------------
    # Armor AC
    # ------------------------------------------------------------------

    def compute_armor_ac(
        self,
        armor: ArmorData,
        magic_bonus: int,
        monster: Monster,
    ) -> dict:
        """Compute effective AC from armor, DEX modifier, and magic bonus.

        Parameters
        ----------
        armor : ArmorData
            SRD armor entry with base_ac, dex_limit, stealth_disadvantage,
            and str_requirement.
        magic_bonus : int
            Magic enhancement bonus (+0/+1/+2/+3).
        monster : Monster
            Monster wearing the armor. Uses monster.ability_scores["DEX"] and
            monster.ability_scores["STR"].

        Returns
        -------
        dict
            Keys: ac, stealth_disadvantage, str_requirement_met,
                  armor_name, magic_bonus.

        Notes
        -----
        D&D 5e armor DEX rules:
        - dex_limit is None (light): full DEX modifier
        - dex_limit is 0 (heavy): no DEX contribution
        - dex_limit is 2 (medium): capped at +2
        """
        dex_score = monster.ability_scores.get("DEX", 10)
        str_score = monster.ability_scores.get("STR", 10)
        dex_mod = _ability_mod(dex_score)

        if armor.dex_limit is None:
            # Light armor — full DEX modifier
            ac_dex = dex_mod
        elif armor.dex_limit == 0:
            # Heavy armor — no DEX contribution
            ac_dex = 0
        else:
            # Medium armor — DEX capped at dex_limit
            ac_dex = min(dex_mod, armor.dex_limit)

        total_ac = armor.base_ac + ac_dex + magic_bonus

        str_requirement_met = (str_score >= armor.str_requirement)

        return {
            "ac": total_ac,
            "stealth_disadvantage": armor.stealth_disadvantage,
            "str_requirement_met": str_requirement_met,
            "armor_name": armor.name,
            "magic_bonus": magic_bonus,
        }

    # ------------------------------------------------------------------
    # Shield bonus
    # ------------------------------------------------------------------

    def compute_shield_bonus(self, magic_bonus: int) -> int:
        """Return the AC bonus from a shield.

        Parameters
        ----------
        magic_bonus : int
            Magic enhancement bonus (+0/+1/+2/+3).

        Returns
        -------
        int
            2 + magic_bonus (shields always grant +2 AC base).
        """
        return 2 + magic_bonus

    # ------------------------------------------------------------------
    # Spellcasting focus bonus
    # ------------------------------------------------------------------

    def compute_focus_bonus(self, focus_magic_bonus: int) -> dict:
        """Return spell attack and spell save DC bonuses from a spellcasting focus.

        Parameters
        ----------
        focus_magic_bonus : int
            Focus magic bonus (+1/+2/+3). A +0 focus is not valid per the
            equipment constraints but handled gracefully (returns 0 bonuses).

        Returns
        -------
        dict
            Keys: spell_attack_bonus, spell_dc_bonus.
            Both equal focus_magic_bonus.
        """
        return {
            "spell_attack_bonus": focus_magic_bonus,
            "spell_dc_bonus": focus_magic_bonus,
        }
