"""Combat domain models — pure Python dataclasses, no Qt dependencies.

These models are the authoritative data structures for CombatTrackerService.
The UI layer is display-only and never holds HP state directly.
"""
from __future__ import annotations

import dataclasses
from dataclasses import dataclass, field
from typing import Optional


# ---------------------------------------------------------------------------
# ConditionEntry
# ---------------------------------------------------------------------------

@dataclass
class ConditionEntry:
    """A single condition/buff on a combatant.

    - duration=None means indefinite (no round count).
    - duration=0 and expired=True means the condition has run out but is still
      shown on the card (grayed out) until the DM dismisses it.
    - color is a hex string set by the UI layer for chip coloring; the service
      preserves it during serialization but never sets it.
    """
    name: str
    duration: Optional[int] = None   # None = indefinite; int >= 0 = rounds remaining
    expired: bool = False
    color: str = ""                  # hex color for UI chip (e.g. "#e53935")


# ---------------------------------------------------------------------------
# CombatantState
# ---------------------------------------------------------------------------

@dataclass
class CombatantState:
    """State for one participant in combat.

    IDs are unique within a combat session (e.g. "Goblin_1", "Goblin_2").
    monster_name is None for PCs; it holds the base Monster library name for
    monsters so the UI can resolve full stat blocks later.
    """
    id: str
    name: str
    monster_name: Optional[str]       # None for PCs
    max_hp: int
    current_hp: int
    temp_hp: int = 0
    initiative: int = 0
    ac: int = 0
    conditions: list[ConditionEntry] = field(default_factory=list)
    is_pc: bool = False
    group_id: str = ""                # shared by same monster type (e.g. "Goblin")
    dex_score: int = 10               # DEX score for initiative tiebreaking
    speed: str = ""                   # e.g. "30 ft." for toggleable display
    passive_perception: int = 0       # for toggleable display
    legendary_resistances: int = 0    # uses remaining
    legendary_resistances_max: int = 0
    legendary_actions: int = 0        # uses remaining
    legendary_actions_max: int = 0
    regeneration_hp: int = 0          # HP per round; 0 = no regen

    @property
    def is_defeated(self) -> bool:
        """True when current HP is at or below zero."""
        return self.current_hp <= 0

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "name": self.name,
            "monster_name": self.monster_name,
            "max_hp": self.max_hp,
            "current_hp": self.current_hp,
            "temp_hp": self.temp_hp,
            "initiative": self.initiative,
            "ac": self.ac,
            "is_pc": self.is_pc,
            "group_id": self.group_id,
            "dex_score": self.dex_score,
            "speed": self.speed,
            "passive_perception": self.passive_perception,
            "legendary_resistances": self.legendary_resistances,
            "legendary_resistances_max": self.legendary_resistances_max,
            "legendary_actions": self.legendary_actions,
            "legendary_actions_max": self.legendary_actions_max,
            "regeneration_hp": self.regeneration_hp,
            "conditions": [
                {
                    "name": c.name,
                    "duration": c.duration,
                    "expired": c.expired,
                    "color": c.color,
                }
                for c in self.conditions
            ],
        }

    @classmethod
    def from_dict(cls, d: dict) -> "CombatantState":
        """Reconstruct from a JSON dict; unknown keys are dropped for forward-compat."""
        d = dict(d)  # shallow copy — do not mutate caller's dict
        d["conditions"] = [
            ConditionEntry(**c) for c in d.get("conditions", [])
        ]
        known = {f.name for f in dataclasses.fields(cls)}
        d = {k: v for k, v in d.items() if k in known}
        return cls(**d)


# ---------------------------------------------------------------------------
# CombatState
# ---------------------------------------------------------------------------

@dataclass
class CombatState:
    """Full combat session state: all combatants, round counter, turn pointer, log."""
    combatants: list[CombatantState] = field(default_factory=list)
    round_number: int = 1
    current_turn_index: int = 0
    initiative_mode: bool = True      # True = sorted by initiative; False = pass-1-round
    grouping_enabled: bool = True
    log_entries: list[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "round_number": self.round_number,
            "current_turn_index": self.current_turn_index,
            "initiative_mode": self.initiative_mode,
            "grouping_enabled": self.grouping_enabled,
            "log_entries": list(self.log_entries),
            "combatants": [c.to_dict() for c in self.combatants],
        }

    @classmethod
    def from_dict(cls, d: dict) -> "CombatState":
        """Reconstruct from a JSON dict; unknown keys are dropped for forward-compat."""
        d = dict(d)
        d["combatants"] = [
            CombatantState.from_dict(c) for c in d.get("combatants", [])
        ]
        known = {f.name for f in dataclasses.fields(cls)}
        d = {k: v for k, v in d.items() if k in known}
        return cls(**d)


# ---------------------------------------------------------------------------
# PlayerCharacter
# ---------------------------------------------------------------------------

@dataclass
class PlayerCharacter:
    """A player character persisted globally across encounters."""
    name: str
    ac: int = 10
    max_hp: int = 1
    current_hp: int = 1
    conditions: list[ConditionEntry] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "name": self.name,
            "ac": self.ac,
            "max_hp": self.max_hp,
            "current_hp": self.current_hp,
            "conditions": [
                {
                    "name": c.name,
                    "duration": c.duration,
                    "expired": c.expired,
                    "color": c.color,
                }
                for c in self.conditions
            ],
        }

    @classmethod
    def from_dict(cls, d: dict) -> "PlayerCharacter":
        d = dict(d)
        d["conditions"] = [
            ConditionEntry(**c) for c in d.get("conditions", [])
        ]
        known = {f.name for f in dataclasses.fields(cls)}
        d = {k: v for k, v in d.items() if k in known}
        return cls(**d)


# ---------------------------------------------------------------------------
# Preset condition and buff constants
# ---------------------------------------------------------------------------

STANDARD_CONDITIONS: list[dict] = [
    {"name": "Blinded",       "default_duration": None},
    {"name": "Charmed",       "default_duration": None},
    {"name": "Deafened",      "default_duration": None},
    {"name": "Frightened",    "default_duration": None},
    {"name": "Grappled",      "default_duration": None},
    {"name": "Incapacitated", "default_duration": None},
    {"name": "Invisible",     "default_duration": None},
    {"name": "Paralyzed",     "default_duration": None},
    {"name": "Petrified",     "default_duration": None},
    {"name": "Poisoned",      "default_duration": None},
    {"name": "Prone",         "default_duration": None},
    {"name": "Restrained",    "default_duration": None},
    {"name": "Stunned",       "default_duration": None},
    {"name": "Unconscious",   "default_duration": None},
]

COMMON_BUFFS: list[dict] = [
    # 1st level
    {"name": "Bane",              "default_duration": 10, "level": 1},
    {"name": "Bless",             "default_duration": 10, "level": 1},
    {"name": "Entangle",          "default_duration": 10, "level": 1},
    {"name": "Faerie Fire",       "default_duration": 10, "level": 1},
    {"name": "Hex",               "default_duration": None, "level": 1},
    {"name": "Hunter's Mark",     "default_duration": None, "level": 1},
    {"name": "Shield",            "default_duration": 1,  "level": 1},
    # 2nd level
    {"name": "Hold Person",       "default_duration": 10, "level": 2},
    {"name": "Web",               "default_duration": 10, "level": 2},
    # 3rd level
    {"name": "Fear",              "default_duration": 10, "level": 3},
    {"name": "Haste",             "default_duration": 10, "level": 3},
    {"name": "Hypnotic Pattern",  "default_duration": 10, "level": 3},
    {"name": "Slow",              "default_duration": 10, "level": 3},
    {"name": "Spirit Guardians",  "default_duration": 10, "level": 3},
    # 8th level
    {"name": "Maze",              "default_duration": None, "level": 8},
]
