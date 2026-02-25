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


# ---------------------------------------------------------------------------
# Module-level helper
# ---------------------------------------------------------------------------

def scale_dice(base_dice: str, size: str) -> str:
    """Scale weapon damage dice by monster size.

    Parameters
    ----------
    base_dice : str
        Base dice string in 'NdM' format (e.g. '1d8', '2d6').
    size : str
        Monster size: 'Tiny', 'Small', 'Medium', 'Large', 'Huge', 'Gargantuan'.

    Returns
    -------
    str
        Scaled dice string (e.g. '2d8' for Large 1d8).

    Raises
    ------
    NotImplementedError
        Always — this is a stub for the RED phase.
    """
    raise NotImplementedError


# ---------------------------------------------------------------------------
# EquipmentService
# ---------------------------------------------------------------------------

class EquipmentService:
    """Computes D&D 5e equipment math for the monster editor.

    Pure calculation class — no state, no Qt, no I/O.
    """

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
            SRD weapon entry.
        magic_bonus : int
            Magic enhancement bonus (+0/+1/+2/+3).
        monster : Monster
            Monster receiving the weapon.

        Returns
        -------
        dict with keys: name, to_hit_bonus, damage_dice, damage_bonus,
                        damage_type, is_equipment_generated.

        Raises
        ------
        NotImplementedError
            Always — this is a stub for the RED phase.
        """
        raise NotImplementedError

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
            SRD armor entry.
        magic_bonus : int
            Magic enhancement bonus (+0/+1/+2/+3).
        monster : Monster
            Monster wearing the armor.

        Returns
        -------
        dict with keys: ac, stealth_disadvantage, str_requirement_met,
                        armor_name, magic_bonus.

        Raises
        ------
        NotImplementedError
            Always — this is a stub for the RED phase.
        """
        raise NotImplementedError

    def compute_shield_bonus(self, magic_bonus: int) -> int:
        """Return the AC bonus from a shield.

        Parameters
        ----------
        magic_bonus : int
            Magic enhancement bonus (+0/+1/+2/+3).

        Returns
        -------
        int
            2 + magic_bonus.

        Raises
        ------
        NotImplementedError
            Always — this is a stub for the RED phase.
        """
        raise NotImplementedError

    def compute_focus_bonus(self, focus_magic_bonus: int) -> dict:
        """Return spell attack and spell save DC bonuses from a focus.

        Parameters
        ----------
        focus_magic_bonus : int
            Focus magic bonus (+1/+2/+3).

        Returns
        -------
        dict with keys: spell_attack_bonus, spell_dc_bonus.

        Raises
        ------
        NotImplementedError
            Always — this is a stub for the RED phase.
        """
        raise NotImplementedError
