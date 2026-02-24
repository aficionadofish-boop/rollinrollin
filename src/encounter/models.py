"""
Encounter models: data-transfer objects for EncounterService and SaveRollService.

All dataclasses use only stdlib (dataclasses, typing) — no Qt, no I/O.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional, Literal


@dataclass
class UnresolvedEntry:
    """A monster name from a loaded encounter file that could not be matched in the library."""
    name: str
    count: int


@dataclass
class SaveParticipant:
    """One participant in a save roll — name plus resolved save bonus."""
    name: str           # e.g. "Goblin 1", "Goblin 2", "Hobgoblin"
    save_bonus: int     # resolved from Monster.saves[ability] or (score-10)//2


@dataclass
class SaveRequest:
    """Everything SaveRollService needs to roll saves for all participants."""
    participants: list[SaveParticipant]
    ability: str                                           # "STR", "DEX", "CON", "INT", "WIS", "CHA"
    dc: int
    advantage: Literal["normal", "advantage", "disadvantage"] = "normal"
    flat_modifier: int = 0
    bonus_dice: list = field(default_factory=list)         # list[BonusDiceEntry] from roll.models
    seed: Optional[int] = None


@dataclass
class SaveParticipantResult:
    """Result for one participant's save roll."""
    name: str
    d20_faces: tuple       # DieFace(s) from engine — 1 or 2 faces depending on advantage
    d20_natural: int       # natural value of kept die
    save_bonus: int
    flat_modifier: int
    bonus_dice_results: list   # list[(formula, signed_total, label)]
    total: int             # d20_natural + save_bonus + flat_modifier + bonus_dice totals
    passed: bool           # total >= dc
    dc: int


@dataclass
class SaveSummary:
    """Aggregate across all participants in one save roll."""
    total_participants: int
    passed: int
    failed: int
    failed_names: list[str]   # names of participants who failed


@dataclass
class SaveRollResult:
    """Full output from SaveRollService.execute_save_roll()."""
    request: SaveRequest
    participant_results: list[SaveParticipantResult]
    summary: SaveSummary
