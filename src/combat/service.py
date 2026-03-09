"""CombatTrackerService — authoritative state holder for all combat operations.

Design decisions (from STATE.md / CONTEXT.md):
- CombatTrackerService is authoritative; widgets are display-only, never hold HP state.
- Temp HP is absorbed before regular HP on damage.
- One-level undo: undo_advance restores the snapshot taken at the last advance_turn.
- Grouped initiative: combatants with the same group_id share a single roll when
  grouping_enabled=True.
- Feature detection: scan Monster.actions[*].raw_text for "Legendary Resistance",
  "Legendary Actions", "Regenerates"/"Regeneration" keywords.
"""
from __future__ import annotations

import copy
import re
from typing import Optional

from src.combat.models import CombatantState, CombatState, ConditionEntry, PlayerCharacter
from src.engine.roller import Roller


class CombatTrackerService:
    """Manages all combat state mutations.

    Usage pattern:
        svc = CombatTrackerService()
        svc.load_encounter([(monster, 3)], roller)
        svc.roll_all_initiative(roller)
        # Each turn:
        svc.advance_turn()
        # On damage:
        svc.apply_damage(combatant_id, -15)
    """

    def __init__(self) -> None:
        self._state = CombatState()
        self._prev_snapshot: Optional[dict] = None  # one-deep undo payload
        self._auto_regen: bool = False

    # ------------------------------------------------------------------
    # Read-only access
    # ------------------------------------------------------------------

    @property
    def state(self) -> CombatState:
        """Read-only access to the current CombatState."""
        return self._state

    def get_combatant(self, combatant_id: str) -> Optional[CombatantState]:
        """Return the CombatantState with the given id, or None if not found."""
        for c in self._state.combatants:
            if c.id == combatant_id:
                return c
        return None

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    def _find(self, combatant_id: str) -> CombatantState:
        """Internal lookup by id. Raises ValueError if not found."""
        c = self.get_combatant(combatant_id)
        if c is None:
            raise ValueError(f"Combatant '{combatant_id}' not found in combat state.")
        return c

    def _sort_by_initiative(self) -> None:
        """Sort combatants by (initiative DESC, dex_score DESC).

        Preserves current_turn_index by tracking the active combatant's ID,
        then finding its new position after sort.
        """
        if not self._state.combatants:
            return

        # Remember who's active
        if 0 <= self._state.current_turn_index < len(self._state.combatants):
            active_id = self._state.combatants[self._state.current_turn_index].id
        else:
            active_id = None

        self._state.combatants.sort(
            key=lambda c: (c.initiative, c.dex_score),
            reverse=True,
        )

        # Restore the turn pointer to the active combatant's new position
        if active_id is not None:
            for i, c in enumerate(self._state.combatants):
                if c.id == active_id:
                    self._state.current_turn_index = i
                    break

    def _decrement_conditions_for(self, combatant: CombatantState) -> list[str]:
        """Decrement all timed conditions on a combatant. Returns log entries for expirations."""
        log: list[str] = []
        for cond in combatant.conditions:
            if cond.duration is None or cond.expired:
                continue
            cond.duration -= 1
            if cond.duration == 0:
                cond.expired = True
                log.append(f"{combatant.name}: {cond.name} expired")
        return log

    def _snapshot_state(self) -> dict:
        """Capture a minimal snapshot for undo: turn_index, round_number, all condition durations."""
        snapshot: dict = {
            "turn_index": self._state.current_turn_index,
            "round_number": self._state.round_number,
            "conditions": {},  # {combatant_id: [(name, duration, expired), ...]}
        }
        for c in self._state.combatants:
            snapshot["conditions"][c.id] = [
                (cond.name, cond.duration, cond.expired) for cond in c.conditions
            ]
        return snapshot

    def _restore_from_snapshot(self, snapshot: dict) -> None:
        """Restore turn_index, round_number, and all condition durations from snapshot."""
        self._state.current_turn_index = snapshot["turn_index"]
        self._state.round_number = snapshot["round_number"]
        cond_map = snapshot["conditions"]
        for c in self._state.combatants:
            if c.id not in cond_map:
                continue
            saved_conds = cond_map[c.id]
            # Restore durations/expired flags by position (conditions list should be unchanged)
            for i, (name, duration, expired) in enumerate(saved_conds):
                if i < len(c.conditions):
                    c.conditions[i].duration = duration
                    c.conditions[i].expired = expired

    # ------------------------------------------------------------------
    # Encounter setup
    # ------------------------------------------------------------------

    def load_encounter(self, members: list[tuple], roller) -> None:
        """Load a new encounter from [(Monster, count)] pairs.

        Clears existing combatants; populates max_hp, current_hp, ac,
        dex_score, group_id, speed, passive_perception, and detects
        legendary_resistance / legendary_actions / regeneration from
        Monster.actions[*].raw_text keyword scan.

        Initiative is NOT rolled here — call roll_all_initiative() separately.
        """
        combatants: list[CombatantState] = []
        for monster, count in members:
            group_id = monster.name

            # Detect legendary mechanics from actions.raw_text
            leg_res_max = 0
            leg_act_max = 0
            regen_hp = 0
            actions = getattr(monster, "actions", [])
            for action in actions:
                raw = getattr(action, "raw_text", "") or ""
                # Legendary Resistance: extract count like "3/Day"
                leg_res_match = re.search(
                    r"legendary resistance\s*\(?(\d+)/day\)?", raw, re.IGNORECASE
                )
                if leg_res_match:
                    leg_res_max = max(leg_res_max, int(leg_res_match.group(1)))
                # Legendary Actions: look for action count in descriptor lines
                leg_act_match = re.search(
                    r"can take\s+(\d+)\s+legendary action", raw, re.IGNORECASE
                )
                if leg_act_match:
                    leg_act_max = max(leg_act_max, int(leg_act_match.group(1)))
                # Regeneration: "Regenerates X hit points" or "Regeneration. X HP"
                regen_match = re.search(
                    r"(?:regenerates?|regeneration)[^.]*?(\d+)\s+(?:hit points?|hp)",
                    raw, re.IGNORECASE
                )
                if regen_match:
                    regen_hp = max(regen_hp, int(regen_match.group(1)))

            # DEX modifier from ability_scores
            dex_score = 10
            ability_scores = getattr(monster, "ability_scores", {})
            if ability_scores:
                dex_score = ability_scores.get("DEX", 10)

            speed = getattr(monster, "speed", "")

            for i in range(1, count + 1):
                cid = f"{monster.name}_{i}".replace(" ", "_")
                cname = f"{monster.name} {i}"
                combatant = CombatantState(
                    id=cid,
                    name=cname,
                    monster_name=monster.name,
                    max_hp=monster.hp,
                    current_hp=monster.hp,
                    temp_hp=0,
                    initiative=0,
                    ac=monster.ac,
                    is_pc=False,
                    group_id=group_id,
                    dex_score=dex_score,
                    speed=speed,
                    passive_perception=getattr(monster, "passive_perception", 0),
                    legendary_resistances=leg_res_max,
                    legendary_resistances_max=leg_res_max,
                    legendary_actions=leg_act_max,
                    legendary_actions_max=leg_act_max,
                    regeneration_hp=regen_hp,
                )
                combatants.append(combatant)

        self._state = CombatState(combatants=combatants)
        self._prev_snapshot = None

    def add_pcs(self, pcs: list[PlayerCharacter]) -> None:
        """Add PC combatants with is_pc=True. Auto-numbers only if names duplicate."""
        existing_names = {c.name for c in self._state.combatants}
        for pc in pcs:
            name = pc.name
            # Auto-number if duplicate
            if name in existing_names:
                suffix = 2
                while f"{name} ({suffix})" in existing_names:
                    suffix += 1
                name = f"{name} ({suffix})"
            existing_names.add(name)

            cid = name.replace(" ", "_")
            combatant = CombatantState(
                id=cid,
                name=name,
                monster_name=None,
                max_hp=pc.max_hp,
                current_hp=pc.current_hp,
                temp_hp=0,
                initiative=0,
                ac=pc.ac,
                is_pc=True,
                group_id="",
                dex_score=10,
                initiative_bonus=getattr(pc, "initiative_bonus", 0),
                conditions=[
                    ConditionEntry(
                        name=c.name, duration=c.duration,
                        expired=c.expired, color=c.color
                    )
                    for c in pc.conditions
                ],
            )
            self._state.combatants.append(combatant)

    def remove_combatant(self, combatant_id: str) -> None:
        """Remove combatant by ID. Adjusts current_turn_index if needed (pitfall #2)."""
        idx = None
        for i, c in enumerate(self._state.combatants):
            if c.id == combatant_id:
                idx = i
                break
        if idx is None:
            return

        self._state.combatants.pop(idx)

        # If removed index is <= current_turn_index, decrement (clamp to 0)
        if idx <= self._state.current_turn_index:
            self._state.current_turn_index = max(0, self._state.current_turn_index - 1)

    # ------------------------------------------------------------------
    # Initiative
    # ------------------------------------------------------------------

    def roll_all_initiative(self, roller: Roller) -> None:
        """Roll 1d20 + DEX modifier for each combatant.

        When grouping_enabled=True, all combatants with the same group_id
        share a single roll. Sort combatants by initiative descending,
        then dex_score descending as tiebreaker.
        """
        group_initiative: dict[str, int] = {}  # group_id -> rolled total

        for c in self._state.combatants:
            if c.is_pc:
                # PCs roll 1d20 + initiative_bonus
                roll_result = roller.roll_dice(1, 20)
                c.initiative = roll_result.total + getattr(c, "initiative_bonus", 0)
            elif self._state.grouping_enabled and c.group_id:
                if c.group_id not in group_initiative:
                    dex_mod = (c.dex_score - 10) // 2
                    roll_result = roller.roll_dice(1, 20)
                    group_initiative[c.group_id] = roll_result.total + dex_mod
                c.initiative = group_initiative[c.group_id]
            else:
                dex_mod = (c.dex_score - 10) // 2
                roll_result = roller.roll_dice(1, 20)
                c.initiative = roll_result.total + dex_mod

        self._sort_by_initiative()
        self._state.log_entries.append("Initiative rolled — combat order set.")

    def resort_initiative(self) -> None:
        """Public: re-sort combatants by initiative without re-rolling."""
        self._sort_by_initiative()

    def set_initiative(self, combatant_id: str, value: int) -> None:
        """Manually set a combatant's initiative. Re-sorts if initiative_mode is on."""
        c = self._find(combatant_id)
        c.initiative = value
        if self._state.initiative_mode:
            self._sort_by_initiative()

    # ------------------------------------------------------------------
    # Damage and healing
    # ------------------------------------------------------------------

    def apply_damage(self, combatant_id: str, signed_value: int) -> str:
        """Apply signed damage (negative) or healing (positive).

        Healing: capped at max_hp.
        Damage: temp_hp absorbs first; remainder from current_hp (floor at 0).

        Returns a log entry string describing the change.
        """
        c = self._find(combatant_id)
        if signed_value >= 0:
            # Healing
            old_hp = c.current_hp
            c.current_hp = min(c.max_hp, c.current_hp + signed_value)
            healed = c.current_hp - old_hp
            entry = f"{c.name}: healed {healed} HP ({old_hp} → {c.current_hp})"
        else:
            # Damage
            damage = abs(signed_value)
            temp_absorbed = min(c.temp_hp, damage)
            c.temp_hp -= temp_absorbed
            remaining = damage - temp_absorbed
            old_hp = c.current_hp
            c.current_hp = max(0, c.current_hp - remaining)
            entry = f"{c.name}: -{damage} dmg"
            if temp_absorbed:
                entry += f" ({temp_absorbed} absorbed by temp HP)"
            entry += f" ({old_hp} → {c.current_hp} HP)"
            if c.is_defeated:
                entry += " [DEFEATED]"

        self._state.log_entries.append(entry)
        return entry

    def apply_aoe_damage(self, combatant_ids: list[str], damage: int) -> list[str]:
        """Apply the same damage value to multiple combatants. damage should be positive (absolute value)."""
        logs: list[str] = []
        for cid in combatant_ids:
            entry = self.apply_damage(cid, -abs(damage))
            logs.append(entry)
        return logs

    # ------------------------------------------------------------------
    # Conditions
    # ------------------------------------------------------------------

    def add_condition(self, combatant_id: str, condition: ConditionEntry) -> str:
        """Add a condition to the combatant's condition list. Returns log entry.

        Rejects duplicates — if a condition with the same name already exists
        (and isn't expired), returns an informational message instead.
        """
        c = self._find(combatant_id)
        for existing in c.conditions:
            if existing.name == condition.name and not existing.expired:
                entry = f"{c.name}: {condition.name} already active (not added)"
                return entry
        c.conditions.append(condition)
        duration_str = f"{condition.duration} rounds" if condition.duration is not None else "indefinite"
        entry = f"{c.name}: {condition.name} added ({duration_str})"
        self._state.log_entries.append(entry)
        return entry

    def remove_condition(self, combatant_id: str, condition_name: str) -> str:
        """Remove the first condition matching condition_name. Returns log entry."""
        c = self._find(combatant_id)
        for i, cond in enumerate(c.conditions):
            if cond.name == condition_name:
                c.conditions.pop(i)
                entry = f"{c.name}: {condition_name} removed"
                self._state.log_entries.append(entry)
                return entry
        entry = f"{c.name}: {condition_name} not found (no change)"
        return entry

    # ------------------------------------------------------------------
    # Turn and round management
    # ------------------------------------------------------------------

    def advance_turn(self) -> list[str]:
        """Advance to the next combatant's turn.

        Steps:
        1. Snapshot current state for undo.
        2. Decrement timed conditions on combatant whose turn is ENDING.
        3. If regeneration_hp > 0 (auto-regen enabled), apply healing.
        4. Advance current_turn_index (wrap around).
        5. If wrapped to 0, increment round_number.
        6. Reset legendary_actions to max for combatant NOW starting turn.
        7. Return log entries for all changes.
        """
        if not self._state.combatants:
            return []

        log: list[str] = []

        # 1. Snapshot for undo
        self._prev_snapshot = self._snapshot_state()

        # 2. Decrement conditions on ending combatant
        ending_idx = self._state.current_turn_index
        ending = self._state.combatants[ending_idx]
        log.extend(self._decrement_conditions_for(ending))

        # 3. Auto-regen (if enabled — _auto_regen flag and regeneration_hp > 0)
        if self._auto_regen and ending.regeneration_hp > 0:
            entry = self.apply_damage(ending.id, ending.regeneration_hp)
            log.append(f"[Regen] {entry}")

        # 4. Advance turn index
        n = len(self._state.combatants)
        new_index = (ending_idx + 1) % n
        self._state.current_turn_index = new_index

        # 5. Increment round if wrapped
        if new_index == 0:
            self._state.round_number += 1
            log.append(f"Round {self._state.round_number} begins.")

        # 6. Reset legendary actions for new active combatant
        starting = self._state.combatants[new_index]
        if starting.legendary_actions_max > 0:
            starting.legendary_actions = starting.legendary_actions_max

        log.append(
            f"Turn: {starting.name} "
            f"(Round {self._state.round_number}, Turn {new_index + 1})"
        )

        self._state.log_entries.extend(log)
        return log

    def undo_advance(self) -> bool:
        """Restore the state to before the last advance_turn.

        Returns False if no snapshot is available (no advance has occurred).
        Restores turn_index, round_number, and all condition durations atomically.
        """
        if self._prev_snapshot is None:
            return False
        self._restore_from_snapshot(self._prev_snapshot)
        self._prev_snapshot = None
        return True

    def pass_one_round(self) -> list[str]:
        """Decrement all timed conditions on ALL combatants. Increment round_number.

        Used in the non-initiative mode ("Pass 1 Round" button).
        Returns log entries for all condition expirations.
        """
        log: list[str] = []
        for c in self._state.combatants:
            log.extend(self._decrement_conditions_for(c))
        self._state.round_number += 1
        log.append(f"Round {self._state.round_number} begins (pass-1-round mode).")
        self._state.log_entries.extend(log)
        return log

    # ------------------------------------------------------------------
    # Combat lifecycle
    # ------------------------------------------------------------------

    def reset_combat(self) -> None:
        """Reset all HP to max, clear conditions and initiative, round_number=1, clear log."""
        for c in self._state.combatants:
            c.current_hp = c.max_hp
            c.temp_hp = 0
            c.conditions = []
            c.initiative = 0
            c.legendary_resistances = c.legendary_resistances_max
            c.legendary_actions = c.legendary_actions_max
        self._state.round_number = 1
        self._state.current_turn_index = 0
        self._state.log_entries = []
        self._prev_snapshot = None

    # ------------------------------------------------------------------
    # Reorder and auto-regen
    # ------------------------------------------------------------------

    def reorder_combatants(self, ordered_ids: list[str]) -> None:
        """Reorder combatants to match the given ID order.

        Only works when initiative_mode is False. Preserves current_turn_index
        by tracking the active combatant's ID and finding its new position.
        """
        if self._state.initiative_mode:
            return  # no-op in initiative mode

        id_to_combatant = {c.id: c for c in self._state.combatants}
        # Build new list; skip unknown IDs; append any IDs not in ordered_ids at end
        ordered = [id_to_combatant[cid] for cid in ordered_ids if cid in id_to_combatant]
        remaining = [c for c in self._state.combatants if c.id not in set(ordered_ids)]
        ordered.extend(remaining)

        # Remember active combatant
        if 0 <= self._state.current_turn_index < len(self._state.combatants):
            active_id = self._state.combatants[self._state.current_turn_index].id
        else:
            active_id = None

        self._state.combatants = ordered

        # Restore turn pointer
        if active_id is not None:
            for i, c in enumerate(self._state.combatants):
                if c.id == active_id:
                    self._state.current_turn_index = i
                    break

    def set_auto_regen(self, enabled: bool) -> None:
        """Enable or disable automatic regeneration healing on turn advance."""
        self._auto_regen = enabled

    # ------------------------------------------------------------------
    # Persistence
    # ------------------------------------------------------------------

    def load_state(self, state: CombatState) -> None:
        """Restore the service from a previously serialized CombatState (from persistence)."""
        self._state = state
        self._prev_snapshot = None
