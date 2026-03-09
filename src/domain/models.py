from __future__ import annotations
from dataclasses import dataclass, field
from typing import Optional
from enum import Enum


# DamageType enum — use string values matching D&D 5e damage type names
class DamageType(str, Enum):
    ACID = "acid"
    BLUDGEONING = "bludgeoning"
    COLD = "cold"
    FIRE = "fire"
    FORCE = "force"
    LIGHTNING = "lightning"
    NECROTIC = "necrotic"
    PIERCING = "piercing"
    POISON = "poison"
    PSYCHIC = "psychic"
    RADIANT = "radiant"
    SLASHING = "slashing"
    THUNDER = "thunder"
    UNKNOWN = "unknown"   # fallback for unparsed types


# All 18 D&D 5e skills mapped to their governing ability score
SKILL_TO_ABILITY: dict[str, str] = {
    "Acrobatics": "DEX", "Animal Handling": "WIS", "Arcana": "INT",
    "Athletics": "STR", "Deception": "CHA", "History": "INT",
    "Insight": "WIS", "Intimidation": "CHA", "Investigation": "INT",
    "Medicine": "WIS", "Nature": "INT", "Perception": "WIS",
    "Performance": "CHA", "Persuasion": "CHA", "Religion": "INT",
    "Sleight of Hand": "DEX", "Stealth": "DEX", "Survival": "WIS",
}


@dataclass
class DamagePart:
    dice_expr: str              # e.g. "2d6+3"
    damage_type: str            # use DamageType.value or raw string from parser
    raw_text: str               # original text from statblock, always present
    condition: Optional[str] = None   # e.g. "on crit", "if target is prone"


@dataclass
class DetectedDie:
    """A dice formula detected in trait description text.

    Captures patterns like '54 (12d8) acid damage' found in trait descriptions.
    """
    full_match: str      # e.g. "54 (12d8) acid damage"
    dice_expr: str       # e.g. "12d8"
    damage_type: str     # e.g. "acid" or "unknown"
    average: int         # e.g. 54


@dataclass
class Trait:
    """A monster trait — a passive ability or special characteristic.

    Distinct from Action: traits have no to_hit_bonus and no damage_parts.
    Examples: Magic Resistance, Amphibious, Legendary Resistance (3/Day).
    """
    name: str
    description: str
    rollable_dice: list[DetectedDie] = field(default_factory=list)
    recharge_range: Optional[tuple[int, int]] = None  # e.g. (5, 6) for "Recharge 5-6"


@dataclass
class Action:
    name: str
    to_hit_bonus: Optional[int]                   # None = not an attack roll, or parse failed
    damage_parts: list[DamagePart] = field(default_factory=list)
    raw_text: str = ""                            # always set; display fallback for unparsed actions
    is_parsed: bool = True                        # False = raw_text only, no roll button
    damage_bonus: Optional[int] = None           # flat damage modifier (formalized from Phase 8 getattr fallback)
    is_equipment_generated: bool = False         # marks auto-generated weapon actions
    after_text: str = ""                         # text after the hit/damage line (e.g. saving throw effects)


@dataclass
class Monster:
    name: str
    ac: int
    hp: int
    cr: str                                        # CR as string: "1/2", "1", "17"
    actions: list[Action] = field(default_factory=list)
    legendary_actions: list[Action] = field(default_factory=list)  # actions from "Legendary Actions" section
    lair_actions: list[Action] = field(default_factory=list)        # actions from "Lair Actions" section
    saves: dict[str, int] = field(default_factory=dict)  # e.g. {"STR": 3, "DEX": 5}
    creature_type: str = ""                        # e.g. "Monstrosity", "Undead"
    ability_scores: dict[str, int] = field(default_factory=dict)  # {"STR": 10, ...}
    lore: str = ""                                 # lore paragraphs following statblock
    raw_text: str = ""                             # full source text for debugging
    incomplete: bool = False                       # True if any required field was missing at import
    tags: list[str] = field(default_factory=list) # user-assignable tags (LIB-05)
    size: str = "Medium"                           # "Tiny", "Small", "Medium", "Large", "Huge", "Gargantuan"
    skills: dict[str, int] = field(default_factory=dict)  # e.g. {"Perception": 5, "Stealth": 4}
    buffs: list["BuffItem"] = field(default_factory=list)  # active buffs carried from editor (EDIT-10)
    traits: list[Trait] = field(default_factory=list)      # passive traits separated from attack actions (Phase 15)
    speed: str = ""                                # e.g. "40 ft., fly 80 ft." parsed from **Speed** line
    proficiency_bonus: Optional[int] = None        # None = auto from CR; set = manual override


@dataclass
class MonsterList:
    name: str
    entries: list[tuple[Monster, int]] = field(default_factory=list)  # (monster, count)


@dataclass
class Encounter:
    name: str
    members: list[tuple[Monster, int]] = field(default_factory=list)  # (monster, count)


class SaveProficiencyState(str, Enum):
    """Save proficiency state for a given ability score."""
    NON_PROFICIENT = "non_proficient"
    PROFICIENT = "proficient"
    EXPERTISE = "expertise"
    CUSTOM = "custom"


@dataclass
class SpellcastingInfo:
    """Spellcasting details parsed or inferred from a monster's statblock."""
    trait_name: str           # "Spellcasting" or "Innate Spellcasting"
    casting_ability: str      # "INT", "WIS", "CHA", etc.
    is_assumed: bool          # True if casting ability was guessed (not found in text)
    focus_bonus: int = 0      # user-settable in Phase 9 editor


@dataclass
class EquipmentItem:
    """A single equipped item on a modified monster."""
    item_type: str          # "weapon", "armor", "shield", "focus"
    item_name: str          # e.g. "Longsword", "Plate Armor"
    magic_bonus: int = 0    # +0, +1, +2, +3


@dataclass
class BuffItem:
    """A custom named bonus for a modified monster."""
    name: str               # e.g. "Bless", "Rage"
    bonus_value: str        # e.g. "+1d4", "+2" (dice expr or flat)
    affects_attacks: bool = True           # applies to attack rolls
    affects_saves: bool = True             # applies to saving throws
    affects_ability_checks: bool = False   # applies to ability checks
    affects_damage: bool = False           # applies to damage rolls


# Migration mapping from old single-target string to new boolean fields.
# Used in MonsterModification.from_dict() to convert saved data from pre-16-01 format.
_BUFF_TARGET_MIGRATION: dict[str, dict[str, bool]] = {
    "attack_rolls":   {"affects_attacks": True,  "affects_saves": False, "affects_ability_checks": False, "affects_damage": False},
    "saving_throws":  {"affects_attacks": False, "affects_saves": True,  "affects_ability_checks": False, "affects_damage": False},
    "ability_checks": {"affects_attacks": False, "affects_saves": False, "affects_ability_checks": True,  "affects_damage": False},
    "damage":         {"affects_attacks": False, "affects_saves": False, "affects_ability_checks": False, "affects_damage": True},
    "all":            {"affects_attacks": True,  "affects_saves": True,  "affects_ability_checks": True,  "affects_damage": True},
}


@dataclass
class MonsterModification:
    """User overrides applied on top of a base monster from the library."""
    base_name: str                                                          # key into MonsterLibrary
    custom_name: Optional[str] = None                                       # if user renamed the modified copy
    ability_scores: dict[str, int] = field(default_factory=dict)            # override scores
    saves: dict[str, int] = field(default_factory=dict)                     # override saves
    skills: dict[str, int] = field(default_factory=dict)                    # override skills
    hp: Optional[int] = None
    hp_formula: Optional[str] = None                                        # e.g. "7d8+14"
    ac: Optional[int] = None
    cr: Optional[str] = None
    size: Optional[str] = None                                              # size override
    equipment: list[EquipmentItem] = field(default_factory=list)            # equipped items
    buffs: list[BuffItem] = field(default_factory=list)                     # custom bonuses
    actions: list[dict] = field(default_factory=list)                       # serialized action overrides
    traits: list[dict] = field(default_factory=list)                        # serialized trait overrides
    spellcasting_infos: list[SpellcastingInfo] = field(default_factory=list)
    proficiency_bonus: Optional[int] = None                                 # manual prof override

    @classmethod
    def from_dict(cls, d: dict) -> "MonsterModification":
        """Reconstruct MonsterModification from a JSON dict, handling both old and new formats."""
        d = dict(d)  # shallow copy to avoid mutating input
        d["equipment"] = [EquipmentItem(**e) for e in d.get("equipment", [])]

        # Buff deserialization with backward-compatible migration.
        # Old format: {"name": "Bless", "bonus_value": "+1d4", "targets": "attack_rolls"}
        # New format: {"name": "Bless", "bonus_value": "+1d4", "affects_attacks": True, ...}
        import dataclasses as _dc
        buff_fields = {f.name for f in _dc.fields(BuffItem)}
        migrated_buffs = []
        for b in d.get("buffs", []):
            b = dict(b)
            if "targets" in b and "affects_attacks" not in b:
                # Old format: migrate targets string to boolean fields
                targets_val = b.pop("targets")
                b.update(_BUFF_TARGET_MIGRATION.get(targets_val, _BUFF_TARGET_MIGRATION["all"]))
            else:
                # New format or mixed: just clean up legacy targets key if present
                b.pop("targets", None)
            # Filter to known BuffItem fields for forward-compat
            b = {k: v for k, v in b.items() if k in buff_fields}
            migrated_buffs.append(BuffItem(**b))
        d["buffs"] = migrated_buffs

        d["spellcasting_infos"] = [SpellcastingInfo(**s) for s in d.get("spellcasting_infos", [])]
        # Filter to only known fields to handle future additions or missing fields gracefully
        known = {f.name for f in _dc.fields(cls)}
        d = {k: v for k, v in d.items() if k in known}
        return cls(**d)
