from src.domain.models import Monster


class MonsterLibrary:
    """In-memory runtime store for Monster instances.

    Provides O(1) has_name lookup via a name->index dict, plus ordered
    iteration via an internal list.  No Qt or I/O imports — pure stdlib +
    domain only.
    """

    def __init__(self) -> None:
        self._monsters: list[Monster] = []
        self._by_name: dict[str, int] = {}  # name -> index in _monsters

    # ------------------------------------------------------------------
    # Mutation
    # ------------------------------------------------------------------

    def add(self, monster: Monster) -> None:
        """Append *monster* to the library.

        If a monster with the same name already exists, the new entry is still
        appended (keep-both duplicate scenario — callers decide on dedup).
        Only the first occurrence is tracked in _by_name for has_name O(1).
        """
        idx = len(self._monsters)
        self._monsters.append(monster)
        # Only record first occurrence; duplicates are still accessible via all()
        if monster.name not in self._by_name:
            self._by_name[monster.name] = idx

    def replace(self, monster: Monster) -> None:
        """Replace the first existing entry with the same name in-place.

        If no monster with that name exists, the monster is appended instead
        (safe fall-through).
        """
        if monster.name in self._by_name:
            idx = self._by_name[monster.name]
            self._monsters[idx] = monster
        else:
            self.add(monster)

    def remove(self, name: str) -> bool:
        """Remove the first monster whose name matches *name*.

        Returns True if a monster was removed, False otherwise.
        Rebuilds _by_name after removal to keep indices consistent.
        """
        for i, m in enumerate(self._monsters):
            if m.name == name:
                del self._monsters[i]
                # Rebuild index dict since indices have shifted
                self._by_name = {
                    m.name: idx
                    for idx, m in enumerate(self._monsters)
                    if m.name not in {self._monsters[j].name for j in range(idx)}
                }
                return True
        return False

    def clear(self) -> None:
        """Remove all monsters from the library."""
        self._monsters = []
        self._by_name = {}

    # ------------------------------------------------------------------
    # Query
    # ------------------------------------------------------------------

    def has_name(self, name: str) -> bool:
        """Return True if any monster with *name* is in the library."""
        return name in self._by_name

    def get_by_name(self, name: str) -> "Monster":
        """Return first monster with given name. Raises KeyError if name not found.

        Always call has_name() first to check existence before calling this.
        The Monster import is already at the top of the file.
        """
        idx = self._by_name[name]
        return self._monsters[idx]

    def all(self) -> list[Monster]:
        """Return a defensive copy of all monsters in insertion order."""
        return list(self._monsters)

    def search(self, query: str) -> list[Monster]:
        """Case-insensitive substring search across name, cr, and creature_type.

        Returns matching monsters in original insertion order.
        """
        q = query.lower()
        return [
            m for m in self._monsters
            if q in m.name.lower()
            or q in m.cr.lower()
            or q in m.creature_type.lower()
        ]

    def creature_types(self) -> list[str]:
        """Return a sorted, deduplicated list of creature_type values.

        Used to populate the type-filter dropdown in the library UI.
        Empty strings are excluded.
        """
        return sorted({m.creature_type for m in self._monsters if m.creature_type})
