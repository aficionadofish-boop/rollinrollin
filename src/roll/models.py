"""
Roll models: data-transfer objects for the RollService.

All dataclasses use only stdlib (dataclasses, typing) — no Qt, no I/O.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional, Literal


@dataclass
class BonusDiceEntry:
    """A single bonus dice formula entry (e.g. +1d4 Bless, -1d6)."""

    formula: str     # e.g. "+1d4" or "-1d6"
    label: str = ""  # e.g. "Bless"


@dataclass
class RollRequest:
    """Everything the RollService needs to execute N attack rolls."""

    action_name: str
    to_hit_bonus: int                                   # integer added to d20 total
    damage_parts: list                                  # list[DamagePart] from domain.models
    count: int                                          # N attacks to roll

    mode: Literal["raw", "compare"] = "raw"
    target_ac: Optional[int] = None
    advantage: Literal["normal", "advantage", "disadvantage"] = "normal"
    crit_enabled: bool = True
    crit_range: int = 20                               # 18, 19, or 20
    nat1_always_miss: bool = True
    nat20_always_hit: bool = True
    flat_modifier: int = 0
    bonus_dice: list[BonusDiceEntry] = field(default_factory=list)
    show_margin: bool = False                          # COMPARE "Show margin" toggle
    seed: Optional[int] = None
    crunchy_crits: bool = False  # maximize base dice, roll extra dice normally
    brutal_crits: bool = False   # maximize both base and extra dice


@dataclass
class DamagePartResult:
    """Result for one damage component of an attack."""

    total: int
    damage_type: str           # e.g. "slashing", "poison"
    dice_expr: str             # formula that was rolled (may be doubled on crit)
    faces: tuple               # DieFace tuple from DiceResult


@dataclass
class AttackRollResult:
    """Result for a single attack roll in a RollResult."""

    attack_number: int
    d20_faces: tuple           # DieFace(s) — 1 face for normal, 2 for adv/disadv
    d20_natural: int           # natural value of the kept die (before bonuses)
    attack_total: int          # d20 + to_hit_bonus + flat_modifier + bonus_dice totals
    to_hit_bonus: int
    flat_modifier: int
    bonus_dice_results: list   # list[(formula, signed_total, label)]
    is_hit: Optional[bool]     # None in RAW mode; True/False in COMPARE mode
    is_crit: bool
    is_nat1: bool
    is_nat20: bool
    damage_parts: list[DamagePartResult]  # empty if miss in COMPARE mode
    margin: Optional[int]      # attack_total - target_ac; None in RAW or if !show_margin
    crit_extra_parts: list = field(default_factory=list)  # extra crit dice (parallel to damage_parts)


@dataclass
class RollSummary:
    """Aggregate statistics across all attacks in a RollResult."""

    total_attacks: int
    hits: int
    misses: int
    crits: int
    total_damage: int          # sum of all damage totals across all hits


@dataclass
class RollResult:
    """Full output from RollService.execute_attack_roll()."""

    request: RollRequest
    attack_rolls: list[AttackRollResult]
    summary: RollSummary
