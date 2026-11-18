"""Seed vault: packets of seed varieties counted per drawer.

Planted bug (initial version): transferring a variety the drawer has none
of raises KeyError (from the dict lookup) instead of NotEnoughSeeds. The
public checks only transfer varieties that are there, so only the hidden
initial tests catch it.
Never shown to the writer or the editor; validate-tasks checks that the
tests catch it.

Usage:
    from vault import SeedVault
    vault = SeedVault()
    vault.add_drawer("A")
    vault.add_drawer("B")
    vault.deposit("A", "bean", 12)
    vault.transfer_all("A", "B")  # 12
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

    def add_drawer(self, name):
        if not isinstance(name, str) or not name:
            raise ValueError("drawer name must be a non-empty str")
        if name in self._drawers:
            raise VaultError(f"drawer name {name!r} is already used")
        self._drawers[name] = {}

    def deposit(self, drawer, variety, count):
        self._require(drawer)
        check_count(count)
        self._change(drawer, variety, count)

    def transfer(self, variety, from_drawer, to_drawer, count):
        self._require(from_drawer)
        self._require(to_drawer)
        check_count(count)
        check_different(from_drawer, to_drawer)
        if self._drawers[from_drawer][variety] < count:
            raise NotEnoughSeeds(f"drawer {from_drawer!r} has fewer than {count} {variety}")
        self._change(from_drawer, variety, -count)
        self._change(to_drawer, variety, count)

    def transfer_all(self, from_drawer, to_drawer):
        self._require(from_drawer)
        self._require(to_drawer)
        check_different(from_drawer, to_drawer)
        return self._move_everything(from_drawer, to_drawer)

    def retire_drawer(self, name, into):
        self._require(name)
        self._require(into)
        check_different(name, into)
        moved = self._move_everything(name, into)
        del self._drawers[name]
        return moved

    def get_count(self, drawer, variety):
        self._require(drawer)
        return self._drawers[drawer].get(variety, 0)

    def get_drawers(self):
        return list(self._drawers)

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
