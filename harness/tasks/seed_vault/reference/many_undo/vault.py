"""Seed vault with several transfers in one call, and undo.

Correct solution for seed_vault after c_many and c_undo.
Never shown to the writer or the editor; validate-tasks checks that it
passes every test it should.

Usage:
    from vault import SeedVault
    vault = SeedVault()
    vault.add_drawer("A")
    vault.add_drawer("B")
    vault.deposit("A", "bean", 12)
    vault.transfer_many([("bean", "A", "B", 5), ("bean", "B", "A", 1)])
    vault.undo()  # both transfers are taken back
"""


class VaultError(Exception):
    pass


class NotEnoughSeeds(VaultError):
    pass


def check_count(count):
    if isinstance(count, bool) or not isinstance(count, int) or count <= 0:
        raise ValueError(f"count must be a positive int, got {count!r}")


def check_different(from_drawer, to_drawer):
    if from_drawer == to_drawer:
        raise ValueError("cannot move packets into the drawer they are in")


class SeedVault:
    def __init__(self):
        # drawer name -> {variety: count}; both dicts keep the order things
        # were added, and only counts above 0 are stored.
        self._drawers = {}
        self._undo_stack = []  # copies of the drawers as they were before each call

    def add_drawer(self, name):
        if not isinstance(name, str) or not name:
            raise ValueError("drawer name must be a non-empty str")
        if name in self._drawers:
            raise VaultError(f"drawer name {name!r} is already used")
        self._save()
        self._drawers[name] = {}

    def deposit(self, drawer, variety, count):
        self._require(drawer)
        check_count(count)
        self._save()
        self._change(drawer, variety, count)

    def transfer(self, variety, from_drawer, to_drawer, count):
        self._check_transfer(variety, from_drawer, to_drawer, count)
        self._save()
        self._apply_transfer(variety, from_drawer, to_drawer, count)

    def transfer_many(self, transfers):
        # The whole call is one entry on the undo stack; on a failure the
        # vault goes back to the copy and nothing is recorded.
        saved = self._copy()
        moved = 0
        try:
            for variety, from_drawer, to_drawer, count in transfers:
                self._check_transfer(variety, from_drawer, to_drawer, count)
                self._apply_transfer(variety, from_drawer, to_drawer, count)
                moved += count
        except Exception:
            self._drawers = saved
            raise
        self._undo_stack.append(saved)
        return moved

    def transfer_all(self, from_drawer, to_drawer):
        self._require(from_drawer)
        self._require(to_drawer)
        check_different(from_drawer, to_drawer)
        self._save()
        return self._move_everything(from_drawer, to_drawer)

    def retire_drawer(self, name, into):
        self._require(name)
        self._require(into)
        check_different(name, into)
        self._save()
        moved = self._move_everything(name, into)
        del self._drawers[name]
        return moved

    def undo(self):
        if not self._undo_stack:
            raise VaultError("nothing to undo")
        self._drawers = self._undo_stack.pop()

    def get_count(self, drawer, variety):
        self._require(drawer)
        return self._drawers[drawer].get(variety, 0)

    def get_drawers(self):
        return list(self._drawers)

    def _save(self):
        # Called by each recorded call once all its checks have passed.
        self._undo_stack.append(self._copy())

    def _copy(self):
        return {name: dict(packets) for name, packets in self._drawers.items()}

    def _check_transfer(self, variety, from_drawer, to_drawer, count):
        self._require(from_drawer)
        self._require(to_drawer)
        check_count(count)
        check_different(from_drawer, to_drawer)
        if self._drawers[from_drawer].get(variety, 0) < count:
            raise NotEnoughSeeds(f"drawer {from_drawer!r} has fewer than {count} {variety}")

    def _apply_transfer(self, variety, from_drawer, to_drawer, count):
        self._change(from_drawer, variety, -count)
        self._change(to_drawer, variety, count)

    def _require(self, drawer):
        if not isinstance(drawer, str) or drawer not in self._drawers:
            raise KeyError(drawer)

    def _move_everything(self, from_drawer, to_drawer):
        packets = self._drawers[from_drawer]
        moved = sum(packets.values())
        for variety, count in packets.items():
            self._change(to_drawer, variety, count)
        packets.clear()
        return moved

    def _change(self, drawer, variety, delta):
        packets = self._drawers[drawer]
        new_count = packets.get(variety, 0) + delta
        if new_count:
            packets[variety] = new_count
        else:
            del packets[variety]
