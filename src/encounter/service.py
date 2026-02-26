"""
EncounterService and SaveRollService — pure Python, no Qt, no I/O beyond pathlib.

EncounterService
  - save_encounter: writes a hand-editable Markdown file
  - load_encounter: restores a saved encounter; unresolved monster names are
    returned as UnresolvedEntry list, never silently dropped

SaveRollService
  - execute_save_roll: rolls d20 per participant with optional advantage/
    disadvantage, adds save_bonus, flat_modifier, bonus_dice, compares to DC

Module-level helpers:
  _resolve_save_bonus(monster, ability_upper) -> int
  _expand_participants(encounter, ability) -> list[SaveParticipant]
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

from src.domain.models import Encounter, Monster
from src.engine.parser import roll_expression
from src.engine.roller import Roller
from src.encounter.models import (
    SaveParticipant,
    SaveParticipantResult,
    SaveRequest,
    SaveRollResult,
    SaveSummary,
    UnresolvedEntry,
)
from src.library.service import MonsterLibrary


# ---------------------------------------------------------------------------
# Regex patterns for Markdown encounter format
# ---------------------------------------------------------------------------

_HEADER_RE = re.compile(r"^#\s*Encounter:\s*(.+)$")
_ENTRY_RE = re.compile(r"^\s*-\s*(\d+)x\s+(.+)$")


# ---------------------------------------------------------------------------
# Module-level helpers
# ---------------------------------------------------------------------------


def _resolve_save_bonus(monster: Monster, ability_upper: str) -> int:
    """Resolve the saving throw bonus for *ability_upper* from *monster*.

    Priority:
    1. If ability_upper in monster.saves → return explicit proficiency bonus.
    2. Else: score = monster.ability_scores.get(ability_upper, 10);
             return (score - 10) // 2   (5e floor-division, correct for negatives)

    Note: (score - 10) // 2 is correct per D&D 5e (e.g. STR 8 → -1).
    This is intentionally NOT int(score / 2) which would give wrong results
    for negatives — see project decisions (01-01 notes about int(a/b) apply
    to damage division only, not ability modifiers).
    """
    if ability_upper in monster.saves:
        return monster.saves[ability_upper]
    score = monster.ability_scores.get(ability_upper, 10)
    return (score - 10) // 2


def _expand_participants(encounter: Encounter, ability: str) -> list[SaveParticipant]:
    """Expand encounter members into a flat list of SaveParticipant objects.

    Rules:
    - count == 1 → name = monster.name  (no numeric suffix)
    - count > 1  → name = f"{monster.name} {i}" for i in range(1, count+1)
    - save_bonus is resolved via _resolve_save_bonus for the given ability.
    """
    ability_upper = ability.upper()
    participants: list[SaveParticipant] = []
    for monster, count in encounter.members:
        bonus = _resolve_save_bonus(monster, ability_upper)
        if count == 1:
            participants.append(SaveParticipant(name=monster.name, save_bonus=bonus))
        else:
            for i in range(1, count + 1):
                participants.append(
                    SaveParticipant(name=f"{monster.name} {i}", save_bonus=bonus)
                )
    return participants


# ---------------------------------------------------------------------------
# EncounterService
# ---------------------------------------------------------------------------


class EncounterService:
    """Pure I/O service for saving and loading encounter Markdown files.

    File format (UTF-8):
        # Encounter: {name}

        - {count}x {monster.name}
        - {count}x {monster.name}
        ...
    """

    def save_encounter(self, encounter: Encounter, path: Path) -> None:
        """Write *encounter* to *path* as a hand-editable Markdown file.

        Parameters
        ----------
        encounter : Encounter
            The encounter to serialise.
        path : Path
            Destination file path. Parent directories must already exist.
        """
        lines = [f"# Encounter: {encounter.name}", ""]
        for monster, count in encounter.members:
            lines.append(f"- {count}x {monster.name}")
        content = "\n".join(lines) + "\n"
        path.write_text(content, encoding="utf-8")

    def load_encounter(
        self,
        path: Path,
        library: MonsterLibrary,
    ) -> tuple[Encounter, list[UnresolvedEntry]]:
        """Parse *path* and restore an Encounter.

        Parameters
        ----------
        path    : Path
            Path to the encounter Markdown file.
        library : MonsterLibrary
            Used to resolve monster names to Monster instances.

        Returns
        -------
        (Encounter, list[UnresolvedEntry])
            - Encounter with resolved members (monster, count) pairs.
            - Unresolved entries whose names were not found in the library.
            Lines that do not match the expected format are silently skipped.
        """
        text = path.read_text(encoding="utf-8")
        encounter_name = "Unknown"
        members: list[tuple[Monster, int]] = []
        unresolved: list[UnresolvedEntry] = []

        for line in text.splitlines():
            header_match = _HEADER_RE.match(line)
            if header_match:
                encounter_name = header_match.group(1).strip()
                continue

            entry_match = _ENTRY_RE.match(line)
            if entry_match:
                count = int(entry_match.group(1))
                name = entry_match.group(2).strip()
                if library.has_name(name):
                    members.append((library.get_by_name(name), count))
                else:
                    unresolved.append(UnresolvedEntry(name=name, count=count))
                continue
            # Any other line (blank, lore text, etc.) is silently skipped.

        return Encounter(name=encounter_name, members=members), unresolved


# ---------------------------------------------------------------------------
# SaveRollService
# ---------------------------------------------------------------------------


class SaveRollService:
    """Rolls saving throws for all participants in a SaveRequest.

    Mirrors RollService's architecture:
    - Accepts an external Roller (caller controls seeding)
    - Uses roll_expression() from the dice engine
    - No Qt imports; pure Python
    """

    def execute_save_roll(
        self, request: SaveRequest, roller: Roller
    ) -> SaveRollResult:
        """Execute saving throws for every participant in *request*.

        Parameters
        ----------
        request : SaveRequest
            Fully specified save roll request (participants, ability, DC,
            advantage mode, flat_modifier, bonus_dice, optional seed).
        roller : Roller
            Shared roller instance (pre-seeded by the caller if determinism needed).

        Returns
        -------
        SaveRollResult
            Per-participant results plus aggregate SaveSummary.
        """
        participant_results: list[SaveParticipantResult] = []
        for participant in request.participants:
            pr = self._roll_one_participant(request, participant, roller)
            participant_results.append(pr)

        summary = self._build_summary(participant_results)
        return SaveRollResult(
            request=request,
            participant_results=participant_results,
            summary=summary,
        )

    # ------------------------------------------------------------------
    # Internal: single participant
    # ------------------------------------------------------------------

    def _roll_one_participant(
        self,
        request: SaveRequest,
        participant: SaveParticipant,
        roller: Roller,
    ) -> SaveParticipantResult:
        # 1. Roll d20 based on advantage mode
        # Per-participant advantage overrides request-level advantage when set
        effective_advantage = participant.advantage if participant.advantage is not None else request.advantage
        if effective_advantage == "advantage":
            d20_result = roll_expression("2d20kh1", roller, request.seed)
        elif effective_advantage == "disadvantage":
            d20_result = roll_expression("2d20kl1", roller, request.seed)
        else:
            d20_result = roll_expression("1d20", roller, request.seed)

        # 2. Find the kept die's natural value
        kept_face = next(f for f in d20_result.faces if f.kept)
        natural = kept_face.value

        # 3. Roll bonus dice (mirrors RollService._roll_bonus_dice pattern)
        bonus_dice_results: list = []
        bonus_total = 0
        for entry in request.bonus_dice:
            formula_clean = entry.formula.lstrip("+")
            b_result = roll_expression(formula_clean, roller, request.seed)
            sign = -1 if entry.formula.startswith("-") else 1
            signed_total = sign * b_result.total
            bonus_total += signed_total
            bonus_dice_results.append((entry.formula, signed_total, entry.label))

        # 4. Compute total
        total = natural + participant.save_bonus + request.flat_modifier + bonus_total

        # 5. Determine pass/fail
        passed = total >= request.dc

        return SaveParticipantResult(
            name=participant.name,
            d20_faces=d20_result.faces,
            d20_natural=natural,
            save_bonus=participant.save_bonus,
            flat_modifier=request.flat_modifier,
            bonus_dice_results=bonus_dice_results,
            total=total,
            passed=passed,
            dc=request.dc,
            detected_features=participant.detected_features,
            lr_uses=participant.lr_uses,
            lr_max=participant.lr_max,
        )

    # ------------------------------------------------------------------
    # Internal: summary
    # ------------------------------------------------------------------

    def _build_summary(
        self, participant_results: list[SaveParticipantResult]
    ) -> SaveSummary:
        passed_count = sum(1 for pr in participant_results if pr.passed)
        failed_count = sum(1 for pr in participant_results if not pr.passed)
        failed_names = [pr.name for pr in participant_results if not pr.passed]
        return SaveSummary(
            total_participants=len(participant_results),
            passed=passed_count,
            failed=failed_count,
            failed_names=failed_names,
        )


# ---------------------------------------------------------------------------
# FeatureRule and FeatureDetectionService
# ---------------------------------------------------------------------------


@dataclass
class FeatureRule:
    """A single detection rule for save feature detection."""
    trigger: str          # substring to match against action raw_text (case-insensitive)
    label: str            # display label, e.g. "MR (auto)", "Evasion"
    behavior: str         # "auto-advantage", "auto-disadvantage", "auto-fail", "auto-pass", "reminder"
    enabled: bool = True
    is_builtin: bool = False  # True = cannot be deleted, only disabled

    def to_dict(self) -> dict:
        return {
            "trigger": self.trigger,
            "label": self.label,
            "behavior": self.behavior,
            "enabled": self.enabled,
        }

    @classmethod
    def from_dict(cls, d: dict) -> "FeatureRule":
        return cls(
            trigger=d.get("trigger", ""),
            label=d.get("label", ""),
            behavior=d.get("behavior", "reminder"),
            enabled=d.get("enabled", True),
            is_builtin=False,
        )


BUILTIN_RULES: list[FeatureRule] = [
    FeatureRule(trigger="magic resistance", label="MR (auto)", behavior="auto-advantage", is_builtin=True),
    FeatureRule(trigger="legendary resistance", label="LR", behavior="reminder", is_builtin=True),
]

_LR_COUNT_RE = re.compile(r"legendary resistance\s*\(?(\d+)/day\)?", re.IGNORECASE)


class FeatureDetectionService:
    """Scans Monster.actions[*].raw_text and applies FeatureRules.

    Produces per-participant advantage and feature label lists.
    Stateless — all state management happens in UI layer.
    """

    def detect_for_participant(
        self,
        monster,
        rules: list[FeatureRule],
        is_magical_save: bool,
    ) -> tuple:
        """Return (advantage_override, detected_labels, lr_uses, lr_max).

        advantage_override: Optional[str] — None if no rule overrides.
        detected_labels: list[str] — feature labels for display.
        lr_uses: int — max LR uses detected (0 if none).
        lr_max: int — same as lr_uses at detection time (UI decrements lr_uses).
        """
        if monster is None:
            return None, [], 0, 0

        actions = getattr(monster, "actions", [])
        all_raw = " ".join(getattr(a, "raw_text", "") or "" for a in actions)

        advantage_override = None
        labels: list[str] = []
        lr_uses = 0
        lr_max = 0

        for rule in rules:
            if not rule.enabled:
                continue
            if rule.trigger.lower() not in all_raw.lower():
                continue

            # Magic Resistance: only triggers when is_magical_save is True
            if rule.trigger.lower() == "magic resistance" and not is_magical_save:
                continue

            if rule.behavior == "auto-advantage":
                advantage_override = "advantage"
                labels.append(rule.label)
            elif rule.behavior == "auto-disadvantage":
                advantage_override = "disadvantage"
                labels.append(rule.label)
            elif rule.behavior == "auto-fail":
                labels.append(f"{rule.label} (auto-fail)")
            elif rule.behavior == "auto-pass":
                labels.append(f"{rule.label} (auto-pass)")
            elif rule.behavior == "reminder":
                if rule.trigger.lower() == "legendary resistance":
                    lr_m = _LR_COUNT_RE.search(all_raw)
                    if lr_m:
                        lr_max = max(lr_max, int(lr_m.group(1)))
                        lr_uses = lr_max
                    labels.append(f"LR {lr_uses}/{lr_max}")
                else:
                    labels.append(f"{rule.label} (reminder)")

        return advantage_override, labels, lr_uses, lr_max
