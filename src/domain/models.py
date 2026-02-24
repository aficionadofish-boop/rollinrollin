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


@dataclass
class DamagePart:
    dice_expr: str              # e.g. "2d6+3"
    damage_type: str            # use DamageType.value or raw string from parser
    raw_text: str               # original text from statblock, always present
    condition: Optional[str] = None   # e.g. "on crit", "if target is prone"


@dataclass
class Action:
    name: str
    to_hit_bonus: Optional[int]                   # None = not an attack roll, or parse failed
    damage_parts: list[DamagePart] = field(default_factory=list)
    raw_text: str = ""                            # always set; display fallback for unparsed actions
    is_parsed: bool = True                        # False = raw_text only, no roll button


@dataclass
class Monster:
    name: str
    ac: int
    hp: int
    cr: str                                        # CR as string: "1/2", "1", "17"
    actions: list[Action] = field(default_factory=list)
    saves: dict[str, int] = field(default_factory=dict)  # e.g. {"STR": 3, "DEX": 5}
    creature_type: str = ""                        # e.g. "Monstrosity", "Undead"
    ability_scores: dict[str, int] = field(default_factory=dict)  # {"STR": 10, ...}
    lore: str = ""                                 # lore paragraphs following statblock
    raw_text: str = ""                             # full source text for debugging
    incomplete: bool = False                       # True if any required field was missing at import
    tags: list[str] = field(default_factory=list) # user-assignable tags (LIB-05)


@dataclass
class MonsterList:
    name: str
    entries: list[tuple[Monster, int]] = field(default_factory=list)  # (monster, count)


@dataclass
class Encounter:
    name: str
    members: list[tuple[Monster, int]] = field(default_factory=list)  # (monster, count)
