"""SRD weapon and armor data tables.

Contains static data structures for all SRD weapons and armor items,
used by EquipmentService to compute to-hit, damage, and AC values.
"""
from __future__ import annotations
from dataclasses import dataclass
from typing import Optional


@dataclass
class WeaponData:
    """SRD weapon entry with damage and property flags."""
    name: str
    damage_dice: str        # e.g. "1d8" (base for Medium; scaled by monster size)
    damage_type: str        # e.g. "slashing"
    is_finesse: bool = False
    is_ranged: bool = False
    is_thrown: bool = False      # thrown weapons use STR (not DEX) unless finesse
    two_handed_dice: str = ""   # e.g. "1d10" for versatile weapons wielded 2H


@dataclass
class ArmorData:
    """SRD armor entry with AC and property flags."""
    name: str
    base_ac: int
    dex_limit: Optional[int]    # None = full DEX; 0 = no DEX; 2 = max +2
    stealth_disadvantage: bool = False
    str_requirement: int = 0    # 0 = no STR requirement


# ---------------------------------------------------------------------------
# Size-based weapon dice multiplier
# ---------------------------------------------------------------------------

SIZE_DICE_MULTIPLIER: dict[str, int] = {
    "Tiny": 1,
    "Small": 1,
    "Medium": 1,
    "Large": 2,
    "Huge": 3,
    "Gargantuan": 4,
}


# ---------------------------------------------------------------------------
# SRD Weapon data (~33 entries covering simple and martial weapons)
# ---------------------------------------------------------------------------

SRD_WEAPONS: list[WeaponData] = [
    # Simple melee weapons
    WeaponData("Club",          "1d4",  "bludgeoning"),
    WeaponData("Dagger",        "1d4",  "piercing",    is_finesse=True, is_thrown=True),
    WeaponData("Greatclub",     "1d8",  "bludgeoning"),
    WeaponData("Handaxe",       "1d6",  "slashing",    is_thrown=True),
    WeaponData("Javelin",       "1d6",  "piercing",    is_thrown=True),
    WeaponData("Light Hammer",  "1d4",  "bludgeoning", is_thrown=True),
    WeaponData("Mace",          "1d6",  "bludgeoning"),
    WeaponData("Quarterstaff",  "1d6",  "bludgeoning", two_handed_dice="1d8"),
    WeaponData("Sickle",        "1d4",  "slashing"),
    WeaponData("Spear",         "1d6",  "piercing",    is_thrown=True, two_handed_dice="1d8"),
    # Martial melee weapons
    WeaponData("Battleaxe",     "1d8",  "slashing",    two_handed_dice="1d10"),
    WeaponData("Flail",         "1d8",  "bludgeoning"),
    WeaponData("Glaive",        "1d10", "slashing"),
    WeaponData("Greataxe",      "1d12", "slashing"),
    WeaponData("Greatsword",    "2d6",  "slashing"),
    WeaponData("Halberd",       "1d10", "slashing"),
    WeaponData("Lance",         "1d12", "piercing"),
    WeaponData("Longsword",     "1d8",  "slashing",    two_handed_dice="1d10"),
    WeaponData("Maul",          "2d6",  "bludgeoning"),
    WeaponData("Morningstar",   "1d8",  "piercing"),
    WeaponData("Pike",          "1d10", "piercing"),
    WeaponData("Rapier",        "1d8",  "piercing",    is_finesse=True),
    WeaponData("Scimitar",      "1d6",  "slashing",    is_finesse=True),
    WeaponData("Shortsword",    "1d6",  "piercing",    is_finesse=True),
    WeaponData("Trident",       "1d6",  "piercing",    is_thrown=True, two_handed_dice="1d8"),
    WeaponData("War Pick",      "1d8",  "piercing"),
    WeaponData("Warhammer",     "1d8",  "bludgeoning", two_handed_dice="1d10"),
    WeaponData("Whip",          "1d4",  "slashing",    is_finesse=True),
    # Ranged weapons
    WeaponData("Shortbow",      "1d6",  "piercing",    is_ranged=True),
    WeaponData("Longbow",       "1d8",  "piercing",    is_ranged=True),
    WeaponData("Hand Crossbow", "1d6",  "piercing",    is_ranged=True),
    WeaponData("Heavy Crossbow","1d10", "piercing",    is_ranged=True),
    WeaponData("Light Crossbow","1d8",  "piercing",    is_ranged=True),
]


# ---------------------------------------------------------------------------
# SRD Armor data (12 entries: light, medium, heavy)
# ---------------------------------------------------------------------------

SRD_ARMORS: list[ArmorData] = [
    # Light armor (base_ac + full DEX modifier)
    ArmorData("Padded",          11, None, stealth_disadvantage=True),
    ArmorData("Leather",         11, None),
    ArmorData("Studded Leather", 12, None),
    # Medium armor (base_ac + min(DEX modifier, 2))
    ArmorData("Hide",            12, 2),
    ArmorData("Chain Shirt",     13, 2),
    ArmorData("Scale Mail",      14, 2, stealth_disadvantage=True),
    ArmorData("Breastplate",     14, 2),
    ArmorData("Half Plate",      15, 2, stealth_disadvantage=True),
    # Heavy armor (fixed AC, no DEX modifier)
    ArmorData("Ring Mail",       14, 0, stealth_disadvantage=True),
    ArmorData("Chain Mail",      16, 0, stealth_disadvantage=True, str_requirement=13),
    ArmorData("Splint",          17, 0, stealth_disadvantage=True, str_requirement=15),
    ArmorData("Plate",           18, 0, stealth_disadvantage=True, str_requirement=15),
]
