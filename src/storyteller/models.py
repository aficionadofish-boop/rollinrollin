from __future__ import annotations
from dataclasses import dataclass, field


@dataclass
class DieResult:
    value: int
    is_success: bool
    is_one: bool
    is_reroll: bool = False  # True if added by 8-again/9-again/rote chain


@dataclass
class MegaDieResult:
    value: int
    sux_count: int           # 0, 2, or 3 (Aberrant mega rules)
    is_one: bool


@dataclass
class WodRollResult:
    dice: list[DieResult]    # all dice including all re-rolls, in order
    net_successes: int       # raw_successes - ones_count (can be negative)
    raw_successes: int       # count of dice with is_success=True
    ones_count: int          # count of non-success dice showing 1
    is_botch: bool           # net_successes < 0
    is_exceptional: bool     # net_successes >= 5
    reroll_threshold: int | None  # 8, 9, or None
    rote_enabled: bool
    pool: int
    difficulty: int


@dataclass
class AberrantRollResult:
    normal_dice: list[DieResult]
    mega_dice: list[MegaDieResult]
    auto_successes: int
    total_successes: int
    is_botch: bool           # total_successes==0 AND any die shows 1
    success_tier: str        # "none", "1-4", "5-8", "9-12", "13-16"
    pool: int
    mega_pool: int
    successes_required: int


@dataclass
class StorytellerPreset:
    name: str
    system: str              # "wod" or "aberrant"
    # WoD fields
    pool: int = 5
    difficulty: int = 6
    reroll_threshold: int | None = None
    rote_enabled: bool = False
    # Aberrant fields
    mega_pool: int = 0
    auto_successes: int = 0
    successes_required: int = 1

    def to_dict(self) -> dict:
        return {
            "name": self.name,
            "system": self.system,
            "pool": self.pool,
            "difficulty": self.difficulty,
            "reroll_threshold": self.reroll_threshold,
            "rote_enabled": self.rote_enabled,
            "mega_pool": self.mega_pool,
            "auto_successes": self.auto_successes,
            "successes_required": self.successes_required,
        }

    @classmethod
    def from_dict(cls, d: dict) -> "StorytellerPreset":
        return cls(
            name=d.get("name", ""),
            system=d.get("system", "wod"),
            pool=d.get("pool", 5),
            difficulty=d.get("difficulty", 6),
            reroll_threshold=d.get("reroll_threshold", None),
            rote_enabled=d.get("rote_enabled", False),
            mega_pool=d.get("mega_pool", 0),
            auto_successes=d.get("auto_successes", 0),
            successes_required=d.get("successes_required", 1),
        )
