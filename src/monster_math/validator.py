"""
MathValidator — validate saving throw bonuses, action to-hit/damage, and spellcasting.

Pure Python, no Qt. Uses DerivedStats from engine and SpellcastingInfo from spellcasting.
"""
from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Optional

from src.domain.models import Action, Monster
from src.monster_math.engine import DerivedStats
from src.monster_math.spellcasting import SpellcastingInfo


# ---------------------------------------------------------------------------
# SaveState — str enum for JSON serialization compatibility
# ---------------------------------------------------------------------------


class SaveState(str, Enum):
    NON_PROFICIENT = "non_proficient"
    PROFICIENT = "proficient"
    EXPERTISE = "expertise"
    CUSTOM = "custom"


# ---------------------------------------------------------------------------
# Validation result dataclasses
# ---------------------------------------------------------------------------


@dataclass
class SaveValidation:
    """Validation result for a single saving throw bonus.

    Attributes
    ----------
    ability : str
        Uppercase ability abbreviation (e.g. "STR").
    actual : int
        The bonus listed on the monster statblock.
    expected_non_proficient : int
        Ability modifier only.
    expected_proficient : int
        Ability modifier + proficiency bonus.
    expected_expertise : int
        Ability modifier + 2 * proficiency bonus.
    state : SaveState
        Classification based on which expected value matches actual.
    """
    ability: str
    actual: int
    expected_non_proficient: int
    expected_proficient: int
    expected_expertise: int
    state: SaveState

    @property
    def is_flagged(self) -> bool:
        """True when the save has a non-standard (CUSTOM) bonus."""
        return self.state == SaveState.CUSTOM

    @property
    def tooltip(self) -> str:
        """Human-readable explanation of the expected vs actual breakdown."""
        if self.state == SaveState.NON_PROFICIENT:
            return f"{self.ability}: +{self.actual} (non-proficient, mod only)"
        if self.state == SaveState.PROFICIENT:
            return f"{self.ability}: +{self.actual} (proficient: mod + prof)"
        if self.state == SaveState.EXPERTISE:
            return f"{self.ability}: +{self.actual} (expertise: mod + 2×prof)"
        # CUSTOM
        return (
            f"{self.ability}: Expected +{self.expected_proficient} (prof) or "
            f"+{self.expected_expertise} (expertise), got +{self.actual} — "
            f"custom {self.actual - self.expected_proficient:+d} from proficient"
        )


@dataclass
class ActionValidation:
    """Validation result for a single action's to-hit and damage bonus.

    To-hit expected = ability_mod + proficiency_bonus.
    Damage expected = ability_mod only (no proficiency on damage).

    Attributes
    ----------
    action_name : str
        Name of the action.
    actual_to_hit : int or None
        Actual to-hit bonus from statblock. None if not an attack action.
    expected_to_hit : int or None
        Expected to-hit = ability_mod + prof. None if actual_to_hit is None.
    to_hit_delta : int
        actual_to_hit - expected_to_hit. 0 if no to-hit.
    actual_damage_bonus : int or None
        Actual damage bonus from statblock. None if action has no damage bonus.
    expected_damage_bonus : int or None
        Expected damage bonus = ability_mod only. None if actual_damage_bonus is None.
    damage_delta : int
        actual_damage_bonus - expected_damage_bonus. 0 if no damage bonus.
    """
    action_name: str
    actual_to_hit: Optional[int]
    expected_to_hit: Optional[int]
    to_hit_delta: int
    actual_damage_bonus: Optional[int]
    expected_damage_bonus: Optional[int]
    damage_delta: int

    @property
    def to_hit_is_flagged(self) -> bool:
        """True when to-hit bonus does not match expected."""
        if self.actual_to_hit is None or self.expected_to_hit is None:
            return False
        return self.to_hit_delta != 0

    @property
    def damage_is_flagged(self) -> bool:
        """True when damage bonus does not match expected."""
        if self.actual_damage_bonus is None or self.expected_damage_bonus is None:
            return False
        return self.damage_delta != 0

    @property
    def is_flagged(self) -> bool:
        """True when either to-hit or damage is flagged."""
        return self.to_hit_is_flagged or self.damage_is_flagged


@dataclass
class SpellValidation:
    """Validation result for a spellcasting trait's attack bonus and save DC.

    Expected attack = casting_mod + proficiency_bonus + focus_bonus.
    Expected DC = 8 + casting_mod + proficiency_bonus + focus_bonus.

    Attributes
    ----------
    trait_name : str
        Name of the spellcasting action.
    actual_attack_bonus : int or None
        Actual spell attack bonus. None if not provided.
    expected_attack_bonus : int or None
        Expected spell attack bonus. None if actual_attack_bonus is None.
    actual_dc : int or None
        Actual spell save DC. None if not provided.
    expected_dc : int or None
        Expected spell save DC. None if actual_dc is None.
    delta_attack : int
        actual_attack_bonus - expected_attack_bonus. 0 if not applicable.
    delta_dc : int
        actual_dc - expected_dc. 0 if not applicable.
    """
    trait_name: str
    actual_attack_bonus: Optional[int]
    expected_attack_bonus: Optional[int]
    actual_dc: Optional[int]
    expected_dc: Optional[int]
    delta_attack: int
    delta_dc: int

    @property
    def is_flagged(self) -> bool:
        """True when either attack bonus or DC does not match expected."""
        attack_flagged = (
            self.actual_attack_bonus is not None
            and self.expected_attack_bonus is not None
            and self.delta_attack != 0
        )
        dc_flagged = (
            self.actual_dc is not None
            and self.expected_dc is not None
            and self.delta_dc != 0
        )
        return attack_flagged or dc_flagged


# ---------------------------------------------------------------------------
# MathValidator
# ---------------------------------------------------------------------------


class MathValidator:
    """Validates monster statblock bonuses against derived mathematical expectations.

    All methods are pure functions — they accept Monster and DerivedStats as
    input and return validation result objects. No state is stored.
    """

    # ------------------------------------------------------------------
    # Save validation
    # ------------------------------------------------------------------

    def validate_saves(
        self, monster: Monster, derived: DerivedStats
    ) -> list[SaveValidation]:
        """Validate each saving throw bonus in monster.saves.

        Parameters
        ----------
        monster : Monster
            Source monster. Only `saves` and `ability_scores` are read.
        derived : DerivedStats
            Pre-computed derived stats from MonsterMathEngine.

        Returns
        -------
        list[SaveValidation]
            One entry per ability in monster.saves.
        """
        results: list[SaveValidation] = []
        for ability, actual in monster.saves.items():
            ability_upper = ability.upper()

            non_prof = derived.expected_saves.get(ability_upper, 0)
            prof = derived.expected_proficient_saves.get(ability_upper, 0)
            expertise = derived.expected_expertise_saves.get(ability_upper, 0)

            state = self._classify_save(actual, non_prof, prof, expertise)
            results.append(
                SaveValidation(
                    ability=ability_upper,
                    actual=actual,
                    expected_non_proficient=non_prof,
                    expected_proficient=prof,
                    expected_expertise=expertise,
                    state=state,
                )
            )
        return results

    @staticmethod
    def _classify_save(
        actual: int,
        non_prof: int,
        prof: int,
        expertise: int,
    ) -> SaveState:
        if actual == expertise:
            return SaveState.EXPERTISE
        if actual == prof:
            return SaveState.PROFICIENT
        if actual == non_prof:
            return SaveState.NON_PROFICIENT
        return SaveState.CUSTOM

    # ------------------------------------------------------------------
    # Action validation
    # ------------------------------------------------------------------

    def validate_action(
        self, action: Action, monster: Monster, derived: DerivedStats
    ) -> ActionValidation:
        """Validate an action's to-hit and damage bonus.

        Ability selection heuristic:
        1. "Ranged" in action.raw_text → use DEX
        2. "finesse" in action.raw_text AND DEX mod > STR mod → use DEX
        3. Otherwise → use STR

        Expected to-hit = ability_mod + proficiency_bonus.
        Expected damage = ability_mod only (proficiency does NOT apply to damage).

        Parameters
        ----------
        action : Action
            The action to validate.
        monster : Monster
            Source monster for ability scores.
        derived : DerivedStats
            Pre-computed derived stats.

        Returns
        -------
        ActionValidation
        """
        raw = action.raw_text or ""
        ability = self._pick_ability(raw, derived)
        ability_mod = derived.ability_modifiers.get(ability, 0)
        prof = derived.proficiency_bonus

        # To-hit validation
        actual_to_hit = action.to_hit_bonus
        if actual_to_hit is not None:
            expected_to_hit = ability_mod + prof
            to_hit_delta = actual_to_hit - expected_to_hit
        else:
            expected_to_hit = None
            to_hit_delta = 0

        # Damage bonus validation — access via getattr for forward-compat
        actual_damage_bonus: Optional[int] = getattr(action, "damage_bonus", None)
        if actual_damage_bonus is not None:
            expected_damage_bonus = ability_mod  # damage: mod only
            damage_delta = actual_damage_bonus - expected_damage_bonus
        else:
            expected_damage_bonus = None
            damage_delta = 0

        return ActionValidation(
            action_name=action.name,
            actual_to_hit=actual_to_hit,
            expected_to_hit=expected_to_hit,
            to_hit_delta=to_hit_delta,
            actual_damage_bonus=actual_damage_bonus,
            expected_damage_bonus=expected_damage_bonus,
            damage_delta=damage_delta,
        )

    @staticmethod
    def _pick_ability(raw_text: str, derived: DerivedStats) -> str:
        """Determine which ability modifier to use for to-hit/damage check."""
        raw_lower = raw_text.lower()
        if "ranged" in raw_lower:
            return "DEX"
        if "finesse" in raw_lower:
            dex_mod = derived.ability_modifiers.get("DEX", 0)
            str_mod = derived.ability_modifiers.get("STR", 0)
            if dex_mod > str_mod:
                return "DEX"
        return "STR"

    # ------------------------------------------------------------------
    # Spell validation
    # ------------------------------------------------------------------

    def validate_spellcasting(
        self,
        spellcasting_info: SpellcastingInfo,
        monster: Monster,
        derived: DerivedStats,
        actual_attack_bonus: Optional[int] = None,
        actual_dc: Optional[int] = None,
    ) -> SpellValidation:
        """Validate a spellcasting trait's attack bonus and save DC.

        Expected attack = casting_mod + proficiency_bonus + focus_bonus.
        Expected DC = 8 + casting_mod + proficiency_bonus + focus_bonus.

        Parameters
        ----------
        spellcasting_info : SpellcastingInfo
            Detected spellcasting info (trait name, casting ability, focus bonus).
        monster : Monster
            Source monster (not currently used beyond validation context).
        derived : DerivedStats
            Pre-computed derived stats for the monster.
        actual_attack_bonus : int or None
            Actual spell attack bonus from statblock. Skipped if None.
        actual_dc : int or None
            Actual spell save DC from statblock. Skipped if None.

        Returns
        -------
        SpellValidation
        """
        casting_ability = spellcasting_info.casting_ability
        casting_mod = derived.ability_modifiers.get(casting_ability, 0)
        prof = derived.proficiency_bonus
        focus = spellcasting_info.focus_bonus

        # Attack bonus
        if actual_attack_bonus is not None:
            expected_attack = casting_mod + prof + focus
            delta_attack = actual_attack_bonus - expected_attack
        else:
            expected_attack = None
            delta_attack = 0

        # Save DC
        if actual_dc is not None:
            expected_dc = 8 + casting_mod + prof + focus
            delta_dc = actual_dc - expected_dc
        else:
            expected_dc = None
            delta_dc = 0

        return SpellValidation(
            trait_name=spellcasting_info.trait_name,
            actual_attack_bonus=actual_attack_bonus,
            expected_attack_bonus=expected_attack,
            actual_dc=actual_dc,
            expected_dc=expected_dc,
            delta_attack=delta_attack,
            delta_dc=delta_dc,
        )
